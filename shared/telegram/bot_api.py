from __future__ import annotations

import httpx

from shared.telegram.errors import TelegramApiError, TelegramConfigError


class BotApiService:
    def __init__(self, settings) -> None:
        self._settings = settings

    def _require_enabled(self) -> None:
        if not getattr(self._settings, "TELEGRAM_ENABLED", True):
            raise TelegramConfigError("Telegram integration is disabled")
        if not self._settings.TELEGRAM_BOT_TOKEN:
            raise TelegramConfigError("TELEGRAM_BOT_TOKEN is not configured")

    def _base_url(self) -> str:
        return f"https://api.telegram.org/bot{self._settings.TELEGRAM_BOT_TOKEN}"

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        reply_markup: dict | None = None,
        disable_web_page_preview: bool = True,
    ) -> dict:
        self._require_enabled()
        payload: dict[str, object] = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        response = httpx.post(f"{self._base_url()}/sendMessage", json=payload)
        if response.status_code != 200:
            raise TelegramApiError(
                f"Bot API error {response.status_code}: {response.text}"
            )
        return response.json()
