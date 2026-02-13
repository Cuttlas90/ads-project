from __future__ import annotations

from datetime import datetime, timedelta, timezone
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
from app.worker.deal_verification import _verify_posted_deals
from shared.db.base import SQLModel


def _seed_posted_deal(
    session: Session,
    *,
    posted_at: datetime,
    placement_type: str,
    exclusive_hours: int,
    retention_hours: int,
) -> tuple[Deal, DealEscrow]:
    advertiser = User(telegram_user_id=111, username="adv", ton_wallet_address="EQ_ADV")
    owner = User(telegram_user_id=222, username="owner", ton_wallet_address="EQ_OWNER")
    session.add(advertiser)
    session.add(owner)
    session.flush()

    channel = Channel(username="channel", telegram_channel_id=123)
    session.add(channel)
    session.flush()

    listing = Listing(channel_id=channel.id, owner_id=owner.id, is_active=True)
    session.add(listing)
    session.flush()

    listing_format = ListingFormat(
        listing_id=listing.id,
        placement_type=placement_type,
        exclusive_hours=exclusive_hours,
        retention_hours=retention_hours,
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
        ad_type=placement_type,
        placement_type=placement_type,
        exclusive_hours=exclusive_hours,
        retention_hours=retention_hours,
        creative_text="Hello",
        creative_media_type="image",
        creative_media_ref="ref",
        posting_params=None,
        state=DealState.POSTED.value,
        posted_message_id="1",
        posted_content_hash="hash",
        posted_at=posted_at,
        verification_window_hours=retention_hours,
    )
    session.add(deal)
    session.flush()

    escrow = DealEscrow(
        deal_id=deal.id,
        state=EscrowState.FUNDED.value,
        deposit_address="0:2222222222222222222222222222222222222222222222222222222222222222",
        deposit_address_raw="0:2222222222222222222222222222222222222222222222222222222222222222",
        subwallet_id=456,
        escrow_network="testnet",
        expected_amount_ton=Decimal("10.00"),
        received_amount_ton=Decimal("10.00"),
        fee_percent=Decimal("5.00"),
    )
    session.add(escrow)
    session.commit()
    session.refresh(deal)
    session.refresh(escrow)
    return deal, escrow


def test_verify_posted_deals_releases_after_windows(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    settings = Settings(
        _env_file=None,
        TON_FEE_PERCENT=Decimal("5.0"),
        TON_REFUND_NETWORK_FEE=Decimal("0.02"),
    )
    now = datetime.now(timezone.utc)
    notifications: list[int] = []
    monkeypatch.setattr(
        "app.worker.deal_verification.notify_deal_released",
        lambda **kwargs: notifications.append(1),
    )

    def fake_transfer(**kwargs):
        return "tx_release"

    with Session(engine) as session:
        deal, escrow = _seed_posted_deal(
            session,
            posted_at=now - timedelta(hours=3),
            placement_type="post",
            exclusive_hours=1,
            retention_hours=2,
        )
        processed = _verify_posted_deals(
            db=session,
            settings=settings,
            now=now,
            fetch_hash_fn=lambda **kwargs: "hash",
            transfer_fn=fake_transfer,
        )
        assert processed == 1

        updated = session.exec(select(Deal).where(Deal.id == deal.id)).one()
        updated_escrow = session.exec(
            select(DealEscrow).where(DealEscrow.id == escrow.id)
        ).one()

        assert updated.state == DealState.RELEASED.value
        assert updated_escrow.release_tx_hash == "tx_release"
        assert updated_escrow.released_amount_ton == Decimal("9.480000000")
        assert notifications == [1]

    SQLModel.metadata.drop_all(engine)


def test_verify_posted_deals_refunds_when_missing_before_retention(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    settings = Settings(
        _env_file=None,
        TON_FEE_PERCENT=Decimal("5.0"),
        TON_REFUND_NETWORK_FEE=Decimal("0.02"),
    )
    now = datetime.now(timezone.utc)
    notifications: list[int] = []
    monkeypatch.setattr(
        "app.worker.deal_verification.notify_deal_refunded",
        lambda **kwargs: notifications.append(1),
    )

    def fake_transfer(**kwargs):
        return "tx_refund"

    with Session(engine) as session:
        deal, escrow = _seed_posted_deal(
            session,
            posted_at=now - timedelta(hours=1),
            placement_type="post",
            exclusive_hours=2,
            retention_hours=24,
        )
        processed = _verify_posted_deals(
            db=session,
            settings=settings,
            now=now,
            fetch_hash_fn=lambda **kwargs: None,
            transfer_fn=fake_transfer,
        )
        assert processed == 1

        updated = session.exec(select(Deal).where(Deal.id == deal.id)).one()
        updated_escrow = session.exec(
            select(DealEscrow).where(DealEscrow.id == escrow.id)
        ).one()

        assert updated.state == DealState.REFUNDED.value
        assert updated_escrow.refund_tx_hash == "tx_refund"
        assert updated_escrow.refunded_amount_ton == Decimal("9.980000000")
        assert notifications == [1]

    SQLModel.metadata.drop_all(engine)


def test_verify_posted_deals_refunds_on_post_exclusivity_breach() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    settings = Settings(
        _env_file=None,
        TON_FEE_PERCENT=Decimal("5.0"),
        TON_REFUND_NETWORK_FEE=Decimal("0.02"),
    )
    now = datetime.now(timezone.utc)

    def fake_transfer(**kwargs):
        return "tx_refund"

    with Session(engine) as session:
        deal, _ = _seed_posted_deal(
            session,
            posted_at=now - timedelta(hours=1),
            placement_type="post",
            exclusive_hours=4,
            retention_hours=24,
        )
        processed = _verify_posted_deals(
            db=session,
            settings=settings,
            now=now,
            fetch_hash_fn=lambda **kwargs: "hash",
            has_post_breach_fn=lambda **kwargs: True,
            transfer_fn=fake_transfer,
        )
        assert processed == 1

        updated = session.exec(select(Deal).where(Deal.id == deal.id)).one()
        assert updated.state == DealState.REFUNDED.value

    SQLModel.metadata.drop_all(engine)


def test_verify_posted_deals_refunds_on_story_exclusivity_breach() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    settings = Settings(
        _env_file=None,
        TON_FEE_PERCENT=Decimal("5.0"),
        TON_REFUND_NETWORK_FEE=Decimal("0.02"),
    )
    now = datetime.now(timezone.utc)

    def fake_transfer(**kwargs):
        return "tx_refund"

    with Session(engine) as session:
        deal, _ = _seed_posted_deal(
            session,
            posted_at=now - timedelta(hours=1),
            placement_type="story",
            exclusive_hours=4,
            retention_hours=24,
        )
        processed = _verify_posted_deals(
            db=session,
            settings=settings,
            now=now,
            fetch_story_hash_fn=lambda **kwargs: "hash",
            has_story_breach_fn=lambda **kwargs: True,
            transfer_fn=fake_transfer,
        )
        assert processed == 1

        updated = session.exec(select(Deal).where(Deal.id == deal.id)).one()
        assert updated.state == DealState.REFUNDED.value

    SQLModel.metadata.drop_all(engine)
