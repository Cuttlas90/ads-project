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
from app.services.telegram.message_inspect import fetch_message_hash_sync
from app.services.ton.payouts import PayoutError, ensure_refund, ensure_release
from app.services.ton.transfers import TonTransferError, send_ton_transfer
from app.settings import get_settings
from app.worker.celery_app import celery_app
from shared.db.session import SessionLocal

logger = logging.getLogger(__name__)


def _verification_window_deadline(deal: Deal, *, default_hours: int) -> datetime | None:
    if deal.posted_at is None:
        return None
    posted_at = deal.posted_at
    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)
    window = deal.verification_window_hours or default_hours
    return posted_at + timedelta(hours=int(window))


def _verify_posted_deals(
    *,
    db: Session,
    settings,
    now: datetime | None = None,
    fetch_hash_fn=fetch_message_hash_sync,
    transfer_fn=send_ton_transfer,
) -> int:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    deals = db.exec(select(Deal).where(Deal.state == DealState.POSTED.value)).all()
    processed = 0

    for deal in deals:
        if not deal.posted_message_id or deal.posted_at is None:
            continue

        deadline = _verification_window_deadline(deal, default_hours=settings.VERIFICATION_WINDOW_DEFAULT_HOURS)
        if deadline is None or now < deadline:
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

        try:
            current_hash = fetch_hash_fn(
                settings=settings,
                channel=chat_id,
                message_id=int(deal.posted_message_id),
            )
        except Exception as exc:
            logger.error("Verification fetch failed", extra={"deal_id": deal.id, "error": str(exc)})
            continue

        tampered = current_hash is None or (deal.posted_content_hash and current_hash != deal.posted_content_hash)

        try:
            if tampered:
                apply_transition(
                    db,
                    deal=deal,
                    action=DealAction.refund.value,
                    actor_id=None,
                    actor_role=DealActorRole.system.value,
                    payload={"reason": "tampered"},
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
