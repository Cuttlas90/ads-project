from __future__ import annotations

import logging

from sqlmodel import Session, select

from app.models.deal import Deal
from app.models.user import User
from app.settings import Settings
from shared.telegram.bot_api import BotApiService
from shared.telegram.errors import TelegramApiError, TelegramConfigError

logger = logging.getLogger(__name__)


def notify_deal_funded(*, db: Session, settings: Settings, deal: Deal) -> None:
    message = f"Funds for deal #{deal.id} deposited"
    service = BotApiService(settings)

    for user_id in (deal.advertiser_id, deal.channel_owner_id):
        user = db.exec(select(User).where(User.id == user_id)).first()
        if user is None or user.telegram_user_id is None:
            logger.warning("Skipping funding notification for missing user", extra={"user_id": user_id})
            continue
        try:
            service.send_message(chat_id=user.telegram_user_id, text=message)
        except (TelegramApiError, TelegramConfigError) as exc:
            logger.error("Failed to send funding notification", extra={"user_id": user_id, "error": str(exc)})
