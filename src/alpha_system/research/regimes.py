"""Regime-filter diagnostics for research-only factor checks."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


def regime_filter_uplift(
    observations: Iterable[Mapping[str, Any]],
    *,
    filter_field: str = "regime_filter",
) -> dict[str, float | int | None]:
    """Compare forward returns with a filter active vs inactive."""
    rows = tuple(observations)
    with_filter = [_return(row) for row in rows if _active(row, filter_field)]
    without_filter = [_return(row) for row in rows if not _active(row, filter_field)]
    with_values = [value for value in with_filter if value is not None]
    without_values = [value for value in without_filter if value is not None]
    with_mean = _mean(with_values)
    without_mean = _mean(without_values)
    return {
        "with_filter_n": len(with_values),
        "without_filter_n": len(without_values),
        "with_filter_mean": with_mean,
        "without_filter_mean": without_mean,
        "uplift": None if with_mean is None or without_mean is None else with_mean - without_mean,
    }


def regime_filter_coverage(
    observations: Iterable[Mapping[str, Any]],
    *,
    filter_field: str = "regime_filter",
) -> dict[str, float | int | None]:
    """Return share of observations retained by a regime filter."""
    rows = tuple(observations)
    if not rows:
        return {"coverage": None, "retained": 0, "total": 0}
    retained = sum(1 for row in rows if _active(row, filter_field))
    return {"coverage": retained / len(rows), "retained": retained, "total": len(rows)}


def false_rejection_rate(
    observations: Iterable[Mapping[str, Any]],
    *,
    filter_field: str = "regime_filter",
) -> dict[str, float | int | None]:
    """Return positive-label observations rejected by a filter."""
    positive = [row for row in observations if (_return(row) or 0) > 0]
    if not positive:
        return {"false_rejection_rate": None, "positive_count": 0}
    rejected = sum(1 for row in positive if not _active(row, filter_field))
    return {"false_rejection_rate": rejected / len(positive), "positive_count": len(positive)}


def conditional_strategy_improvement(
    observations: Iterable[Mapping[str, Any]],
    *,
    filter_field: str = "regime_filter",
) -> dict[str, float | int | None]:
    """Return hit-rate and mean-return differences for retained observations."""
    rows = [row for row in observations if _return(row) is not None]
    retained = [row for row in rows if _active(row, filter_field)]
    all_returns = [_return(row) for row in rows]
    retained_returns = [_return(row) for row in retained]
    all_values = [value for value in all_returns if value is not None]
    retained_values = [value for value in retained_returns if value is not None]
    all_mean = _mean(all_values)
    retained_mean = _mean(retained_values)
    return {
        "retained_n": len(retained_values),
        "all_n": len(all_values),
        "mean_return_improvement": (
            None if retained_mean is None or all_mean is None else retained_mean - all_mean
        ),
        "hit_rate_improvement": _difference(_hit_rate(retained_values), _hit_rate(all_values)),
    }


def _active(row: Mapping[str, Any], field: str) -> bool:
    if field in row:
        return bool(row[field])
    value = row.get("factor_value")
    if isinstance(value, bool):
        return value
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _return(row: Mapping[str, Any]) -> float | None:
    value = row.get("forward_return", row.get("label_value"))
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean(values: Sequence[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def _hit_rate(values: Sequence[float]) -> float | None:
    return None if not values else sum(1 for value in values if value > 0) / len(values)


def _difference(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right
