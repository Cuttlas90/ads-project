from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlmodel import Field, SQLModel


class CampaignRequest(SQLModel, table=True):
    __tablename__ = "campaign_requests"

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    advertiser_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False, index=True),
    )
    title: str = Field(sa_column=Column(String, nullable=False))
    brief: str = Field(sa_column=Column(Text, nullable=False))
    budget_usdt: Decimal | None = Field(default=None, sa_column=Column(Numeric(18, 2), nullable=True))
    budget_ton: Decimal | None = Field(default=None, sa_column=Column(Numeric(18, 2), nullable=True))
    preferred_language: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    start_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    end_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    min_subscribers: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    min_avg_views: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default=text("true")),
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
