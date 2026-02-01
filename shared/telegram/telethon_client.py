from __future__ import annotations

from telethon import TelegramClient

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

    def _get_client(self) -> TelegramClient:
        if self._client is None:
            self._client = TelegramClient(
                self._settings.TELEGRAM_SESSION_NAME,
                self._settings.TELEGRAM_API_ID,
                self._settings.TELEGRAM_API_HASH,
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
