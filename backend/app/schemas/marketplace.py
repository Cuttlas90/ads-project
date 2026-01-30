from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class MarketplaceListingFormat(BaseModel):
    label: str
    price: Decimal


class MarketplaceListingStats(BaseModel):
    subscribers: int | None
    avg_views: int | None
    premium_ratio: float


class MarketplaceListing(BaseModel):
    listing_id: int
    channel_username: str | None
    channel_title: str | None
    formats: list[MarketplaceListingFormat]
    stats: MarketplaceListingStats


class MarketplaceListingPage(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[MarketplaceListing]
