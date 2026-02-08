from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


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
    placement_type: Literal["post", "story"]
    exclusive_hours: int = Field(ge=0)
    retention_hours: int = Field(ge=1)
    price: Decimal = Field(ge=0)


class ListingFormatUpdate(BaseModel):
    placement_type: Literal["post", "story"] | None = None
    exclusive_hours: int | None = Field(default=None, ge=0)
    retention_hours: int | None = Field(default=None, ge=1)
    price: Decimal | None = Field(default=None, ge=0)


class ListingFormatSummary(BaseModel):
    id: int
    listing_id: int
    placement_type: Literal["post", "story"]
    exclusive_hours: int
    retention_hours: int
    price: Decimal


class ListingDetail(ListingSummary):
    formats: list[ListingFormatSummary]


class ChannelListingResponse(BaseModel):
    has_listing: bool
    listing: ListingDetail | None = None
