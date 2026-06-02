"""Execution-filter sensitivity diagnostics without execution accounting."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from math import sqrt
from typing import Any


def sensitivity_by_field(
    observations: Iterable[Mapping[str, Any]],
    *,
    field: str,
    bucket_count: int = 3,
) -> dict[str, Any]:
    """Measure forward-return sensitivity to a numeric filter field."""
    rows = [
        (metric, forward)
        for row in observations
        if (metric := _float(row.get(field))) is not None
        and (forward := _return(row)) is not None
    ]
    if not rows:
        return {"field": field, "n": 0, "correlation": None, "buckets": []}
    assignments = _assign_buckets([metric for metric, _ in rows], bucket_count)
    buckets = []
    for bucket in range(1, bucket_count + 1):
        bucket_rows = [
            (metric, forward)
            for (metric, forward), assigned in zip(rows, assignments, strict=True)
            if assigned == bucket
        ]
        forwards = [forward for _, forward in bucket_rows]
        metrics = [metric for metric, _ in bucket_rows]
        buckets.append(
            {
                "bucket": bucket,
                "n": len(bucket_rows),
                "mean_filter_value": _mean(metrics),
                "mean_forward_return": _mean(forwards),
            }
        )
    return {
        "field": field,
        "n": len(rows),
        "correlation": _pearson([metric for metric, _ in rows], [forward for _, forward in rows]),
        "buckets": buckets,
    }


def spread_sensitivity(observations: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    return sensitivity_by_field(observations, field="spread")


def liquidity_sensitivity(observations: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    return sensitivity_by_field(observations, field="liquidity")


def slippage_sensitivity(observations: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    return sensitivity_by_field(observations, field="slippage")


def volume_participation_sensitivity(observations: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    return sensitivity_by_field(observations, field="volume_participation")


def adverse_selection_proxy(observations: Iterable[Mapping[str, Any]]) -> dict[str, float | int | None]:
    """Use factor direction times forward return as a simple adverse-selection proxy."""
    values = []
    for row in observations:
        factor = _float(row.get("factor_value"))
        forward = _return(row)
        if factor is not None and forward is not None:
            direction = 1.0 if factor >= 0 else -1.0
            values.append(direction * forward)
    if not values:
        return {"adverse_selection_proxy": None, "n": 0}
    return {"adverse_selection_proxy": -_mean(values), "n": len(values)}


def execution_filter_summary(observations: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Return all scoped execution-filter diagnostics."""
    rows = tuple(observations)
    return {
        "spread_sensitivity": spread_sensitivity(rows),
        "liquidity_sensitivity": liquidity_sensitivity(rows),
        "slippage_sensitivity": slippage_sensitivity(rows),
        "volume_participation": volume_participation_sensitivity(rows),
        "adverse_selection_proxy": adverse_selection_proxy(rows),
    }


def _assign_buckets(values: Sequence[float], bucket_count: int) -> list[int]:
    if bucket_count < 2:
        msg = "bucket_count must be at least 2"
        raise ValueError(msg)
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    count = len(indexed)
    assignments = [1] * count
    for rank, (index, _) in enumerate(indexed):
        assignments[index] = min(bucket_count, int(rank * bucket_count / count) + 1)
    return assignments


def _return(row: Mapping[str, Any]) -> float | None:
    return _float(row.get("forward_return", row.get("label_value")))


def _float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean(values: Sequence[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    denominator = sqrt(sum((x - mean_x) ** 2 for x in xs)) * sqrt(
        sum((y - mean_y) ** 2 for y in ys)
    )
    return None if denominator == 0 else numerator / denominator
