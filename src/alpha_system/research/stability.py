"""Stability helpers for intraday factor diagnostics."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from alpha_system.research.ic import pearson_ic


def time_of_day_stability(observations: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Summarize observations by UTC HH:MM event time."""
    return _group_summary(observations, key_fn=lambda row: _datetime(row["event_ts"]).strftime("%H:%M"))


def session_segment_stability(
    observations: Iterable[Mapping[str, Any]],
    *,
    segments: int = 3,
) -> dict[str, dict[str, Any]]:
    """Summarize observations by early/middle/late bar-index segment."""
    rows = tuple(observations)
    max_index = max((int(row.get("bar_index", 0)) for row in rows), default=0)

    def key(row: Mapping[str, Any]) -> str:
        if max_index <= 0:
            return "segment_1"
        segment = min(segments, int(int(row.get("bar_index", 0)) * segments / (max_index + 1)) + 1)
        return f"segment_{segment}"

    return _group_summary(rows, key_fn=key)


def monthly_stability(observations: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Summarize observations by calendar month."""
    return _group_summary(
        observations,
        key_fn=lambda row: _datetime(row["event_ts"]).strftime("%Y-%m"),
    )


def regime_stability(
    observations: Iterable[Mapping[str, Any]],
    *,
    field: str = "regime",
) -> dict[str, dict[str, Any]]:
    """Summarize observations by a caller-supplied regime field."""
    return _group_summary(observations, key_fn=lambda row: str(row.get(field, "unknown")))


def _group_summary(
    observations: Iterable[Mapping[str, Any]],
    *,
    key_fn: Any,
) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in observations:
        groups[str(key_fn(row))].append(row)
    output: dict[str, dict[str, Any]] = {}
    for key, rows in sorted(groups.items()):
        returns = [
            value
            for row in rows
            if (value := _float(row.get("forward_return", row.get("label_value")))) is not None
        ]
        output[key] = {
            "n": len(rows),
            "mean_forward_return": _mean(returns),
            "pearson_ic": pearson_ic(
                (row.get("factor_value") for row in rows),
                (row.get("label_value", row.get("forward_return")) for row in rows),
            )["ic"],
        }
    return output


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        active = value
    else:
        active = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc)


def _float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean(values: Sequence[float]) -> float | None:
    return None if not values else sum(values) / len(values)
