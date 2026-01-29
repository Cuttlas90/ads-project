from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.auth.telegram_initdata import AuthError, verify_init_data
from app.models.user import User
from app.settings import Settings, get_settings
from shared.db.session import get_db as shared_get_db


def get_settings_dep() -> Settings:
    return get_settings()


def get_db():
    yield from shared_get_db()


def _get_init_data(request: Request) -> str | None:
    return request.headers.get("X-Telegram-Init-Data") or request.query_params.get("initData")


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
) -> User:
    init_data = _get_init_data(request)
    if not init_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing initData")

    try:
        parsed = verify_init_data(init_data, settings.TELEGRAM_BOT_TOKEN or "")
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user_payload = parsed.get("user")
    if not user_payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user data")

    try:
        user_data = json.loads(user_payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user data") from exc

    try:
        telegram_user_id = int(user_data["id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user id") from exc

    now = datetime.now(timezone.utc)
    user = db.exec(select(User).where(User.telegram_user_id == telegram_user_id)).first()
    if user is None:
        user = User(
            telegram_user_id=telegram_user_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            language_code=user_data.get("language_code"),
            is_premium=user_data.get("is_premium"),
            last_login_at=now,
        )
    else:
        user.username = user_data.get("username")
        user.first_name = user_data.get("first_name")
        user.last_name = user_data.get("last_name")
        user.language_code = user_data.get("language_code")
        user.is_premium = user_data.get("is_premium")
        user.last_login_at = now

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        user = db.exec(select(User).where(User.telegram_user_id == telegram_user_id)).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to persist user")
        user.username = user_data.get("username")
        user.first_name = user_data.get("first_name")
        user.last_name = user_data.get("last_name")
        user.language_code = user_data.get("language_code")
        user.is_premium = user_data.get("is_premium")
        user.last_login_at = now
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        db.refresh(user)

    return user
