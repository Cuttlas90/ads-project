from __future__ import annotations

from pathlib import Path

from telethon import TelegramClient
from telethon.network.connection.tcpmtproxy import ConnectionTcpMTProxyRandomizedIntermediate
from telethon.sessions import StringSession

from shared.telegram.errors import TelegramAuthorizationError, TelegramConfigError


def resolve_mtproxy(settings) -> tuple[str, int, str] | None:
    host = getattr(settings, "TELEGRAM_MTPROXY_HOST", None)
    port = getattr(settings, "TELEGRAM_MTPROXY_PORT", None)
    secret = getattr(settings, "TELEGRAM_MTPROXY_SECRET", None)

    if not host and port is None and not secret:
        return None

    missing: list[str] = []
    if not host:
        missing.append("TELEGRAM_MTPROXY_HOST")
    if port is None:
        missing.append("TELEGRAM_MTPROXY_PORT")
    if not secret:
        missing.append("TELEGRAM_MTPROXY_SECRET")
    if missing:
        raise TelegramConfigError(f"Incomplete MTProxy configuration: {', '.join(missing)}")

    proxy_host = str(host).strip()
    proxy_secret = str(secret).strip()
    if not proxy_host:
        raise TelegramConfigError("TELEGRAM_MTPROXY_HOST is not configured")
    if not proxy_secret:
        raise TelegramConfigError("TELEGRAM_MTPROXY_SECRET is not configured")

    try:
        proxy_port = int(port)
    except (TypeError, ValueError) as exc:
        raise TelegramConfigError("TELEGRAM_MTPROXY_PORT must be an integer") from exc

    if proxy_port <= 0 or proxy_port > 65535:
        raise TelegramConfigError("TELEGRAM_MTPROXY_PORT must be between 1 and 65535")

    return proxy_host, proxy_port, proxy_secret


def build_telethon_client_kwargs(settings) -> dict[str, object]:
    kwargs: dict[str, object] = {}
    mtproxy = resolve_mtproxy(settings)
    if mtproxy is not None:
        kwargs["connection"] = ConnectionTcpMTProxyRandomizedIntermediate
        kwargs["proxy"] = mtproxy
    return kwargs


class TelegramClientService:
    def __init__(self, settings) -> None:
        self._settings = settings
        self._client: TelegramClient | None = None

    def _require_enabled(self) -> None:
        if not getattr(self._settings, "TELEGRAM_ENABLED", True):
            raise TelegramConfigError("Telegram integration is disabled")
        if self._settings.TELEGRAM_API_ID is None:
            raise TelegramConfigError("TELEGRAM_API_ID is not configured")
        if not self._settings.TELEGRAM_API_HASH:
            raise TelegramConfigError("TELEGRAM_API_HASH is not configured")
        if not self._settings.TELEGRAM_SESSION_NAME:
            raise TelegramConfigError("TELEGRAM_SESSION_NAME is not configured")

    def _get_session(self):
        session_string = getattr(self._settings, "TELEGRAM_SESSION_STRING", None)
        session_string_path = getattr(self._settings, "TELEGRAM_SESSION_STRING_PATH", None)

        if session_string and session_string_path:
            raise TelegramConfigError(
                "Set only one of TELEGRAM_SESSION_STRING or TELEGRAM_SESSION_STRING_PATH"
            )

        if session_string:
            value = str(session_string).strip()
            if not value:
                raise TelegramConfigError("TELEGRAM_SESSION_STRING is not configured")
            return StringSession(value)

        if session_string_path:
            path = Path(str(session_string_path)).expanduser()
            try:
                value = path.read_text(encoding="utf-8").strip()
            except FileNotFoundError as exc:
                raise TelegramConfigError(
                    f"TELEGRAM_SESSION_STRING_PATH does not exist: {path}"
                ) from exc
            except OSError as exc:
                raise TelegramConfigError(
                    f"Failed to read TELEGRAM_SESSION_STRING_PATH: {path}"
                ) from exc

            if not value:
                raise TelegramConfigError(
                    f"TELEGRAM_SESSION_STRING_PATH is empty: {path}"
                )
            return StringSession(value)

        return self._settings.TELEGRAM_SESSION_NAME

    def _get_mtproxy(self) -> tuple[str, int, str] | None:
        return resolve_mtproxy(self._settings)

    def _get_client(self) -> TelegramClient:
        if self._client is None:
            self._client = TelegramClient(
                self._get_session(),
                self._settings.TELEGRAM_API_ID,
                self._settings.TELEGRAM_API_HASH,
                **build_telethon_client_kwargs(self._settings),
            )
        return self._client

    def client(self) -> TelegramClient:
        self._require_enabled()
        return self._get_client()

    async def connect(self) -> None:
        self._require_enabled()
        client = self._get_client()
        await client.connect()

    async def is_authorized(self) -> bool:
        self._require_enabled()
        client = self._get_client()
        is_user_authorized = getattr(client, "is_user_authorized", None)
        if is_user_authorized is None:
            return True
        return bool(await _maybe_await(is_user_authorized()))

    async def require_authorized(self) -> None:
        if await self.is_authorized():
            return
        raise TelegramAuthorizationError(
            "Telegram client session is not authorized. Authenticate TELEGRAM_SESSION_NAME first."
        )

    def export_session_string(self) -> str:
        self._require_enabled()
        client = self._get_client()
        session = getattr(client, "session", None)
        if session is None:
            raise TelegramConfigError("Telegram session is not initialized")
        return StringSession.save(session)

    async def disconnect(self) -> None:
        self._require_enabled()
        if self._client is None:
            return
        await self._client.disconnect()


async def _maybe_await(value):
    if hasattr(value, "__await__"):
        return await value
    return value
