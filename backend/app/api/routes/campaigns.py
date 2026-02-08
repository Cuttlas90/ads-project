from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, or_
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_db
from app.models.campaign_application import CampaignApplication
from app.models.campaign_request import CampaignLifecycleState, CampaignRequest
from app.models.channel import Channel
from app.models.user import User
from app.schemas.campaigns import (
    CampaignDiscoverItem,
    CampaignDiscoverPage,
    CampaignOfferInboxItem,
    CampaignOfferInboxPage,
    CampaignRequestCreate,
    CampaignRequestPage,
    CampaignRequestSummary,
)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20


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


def _require_non_empty(value: str | None, *, field: str) -> None:
    if value is None or not value.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")


def _validate_budget(value: Decimal | None, *, field: str) -> None:
    if value is None:
        return
    try:
        normalized = Decimal(value)
    except (InvalidOperation, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")
    if normalized < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")


def _validate_max_acceptances(value: int | None) -> int:
    if value is None:
        return 10
    if value < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid max_acceptances")
    return value


def _parse_search(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized


def _campaign_summary(campaign: CampaignRequest) -> CampaignRequestSummary:
    return CampaignRequestSummary(
        id=campaign.id,
        advertiser_id=campaign.advertiser_id,
        title=campaign.title,
        brief=campaign.brief,
        budget_usdt=campaign.budget_usdt,
        budget_ton=campaign.budget_ton,
        preferred_language=campaign.preferred_language,
        start_at=campaign.start_at,
        end_at=campaign.end_at,
        min_subscribers=campaign.min_subscribers,
        min_avg_views=campaign.min_avg_views,
        lifecycle_state=campaign.lifecycle_state,
        max_acceptances=campaign.max_acceptances,
        hidden_at=campaign.hidden_at,
        is_active=campaign.is_active,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


def _campaign_discover_item(campaign: CampaignRequest) -> CampaignDiscoverItem:
    return CampaignDiscoverItem(
        id=campaign.id,
        advertiser_id=campaign.advertiser_id,
        title=campaign.title,
        brief=campaign.brief,
        budget_ton=campaign.budget_ton,
        preferred_language=campaign.preferred_language,
        min_subscribers=campaign.min_subscribers,
        min_avg_views=campaign.min_avg_views,
        max_acceptances=campaign.max_acceptances,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


def _campaign_offer_inbox_item(
    application: CampaignApplication,
    campaign: CampaignRequest,
    channel: Channel,
) -> CampaignOfferInboxItem:
    return CampaignOfferInboxItem(
        application_id=application.id,
        campaign_id=campaign.id,
        campaign_title=campaign.title,
        channel_id=application.channel_id,
        channel_username=channel.username,
        channel_title=channel.title,
        owner_id=application.owner_id,
        proposed_format_label=application.proposed_format_label,
        status=application.status,
        created_at=application.created_at,
    )


@router.post("", response_model=CampaignRequestSummary, status_code=status.HTTP_201_CREATED)
def create_campaign(
    payload: CampaignRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignRequestSummary:
    _require_non_empty(payload.title, field="title")
    _require_non_empty(payload.brief, field="brief")
    _validate_budget(payload.budget_usdt, field="budget_usdt")
    _validate_budget(payload.budget_ton, field="budget_ton")
    max_acceptances = _validate_max_acceptances(payload.max_acceptances)

    if payload.start_at and payload.end_at and payload.end_at <= payload.start_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date range")

    campaign = CampaignRequest(
        advertiser_id=current_user.id,
        title=payload.title.strip(),
        brief=payload.brief.strip(),
        budget_usdt=payload.budget_usdt,
        budget_ton=payload.budget_ton,
        preferred_language=payload.preferred_language,
        start_at=payload.start_at,
        end_at=payload.end_at,
        min_subscribers=payload.min_subscribers,
        min_avg_views=payload.min_avg_views,
        lifecycle_state=CampaignLifecycleState.ACTIVE.value,
        max_acceptances=max_acceptances,
        hidden_at=None,
        is_active=True,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    return _campaign_summary(campaign)


@router.get("", response_model=CampaignRequestPage)
def list_campaigns(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignRequestPage:
    params = request.query_params
    page = _parse_int(params.get("page"), field="page", minimum=1) or DEFAULT_PAGE
    page_size = _parse_int(params.get("page_size"), field="page_size", minimum=1) or DEFAULT_PAGE_SIZE

    stmt = (
        select(CampaignRequest)
        .where(CampaignRequest.advertiser_id == current_user.id)
        .where(CampaignRequest.lifecycle_state != CampaignLifecycleState.HIDDEN.value)
    )
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = db.exec(total_stmt).one()
    total = total_result if isinstance(total_result, int) else total_result[0]

    offset = (page - 1) * page_size
    rows = db.exec(
        stmt.order_by(CampaignRequest.id.asc()).limit(page_size).offset(offset)
    ).all()

    return CampaignRequestPage(
        page=page,
        page_size=page_size,
        total=total,
        items=[_campaign_summary(campaign) for campaign in rows],
    )


@router.get("/discover", response_model=CampaignDiscoverPage)
def discover_campaigns(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CampaignDiscoverPage:
    params = request.query_params
    page = _parse_int(params.get("page"), field="page", minimum=1) or DEFAULT_PAGE
    page_size = _parse_int(params.get("page_size"), field="page_size", minimum=1) or DEFAULT_PAGE_SIZE
    search = _parse_search(params.get("search"))

    stmt = (
        select(CampaignRequest)
        .where(CampaignRequest.lifecycle_state == CampaignLifecycleState.ACTIVE.value)
    )
    if search is not None:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                CampaignRequest.title.ilike(pattern),
                CampaignRequest.brief.ilike(pattern),
            )
        )

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = db.exec(total_stmt).one()
    total = total_result if isinstance(total_result, int) else total_result[0]

    offset = (page - 1) * page_size
    rows = db.exec(
        stmt.order_by(CampaignRequest.created_at.desc(), CampaignRequest.id.desc()).limit(page_size).offset(offset)
    ).all()

    return CampaignDiscoverPage(
        page=page,
        page_size=page_size,
        total=total,
        items=[_campaign_discover_item(campaign) for campaign in rows],
    )


@router.get("/offers", response_model=CampaignOfferInboxPage)
def list_aggregated_offers(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignOfferInboxPage:
    params = request.query_params
    page = _parse_int(params.get("page"), field="page", minimum=1) or DEFAULT_PAGE
    page_size = _parse_int(params.get("page_size"), field="page_size", minimum=1) or DEFAULT_PAGE_SIZE

    stmt = (
        select(CampaignApplication, CampaignRequest, Channel)
        .join(CampaignRequest, CampaignRequest.id == CampaignApplication.campaign_id)
        .join(Channel, Channel.id == CampaignApplication.channel_id)
        .where(CampaignRequest.advertiser_id == current_user.id)
        .where(CampaignRequest.lifecycle_state != CampaignLifecycleState.HIDDEN.value)
        .where(CampaignApplication.hidden_at.is_(None))
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

    return CampaignOfferInboxPage(
        page=page,
        page_size=page_size,
        total=total,
        items=[
            _campaign_offer_inbox_item(application, campaign, channel)
            for application, campaign, channel in rows
        ],
    )


@router.get("/{campaign_id}", response_model=CampaignRequestSummary)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignRequestSummary:
    campaign = db.exec(
        select(CampaignRequest)
        .where(CampaignRequest.id == campaign_id)
        .where(CampaignRequest.lifecycle_state != CampaignLifecycleState.HIDDEN.value)
    ).first()
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    if campaign.advertiser_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return _campaign_summary(campaign)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    campaign = db.exec(select(CampaignRequest).where(CampaignRequest.id == campaign_id)).first()
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    if campaign.advertiser_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if campaign.lifecycle_state == CampaignLifecycleState.HIDDEN.value:
        return

    hidden_at = datetime.now(timezone.utc)
    campaign.lifecycle_state = CampaignLifecycleState.HIDDEN.value
    campaign.hidden_at = hidden_at
    campaign.is_active = False
    campaign.updated_at = hidden_at
    db.add(campaign)

    applications = db.exec(
        select(CampaignApplication)
        .where(CampaignApplication.campaign_id == campaign.id)
        .where(CampaignApplication.hidden_at.is_(None))
    ).all()
    for application in applications:
        application.hidden_at = hidden_at
        db.add(application)

    db.commit()
