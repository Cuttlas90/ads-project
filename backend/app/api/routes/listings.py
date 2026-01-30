from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_db
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.listing import Listing
from app.models.listing_format import ListingFormat
from app.models.user import User
from app.schemas.channel import ChannelRole
from app.schemas.listing import (
    ListingCreate,
    ListingFormatCreate,
    ListingFormatSummary,
    ListingFormatUpdate,
    ListingSummary,
    ListingUpdate,
)

router = APIRouter(prefix="/listings", tags=["listings"])


def _load_channel(db: Session, channel_id: int) -> Channel:
    channel = db.exec(select(Channel).where(Channel.id == channel_id)).first()
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return channel


def _load_listing(db: Session, listing_id: int) -> Listing:
    listing = db.exec(select(Listing).where(Listing.id == listing_id)).first()
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return listing


def _load_listing_format(db: Session, format_id: int) -> ListingFormat:
    listing_format = db.exec(select(ListingFormat).where(ListingFormat.id == format_id)).first()
    if listing_format is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Format not found")
    return listing_format


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


def _require_listing_owner(listing: Listing, user_id: int | None) -> None:
    if user_id is None or listing.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only listing owners may manage listings",
        )


@router.post("", response_model=ListingSummary, status_code=status.HTTP_201_CREATED)
def create_listing(
    payload: ListingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListingSummary:
    channel = _load_channel(db, payload.channel_id)
    _require_owner_membership(db, channel_id=channel.id, user_id=current_user.id)

    listing = Listing(channel_id=channel.id, owner_id=current_user.id, is_active=True)
    db.add(listing)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.exec(select(Listing).where(Listing.channel_id == channel.id)).first()
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Listing already exists")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Listing conflict")

    db.refresh(listing)
    return ListingSummary(
        id=listing.id,
        channel_id=listing.channel_id,
        owner_id=listing.owner_id,
        is_active=listing.is_active,
    )


@router.put("/{listing_id}", response_model=ListingSummary)
def update_listing(
    listing_id: int,
    payload: ListingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListingSummary:
    listing = _load_listing(db, listing_id)
    _require_listing_owner(listing, current_user.id)

    listing.is_active = payload.is_active
    db.add(listing)
    db.commit()
    db.refresh(listing)

    return ListingSummary(
        id=listing.id,
        channel_id=listing.channel_id,
        owner_id=listing.owner_id,
        is_active=listing.is_active,
    )


@router.post("/{listing_id}/formats", response_model=ListingFormatSummary, status_code=status.HTTP_201_CREATED)
def create_listing_format(
    listing_id: int,
    payload: ListingFormatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListingFormatSummary:
    listing = _load_listing(db, listing_id)
    _require_listing_owner(listing, current_user.id)

    listing_format = ListingFormat(
        listing_id=listing.id,
        label=payload.label,
        price=payload.price,
    )
    db.add(listing_format)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Format label already exists")

    db.refresh(listing_format)
    return ListingFormatSummary(
        id=listing_format.id,
        listing_id=listing_format.listing_id,
        label=listing_format.label,
        price=listing_format.price,
    )


@router.put("/{listing_id}/formats/{format_id}", response_model=ListingFormatSummary)
def update_listing_format(
    listing_id: int,
    format_id: int,
    payload: ListingFormatUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListingFormatSummary:
    listing = _load_listing(db, listing_id)
    _require_listing_owner(listing, current_user.id)

    listing_format = _load_listing_format(db, format_id)
    if listing_format.listing_id != listing.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Format not found")

    if payload.label is None and payload.price is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    if payload.label is not None:
        listing_format.label = payload.label
    if payload.price is not None:
        listing_format.price = payload.price

    db.add(listing_format)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Format label already exists")

    db.refresh(listing_format)
    return ListingFormatSummary(
        id=listing_format.id,
        listing_id=listing_format.listing_id,
        label=listing_format.label,
        price=listing_format.price,
    )
