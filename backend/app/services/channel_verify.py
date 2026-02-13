from __future__ import annotations

import base64
import logging
from typing import Any

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
from shared.telegram import BotApiService, TelegramClientService
from shared.telegram.errors import TelegramAuthorizationError

logger = logging.getLogger(__name__)


def _to_bot_api_chat_id(chat_id: int) -> int:
    # Telethon channel ids are typically positive; Bot API channel ids are -100-prefixed.
    if 0 < chat_id < 1_000_000_000_000:
        return -1_000_000_000_000 - chat_id
    return chat_id


async def verify_channel(
    *,
    channel_id: int,
    user: User,
    db: Session,
    telegram_client: TelegramClientService,
    bot_api: BotApiService,
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

    # Prefer username when available; it is stable for both Bot API and Telethon resolution.
    channel_ref = channel.username or channel.telegram_channel_id
    if channel_ref is None:
        raise ChannelVerificationError("Channel is missing Telegram identifiers", channel_id=channel_id)

    permission_result = await check_bot_permissions(bot_api, channel_ref)
    if not permission_result.ok:
        _log_phase(
            channel_id=channel_id,
            phase="bot_check",
            status="failed",
            reason="bot_permission_denied",
        )
        raise ChannelBotPermissionDenied(
            channel_id,
            missing_permissions=list(permission_result.missing_permissions),
        )
    _log_phase(channel_id=channel_id, phase="bot_check", status="ok")

    boosts_status = None
    statistics_payload: dict[str, Any] = {}
    phase = "telethon_connect"
    try:
        _log_phase(channel_id=channel_id, phase=phase, status="start")
        await telegram_client.connect()

        phase = "telethon_auth"
        _log_phase(channel_id=channel_id, phase=phase, status="start")
        await telegram_client.require_authorized()
        _log_phase(channel_id=channel_id, phase=phase, status="ok")

        phase = "stats_fetch"
        _log_phase(channel_id=channel_id, phase=phase, status="start")
        client = telegram_client.client()
        input_entity = await _resolve_input_entity(client, channel_ref)
        full_response = await client(functions.channels.GetFullChannelRequest(channel=input_entity))
        stats_response = await client(functions.stats.GetBroadcastStatsRequest(channel=input_entity))
        _log_phase(channel_id=channel_id, phase=phase, status="ok")

        phase = "stats_async_graph_fetch"
        _log_phase(channel_id=channel_id, phase=phase, status="start")
        try:
            statistics_payload = _to_dict(stats_response) or {}
            statistics_payload = await _resolve_async_graphs(
                client=client,
                payload=statistics_payload,
                channel_id=channel_id,
            )
            _log_phase(channel_id=channel_id, phase=phase, status="ok")
        except Exception as exc:
            _log_phase(
                channel_id=channel_id,
                phase=phase,
                status="failed",
                reason="async_graph_resolution_failed",
                error=exc,
            )
            statistics_payload = _to_dict(stats_response) or {}

        # Boost status provides premium audience metrics when broadcast stats omit premium graph.
        phase = "boosts_fetch"
        _log_phase(channel_id=channel_id, phase=phase, status="start")
        try:
            boosts_status = await client(functions.premium.GetBoostsStatusRequest(peer=input_entity))
            _log_phase(channel_id=channel_id, phase=phase, status="ok")
        except Exception as exc:
            _log_phase(
                channel_id=channel_id,
                phase=phase,
                status="failed",
                reason="boosts_status_failed",
                error=exc,
            )
    except TelegramAuthorizationError as exc:
        _log_phase(
            channel_id=channel_id,
            phase=phase,
            status="failed",
            reason="telethon_unauthorized",
            error=exc,
        )
        raise ChannelVerificationError(str(exc), channel_id=channel_id) from exc
    except ChannelVerificationError:
        raise
    except Exception as exc:
        reason = (
            "telethon_connect_failed"
            if phase == "telethon_connect"
            else "telethon_stats_failed"
        )
        _log_phase(
            channel_id=channel_id,
            phase=phase,
            status="failed",
            reason=reason,
            error=exc,
        )
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
    boosts_status_raw = _to_dict(boosts_status)
    language_stats = _to_dict(statistics_payload.get("languages_graph"))
    premium_stats = _extract_premium_stats(
        premium_graph=statistics_payload.get("premium_graph"),
        boosts_status=boosts_status_raw,
    )

    full_chat_id = getattr(getattr(full_response, "full_chat", None), "id", None)
    chat_id, chat_username, chat_title = _extract_chat_info(full_response)

    raw_stats = {
        "full_channel": _to_dict(full_response),
        "statistics": statistics_payload,
        "boosts_status": boosts_status_raw,
        "bot_chat_member": permission_result.raw_member,
        "bot_permission_details": permission_result.permission_details,
    }

    _log_phase(channel_id=channel_id, phase="persist", status="start")
    try:
        if full_chat_id is not None:
            channel.telegram_channel_id = _to_bot_api_chat_id(int(full_chat_id))
        elif chat_id is not None:
            channel.telegram_channel_id = _to_bot_api_chat_id(int(chat_id))

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
        _log_phase(channel_id=channel_id, phase="persist", status="ok")
    except IntegrityError as exc:
        _log_phase(
            channel_id=channel_id,
            phase="persist",
            status="failed",
            reason="persist_integrity_error",
            error=exc,
        )
        db.rollback()
        raise ChannelVerificationError(
            "Failed to persist channel verification",
            channel_id=channel_id,
        ) from exc
    except Exception as exc:
        _log_phase(
            channel_id=channel_id,
            phase="persist",
            status="failed",
            reason="persist_failed",
            error=exc,
        )
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


async def _resolve_async_graphs(*, client, payload: dict[str, Any], channel_id: int) -> dict[str, Any]:
    return await _resolve_async_graph_node(
        client=client,
        value=payload,
        channel_id=channel_id,
        seen_tokens=set(),
    )


async def _resolve_async_graph_node(
    *,
    client,
    value: Any,
    channel_id: int,
    seen_tokens: set[str],
) -> Any:
    if isinstance(value, dict):
        marker = _coerce_str(value.get("_"))
        if marker == "StatsGraphAsync":
            token = _coerce_str(value.get("token")) or _coerce_str(value.get("zoom_token"))
            if token is None:
                return value
            if token in seen_tokens:
                return value
            seen_tokens.add(token)
            try:
                loaded_graph = await client(functions.stats.LoadAsyncGraphRequest(token=token))
            except Exception as exc:
                _log_phase(
                    channel_id=channel_id,
                    phase="stats_async_graph_fetch",
                    status="failed",
                    reason="async_graph_load_failed",
                    error=exc,
                )
                return value
            return await _resolve_async_graph_node(
                client=client,
                value=_to_dict(loaded_graph),
                channel_id=channel_id,
                seen_tokens=seen_tokens,
            )

        resolved: dict[str, Any] = {}
        for key, nested in value.items():
            resolved[str(key)] = await _resolve_async_graph_node(
                client=client,
                value=nested,
                channel_id=channel_id,
                seen_tokens=seen_tokens,
            )
        return resolved

    if isinstance(value, list):
        return [
            await _resolve_async_graph_node(
                client=client,
                value=nested,
                channel_id=channel_id,
                seen_tokens=seen_tokens,
            )
            for nested in value
        ]

    return value


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
        return _json_safe(to_dict())
    return _json_safe(value)


def _coerce_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_premium_stats(*, premium_graph, boosts_status) -> dict | None:
    premium_graph = _to_dict(premium_graph)
    boosts_status_raw = _to_dict(boosts_status)
    premium_audience = (
        _to_dict(boosts_status_raw.get("premium_audience"))
        if isinstance(boosts_status_raw, dict)
        else None
    )

    premium_ratio = _extract_premium_ratio(premium_graph)
    if premium_ratio is None:
        premium_ratio = _extract_premium_ratio(premium_audience)

    payload: dict[str, object] = {}
    if premium_ratio is not None:
        payload["premium_ratio"] = premium_ratio
    if premium_audience is not None:
        payload["premium_audience"] = premium_audience
    if premium_graph is not None:
        payload["premium_graph"] = premium_graph
    if boosts_status_raw is not None:
        payload["boosts_status"] = boosts_status_raw

    return payload or None


def _extract_premium_ratio(value) -> float | None:
    if not isinstance(value, dict):
        return None

    premium_ratio = _coerce_float(value.get("premium_ratio"))
    if premium_ratio is not None:
        return premium_ratio

    part = _coerce_float(value.get("part"))
    total = _coerce_float(value.get("total"))
    if part is None or total is None or total <= 0:
        return None
    return part / total


def _coerce_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_str(value) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


async def _maybe_await(value):
    if hasattr(value, "__await__"):
        return await value
    return value


def _json_safe(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return {"__bytes_b64__": base64.b64encode(raw).decode("ascii")}

    if isinstance(value, dict):
        return {str(key): _json_safe(val) for key, val in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]

    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _json_safe(to_dict())

    return str(value)


def _log_phase(
    *,
    channel_id: int,
    phase: str,
    status: str,
    reason: str | None = None,
    error: Exception | None = None,
) -> None:
    payload = [f"phase={phase}", f"status={status}", f"channel_id={channel_id}"]
    if reason:
        payload.append(f"reason={reason}")
    if error is not None:
        payload.append(f"error_type={error.__class__.__name__}")

    message = "channel_verify " + " ".join(payload)
    if status == "failed":
        logger.warning(message)
        return
    logger.info(message)
