from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, select

from app.domain.escrow_fsm import EscrowState
from app.models.channel import Channel
from app.models.deal import Deal, DealSourceType, DealState
from app.models.deal_escrow import DealEscrow
from app.models.deal_event import DealEvent
from app.models.listing import Listing
from app.models.listing_format import ListingFormat
from app.models.user import User
from app.services.deal_fsm import DealTransitionError
from app.settings import Settings
from app.worker.ton_watch import _process_escrow
from shared.db.base import SQLModel


class FakeAdapter:
    def __init__(self, txs: list[dict]) -> None:
        self._txs = txs
        self.confirmations = 0

    def find_incoming_tx(
        self, address: str, min_amount: Decimal, since_lt: str | None
    ) -> dict | None:
        since_value = int(since_lt) if since_lt is not None else None
        for tx in self._txs:
            lt_value = int(tx["lt"])
            if since_value is None or lt_value > since_value:
                return tx
        return None

    def get_confirmations(self, tx_hash: str) -> int:
        return self.confirmations


def _seed_escrow(
    session: Session,
    *,
    scheduled_at: datetime | None = None,
    received_amount: Decimal = Decimal("0"),
    escrow_state: str = EscrowState.AWAITING_DEPOSIT.value,
) -> DealEscrow:
    advertiser = User(telegram_user_id=111, username="adv", ton_wallet_address="EQ_ADV")
    owner = User(telegram_user_id=222, username="owner")
    session.add(advertiser)
    session.add(owner)
    session.flush()

    channel = Channel(username="channel")
    session.add(channel)
    session.flush()

    listing = Listing(channel_id=channel.id, owner_id=owner.id, is_active=True)
    session.add(listing)
    session.flush()

    listing_format = ListingFormat(
        listing_id=listing.id,
        placement_type="post",
        exclusive_hours=1,
        retention_hours=24,
        price=Decimal("10.00"),
    )
    session.add(listing_format)
    session.flush()

    deal = Deal(
        source_type=DealSourceType.LISTING.value,
        advertiser_id=advertiser.id,
        channel_id=channel.id,
        channel_owner_id=owner.id,
        listing_id=listing.id,
        listing_format_id=listing_format.id,
        price_ton=Decimal("10.00"),
        ad_type=listing_format.placement_type,
        placement_type=listing_format.placement_type,
        exclusive_hours=listing_format.exclusive_hours,
        retention_hours=listing_format.retention_hours,
        creative_text="Hello",
        creative_media_type="image",
        creative_media_ref="ref",
        posting_params=None,
        scheduled_at=scheduled_at,
        state=DealState.CREATIVE_APPROVED.value,
    )
    session.add(deal)
    session.flush()

    escrow = DealEscrow(
        deal_id=deal.id,
        state=escrow_state,
        deposit_address="0:1111111111111111111111111111111111111111111111111111111111111111",
        deposit_address_raw="0:1111111111111111111111111111111111111111111111111111111111111111",
        subwallet_id=123,
        escrow_network="testnet",
        expected_amount_ton=Decimal("10.00"),
        received_amount_ton=received_amount,
        fee_percent=Decimal("5.00"),
    )
    session.add(escrow)
    session.commit()
    session.refresh(escrow)
    return escrow


def test_watch_idempotent(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    calls: list[int] = []

    def _record_notify(**kwargs):
        calls.append(1)

    monkeypatch.setattr("app.worker.ton_watch.notify_deal_funded", _record_notify)

    txs = [
        {
            "hash": "tx1",
            "lt": "1",
            "amount_ton": Decimal("5"),
            "utime": 1,
            "mc_block_seqno": 10,
        },
        {
            "hash": "tx2",
            "lt": "2",
            "amount_ton": Decimal("5"),
            "utime": 2,
            "mc_block_seqno": 11,
        },
    ]
    adapter = FakeAdapter(txs)
    settings = Settings(_env_file=None, TON_CONFIRMATIONS_REQUIRED=3)

    with Session(engine) as session:
        escrow = _seed_escrow(session)
        _process_escrow(db=session, escrow=escrow, adapter=adapter, settings=settings)
        session.commit()
        session.refresh(escrow)

        assert escrow.state == EscrowState.DEPOSIT_DETECTED.value
        assert escrow.received_amount_ton == Decimal("10")

        adapter.confirmations = 3
        _process_escrow(db=session, escrow=escrow, adapter=adapter, settings=settings)
        session.commit()
        session.refresh(escrow)

        assert escrow.state == EscrowState.FUNDED.value
        deal = session.exec(select(Deal).where(Deal.id == escrow.deal_id)).one()
        assert deal.state == DealState.FUNDED.value
        assert len(calls) == 1

        previous_amount = escrow.received_amount_ton
        _process_escrow(db=session, escrow=escrow, adapter=adapter, settings=settings)
        session.commit()
        session.refresh(escrow)
        assert escrow.received_amount_ton == previous_amount

    SQLModel.metadata.drop_all(engine)


def test_watch_timeout_without_funding_marks_refunded() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    now = datetime.now(timezone.utc)
    settings = Settings(_env_file=None, TON_CONFIRMATIONS_REQUIRED=3)
    adapter = FakeAdapter([])

    with Session(engine) as session:
        escrow = _seed_escrow(
            session,
            scheduled_at=now - timedelta(minutes=1),
            received_amount=Decimal("0"),
            escrow_state=EscrowState.AWAITING_DEPOSIT.value,
        )
        _process_escrow(db=session, escrow=escrow, adapter=adapter, settings=settings)
        session.commit()
        session.refresh(escrow)

        deal = session.exec(select(Deal).where(Deal.id == escrow.deal_id)).one()
        assert escrow.state == EscrowState.FAILED.value
        assert deal.state == DealState.REFUNDED.value
        assert escrow.refunded_amount_ton == Decimal("0E-9")
        assert escrow.refunded_at is not None

    SQLModel.metadata.drop_all(engine)


def test_watch_timeout_partial_funding_triggers_refund(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    now = datetime.now(timezone.utc)
    settings = Settings(_env_file=None, TON_CONFIRMATIONS_REQUIRED=3)
    adapter = FakeAdapter([])
    calls: list[int] = []
    refund_notifications: list[int] = []

    def _fake_refund(*, escrow, **kwargs):
        calls.append(1)
        escrow.refund_tx_hash = "tx_timeout_refund"
        escrow.refunded_amount_ton = Decimal("4.980000000")
        escrow.refunded_at = datetime.now(timezone.utc)
        return None

    monkeypatch.setattr("app.worker.ton_watch.ensure_refund", _fake_refund)
    monkeypatch.setattr(
        "app.worker.ton_watch.notify_deal_refunded",
        lambda **kwargs: refund_notifications.append(1),
    )

    with Session(engine) as session:
        escrow = _seed_escrow(
            session,
            scheduled_at=now - timedelta(minutes=1),
            received_amount=Decimal("5"),
            escrow_state=EscrowState.DEPOSIT_DETECTED.value,
        )
        _process_escrow(db=session, escrow=escrow, adapter=adapter, settings=settings)
        session.commit()
        session.refresh(escrow)

        deal = session.exec(select(Deal).where(Deal.id == escrow.deal_id)).one()
        assert escrow.state == EscrowState.FAILED.value
        assert deal.state == DealState.REFUNDED.value
        assert escrow.refund_tx_hash == "tx_timeout_refund"
        assert calls == [1]
        assert refund_notifications == [1]

    SQLModel.metadata.drop_all(engine)


def test_watch_timeout_uses_start_at_fallback_from_proposal() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    settings = Settings(_env_file=None, TON_CONFIRMATIONS_REQUIRED=3)
    adapter = FakeAdapter([])

    with Session(engine) as session:
        escrow = _seed_escrow(
            session,
            scheduled_at=None,
            received_amount=Decimal("0"),
            escrow_state=EscrowState.AWAITING_DEPOSIT.value,
        )
        session.add(
            DealEvent(
                deal_id=escrow.deal_id,
                actor_id=None,
                event_type="proposal",
                payload={
                    "start_at": (
                        datetime.now(timezone.utc) - timedelta(minutes=1)
                    ).isoformat()
                },
            )
        )
        session.commit()
        session.refresh(escrow)

        _process_escrow(db=session, escrow=escrow, adapter=adapter, settings=settings)
        session.commit()
        session.refresh(escrow)

        deal = session.exec(select(Deal).where(Deal.id == escrow.deal_id)).one()
        assert escrow.state == EscrowState.FAILED.value
        assert deal.state == DealState.REFUNDED.value

    SQLModel.metadata.drop_all(engine)


def test_watch_uses_fsm_transition_helpers(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    settings = Settings(_env_file=None, TON_CONFIRMATIONS_REQUIRED=3)
    txs = [
        {
            "hash": "tx1",
            "lt": "1",
            "amount_ton": Decimal("10"),
            "utime": 1,
            "mc_block_seqno": 10,
        },
    ]
    adapter = FakeAdapter(txs)
    adapter.confirmations = 3

    def _boom(*args, **kwargs):
        raise DealTransitionError("blocked")

    monkeypatch.setattr("app.worker.ton_watch.apply_transition", _boom)

    with Session(engine) as session:
        escrow = _seed_escrow(session)
        with pytest.raises(DealTransitionError):
            _process_escrow(
                db=session, escrow=escrow, adapter=adapter, settings=settings
            )
        session.rollback()

        refreshed = session.exec(select(Deal).where(Deal.id == escrow.deal_id)).one()
        assert refreshed.state == DealState.CREATIVE_APPROVED.value

    SQLModel.metadata.drop_all(engine)
