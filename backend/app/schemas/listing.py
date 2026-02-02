from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class ListingCreate(BaseModel):
    channel_id: int


class ListingUpdate(BaseModel):
    is_active: bool


class ListingSummary(BaseModel):
    id: int
    channel_id: int
    owner_id: int
    is_active: bool


class ListingFormatCreate(BaseModel):
    label: str
    price: Decimal


class ListingFormatUpdate(BaseModel):
    label: str | None = None
    price: Decimal | None = None


class ListingFormatSummary(BaseModel):
    id: int
    listing_id: int
    label: str
    price: Decimal


class ListingDetail(ListingSummary):
    formats: list[ListingFormatSummary]


class ChannelListingResponse(BaseModel):
    has_listing: bool
    listing: ListingDetail | None = None
