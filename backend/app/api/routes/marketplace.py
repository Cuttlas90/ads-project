from __future__ import annotations

from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from app.api.deps import get_db
from app.repositories.marketplace_repo import fetch_marketplace_listings
from app.schemas.marketplace import (
    MarketplaceListing,
    MarketplaceListingFormat,
    MarketplaceListingPage,
    MarketplaceListingStats,
)

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
ALLOWED_SORTS = {"price", "subscribers"}
ALLOWED_PLACEMENT_TYPES = {"post", "story"}


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


def _parse_decimal(value: str | None, *, field: str, minimum: Decimal | None = None) -> Decimal | None:
    if value is None:
        return None
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")
    if minimum is not None and parsed < minimum:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")
    return parsed


def _parse_float(value: str | None, *, field: str, minimum: float | None = None) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")
    if minimum is not None and parsed < minimum:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")
    return parsed


def _validate_range(min_value, max_value, *, field: str) -> None:
    if min_value is None or max_value is None:
        return
    if min_value > max_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field} range")


@router.get("/listings", response_model=MarketplaceListingPage)
def list_marketplace_listings(
    request: Request,
    db: Session = Depends(get_db),
) -> MarketplaceListingPage:
    params = request.query_params

    min_price = _parse_decimal(params.get("min_price"), field="min_price", minimum=Decimal("0"))
    max_price = _parse_decimal(params.get("max_price"), field="max_price", minimum=Decimal("0"))
    placement_type = params.get("placement_type")
    min_exclusive_hours = _parse_int(params.get("min_exclusive_hours"), field="min_exclusive_hours", minimum=0)
    max_exclusive_hours = _parse_int(params.get("max_exclusive_hours"), field="max_exclusive_hours", minimum=0)
    min_retention_hours = _parse_int(params.get("min_retention_hours"), field="min_retention_hours", minimum=1)
    max_retention_hours = _parse_int(params.get("max_retention_hours"), field="max_retention_hours", minimum=1)
    min_subscribers = _parse_int(params.get("min_subscribers"), field="min_subscribers", minimum=0)
    max_subscribers = _parse_int(params.get("max_subscribers"), field="max_subscribers", minimum=0)
    min_avg_views = _parse_int(params.get("min_avg_views"), field="min_avg_views", minimum=0)
    max_avg_views = _parse_int(params.get("max_avg_views"), field="max_avg_views", minimum=0)
    language = params.get("language")
    min_premium_pct = _parse_float(params.get("min_premium_pct"), field="min_premium_pct", minimum=0.0)
    search = params.get("search")
    sort = params.get("sort")

    page = _parse_int(params.get("page"), field="page", minimum=1) or DEFAULT_PAGE
    page_size = _parse_int(params.get("page_size"), field="page_size", minimum=1) or DEFAULT_PAGE_SIZE

    if sort is not None and sort not in ALLOWED_SORTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort")

    if placement_type is not None and placement_type not in ALLOWED_PLACEMENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid placement_type")

    if min_premium_pct is not None and min_premium_pct > 1.0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid min_premium_pct")

    _validate_range(min_price, max_price, field="price")
    _validate_range(min_exclusive_hours, max_exclusive_hours, field="exclusive_hours")
    _validate_range(min_retention_hours, max_retention_hours, field="retention_hours")
    _validate_range(min_subscribers, max_subscribers, field="subscribers")
    _validate_range(min_avg_views, max_avg_views, field="avg_views")

    result = fetch_marketplace_listings(
        db,
        min_price=min_price,
        max_price=max_price,
        placement_type=placement_type,
        min_exclusive_hours=min_exclusive_hours,
        max_exclusive_hours=max_exclusive_hours,
        min_retention_hours=min_retention_hours,
        max_retention_hours=max_retention_hours,
        min_subscribers=min_subscribers,
        max_subscribers=max_subscribers,
        min_avg_views=min_avg_views,
        max_avg_views=max_avg_views,
        language=language,
        min_premium_pct=min_premium_pct,
        search=search,
        sort=sort,
        page=page,
        page_size=page_size,
    )

    items = [
        MarketplaceListing(
            listing_id=item.listing_id,
            channel_username=item.channel_username,
            channel_title=item.channel_title,
            formats=[
                MarketplaceListingFormat(
                    id=format_item.id,
                    placement_type=format_item.placement_type,
                    exclusive_hours=format_item.exclusive_hours,
                    retention_hours=format_item.retention_hours,
                    price=format_item.price,
                )
                for format_item in item.formats
            ],
            stats=MarketplaceListingStats(
                subscribers=item.subscribers,
                avg_views=item.avg_views,
                premium_ratio=item.premium_ratio,
            ),
        )
        for item in result.items
    ]

    return MarketplaceListingPage(page=page, page_size=page_size, total=result.total, items=items)
