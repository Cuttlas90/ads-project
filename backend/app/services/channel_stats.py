from __future__ import annotations

from typing import Any

from sqlmodel import Session, select

from app.models.channel import Channel
from app.models.channel_stats_snapshot import ChannelStatsSnapshot
from app.schemas.channel_stats import (
    ChannelStatsAvailability,
    ChannelStatsChartMetric,
    ChannelStatsPremiumAudience,
    ChannelStatsResponse,
    ChannelStatsScalarMetric,
)


def read_latest_channel_snapshot(*, db: Session, channel_id: int) -> ChannelStatsSnapshot | None:
    return (
        db.exec(
            select(ChannelStatsSnapshot)
            .where(ChannelStatsSnapshot.channel_id == channel_id)
            .order_by(ChannelStatsSnapshot.created_at.desc(), ChannelStatsSnapshot.id.desc())
        )
        .first()
    )


def build_channel_stats_response(
    *,
    channel: Channel,
    snapshot: ChannelStatsSnapshot | None,
) -> ChannelStatsResponse:
    if snapshot is None:
        return ChannelStatsResponse(
            channel_id=channel.id,
            channel_username=channel.username,
            channel_title=channel.title,
            captured_at=None,
            snapshot_available=False,
            read_only=True,
            scalar_metrics=[],
            chart_metrics=[],
            premium_audience=ChannelStatsPremiumAudience(
                availability=ChannelStatsAvailability.missing,
            ),
        )

    raw_stats = _as_dict(snapshot.raw_stats)
    statistics = _as_dict(raw_stats.get("statistics"))
    boosts_status = _as_dict(raw_stats.get("boosts_status"))

    premium_audience = _normalize_premium_audience(
        premium_graph=_as_dict(statistics.get("premium_graph")),
        boosts_status=boosts_status,
        premium_stats=_as_dict(snapshot.premium_stats),
    )
    scalar_metrics = _build_scalar_metrics(
        snapshot=snapshot,
        statistics=statistics,
        premium_audience=premium_audience,
    )
    chart_metrics = _build_chart_metrics(statistics=statistics)

    return ChannelStatsResponse(
        channel_id=channel.id,
        channel_username=channel.username,
        channel_title=channel.title,
        captured_at=snapshot.created_at,
        snapshot_available=True,
        read_only=True,
        scalar_metrics=scalar_metrics,
        chart_metrics=chart_metrics,
        premium_audience=premium_audience,
    )


def _build_scalar_metrics(
    *,
    snapshot: ChannelStatsSnapshot,
    statistics: dict[str, Any],
    premium_audience: ChannelStatsPremiumAudience,
) -> list[ChannelStatsScalarMetric]:
    metrics: list[ChannelStatsScalarMetric] = [
        _snapshot_value_metric("subscribers", snapshot.subscribers),
        _snapshot_value_metric("avg_views", snapshot.avg_views),
        (
            ChannelStatsScalarMetric(
                key="premium_ratio",
                availability=ChannelStatsAvailability.ready,
                value=premium_audience.premium_ratio,
            )
            if premium_audience.premium_ratio is not None
            else ChannelStatsScalarMetric(
                key="premium_ratio",
                availability=ChannelStatsAvailability.missing,
            )
        ),
    ]

    for key in sorted(statistics.keys()):
        if key.endswith("_graph"):
            continue
        if key in {"_", "subscribers", "avg_views", "premium_ratio"}:
            continue
        metric = _normalize_scalar_metric(key=key, value=statistics.get(key))
        if metric is not None:
            metrics.append(metric)

    return metrics


def _snapshot_value_metric(key: str, value: int | None) -> ChannelStatsScalarMetric:
    if value is None:
        return ChannelStatsScalarMetric(
            key=key,
            availability=ChannelStatsAvailability.missing,
        )
    return ChannelStatsScalarMetric(
        key=key,
        availability=ChannelStatsAvailability.ready,
        value=value,
    )


def _normalize_scalar_metric(*, key: str, value: Any) -> ChannelStatsScalarMetric | None:
    if value is None:
        return ChannelStatsScalarMetric(
            key=key,
            availability=ChannelStatsAvailability.missing,
        )

    if isinstance(value, (int, float, str, bool)):
        return ChannelStatsScalarMetric(
            key=key,
            availability=ChannelStatsAvailability.ready,
            value=value,
        )

    if isinstance(value, dict):
        marker = str(value.get("_") or "")

        if marker == "StatsAbsValueAndPrev":
            current = _coerce_number(value.get("current"))
            previous = _coerce_number(value.get("previous"))
            if current is not None:
                return ChannelStatsScalarMetric(
                    key=key,
                    availability=ChannelStatsAvailability.ready,
                    value=current,
                    previous=previous,
                )
            return ChannelStatsScalarMetric(
                key=key,
                availability=ChannelStatsAvailability.missing,
                reason="missing_current",
            )

        if marker == "StatsPercentValue":
            part = _coerce_float(value.get("part"))
            total = _coerce_float(value.get("total"))
            ratio = _ratio(part=part, total=total)
            if ratio is not None or part is not None or total is not None:
                return ChannelStatsScalarMetric(
                    key=key,
                    availability=ChannelStatsAvailability.ready,
                    value=ratio,
                    part=part,
                    total=total,
                )
            return ChannelStatsScalarMetric(
                key=key,
                availability=ChannelStatsAvailability.missing,
                reason="missing_percent_values",
            )

        current = _coerce_number(value.get("current"))
        if current is not None:
            return ChannelStatsScalarMetric(
                key=key,
                availability=ChannelStatsAvailability.ready,
                value=current,
                previous=_coerce_number(value.get("previous")),
            )

        part = _coerce_float(value.get("part"))
        total = _coerce_float(value.get("total"))
        ratio = _ratio(part=part, total=total)
        if ratio is not None or part is not None or total is not None:
            return ChannelStatsScalarMetric(
                key=key,
                availability=ChannelStatsAvailability.ready,
                value=ratio,
                part=part,
                total=total,
            )

        reason = value.get("error")
        if isinstance(reason, str) and reason.strip():
            return ChannelStatsScalarMetric(
                key=key,
                availability=ChannelStatsAvailability.error,
                reason=reason,
            )

        return ChannelStatsScalarMetric(
            key=key,
            availability=ChannelStatsAvailability.missing,
            reason="unsupported_metric_format",
        )

    return ChannelStatsScalarMetric(
        key=key,
        availability=ChannelStatsAvailability.missing,
        reason="unsupported_metric_type",
    )


def _build_chart_metrics(*, statistics: dict[str, Any]) -> list[ChannelStatsChartMetric]:
    metrics: list[ChannelStatsChartMetric] = []
    for key in sorted(statistics.keys()):
        if not key.endswith("_graph"):
            continue
        metrics.append(_normalize_chart_metric(key=key, value=statistics.get(key)))
    return metrics


def _normalize_chart_metric(*, key: str, value: Any) -> ChannelStatsChartMetric:
    if not isinstance(value, dict):
        return ChannelStatsChartMetric(
            key=key,
            availability=ChannelStatsAvailability.missing,
        )

    marker = str(value.get("_") or "")

    if marker == "StatsGraphAsync":
        token = _coerce_str(value.get("token")) or _coerce_str(value.get("zoom_token"))
        return ChannelStatsChartMetric(
            key=key,
            availability=ChannelStatsAvailability.async_pending,
            token=token,
        )

    if marker == "StatsGraphError":
        return ChannelStatsChartMetric(
            key=key,
            availability=ChannelStatsAvailability.error,
            reason=_coerce_str(value.get("error")) or "Unknown chart error",
        )

    if marker == "StatsGraph":
        payload = value.get("json")
        if isinstance(payload, (dict, list, str)):
            return ChannelStatsChartMetric(
                key=key,
                availability=ChannelStatsAvailability.ready,
                data=payload,
            )
        reduced = {k: v for k, v in value.items() if k not in {"_", "token", "zoom_token"}}
        return ChannelStatsChartMetric(
            key=key,
            availability=ChannelStatsAvailability.ready,
            data=reduced if reduced else None,
        )

    # Some graphs are already materialized plain dict payloads.
    if not marker:
        return ChannelStatsChartMetric(
            key=key,
            availability=ChannelStatsAvailability.ready,
            data=value,
        )

    return ChannelStatsChartMetric(
        key=key,
        availability=ChannelStatsAvailability.missing,
        reason="unsupported_graph_marker",
    )


def _normalize_premium_audience(
    *,
    premium_graph: dict[str, Any],
    boosts_status: dict[str, Any],
    premium_stats: dict[str, Any],
) -> ChannelStatsPremiumAudience:
    boosts_audience = _as_dict(boosts_status.get("premium_audience"))
    premium_stats_audience = _as_dict(premium_stats.get("premium_audience"))

    ratio = _extract_ratio(premium_graph)
    part, total = _extract_part_total(premium_graph)

    if ratio is None:
        ratio = _extract_ratio(boosts_audience)
        if ratio is not None:
            part, total = _extract_part_total(boosts_audience)

    if ratio is None:
        ratio = _coerce_float(premium_stats.get("premium_ratio"))

    if part is None and total is None:
        part, total = _extract_part_total(boosts_audience)

    if part is None and total is None:
        part, total = _extract_part_total(premium_stats_audience)

    availability = (
        ChannelStatsAvailability.ready
        if ratio is not None or part is not None or total is not None
        else ChannelStatsAvailability.missing
    )
    return ChannelStatsPremiumAudience(
        availability=availability,
        premium_ratio=ratio,
        part=part,
        total=total,
    )


def _extract_part_total(value: Any) -> tuple[float | None, float | None]:
    data = _as_dict(value)
    if not data:
        return None, None
    return _coerce_float(data.get("part")), _coerce_float(data.get("total"))


def _extract_ratio(value: Any) -> float | None:
    data = _as_dict(value)
    if not data:
        return None
    explicit = _coerce_float(data.get("premium_ratio"))
    if explicit is not None:
        return explicit
    part = _coerce_float(data.get("part"))
    total = _coerce_float(data.get("total"))
    return _ratio(part=part, total=total)


def _ratio(*, part: float | None, total: float | None) -> float | None:
    if part is None or total is None or total <= 0:
        return None
    return part / total


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_number(value: Any) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        as_float = float(value)
    except (TypeError, ValueError):
        return None
    if as_float.is_integer():
        return int(as_float)
    return as_float


def _coerce_str(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
