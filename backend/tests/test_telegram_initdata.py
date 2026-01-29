from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from app.auth.telegram_initdata import AuthError, verify_init_data

BOT_TOKEN = "test-bot-token"


def build_init_data(payload: dict[str, str], bot_token: str = BOT_TOKEN) -> str:
    data = {key: str(value) for key, value in payload.items()}
    data_check_string = "\n".join(f"{key}={data[key]}" for key in sorted(data))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    data["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(data)


def test_verify_init_data_valid() -> None:
    auth_date = str(int(time.time()))
    user_json = json.dumps({"id": 123, "first_name": "Ada"})
    init_data = build_init_data({"auth_date": auth_date, "user": user_json})

    parsed = verify_init_data(init_data, BOT_TOKEN)

    assert parsed["user"] == user_json
    assert parsed["auth_date"] == auth_date


def test_verify_init_data_invalid_hash() -> None:
    auth_date = str(int(time.time()))
    user_json = json.dumps({"id": 123, "first_name": "Ada"})
    init_data = build_init_data({"auth_date": auth_date, "user": user_json}, bot_token="wrong-token")

    with pytest.raises(AuthError):
        verify_init_data(init_data, BOT_TOKEN)


def test_verify_init_data_missing_hash() -> None:
    auth_date = str(int(time.time()))
    user_json = json.dumps({"id": 123, "first_name": "Ada"})
    init_data = urlencode({"auth_date": auth_date, "user": user_json})

    with pytest.raises(AuthError):
        verify_init_data(init_data, BOT_TOKEN)


def test_verify_init_data_missing_auth_date() -> None:
    user_json = json.dumps({"id": 123, "first_name": "Ada"})
    init_data = build_init_data({"user": user_json})

    with pytest.raises(AuthError):
        verify_init_data(init_data, BOT_TOKEN)


def test_verify_init_data_expired_auth_date() -> None:
    auth_date = str(int(time.time()) - (60 * 60 * 25))
    user_json = json.dumps({"id": 123, "first_name": "Ada"})
    init_data = build_init_data({"auth_date": auth_date, "user": user_json})

    with pytest.raises(AuthError):
        verify_init_data(init_data, BOT_TOKEN)
