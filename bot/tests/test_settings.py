from app.settings import Settings, get_settings


_ENV_KEYS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_API_ID",
    "TELEGRAM_API_HASH",
    "TELEGRAM_ENABLED",
    "TELEGRAM_SESSION_NAME",
]


def test_settings_defaults(monkeypatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    settings = Settings(_env_file=None)

    assert settings.TELEGRAM_BOT_TOKEN is None
    assert settings.TELEGRAM_API_ID is None
    assert settings.TELEGRAM_API_HASH is None
    assert settings.TELEGRAM_ENABLED is True
    assert settings.TELEGRAM_SESSION_NAME == "tgads_backend"


def test_settings_overrides(monkeypatch) -> None:
    overrides = {
        "TELEGRAM_BOT_TOKEN": "token",
        "TELEGRAM_API_ID": "987",
        "TELEGRAM_API_HASH": "hash",
        "TELEGRAM_ENABLED": "false",
        "TELEGRAM_SESSION_NAME": "custom_session",
    }

    for key, value in overrides.items():
        monkeypatch.setenv(key, value)

    settings = Settings(_env_file=None)

    assert settings.TELEGRAM_BOT_TOKEN == overrides["TELEGRAM_BOT_TOKEN"]
    assert settings.TELEGRAM_API_ID == int(overrides["TELEGRAM_API_ID"])
    assert settings.TELEGRAM_API_HASH == overrides["TELEGRAM_API_HASH"]
    assert settings.TELEGRAM_ENABLED is False
    assert settings.TELEGRAM_SESSION_NAME == overrides["TELEGRAM_SESSION_NAME"]


def test_get_settings_cached(monkeypatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()

    assert first is second
