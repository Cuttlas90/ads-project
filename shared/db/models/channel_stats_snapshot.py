from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, text
from sqlmodel import Field, SQLModel


class ChannelStatsSnapshot(SQLModel, table=True):
    __tablename__ = "channel_stats_snapshots"

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    channel_id: int = Field(
        sa_column=Column(Integer, ForeignKey("channels.id"), nullable=False, index=True),
    )
    subscribers: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    avg_views: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    language_stats: dict | list | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    premium_stats: dict | list | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    raw_stats: dict | list | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
