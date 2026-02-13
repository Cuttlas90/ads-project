from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, select

from app.models.channel import Channel
from app.models.deal import Deal, DealSourceType, DealState
from app.models.listing import Listing
from app.models.listing_format import ListingFormat
from app.models.user import User
from app.services.deal_fsm import DealTransitionError
from app.settings import Settings
from app.worker.deal_posting import _post_due_deals
from shared.db.base import SQLModel
import app.services.deal_posting as deal_posting


class FakeBotApi:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def send_message(self, **kwargs):
        self.calls.append({"method": "sendMessage", **kwargs})
        return {"ok": True, "result": {"message_id": 1}}

    def send_photo(self, **kwargs):
        self.calls.append({"method": "sendPhoto", **kwargs})
        return {"ok": True, "result": {"message_id": 1}}

    def send_video(self, **kwargs):
        self.calls.append({"method": "sendVideo", **kwargs})
        return {"ok": True, "result": {"message_id": 1}}

    def post_story(self, **kwargs):
        self.calls.append({"method": "postStory", **kwargs})
        return {"ok": True, "result": {"id": 77}}


def _seed_deal(
    session: Session,
    *,
    scheduled_at: datetime,
    placement_type: str,
    media_type: str,
    retention_hours: int,
    state: str = DealState.FUNDED.value,
) -> Deal:
    advertiser = User(telegram_user_id=111, username="adv")
    owner = User(telegram_user_id=222, username="owner")
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
        exclusive_hours=1,
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
        exclusive_hours=listing_format.exclusive_hours,
        retention_hours=listing_format.retention_hours,
        creative_text="Hello",
        creative_media_type=media_type,
        creative_media_ref="ref",
        posting_params=None,
        scheduled_at=scheduled_at,
        state=state,
    )
    session.add(deal)
    session.commit()
    session.refresh(deal)
    return deal


def test_post_due_deals_posts_feed_and_transitions(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    now = datetime.now(timezone.utc)
    settings = Settings(_env_file=None)
    notifications: list[int] = []

    monkeypatch.setattr(
        deal_posting, "fetch_message_hash_sync", lambda **kwargs: "hash"
    )
    monkeypatch.setattr(
        "app.worker.deal_posting.notify_deal_posted",
        lambda **kwargs: notifications.append(1),
    )

    with Session(engine) as session:
        deal = _seed_deal(
            session,
            scheduled_at=now - timedelta(minutes=1),
            placement_type="post",
            media_type="image",
            retention_hours=48,
        )
        bot_api = FakeBotApi()

        processed = _post_due_deals(
            db=session, settings=settings, now=now, bot_api=bot_api
        )
        assert processed == 1

        updated = session.exec(select(Deal).where(Deal.id == deal.id)).one()
        assert updated.state == DealState.POSTED.value
        assert updated.posted_message_id == "1"
        assert updated.posted_content_hash == "hash"
        assert updated.posted_at is not None
        assert updated.verification_window_hours == 48
        assert bot_api.calls[0]["method"] == "sendPhoto"
        assert notifications == [1]

    SQLModel.metadata.drop_all(engine)


def test_post_due_deals_posts_story(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    now = datetime.now(timezone.utc)
    settings = Settings(_env_file=None)

    monkeypatch.setattr(
        deal_posting, "fetch_story_hash_sync", lambda **kwargs: "story-hash"
    )

    with Session(engine) as session:
        deal = _seed_deal(
            session,
            scheduled_at=now - timedelta(minutes=1),
            placement_type="story",
            media_type="video",
            retention_hours=24,
        )
        bot_api = FakeBotApi()

        processed = _post_due_deals(
            db=session, settings=settings, now=now, bot_api=bot_api
        )
        assert processed == 1

        updated = session.exec(select(Deal).where(Deal.id == deal.id)).one()
        assert updated.state == DealState.POSTED.value
        assert updated.posted_message_id == "77"
        assert updated.posted_content_hash == "story-hash"
        assert updated.verification_window_hours == 24
        assert bot_api.calls[0]["method"] == "postStory"

    SQLModel.metadata.drop_all(engine)


def test_post_due_deals_skips_unfunded_creative_approved(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    now = datetime.now(timezone.utc)
    settings = Settings(_env_file=None)
    monkeypatch.setattr(
        deal_posting, "fetch_message_hash_sync", lambda **kwargs: "hash"
    )

    with Session(engine) as session:
        deal = _seed_deal(
            session,
            scheduled_at=now - timedelta(minutes=1),
            placement_type="post",
            media_type="image",
            retention_hours=24,
            state=DealState.CREATIVE_APPROVED.value,
        )
        bot_api = FakeBotApi()

        processed = _post_due_deals(
            db=session, settings=settings, now=now, bot_api=bot_api
        )
        assert processed == 0

        updated = session.exec(select(Deal).where(Deal.id == deal.id)).one()
        assert updated.state == DealState.CREATIVE_APPROVED.value
        assert updated.posted_message_id is None
        assert bot_api.calls == []

    SQLModel.metadata.drop_all(engine)


def test_post_due_deals_uses_fsm_transition_helper(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    now = datetime.now(timezone.utc)
    settings = Settings(_env_file=None)
    monkeypatch.setattr(
        deal_posting, "fetch_message_hash_sync", lambda **kwargs: "hash"
    )

    def _boom(*args, **kwargs):
        raise DealTransitionError("blocked")

    monkeypatch.setattr("app.worker.deal_posting.apply_transition", _boom)

    with Session(engine) as session:
        deal = _seed_deal(
            session,
            scheduled_at=now - timedelta(minutes=1),
            placement_type="post",
            media_type="image",
            retention_hours=24,
            state=DealState.FUNDED.value,
        )
        bot_api = FakeBotApi()

        processed = _post_due_deals(
            db=session, settings=settings, now=now, bot_api=bot_api
        )
        assert processed == 0

        updated = session.exec(select(Deal).where(Deal.id == deal.id)).one()
        assert updated.state == DealState.FUNDED.value
        assert updated.posted_message_id is None
        assert bot_api.calls == []

    SQLModel.metadata.drop_all(engine)


def test_post_due_deals_normalizes_numeric_channel_id_for_bot_api(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    now = datetime.now(timezone.utc)
    settings = Settings(_env_file=None)
    monkeypatch.setattr(
        deal_posting, "fetch_message_hash_sync", lambda **kwargs: "hash"
    )

    with Session(engine) as session:
        deal = _seed_deal(
            session,
            scheduled_at=now - timedelta(minutes=1),
            placement_type="post",
            media_type="image",
            retention_hours=24,
            state=DealState.FUNDED.value,
        )
        channel = session.exec(
            select(Channel).where(Channel.id == deal.channel_id)
        ).one()
        channel.telegram_channel_id = 2210950485
        channel.username = None
        session.add(channel)
        session.commit()

        bot_api = FakeBotApi()
        processed = _post_due_deals(
            db=session, settings=settings, now=now, bot_api=bot_api
        )

        assert processed == 1
        assert bot_api.calls
        assert bot_api.calls[0]["chat_id"] == -1002210950485

    SQLModel.metadata.drop_all(engine)


def test_post_due_deals_prefixes_username_channel_ref(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    now = datetime.now(timezone.utc)
    settings = Settings(_env_file=None)
    monkeypatch.setattr(
        deal_posting, "fetch_message_hash_sync", lambda **kwargs: "hash"
    )

    with Session(engine) as session:
        deal = _seed_deal(
            session,
            scheduled_at=now - timedelta(minutes=1),
            placement_type="post",
            media_type="image",
            retention_hours=24,
            state=DealState.FUNDED.value,
        )
        channel = session.exec(
            select(Channel).where(Channel.id == deal.channel_id)
        ).one()
        channel.telegram_channel_id = None
        channel.username = "ludex_channel"
        session.add(channel)
        session.commit()

        bot_api = FakeBotApi()
        processed = _post_due_deals(
            db=session, settings=settings, now=now, bot_api=bot_api
        )

        assert processed == 1
        assert bot_api.calls
        assert bot_api.calls[0]["chat_id"] == "@ludex_channel"

    SQLModel.metadata.drop_all(engine)
