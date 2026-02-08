from __future__ import annotations

import asyncio

from app.settings import Settings
import app.telegram.bootstrap as telethon_bootstrap
import shared.telegram.telethon_client as shared_telethon_client


class DummyStringSession:
    def __init__(self, value: str = "") -> None:
        self.value = value

    @staticmethod
    def save(_session) -> str:
        return "session-string-value"


class DummyTelegramClient:
    require_2fa = False

    def __init__(self, _session, _api_id: int, _api_hash: str, **kwargs) -> None:
        self.connected = False
        self.authorized = False
        self.phone: str | None = None
        self.code: str | None = None
        self.password: str | None = None
        self.session = object()
        self.kwargs = kwargs

    async def connect(self) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    async def is_user_authorized(self) -> bool:
        return self.authorized

    async def send_code_request(self, phone: str) -> None:
        self.phone = phone

    async def sign_in(self, *, phone: str | None = None, code: str | None = None, password: str | None = None):
        if password is not None:
            self.password = password
            self.authorized = True
            return

        self.phone = phone
        self.code = code
        if self.require_2fa:
            raise telethon_bootstrap.SessionPasswordNeededError(None)
        self.authorized = True


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        TELEGRAM_ENABLED=True,
        TELEGRAM_API_ID=12345,
        TELEGRAM_API_HASH="hash",
        TELEGRAM_SESSION_STRING_PATH=None,
        TELEGRAM_SESSION_STRING=None,
        TELEGRAM_MTPROXY_HOST=None,
        TELEGRAM_MTPROXY_PORT=None,
        TELEGRAM_MTPROXY_SECRET=None,
    )


def test_bootstrap_session_writes_file(monkeypatch, tmp_path) -> None:
    outputs: list[str] = []
    session_path = tmp_path / "telethon.session"

    monkeypatch.setattr(telethon_bootstrap, "TelegramClient", DummyTelegramClient)
    monkeypatch.setattr(telethon_bootstrap, "StringSession", DummyStringSession)

    result = asyncio.run(
        telethon_bootstrap.bootstrap_telethon_session(
            settings=_settings(),
            phone="+15550000000",
            code="12345",
            output_path=session_path,
            print_fn=outputs.append,
        )
    )

    assert result == "session-string-value"
    assert session_path.read_text(encoding="utf-8") == "session-string-value"
    assert "Telethon session string saved to" in outputs[0]
    assert "12345" not in outputs[0]


def test_bootstrap_uses_mtproxy_settings(monkeypatch, tmp_path) -> None:
    session_path = tmp_path / "telethon.session"
    created: dict[str, DummyTelegramClient] = {}

    def fake_client(_session, _api_id: int, _api_hash: str, **kwargs) -> DummyTelegramClient:
        client = DummyTelegramClient(_session, _api_id, _api_hash, **kwargs)
        created["client"] = client
        return client

    monkeypatch.setattr(telethon_bootstrap, "TelegramClient", fake_client)
    monkeypatch.setattr(telethon_bootstrap, "StringSession", DummyStringSession)

    settings = Settings(
        _env_file=None,
        TELEGRAM_ENABLED=True,
        TELEGRAM_API_ID=12345,
        TELEGRAM_API_HASH="hash",
        TELEGRAM_MTPROXY_HOST="91.239.192.223",
        TELEGRAM_MTPROXY_PORT=15,
        TELEGRAM_MTPROXY_SECRET="ee1603010200010001fc030386e24c3add63646e2e79656b74616e65742e636f6d",
    )

    asyncio.run(
        telethon_bootstrap.bootstrap_telethon_session(
            settings=settings,
            phone="+15550000000",
            code="12345",
            output_path=session_path,
        )
    )

    client = created["client"]
    assert client.kwargs["proxy"] == (
        "91.239.192.223",
        15,
        "ee1603010200010001fc030386e24c3add63646e2e79656b74616e65742e636f6d",
    )
    assert (
        client.kwargs["connection"]
        is shared_telethon_client.ConnectionTcpMTProxyRandomizedIntermediate
    )


def test_bootstrap_session_supports_2fa(monkeypatch, tmp_path) -> None:
    outputs: list[str] = []
    session_path = tmp_path / "telethon.session"
    DummyTelegramClient.require_2fa = True

    monkeypatch.setattr(telethon_bootstrap, "TelegramClient", DummyTelegramClient)
    monkeypatch.setattr(telethon_bootstrap, "StringSession", DummyStringSession)

    result = asyncio.run(
        telethon_bootstrap.bootstrap_telethon_session(
            settings=_settings(),
            phone="+15550000000",
            code="12345",
            password="super-secret",
            output_path=session_path,
            print_fn=outputs.append,
        )
    )
    DummyTelegramClient.require_2fa = False

    assert result == "session-string-value"
    assert session_path.read_text(encoding="utf-8") == "session-string-value"
    assert "super-secret" not in outputs[0]


def test_bootstrap_main_requires_output_target(monkeypatch) -> None:
    monkeypatch.setattr(telethon_bootstrap, "get_settings", _settings)

    exit_code = telethon_bootstrap.main([])

    assert exit_code == 1
