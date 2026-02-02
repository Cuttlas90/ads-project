from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.users import (
    UserPreferencesSummary,
    UserPreferencesUpdate,
    UserWalletSummary,
    UserWalletUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


def _require_wallet_address(value: str | None) -> str:
    if value is None or not value.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid wallet address")
    return value.strip()


def _require_preferred_role(value: str | None) -> str:
    if value is None or not value.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid preferred_role")
    normalized = value.strip().lower()
    if normalized not in {"owner", "advertiser"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid preferred_role")
    return normalized


@router.put("/me/wallet", response_model=UserWalletSummary)
def update_wallet(
    payload: UserWalletUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserWalletSummary:
    address = _require_wallet_address(payload.ton_wallet_address)
    current_user.ton_wallet_address = address
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return UserWalletSummary(
        id=current_user.id,
        telegram_user_id=current_user.telegram_user_id,
        ton_wallet_address=current_user.ton_wallet_address,
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
