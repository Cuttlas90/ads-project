from __future__ import annotations

from dataclasses import dataclass
import inspect
from typing import Iterable

REQUIRED_BOT_RIGHTS = {
    "can_post_messages",
    "can_edit_messages",
    "can_delete_messages",
    "can_post_stories",
    "can_edit_stories",
    "can_delete_stories",
}

BOT_MEMBER_PERMISSION_FIELDS = (
    "can_be_edited",
    "is_anonymous",
    "can_manage_chat",
    "can_delete_messages",
    "can_manage_video_chats",
    "can_restrict_members",
    "can_promote_members",
    "can_change_info",
    "can_invite_users",
    "can_post_stories",
    "can_edit_stories",
    "can_delete_stories",
    "can_post_messages",
    "can_edit_messages",
    "can_pin_messages",
    "can_manage_topics",
    "can_manage_direct_messages",
)


@dataclass(frozen=True)
class PermissionCheckResult:
    ok: bool
    is_admin: bool
    missing_permissions: list[str]
    present_permissions: list[str]
    permission_details: dict[str, bool | None] | None = None
    raw_member: dict | None = None


async def check_bot_permissions(bot_api, channel) -> PermissionCheckResult:
    """Check bot admin permissions in a channel via Bot API getMe/getChatMember."""
    required_order = sorted(REQUIRED_BOT_RIGHTS)
    try:
        me = bot_api.get_me()
        bot_id = int(me["id"])
    except Exception:
        return PermissionCheckResult(
            ok=False,
            is_admin=False,
            missing_permissions=required_order,
            present_permissions=[],
            permission_details=None,
            raw_member=None,
        )

    member: dict | None = None
    refs = _build_bot_chat_refs(channel)
    for chat_ref in refs:
        try:
            member = bot_api.get_chat_member(chat_id=chat_ref, user_id=bot_id)
            break
        except Exception:
            continue

    if member is None:
        return PermissionCheckResult(
            ok=False,
            is_admin=False,
            missing_permissions=required_order,
            present_permissions=[],
            permission_details=None,
            raw_member=None,
        )

    status = str(member.get("status", "")).lower()
    is_admin = status == "administrator"
    permission_details = {
        field: _coerce_optional_bool(member.get(field))
        for field in BOT_MEMBER_PERMISSION_FIELDS
    }

    if not is_admin:
        return PermissionCheckResult(
            ok=False,
            is_admin=False,
            missing_permissions=required_order,
            present_permissions=[],
            permission_details=permission_details,
            raw_member=member,
        )

    present = [right for right in required_order if permission_details.get(right) is True]
    missing = [right for right in required_order if right not in present]
    return PermissionCheckResult(
        ok=len(missing) == 0,
        is_admin=True,
        missing_permissions=missing,
        present_permissions=present,
        permission_details=permission_details,
        raw_member=member,
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


def _coerce_optional_bool(value) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _build_bot_chat_refs(channel) -> list[int | str]:
    refs: list[int | str] = []
    seen: set[int | str] = set()

    def add(ref: int | str) -> None:
        if ref in seen:
            return
        seen.add(ref)
        refs.append(ref)

    if isinstance(channel, str):
        value = channel.strip()
        if not value:
            return refs
        if value.lstrip("-").isdigit():
            for item in _numeric_chat_refs(int(value)):
                add(item)
            return refs

        if value.startswith("@"):
            add(value)
            add(value[1:])
            return refs

        add(f"@{value}")
        add(value)
        return refs

    if isinstance(channel, int):
        for item in _numeric_chat_refs(channel):
            add(item)
        return refs

    add(channel)
    return refs


def _numeric_chat_refs(value: int) -> list[int]:
    if value > 0:
        # Telethon channel ids are usually positive; Bot API channel ids use -100 prefix.
        return [int(f"-100{value}"), value]
    return [value]


async def _maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value
