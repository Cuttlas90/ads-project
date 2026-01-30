from __future__ import annotations

import asyncio

import pytest

import app.services.manager_revalidate as manager_revalidate
from app.domain.permissions import ChannelAccessDenied
from app.models.channel import Channel
from app.telegram.permissions import PermissionCheckResult


class DummyTelegramService:
    def __init__(self, client) -> None:
        self._client = client

    async def connect(self) -> None:
        return None

    async def disconnect(self) -> None:
        return None

    def _get_client(self):
        return self._client


def test_revalidate_channel_access_ok(monkeypatch) -> None:
    async def fake_check_user_permissions(_client, _channel, telegram_user_id: int, required_rights: set[str]):
        return PermissionCheckResult(
            ok=True,
            is_admin=True,
            missing_permissions=[],
            present_permissions=sorted(required_rights),
        )

    monkeypatch.setattr(manager_revalidate, "check_user_permissions", fake_check_user_permissions)

    channel = Channel(id=1, telegram_channel_id=777, username="example")
    service = DummyTelegramService(client=object())

    asyncio.run(
        manager_revalidate.revalidate_channel_access(
            telegram_client=service,
            channel=channel,
            telegram_user_id=42,
            required_rights={"post_messages"},
        )
    )


def test_revalidate_channel_access_missing_rights(monkeypatch) -> None:
    async def fake_check_user_permissions(_client, _channel, telegram_user_id: int, required_rights: set[str]):
        return PermissionCheckResult(
            ok=False,
            is_admin=True,
            missing_permissions=sorted(required_rights),
            present_permissions=[],
        )

    monkeypatch.setattr(manager_revalidate, "check_user_permissions", fake_check_user_permissions)

    channel = Channel(id=11, telegram_channel_id=777, username="example")
    service = DummyTelegramService(client=object())

    with pytest.raises(ChannelAccessDenied) as excinfo:
        asyncio.run(
            manager_revalidate.revalidate_channel_access(
                telegram_client=service,
                channel=channel,
                telegram_user_id=99,
                required_rights={"post_messages"},
            )
        )

    assert excinfo.value.channel_id == 11
    assert excinfo.value.telegram_user_id == 99
    assert excinfo.value.missing_permissions == ["post_messages"]


def test_revalidate_channel_access_not_admin(monkeypatch) -> None:
    async def fake_check_user_permissions(_client, _channel, telegram_user_id: int, required_rights: set[str]):
        return PermissionCheckResult(
            ok=False,
            is_admin=False,
            missing_permissions=sorted(required_rights),
            present_permissions=[],
        )

    monkeypatch.setattr(manager_revalidate, "check_user_permissions", fake_check_user_permissions)

    channel = Channel(id=22, telegram_channel_id=888, username="example")
    service = DummyTelegramService(client=object())

    with pytest.raises(ChannelAccessDenied) as excinfo:
        asyncio.run(
            manager_revalidate.revalidate_channel_access(
                telegram_client=service,
                channel=channel,
                telegram_user_id=123,
                required_rights={"post_messages"},
            )
        )

    assert excinfo.value.channel_id == 22
    assert excinfo.value.telegram_user_id == 123
    assert excinfo.value.missing_permissions == ["post_messages"]
