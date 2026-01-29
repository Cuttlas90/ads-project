from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from shared.db.models.channel import Channel
    from shared.db.models.users import User


class ChannelMember(SQLModel, table=True):
    __tablename__ = "channel_members"
    __table_args__ = (
        UniqueConstraint("channel_id", "user_id", name="ux_channel_members_channel_user"),
        Index(
            "ux_channel_members_single_owner",
            "channel_id",
            unique=True,
            postgresql_where=text("role = 'owner'"),
        ),
    )

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    channel_id: int = Field(
        sa_column=Column(Integer, ForeignKey("channels.id"), nullable=False, index=True),
    )
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False, index=True),
    )
    role: str = Field(sa_column=Column(String, nullable=False))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
    channel: Optional["Channel"] = Relationship(back_populates="members")
    user: Optional["User"] = Relationship(back_populates="channel_memberships")
