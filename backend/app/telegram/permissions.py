from __future__ import annotations

from dataclasses import dataclass
import inspect
from typing import Iterable

REQUIRED_BOT_RIGHTS = {
    "post_messages",
    "edit_messages",
    "delete_messages",
    "view_statistics",
}


@dataclass(frozen=True)
class PermissionCheckResult:
    ok: bool
    is_admin: bool
    missing_permissions: list[str]
    present_permissions: list[str]


async def check_bot_permissions(client, channel) -> PermissionCheckResult:
    """Check the current Telethon client's admin rights against REQUIRED_BOT_RIGHTS."""
    return await _check_permissions(
        client=client,
        channel=channel,
        who="me",
        required_rights=REQUIRED_BOT_RIGHTS,
    )


async def check_user_permissions(
    client,
    channel,
    telegram_user_id: int,
    required_rights: set[str],
) -> PermissionCheckResult:
    """Check a specific Telegram user's admin rights against required_rights."""
    return await _check_permissions(
        client=client,
        channel=channel,
        who=telegram_user_id,
        required_rights=required_rights,
    )


async def _check_permissions(
    *,
    client,
    channel,
    who,
    required_rights: Iterable[str],
) -> PermissionCheckResult:
    required_set = set(required_rights)
    required_order = sorted(required_set)
    try:
        channel_entity = await _resolve_channel(client, channel)
        permissions = await _fetch_permissions(client, channel_entity, who)
    except Exception:
        permissions = None

    is_admin, admin_rights = _extract_admin_rights(permissions)
    if not is_admin:
        return PermissionCheckResult(
            ok=False,
            is_admin=False,
            missing_permissions=required_order,
            present_permissions=[],
        )

    present = [right for right in required_order if _has_right(admin_rights, right)]
    missing = [right for right in required_order if right not in present]
    ok = len(missing) == 0
    return PermissionCheckResult(
        ok=ok,
        is_admin=True,
        missing_permissions=missing,
        present_permissions=present,
    )


async def _resolve_channel(client, channel):
    get_input_entity = getattr(client, "get_input_entity", None)
    if get_input_entity is None:
        return channel
    return await _maybe_await(get_input_entity(channel))


async def _fetch_permissions(client, channel, who):
    get_permissions = getattr(client, "get_permissions", None)
    if get_permissions is None:
        return None
    try:
        return await _maybe_await(get_permissions(channel, who))
    except Exception:
        return None


def _extract_admin_rights(permissions) -> tuple[bool, object | None]:
    if permissions is None:
        return False, None
    participant = getattr(permissions, "participant", permissions)
    if participant is None:
        return False, None

    if getattr(participant, "is_admin", False):
        return True, getattr(participant, "admin_rights", None)
    if getattr(participant, "admin_rights", None) is not None:
        return True, getattr(participant, "admin_rights", None)
    if getattr(participant, "creator", False):
        return True, getattr(participant, "admin_rights", None)
    if participant.__class__.__name__.endswith("Creator"):
        return True, getattr(participant, "admin_rights", None)

    return False, None


def _has_right(admin_rights: object | None, right: str) -> bool:
    if admin_rights is None:
        return False
    return bool(getattr(admin_rights, right, False))


async def _maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value
