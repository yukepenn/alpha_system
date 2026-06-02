"""Bucket diagnostics for nonlinear factor behavior."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from math import sqrt
from typing import Any


def bucket_forward_returns(
    observations: Iterable[Mapping[str, Any]],
    *,
    bucket_count: int = 5,
) -> list[dict[str, float | int | None]]:
    """Bucket observations by factor rank and summarize forward returns."""
    rows = _clean_rows(observations)
    assignments = _assign_buckets([row["factor_value"] for row in rows], bucket_count)
    summaries: list[dict[str, float | int | None]] = []
    for bucket in range(1, bucket_count + 1):
        values = [
            float(row["label_value"])
            for row, assigned in zip(rows, assignments, strict=True)
            if assigned == bucket
        ]
        summaries.append(
            {
                "bucket": bucket,
                "n": len(values),
                "mean_return": _mean(values),
                "hit_rate": _hit_rate(values),
            }
        )
    return summaries


def bucket_monotonicity(
    bucket_summary: Sequence[Mapping[str, Any]],
) -> dict[str, float | int | bool | str | None]:
    """Assess whether bucket mean returns move consistently across buckets."""
    means = [_float(row.get("mean_return")) for row in bucket_summary]
    values = [value for value in means if value is not None]
    if len(values) < 2:
        return {
            "is_monotonic": False,
            "direction": "insufficient",
            "rank_correlation": None,
            "sign_changes": None,
            "n_buckets": len(values),
        }
    nondecreasing = all(values[index] <= values[index + 1] for index in range(len(values) - 1))
    nonincreasing = all(values[index] >= values[index + 1] for index in range(len(values) - 1))
    direction = "increasing" if nondecreasing else "decreasing" if nonincreasing else "mixed"
    deltas = [values[index + 1] - values[index] for index in range(len(values) - 1)]
    signs = [1 if delta > 0 else -1 if delta < 0 else 0 for delta in deltas]
    non_zero_signs = [sign for sign in signs if sign]
    sign_changes = sum(
        1
        for index in range(len(non_zero_signs) - 1)
        if non_zero_signs[index] != non_zero_signs[index + 1]
    )
    return {
        "is_monotonic": nondecreasing or nonincreasing,
        "direction": direction,
        "rank_correlation": _pearson(
            [float(index + 1) for index in range(len(values))],
            values,
        ),
        "sign_changes": sign_changes,
        "n_buckets": len(values),
    }


def tail_expectancy(
    bucket_summary: Sequence[Mapping[str, Any]],
) -> dict[str, float | int | None]:
    """Return high-tail minus low-tail mean forward return."""
    populated = [row for row in bucket_summary if _float(row.get("mean_return")) is not None]
    if len(populated) < 2:
        return {"tail_expectancy": None, "low_tail_mean": None, "high_tail_mean": None}
    low = populated[0]
    high = populated[-1]
    low_mean = _float(low.get("mean_return"))
    high_mean = _float(high.get("mean_return"))
    assert low_mean is not None and high_mean is not None
    return {
        "tail_expectancy": high_mean - low_mean,
        "low_tail_mean": low_mean,
        "high_tail_mean": high_mean,
        "low_tail_n": int(low.get("n", 0)),
        "high_tail_n": int(high.get("n", 0)),
    }


def u_shape_profile(
    bucket_summary: Sequence[Mapping[str, Any]],
) -> dict[str, float | bool | None]:
    """Measure whether edge buckets outperform center buckets."""
    values = [_float(row.get("mean_return")) for row in bucket_summary]
    means = [value for value in values if value is not None]
    if len(means) < 3:
        return {"u_shape_score": None, "is_u_shaped": False, "edge_mean": None, "center_mean": None}
    edge_mean = (means[0] + means[-1]) / 2
    middle = means[1:-1]
    center_mean = sum(middle) / len(middle)
    return {
        "u_shape_score": edge_mean - center_mean,
        "is_u_shaped": means[0] > center_mean and means[-1] > center_mean,
        "edge_mean": edge_mean,
        "center_mean": center_mean,
    }


def extreme_bucket_hit_rate(
    observations: Iterable[Mapping[str, Any]],
    *,
    bucket_count: int = 5,
) -> dict[str, float | int | None]:
    """Return hit rates for the lowest and highest factor buckets."""
    rows = _clean_rows(observations)
    assignments = _assign_buckets([row["factor_value"] for row in rows], bucket_count)
    low = [
        float(row["label_value"])
        for row, bucket in zip(rows, assignments, strict=True)
        if bucket == 1
    ]
    high = [
        float(row["label_value"])
        for row, bucket in zip(rows, assignments, strict=True)
        if bucket == bucket_count
    ]
    return {
        "low_tail_hit_rate": _hit_rate(low),
        "high_tail_hit_rate": _hit_rate(high),
        "low_tail_n": len(low),
        "high_tail_n": len(high),
    }


def mfe_mae_by_bucket(
    observations: Iterable[Mapping[str, Any]],
    *,
    bucket_count: int = 5,
) -> list[dict[str, float | int | None]]:
    """Summarize post-event MFE and MAE labels by factor bucket."""
    rows = [row for row in observations if _float(row.get("factor_value")) is not None]
    assignments = _assign_buckets([row["factor_value"] for row in rows], bucket_count)
    output: list[dict[str, float | int | None]] = []
    for bucket in range(1, bucket_count + 1):
        mfe_values = [
            value
            for row, assigned in zip(rows, assignments, strict=True)
            if assigned == bucket and (value := _float(row.get("mfe"))) is not None
        ]
        mae_values = [
            value
            for row, assigned in zip(rows, assignments, strict=True)
            if assigned == bucket and (value := _float(row.get("mae"))) is not None
        ]
        output.append(
            {
                "bucket": bucket,
                "n_mfe": len(mfe_values),
                "mean_mfe": _mean(mfe_values),
                "n_mae": len(mae_values),
                "mean_mae": _mean(mae_values),
            }
        )
    return output


def _clean_rows(observations: Iterable[Mapping[str, Any]]) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for row in observations:
        factor = _float(row.get("factor_value"))
        label = _float(row.get("label_value", row.get("forward_return")))
        if factor is not None and label is not None:
            rows.append({"factor_value": factor, "label_value": label})
    return rows


def _assign_buckets(values: Sequence[Any], bucket_count: int) -> list[int]:
    if bucket_count < 2:
        msg = "bucket_count must be at least 2"
        raise ValueError(msg)
    numeric = [_float(value) for value in values]
    if any(value is None for value in numeric):
        msg = "all bucket inputs must be numeric"
        raise ValueError(msg)
    indexed = sorted(enumerate(float(value) for value in numeric if value is not None), key=lambda item: item[1])
    assignments = [1] * len(values)
    count = len(indexed)
    if count == 0:
        return assignments
    for rank, (index, _) in enumerate(indexed):
        assignments[index] = min(bucket_count, int(rank * bucket_count / count) + 1)
    return assignments


def _mean(values: Sequence[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def _hit_rate(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return sum(1 for value in values if value > 0) / len(values)


def _float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(ys) < 2:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    denom_x = sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = sqrt(sum((y - mean_y) ** 2 for y in ys))
    denominator = denom_x * denom_y
    return None if denominator == 0 else numerator / denominator
