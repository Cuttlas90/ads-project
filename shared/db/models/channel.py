from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from shared.db.models.channel_member import ChannelMember


class Channel(SQLModel, table=True):
    __tablename__ = "channels"

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    telegram_channel_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, nullable=True, index=True),
    )
    username: str | None = Field(
        default=None,
        sa_column=Column(String, nullable=True, index=True, unique=True),
    )
    title: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    is_verified: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default=text("false")),
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
    members: List["ChannelMember"] = Relationship(back_populates="channel")
