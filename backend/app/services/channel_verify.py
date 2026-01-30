from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from telethon.tl import functions

from app.domain.channel_verification import (
    ChannelAccessDenied,
    ChannelBotPermissionDenied,
    ChannelNotFound,
    ChannelVerificationError,
)
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.channel_stats_snapshot import ChannelStatsSnapshot
from app.models.user import User
from app.telegram.permissions import check_bot_permissions
from shared.telegram import TelegramClientService


async def verify_channel(
    *,
    channel_id: int,
    user: User,
    db: Session,
    telegram_client: TelegramClientService,
) -> Channel:
    channel = db.exec(select(Channel).where(Channel.id == channel_id)).first()
    if channel is None:
        raise ChannelNotFound(channel_id)

    if user.id is None:
        raise ChannelAccessDenied(channel_id, user.id)

    membership = (
        db.exec(
            select(ChannelMember)
            .where(ChannelMember.channel_id == channel.id)
            .where(ChannelMember.user_id == user.id)
            .where(ChannelMember.role.in_(["owner", "manager"]))
        )
        .first()
    )
    if membership is None:
        raise ChannelAccessDenied(channel_id, user.id)

    channel_ref = channel.telegram_channel_id or channel.username
    if channel_ref is None:
        raise ChannelVerificationError("Channel is missing Telegram identifiers", channel_id=channel_id)

    await telegram_client.connect()
    try:
        client = telegram_client._get_client()
        permission_result = await check_bot_permissions(client, channel_ref)
        if not permission_result.ok:
            raise ChannelBotPermissionDenied(
                channel_id,
                missing_permissions=list(permission_result.missing_permissions),
            )

        input_entity = await _resolve_input_entity(client, channel_ref)
        full_response = await client(functions.channels.GetFullChannelRequest(channel=input_entity))
        stats_response = await client(functions.stats.GetBroadcastStatsRequest(channel=input_entity))
    except ChannelBotPermissionDenied:
        raise
    except Exception as exc:
        raise ChannelVerificationError(
            "Failed to verify channel with Telegram",
            channel_id=channel_id,
        ) from exc
    finally:
        await telegram_client.disconnect()

    subscribers = _coerce_int(
        getattr(getattr(full_response, "full_chat", None), "participants_count", None)
    )
    avg_views = _coerce_int(
        getattr(getattr(stats_response, "views_per_post", None), "current", None)
    )
    language_stats = _to_dict(getattr(stats_response, "languages_graph", None))
    premium_stats = _to_dict(getattr(stats_response, "premium_graph", None))

    full_chat_id = getattr(getattr(full_response, "full_chat", None), "id", None)
    chat_id, chat_username, chat_title = _extract_chat_info(full_response)

    raw_stats = {
        "full_channel": _to_dict(full_response),
        "statistics": _to_dict(stats_response),
    }

    try:
        if full_chat_id is not None:
            channel.telegram_channel_id = int(full_chat_id)
        elif chat_id is not None:
            channel.telegram_channel_id = int(chat_id)

        if chat_username:
            channel.username = chat_username.lower()
        if chat_title:
            channel.title = chat_title

        channel.is_verified = True

        snapshot = ChannelStatsSnapshot(
            channel_id=channel.id,
            subscribers=subscribers,
            avg_views=avg_views,
            language_stats=language_stats,
            premium_stats=premium_stats,
            raw_stats=raw_stats,
        )
        db.add(snapshot)
        db.add(channel)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ChannelVerificationError(
            "Failed to persist channel verification",
            channel_id=channel_id,
        ) from exc
    except Exception as exc:
        db.rollback()
        raise ChannelVerificationError(
            "Failed to persist channel verification",
            channel_id=channel_id,
        ) from exc

    db.refresh(channel)
    return channel


async def _resolve_input_entity(client, channel_ref):
    get_input_entity = getattr(client, "get_input_entity", None)
    if get_input_entity is None:
        return channel_ref
    return await _maybe_await(get_input_entity(channel_ref))


def _extract_chat_info(full_response) -> tuple[int | None, str | None, str | None]:
    chats = getattr(full_response, "chats", None) or []
    for chat in chats:
        chat_id = getattr(chat, "id", None)
        username = getattr(chat, "username", None)
        title = getattr(chat, "title", None)
        if chat_id is not None or username is not None or title is not None:
            return chat_id, username, title
    return None, None, None


def _to_dict(value):
    if value is None:
        return None
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    return value


def _coerce_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


async def _maybe_await(value):
    if hasattr(value, "__await__"):
        return await value
    return value
