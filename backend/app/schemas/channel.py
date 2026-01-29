from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class ChannelRole(str, Enum):
    owner = "owner"
    manager = "manager"


class ChannelCreate(BaseModel):
    username: str


class ChannelSummary(BaseModel):
    id: int
    username: str | None
    title: str | None
    is_verified: bool


class ChannelWithRole(ChannelSummary):
    role: ChannelRole
