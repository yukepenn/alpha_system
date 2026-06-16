"""FIX 2 canaries: the reference fill path can charge real per-contract futures
fees (+ an explicit spread term) via the existing ``costs.py`` models, selectable
from config (back-compatible with ``fixed_bps``). Fails on old code (engine could
only apply flat ``fixed_bps`` and the fee schedule never saw the instrument).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.backtest.engine_config import ReferenceEngineConfig
from alpha_system.backtest.futures_fees import (
    ES_CME_CLEARING_FEE_PER_SIDE,
    ES_CME_EXCHANGE_FEE_PER_SIDE,
    ES_NFA_REGULATORY_FEE_PER_SIDE,
    ES_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE,
)
from alpha_system.backtest.reference import run_reference_backtest


_BASE_TS = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
_SESSION = "GLBX:2026-01-02:eth"
_DATA_VERSION = "data:fee-canary:v1"
_INSTRUMENT = "inst_databento_es"
_ROOTS = {_INSTRUMENT: "ES"}

_ES_FEE_PER_SIDE = (
    ES_CME_EXCHANGE_FEE_PER_SIDE
    + ES_CME_CLEARING_FEE_PER_SIDE
    + ES_NFA_REGULATORY_FEE_PER_SIDE
    + ES_RETAIL_DISCOUNT_BROKER_COMMISSION_PER_SIDE
)


def _bar(index: int, *, open_price: str, close: str, spread: str = "0.5") -> dict[str, object]:
    start = _BASE_TS + timedelta(minutes=index)
    end = _BASE_TS + timedelta(minutes=index + 1)
    op = Decimal(open_price)
    cl = Decimal(close)
    half = Decimal(spread) / 2
    return {
        "instrument_id": _INSTRUMENT,
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
        "bid": str(op - half),
        "ask": str(op + half),
        "spread": str(spread),
        "source_version": "synthetic",
        "data_version": _DATA_VERSION,
        "quality_flags": "synthetic|deterministic correctness_only",
    }


def _signal(index: int, signal_type: str) -> dict[str, object]:
    event = _BASE_TS + timedelta(minutes=index + 1)
    return {
        "signal_id": f"{signal_type}-{index}",
        "instrument_id": _INSTRUMENT,
        "event_ts": event.isoformat().replace("+00:00", "Z"),
        "available_ts": event.isoformat().replace("+00:00", "Z"),
        "session_id": _SESSION,
        "bar_index": index,
        "signal_type": signal_type,
        "direction": "long",
        "score": None,
        "confidence": None,
        "desired_exposure": None,
        "strategy_id": "fee_canary",
        "strategy_version": "v1",
        "factor_versions": {"f": "v1"},
        "quality_flags": ["synthetic"],
        "data_version": _DATA_VERSION,
    }


def _run(cost_model_payload: dict[str, object], *, spread: str = "0.5"):
    bars = [
        _bar(0, open_price="5000", close="5000", spread=spread),
        _bar(1, open_price="5000", close="5000", spread=spread),
        _bar(2, open_price="5010", close="5010", spread=spread),
        _bar(3, open_price="5010", close="5010", spread=spread),
    ]
    signals = [_signal(0, "entry"), _signal(2, "exit")]
    config = ReferenceEngineConfig.from_mapping({"cost_model": cost_model_payload})
    return run_reference_backtest(
        bars=bars,
        signals=signals,
        config=config,
        instrument_roots=_ROOTS,
        run_id="fee-canary",
    )


def test_futures_fee_schedule_charges_per_contract_fee_not_flat_bps() -> None:
    result = _run(
        {
            "model": "composite",
            "components": [{"model": "futures_fee_schedule", "default_symbol": "ES"}],
        }
    )
    assert result.summary.total_trades == 1
    trade = result.trades[0]
    # 1 contract, entry + exit = 2 sides -> 2 x ES all-in per-side fee.
    expected = _ES_FEE_PER_SIDE * Decimal("2")
    assert trade.costs == expected
    # ES per-side fee is 1.99 (1.38 + 0.00 + 0.02 + 0.59).
    assert _ES_FEE_PER_SIDE == Decimal("1.99")
    assert trade.costs == Decimal("3.98")


def test_composite_adds_spread_term_on_top_of_fee() -> None:
    spread = "0.5"
    result = _run(
        {
            "model": "composite",
            "components": [
                {"model": "futures_fee_schedule", "default_symbol": "ES"},
                {"model": "spread_cost", "assumption": "half_spread"},
            ],
        },
        spread=spread,
    )
    trade = result.trades[0]
    # spread cost per side = half_spread * spread * qty(1) * multiplier(50)
    # = 0.5 * 0.5 * 1 * 50 = 12.5 per side, x2 sides = 25.0
    spread_cost_two_sides = Decimal("0.5") * Decimal(spread) * Decimal("1") * Decimal("50") * Decimal("2")
    fee_two_sides = _ES_FEE_PER_SIDE * Decimal("2")
    assert trade.costs == fee_two_sides + spread_cost_two_sides
    # And strictly greater than a fee-only run (spread makes it stricter, not looser).
    fee_only = _run(
        {"model": "composite", "components": [{"model": "futures_fee_schedule", "default_symbol": "ES"}]},
        spread=spread,
    )
    assert trade.costs > fee_only.trades[0].costs


def test_fixed_bps_still_supported_back_compat() -> None:
    result = _run({"model": "fixed_bps", "fixed_bps": "1.0"})
    trade = result.trades[0]
    # fixed_bps cost is on dollar notional (price * qty * multiplier 50), per side.
    # entry notional ~ 5000.25 * 1 * 50, exit ~ 5009.75 * 1 * 50; 1 bps = /10000.
    assert trade.costs > 0
    # Distinct from the per-contract fee number (proves selection works).
    assert trade.costs != Decimal("3.98")
