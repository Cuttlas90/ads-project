from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from shared.db.models.listing import Listing


class ListingFormat(SQLModel, table=True):
    __tablename__ = "listing_formats"
    __table_args__ = (UniqueConstraint("listing_id", "label", name="ux_listing_formats_listing_label"),)

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    listing_id: int = Field(
        sa_column=Column(Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True),
    )
    label: str = Field(sa_column=Column(String, nullable=False))
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
