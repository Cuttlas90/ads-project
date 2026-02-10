from __future__ import annotations

from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

from app.domain.escrow_fsm import EscrowState
from app.models.channel import Channel
from app.models.deal import Deal, DealSourceType, DealState
from app.models.deal_escrow import DealEscrow
from app.models.listing import Listing
from app.models.listing_format import ListingFormat
from app.models.user import User
from app.services.ton.payouts import ensure_refund, refund_funds, release_funds
from app.settings import Settings
from shared.db.base import SQLModel


def _seed_deal_and_escrow(
    session: Session,
    *,
    deal_state: str,
    expected_amount: Decimal,
    received_amount: Decimal,
    subwallet_id: int,
) -> tuple[Deal, DealEscrow, User, User]:
    advertiser = User(telegram_user_id=111, username="adv", ton_wallet_address="EQ_ADV")
    owner = User(telegram_user_id=222, username="owner", ton_wallet_address="EQ_OWNER")
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
        state=deal_state,
    )
    session.add(deal)
    session.flush()

    escrow = DealEscrow(
        deal_id=deal.id,
        state=EscrowState.FUNDED.value,
        deposit_address="0:1111111111111111111111111111111111111111111111111111111111111111",
        deposit_address_raw="0:1111111111111111111111111111111111111111111111111111111111111111",
        subwallet_id=subwallet_id,
        escrow_network="testnet",
        expected_amount_ton=expected_amount,
        received_amount_ton=received_amount,
        fee_percent=Decimal("5.00"),
    )
    session.add(escrow)
    session.commit()
    session.refresh(deal)
    session.refresh(escrow)
    return deal, escrow, advertiser, owner


def test_release_uses_escrow_principal_and_subwallet() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    settings = Settings(
        _env_file=None,
        TON_FEE_PERCENT=Decimal("10.0"),
        TON_REFUND_NETWORK_FEE=Decimal("0.02"),
    )
    calls: list[dict] = []

    def fake_transfer(**kwargs):
        calls.append(kwargs)
        return "tx_release"

    with Session(engine) as session:
        deal, escrow, _, owner = _seed_deal_and_escrow(
            session,
            deal_state=DealState.VERIFIED.value,
            expected_amount=Decimal("10.00"),
            received_amount=Decimal("6.00"),
            subwallet_id=777,
        )

        result = release_funds(
            db=session,
            deal=deal,
            escrow=escrow,
            owner=owner,
            settings=settings,
            transfer_fn=fake_transfer,
        )
        session.commit()
        session.refresh(deal)
        session.refresh(escrow)

        assert result.tx_hash == "tx_release"
        assert result.amount_ton == Decimal("5.380000000")
        assert deal.state == DealState.RELEASED.value
        assert escrow.released_amount_ton == Decimal("5.380000000")
        assert calls[0]["source_subwallet_id"] == 777
        assert calls[0]["amount_ton"] == Decimal("5.380000000")

    SQLModel.metadata.drop_all(engine)


def test_refund_always_deducts_fee_and_records_zero_without_transfer() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    settings = Settings(_env_file=None, TON_REFUND_NETWORK_FEE=Decimal("0.02"))

    def fail_transfer(**kwargs):
        raise AssertionError("transfer should not be called")

    with Session(engine) as session:
        deal, escrow, advertiser, _ = _seed_deal_and_escrow(
            session,
            deal_state=DealState.REFUNDED.value,
            expected_amount=Decimal("10.00"),
            received_amount=Decimal("0.01"),
            subwallet_id=555,
        )

        result = refund_funds(
            db=session,
            deal=deal,
            escrow=escrow,
            advertiser=advertiser,
            settings=settings,
            transfer_fn=fail_transfer,
        )
        session.commit()
        session.refresh(escrow)

        assert result.amount_ton == Decimal("0E-9")
        assert result.tx_hash == ""
        assert escrow.refund_tx_hash is None
        assert escrow.refunded_at is not None
        assert escrow.refunded_amount_ton == Decimal("0E-9")

        assert (
            ensure_refund(
                db=session,
                deal=deal,
                escrow=escrow,
                advertiser=advertiser,
                settings=settings,
                transfer_fn=fail_transfer,
            )
            is None
        )

    SQLModel.metadata.drop_all(engine)


def test_release_records_zero_without_transfer_when_fees_exceed_principal() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    settings = Settings(
        _env_file=None,
        TON_FEE_PERCENT=Decimal("10.0"),
        TON_REFUND_NETWORK_FEE=Decimal("0.02"),
    )

    def fail_transfer(**kwargs):
        raise AssertionError("transfer should not be called")

    with Session(engine) as session:
        deal, escrow, _, owner = _seed_deal_and_escrow(
            session,
            deal_state=DealState.VERIFIED.value,
            expected_amount=Decimal("10.00"),
            received_amount=Decimal("0.01"),
            subwallet_id=888,
        )

        result = release_funds(
            db=session,
            deal=deal,
            escrow=escrow,
            owner=owner,
            settings=settings,
            transfer_fn=fail_transfer,
        )
        session.commit()
        session.refresh(deal)
        session.refresh(escrow)

        assert result.amount_ton == Decimal("0E-9")
        assert result.tx_hash == ""
        assert deal.state == DealState.RELEASED.value
        assert escrow.release_tx_hash is None
        assert escrow.released_at is not None
        assert escrow.released_amount_ton == Decimal("0E-9")

    SQLModel.metadata.drop_all(engine)
