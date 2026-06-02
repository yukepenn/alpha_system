"""Tiny synthetic correctness fixtures for reference backtest tests.

These fixtures are deterministic schema fixtures only. They are not market
evidence and are not generated from real market data.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from alpha_system.backtest.engine_config import CostModelConfig, ReferenceEngineConfig


BASE_TS = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
SESSION_ID = "XNYS:2026-01-02:regular"
INSTRUMENT_ID = "SYNTH"
DATA_VERSION = "data:v1"
FACTOR_VERSIONS = {"fixture_factor": "v1"}


def zero_cost_config(**overrides: Any) -> ReferenceEngineConfig:
    payload = {
        "cost_model": CostModelConfig(
            fixed_bps=Decimal("0"),
            minimum_cost=Decimal("0"),
            description="explicit synthetic fixture zero cost",
        )
    }
    payload.update(overrides)
    return ReferenceEngineConfig(**payload)


def synthetic_bar(
    index: int,
    *,
    open_price: str = "100",
    high: str | None = None,
    low: str | None = None,
    close: str | None = None,
    available_delay_seconds: int = 0,
    data_version: str = DATA_VERSION,
) -> dict[str, object]:
    open_decimal = Decimal(open_price)
    high_decimal = Decimal(high) if high is not None else open_decimal + Decimal("1")
    low_decimal = Decimal(low) if low is not None else open_decimal - Decimal("1")
    close_decimal = Decimal(close) if close is not None else open_decimal
    start = BASE_TS + timedelta(minutes=index)
    end = BASE_TS + timedelta(minutes=index + 1)
    bid = open_decimal - Decimal("0.01")
    ask = open_decimal + Decimal("0.01")
    return {
        "instrument_id": INSTRUMENT_ID,
        "session_id": SESSION_ID,
        "bar_index": index,
        "bar_start_ts": _text(start),
        "bar_end_ts": _text(end),
        "event_ts": _text(end),
        "available_ts": _text(end + timedelta(seconds=available_delay_seconds)),
        "open": str(open_decimal),
        "high": str(high_decimal),
        "low": str(low_decimal),
        "close": str(close_decimal),
        "volume": "1000",
        "vwap": str(close_decimal),
        "trade_count": 10,
        "bid": str(bid),
        "ask": str(ask),
        "spread": "0.02",
        "source_version": "synthetic",
        "data_version": data_version,
        "quality_flags": "synthetic|deterministic correctness_only",
    }


def synthetic_bars(count: int = 4, *, available_delay_seconds: int = 0) -> list[dict[str, object]]:
    return [
        synthetic_bar(
            index,
            open_price=str(100 + index),
            close=str(100 + index),
            available_delay_seconds=available_delay_seconds,
        )
        for index in range(count)
    ]


def signal_record(
    index: int,
    signal_type: str,
    *,
    signal_id: str | None = None,
    direction: str = "long",
    available_delay_seconds: int = 0,
    data_version: str = DATA_VERSION,
) -> dict[str, object]:
    event = BASE_TS + timedelta(minutes=index + 1)
    return {
        "signal_id": signal_id or f"{signal_type}-{index}",
        "instrument_id": INSTRUMENT_ID,
        "event_ts": _text(event),
        "available_ts": _text(event + timedelta(seconds=available_delay_seconds)),
        "session_id": SESSION_ID,
        "bar_index": index,
        "signal_type": signal_type,
        "direction": direction,
        "score": None,
        "confidence": None,
        "desired_exposure": None,
        "strategy_id": "fixture_strategy",
        "strategy_version": "v1",
        "factor_versions": FACTOR_VERSIONS,
        "quality_flags": ["synthetic"],
        "data_version": data_version,
    }


def write_bars_csv(path: Path, rows: list[dict[str, object]]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_signals_jsonl(path: Path, rows: list[dict[str, object]]) -> Path:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def _text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
