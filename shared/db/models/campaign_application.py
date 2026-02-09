from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlmodel import Field, SQLModel


class CampaignApplication(SQLModel, table=True):
    __tablename__ = "campaign_applications"
    __table_args__ = (
        UniqueConstraint("campaign_id", "channel_id", name="ux_campaign_applications_campaign_channel"),
        CheckConstraint(
            "proposed_placement_type IN ('post', 'story')",
            name="ck_campaign_applications_proposed_placement_type",
        ),
        CheckConstraint(
            "proposed_exclusive_hours >= 0",
            name="ck_campaign_applications_proposed_exclusive_hours",
        ),
        CheckConstraint(
            "proposed_retention_hours >= 1",
            name="ck_campaign_applications_proposed_retention_hours",
        ),
    )

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    campaign_id: int = Field(
        sa_column=Column(Integer, ForeignKey("campaign_requests.id"), nullable=False, index=True),
    )
    channel_id: int = Field(
        sa_column=Column(Integer, ForeignKey("channels.id"), nullable=False, index=True),
    )
    owner_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False, index=True),
    )
    proposed_format_label: str = Field(sa_column=Column(String, nullable=False))
    proposed_placement_type: str = Field(sa_column=Column(String, nullable=False))
    proposed_exclusive_hours: int = Field(sa_column=Column(Integer, nullable=False))
    proposed_retention_hours: int = Field(sa_column=Column(Integer, nullable=False))
    message: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    status: str = Field(
        default="submitted",
        sa_column=Column(String, nullable=False, server_default=text("'submitted'")),
    )
    hidden_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
