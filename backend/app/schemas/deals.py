from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class DealCreateFromListing(BaseModel):
    listing_format_id: int
    creative_text: str
    creative_media_type: str
    creative_media_ref: str
    start_at: datetime | None = None
    posting_params: dict | list | None = None


class DealCreateFromCampaignAccept(BaseModel):
    price_ton: Decimal | None = None
    ad_type: str | None = None
    creative_text: str
    creative_media_type: str
    creative_media_ref: str
    start_at: datetime | None = None
    posting_params: dict | list | None = None


class DealUpdate(BaseModel):
    price_ton: Decimal | None = None
    ad_type: str | None = None
    start_at: datetime | None = None
    placement_type: Literal["post", "story"] | None = None
    exclusive_hours: int | None = Field(default=None, ge=0)
    retention_hours: int | None = Field(default=None, ge=1)
    creative_text: str | None = None
    creative_media_type: str | None = None
    creative_media_ref: str | None = None
    posting_params: dict | list | None = None


class DealSummary(BaseModel):
    id: int
    source_type: str
    advertiser_id: int
    channel_id: int
    channel_owner_id: int
    listing_id: int | None
    listing_format_id: int | None
    campaign_id: int | None
    campaign_application_id: int | None
    price_ton: Decimal
    ad_type: str
    placement_type: Literal["post", "story"] | None = None
    exclusive_hours: int | None = None
    retention_hours: int | None = None
    creative_text: str
    creative_media_type: str
    creative_media_ref: str
    posting_params: dict | list | None
    scheduled_at: datetime | None = None
    verification_window_hours: int | None = None
    posted_at: datetime | None = None
    posted_message_id: str | None = None
    posted_content_hash: str | None = None
    verified_at: datetime | None = None
    state: str
    created_at: datetime
    updated_at: datetime


class DealInboxItem(BaseModel):
    id: int
    state: str
    channel_id: int
    channel_username: str | None
    channel_title: str | None
    advertiser_id: int
    price_ton: Decimal
    ad_type: str
    updated_at: datetime


class DealInboxPage(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[DealInboxItem]


class DealDetail(DealSummary):
    channel_username: str | None
    channel_title: str | None
    advertiser_username: str | None
    advertiser_first_name: str | None
    advertiser_last_name: str | None


class DealCreativeSubmit(BaseModel):
    creative_text: str
    creative_media_type: str
    creative_media_ref: str


class DealCreativeUploadResponse(BaseModel):
    creative_media_ref: str
    creative_media_type: str


class DealTimelineEvent(BaseModel):
    event_type: str
    from_state: str | None
    to_state: str | None
    payload: dict | list | None
    created_at: datetime
    actor_id: int | None


class DealTimelinePage(BaseModel):
    items: list[DealTimelineEvent]
    next_cursor: str | None = None


class DealMessageCreate(BaseModel):
    text: str


class DealMessageSummary(BaseModel):
    id: int
    deal_id: int
    actor_id: int | None
    text: str
    created_at: datetime
