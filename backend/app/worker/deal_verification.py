from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.domain.escrow_fsm import EscrowState
from app.models.channel import Channel
from app.models.deal import Deal, DealState
from app.models.deal_escrow import DealEscrow
from app.models.user import User
from app.services.deal_fsm import DealAction, DealActorRole, DealTransitionError, apply_transition
from app.services.telegram.message_inspect import (
    fetch_message_hash_sync,
    fetch_story_hash_sync,
    has_additional_posts_sync,
    has_additional_stories_sync,
)
from app.services.ton.payouts import PayoutError, ensure_refund, ensure_release
from app.services.ton.transfers import TonTransferError, send_ton_transfer
from app.settings import get_settings
from app.worker.celery_app import celery_app
from shared.db.session import SessionLocal

logger = logging.getLogger(__name__)


def _ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _resolve_placement_type(deal: Deal) -> str:
    placement_type = (deal.placement_type or "").strip().lower()
    if placement_type in {"post", "story"}:
        return placement_type

    fallback = (deal.ad_type or "").strip().lower()
    if fallback in {"post", "story"}:
        return fallback
    return "post"


def _retention_deadline(deal: Deal, *, default_hours: int) -> datetime | None:
    if deal.posted_at is None:
        return None
    posted_at = _ensure_aware_utc(deal.posted_at)
    retention_hours = deal.retention_hours or deal.verification_window_hours or default_hours
    retention_hours = max(int(retention_hours), 1)
    return posted_at + timedelta(hours=retention_hours)


def _exclusivity_deadline(deal: Deal) -> datetime | None:
    if deal.posted_at is None:
        return None
    posted_at = _ensure_aware_utc(deal.posted_at)
    exclusive_hours = max(int(deal.exclusive_hours or 0), 0)
    return posted_at + timedelta(hours=exclusive_hours)


def _verification_deadline(deal: Deal, *, default_hours: int) -> datetime | None:
    retention = _retention_deadline(deal, default_hours=default_hours)
    exclusivity = _exclusivity_deadline(deal)
    if retention is None:
        return None
    if exclusivity is None:
        return retention
    return max(retention, exclusivity)


def _verify_posted_deals(
    *,
    db: Session,
    settings,
    now: datetime | None = None,
    fetch_hash_fn=fetch_message_hash_sync,
    fetch_story_hash_fn=fetch_story_hash_sync,
    has_post_breach_fn=has_additional_posts_sync,
    has_story_breach_fn=has_additional_stories_sync,
    transfer_fn=send_ton_transfer,
) -> int:
    now = now or datetime.now(timezone.utc)
    now = _ensure_aware_utc(now)

    deals = db.exec(select(Deal).where(Deal.state == DealState.POSTED.value)).all()
    processed = 0

    for deal in deals:
        if not deal.posted_message_id or deal.posted_at is None:
            continue

        verification_deadline = _verification_deadline(
            deal,
            default_hours=settings.VERIFICATION_WINDOW_DEFAULT_HOURS,
        )
        retention_deadline = _retention_deadline(
            deal,
            default_hours=settings.VERIFICATION_WINDOW_DEFAULT_HOURS,
        )
        exclusivity_deadline = _exclusivity_deadline(deal)
        if verification_deadline is None or retention_deadline is None or exclusivity_deadline is None:
            continue

        channel = db.exec(select(Channel).where(Channel.id == deal.channel_id)).first()
        if channel is None:
            logger.error("Channel not found for verification", extra={"deal_id": deal.id})
            continue

        escrow = db.exec(select(DealEscrow).where(DealEscrow.deal_id == deal.id)).first()
        if escrow is None:
            logger.error("Escrow not found for verification", extra={"deal_id": deal.id})
            continue
        if escrow.state != EscrowState.FUNDED.value:
            logger.error("Escrow not funded", extra={"deal_id": deal.id, "state": escrow.state})
            continue

        chat_id = channel.telegram_channel_id or channel.username
        if not chat_id:
            logger.error("Channel missing telegram identifier", extra={"deal_id": deal.id})
            continue

        placement_type = _resolve_placement_type(deal)
        posted_message_id = int(deal.posted_message_id)

        tamper_reason: str | None = None
        if now <= retention_deadline:
            try:
                if placement_type == "story":
                    current_hash = fetch_story_hash_fn(
                        settings=settings,
                        channel=chat_id,
                        story_id=posted_message_id,
                    )
                else:
                    current_hash = fetch_hash_fn(
                        settings=settings,
                        channel=chat_id,
                        message_id=posted_message_id,
                    )
            except Exception as exc:
                logger.error("Verification fetch failed", extra={"deal_id": deal.id, "error": str(exc)})
                continue

            if current_hash is None:
                tamper_reason = "missing_content"
            elif deal.posted_content_hash and current_hash != deal.posted_content_hash:
                tamper_reason = "content_changed"

        exclusivity_active = now <= exclusivity_deadline and max(int(deal.exclusive_hours or 0), 0) > 0
        if tamper_reason is None and exclusivity_active:
            posted_at = _ensure_aware_utc(deal.posted_at)
            try:
                if placement_type == "story":
                    breached = has_story_breach_fn(
                        settings=settings,
                        channel=chat_id,
                        start_at=posted_at,
                        end_at=min(now, exclusivity_deadline),
                        exclude_story_id=posted_message_id,
                    )
                else:
                    breached = has_post_breach_fn(
                        settings=settings,
                        channel=chat_id,
                        start_at=posted_at,
                        end_at=min(now, exclusivity_deadline),
                        exclude_message_id=posted_message_id,
                    )
            except Exception as exc:
                logger.error("Exclusivity check failed", extra={"deal_id": deal.id, "error": str(exc)})
                continue

            if breached:
                tamper_reason = "exclusivity_breach"

        if tamper_reason is None and now < verification_deadline:
            continue

        try:
            if tamper_reason is not None:
                apply_transition(
                    db,
                    deal=deal,
                    action=DealAction.refund.value,
                    actor_id=None,
                    actor_role=DealActorRole.system.value,
                    payload={"reason": tamper_reason},
                )
                advertiser = db.exec(select(User).where(User.id == deal.advertiser_id)).first()
                if advertiser is None:
                    raise PayoutError("Advertiser not found")
                ensure_refund(
                    db=db,
                    deal=deal,
                    escrow=escrow,
                    advertiser=advertiser,
                    settings=settings,
                    transfer_fn=transfer_fn,
                )
            else:
                deal.verified_at = now
                apply_transition(
                    db,
                    deal=deal,
                    action=DealAction.verify.value,
                    actor_id=None,
                    actor_role=DealActorRole.system.value,
                    payload={"verified_at": now.isoformat()},
                )
                owner = db.exec(select(User).where(User.id == deal.channel_owner_id)).first()
                if owner is None:
                    raise PayoutError("Channel owner not found")
                ensure_release(
                    db=db,
                    deal=deal,
                    escrow=escrow,
                    owner=owner,
                    settings=settings,
                    transfer_fn=transfer_fn,
                )

            db.add(deal)
            db.add(escrow)
            db.commit()
            processed += 1
        except (DealTransitionError, PayoutError, TonTransferError) as exc:
            db.rollback()
            logger.error("Verification processing failed", extra={"deal_id": deal.id, "error": str(exc)})
            continue

    return processed


@celery_app.task(name="app.worker.deal_verification.verify_posted_deals")
def verify_posted_deals() -> int:
    settings = get_settings()
    if not settings.TELEGRAM_ENABLED or not settings.TON_ENABLED:
        return 0

    with SessionLocal() as db:
        return _verify_posted_deals(db=db, settings=settings)
