"""Tiny deterministic fixtures for fast/reference parity checks.

These fixtures are correctness fixtures only. They are synthetic, in-memory,
and are not market evidence.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from alpha_system.backtest.engine_config import CostModelConfig, ReferenceEngineConfig


BASE_TS = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
SESSION_ID = "XNYS:2026-01-02:regular"
INSTRUMENT_ID = "SYNTH"
DATA_VERSION = "data:fast-path-parity:v1"
FACTOR_VERSIONS = {"fixture_factor": "v1"}
STRATEGY_ID = "fast_path_fixture_strategy"
STRATEGY_VERSION = "v1"


def fixture_zero_cost_config(**overrides: Any) -> ReferenceEngineConfig:
    """Return explicit zero-cost reference config for tiny parity fixtures."""

    payload = {
        "cost_model": CostModelConfig(
            fixed_bps=Decimal("0"),
            minimum_cost=Decimal("0"),
            description="explicit synthetic fixture zero cost",
        )
    }
    payload.update(overrides)
    return ReferenceEngineConfig(**payload)


def fixture_cost_config(*, fixed_bps: str = "100", **overrides: Any) -> ReferenceEngineConfig:
    """Return a deterministic non-zero cost config for cost parity."""

    payload = {
        "cost_model": CostModelConfig(
            fixed_bps=Decimal(fixed_bps),
            minimum_cost=Decimal("0"),
            description="synthetic fixed bps parity cost",
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
    """Return one deterministic 1-minute OHLCV bar mapping."""

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
        "bar_start_ts": _datetime_text(start),
        "bar_end_ts": _datetime_text(end),
        "event_ts": _datetime_text(end),
        "available_ts": _datetime_text(end + timedelta(seconds=available_delay_seconds)),
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
        "quality_flags": "synthetic|fast_path_parity|correctness_only",
    }


def synthetic_bars(count: int = 4, *, start_price: int = 100) -> tuple[dict[str, object], ...]:
    """Return a deterministic increasing synthetic bar sequence."""

    return tuple(
        synthetic_bar(index, open_price=str(start_price + index), close=str(start_price + index))
        for index in range(count)
    )


def falling_bars(count: int = 4, *, start_price: int = 100) -> tuple[dict[str, object], ...]:
    """Return a deterministic decreasing synthetic bar sequence."""

    return tuple(
        synthetic_bar(index, open_price=str(start_price - index), close=str(start_price - index))
        for index in range(count)
    )


def signal_record(
    index: int,
    signal_type: str,
    *,
    signal_id: str | None = None,
    direction: str = "long",
    available_delay_seconds: int = 0,
    data_version: str = DATA_VERSION,
) -> dict[str, object]:
    """Return a deterministic signal mapping accepted by the reference engine."""

    event = BASE_TS + timedelta(minutes=index + 1)
    return {
        "signal_id": signal_id or f"{signal_type}-{direction}-{index}",
        "instrument_id": INSTRUMENT_ID,
        "event_ts": _datetime_text(event),
        "available_ts": _datetime_text(event + timedelta(seconds=available_delay_seconds)),
        "session_id": SESSION_ID,
        "bar_index": index,
        "signal_type": signal_type,
        "direction": direction,
        "score": None,
        "confidence": None,
        "desired_exposure": None,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "factor_versions": FACTOR_VERSIONS,
        "quality_flags": ["synthetic", "fast_path_parity", "correctness_only"],
        "data_version": data_version,
    }


def entry_exit_signals(
    *,
    direction: str = "long",
    entry_index: int = 0,
    exit_index: int = 2,
) -> tuple[dict[str, object], ...]:
    """Return one entry and one exit signal under next-bar semantics."""

    return (
        signal_record(entry_index, "entry", signal_id=f"{direction}-entry", direction=direction),
        signal_record(exit_index, "exit", signal_id=f"{direction}-exit", direction=direction),
    )


def no_trade_signals() -> tuple[dict[str, object], ...]:
    """Return a hold-only signal set so reference validation has one signal."""

    return (signal_record(0, "hold", signal_id="hold-no-trade", direction="long"),)


def _datetime_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
