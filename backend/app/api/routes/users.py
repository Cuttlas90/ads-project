from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.users import UserWalletSummary, UserWalletUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _require_wallet_address(value: str | None) -> str:
    if value is None or not value.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid wallet address")
    return value.strip()


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
