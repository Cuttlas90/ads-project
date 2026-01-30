from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CampaignRequestCreate(BaseModel):
    title: str
    brief: str
    budget_usdt: Decimal | None = None
    budget_ton: Decimal | None = None
    preferred_language: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    min_subscribers: int | None = None
    min_avg_views: int | None = None


class CampaignRequestSummary(BaseModel):
    id: int
    advertiser_id: int
    title: str
    brief: str
    budget_usdt: Decimal | None
    budget_ton: Decimal | None
    preferred_language: str | None
    start_at: datetime | None
    end_at: datetime | None
    min_subscribers: int | None
    min_avg_views: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CampaignRequestPage(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[CampaignRequestSummary]


class CampaignApplicationCreate(BaseModel):
    channel_id: int
    proposed_format_label: str
    message: str | None = None


class CampaignApplicationSummary(BaseModel):
    id: int
    campaign_id: int
    channel_id: int
    owner_id: int
    proposed_format_label: str
    message: str | None
    status: str
    created_at: datetime


class CampaignApplicationStatsSummary(BaseModel):
    avg_views: int | None
    premium_ratio: float
    language_stats: dict[str, float] | None


class CampaignApplicationListingItem(BaseModel):
    id: int
    channel_id: int
    channel_username: str | None
    channel_title: str | None
    proposed_format_label: str
    status: str
    created_at: datetime
    stats: CampaignApplicationStatsSummary


class CampaignApplicationPage(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[CampaignApplicationListingItem]
