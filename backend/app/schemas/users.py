from __future__ import annotations

from pydantic import BaseModel


class UserWalletUpdate(BaseModel):
    ton_wallet_address: str


class UserWalletSummary(BaseModel):
    id: int
    telegram_user_id: int
    ton_wallet_address: str | None
