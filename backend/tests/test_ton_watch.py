from __future__ import annotations

from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, select

from app.domain.escrow_fsm import EscrowState
from app.models.channel import Channel
from app.models.deal import Deal, DealSourceType, DealState
from app.models.deal_escrow import DealEscrow
from app.models.listing import Listing
from app.models.listing_format import ListingFormat
from app.models.user import User
from app.settings import Settings
from app.worker.ton_watch import _process_escrow
from shared.db.base import SQLModel


class FakeAdapter:
    def __init__(self, txs: list[dict]) -> None:
        self._txs = txs
        self.confirmations = 0

    def find_incoming_tx(self, address: str, min_amount: Decimal, since_lt: str | None) -> dict | None:
        since_value = int(since_lt) if since_lt is not None else None
        for tx in self._txs:
            lt_value = int(tx["lt"])
            if since_value is None or lt_value > since_value:
                return tx
        return None

    def get_confirmations(self, tx_hash: str) -> int:
        return self.confirmations


def _seed_escrow(session: Session) -> DealEscrow:
    advertiser = User(telegram_user_id=111, username="adv")
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

    listing_format = ListingFormat(listing_id=listing.id, label="Post", price=Decimal("10.00"))
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
        ad_type=listing_format.label,
        creative_text="Hello",
        creative_media_type="image",
        creative_media_ref="ref",
        posting_params=None,
        state=DealState.CREATIVE_APPROVED.value,
    )
    session.add(deal)
    session.flush()

    escrow = DealEscrow(
        deal_id=deal.id,
        state=EscrowState.AWAITING_DEPOSIT.value,
        deposit_address="EQ_TEST_ADDRESS",
        expected_amount_ton=Decimal("10.00"),
        received_amount_ton=Decimal("0"),
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
        {"hash": "tx1", "lt": "1", "amount_ton": Decimal("5"), "utime": 1, "mc_block_seqno": 10},
        {"hash": "tx2", "lt": "2", "amount_ton": Decimal("5"), "utime": 2, "mc_block_seqno": 11},
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
