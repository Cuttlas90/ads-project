from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_db, get_settings_dep
from app.domain.channel_verification import (
    ChannelAccessDenied,
    ChannelBotPermissionDenied,
    ChannelNotFound,
    ChannelVerificationError,
)
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.listing import Listing
from app.models.listing_format import ListingFormat
from app.models.user import User
from app.schemas.channel import ChannelCreate, ChannelRole, ChannelSummary, ChannelWithRole
from app.schemas.listing import ChannelListingResponse, ListingDetail, ListingFormatSummary
from app.services.channel_verify import verify_channel
from app.settings import Settings
from shared.telegram import BotApiService, TelegramClientService

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


def _require_owner_membership(db: Session, *, channel_id: int, user_id: int | None) -> None:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only channel owners may manage listings",
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
            detail="Only channel owners may manage listings",
        )


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


@router.get("/{channel_id}/listing", response_model=ChannelListingResponse)
def read_channel_listing(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChannelListingResponse:
    _require_owner_membership(db, channel_id=channel_id, user_id=current_user.id)

    listing = db.exec(select(Listing).where(Listing.channel_id == channel_id)).first()
    if listing is None:
        return ChannelListingResponse(has_listing=False, listing=None)

    formats = db.exec(
        select(ListingFormat)
        .where(ListingFormat.listing_id == listing.id)
        .order_by(
            ListingFormat.placement_type.asc(),
            ListingFormat.exclusive_hours.asc(),
            ListingFormat.retention_hours.asc(),
            ListingFormat.price.asc(),
            ListingFormat.id.asc(),
        )
    ).all()

    return ChannelListingResponse(
        has_listing=True,
        listing=ListingDetail(
            id=listing.id,
            channel_id=listing.channel_id,
            owner_id=listing.owner_id,
            is_active=listing.is_active,
            formats=[
                ListingFormatSummary(
                    id=format_row.id,
                    listing_id=format_row.listing_id,
                    placement_type=format_row.placement_type,
                    exclusive_hours=format_row.exclusive_hours,
                    retention_hours=format_row.retention_hours,
                    price=format_row.price,
                )
                for format_row in formats
            ],
        ),
    )


@router.post("/{channel_id}/verify", response_model=ChannelSummary)
async def verify_channel_endpoint(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings_dep),
) -> ChannelSummary:
    telegram_client = TelegramClientService(settings)
    bot_api = BotApiService(settings)
    try:
        channel = await verify_channel(
            channel_id=channel_id,
            user=current_user,
            db=db,
            telegram_client=telegram_client,
            bot_api=bot_api,
        )
    except ChannelNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (ChannelAccessDenied, ChannelBotPermissionDenied) as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ChannelVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return ChannelSummary(
        id=channel.id,
        username=channel.username,
        title=channel.title,
        is_verified=channel.is_verified,
    )
