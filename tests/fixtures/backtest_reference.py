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

# The synthetic ``SYNTH`` correctness instrument is intentionally absent from the
# futures instrument master; the reference engine's fail-loud multiplier
# resolution needs an explicit unit multiplier for fixture-based backtests.
SYNTH_INSTRUMENT_MULTIPLIERS = {INSTRUMENT_ID: Decimal("1")}


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


def multi_session_bars(
    *,
    sessions: int = 3,
    bars_per_session: int = 4,
    available_delay_seconds: int = 0,
) -> list[dict[str, object]]:
    """Deterministic multi-session bars spanning consecutive trading days.

    Each session gets its own ``session_id`` and its own ``bar_index`` range
    starting at 0, mirroring how real per-RTH-session bars are emitted. Used to
    exercise the multi-session ``eod_flat`` path directly in one backtest call.
    """

    rows: list[dict[str, object]] = []
    for session in range(sessions):
        session_day = BASE_TS + timedelta(days=session)
        session_id = f"XNYS:{session_day.date().isoformat()}:regular"
        for index in range(bars_per_session):
            price = 100 + session * 10 + index
            start = session_day + timedelta(minutes=index)
            end = session_day + timedelta(minutes=index + 1)
            open_decimal = Decimal(str(price))
            rows.append(
                {
                    "instrument_id": INSTRUMENT_ID,
                    "session_id": session_id,
                    "bar_index": index,
                    "bar_start_ts": _text(start),
                    "bar_end_ts": _text(end),
                    "event_ts": _text(end),
                    "available_ts": _text(end + timedelta(seconds=available_delay_seconds)),
                    "open": str(open_decimal),
                    "high": str(open_decimal + Decimal("1")),
                    "low": str(open_decimal - Decimal("1")),
                    "close": str(open_decimal),
                    "volume": "1000",
                    "vwap": str(open_decimal),
                    "trade_count": 10,
                    "bid": str(open_decimal - Decimal("0.01")),
                    "ask": str(open_decimal + Decimal("0.01")),
                    "spread": "0.02",
                    "source_version": "synthetic",
                    "data_version": DATA_VERSION,
                    "quality_flags": "synthetic|deterministic correctness_only",
                }
            )
    return rows


def multi_session_signal(
    session: int,
    bar_index: int,
    signal_type: str,
    *,
    signal_id: str | None = None,
    direction: str = "long",
    available_delay_seconds: int = 0,
) -> dict[str, object]:
    """Signal aligned to ``multi_session_bars`` (session-local ``bar_index``)."""

    session_day = BASE_TS + timedelta(days=session)
    session_id = f"XNYS:{session_day.date().isoformat()}:regular"
    event = session_day + timedelta(minutes=bar_index + 1)
    return {
        "signal_id": signal_id or f"{signal_type}-{session}-{bar_index}",
        "instrument_id": INSTRUMENT_ID,
        "event_ts": _text(event),
        "available_ts": _text(event + timedelta(seconds=available_delay_seconds)),
        "session_id": session_id,
        "bar_index": bar_index,
        "signal_type": signal_type,
        "direction": direction,
        "score": None,
        "confidence": None,
        "desired_exposure": None,
        "strategy_id": "fixture_strategy",
        "strategy_version": "v1",
        "factor_versions": FACTOR_VERSIONS,
        "quality_flags": ["synthetic"],
        "data_version": DATA_VERSION,
    }


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
