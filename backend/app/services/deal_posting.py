from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from app.models.channel import Channel
from app.models.deal import Deal
from app.services.telegram.message_inspect import fetch_message_hash_sync, fetch_story_hash_sync
from app.settings import Settings
from shared.telegram.bot_api import BotApiService


class DealPostingError(RuntimeError):
    pass


def _resolve_chat_id(channel: Channel) -> int | str:
    if channel.telegram_channel_id is not None:
        return channel.telegram_channel_id
    if channel.username:
        return channel.username
    raise DealPostingError("Channel is missing telegram identifier")


def _derive_verification_window_hours(deal: Deal, settings: Settings) -> int:
    if deal.verification_window_hours is not None:
        return int(deal.verification_window_hours)
    if deal.retention_hours is not None and int(deal.retention_hours) > 0:
        return int(deal.retention_hours)
    if isinstance(deal.posting_params, dict):
        raw = deal.posting_params.get("verification_window_hours")
        if raw is not None:
            try:
                value = int(raw)
            except (TypeError, ValueError):
                value = settings.VERIFICATION_WINDOW_DEFAULT_HOURS
            else:
                if value <= 0:
                    value = settings.VERIFICATION_WINDOW_DEFAULT_HOURS
            return value
    return settings.VERIFICATION_WINDOW_DEFAULT_HOURS


def _payload_hash(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _resolve_placement_type(deal: Deal) -> str:
    placement_type = (deal.placement_type or "").strip().lower()
    if placement_type in {"post", "story"}:
        return placement_type

    fallback = (deal.ad_type or "").strip().lower()
    if fallback in {"post", "story"}:
        return fallback
    return "post"


def _extract_story_id(result: dict) -> int:
    for key in ("story_id", "id"):
        value = result.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    raise DealPostingError("Bot API story response missing story id")


def publish_deal_post(
    *,
    deal: Deal,
    channel: Channel,
    settings: Settings,
    bot_api: BotApiService,
) -> dict[str, object]:
    chat_id = _resolve_chat_id(channel)
    placement_type = _resolve_placement_type(deal)
    media_type = deal.creative_media_type

    if placement_type == "story":
        if media_type not in {"image", "video"}:
            raise DealPostingError("Story placement requires image or video creative")
        response = bot_api.post_story(
            media_type=media_type,
            media=deal.creative_media_ref,
            caption=deal.creative_text,
        )
    else:
        if media_type == "image":
            response = bot_api.send_photo(
                chat_id=chat_id,
                photo=deal.creative_media_ref,
                caption=deal.creative_text,
            )
        elif media_type == "video":
            response = bot_api.send_video(
                chat_id=chat_id,
                video=deal.creative_media_ref,
                caption=deal.creative_text,
            )
        else:
            response = bot_api.send_message(
                chat_id=chat_id,
                text=deal.creative_text,
            )

    result = response.get("result") if isinstance(response, dict) else None
    if not isinstance(result, dict):
        raise DealPostingError("Bot API response missing result payload")

    if placement_type == "story":
        message_id = _extract_story_id(result)
        content_hash = fetch_story_hash_sync(settings=settings, channel=chat_id, story_id=message_id)
    else:
        if "message_id" not in result:
            raise DealPostingError("Bot API response missing message_id")
        message_id = int(result["message_id"])
        content_hash = fetch_message_hash_sync(settings=settings, channel=chat_id, message_id=message_id)

    if content_hash is None:
        content_hash = _payload_hash(
            {
                "placement_type": placement_type,
                "text": deal.creative_text,
                "media_type": deal.creative_media_type,
                "media_ref": deal.creative_media_ref,
            }
        )

    deal.posted_message_id = str(message_id)
    deal.posted_content_hash = content_hash
    deal.posted_at = datetime.now(timezone.utc)
    deal.verification_window_hours = _derive_verification_window_hours(deal, settings)

    return {
        "message_id": message_id,
        "content_hash": content_hash,
    }
