from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any


def make_bars(
    closes: list[str | int | float | Decimal],
    *,
    highs: list[str | int | float | Decimal] | None = None,
    lows: list[str | int | float | Decimal] | None = None,
    spreads: list[str | int | float | Decimal] | None = None,
    volumes: list[str | int | float | Decimal] | None = None,
    session_id: str = "XNYS:2026-01-02:regular",
    instrument_id: str = "SYNTH_LABEL",
    data_version: str = "data:synthetic-labels:v1",
    quality_flags: tuple[str, ...] = ("synthetic", "correctness_only"),
    start: datetime = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc),
) -> list[dict[str, Any]]:
    bars: list[dict[str, Any]] = []
    close_values = [_decimal(value) for value in closes]
    high_values = _series_or_default(highs, close_values, Decimal("0.50"), add=True)
    low_values = _series_or_default(lows, close_values, Decimal("0.50"), add=False)
    spread_values = _series_or_default(spreads, close_values, Decimal("0.20"), spread=True)
    volume_values = [_decimal(value) for value in volumes] if volumes is not None else [
        Decimal("1000") + Decimal(index * 10) for index in range(len(close_values))
    ]

    for index, close in enumerate(close_values):
        bar_start = start + timedelta(minutes=index)
        bar_end = bar_start + timedelta(minutes=1)
        spread = spread_values[index]
        bars.append(
            {
                "instrument_id": instrument_id,
                "session_id": session_id,
                "bar_index": index,
                "bar_start_ts": bar_start,
                "bar_end_ts": bar_end,
                "event_ts": bar_end,
                "available_ts": bar_end + timedelta(seconds=5),
                "open": close_values[index - 1] if index else close,
                "high": high_values[index],
                "low": low_values[index],
                "close": close,
                "volume": volume_values[index],
                "vwap": close,
                "trade_count": 10 + index,
                "bid": close - (spread / Decimal("2")),
                "ask": close + (spread / Decimal("2")),
                "spread": spread,
                "source_version": "src:synthetic-labels:v1",
                "data_version": data_version,
                "quality_flags": quality_flags,
            }
        )
    return bars


def regular_bars(count: int = 32) -> list[dict[str, Any]]:
    return make_bars([Decimal("100") + Decimal(index) for index in range(count)])


def _series_or_default(
    values: list[str | int | float | Decimal] | None,
    closes: list[Decimal],
    offset: Decimal,
    *,
    add: bool = True,
    spread: bool = False,
) -> list[Decimal]:
    if values is not None:
        return [_decimal(value) for value in values]
    if spread:
        return [offset for _ in closes]
    if add:
        return [close + offset for close in closes]
    return [close - offset for close in closes]


def _decimal(value: str | int | float | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
