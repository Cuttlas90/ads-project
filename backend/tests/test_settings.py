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
    "TELEGRAM_SESSION_STRING",
    "TELEGRAM_SESSION_STRING_PATH",
    "TELEGRAM_MTPROXY_HOST",
    "TELEGRAM_MTPROXY_PORT",
    "TELEGRAM_MTPROXY_SECRET",
    "TELEGRAM_MEDIA_CHANNEL_ID",
    "CORS_ALLOW_ORIGINS",
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
    assert settings.TELEGRAM_SESSION_STRING is None
    assert settings.TELEGRAM_SESSION_STRING_PATH is None
    assert settings.TELEGRAM_MTPROXY_HOST is None
    assert settings.TELEGRAM_MTPROXY_PORT is None
    assert settings.TELEGRAM_MTPROXY_SECRET is None
    assert settings.TELEGRAM_MEDIA_CHANNEL_ID is None
    assert settings.CORS_ALLOW_ORIGINS == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://app.chainofwinners.com",
    ]


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
        "TELEGRAM_SESSION_STRING": "encoded-session-string",
        "TELEGRAM_SESSION_STRING_PATH": "/tmp/telethon.session",
        "TELEGRAM_MTPROXY_HOST": "91.239.192.223",
        "TELEGRAM_MTPROXY_PORT": "15",
        "TELEGRAM_MTPROXY_SECRET": "ee1603010200010001fc030386e24c3a",
        "TELEGRAM_MEDIA_CHANNEL_ID": "123",
        "CORS_ALLOW_ORIGINS": '["https://app.chainofwinners.com", "https://admin.chainofwinners.com"]',
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
    assert settings.TELEGRAM_SESSION_STRING == overrides["TELEGRAM_SESSION_STRING"]
    assert settings.TELEGRAM_SESSION_STRING_PATH == overrides["TELEGRAM_SESSION_STRING_PATH"]
    assert settings.TELEGRAM_MTPROXY_HOST == overrides["TELEGRAM_MTPROXY_HOST"]
    assert settings.TELEGRAM_MTPROXY_PORT == int(overrides["TELEGRAM_MTPROXY_PORT"])
    assert settings.TELEGRAM_MTPROXY_SECRET == overrides["TELEGRAM_MTPROXY_SECRET"]
    assert settings.TELEGRAM_MEDIA_CHANNEL_ID == int(overrides["TELEGRAM_MEDIA_CHANNEL_ID"])
    assert settings.CORS_ALLOW_ORIGINS == [
        "https://app.chainofwinners.com",
        "https://admin.chainofwinners.com",
    ]


def test_settings_cors_csv_with_quotes(monkeypatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv(
        "CORS_ALLOW_ORIGINS",
        "'http://localhost:5173', \"https://app.chainofwinners.com\"",
    )

    settings = Settings(_env_file=None)

    assert settings.CORS_ALLOW_ORIGINS == [
        "http://localhost:5173",
        "https://app.chainofwinners.com",
    ]


def test_get_settings_cached(monkeypatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()

    assert first is second
