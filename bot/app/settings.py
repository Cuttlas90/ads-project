from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_API_ID: int | None = None
    TELEGRAM_API_HASH: str | None = None
    TELEGRAM_ENABLED: bool = True
    TELEGRAM_SESSION_NAME: str = "tgads_backend"
    TELEGRAM_SESSION_STRING: str | None = None
    TELEGRAM_SESSION_STRING_PATH: str | None = None
    TELEGRAM_MTPROXY_HOST: str | None = None
    TELEGRAM_MTPROXY_PORT: int | None = None
    TELEGRAM_MTPROXY_SECRET: str | None = None
    TELEGRAM_MEDIA_CHANNEL_ID: int | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
