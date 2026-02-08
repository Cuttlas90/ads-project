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

    def _post(self, method: str, payload: dict[str, object]) -> dict:
        self._require_enabled()
        response = httpx.post(f"{self._base_url()}/{method}", json=payload)
        if response.status_code != 200:
            raise TelegramApiError(
                f"Bot API error {response.status_code}: {response.text}"
            )
        return response.json()

    def get_me(self) -> dict:
        payload = self._post("getMe", {})
        if not payload.get("ok"):
            raise TelegramApiError(f"Bot API error: {payload}")
        result = payload.get("result")
        if not isinstance(result, dict):
            raise TelegramApiError("Bot API response missing getMe result")
        return result

    def get_chat_member(self, *, chat_id: int | str, user_id: int) -> dict:
        payload = self._post("getChatMember", {"chat_id": chat_id, "user_id": user_id})
        if not payload.get("ok"):
            raise TelegramApiError(f"Bot API error: {payload}")
        result = payload.get("result")
        if not isinstance(result, dict):
            raise TelegramApiError("Bot API response missing getChatMember result")
        return result

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        reply_markup: dict | None = None,
        disable_web_page_preview: bool = True,
    ) -> dict:
        payload: dict[str, object] = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        return self._post("sendMessage", payload)

    def send_photo(
        self,
        chat_id: int | str,
        photo: str,
        caption: str | None = None,
        disable_notification: bool = False,
    ) -> dict:
        payload: dict[str, object] = {
            "chat_id": chat_id,
            "photo": photo,
            "disable_notification": disable_notification,
        }
        if caption is not None:
            payload["caption"] = caption
        return self._post("sendPhoto", payload)

    def send_video(
        self,
        chat_id: int | str,
        video: str,
        caption: str | None = None,
        disable_notification: bool = False,
    ) -> dict:
        payload: dict[str, object] = {
            "chat_id": chat_id,
            "video": video,
            "disable_notification": disable_notification,
        }
        if caption is not None:
            payload["caption"] = caption
        return self._post("sendVideo", payload)

    def upload_media(
        self,
        *,
        media_type: str,
        filename: str,
        content: bytes,
    ) -> dict:
        self._require_enabled()
        channel_id = getattr(self._settings, "TELEGRAM_MEDIA_CHANNEL_ID", None)
        if not channel_id:
            raise TelegramConfigError("TELEGRAM_MEDIA_CHANNEL_ID is not configured")
        if media_type not in {"image", "video"}:
            raise TelegramApiError("Unsupported media type")

        method = "sendPhoto" if media_type == "image" else "sendVideo"
        field_name = "photo" if media_type == "image" else "video"

        response = httpx.post(
            f"{self._base_url()}/{method}",
            data={"chat_id": channel_id, "disable_notification": True},
            files={field_name: (filename, content)},
        )
        if response.status_code != 200:
            raise TelegramApiError(
                f"Bot API error {response.status_code}: {response.text}"
            )

        payload = response.json()
        if not payload.get("ok"):
            raise TelegramApiError(f"Bot API error: {payload}")

        result = payload.get("result") or {}
        file_id: str | None = None
        if media_type == "image":
            photos = result.get("photo") or []
            if isinstance(photos, list) and photos:
                file_id = photos[-1].get("file_id")
        else:
            video = result.get("video") or {}
            if isinstance(video, dict):
                file_id = video.get("file_id")

        if not file_id:
            raise TelegramApiError("Bot API response missing file_id")

        return {"file_id": file_id, "media_type": media_type}
