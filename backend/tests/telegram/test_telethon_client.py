import asyncio

import pytest

from app.settings import Settings
from shared.telegram.errors import TelegramAuthorizationError, TelegramConfigError
from shared.telegram.telethon_client import TelegramClientService
import shared.telegram.telethon_client as telethon_client


def _clear_mtproxy_env(monkeypatch) -> None:
    monkeypatch.delenv("TELEGRAM_MTPROXY_HOST", raising=False)
    monkeypatch.delenv("TELEGRAM_MTPROXY_PORT", raising=False)
    monkeypatch.delenv("TELEGRAM_MTPROXY_SECRET", raising=False)
    monkeypatch.delenv("TELEGRAM_SESSION_STRING", raising=False)
    monkeypatch.delenv("TELEGRAM_SESSION_STRING_PATH", raising=False)


class DummyClient:
    def __init__(self, session, api_id: int, api_hash: str, **kwargs) -> None:
        self.session = session
        self.api_id = api_id
        self.api_hash = api_hash
        self.kwargs = kwargs
        self.connect_calls = 0
        self.disconnect_calls = 0
        self.authorized = True

    async def connect(self) -> None:
        self.connect_calls += 1

    async def disconnect(self) -> None:
        self.disconnect_calls += 1

    async def is_user_authorized(self) -> bool:
        return self.authorized


def test_telethon_connect_disconnect(monkeypatch) -> None:
    _clear_mtproxy_env(monkeypatch)
    created: dict[str, DummyClient] = {}

    def fake_client(session, api_id: int, api_hash: str, **kwargs) -> DummyClient:
        client = DummyClient(session, api_id, api_hash, **kwargs)
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
    assert client.session == "session"
    assert client.api_id == 12345
    assert client.api_hash == "hash"
    assert client.kwargs == {}
    assert client.connect_calls == 1
    assert client.disconnect_calls == 1


def test_telethon_disabled(monkeypatch) -> None:
    _clear_mtproxy_env(monkeypatch)
    called = {"count": 0}

    def fake_client(*args, **kwargs) -> DummyClient:
        called["count"] += 1
        return DummyClient("session", 1, "hash", **kwargs)

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


def test_telethon_missing_credentials(monkeypatch) -> None:
    _clear_mtproxy_env(monkeypatch)
    settings = Settings(_env_file=None, TELEGRAM_ENABLED=True, TELEGRAM_API_ID=None)
    service = TelegramClientService(settings)

    with pytest.raises(TelegramConfigError):
        asyncio.run(service.connect())


def test_telethon_mtproxy(monkeypatch) -> None:
    _clear_mtproxy_env(monkeypatch)
    created: dict[str, DummyClient] = {}

    def fake_client(session, api_id: int, api_hash: str, **kwargs) -> DummyClient:
        client = DummyClient(session, api_id, api_hash, **kwargs)
        created["client"] = client
        return client

    monkeypatch.setattr(telethon_client, "TelegramClient", fake_client)

    settings = Settings(
        _env_file=None,
        TELEGRAM_ENABLED=True,
        TELEGRAM_API_ID=12345,
        TELEGRAM_API_HASH="hash",
        TELEGRAM_SESSION_NAME="session",
        TELEGRAM_MTPROXY_HOST="91.239.192.223",
        TELEGRAM_MTPROXY_PORT=15,
        TELEGRAM_MTPROXY_SECRET="ee1603010200010001fc030386e24c3add63646e2e79656b74616e65742e636f6d",
    )
    service = TelegramClientService(settings)

    asyncio.run(service.connect())
    asyncio.run(service.disconnect())

    client = created["client"]
    assert client.kwargs["proxy"] == (
        "91.239.192.223",
        15,
        "ee1603010200010001fc030386e24c3add63646e2e79656b74616e65742e636f6d",
    )
    assert (
        client.kwargs["connection"] is telethon_client.ConnectionTcpMTProxyRandomizedIntermediate
    )


def test_telethon_mtproxy_incomplete_config(monkeypatch) -> None:
    _clear_mtproxy_env(monkeypatch)
    settings = Settings(
        _env_file=None,
        TELEGRAM_ENABLED=True,
        TELEGRAM_API_ID=12345,
        TELEGRAM_API_HASH="hash",
        TELEGRAM_MTPROXY_HOST="91.239.192.223",
        TELEGRAM_MTPROXY_PORT=15,
    )
    service = TelegramClientService(settings)

    with pytest.raises(TelegramConfigError, match="TELEGRAM_MTPROXY_SECRET"):
        asyncio.run(service.connect())


def test_telethon_require_authorized(monkeypatch) -> None:
    _clear_mtproxy_env(monkeypatch)

    def fake_client(session, api_id: int, api_hash: str, **kwargs) -> DummyClient:
        client = DummyClient(session, api_id, api_hash, **kwargs)
        client.authorized = False
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

    with pytest.raises(TelegramAuthorizationError):
        asyncio.run(service.require_authorized())


def test_telethon_session_sources_conflict(monkeypatch) -> None:
    _clear_mtproxy_env(monkeypatch)
    settings = Settings(
        _env_file=None,
        TELEGRAM_ENABLED=True,
        TELEGRAM_API_ID=12345,
        TELEGRAM_API_HASH="hash",
        TELEGRAM_SESSION_STRING="session-string",
        TELEGRAM_SESSION_STRING_PATH="/tmp/session-string",
    )
    service = TelegramClientService(settings)

    with pytest.raises(
        TelegramConfigError, match="TELEGRAM_SESSION_STRING or TELEGRAM_SESSION_STRING_PATH"
    ):
        service.client()


def test_telethon_session_string_path(monkeypatch, tmp_path) -> None:
    _clear_mtproxy_env(monkeypatch)
    created: dict[str, DummyClient] = {}

    class DummyStringSession:
        def __init__(self, value: str = "") -> None:
            self.value = value

        @staticmethod
        def save(_session) -> str:
            return "saved-session"

    def fake_client(session, api_id: int, api_hash: str, **kwargs) -> DummyClient:
        client = DummyClient(session, api_id, api_hash, **kwargs)
        created["client"] = client
        return client

    session_path = tmp_path / "telethon.session"
    session_path.write_text("encoded", encoding="utf-8")

    monkeypatch.setattr(telethon_client, "TelegramClient", fake_client)
    monkeypatch.setattr(telethon_client, "StringSession", DummyStringSession)

    settings = Settings(
        _env_file=None,
        TELEGRAM_ENABLED=True,
        TELEGRAM_API_ID=12345,
        TELEGRAM_API_HASH="hash",
        TELEGRAM_SESSION_STRING_PATH=str(session_path),
    )
    service = TelegramClientService(settings)

    asyncio.run(service.connect())
    asyncio.run(service.disconnect())

    client = created["client"]
    assert isinstance(client.session, DummyStringSession)
    assert client.session.value == "encoded"


def test_telethon_export_session_string(monkeypatch) -> None:
    _clear_mtproxy_env(monkeypatch)

    class DummyStringSession:
        def __init__(self, value: str = "") -> None:
            self.value = value

        @staticmethod
        def save(_session) -> str:
            return "saved-session"

    def fake_client(session, api_id: int, api_hash: str, **kwargs) -> DummyClient:
        return DummyClient(session, api_id, api_hash, **kwargs)

    monkeypatch.setattr(telethon_client, "TelegramClient", fake_client)
    monkeypatch.setattr(telethon_client, "StringSession", DummyStringSession)

    settings = Settings(
        _env_file=None,
        TELEGRAM_ENABLED=True,
        TELEGRAM_API_ID=12345,
        TELEGRAM_API_HASH="hash",
        TELEGRAM_SESSION_NAME="session",
    )
    service = TelegramClientService(settings)

    assert service.export_session_string() == "saved-session"
