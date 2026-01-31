from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_db
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.deal import Deal, DealSourceType
from app.models.deal_event import DealEvent
from app.models.listing import Listing
from app.models.listing_format import ListingFormat
from app.models.user import User
from app.schemas.channel import ChannelRole
from app.schemas.deals import DealCreateFromListing, DealSummary
from app.schemas.listing import (
    ListingCreate,
    ListingFormatCreate,
    ListingFormatSummary,
    ListingFormatUpdate,
    ListingSummary,
    ListingUpdate,
)

router = APIRouter(prefix="/listings", tags=["listings"])

ALLOWED_MEDIA_TYPES = {"image", "video"}


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


def _require_non_empty(value: str | None, *, field: str) -> str:
    if value is None or not value.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")
    return value.strip()


def _require_media_type(value: str | None) -> str:
    normalized = _require_non_empty(value, field="creative_media_type")
    if normalized not in ALLOWED_MEDIA_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid creative_media_type")
    return normalized


def _deal_summary(deal: Deal) -> DealSummary:
    return DealSummary(
        id=deal.id,
        source_type=deal.source_type,
        advertiser_id=deal.advertiser_id,
        channel_id=deal.channel_id,
        channel_owner_id=deal.channel_owner_id,
        listing_id=deal.listing_id,
        listing_format_id=deal.listing_format_id,
        campaign_id=deal.campaign_id,
        campaign_application_id=deal.campaign_application_id,
        price_ton=deal.price_ton,
        ad_type=deal.ad_type,
        creative_text=deal.creative_text,
        creative_media_type=deal.creative_media_type,
        creative_media_ref=deal.creative_media_ref,
        posting_params=deal.posting_params,
        state=deal.state,
        created_at=deal.created_at,
        updated_at=deal.updated_at,
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


@router.post("/{listing_id}/deals", response_model=DealSummary, status_code=status.HTTP_201_CREATED)
def create_deal_from_listing(
    listing_id: int,
    payload: DealCreateFromListing,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealSummary:
    listing = _load_listing(db, listing_id)
    if not listing.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Listing is inactive")

    listing_format = _load_listing_format(db, payload.listing_format_id)
    if listing_format.listing_id != listing.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Format not found")

    creative_text = _require_non_empty(payload.creative_text, field="creative_text")
    creative_media_type = _require_media_type(payload.creative_media_type)
    creative_media_ref = _require_non_empty(payload.creative_media_ref, field="creative_media_ref")

    deal = Deal(
        source_type=DealSourceType.LISTING.value,
        advertiser_id=current_user.id,
        channel_id=listing.channel_id,
        channel_owner_id=listing.owner_id,
        listing_id=listing.id,
        listing_format_id=listing_format.id,
        price_ton=listing_format.price,
        ad_type=listing_format.label,
        creative_text=creative_text,
        creative_media_type=creative_media_type,
        creative_media_ref=creative_media_ref,
        posting_params=payload.posting_params,
    )
    db.add(deal)
    db.flush()

    proposal_event = DealEvent(
        deal_id=deal.id,
        actor_id=current_user.id,
        event_type="proposal",
        payload={
            "price_ton": str(listing_format.price),
            "ad_type": listing_format.label,
            "creative_text": creative_text,
            "creative_media_type": creative_media_type,
            "creative_media_ref": creative_media_ref,
            "posting_params": payload.posting_params,
        },
    )
    db.add(proposal_event)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Deal conflict")

    db.refresh(deal)
    return _deal_summary(deal)
