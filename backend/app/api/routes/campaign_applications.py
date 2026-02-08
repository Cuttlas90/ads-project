from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_db
from app.models.campaign_application import CampaignApplication
from app.models.campaign_request import CampaignRequest
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.channel_stats_snapshot import ChannelStatsSnapshot
from app.models.deal import Deal, DealSourceType
from app.models.deal_event import DealEvent
from app.models.user import User
from app.schemas.campaigns import (
    CampaignApplicationCreate,
    CampaignApplicationListingItem,
    CampaignApplicationPage,
    CampaignApplicationStatsSummary,
    CampaignApplicationSummary,
)
from app.schemas.deals import DealCreateFromCampaignAccept, DealSummary
from app.schemas.channel import ChannelRole

router = APIRouter(prefix="/campaigns", tags=["campaign-applications"])

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
PREMIUM_RATIO_KEY = "premium_ratio"
ALLOWED_MEDIA_TYPES = {"image", "video"}


def _parse_int(value: str | None, *, field: str, minimum: int | None = None) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")
    if minimum is not None and parsed < minimum:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")
    return parsed


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
        placement_type=deal.placement_type,
        exclusive_hours=deal.exclusive_hours,
        retention_hours=deal.retention_hours,
        creative_text=deal.creative_text,
        creative_media_type=deal.creative_media_type,
        creative_media_ref=deal.creative_media_ref,
        posting_params=deal.posting_params,
        state=deal.state,
        created_at=deal.created_at,
        updated_at=deal.updated_at,
    )


def _require_owner_membership(db: Session, *, channel_id: int, user_id: int | None) -> None:
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only channel owners may apply")

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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only channel owners may apply")


def _latest_snapshot_subquery():
    return (
        select(
            ChannelStatsSnapshot.id.label("snapshot_id"),
            ChannelStatsSnapshot.channel_id.label("channel_id"),
            ChannelStatsSnapshot.avg_views.label("avg_views"),
            ChannelStatsSnapshot.language_stats.label("language_stats"),
            ChannelStatsSnapshot.premium_stats.label("premium_stats"),
            func.row_number()
            .over(
                partition_by=ChannelStatsSnapshot.channel_id,
                order_by=(
                    ChannelStatsSnapshot.created_at.desc(),
                    ChannelStatsSnapshot.id.desc(),
                ),
            )
            .label("rn"),
        )
        .subquery()
    )


def _premium_ratio_from_stats(premium_stats) -> float:
    if isinstance(premium_stats, dict):
        value = premium_stats.get(PREMIUM_RATIO_KEY)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def _top_language(language_stats) -> dict[str, float] | None:
    if not isinstance(language_stats, dict):
        return None
    top_key = None
    top_value = None
    for key, value in language_stats.items():
        try:
            ratio = float(value)
        except (TypeError, ValueError):
            continue
        if top_value is None or ratio > top_value:
            top_value = ratio
            top_key = key
    if top_key is None:
        return None
    return {str(top_key): float(top_value)}


def _application_summary(application: CampaignApplication) -> CampaignApplicationSummary:
    return CampaignApplicationSummary(
        id=application.id,
        campaign_id=application.campaign_id,
        channel_id=application.channel_id,
        owner_id=application.owner_id,
        proposed_format_label=application.proposed_format_label,
        message=application.message,
        status=application.status,
        created_at=application.created_at,
    )


@router.post("/{campaign_id}/apply", response_model=CampaignApplicationSummary, status_code=status.HTTP_201_CREATED)
def apply_to_campaign(
    campaign_id: int,
    payload: CampaignApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignApplicationSummary:
    if payload.proposed_format_label is None or not payload.proposed_format_label.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid proposed_format_label")

    campaign = db.exec(select(CampaignRequest).where(CampaignRequest.id == campaign_id)).first()
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    if not campaign.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Campaign is inactive")

    channel = db.exec(select(Channel).where(Channel.id == payload.channel_id)).first()
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    if not channel.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Channel not verified")

    _require_owner_membership(db, channel_id=channel.id, user_id=current_user.id)

    application = CampaignApplication(
        campaign_id=campaign.id,
        channel_id=channel.id,
        owner_id=current_user.id,
        proposed_format_label=payload.proposed_format_label.strip(),
        message=payload.message,
        status="submitted",
    )
    db.add(application)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = (
            db.exec(
                select(CampaignApplication)
                .where(CampaignApplication.campaign_id == campaign.id)
                .where(CampaignApplication.channel_id == channel.id)
            )
            .first()
        )
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application already exists")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application conflict")

    db.refresh(application)
    return _application_summary(application)


@router.get("/{campaign_id}/applications", response_model=CampaignApplicationPage)
def list_campaign_applications(
    campaign_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignApplicationPage:
    campaign = db.exec(select(CampaignRequest).where(CampaignRequest.id == campaign_id)).first()
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    if campaign.advertiser_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    params = request.query_params
    page = _parse_int(params.get("page"), field="page", minimum=1) or DEFAULT_PAGE
    page_size = _parse_int(params.get("page_size"), field="page_size", minimum=1) or DEFAULT_PAGE_SIZE

    snapshot_subq = _latest_snapshot_subquery()
    stmt = (
        select(
            CampaignApplication,
            Channel.username,
            Channel.title,
            snapshot_subq.c.avg_views,
            snapshot_subq.c.language_stats,
            snapshot_subq.c.premium_stats,
        )
        .join(Channel, Channel.id == CampaignApplication.channel_id)
        .join(
            snapshot_subq,
            and_(
                snapshot_subq.c.channel_id == CampaignApplication.channel_id,
                snapshot_subq.c.rn == 1,
            ),
            isouter=True,
        )
        .where(CampaignApplication.campaign_id == campaign_id)
    )

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = db.exec(total_stmt).one()
    total = total_result if isinstance(total_result, int) else total_result[0]

    offset = (page - 1) * page_size
    rows = db.exec(
        stmt.order_by(CampaignApplication.created_at.desc(), CampaignApplication.id.desc())
        .limit(page_size)
        .offset(offset)
    ).all()

    items: list[CampaignApplicationListingItem] = []
    for application, channel_username, channel_title, avg_views, language_stats, premium_stats in rows:
        stats = CampaignApplicationStatsSummary(
            avg_views=avg_views,
            premium_ratio=_premium_ratio_from_stats(premium_stats),
            language_stats=_top_language(language_stats),
        )
        items.append(
            CampaignApplicationListingItem(
                id=application.id,
                channel_id=application.channel_id,
                channel_username=channel_username,
                channel_title=channel_title,
                proposed_format_label=application.proposed_format_label,
                status=application.status,
                created_at=application.created_at,
                stats=stats,
            )
        )

    return CampaignApplicationPage(
        page=page,
        page_size=page_size,
        total=total,
        items=items,
    )


@router.post(
    "/{campaign_id}/applications/{application_id}/accept",
    response_model=DealSummary,
    status_code=status.HTTP_201_CREATED,
)
def accept_campaign_application(
    campaign_id: int,
    application_id: int,
    payload: DealCreateFromCampaignAccept,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealSummary:
    campaign = db.exec(select(CampaignRequest).where(CampaignRequest.id == campaign_id)).first()
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    if campaign.advertiser_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    application = db.exec(select(CampaignApplication).where(CampaignApplication.id == application_id)).first()
    if application is None or application.campaign_id != campaign_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if application.status != "submitted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application is not submitted")

    existing_campaign = db.exec(select(Deal).where(Deal.campaign_id == campaign_id)).first()
    if existing_campaign is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Deal already exists")
    existing_application = db.exec(
        select(Deal).where(Deal.campaign_application_id == application_id)
    ).first()
    if existing_application is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Deal already exists")

    price_ton = payload.price_ton
    if price_ton is None or price_ton < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid price_ton")

    ad_type = _require_non_empty(payload.ad_type, field="ad_type")
    creative_text = _require_non_empty(payload.creative_text, field="creative_text")
    creative_media_type = _require_media_type(payload.creative_media_type)
    creative_media_ref = _require_non_empty(payload.creative_media_ref, field="creative_media_ref")

    deal = Deal(
        source_type=DealSourceType.CAMPAIGN.value,
        advertiser_id=current_user.id,
        channel_id=application.channel_id,
        channel_owner_id=application.owner_id,
        campaign_id=campaign.id,
        campaign_application_id=application.id,
        price_ton=price_ton,
        ad_type=ad_type,
        creative_text=creative_text,
        creative_media_type=creative_media_type,
        creative_media_ref=creative_media_ref,
        posting_params=payload.posting_params,
    )
    db.add(deal)
    db.flush()

    application.status = "accepted"
    db.add(application)

    proposal_event = DealEvent(
        deal_id=deal.id,
        actor_id=current_user.id,
        event_type="proposal",
        payload={
            "price_ton": str(price_ton),
            "ad_type": ad_type,
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
