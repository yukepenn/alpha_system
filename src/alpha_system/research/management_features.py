"""Management-feature diagnostics only; no execution accounting."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


def target_before_stop(
    observations: Iterable[Mapping[str, Any]],
) -> dict[str, float | int | None]:
    values = [bool(row["target_before_stop"]) for row in observations if row.get("target_before_stop") is not None]
    return {"probability": None if not values else sum(values) / len(values), "n": len(values)}


def time_to_target(
    observations: Iterable[Mapping[str, Any]],
) -> dict[str, float | int | None]:
    values = [value for row in observations if (value := _float(row.get("time_to_target"))) is not None]
    return {"mean_bars": _mean(values), "n": len(values)}


def time_to_stop(
    observations: Iterable[Mapping[str, Any]],
) -> dict[str, float | int | None]:
    values = [value for row in observations if (value := _float(row.get("time_to_stop"))) is not None]
    return {"mean_bars": _mean(values), "n": len(values)}


def breakeven_usefulness(
    observations: Iterable[Mapping[str, Any]],
) -> dict[str, float | int | None]:
    """Estimate whether positive excursion existed before stop-first outcomes."""
    candidates = [
        row
        for row in observations
        if row.get("stop_before_target") is True and _float(row.get("mfe")) is not None
    ]
    if not candidates:
        return {"usefulness_rate": None, "n": 0}
    useful = sum(1 for row in candidates if (_float(row.get("mfe")) or 0) > 0)
    return {"usefulness_rate": useful / len(candidates), "n": len(candidates)}


def trailing_stop_usefulness(
    observations: Iterable[Mapping[str, Any]],
) -> dict[str, float | int | None]:
    """Estimate whether peak favorable excursion exceeded terminal return."""
    candidates = [
        row
        for row in observations
        if _float(row.get("mfe")) is not None and _float(row.get("forward_return", row.get("label_value"))) is not None
    ]
    if not candidates:
        return {"usefulness_rate": None, "n": 0}
    useful = 0
    for row in candidates:
        mfe = _float(row.get("mfe"))
        forward = _float(row.get("forward_return", row.get("label_value")))
        assert mfe is not None and forward is not None
        if mfe > max(forward, 0.0):
            useful += 1
    return {"usefulness_rate": useful / len(candidates), "n": len(candidates)}


def management_feature_summary(observations: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = tuple(observations)
    return {
        "target_before_stop": target_before_stop(rows),
        "time_to_target": time_to_target(rows),
        "time_to_stop": time_to_stop(rows),
        "breakeven_usefulness": breakeven_usefulness(rows),
        "trailing_stop_usefulness": trailing_stop_usefulness(rows),
    }


def _float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean(values: Sequence[float]) -> float | None:
    return None if not values else sum(values) / len(values)
