from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


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
    max_acceptances: int | None = None


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
    lifecycle_state: str
    max_acceptances: int
    hidden_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CampaignRequestPage(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[CampaignRequestSummary]


class CampaignDiscoverItem(BaseModel):
    id: int
    advertiser_id: int
    title: str
    brief: str
    budget_ton: Decimal | None
    preferred_language: str | None
    min_subscribers: int | None
    min_avg_views: int | None
    max_acceptances: int
    created_at: datetime
    updated_at: datetime


class CampaignDiscoverPage(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[CampaignDiscoverItem]


class CampaignApplicationCreate(BaseModel):
    channel_id: int
    proposed_format_label: str | None = None
    proposed_placement_type: Literal["post", "story"]
    proposed_exclusive_hours: int = Field(ge=0)
    proposed_retention_hours: int = Field(ge=1)
    message: str | None = None


class CampaignApplicationSummary(BaseModel):
    id: int
    campaign_id: int
    channel_id: int
    owner_id: int
    proposed_format_label: str
    proposed_placement_type: Literal["post", "story"]
    proposed_exclusive_hours: int
    proposed_retention_hours: int
    message: str | None
    status: str
    hidden_at: datetime | None
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
    proposed_placement_type: Literal["post", "story"]
    proposed_exclusive_hours: int
    proposed_retention_hours: int
    status: str
    created_at: datetime
    stats: CampaignApplicationStatsSummary


class CampaignApplicationPage(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[CampaignApplicationListingItem]


class CampaignOfferInboxItem(BaseModel):
    application_id: int
    campaign_id: int
    campaign_title: str
    channel_id: int
    channel_username: str | None
    channel_title: str | None
    owner_id: int
    proposed_format_label: str
    proposed_placement_type: Literal["post", "story"]
    proposed_exclusive_hours: int
    proposed_retention_hours: int
    status: str
    created_at: datetime


class CampaignOfferInboxPage(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[CampaignOfferInboxItem]
