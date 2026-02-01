from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any

from shared.telegram.telethon_client import TelegramClientService


async def fetch_message(client, *, channel, message_id: int):
    try:
        result = await client.get_messages(channel, ids=message_id)
    except Exception:
        return None

    if isinstance(result, list):
        return result[0] if result else None
    return result


def _media_fingerprint(message) -> dict[str, Any]:
    media = getattr(message, "media", None)
    if media is None:
        return {"media_type": None}

    media_type = media.__class__.__name__
    media_id = None
    access_hash = None

    photo = getattr(media, "photo", None)
    document = getattr(media, "document", None)
    if photo is not None:
        media_id = getattr(photo, "id", None)
        access_hash = getattr(photo, "access_hash", None)
    elif document is not None:
        media_id = getattr(document, "id", None)
        access_hash = getattr(document, "access_hash", None)
    else:
        media_id = getattr(media, "id", None)
        access_hash = getattr(media, "access_hash", None)

    return {
        "media_type": media_type,
        "media_id": media_id,
        "media_access_hash": access_hash,
    }


def compute_message_hash(message) -> str:
    payload = {
        "text": getattr(message, "message", None),
        **_media_fingerprint(message),
    }
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def fetch_message_hash_sync(
    *,
    settings,
    channel,
    message_id: int,
) -> str | None:
    service = TelegramClientService(settings)

    async def _run() -> str | None:
        await service.connect()
        client = service.client()
        message = await fetch_message(client, channel=channel, message_id=message_id)
        await service.disconnect()
        if message is None:
            return None
        return compute_message_hash(message)

    try:
        return asyncio.run(_run())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_run())
        finally:
            loop.close()
