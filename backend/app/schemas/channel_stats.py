from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class ChannelStatsAvailability(str, Enum):
    ready = "ready"
    missing = "missing"
    error = "error"
    async_pending = "async_pending"


class ChannelStatsScalarMetric(BaseModel):
    key: str
    availability: ChannelStatsAvailability
    value: float | int | str | bool | None = None
    previous: float | int | None = None
    part: float | None = None
    total: float | None = None
    reason: str | None = None


class ChannelStatsChartMetric(BaseModel):
    key: str
    availability: ChannelStatsAvailability
    data: dict[str, Any] | list[Any] | str | None = None
    token: str | None = None
    reason: str | None = None


class ChannelStatsPremiumAudience(BaseModel):
    availability: ChannelStatsAvailability
    premium_ratio: float | None = None
    part: float | None = None
    total: float | None = None


class ChannelStatsResponse(BaseModel):
    channel_id: int
    channel_username: str | None
    channel_title: str | None
    captured_at: datetime | None
    snapshot_available: bool
    read_only: bool
    scalar_metrics: list[ChannelStatsScalarMetric]
    chart_metrics: list[ChannelStatsChartMetric]
    premium_audience: ChannelStatsPremiumAudience
