from __future__ import annotations

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "dev"
    APP_NAME: str = "Telegram Ads Marketplace API"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "postgresql+psycopg://ads:ads@postgres:5432/ads"
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_API_ID: int | None = None
    TELEGRAM_API_HASH: str | None = None
    TELEGRAM_ENABLED: bool = True
    TELEGRAM_SESSION_NAME: str = "tgads_backend"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def apply_celery_defaults(self) -> "Settings":
        if self.CELERY_BROKER_URL is None:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if self.CELERY_RESULT_BACKEND is None:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
