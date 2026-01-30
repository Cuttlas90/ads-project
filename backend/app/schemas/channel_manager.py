from __future__ import annotations

from pydantic import BaseModel

from app.schemas.channel import ChannelRole


class ChannelManagerCreate(BaseModel):
    telegram_user_id: int


class ChannelManagerSummary(BaseModel):
    telegram_user_id: int
    role: ChannelRole
