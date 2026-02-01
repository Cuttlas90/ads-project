from __future__ import annotations

from decimal import Decimal
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
    TON_ENABLED: bool = True
    TON_NETWORK: str | None = None
    TON_CONFIRMATIONS_REQUIRED: int = 3
    TON_FEE_PERCENT: Decimal | None = None
    TON_HOT_WALLET_MNEMONIC: str | None = None
    TONCENTER_API: str | None = None
    TONCENTER_KEY: str | None = None
    TONCONNECT_MANIFEST_URL: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def apply_celery_defaults(self) -> "Settings":
        if self.CELERY_BROKER_URL is None:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if self.CELERY_RESULT_BACKEND is None:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL
        if self.TON_NETWORK is None:
            self.TON_NETWORK = "testnet" if self.ENV == "dev" else "mainnet"
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
