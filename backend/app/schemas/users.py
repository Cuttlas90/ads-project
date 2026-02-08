from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserWalletUpdate(BaseModel):
    ton_wallet_address: str


class UserWalletSummary(BaseModel):
    id: int
    telegram_user_id: int
    ton_wallet_address: str | None
    has_wallet: bool


class UserPreferencesUpdate(BaseModel):
    preferred_role: str


class UserPreferencesSummary(BaseModel):
    preferred_role: str | None


class AuthMeSummary(BaseModel):
    id: int
    telegram_user_id: int
    preferred_role: str | None
    ton_wallet_address: str | None
    has_wallet: bool


class UserWalletChallengeSummary(BaseModel):
    challenge: str
    expires_at: datetime
    ttl_seconds: int


class TonProofDomainPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    length_bytes: int = Field(alias="lengthBytes", ge=0)
    value: str


class TonProofPayload(BaseModel):
    timestamp: int
    domain: TonProofDomainPayload
    signature: str
    payload: str


class TonAccountPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    address: str
    chain: str | None = None
    wallet_state_init: str | None = Field(default=None, alias="walletStateInit")
    public_key: str | None = Field(default=None, alias="publicKey")


class UserWalletProofVerifyRequest(BaseModel):
    account: TonAccountPayload
    proof: TonProofPayload
