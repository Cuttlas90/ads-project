from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, text
from sqlmodel import Field, SQLModel


class EscrowEvent(SQLModel, table=True):
    __tablename__ = "escrow_events"

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    escrow_id: int = Field(
        sa_column=Column(Integer, ForeignKey("deal_escrows.id"), nullable=False, index=True),
    )
    actor_user_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=True),
    )
    from_state: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    to_state: str = Field(sa_column=Column(String, nullable=False))
    event_type: str = Field(sa_column=Column(String, nullable=False))
    payload: dict | list | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
