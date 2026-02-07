from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.bot_api import BotApiService
from app.settings import Settings
from shared.db.models.deal import Deal, DealState
from shared.db.models.deal_event import DealEvent
from shared.db.models.deal_message_selection import DealMessageSelection
from shared.db.models.users import User

DEAL_MENU_STATES = {DealState.DRAFT.value, DealState.NEGOTIATION.value}


@dataclass(frozen=True)
class IncomingMessage:
    update_id: int
    chat_id: int
    telegram_user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    language_code: str | None
    is_premium: bool | None
    text: str | None
    is_text: bool


def parse_update(update: dict[str, Any]) -> IncomingMessage | None:
    message = update.get("message")
    if not isinstance(message, dict):
        return None
    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    chat_id = chat.get("id")
    telegram_user_id = sender.get("id")
    if chat_id is None or telegram_user_id is None:
        return None
    text = message.get("text")
    is_premium = sender.get("is_premium")
    return IncomingMessage(
        update_id=update.get("update_id"),
        chat_id=chat_id,
        telegram_user_id=telegram_user_id,
        username=sender.get("username"),
        first_name=sender.get("first_name"),
        last_name=sender.get("last_name"),
        language_code=sender.get("language_code"),
        is_premium=is_premium if isinstance(is_premium, bool) else None,
        text=text,
        is_text=isinstance(text, str),
    )


def build_reply_keyboard(options: list[str]) -> dict[str, Any]:
    keyboard = [[{"text": option}] for option in options]
    return {"keyboard": keyboard, "resize_keyboard": True, "one_time_keyboard": True}


def _upsert_user_from_incoming(*, db: Session, incoming: IncomingMessage) -> User:
    now = datetime.now(timezone.utc)
    user = db.exec(select(User).where(User.telegram_user_id == incoming.telegram_user_id)).first()
    if user is None:
        user = User(
            telegram_user_id=incoming.telegram_user_id,
            username=incoming.username,
            first_name=incoming.first_name,
            last_name=incoming.last_name,
            language_code=incoming.language_code,
            is_premium=incoming.is_premium,
            last_login_at=now,
        )
    else:
        user.username = incoming.username
        user.first_name = incoming.first_name
        user.last_name = incoming.last_name
        user.language_code = incoming.language_code
        user.is_premium = incoming.is_premium
        user.last_login_at = now

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        user = db.exec(select(User).where(User.telegram_user_id == incoming.telegram_user_id)).first()
        if user is None:
            raise RuntimeError("Failed to register user from /start")
        user.username = incoming.username
        user.first_name = incoming.first_name
        user.last_name = incoming.last_name
        user.language_code = incoming.language_code
        user.is_premium = incoming.is_premium
        user.last_login_at = now
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        db.refresh(user)

    return user


def handle_update(
    *,
    update: dict[str, Any],
    db: Session,
    bot_api: BotApiService,
    settings: Settings,
) -> None:
    incoming = parse_update(update)
    if incoming is None:
        return

    text = (incoming.text or "").strip() if incoming.is_text else ""
    if text.startswith("/start"):
        _upsert_user_from_incoming(db=db, incoming=incoming)
        bot_api.send_message(chat_id=incoming.chat_id, text="Welcome! Use /deals to open your active deals.")
        return

    user = db.exec(select(User).where(User.telegram_user_id == incoming.telegram_user_id)).first()
    if user is None:
        bot_api.send_message(chat_id=incoming.chat_id, text="Please run /start to register first.")
        return

    if not incoming.is_text:
        bot_api.send_message(chat_id=incoming.chat_id, text="Text only, please.")
        return

    if not text:
        bot_api.send_message(chat_id=incoming.chat_id, text="Text only, please.")
        return

    if text.startswith("/deals"):
        _handle_deals_menu(db=db, bot_api=bot_api, user_id=user.id, chat_id=incoming.chat_id)
        return

    if text.startswith("/deal"):
        _handle_deal_select(
            db=db,
            bot_api=bot_api,
            user_id=user.id,
            chat_id=incoming.chat_id,
            text=text,
        )
        return

    _handle_forward_message(
        db=db,
        bot_api=bot_api,
        user_id=user.id,
        chat_id=incoming.chat_id,
        text=text,
    )


def _handle_deals_menu(*, db: Session, bot_api: BotApiService, user_id: int, chat_id: int) -> None:
    deals = db.exec(
        select(Deal)
        .where(Deal.state.in_(DEAL_MENU_STATES))
        .where((Deal.advertiser_id == user_id) | (Deal.channel_owner_id == user_id))
        .order_by(Deal.id.desc())
    ).all()
    if not deals:
        bot_api.send_message(chat_id=chat_id, text="No active deals to message.")
        return
    options = [f"/deal {deal.id}" for deal in deals if deal.id is not None]
    bot_api.send_message(
        chat_id=chat_id,
        text="Select a deal to message:",
        reply_markup=build_reply_keyboard(options),
    )


def _handle_deal_select(
    *,
    db: Session,
    bot_api: BotApiService,
    user_id: int,
    chat_id: int,
    text: str,
) -> None:
    parts = text.split()
    if len(parts) < 2:
        bot_api.send_message(chat_id=chat_id, text="Usage: /deal <id>")
        return

    try:
        deal_id = int(parts[1])
    except ValueError:
        bot_api.send_message(chat_id=chat_id, text="Invalid deal id")
        return

    deal = db.exec(select(Deal).where(Deal.id == deal_id)).first()
    if deal is None:
        bot_api.send_message(chat_id=chat_id, text="Deal not found")
        return

    if deal.state not in DEAL_MENU_STATES:
        bot_api.send_message(chat_id=chat_id, text="Deal is not open for messaging")
        return

    if user_id not in {deal.advertiser_id, deal.channel_owner_id}:
        bot_api.send_message(chat_id=chat_id, text="Not authorized for this deal")
        return

    selection = db.exec(select(DealMessageSelection).where(DealMessageSelection.user_id == user_id)).first()
    if selection is None:
        selection = DealMessageSelection(user_id=user_id, deal_id=deal.id)
    else:
        selection.deal_id = deal.id
        selection.selected_at = datetime.now(timezone.utc)

    db.add(selection)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        bot_api.send_message(chat_id=chat_id, text="Failed to select deal")
        return

    bot_api.send_message(chat_id=chat_id, text=f"Deal #{deal.id} selected. Send your message.")


def _handle_forward_message(
    *,
    db: Session,
    bot_api: BotApiService,
    user_id: int,
    chat_id: int,
    text: str,
) -> None:
    selection = db.exec(select(DealMessageSelection).where(DealMessageSelection.user_id == user_id)).first()
    if selection is None:
        bot_api.send_message(chat_id=chat_id, text="Please run /deals to select a deal first.")
        return

    deal = db.exec(select(Deal).where(Deal.id == selection.deal_id)).first()
    if deal is None or deal.state not in DEAL_MENU_STATES:
        db.delete(selection)
        db.commit()
        bot_api.send_message(chat_id=chat_id, text="Deal is no longer available. Use /deals again.")
        return

    if user_id not in {deal.advertiser_id, deal.channel_owner_id}:
        db.delete(selection)
        db.commit()
        bot_api.send_message(chat_id=chat_id, text="Not authorized for this deal")
        return

    recipient_id = deal.channel_owner_id if user_id == deal.advertiser_id else deal.advertiser_id
    recipient = db.exec(select(User).where(User.id == recipient_id)).first()
    if recipient is None or recipient.telegram_user_id is None:
        bot_api.send_message(chat_id=chat_id, text="Recipient not available")
        return

    event = DealEvent(
        deal_id=deal.id,
        actor_id=user_id,
        event_type="message",
        payload={"text": text, "to_user_id": recipient.id},
    )
    db.add(event)

    db.delete(selection)
    db.commit()

    shortcut = f"/deal {deal.id}"
    outbound_text = f"Deal #{deal.id}: {text}"
    bot_api.send_message(
        chat_id=recipient.telegram_user_id,
        text=outbound_text,
        reply_markup=build_reply_keyboard([shortcut]),
    )
