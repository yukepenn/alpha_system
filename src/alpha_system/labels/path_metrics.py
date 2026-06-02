"""Path-dependent label metrics for tiny deterministic bar paths."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class ExcursionMetrics:
    """MFE/MAE values and path details for a forward bar window."""

    mfe: float | None
    mae: float | None
    path_metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class StopTargetOrdering:
    """Conservative target/stop ordering result for one forward bar path."""

    ordering: str
    target_before_stop: bool
    stop_before_target: bool
    path_metadata: dict[str, Any]


def compute_mfe_mae(
    *,
    entry_price: Decimal,
    path_bars: Iterable[Mapping[str, Any]],
) -> ExcursionMetrics:
    """Compute long-side MFE and MAE from high/low prices in a path."""
    bars = tuple(path_bars)
    metadata: dict[str, Any] = {"path_bar_count": len(bars)}
    if not bars or entry_price <= Decimal("0"):
        metadata["insufficient_path"] = True
        return ExcursionMetrics(mfe=None, mae=None, path_metadata=metadata)

    max_high_bar = max(bars, key=lambda row: _decimal(row["high"]))
    min_low_bar = min(bars, key=lambda row: _decimal(row["low"]))
    max_high = _decimal(max_high_bar["high"])
    min_low = _decimal(min_low_bar["low"])
    mfe = (max_high / entry_price) - Decimal("1")
    mae = (min_low / entry_price) - Decimal("1")

    metadata.update(
        {
            "entry_price": str(entry_price),
            "max_high": str(max_high),
            "max_high_bar_index": int(max_high_bar["bar_index"]),
            "max_high_event_ts": _datetime_to_text(max_high_bar["event_ts"]),
            "min_low": str(min_low),
            "min_low_bar_index": int(min_low_bar["bar_index"]),
            "min_low_event_ts": _datetime_to_text(min_low_bar["event_ts"]),
        }
    )
    return ExcursionMetrics(mfe=float(mfe), mae=float(mae), path_metadata=metadata)


def compute_stop_target_ordering(
    *,
    entry_price: Decimal,
    path_bars: Iterable[Mapping[str, Any]],
    target_return: Decimal,
    stop_return: Decimal,
) -> StopTargetOrdering:
    """Return conservative target/stop ordering for a long-side path."""
    bars = tuple(path_bars)
    target_price = entry_price * (Decimal("1") + target_return)
    stop_price = entry_price * (Decimal("1") - stop_return)
    metadata: dict[str, Any] = {
        "entry_price": str(entry_price),
        "target_return": str(target_return),
        "stop_return": str(stop_return),
        "target_price": str(target_price),
        "stop_price": str(stop_price),
        "path_bar_count": len(bars),
    }
    target_hit: Mapping[str, Any] | None = None
    stop_hit: Mapping[str, Any] | None = None

    for bar in bars:
        high = _decimal(bar["high"])
        low = _decimal(bar["low"])
        hit_target = high >= target_price
        hit_stop = low <= stop_price
        if hit_target and target_hit is None:
            target_hit = bar
        if hit_stop and stop_hit is None:
            stop_hit = bar
        if hit_target and hit_stop:
            metadata.update(_hit_metadata("target", bar))
            metadata.update(_hit_metadata("stop", bar))
            metadata["ambiguous_same_bar"] = True
            return StopTargetOrdering(
                ordering="ambiguous_same_bar",
                target_before_stop=False,
                stop_before_target=False,
                path_metadata=metadata,
            )

    if target_hit is None and stop_hit is None:
        metadata["neither_hit"] = True
        return StopTargetOrdering(
            ordering="neither",
            target_before_stop=False,
            stop_before_target=False,
            path_metadata=metadata,
        )
    if target_hit is not None and stop_hit is None:
        metadata.update(_hit_metadata("target", target_hit))
        return StopTargetOrdering(
            ordering="target_before_stop",
            target_before_stop=True,
            stop_before_target=False,
            path_metadata=metadata,
        )
    if stop_hit is not None and target_hit is None:
        metadata.update(_hit_metadata("stop", stop_hit))
        return StopTargetOrdering(
            ordering="stop_before_target",
            target_before_stop=False,
            stop_before_target=True,
            path_metadata=metadata,
        )

    assert target_hit is not None
    assert stop_hit is not None
    target_index = int(target_hit["bar_index"])
    stop_index = int(stop_hit["bar_index"])
    metadata.update(_hit_metadata("target", target_hit))
    metadata.update(_hit_metadata("stop", stop_hit))
    if target_index < stop_index:
        return StopTargetOrdering(
            ordering="target_before_stop",
            target_before_stop=True,
            stop_before_target=False,
            path_metadata=metadata,
        )
    if stop_index < target_index:
        return StopTargetOrdering(
            ordering="stop_before_target",
            target_before_stop=False,
            stop_before_target=True,
            path_metadata=metadata,
        )
    metadata["ambiguous_same_bar"] = True
    return StopTargetOrdering(
        ordering="ambiguous_same_bar",
        target_before_stop=False,
        stop_before_target=False,
        path_metadata=metadata,
    )


def _hit_metadata(prefix: str, bar: Mapping[str, Any]) -> dict[str, Any]:
    return {
        f"{prefix}_hit_bar_index": int(bar["bar_index"]),
        f"{prefix}_hit_event_ts": _datetime_to_text(bar["event_ts"]),
    }


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _datetime_to_text(value: Any) -> str:
    if not isinstance(value, datetime):
        value = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
