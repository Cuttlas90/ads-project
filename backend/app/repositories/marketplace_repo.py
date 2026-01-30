from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from sqlalchemy import and_, exists, func, or_, select
from sqlmodel import Session

from app.models.channel import Channel
from app.models.channel_stats_snapshot import ChannelStatsSnapshot
from app.models.listing import Listing
from app.models.listing_format import ListingFormat

LANGUAGE_MATCH_THRESHOLD = 0.10
PREMIUM_RATIO_KEY = "premium_ratio"


@dataclass(frozen=True)
class MarketplaceListingFormatResult:
    label: str
    price: Decimal


@dataclass(frozen=True)
class MarketplaceListingResult:
    listing_id: int
    channel_username: str | None
    channel_title: str | None
    subscribers: int | None
    avg_views: int | None
    premium_ratio: float
    formats: list[MarketplaceListingFormatResult]


@dataclass(frozen=True)
class MarketplacePageResult:
    items: list[MarketplaceListingResult]
    total: int


def fetch_marketplace_listings(
    db: Session,
    *,
    min_price: Decimal | None,
    max_price: Decimal | None,
    min_subscribers: int | None,
    max_subscribers: int | None,
    min_avg_views: int | None,
    max_avg_views: int | None,
    language: str | None,
    min_premium_pct: float | None,
    search: str | None,
    sort: str | None,
    page: int,
    page_size: int,
) -> MarketplacePageResult:
    snapshot_subq = _latest_snapshot_subquery()
    min_price_subq = _min_price_subquery()

    stmt = (
        select(
            Listing.id.label("listing_id"),
            Listing.channel_id.label("channel_id"),
            Listing.created_at.label("listing_created_at"),
            Channel.username.label("channel_username"),
            Channel.title.label("channel_title"),
            snapshot_subq.c.subscribers,
            snapshot_subq.c.avg_views,
            snapshot_subq.c.language_stats,
            snapshot_subq.c.premium_stats,
            min_price_subq.c.min_price,
        )
        .join(Channel, Channel.id == Listing.channel_id)
        .join(
            snapshot_subq,
            and_(
                snapshot_subq.c.channel_id == Listing.channel_id,
                snapshot_subq.c.rn == 1,
            ),
            isouter=True,
        )
        .join(min_price_subq, min_price_subq.c.listing_id == Listing.id, isouter=True)
        .where(Listing.is_active.is_(True))
        .where(Channel.is_verified.is_(True))
    )

    stmt = _apply_filters(
        stmt,
        snapshot_subq=snapshot_subq,
        min_price=min_price,
        max_price=max_price,
        min_subscribers=min_subscribers,
        max_subscribers=max_subscribers,
        min_avg_views=min_avg_views,
        max_avg_views=max_avg_views,
        language=language,
        min_premium_pct=min_premium_pct,
        search=search,
    )

    order_by = _build_order_by(sort, min_price_subq=min_price_subq, snapshot_subq=snapshot_subq)
    stmt = stmt.order_by(*order_by)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = db.exec(total_stmt).one()
    total = total_result if isinstance(total_result, int) else total_result[0]

    offset = (page - 1) * page_size
    rows = db.exec(stmt.limit(page_size).offset(offset)).all()

    listing_ids = [row.listing_id for row in rows]
    formats_by_listing = _load_formats(db, listing_ids)

    items = [
        MarketplaceListingResult(
            listing_id=row.listing_id,
            channel_username=row.channel_username,
            channel_title=row.channel_title,
            subscribers=row.subscribers,
            avg_views=row.avg_views,
            premium_ratio=_premium_ratio_from_stats(row.premium_stats),
            formats=formats_by_listing.get(row.listing_id, []),
        )
        for row in rows
    ]

    return MarketplacePageResult(items=items, total=total)


def _latest_snapshot_subquery():
    return (
        select(
            ChannelStatsSnapshot.id.label("snapshot_id"),
            ChannelStatsSnapshot.channel_id.label("channel_id"),
            ChannelStatsSnapshot.subscribers.label("subscribers"),
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


def _min_price_subquery():
    return (
        select(
            ListingFormat.listing_id.label("listing_id"),
            func.min(ListingFormat.price).label("min_price"),
        )
        .group_by(ListingFormat.listing_id)
        .subquery()
    )


def _apply_filters(
    stmt,
    *,
    snapshot_subq,
    min_price: Decimal | None,
    max_price: Decimal | None,
    min_subscribers: int | None,
    max_subscribers: int | None,
    min_avg_views: int | None,
    max_avg_views: int | None,
    language: str | None,
    min_premium_pct: float | None,
    search: str | None,
):
    if min_price is not None or max_price is not None:
        price_conditions = [ListingFormat.listing_id == Listing.id]
        if min_price is not None:
            price_conditions.append(ListingFormat.price >= min_price)
        if max_price is not None:
            price_conditions.append(ListingFormat.price <= max_price)
        stmt = stmt.where(exists(select(1).select_from(ListingFormat).where(*price_conditions)))

    if min_subscribers is not None:
        stmt = stmt.where(snapshot_subq.c.subscribers >= min_subscribers)
    if max_subscribers is not None:
        stmt = stmt.where(snapshot_subq.c.subscribers <= max_subscribers)

    if min_avg_views is not None:
        stmt = stmt.where(snapshot_subq.c.avg_views >= min_avg_views)
    if max_avg_views is not None:
        stmt = stmt.where(snapshot_subq.c.avg_views <= max_avg_views)

    if language:
        language_expr = snapshot_subq.c.language_stats[language].as_float()
        stmt = stmt.where(language_expr >= LANGUAGE_MATCH_THRESHOLD)

    if min_premium_pct is not None:
        premium_expr = func.coalesce(
            snapshot_subq.c.premium_stats[PREMIUM_RATIO_KEY].as_float(),
            0.0,
        )
        stmt = stmt.where(premium_expr >= min_premium_pct)

    if search:
        term = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Channel.username).like(term),
                func.lower(Channel.title).like(term),
            )
        )

    return stmt


def _build_order_by(sort: str | None, *, min_price_subq, snapshot_subq) -> tuple:
    if sort == "price":
        return (
            min_price_subq.c.min_price.asc().nulls_last(),
            Listing.created_at.asc(),
            Listing.id.asc(),
        )
    if sort == "subscribers":
        return (
            snapshot_subq.c.subscribers.desc().nulls_last(),
            Listing.created_at.asc(),
            Listing.id.asc(),
        )
    return (
        Listing.created_at.asc(),
        Listing.id.asc(),
    )


def _load_formats(
    db: Session,
    listing_ids: Iterable[int],
) -> dict[int, list[MarketplaceListingFormatResult]]:
    if not listing_ids:
        return {}

    rows = db.exec(
        select(
            ListingFormat.listing_id,
            ListingFormat.label,
            ListingFormat.price,
        )
        .where(ListingFormat.listing_id.in_(listing_ids))
        .order_by(ListingFormat.price.asc(), ListingFormat.id.asc())
    ).all()

    formats_by_listing: dict[int, list[MarketplaceListingFormatResult]] = {}
    for format_row in rows:
        formats_by_listing.setdefault(format_row.listing_id, []).append(
            MarketplaceListingFormatResult(
                label=format_row.label,
                price=format_row.price,
            )
        )

    return formats_by_listing


def _premium_ratio_from_stats(premium_stats) -> float:
    if isinstance(premium_stats, dict):
        value = premium_stats.get(PREMIUM_RATIO_KEY)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    return 0.0
