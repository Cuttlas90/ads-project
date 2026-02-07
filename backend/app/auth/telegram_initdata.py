from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from urllib.parse import parse_qsl

AUTH_DATE_MAX_AGE_SECONDS = 60 * 60 * 24


class AuthError(Exception):
    pass


def _build_data_check_string(data: dict[str, str]) -> str:
    parts = [f"{key}={data[key]}" for key in sorted(k for k in data if k != "hash")]
    return "\n".join(parts)


def verify_init_data(init_data: str, bot_token: str) -> dict[str, str]:
    """Return parsed init data dict if valid, otherwise raise AuthError."""
    if not init_data:
        raise AuthError("Missing initData")
    if not bot_token:
        raise AuthError("Bot token not configured")

    parsed_pairs = parse_qsl(init_data, keep_blank_values=True)
    if not parsed_pairs:
        raise AuthError("Invalid initData")

    data = {key: value for key, value in parsed_pairs}
    provided_hash = data.get("hash")
    if not provided_hash:
        raise AuthError("Missing hash")

    check_string = _build_data_check_string(data)
    # Mini App-only verification: this uses WebAppData derivation and intentionally
    # does not support Telegram Login Widget's sha256(bot_token) secret model.
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_hash, provided_hash):
        raise AuthError("Invalid hash")

    auth_date_value = data.get("auth_date")
    if not auth_date_value:
        raise AuthError("Missing auth_date")

    try:
        auth_date = int(auth_date_value)
    except ValueError as exc:
        raise AuthError("Invalid auth_date") from exc

    now_ts = int(datetime.now(timezone.utc).timestamp())
    if now_ts - auth_date > AUTH_DATE_MAX_AGE_SECONDS:
        raise AuthError("auth_date expired")

    return data
