"""FIX 1 canaries: reference PnL/equity are in DOLLARS via the contract multiplier.

These tests fail on the old code (PnL in price points, silent x1) and pass on the
new code (PnL = points x instrument multiplier, resolved per-instrument from the
futures instrument master, fail-loud on unknown).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from alpha_system.backtest.accounting import realized_pnl_for
from alpha_system.backtest.instrument_economics import (
    InstrumentMultiplierError,
    resolve_instrument_multipliers,
)
from alpha_system.backtest.reference import run_reference_backtest
from alpha_system.core.enums import Direction
from alpha_system.data.foundation.instruments import load_futures_instrument_master_by_root


_BASE_TS = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
_SESSION = "GLBX:2026-01-02:eth"
_DATA_VERSION = "data:multiplier-canary:v1"


def _bar(index: int, *, instrument_id: str, open_price: str, close: str) -> dict[str, object]:
    start = _BASE_TS + timedelta(minutes=index)
    end = _BASE_TS + timedelta(minutes=index + 1)
    op = Decimal(open_price)
    cl = Decimal(close)
    return {
        "instrument_id": instrument_id,
        "session_id": _SESSION,
        "bar_index": index,
        "bar_start_ts": start.isoformat().replace("+00:00", "Z"),
        "bar_end_ts": end.isoformat().replace("+00:00", "Z"),
        "event_ts": end.isoformat().replace("+00:00", "Z"),
        "available_ts": end.isoformat().replace("+00:00", "Z"),
        "open": str(op),
        "high": str(max(op, cl) + Decimal("1")),
        "low": str(min(op, cl) - Decimal("1")),
        "close": str(cl),
        "volume": "1000",
        "vwap": str(cl),
        "trade_count": 10,
        "bid": str(op - Decimal("0.25")),
        "ask": str(op + Decimal("0.25")),
        "spread": "0.5",
        "source_version": "synthetic",
        "data_version": _DATA_VERSION,
        "quality_flags": "synthetic|deterministic correctness_only",
    }


def _signal(index: int, signal_type: str, *, instrument_id: str) -> dict[str, object]:
    event = _BASE_TS + timedelta(minutes=index + 1)
    return {
        "signal_id": f"{instrument_id}-{signal_type}-{index}",
        "instrument_id": instrument_id,
        "event_ts": event.isoformat().replace("+00:00", "Z"),
        "available_ts": event.isoformat().replace("+00:00", "Z"),
        "session_id": _SESSION,
        "bar_index": index,
        "signal_type": signal_type,
        "direction": "long",
        "score": None,
        "confidence": None,
        "desired_exposure": None,
        "strategy_id": "multiplier_canary",
        "strategy_version": "v1",
        "factor_versions": {"f": "v1"},
        "quality_flags": ["synthetic"],
        "data_version": _DATA_VERSION,
    }


def _buy_and_hold(instrument_id: str, *, entry_open: str, exit_close: str, roots, multipliers=None):
    """Enter long at bar 0 (filled bar 1) and exit at the last bar."""
    bars = [
        _bar(0, instrument_id=instrument_id, open_price=entry_open, close=entry_open),
        _bar(1, instrument_id=instrument_id, open_price=entry_open, close=entry_open),
        _bar(2, instrument_id=instrument_id, open_price=exit_close, close=exit_close),
        _bar(3, instrument_id=instrument_id, open_price=exit_close, close=exit_close),
    ]
    signals = [
        _signal(0, "entry", instrument_id=instrument_id),
        _signal(2, "exit", instrument_id=instrument_id),
    ]
    return run_reference_backtest(
        bars=bars,
        signals=signals,
        instrument_roots=roots,
        instrument_multipliers=multipliers,
        run_id=f"mult-canary-{instrument_id}",
    )


def test_realized_pnl_applies_multiplier_in_dollars() -> None:
    points = realized_pnl_for(
        direction=Direction.LONG,
        entry_price=Decimal("100"),
        exit_price=Decimal("110"),
        quantity=Decimal("1"),
    )
    assert points == Decimal("10")  # default multiplier 1 = price points (back-compat)
    dollars = realized_pnl_for(
        direction=Direction.LONG,
        entry_price=Decimal("100"),
        exit_price=Decimal("110"),
        quantity=Decimal("1"),
        multiplier=Decimal("50"),
    )
    assert dollars == Decimal("500")  # 10 points x ES multiplier 50


def test_buy_and_hold_es_pnl_is_points_times_fifty() -> None:
    # ES entry ask = open + 0.25, exit bid = close - 0.25; engine fills are conservative.
    # Use the master ES multiplier (50) resolved via instrument_roots.
    result = _buy_and_hold(
        "inst_databento_es",
        entry_open="5000",
        exit_close="5040",
        roots={"inst_databento_es": "ES"},
    )
    assert result.summary.total_trades == 1
    trade = result.trades[0]
    # gross dollar PnL == (exit_price - entry_price) * qty * 50, and == points * 50.
    points = (trade.exit_price - trade.entry_price) * trade.quantity
    assert trade.gross_pnl == points * Decimal("50")
    # OLD CODE regression: gross_pnl would equal `points` (no multiplier).
    assert trade.gross_pnl != points


def test_buy_and_hold_nq_uses_per_instrument_multiplier_not_hardcoded() -> None:
    result = _buy_and_hold(
        "inst_databento_nq",
        entry_open="18000",
        exit_close="18050",
        roots={"inst_databento_nq": "NQ"},
    )
    trade = result.trades[0]
    points = (trade.exit_price - trade.entry_price) * trade.quantity
    # NQ multiplier is 20 (not ES's 50) -> proves per-instrument resolution.
    assert trade.gross_pnl == points * Decimal("20")
    assert trade.gross_pnl != points * Decimal("50")


def test_unknown_instrument_fails_loud_no_silent_x1() -> None:
    with pytest.raises(InstrumentMultiplierError, match="refusing to default to 1"):
        _buy_and_hold("inst_unknown_thing", entry_open="100", exit_close="110", roots=None)


def test_resolver_reads_multiplier_from_master() -> None:
    master = load_futures_instrument_master_by_root()
    resolved = resolve_instrument_multipliers(
        ["inst_databento_es", "inst_databento_nq", "inst_databento_rty"],
        roots={
            "inst_databento_es": "ES",
            "inst_databento_nq": "NQ",
            "inst_databento_rty": "RTY",
        },
    )
    assert resolved["inst_databento_es"] == master["ES"].multiplier == Decimal("50")
    assert resolved["inst_databento_nq"] == master["NQ"].multiplier == Decimal("20")
    assert resolved["inst_databento_rty"] == master["RTY"].multiplier == Decimal("50")


def test_explicit_override_beats_master_and_is_per_instrument() -> None:
    resolved = resolve_instrument_multipliers(
        ["SYNTH", "inst_databento_es"],
        multipliers={"SYNTH": Decimal("1")},
        roots={"inst_databento_es": "ES"},
    )
    assert resolved["SYNTH"] == Decimal("1")
    assert resolved["inst_databento_es"] == Decimal("50")
