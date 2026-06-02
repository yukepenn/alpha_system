"""Event-trigger factor diagnostics."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


def event_study(
    observations: Iterable[Mapping[str, Any]],
    *,
    trigger_threshold: float = 0.0,
) -> dict[str, float | int | None]:
    """Compare event-trigger observations against non-events."""
    rows = tuple(observations)
    event_returns = [
        value
        for row in rows
        if _is_event(row, trigger_threshold=trigger_threshold)
        and (value := _return(row)) is not None
    ]
    non_event_returns = [
        value
        for row in rows
        if not _is_event(row, trigger_threshold=trigger_threshold)
        and (value := _return(row)) is not None
    ]
    return {
        "event_count": len(event_returns),
        "non_event_count": len(non_event_returns),
        "event_mean_return": _mean(event_returns),
        "non_event_mean_return": _mean(non_event_returns),
        "uplift": _difference(_mean(event_returns), _mean(non_event_returns)),
    }


def conditional_forward_returns(
    observations: Iterable[Mapping[str, Any]],
    *,
    trigger_threshold: float = 0.0,
) -> dict[str, float | int | None]:
    """Alias event-study return summary for event-trigger diagnostics."""
    return event_study(observations, trigger_threshold=trigger_threshold)


def sample_size(
    observations: Iterable[Mapping[str, Any]],
    *,
    trigger_threshold: float = 0.0,
) -> dict[str, int]:
    """Return total/event/non-event sample counts."""
    rows = tuple(observations)
    event_count = sum(1 for row in rows if _is_event(row, trigger_threshold=trigger_threshold))
    return {"total": len(rows), "events": event_count, "non_events": len(rows) - event_count}


def false_breakout_rate(
    observations: Iterable[Mapping[str, Any]],
    *,
    trigger_threshold: float = 0.0,
) -> dict[str, float | int | None]:
    """Return event share with non-positive forward return."""
    returns = [
        value
        for row in observations
        if _is_event(row, trigger_threshold=trigger_threshold)
        and (value := _return(row)) is not None
    ]
    if not returns:
        return {"false_breakout_rate": None, "event_count": 0}
    return {
        "false_breakout_rate": sum(1 for value in returns if value <= 0) / len(returns),
        "event_count": len(returns),
    }


def target_before_stop_probability(
    observations: Iterable[Mapping[str, Any]],
    *,
    trigger_threshold: float = 0.0,
) -> dict[str, float | int | None]:
    """Return event share where target-before-stop label is true."""
    values = [
        bool(row["target_before_stop"])
        for row in observations
        if _is_event(row, trigger_threshold=trigger_threshold)
        and row.get("target_before_stop") is not None
    ]
    if not values:
        return {"target_before_stop_probability": None, "event_count": 0}
    return {
        "target_before_stop_probability": sum(1 for value in values if value) / len(values),
        "event_count": len(values),
    }


def post_event_mfe_mae(
    observations: Iterable[Mapping[str, Any]],
    *,
    trigger_threshold: float = 0.0,
) -> dict[str, float | int | None]:
    """Return post-event MFE and MAE averages."""
    events = [row for row in observations if _is_event(row, trigger_threshold=trigger_threshold)]
    mfe = [value for row in events if (value := _float(row.get("mfe"))) is not None]
    mae = [value for row in events if (value := _float(row.get("mae"))) is not None]
    return {
        "event_count": len(events),
        "mfe_n": len(mfe),
        "mean_mfe": _mean(mfe),
        "mae_n": len(mae),
        "mean_mae": _mean(mae),
    }


def _is_event(row: Mapping[str, Any], *, trigger_threshold: float) -> bool:
    if "event_trigger" in row:
        return bool(row["event_trigger"])
    value = row.get("factor_value")
    if isinstance(value, bool):
        return value
    numeric = _float(value)
    return False if numeric is None else numeric > trigger_threshold


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


def _difference(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right
