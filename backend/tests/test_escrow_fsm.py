from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, select

from app.domain.escrow_fsm import EscrowState, EscrowTransitionError, apply_escrow_transition
from app.models.channel import Channel
from app.models.deal import Deal, DealSourceType, DealState
from app.models.deal_escrow import DealEscrow
from app.models.escrow_event import EscrowEvent
from app.models.listing import Listing
from app.models.listing_format import ListingFormat
from app.models.user import User
from shared.db.base import SQLModel


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


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
        state=DealState.ACCEPTED.value,
    )
    session.add(deal)
    session.flush()

    escrow = DealEscrow(
        deal_id=deal.id,
        state=EscrowState.CREATED.value,
        subwallet_id=789,
        escrow_network="testnet",
        expected_amount_ton=Decimal("10.00"),
        received_amount_ton=Decimal("0"),
        fee_percent=Decimal("5.00"),
    )
    session.add(escrow)
    session.commit()
    session.refresh(escrow)
    return escrow


def test_escrow_transition_creates_event(db_engine) -> None:
    with Session(db_engine) as session:
        escrow = _seed_escrow(session)
        apply_escrow_transition(
            session,
            escrow=escrow,
            to_state=EscrowState.AWAITING_DEPOSIT.value,
            actor_user_id=None,
            event_type="address_generated",
        )
        session.commit()
        session.refresh(escrow)

        assert escrow.state == EscrowState.AWAITING_DEPOSIT.value
        events = session.exec(select(EscrowEvent).where(EscrowEvent.escrow_id == escrow.id)).all()
        assert len(events) == 1
        assert events[0].event_type == "address_generated"


def test_invalid_escrow_transition_rejected(db_engine) -> None:
    with Session(db_engine) as session:
        escrow = _seed_escrow(session)
        with pytest.raises(EscrowTransitionError):
            apply_escrow_transition(
                session,
                escrow=escrow,
                to_state=EscrowState.FUNDED.value,
                actor_user_id=None,
                event_type="confirmed",
            )
