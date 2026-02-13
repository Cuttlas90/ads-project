from __future__ import annotations

import logging
from decimal import Decimal

from sqlmodel import Session, select

from app.models.deal import Deal
from app.models.user import User
from app.settings import Settings
from shared.telegram.bot_api import BotApiService
from shared.telegram.errors import TelegramApiError, TelegramConfigError

logger = logging.getLogger(__name__)


def _normalize_user_ids(
    user_ids: tuple[int | None, ...] | list[int | None],
) -> list[int]:
    seen: set[int] = set()
    normalized: list[int] = []
    for user_id in user_ids:
        if user_id is None or user_id in seen:
            continue
        seen.add(user_id)
        normalized.append(user_id)
    return normalized


def _safe_send_to_users(
    *,
    db: Session,
    settings: Settings,
    user_ids: tuple[int | None, ...] | list[int | None],
    message: str,
    event: str,
) -> None:
    resolved_user_ids = _normalize_user_ids(user_ids)
    if not resolved_user_ids:
        return

    try:
        service = BotApiService(settings)
    except (TelegramApiError, TelegramConfigError) as exc:
        logger.error(
            "Failed to initialize bot notification service",
            extra={"event": event, "error": str(exc)},
        )
        return

    for user_id in resolved_user_ids:
        user = db.exec(select(User).where(User.id == user_id)).first()
        if user is None or user.telegram_user_id is None:
            logger.warning(
                "Skipping bot notification for missing user",
                extra={"event": event, "user_id": user_id},
            )
            continue
        try:
            service.send_message(chat_id=user.telegram_user_id, text=message)
        except Exception as exc:
            logger.error(
                "Failed to send bot notification",
                extra={"event": event, "user_id": user_id, "error": str(exc)},
            )


def _deal_participants(deal: Deal) -> tuple[int | None, int | None]:
    return deal.advertiser_id, deal.channel_owner_id


def _amount_line(
    *,
    amount_ton: Decimal | None,
    tx_hash: str | None,
    positive_label: str,
    zero_label: str,
) -> str:
    if amount_ton is None:
        return zero_label
    if amount_ton > 0:
        tx_part = f" TX: {tx_hash}" if tx_hash else ""
        return f"{positive_label}: {amount_ton} TON.{tx_part}"
    return zero_label


def notify_listing_offer_received(
    *, db: Session, settings: Settings, deal: Deal
) -> None:
    message = (
        f"New offer received for your listing. "
        f"Deal #{deal.id} is waiting for your review in the mini app."
    )
    _safe_send_to_users(
        db=db,
        settings=settings,
        user_ids=(deal.channel_owner_id,),
        message=message,
        event="listing_offer_received",
    )


def notify_campaign_offer_received(
    *,
    db: Session,
    settings: Settings,
    advertiser_id: int | None,
    campaign_id: int,
    application_id: int,
) -> None:
    message = (
        f"New campaign offer received. "
        f"Campaign #{campaign_id}, offer #{application_id} is waiting for your review."
    )
    _safe_send_to_users(
        db=db,
        settings=settings,
        user_ids=(advertiser_id,),
        message=message,
        event="campaign_offer_received",
    )


def notify_campaign_offer_accepted(
    *, db: Session, settings: Settings, deal: Deal
) -> None:
    message = (
        f"Your campaign offer was accepted. "
        f"Deal #{deal.id} has been created and is now open for negotiation."
    )
    _safe_send_to_users(
        db=db,
        settings=settings,
        user_ids=(deal.channel_owner_id,),
        message=message,
        event="campaign_offer_accepted",
    )


def notify_deal_offer_accepted(
    *, db: Session, settings: Settings, deal: Deal, accepted_by_role: str
) -> None:
    actor = accepted_by_role.replace("_", " ")
    message = (
        f"Offer accepted for deal #{deal.id} by {actor}. "
        "Deal moved to creative-approved stage."
    )
    _safe_send_to_users(
        db=db,
        settings=settings,
        user_ids=_deal_participants(deal),
        message=message,
        event="deal_offer_accepted",
    )


def notify_deal_funded(*, db: Session, settings: Settings, deal: Deal) -> None:
    message = f"Funds for deal #{deal.id} were deposited into escrow."
    _safe_send_to_users(
        db=db,
        settings=settings,
        user_ids=_deal_participants(deal),
        message=message,
        event="deal_funded",
    )


def notify_deal_posted(*, db: Session, settings: Settings, deal: Deal) -> None:
    placement = (
        deal.placement_type or deal.ad_type or "post"
    ).strip().lower() or "post"
    message_id = deal.posted_message_id or "n/a"
    message = (
        f"Content posted for deal #{deal.id}. "
        f"Placement: {placement}. Post ID: {message_id}."
    )
    _safe_send_to_users(
        db=db,
        settings=settings,
        user_ids=_deal_participants(deal),
        message=message,
        event="deal_posted",
    )


def notify_deal_released(
    *,
    db: Session,
    settings: Settings,
    deal: Deal,
    released_amount_ton: Decimal | None,
    tx_hash: str | None,
) -> None:
    amount_line = _amount_line(
        amount_ton=released_amount_ton,
        tx_hash=tx_hash,
        positive_label="Released payout",
        zero_label="Release completed with zero payout transfer.",
    )
    message = f"Escrow released for deal #{deal.id}. {amount_line}"
    _safe_send_to_users(
        db=db,
        settings=settings,
        user_ids=_deal_participants(deal),
        message=message,
        event="deal_released",
    )


def notify_deal_refunded(
    *,
    db: Session,
    settings: Settings,
    deal: Deal,
    refunded_amount_ton: Decimal | None,
    tx_hash: str | None,
    reason: str | None = None,
) -> None:
    amount_line = _amount_line(
        amount_ton=refunded_amount_ton,
        tx_hash=tx_hash,
        positive_label="Refund amount",
        zero_label="Refund completed with zero transfer.",
    )
    reason_line = f" Reason: {reason}." if reason else ""
    message = f"Deal #{deal.id} refunded.{reason_line} {amount_line}"
    _safe_send_to_users(
        db=db,
        settings=settings,
        user_ids=_deal_participants(deal),
        message=message,
        event="deal_refunded",
    )
