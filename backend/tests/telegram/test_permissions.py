import asyncio

import pytest

from app.domain.permissions import PermissionDenied, ensure_permissions
from app.telegram.permissions import (
    REQUIRED_BOT_RIGHTS,
    PermissionCheckResult,
    check_bot_permissions,
    check_user_permissions,
)


class DummyAdminRights:
    def __init__(self, **rights: bool) -> None:
        for name, value in rights.items():
            setattr(self, name, value)


class DummyParticipant:
    def __init__(self, *, admin_rights=None, is_admin: bool = False, creator: bool = False) -> None:
        self.admin_rights = admin_rights
        self.is_admin = is_admin
        self.creator = creator


class DummyClient:
    def __init__(self, permissions_by_user: dict[object, object | None]) -> None:
        self.permissions_by_user = permissions_by_user

    async def get_input_entity(self, channel):
        return channel

    async def get_permissions(self, channel, who):
        return self.permissions_by_user.get(who)


def test_check_bot_permissions_not_admin() -> None:
    client = DummyClient({"me": DummyParticipant(is_admin=False, admin_rights=None)})

    result = asyncio.run(check_bot_permissions(client, 123))

    assert result.ok is False
    assert result.is_admin is False
    assert result.present_permissions == []
    assert result.missing_permissions == sorted(REQUIRED_BOT_RIGHTS)


def test_check_bot_permissions_missing_rights() -> None:
    rights = DummyAdminRights(post_messages=True, edit_messages=False, delete_messages=True, view_statistics=False)
    client = DummyClient({"me": DummyParticipant(is_admin=True, admin_rights=rights)})

    result = asyncio.run(check_bot_permissions(client, 123))

    assert result.ok is False
    assert result.is_admin is True
    assert result.present_permissions == ["delete_messages", "post_messages"]
    assert result.missing_permissions == ["edit_messages", "view_statistics"]


def test_check_bot_permissions_full_rights() -> None:
    rights = DummyAdminRights(**{right: True for right in REQUIRED_BOT_RIGHTS})
    client = DummyClient({"me": DummyParticipant(is_admin=True, admin_rights=rights)})

    result = asyncio.run(check_bot_permissions(client, 123))

    assert result.ok is True
    assert result.is_admin is True
    assert result.missing_permissions == []
    assert result.present_permissions == sorted(REQUIRED_BOT_RIGHTS)


def test_check_user_permissions_not_member() -> None:
    client = DummyClient({})

    result = asyncio.run(
        check_user_permissions(
            client,
            123,
            telegram_user_id=42,
            required_rights={"post_messages", "edit_messages"},
        )
    )

    assert result.ok is False
    assert result.is_admin is False
    assert result.present_permissions == []
    assert result.missing_permissions == ["edit_messages", "post_messages"]


def test_check_user_permissions_not_admin() -> None:
    client = DummyClient({42: DummyParticipant(is_admin=False, admin_rights=None)})

    result = asyncio.run(
        check_user_permissions(
            client,
            123,
            telegram_user_id=42,
            required_rights={"post_messages", "edit_messages"},
        )
    )

    assert result.ok is False
    assert result.is_admin is False
    assert result.present_permissions == []
    assert result.missing_permissions == ["edit_messages", "post_messages"]


def test_check_user_permissions_missing_rights() -> None:
    rights = DummyAdminRights(post_messages=True, edit_messages=False)
    client = DummyClient({42: DummyParticipant(is_admin=True, admin_rights=rights)})

    result = asyncio.run(
        check_user_permissions(
            client,
            123,
            telegram_user_id=42,
            required_rights={"post_messages", "edit_messages"},
        )
    )

    assert result.ok is False
    assert result.is_admin is True
    assert result.present_permissions == ["post_messages"]
    assert result.missing_permissions == ["edit_messages"]


def test_check_user_permissions_full_rights() -> None:
    rights = DummyAdminRights(post_messages=True, edit_messages=True)
    client = DummyClient({42: DummyParticipant(is_admin=True, admin_rights=rights)})

    result = asyncio.run(
        check_user_permissions(
            client,
            123,
            telegram_user_id=42,
            required_rights={"post_messages", "edit_messages"},
        )
    )

    assert result.ok is True
    assert result.is_admin is True
    assert result.missing_permissions == []
    assert result.present_permissions == ["edit_messages", "post_messages"]


def test_ensure_permissions_ok() -> None:
    result = PermissionCheckResult(
        ok=True,
        is_admin=True,
        missing_permissions=[],
        present_permissions=["post_messages"],
    )

    ensure_permissions(result, context="posting")


def test_ensure_permissions_raises() -> None:
    result = PermissionCheckResult(
        ok=False,
        is_admin=False,
        missing_permissions=["post_messages"],
        present_permissions=[],
    )

    with pytest.raises(PermissionDenied) as excinfo:
        ensure_permissions(result, context="posting")

    assert excinfo.value.context == "posting"
    assert excinfo.value.missing_permissions == ["post_messages"]
    assert "posting" in str(excinfo.value)
