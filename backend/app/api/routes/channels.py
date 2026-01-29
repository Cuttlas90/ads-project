from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_db
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.user import User
from app.schemas.channel import ChannelCreate, ChannelRole, ChannelWithRole

router = APIRouter(prefix="/channels", tags=["channels"])

_USERNAME_PATTERN = re.compile(r"^[a-z0-9_]{5,32}$")


def _normalize_username(raw_username: str) -> str:
    normalized = raw_username.strip()
    if normalized.startswith("@"):
        normalized = normalized[1:]
    normalized = normalized.lower()

    if "/" in normalized or "t.me" in normalized or "http://" in normalized or "https://" in normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username")

    if not _USERNAME_PATTERN.fullmatch(normalized):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username")

    return normalized


@router.post("", response_model=ChannelWithRole, status_code=status.HTTP_201_CREATED)
def submit_channel(
    payload: ChannelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChannelWithRole:
    normalized = _normalize_username(payload.username)

    existing = db.exec(select(Channel).where(Channel.username == normalized)).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Channel already exists")

    channel = Channel(username=normalized, is_verified=False)
    db.add(channel)

    try:
        db.flush()
        membership = ChannelMember(
            channel_id=channel.id,
            user_id=current_user.id,
            role=ChannelRole.owner.value,
        )
        db.add(membership)
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.exec(select(Channel).where(Channel.username == normalized)).first() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Channel already exists")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Channel conflict")

    db.refresh(channel)
    return ChannelWithRole(
        id=channel.id,
        username=channel.username,
        title=channel.title,
        is_verified=channel.is_verified,
        role=ChannelRole.owner,
    )


@router.get("", response_model=list[ChannelWithRole])
def list_channels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChannelWithRole]:
    if current_user.id is None:
        return []

    stmt = (
        select(Channel, ChannelMember.role)
        .join(ChannelMember, ChannelMember.channel_id == Channel.id)
        .where(ChannelMember.user_id == current_user.id)
        .where(ChannelMember.role.in_([ChannelRole.owner.value, ChannelRole.manager.value]))
        .order_by(Channel.id)
    )
    results = db.exec(stmt).all()

    return [
        ChannelWithRole(
            id=channel.id,
            username=channel.username,
            title=channel.title,
            is_verified=channel.is_verified,
            role=ChannelRole(role),
        )
        for channel, role in results
    ]
