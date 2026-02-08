from __future__ import annotations

from telethon import TelegramClient
from telethon.network.connection.tcpmtproxy import ConnectionTcpMTProxyRandomizedIntermediate

from shared.telegram.errors import TelegramConfigError


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

    def _get_mtproxy(self) -> tuple[str, int, str] | None:
        host = getattr(self._settings, "TELEGRAM_MTPROXY_HOST", None)
        port = getattr(self._settings, "TELEGRAM_MTPROXY_PORT", None)
        secret = getattr(self._settings, "TELEGRAM_MTPROXY_SECRET", None)

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

    def _get_client(self) -> TelegramClient:
        if self._client is None:
            kwargs: dict[str, object] = {}
            mtproxy = self._get_mtproxy()
            if mtproxy is not None:
                kwargs["connection"] = ConnectionTcpMTProxyRandomizedIntermediate
                kwargs["proxy"] = mtproxy

            self._client = TelegramClient(
                self._settings.TELEGRAM_SESSION_NAME,
                self._settings.TELEGRAM_API_ID,
                self._settings.TELEGRAM_API_HASH,
                **kwargs,
            )
        return self._client

    def client(self) -> TelegramClient:
        self._require_enabled()
        return self._get_client()

    async def connect(self) -> None:
        self._require_enabled()
        client = self._get_client()
        await client.connect()

    async def disconnect(self) -> None:
        self._require_enabled()
        if self._client is None:
            return
        await self._client.disconnect()
