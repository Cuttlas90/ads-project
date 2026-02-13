from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.channel import Channel
from app.models.deal import Deal, DealState
from app.services.bot_notifications import notify_deal_posted
from app.services.deal_fsm import (
    DealAction,
    DealActorRole,
    DealTransitionError,
    apply_transition,
)
from app.services.deal_posting import DealPostingError, publish_deal_post
from app.settings import get_settings
from app.worker.celery_app import celery_app
from shared.db.session import SessionLocal
from shared.telegram.bot_api import BotApiService
from shared.telegram.errors import TelegramApiError, TelegramConfigError

logger = logging.getLogger(__name__)


def _post_due_deals(
    *,
    db: Session,
    settings,
    now: datetime | None = None,
    bot_api: BotApiService | None = None,
) -> int:
    now = now or datetime.now(timezone.utc)
    bot_api = bot_api or BotApiService(settings)

    deals = db.exec(
        select(Deal)
        .where(Deal.scheduled_at.is_not(None))
        .where(Deal.scheduled_at <= now)
        .where(Deal.state.in_([DealState.FUNDED.value, DealState.SCHEDULED.value]))
    ).all()

    processed = 0
    for deal in deals:
        channel = db.exec(select(Channel).where(Channel.id == deal.channel_id)).first()
        if channel is None:
            logger.error("Channel not found for deal", extra={"deal_id": deal.id})
            continue

        notify_posted = False
        try:
            if deal.state == DealState.FUNDED.value:
                apply_transition(
                    db,
                    deal=deal,
                    action=DealAction.schedule.value,
                    actor_id=None,
                    actor_role=DealActorRole.system.value,
                    payload={
                        "scheduled_at": (
                            deal.scheduled_at.isoformat() if deal.scheduled_at else None
                        )
                    },
                )

            if deal.state == DealState.SCHEDULED.value and not deal.posted_message_id:
                publish_deal_post(
                    deal=deal, channel=channel, settings=settings, bot_api=bot_api
                )
                apply_transition(
                    db,
                    deal=deal,
                    action=DealAction.post.value,
                    actor_id=None,
                    actor_role=DealActorRole.system.value,
                    payload={"message_id": deal.posted_message_id},
                )
                notify_posted = True

            db.add(deal)
            processed += 1
        except (
            DealPostingError,
            DealTransitionError,
            TelegramApiError,
            TelegramConfigError,
        ) as exc:
            db.rollback()
            logger.error(
                "Deal posting failed", extra={"deal_id": deal.id, "error": str(exc)}
            )
            continue
        else:
            db.commit()
            if notify_posted:
                notify_deal_posted(db=db, settings=settings, deal=deal)

    return processed


@celery_app.task(name="app.worker.deal_posting.post_due_deals")
def post_due_deals() -> int:
    settings = get_settings()
    if not settings.TELEGRAM_ENABLED:
        return 0

    with SessionLocal() as db:
        return _post_due_deals(db=db, settings=settings)
