"""Information-coefficient diagnostics for factor research."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
from math import sqrt
from typing import Any


Number = int | float


def pearson_ic(
    factor_values: Iterable[Any],
    label_values: Iterable[Any],
) -> dict[str, float | int | None]:
    """Return Pearson information coefficient and sample count."""
    pairs = _clean_pairs(factor_values, label_values)
    return {"ic": _pearson([x for x, _ in pairs], [y for _, y in pairs]), "n": len(pairs)}


def rank_ic(
    factor_values: Iterable[Any],
    label_values: Iterable[Any],
) -> dict[str, float | int | None]:
    """Return Spearman rank information coefficient and sample count."""
    pairs = _clean_pairs(factor_values, label_values)
    if not pairs:
        return {"ic": None, "n": 0}
    ranked_x = _average_ranks([x for x, _ in pairs])
    ranked_y = _average_ranks([y for _, y in pairs])
    return {"ic": _pearson(ranked_x, ranked_y), "n": len(pairs)}


def ic_by_horizon(
    observations: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, float | int | None]]:
    """Compute Pearson and rank IC for each horizon."""
    groups: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    for row in observations:
        groups[_horizon_seconds(row)].append(row)
    return {
        str(horizon): {
            "pearson_ic": pearson_ic(
                (row.get("factor_value") for row in rows),
                (row.get("label_value") for row in rows),
            )["ic"],
            "rank_ic": rank_ic(
                (row.get("factor_value") for row in rows),
                (row.get("label_value") for row in rows),
            )["ic"],
            "n": len(_clean_pairs(
                (row.get("factor_value") for row in rows),
                (row.get("label_value") for row in rows),
            )),
        }
        for horizon, rows in sorted(groups.items())
    }


def ic_decay(observations: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Return IC by horizon plus the long-minus-short IC slope."""
    by_horizon = ic_by_horizon(observations)
    points = [
        (int(horizon), metrics["pearson_ic"])
        for horizon, metrics in by_horizon.items()
        if metrics["pearson_ic"] is not None
    ]
    if len(points) < 2:
        slope = None
    else:
        first_horizon, first_ic = points[0]
        last_horizon, last_ic = points[-1]
        assert first_ic is not None and last_ic is not None
        denominator = max(last_horizon - first_horizon, 1)
        slope = (float(last_ic) - float(first_ic)) / denominator
    return {"by_horizon": by_horizon, "decay_slope_per_second": slope, "n_horizons": len(points)}


def ic_by_calendar_period(
    observations: Iterable[Mapping[str, Any]],
    *,
    period: str = "day",
) -> dict[str, dict[str, float | int | None]]:
    """Compute IC grouped by day, ISO week, or month."""
    if period not in {"day", "week", "month"}:
        msg = "period must be day, week, or month"
        raise ValueError(msg)
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in observations:
        groups[_period_key(_datetime(row["event_ts"]), period)].append(row)
    return {
        key: pearson_ic(
            (row.get("factor_value") for row in rows),
            (row.get("label_value") for row in rows),
        )
        for key, rows in sorted(groups.items())
    }


def icir(ic_values: Iterable[Any]) -> dict[str, float | int | None]:
    """Return IC information ratio from a series of period IC values."""
    values = [_float(value) for value in ic_values]
    values = [value for value in values if value is not None]
    if not values:
        return {"icir": None, "mean_ic": None, "std_ic": None, "n": 0}
    mean = sum(values) / len(values)
    if len(values) < 2:
        return {"icir": None, "mean_ic": mean, "std_ic": None, "n": len(values)}
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    std = sqrt(variance)
    return {
        "icir": None if std <= 1e-12 else mean / std,
        "mean_ic": mean,
        "std_ic": std,
        "n": len(values),
    }


def icir_from_calendar_periods(
    observations: Iterable[Mapping[str, Any]],
    *,
    period: str = "day",
) -> dict[str, float | int | None]:
    """Compute period IC and return ICIR over non-null period values."""
    by_period = ic_by_calendar_period(observations, period=period)
    return icir(metrics["ic"] for metrics in by_period.values())


def _clean_pairs(
    factor_values: Iterable[Any],
    label_values: Iterable[Any],
) -> tuple[tuple[float, float], ...]:
    pairs: list[tuple[float, float]] = []
    for left, right in zip(factor_values, label_values, strict=False):
        x = _float(left)
        y = _float(right)
        if x is not None and y is not None:
            pairs.append((x, y))
    return tuple(pairs)


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(ys) < 2:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    centered = [(x - mean_x, y - mean_y) for x, y in zip(xs, ys, strict=True)]
    numerator = sum(x * y for x, y in centered)
    denom_x = sqrt(sum(x * x for x, _ in centered))
    denom_y = sqrt(sum(y * y for _, y in centered))
    denominator = denom_x * denom_y
    if denominator == 0:
        return None
    return numerator / denominator


def _average_ranks(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(indexed):
        end = index + 1
        while end < len(indexed) and indexed[end][1] == indexed[index][1]:
            end += 1
        average_rank = (index + 1 + end) / 2
        for original_index, _ in indexed[index:end]:
            ranks[original_index] = average_rank
        index = end
    return ranks


def _float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _horizon_seconds(row: Mapping[str, Any]) -> int:
    if "horizon_seconds" in row:
        return int(row["horizon_seconds"])
    if "horizon" in row:
        horizon = row["horizon"]
        if hasattr(horizon, "total_seconds"):
            return int(horizon.total_seconds())
        return int(horizon)
    return 0


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        active = value
    else:
        active = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc)


def _period_key(value: datetime, period: str) -> str:
    if period == "day":
        return value.date().isoformat()
    if period == "week":
        iso = value.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    return f"{value.year:04d}-{value.month:02d}"
