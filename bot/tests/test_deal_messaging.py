from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, select

from app.deal_messaging import handle_update
from app.settings import Settings
from shared.db.base import SQLModel
from shared.db.models.deal import Deal, DealSourceType, DealState
from shared.db.models.deal_event import DealEvent
from shared.db.models.deal_message_selection import DealMessageSelection
from shared.db.models.users import User


class FakeBotApi:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    def send_message(self, **kwargs):
        self.sent.append(kwargs)
        return {"ok": True}


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


def _make_update(user_id: int, text: str | None) -> dict:
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "chat": {"id": user_id},
            "from": {"id": user_id},
            "text": text,
        },
    }


def _seed_deal(session: Session, *, deal_id: int = 1) -> tuple[User, User, Deal]:
    advertiser = User(telegram_user_id=111, username="adv")
    owner = User(telegram_user_id=222, username="owner")
    session.add(advertiser)
    session.add(owner)
    session.flush()

    deal = Deal(
        id=deal_id,
        source_type=DealSourceType.LISTING.value,
        advertiser_id=advertiser.id,
        channel_id=1,
        channel_owner_id=owner.id,
        listing_id=1,
        listing_format_id=1,
        price_ton=Decimal("10.00"),
        ad_type="Post",
        creative_text="Hello",
        creative_media_type="image",
        creative_media_ref="ref",
        posting_params=None,
        state=DealState.DRAFT.value,
    )
    session.add(deal)
    session.commit()
    session.refresh(deal)
    return advertiser, owner, deal


def test_unregistered_user_prompt(db_engine) -> None:
    bot = FakeBotApi()
    settings = Settings(_env_file=None, TELEGRAM_BOT_TOKEN="token")

    with Session(db_engine) as session:
        handle_update(update=_make_update(555, "/deals"), db=session, bot_api=bot, settings=settings)

    assert bot.sent[-1]["text"] == "Please run /start to register first."


def test_start_registers_user(db_engine) -> None:
    bot = FakeBotApi()
    settings = Settings(_env_file=None, TELEGRAM_BOT_TOKEN="token")

    with Session(db_engine) as session:
        handle_update(update=_make_update(555, "/start"), db=session, bot_api=bot, settings=settings)
        user = session.exec(select(User).where(User.telegram_user_id == 555)).first()
        assert user is not None

    assert bot.sent[-1]["text"] == "Welcome! Use /deals to open your active deals."


def test_non_text_message_rejected(db_engine) -> None:
    bot = FakeBotApi()
    settings = Settings(_env_file=None, TELEGRAM_BOT_TOKEN="token")

    with Session(db_engine) as session:
        user = User(telegram_user_id=111, username="adv")
        session.add(user)
        session.commit()

        update = _make_update(111, None)
        update["message"].pop("text", None)
        handle_update(update=update, db=session, bot_api=bot, settings=settings)

    assert bot.sent[-1]["text"] == "Text only, please."


def test_deals_menu_lists_active_deals(db_engine) -> None:
    bot = FakeBotApi()
    settings = Settings(_env_file=None, TELEGRAM_BOT_TOKEN="token")

    with Session(db_engine) as session:
        advertiser, _, deal = _seed_deal(session)

        handle_update(update=_make_update(advertiser.telegram_user_id, "/deals"), db=session, bot_api=bot, settings=settings)

    assert bot.sent[-1]["text"] == "Select a deal to message:"
    assert bot.sent[-1]["reply_markup"]["keyboard"][0][0]["text"] == "/deal 1"


def test_deal_selection_and_message_forward(db_engine) -> None:
    bot = FakeBotApi()
    settings = Settings(_env_file=None, TELEGRAM_BOT_TOKEN="token")

    with Session(db_engine) as session:
        advertiser, owner, deal = _seed_deal(session, deal_id=42)

        handle_update(update=_make_update(advertiser.telegram_user_id, "/deal 42"), db=session, bot_api=bot, settings=settings)
        selection = session.exec(
            select(DealMessageSelection).where(DealMessageSelection.user_id == advertiser.id)
        ).first()
        assert selection is not None

        handle_update(update=_make_update(advertiser.telegram_user_id, "Hello"), db=session, bot_api=bot, settings=settings)
        selection = session.exec(
            select(DealMessageSelection).where(DealMessageSelection.user_id == advertiser.id)
        ).first()
        assert selection is None

        events = session.exec(select(DealEvent)).all()
        assert events

    outbound = bot.sent[-1]
    assert outbound["chat_id"] == owner.telegram_user_id
    assert outbound["text"].startswith("Deal #42:")
    assert "/deal 42" in outbound["reply_markup"]["keyboard"][0][0]["text"]
