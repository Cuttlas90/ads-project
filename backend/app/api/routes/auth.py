from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_registered_user
from app.models.user import User
from app.schemas.users import AuthMeSummary

router = APIRouter()


@router.get("/auth/me", response_model=AuthMeSummary)
def read_current_user(current_user: User = Depends(get_registered_user)) -> AuthMeSummary:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is missing")
    has_wallet = bool(current_user.ton_wallet_address and current_user.ton_wallet_address.strip())
    return AuthMeSummary(
        id=current_user.id,
        telegram_user_id=current_user.telegram_user_id,
        preferred_role=current_user.preferred_role,
        ton_wallet_address=current_user.ton_wallet_address,
        has_wallet=has_wallet,
    )
