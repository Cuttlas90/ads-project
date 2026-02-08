from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone
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


async def fetch_story(client, *, channel, story_id: int):
    try:
        from telethon import functions
    except Exception:
        return None

    try:
        entity = await client.get_input_entity(channel)
        response = await client(functions.stories.GetStoriesByIDRequest(peer=entity, id=[story_id]))
    except Exception:
        return None

    stories = getattr(response, "stories", None)
    if not isinstance(stories, list) or not stories:
        return None
    return stories[0]


def _ensure_aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


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


def _story_media_fingerprint(story) -> dict[str, Any]:
    media = getattr(story, "media", None)
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


def compute_story_hash(story) -> str:
    payload = {
        "story_id": getattr(story, "id", None),
        "caption": getattr(story, "caption", None),
        **_story_media_fingerprint(story),
    }
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _is_feed_post(message) -> bool:
    if message is None:
        return False
    if getattr(message, "action", None) is not None:
        return False
    has_text = bool(getattr(message, "message", None))
    has_media = getattr(message, "media", None) is not None
    return has_text or has_media


async def has_additional_posts(
    client,
    *,
    channel,
    start_at: datetime,
    end_at: datetime,
    exclude_message_id: int,
) -> bool:
    start_window = _ensure_aware_utc(start_at)
    end_window = _ensure_aware_utc(end_at)
    if start_window is None or end_window is None:
        return False

    try:
        async for message in client.iter_messages(channel, offset_date=end_window, limit=500):
            if message is None:
                continue
            message_date = _ensure_aware_utc(getattr(message, "date", None))
            if message_date is None:
                continue
            if message_date < start_window:
                break
            if message_date > end_window:
                continue
            if int(getattr(message, "id", 0) or 0) == exclude_message_id:
                continue
            if _is_feed_post(message):
                return True
    except Exception:
        return False

    return False


async def has_additional_stories(
    client,
    *,
    channel,
    start_at: datetime,
    end_at: datetime,
    exclude_story_id: int,
) -> bool:
    start_window = _ensure_aware_utc(start_at)
    end_window = _ensure_aware_utc(end_at)
    if start_window is None or end_window is None:
        return False

    try:
        from telethon import functions
    except Exception:
        return False

    try:
        entity = await client.get_input_entity(channel)
        response = await client(functions.stories.GetPeerStoriesRequest(peer=entity))
    except Exception:
        return False

    peer_stories = getattr(response, "stories", None)
    stories = getattr(peer_stories, "stories", None)
    if not isinstance(stories, list):
        return False

    for story in stories:
        story_id = int(getattr(story, "id", 0) or 0)
        if story_id == exclude_story_id:
            continue
        story_date = _ensure_aware_utc(getattr(story, "date", None))
        if story_date is None:
            continue
        if start_window <= story_date <= end_window:
            return True

    return False


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


def fetch_story_hash_sync(
    *,
    settings,
    channel,
    story_id: int,
) -> str | None:
    service = TelegramClientService(settings)

    async def _run() -> str | None:
        await service.connect()
        client = service.client()
        story = await fetch_story(client, channel=channel, story_id=story_id)
        await service.disconnect()
        if story is None:
            return None
        return compute_story_hash(story)

    try:
        return asyncio.run(_run())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_run())
        finally:
            loop.close()


def has_additional_posts_sync(
    *,
    settings,
    channel,
    start_at: datetime,
    end_at: datetime,
    exclude_message_id: int,
) -> bool:
    service = TelegramClientService(settings)

    async def _run() -> bool:
        await service.connect()
        client = service.client()
        result = await has_additional_posts(
            client,
            channel=channel,
            start_at=start_at,
            end_at=end_at,
            exclude_message_id=exclude_message_id,
        )
        await service.disconnect()
        return result

    try:
        return bool(asyncio.run(_run()))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return bool(loop.run_until_complete(_run()))
        finally:
            loop.close()


def has_additional_stories_sync(
    *,
    settings,
    channel,
    start_at: datetime,
    end_at: datetime,
    exclude_story_id: int,
) -> bool:
    service = TelegramClientService(settings)

    async def _run() -> bool:
        await service.connect()
        client = service.client()
        result = await has_additional_stories(
            client,
            channel=channel,
            start_at=start_at,
            end_at=end_at,
            exclude_story_id=exclude_story_id,
        )
        await service.disconnect()
        return result

    try:
        return bool(asyncio.run(_run()))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return bool(loop.run_until_complete(_run()))
        finally:
            loop.close()
