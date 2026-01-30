from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_db
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.user import User
from app.schemas.channel import ChannelRole
from app.schemas.channel_manager import ChannelManagerCreate, ChannelManagerSummary

router = APIRouter(prefix="/channels/{channel_id}/managers", tags=["channel-managers"])


def _load_channel(db: Session, channel_id: int) -> Channel:
    channel = db.exec(select(Channel).where(Channel.id == channel_id)).first()
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return channel


def _require_owner(db: Session, *, channel_id: int, user_id: int | None) -> None:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only channel owners may manage managers",
        )

    membership = (
        db.exec(
            select(ChannelMember)
            .where(ChannelMember.channel_id == channel_id)
            .where(ChannelMember.user_id == user_id)
            .where(ChannelMember.role == ChannelRole.owner.value)
        )
        .first()
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only channel owners may manage managers",
        )


def _require_member(db: Session, *, channel_id: int, user_id: int | None) -> None:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only channel members may view managers",
        )

    membership = (
        db.exec(
            select(ChannelMember)
            .where(ChannelMember.channel_id == channel_id)
            .where(ChannelMember.user_id == user_id)
            .where(ChannelMember.role.in_([ChannelRole.owner.value, ChannelRole.manager.value]))
        )
        .first()
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only channel members may view managers",
        )


@router.post("", response_model=ChannelManagerSummary, status_code=status.HTTP_201_CREATED)
def add_manager(
    channel_id: int,
    payload: ChannelManagerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChannelManagerSummary:
    channel = _load_channel(db, channel_id)
    _require_owner(db, channel_id=channel.id, user_id=current_user.id)

    target_user = db.exec(
        select(User).where(User.telegram_user_id == payload.telegram_user_id)
    ).first()
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Owner cannot add themselves as manager",
        )

    existing = (
        db.exec(
            select(ChannelMember)
            .where(ChannelMember.channel_id == channel.id)
            .where(ChannelMember.user_id == target_user.id)
        )
        .first()
    )
    if existing is not None:
        detail = "User already a manager" if existing.role == ChannelRole.manager.value else "User already a member"
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    membership = ChannelMember(
        channel_id=channel.id,
        user_id=target_user.id,
        role=ChannelRole.manager.value,
    )
    db.add(membership)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already a manager")

    return ChannelManagerSummary(
        telegram_user_id=target_user.telegram_user_id,
        role=ChannelRole.manager,
    )


@router.delete("/{telegram_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_manager(
    channel_id: int,
    telegram_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    channel = _load_channel(db, channel_id)
    _require_owner(db, channel_id=channel.id, user_id=current_user.id)

    if current_user.telegram_user_id == telegram_user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Owner cannot remove themselves",
        )

    target_user = db.exec(
        select(User).where(User.telegram_user_id == telegram_user_id)
    ).first()
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manager not found")

    membership = (
        db.exec(
            select(ChannelMember)
            .where(ChannelMember.channel_id == channel.id)
            .where(ChannelMember.user_id == target_user.id)
            .where(ChannelMember.role == ChannelRole.manager.value)
        )
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manager not found")

    db.delete(membership)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("", response_model=list[ChannelManagerSummary])
def list_managers(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChannelManagerSummary]:
    channel = _load_channel(db, channel_id)
    _require_member(db, channel_id=channel.id, user_id=current_user.id)

    stmt = (
        select(User.telegram_user_id, ChannelMember.role)
        .join(ChannelMember, ChannelMember.user_id == User.id)
        .where(ChannelMember.channel_id == channel.id)
        .where(ChannelMember.role == ChannelRole.manager.value)
        .order_by(User.telegram_user_id)
    )
    results = db.exec(stmt).all()

    return [
        ChannelManagerSummary(
            telegram_user_id=telegram_user_id,
            role=ChannelRole(role),
        )
        for telegram_user_id, role in results
    ]
