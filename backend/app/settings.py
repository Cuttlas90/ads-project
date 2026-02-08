from __future__ import annotations

import json
from decimal import Decimal
from functools import lru_cache
from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
    TELEGRAM_SESSION_STRING: str | None = None
    TELEGRAM_SESSION_STRING_PATH: str | None = None
    TELEGRAM_MTPROXY_HOST: str | None = None
    TELEGRAM_MTPROXY_PORT: int | None = None
    TELEGRAM_MTPROXY_SECRET: str | None = None
    TELEGRAM_MEDIA_CHANNEL_ID: int | None = None
    TELEGRAM_BUSINESS_CONNECTION_ID: str | None = None
    TON_ENABLED: bool = True
    TON_NETWORK: str | None = None
    TON_CONFIRMATIONS_REQUIRED: int = 3
    TON_FEE_PERCENT: Decimal | None = None
    TON_REFUND_NETWORK_FEE: Decimal = Decimal("0.02")
    TON_HOT_WALLET_MNEMONIC: str | None = None
    TONCENTER_API: str | None = None
    TONCENTER_KEY: str | None = None
    TONCONNECT_MANIFEST_URL: str | None = None
    VERIFICATION_WINDOW_DEFAULT_HOURS: int = 24
    CORS_ALLOW_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://app.chainofwinners.com",
    ]

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

    @field_validator("CORS_ALLOW_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        def normalize(origins: list[object]) -> list[str]:
            parsed: list[str] = []
            for origin in origins:
                item = str(origin).strip().strip("'\"")
                if item:
                    parsed.append(item)
            return parsed

        if isinstance(value, (list, tuple, set)):
            return normalize(list(value))
        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []
            if raw_value.startswith("["):
                try:
                    decoded = json.loads(raw_value)
                    if isinstance(decoded, list):
                        return normalize(decoded)
                except json.JSONDecodeError:
                    pass
            return normalize(raw_value.split(","))
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
