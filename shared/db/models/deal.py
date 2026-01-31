from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlmodel import Field, SQLModel


class DealState(str, Enum):
    DRAFT = "DRAFT"
    NEGOTIATION = "NEGOTIATION"
    REJECTED = "REJECTED"
    ACCEPTED = "ACCEPTED"
    FUNDED = "FUNDED"
    CREATIVE_SUBMITTED = "CREATIVE_SUBMITTED"
    CREATIVE_APPROVED = "CREATIVE_APPROVED"
    SCHEDULED = "SCHEDULED"
    POSTED = "POSTED"
    VERIFIED = "VERIFIED"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"


class DealSourceType(str, Enum):
    LISTING = "listing"
    CAMPAIGN = "campaign"


class Deal(SQLModel, table=True):
    __tablename__ = "deals"
    __table_args__ = (
        UniqueConstraint("campaign_id", name="ux_deals_campaign_id"),
        UniqueConstraint("campaign_application_id", name="ux_deals_campaign_application_id"),
        CheckConstraint(
            "(source_type = 'listing' AND listing_id IS NOT NULL AND listing_format_id IS NOT NULL "
            "AND campaign_id IS NULL AND campaign_application_id IS NULL) OR "
            "(source_type = 'campaign' AND campaign_id IS NOT NULL AND campaign_application_id IS NOT NULL "
            "AND listing_id IS NULL AND listing_format_id IS NULL)",
            name="ck_deals_source",
        ),
    )

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    source_type: str = Field(sa_column=Column(String, nullable=False))
    advertiser_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False, index=True),
    )
    channel_id: int = Field(
        sa_column=Column(Integer, ForeignKey("channels.id"), nullable=False, index=True),
    )
    channel_owner_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False),
    )
    listing_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("listings.id"), nullable=True),
    )
    listing_format_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("listing_formats.id"), nullable=True),
    )
    campaign_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("campaign_requests.id"), nullable=True),
    )
    campaign_application_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("campaign_applications.id"), nullable=True),
    )
    price_ton: Decimal = Field(sa_column=Column(Numeric(18, 2), nullable=False))
    ad_type: str = Field(sa_column=Column(String, nullable=False))
    creative_text: str = Field(sa_column=Column(Text, nullable=False))
    creative_media_type: str = Field(sa_column=Column(String, nullable=False))
    creative_media_ref: str = Field(sa_column=Column(String, nullable=False))
    posting_params: dict | list | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    state: str = Field(
        default=DealState.DRAFT.value,
        sa_column=Column(String, nullable=False, server_default=text("'DRAFT'"), index=True),
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
