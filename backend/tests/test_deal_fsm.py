from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, select

from app.models.channel import Channel
from app.models.deal import Deal, DealSourceType, DealState
from app.models.deal_event import DealEvent
from app.models.listing import Listing
from app.models.listing_format import ListingFormat
from app.models.user import User
from app.services.deal_fsm import DealAction, DealActorRole, DealTransitionError, apply_transition
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


def _seed_listing_deal(session: Session) -> Deal:
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
        state=DealState.DRAFT.value,
    )
    session.add(deal)
    session.commit()
    session.refresh(deal)
    return deal


def test_apply_transition_moves_to_negotiation(db_engine) -> None:
    with Session(db_engine) as session:
        deal = _seed_listing_deal(session)
        apply_transition(
            session,
            deal=deal,
            action=DealAction.propose.value,
            actor_id=deal.advertiser_id,
            actor_role=DealActorRole.advertiser.value,
        )
        session.commit()
        session.refresh(deal)

        assert deal.state == DealState.NEGOTIATION.value
        events = session.exec(select(DealEvent)).all()
        assert len(events) == 1
        assert events[0].event_type == "transition"


def test_invalid_transition_rejected(db_engine) -> None:
    with Session(db_engine) as session:
        deal = _seed_listing_deal(session)
        with pytest.raises(DealTransitionError):
            apply_transition(
                session,
                deal=deal,
                action=DealAction.accept.value,
                actor_id=deal.advertiser_id,
                actor_role=DealActorRole.advertiser.value,
            )


def test_system_can_fund_creative_approved_deal(db_engine) -> None:
    with Session(db_engine) as session:
        deal = _seed_listing_deal(session)
        apply_transition(
            session,
            deal=deal,
            action=DealAction.propose.value,
            actor_id=deal.advertiser_id,
            actor_role=DealActorRole.advertiser.value,
        )
        apply_transition(
            session,
            deal=deal,
            action=DealAction.accept.value,
            actor_id=deal.channel_owner_id,
            actor_role=DealActorRole.channel_owner.value,
        )
        apply_transition(
            session,
            deal=deal,
            action=DealAction.creative_submit.value,
            actor_id=deal.channel_owner_id,
            actor_role=DealActorRole.channel_owner.value,
        )
        apply_transition(
            session,
            deal=deal,
            action=DealAction.creative_approve.value,
            actor_id=deal.advertiser_id,
            actor_role=DealActorRole.advertiser.value,
        )
        apply_transition(
            session,
            deal=deal,
            action=DealAction.fund.value,
            actor_id=None,
            actor_role=DealActorRole.system.value,
        )
        session.commit()
        session.refresh(deal)

        assert deal.state == DealState.FUNDED.value


def test_system_transition_requires_null_actor(db_engine) -> None:
    with Session(db_engine) as session:
        deal = _seed_listing_deal(session)
        with pytest.raises(DealTransitionError):
            apply_transition(
                session,
                deal=deal,
                action=DealAction.advance.value,
                actor_id=deal.advertiser_id,
                actor_role=DealActorRole.system.value,
            )


def test_system_posting_and_verification_transitions(db_engine) -> None:
    with Session(db_engine) as session:
        deal = _seed_listing_deal(session)
        deal.state = DealState.FUNDED.value
        session.add(deal)
        session.commit()

        apply_transition(
            session,
            deal=deal,
            action=DealAction.schedule.value,
            actor_id=None,
            actor_role=DealActorRole.system.value,
        )
        apply_transition(
            session,
            deal=deal,
            action=DealAction.post.value,
            actor_id=None,
            actor_role=DealActorRole.system.value,
        )
        apply_transition(
            session,
            deal=deal,
            action=DealAction.verify.value,
            actor_id=None,
            actor_role=DealActorRole.system.value,
        )
        apply_transition(
            session,
            deal=deal,
            action=DealAction.release.value,
            actor_id=None,
            actor_role=DealActorRole.system.value,
        )
        session.commit()
        session.refresh(deal)

        assert deal.state == DealState.RELEASED.value


def test_creative_edit_loop_transitions(db_engine) -> None:
    with Session(db_engine) as session:
        deal = _seed_listing_deal(session)
        apply_transition(
            session,
            deal=deal,
            action=DealAction.propose.value,
            actor_id=deal.advertiser_id,
            actor_role=DealActorRole.advertiser.value,
        )
        apply_transition(
            session,
            deal=deal,
            action=DealAction.accept.value,
            actor_id=deal.channel_owner_id,
            actor_role=DealActorRole.channel_owner.value,
        )
        apply_transition(
            session,
            deal=deal,
            action=DealAction.creative_submit.value,
            actor_id=deal.channel_owner_id,
            actor_role=DealActorRole.channel_owner.value,
        )
        apply_transition(
            session,
            deal=deal,
            action=DealAction.creative_request_edits.value,
            actor_id=deal.advertiser_id,
            actor_role=DealActorRole.advertiser.value,
        )
        apply_transition(
            session,
            deal=deal,
            action=DealAction.creative_submit.value,
            actor_id=deal.channel_owner_id,
            actor_role=DealActorRole.channel_owner.value,
        )
        apply_transition(
            session,
            deal=deal,
            action=DealAction.creative_approve.value,
            actor_id=deal.advertiser_id,
            actor_role=DealActorRole.advertiser.value,
        )
        session.commit()
        session.refresh(deal)

        assert deal.state == DealState.CREATIVE_APPROVED.value


def test_system_can_refund_posted_deal(db_engine) -> None:
    with Session(db_engine) as session:
        deal = _seed_listing_deal(session)
        deal.state = DealState.POSTED.value
        session.add(deal)
        session.commit()

        apply_transition(
            session,
            deal=deal,
            action=DealAction.refund.value,
            actor_id=None,
            actor_role=DealActorRole.system.value,
        )
        session.commit()
        session.refresh(deal)

        assert deal.state == DealState.REFUNDED.value
