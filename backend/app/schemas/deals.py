from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class DealCreateFromListing(BaseModel):
    listing_format_id: int
    creative_text: str
    creative_media_type: str
    creative_media_ref: str
    posting_params: dict | list | None = None


class DealCreateFromCampaignAccept(BaseModel):
    price_ton: Decimal
    ad_type: str
    creative_text: str
    creative_media_type: str
    creative_media_ref: str
    posting_params: dict | list | None = None


class DealUpdate(BaseModel):
    price_ton: Decimal | None = None
    ad_type: str | None = None
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
    creative_text: str
    creative_media_type: str
    creative_media_ref: str
    posting_params: dict | list | None
    state: str
    created_at: datetime
    updated_at: datetime


class DealMessageCreate(BaseModel):
    text: str


class DealMessageSummary(BaseModel):
    id: int
    deal_id: int
    actor_id: int | None
    text: str
    created_at: datetime
