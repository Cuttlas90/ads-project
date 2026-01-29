import asyncio

import pytest

from app.settings import Settings
from shared.telegram.bot_api import BotApiService
from shared.telegram.errors import TelegramConfigError
from shared.telegram.telethon_client import TelegramClientService
import shared.telegram.bot_api as bot_api
import shared.telegram.telethon_client as telethon_client


class DummyClient:
    async def connect(self) -> None:
        return None

    async def disconnect(self) -> None:
        return None


def test_bot_api_disabled(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        raise AssertionError("httpx.post should not be called")

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)

    settings = Settings(_env_file=None, TELEGRAM_ENABLED=False, TELEGRAM_BOT_TOKEN="token")
    service = BotApiService(settings)

    with pytest.raises(TelegramConfigError):
        service.send_message(chat_id=1, text="blocked")


def test_telethon_missing_credentials(monkeypatch) -> None:
    called = {"count": 0}

    def fake_client(*args, **kwargs):
        called["count"] += 1
        return DummyClient()

    monkeypatch.setattr(telethon_client, "TelegramClient", fake_client)

    settings = Settings(_env_file=None, TELEGRAM_ENABLED=True, TELEGRAM_API_ID=None)
    service = TelegramClientService(settings)

    with pytest.raises(TelegramConfigError):
        asyncio.run(service.connect())

    assert called["count"] == 0
