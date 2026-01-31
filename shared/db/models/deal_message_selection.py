from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, text
from sqlmodel import Field, SQLModel


class DealMessageSelection(SQLModel, table=True):
    __tablename__ = "deal_message_selections"
    __table_args__ = (
        UniqueConstraint("user_id", name="ux_deal_message_selections_user"),
    )

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False, index=True),
    )
    deal_id: int = Field(
        sa_column=Column(Integer, ForeignKey("deals.id"), nullable=False, index=True),
    )
    selected_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
