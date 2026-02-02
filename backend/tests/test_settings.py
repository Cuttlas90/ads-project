from app.settings import Settings, get_settings


_ENV_KEYS = [
    "ENV",
    "APP_NAME",
    "LOG_LEVEL",
    "DATABASE_URL",
    "REDIS_URL",
    "CELERY_BROKER_URL",
    "CELERY_RESULT_BACKEND",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_API_ID",
    "TELEGRAM_API_HASH",
    "TELEGRAM_ENABLED",
    "TELEGRAM_SESSION_NAME",
    "TELEGRAM_MEDIA_CHANNEL_ID",
]


def test_settings_defaults(monkeypatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    settings = Settings(_env_file=None)

    assert settings.ENV == "dev"
    assert settings.APP_NAME == "Telegram Ads Marketplace API"
    assert settings.LOG_LEVEL == "INFO"
    assert settings.DATABASE_URL == "postgresql+psycopg://ads:ads@postgres:5432/ads"
    assert settings.REDIS_URL == "redis://redis:6379/0"
    assert settings.CELERY_BROKER_URL == settings.REDIS_URL
    assert settings.CELERY_RESULT_BACKEND == settings.REDIS_URL
    assert settings.TELEGRAM_BOT_TOKEN is None
    assert settings.TELEGRAM_API_ID is None
    assert settings.TELEGRAM_API_HASH is None
    assert settings.TELEGRAM_ENABLED is True
    assert settings.TELEGRAM_SESSION_NAME == "tgads_backend"
    assert settings.TELEGRAM_MEDIA_CHANNEL_ID is None


def test_settings_overrides(monkeypatch) -> None:
    overrides = {
        "ENV": "prod",
        "APP_NAME": "Test API",
        "LOG_LEVEL": "DEBUG",
        "DATABASE_URL": "postgresql+psycopg://user:pass@localhost:5432/db",
        "REDIS_URL": "redis://localhost:6379/1",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/2",
        "TELEGRAM_BOT_TOKEN": "test-token",
        "TELEGRAM_API_ID": "12345",
        "TELEGRAM_API_HASH": "hash",
        "TELEGRAM_ENABLED": "false",
        "TELEGRAM_SESSION_NAME": "custom_session",
        "TELEGRAM_MEDIA_CHANNEL_ID": "123",
    }

    for key, value in overrides.items():
        monkeypatch.setenv(key, value)

    settings = Settings(_env_file=None)

    assert settings.ENV == overrides["ENV"]
    assert settings.APP_NAME == overrides["APP_NAME"]
    assert settings.LOG_LEVEL == overrides["LOG_LEVEL"]
    assert settings.DATABASE_URL == overrides["DATABASE_URL"]
    assert settings.REDIS_URL == overrides["REDIS_URL"]
    assert settings.CELERY_BROKER_URL == overrides["REDIS_URL"]
    assert settings.CELERY_RESULT_BACKEND == overrides["CELERY_RESULT_BACKEND"]
    assert settings.TELEGRAM_BOT_TOKEN == overrides["TELEGRAM_BOT_TOKEN"]
    assert settings.TELEGRAM_API_ID == int(overrides["TELEGRAM_API_ID"])
    assert settings.TELEGRAM_API_HASH == overrides["TELEGRAM_API_HASH"]
    assert settings.TELEGRAM_ENABLED is False
    assert settings.TELEGRAM_SESSION_NAME == overrides["TELEGRAM_SESSION_NAME"]
    assert settings.TELEGRAM_MEDIA_CHANNEL_ID == int(overrides["TELEGRAM_MEDIA_CHANNEL_ID"])


def test_get_settings_cached(monkeypatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()

    assert first is second
