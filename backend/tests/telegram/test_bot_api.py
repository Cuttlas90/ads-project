import pytest

from app.settings import Settings
from shared.telegram.bot_api import BotApiService
from shared.telegram.errors import TelegramApiError, TelegramConfigError
import shared.telegram.bot_api as bot_api


class DummyResponse:
    def __init__(self, status_code: int, json_data: dict, text: str = "") -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self) -> dict:
        return self._json_data


def test_send_message_success(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, json: dict) -> DummyResponse:
        captured["url"] = url
        captured["json"] = json
        return DummyResponse(200, {"ok": True, "result": {"message_id": 1}})

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)

    settings = Settings(
        _env_file=None,
        TELEGRAM_ENABLED=True,
        TELEGRAM_BOT_TOKEN="token",
    )
    service = BotApiService(settings)

    response = service.send_message(
        chat_id=123,
        text="hello",
        reply_markup={"inline_keyboard": []},
        disable_web_page_preview=False,
    )

    assert response["ok"] is True
    assert captured["url"] == "https://api.telegram.org/bottoken/sendMessage"
    assert captured["json"] == {
        "chat_id": 123,
        "text": "hello",
        "disable_web_page_preview": False,
        "reply_markup": {"inline_keyboard": []},
    }


def test_send_message_error(monkeypatch) -> None:
    def fake_post(url: str, json: dict) -> DummyResponse:
        return DummyResponse(400, {"ok": False}, text="bad request")

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)

    settings = Settings(
        _env_file=None,
        TELEGRAM_ENABLED=True,
        TELEGRAM_BOT_TOKEN="token",
    )
    service = BotApiService(settings)

    with pytest.raises(TelegramApiError):
        service.send_message(chat_id=1, text="fail")


def test_get_me_success(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, json: dict) -> DummyResponse:
        captured["url"] = url
        captured["json"] = json
        return DummyResponse(200, {"ok": True, "result": {"id": 999, "username": "bot"}})

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)

    settings = Settings(_env_file=None, TELEGRAM_ENABLED=True, TELEGRAM_BOT_TOKEN="token")
    service = BotApiService(settings)

    result = service.get_me()
    assert result["id"] == 999
    assert captured["url"] == "https://api.telegram.org/bottoken/getMe"
    assert captured["json"] == {}


def test_get_chat_member_success(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, json: dict) -> DummyResponse:
        captured["url"] = url
        captured["json"] = json
        return DummyResponse(200, {"ok": True, "result": {"status": "administrator"}})

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)

    settings = Settings(_env_file=None, TELEGRAM_ENABLED=True, TELEGRAM_BOT_TOKEN="token")
    service = BotApiService(settings)

    result = service.get_chat_member(chat_id="@chan", user_id=999)
    assert result["status"] == "administrator"
    assert captured["url"] == "https://api.telegram.org/bottoken/getChatMember"
    assert captured["json"] == {"chat_id": "@chan", "user_id": 999}


def test_bot_api_disabled(monkeypatch) -> None:
    def fake_post(*args, **kwargs) -> DummyResponse:
        raise AssertionError("httpx.post should not be called")

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)

    settings = Settings(
        _env_file=None,
        TELEGRAM_ENABLED=False,
        TELEGRAM_BOT_TOKEN="token",
    )
    service = BotApiService(settings)

    with pytest.raises(TelegramConfigError):
        service.send_message(chat_id=1, text="blocked")


def test_bot_api_missing_token(monkeypatch) -> None:
    def fake_post(*args, **kwargs) -> DummyResponse:
        raise AssertionError("httpx.post should not be called")

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)

    settings = Settings(_env_file=None, TELEGRAM_ENABLED=True, TELEGRAM_BOT_TOKEN=None)
    service = BotApiService(settings)

    with pytest.raises(TelegramConfigError):
        service.send_message(chat_id=1, text="blocked")


def test_upload_media_returns_file_id(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, data: dict, files: dict) -> DummyResponse:
        captured["url"] = url
        captured["data"] = data
        captured["files"] = files
        return DummyResponse(
            200,
            {"ok": True, "result": {"photo": [{"file_id": "file-1"}, {"file_id": "file-2"}]}},
        )

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)

    settings = Settings(
        _env_file=None,
        TELEGRAM_ENABLED=True,
        TELEGRAM_BOT_TOKEN="token",
        TELEGRAM_MEDIA_CHANNEL_ID=123,
    )
    service = BotApiService(settings)

    response = service.upload_media(media_type="image", filename="photo.jpg", content=b"data")

    assert response["file_id"] == "file-2"
    assert response["media_type"] == "image"
    assert captured["data"]["chat_id"] == 123


def test_post_story_success(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, json: dict) -> DummyResponse:
        captured["url"] = url
        captured["json"] = json
        return DummyResponse(200, {"ok": True, "result": {"id": 42}})

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)

    settings = Settings(
        _env_file=None,
        TELEGRAM_ENABLED=True,
        TELEGRAM_BOT_TOKEN="token",
        TELEGRAM_BUSINESS_CONNECTION_ID="biz_123",
    )
    service = BotApiService(settings)

    response = service.post_story(media_type="image", media="file-id", caption="hello")

    assert response["ok"] is True
    assert captured["url"] == "https://api.telegram.org/bottoken/postStory"
    assert captured["json"] == {
        "business_connection_id": "biz_123",
        "content": {"type": "photo", "photo": "file-id"},
        "caption": "hello",
    }


def test_post_story_requires_business_connection_id(monkeypatch) -> None:
    def fake_post(*args, **kwargs) -> DummyResponse:
        raise AssertionError("httpx.post should not be called")

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)

    settings = Settings(
        _env_file=None,
        TELEGRAM_ENABLED=True,
        TELEGRAM_BOT_TOKEN="token",
        TELEGRAM_BUSINESS_CONNECTION_ID=None,
    )
    service = BotApiService(settings)

    with pytest.raises(TelegramConfigError):
        service.post_story(media_type="image", media="file-id")
