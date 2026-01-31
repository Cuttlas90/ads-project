from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, text
from sqlmodel import Field, SQLModel


class DealEvent(SQLModel, table=True):
    __tablename__ = "deal_events"

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    deal_id: int = Field(
        sa_column=Column(Integer, ForeignKey("deals.id"), nullable=False, index=True),
    )
    actor_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=True),
    )
    event_type: str = Field(sa_column=Column(String, nullable=False))
    from_state: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    to_state: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    payload: dict | list | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
