from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/auth/me")
def read_current_user(current_user: User = Depends(get_current_user)) -> dict[str, int | None | str]:
    return {
        "id": current_user.id,
        "telegram_user_id": current_user.telegram_user_id,
        "preferred_role": current_user.preferred_role,
    }
