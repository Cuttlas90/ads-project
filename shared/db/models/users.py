from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from shared.db.models.channel_member import ChannelMember


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    telegram_user_id: int = Field(
        sa_column=Column(BigInteger, nullable=False, unique=True, index=True),
    )
    username: str | None = Field(default=None, sa_column=Column(String))
    first_name: str | None = Field(default=None, sa_column=Column(String))
    last_name: str | None = Field(default=None, sa_column=Column(String))
    language_code: str | None = Field(default=None, sa_column=Column(String))
    is_premium: bool | None = Field(default=None, sa_column=Column(Boolean, nullable=True))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
    last_login_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    channel_memberships: List["ChannelMember"] = Relationship(back_populates="user")
