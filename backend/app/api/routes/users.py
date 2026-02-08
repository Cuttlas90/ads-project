from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_db, get_settings_dep
from app.models.user import User
from app.models.wallet_proof_challenge import WalletProofChallenge
from app.schemas.users import (
    UserPreferencesSummary,
    UserPreferencesUpdate,
    UserWalletChallengeSummary,
    UserWalletProofVerifyRequest,
    UserWalletSummary,
)
from app.services.ton.wallet_proof import TonProofVerificationError, resolve_ton_proof_domain, verify_ton_proof
from app.settings import Settings

router = APIRouter(prefix="/users", tags=["users"])

WALLET_PROOF_CHALLENGE_TTL_SECONDS = 300


def _require_preferred_role(value: str | None) -> str:
    if value is None or not value.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid preferred_role")
    normalized = value.strip().lower()
    if normalized not in {"owner", "advertiser"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid preferred_role")
    return normalized


def _require_user_id(current_user: User) -> int:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is missing")
    return current_user.id


def _has_wallet(address: str | None) -> bool:
    return bool(address and address.strip())


def _is_expired(expires_at: datetime, now_utc: datetime) -> bool:
    if expires_at.tzinfo is None:
        return expires_at <= now_utc.replace(tzinfo=None)
    return expires_at <= now_utc


def _db_now(expires_at: datetime, now_utc: datetime) -> datetime:
    if expires_at.tzinfo is None:
        return now_utc.replace(tzinfo=None)
    return now_utc


@router.put("/me/wallet", deprecated=True)
def update_wallet_legacy(current_user: User = Depends(get_current_user)) -> None:
    _require_user_id(current_user)
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "Wallet update requires TonConnect proof. "
            "Use POST /users/me/wallet/challenge then POST /users/me/wallet/verify."
        ),
    )


@router.post("/me/wallet/challenge", response_model=UserWalletChallengeSummary)
def issue_wallet_challenge(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserWalletChallengeSummary:
    user_id = _require_user_id(current_user)
    now = datetime.now(timezone.utc)
    challenge = secrets.token_urlsafe(24)
    expires_at = now + timedelta(seconds=WALLET_PROOF_CHALLENGE_TTL_SECONDS)

    record = WalletProofChallenge(
        user_id=user_id,
        challenge=challenge,
        expires_at=expires_at,
    )
    db.add(record)
    db.commit()

    return UserWalletChallengeSummary(
        challenge=challenge,
        expires_at=expires_at,
        ttl_seconds=WALLET_PROOF_CHALLENGE_TTL_SECONDS,
    )


@router.post("/me/wallet/verify", response_model=UserWalletSummary)
def verify_wallet(
    payload: UserWalletProofVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings_dep),
) -> UserWalletSummary:
    user_id = _require_user_id(current_user)
    now = datetime.now(timezone.utc)

    challenge = db.exec(
        select(WalletProofChallenge).where(WalletProofChallenge.challenge == payload.proof.payload)
    ).first()
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid challenge")

    if challenge.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Challenge does not belong to current user")

    if challenge.consumed_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Challenge has already been used")

    if _is_expired(challenge.expires_at, now):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Challenge has expired")

    try:
        expected_domain = resolve_ton_proof_domain(settings)
        verify_ton_proof(
            account_address=payload.account.address,
            account_public_key=payload.account.public_key,
            proof_domain_value=payload.proof.domain.value,
            proof_domain_length_bytes=payload.proof.domain.length_bytes,
            proof_timestamp=payload.proof.timestamp,
            proof_payload=payload.proof.payload,
            proof_signature=payload.proof.signature,
            expected_domain=expected_domain,
            expected_payload=challenge.challenge,
            max_age_seconds=WALLET_PROOF_CHALLENGE_TTL_SECONDS,
            now=now,
        )
    except TonProofVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db_now = _db_now(challenge.expires_at, now)

    consume_stmt = (
        update(WalletProofChallenge)
        .where(WalletProofChallenge.id == challenge.id)
        .where(WalletProofChallenge.user_id == user_id)
        .where(WalletProofChallenge.consumed_at.is_(None))
        .where(WalletProofChallenge.expires_at > db_now)
        .values(consumed_at=db_now)
    )
    consume_result = db.exec(consume_stmt)
    if consume_result.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Challenge is no longer valid")

    normalized_address = payload.account.address.strip()
    if not normalized_address:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid wallet address")

    current_user.ton_wallet_address = normalized_address
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is missing")

    return UserWalletSummary(
        id=current_user.id,
        telegram_user_id=current_user.telegram_user_id,
        ton_wallet_address=current_user.ton_wallet_address,
        has_wallet=_has_wallet(current_user.ton_wallet_address),
    )


@router.put("/me/preferences", response_model=UserPreferencesSummary)
def update_preferences(
    payload: UserPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserPreferencesSummary:
    preferred_role = _require_preferred_role(payload.preferred_role)
    current_user.preferred_role = preferred_role
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return UserPreferencesSummary(preferred_role=current_user.preferred_role)
