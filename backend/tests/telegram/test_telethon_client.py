import asyncio

import pytest

from app.settings import Settings
from shared.telegram.errors import TelegramConfigError
from shared.telegram.telethon_client import TelegramClientService
import shared.telegram.telethon_client as telethon_client


class DummyClient:
    def __init__(self, session_name: str, api_id: int, api_hash: str) -> None:
        self.session_name = session_name
        self.api_id = api_id
        self.api_hash = api_hash
        self.connect_calls = 0
        self.disconnect_calls = 0

    async def connect(self) -> None:
        self.connect_calls += 1

    async def disconnect(self) -> None:
        self.disconnect_calls += 1


def test_telethon_connect_disconnect(monkeypatch) -> None:
    created: dict[str, DummyClient] = {}

    def fake_client(session_name: str, api_id: int, api_hash: str) -> DummyClient:
        client = DummyClient(session_name, api_id, api_hash)
        created["client"] = client
        return client

    monkeypatch.setattr(telethon_client, "TelegramClient", fake_client)

    settings = Settings(
        _env_file=None,
        TELEGRAM_ENABLED=True,
        TELEGRAM_API_ID=12345,
        TELEGRAM_API_HASH="hash",
        TELEGRAM_SESSION_NAME="session",
    )
    service = TelegramClientService(settings)

    asyncio.run(service.connect())
    asyncio.run(service.disconnect())

    client = created["client"]
    assert client.session_name == "session"
    assert client.api_id == 12345
    assert client.api_hash == "hash"
    assert client.connect_calls == 1
    assert client.disconnect_calls == 1


def test_telethon_disabled(monkeypatch) -> None:
    called = {"count": 0}

    def fake_client(*args, **kwargs) -> DummyClient:
        called["count"] += 1
        return DummyClient("session", 1, "hash")

    monkeypatch.setattr(telethon_client, "TelegramClient", fake_client)

    settings = Settings(
        _env_file=None,
        TELEGRAM_ENABLED=False,
        TELEGRAM_API_ID=123,
        TELEGRAM_API_HASH="hash",
    )
    service = TelegramClientService(settings)

    with pytest.raises(TelegramConfigError):
        asyncio.run(service.connect())

    assert called["count"] == 0


def test_telethon_missing_credentials() -> None:
    settings = Settings(_env_file=None, TELEGRAM_ENABLED=True, TELEGRAM_API_ID=None)
    service = TelegramClientService(settings)

    with pytest.raises(TelegramConfigError):
        asyncio.run(service.connect())
