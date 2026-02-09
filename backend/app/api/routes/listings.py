from __future__ import annotations

from datetime import timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_db, get_settings_dep
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.deal import Deal, DealSourceType
from app.models.deal_event import DealEvent
from app.models.listing import Listing
from app.models.listing_format import ListingFormat
from app.models.user import User
from app.schemas.channel import ChannelRole
from app.schemas.deals import DealCreateFromListing, DealCreativeUploadResponse, DealSummary
from app.schemas.listing import (
    ListingCreate,
    ListingFormatCreate,
    ListingFormatSummary,
    ListingFormatUpdate,
    ListingSummary,
    ListingUpdate,
)
from app.settings import Settings
from shared.telegram.bot_api import BotApiService
from shared.telegram.errors import TelegramApiError, TelegramConfigError

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


def _normalize_datetime(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


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
        placement_type=deal.placement_type,
        exclusive_hours=deal.exclusive_hours,
        retention_hours=deal.retention_hours,
        creative_text=deal.creative_text,
        creative_media_type=deal.creative_media_type,
        creative_media_ref=deal.creative_media_ref,
        posting_params=deal.posting_params,
        scheduled_at=deal.scheduled_at,
        verification_window_hours=deal.verification_window_hours,
        posted_at=deal.posted_at,
        posted_message_id=deal.posted_message_id,
        posted_content_hash=deal.posted_content_hash,
        verified_at=deal.verified_at,
        state=deal.state,
        created_at=deal.created_at,
        updated_at=deal.updated_at,
    )


def _listing_has_formats(db: Session, listing_id: int) -> bool:
    count = db.exec(
        select(func.count())
        .select_from(ListingFormat)
        .where(ListingFormat.listing_id == listing_id)
    ).one()
    total = count if isinstance(count, int) else count[0]
    return total > 0


@router.post("", response_model=ListingSummary, status_code=status.HTTP_201_CREATED)
def create_listing(
    payload: ListingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListingSummary:
    channel = _load_channel(db, payload.channel_id)
    _require_owner_membership(db, channel_id=channel.id, user_id=current_user.id)

    listing = Listing(channel_id=channel.id, owner_id=current_user.id, is_active=False)
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

    if payload.is_active and not _listing_has_formats(db, listing.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Listing must have at least one format before activation",
        )

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
        placement_type=payload.placement_type,
        exclusive_hours=payload.exclusive_hours,
        retention_hours=payload.retention_hours,
        price=payload.price,
    )
    db.add(listing_format)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Format terms already exist")

    db.refresh(listing_format)
    return ListingFormatSummary(
        id=listing_format.id,
        listing_id=listing_format.listing_id,
        placement_type=listing_format.placement_type,
        exclusive_hours=listing_format.exclusive_hours,
        retention_hours=listing_format.retention_hours,
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

    if (
        payload.placement_type is None
        and payload.exclusive_hours is None
        and payload.retention_hours is None
        and payload.price is None
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    if payload.placement_type is not None:
        listing_format.placement_type = payload.placement_type
    if payload.exclusive_hours is not None:
        listing_format.exclusive_hours = payload.exclusive_hours
    if payload.retention_hours is not None:
        listing_format.retention_hours = payload.retention_hours
    if payload.price is not None:
        listing_format.price = payload.price

    db.add(listing_format)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Format terms already exist")

    db.refresh(listing_format)
    return ListingFormatSummary(
        id=listing_format.id,
        listing_id=listing_format.listing_id,
        placement_type=listing_format.placement_type,
        exclusive_hours=listing_format.exclusive_hours,
        retention_hours=listing_format.retention_hours,
        price=listing_format.price,
    )


@router.post("/{listing_id}/creative/upload", response_model=DealCreativeUploadResponse)
def upload_listing_creative_media(
    listing_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings_dep),
) -> DealCreativeUploadResponse:
    listing = _load_listing(db, listing_id)
    if not listing.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Listing is inactive")

    content_type = file.content_type or ""
    if content_type.startswith("image/"):
        media_type = "image"
    elif content_type.startswith("video/"):
        media_type = "video"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid creative_media_type")

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty upload")

    service = BotApiService(settings)
    try:
        result = service.upload_media(
            media_type=media_type,
            filename=file.filename or f"creative.{media_type}",
            content=content,
        )
    except (TelegramApiError, TelegramConfigError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to upload media") from exc

    return DealCreativeUploadResponse(
        creative_media_ref=result["file_id"],
        creative_media_type=result["media_type"],
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
    scheduled_at = _normalize_datetime(payload.start_at)

    deal = Deal(
        source_type=DealSourceType.LISTING.value,
        advertiser_id=current_user.id,
        channel_id=listing.channel_id,
        channel_owner_id=listing.owner_id,
        listing_id=listing.id,
        listing_format_id=listing_format.id,
        price_ton=listing_format.price,
        ad_type=listing_format.placement_type,
        placement_type=listing_format.placement_type,
        exclusive_hours=listing_format.exclusive_hours,
        retention_hours=listing_format.retention_hours,
        creative_text=creative_text,
        creative_media_type=creative_media_type,
        creative_media_ref=creative_media_ref,
        scheduled_at=scheduled_at,
        posting_params=payload.posting_params,
        verification_window_hours=listing_format.retention_hours,
    )
    db.add(deal)
    db.flush()

    proposal_event = DealEvent(
        deal_id=deal.id,
        actor_id=current_user.id,
        event_type="proposal",
        payload={
            "price_ton": str(listing_format.price),
            "ad_type": listing_format.placement_type,
            "placement_type": listing_format.placement_type,
            "exclusive_hours": listing_format.exclusive_hours,
            "retention_hours": listing_format.retention_hours,
            "creative_text": creative_text,
            "creative_media_type": creative_media_type,
            "creative_media_ref": creative_media_ref,
            "start_at": scheduled_at.isoformat() if scheduled_at else None,
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
