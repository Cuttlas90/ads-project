import pytest

from app.bot_api import BotApiService
from app.settings import Settings
from shared.telegram.errors import TelegramApiError, TelegramConfigError
import app.bot_api as bot_api


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


def test_get_updates_success(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_get(url: str, params: dict) -> DummyResponse:
        captured["url"] = url
        captured["params"] = params
        return DummyResponse(200, {"ok": True, "result": []})

    monkeypatch.setattr(bot_api.httpx, "get", fake_get)

    settings = Settings(_env_file=None, TELEGRAM_ENABLED=True, TELEGRAM_BOT_TOKEN="token")
    service = BotApiService(settings)

    response = service.get_updates(offset=10, timeout=5)
    assert response["ok"] is True
    assert captured["url"] == "https://api.telegram.org/bottoken/getUpdates"
    assert captured["params"] == {"timeout": 5, "offset": 10}


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


def test_get_updates_error(monkeypatch) -> None:
    def fake_get(url: str, params: dict) -> DummyResponse:
        return DummyResponse(500, {"ok": False}, text="bad")

    monkeypatch.setattr(bot_api.httpx, "get", fake_get)

    settings = Settings(_env_file=None, TELEGRAM_ENABLED=True, TELEGRAM_BOT_TOKEN="token")
    service = BotApiService(settings)

    with pytest.raises(TelegramApiError):
        service.get_updates()


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
