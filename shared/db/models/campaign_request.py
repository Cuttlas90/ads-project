from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlmodel import Field, SQLModel


class CampaignLifecycleState(str, Enum):
    ACTIVE = "active"
    HIDDEN = "hidden"
    CLOSED_BY_LIMIT = "closed_by_limit"


class CampaignRequest(SQLModel, table=True):
    __tablename__ = "campaign_requests"
    __table_args__ = (
        CheckConstraint(
            "lifecycle_state IN ('active', 'hidden', 'closed_by_limit')",
            name="ck_campaign_requests_lifecycle_state",
        ),
        CheckConstraint(
            "max_acceptances >= 1",
            name="ck_campaign_requests_max_acceptances",
        ),
    )

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
    lifecycle_state: str = Field(
        default=CampaignLifecycleState.ACTIVE.value,
        sa_column=Column(
            String,
            nullable=False,
            server_default=text("'active'"),
            index=True,
        ),
    )
    max_acceptances: int = Field(
        default=10,
        sa_column=Column(
            Integer,
            nullable=False,
            server_default=text("10"),
        ),
    )
    hidden_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
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
