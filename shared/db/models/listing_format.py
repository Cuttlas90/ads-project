from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from shared.db.models.listing import Listing


class ListingPlacementType(str, Enum):
    POST = "post"
    STORY = "story"


class ListingFormat(SQLModel, table=True):
    __tablename__ = "listing_formats"
    __table_args__ = (
        UniqueConstraint(
            "listing_id",
            "placement_type",
            "exclusive_hours",
            "retention_hours",
            name="ux_listing_formats_listing_terms",
        ),
        CheckConstraint(
            "placement_type IN ('post', 'story')",
            name="ck_listing_formats_placement_type",
        ),
        CheckConstraint("exclusive_hours >= 0", name="ck_listing_formats_exclusive_hours"),
        CheckConstraint("retention_hours >= 1", name="ck_listing_formats_retention_hours"),
    )

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    listing_id: int = Field(
        sa_column=Column(Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
    )
    placement_type: str = Field(sa_column=Column(String, nullable=False))
    exclusive_hours: int = Field(sa_column=Column(Integer, nullable=False))
    retention_hours: int = Field(sa_column=Column(Integer, nullable=False))
    price: Decimal = Field(sa_column=Column(Numeric(18, 2), nullable=False))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
    listing: Optional["Listing"] = Relationship(back_populates="formats")
