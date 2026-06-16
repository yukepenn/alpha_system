"""Regression guard for the O(N) ``eod_flat`` last-session-bar precompute.

Two properties are asserted:

1. **Semantics unchanged.** The O(1) ``_is_last_session_bar`` lookup against the
   precomputed ``_last_bar_index_by_session`` map must agree bar-for-bar with the
   original O(N) rescan implementation on a multi-session fixture, and a direct
   multi-session ``run_reference_backtest`` must flatten every session at its own
   last bar.
2. **Performance.** A full-year-scale synthetic run (250 sessions x ~390 bars)
   must complete quickly. Under the old O(N^2) rescan this would scan the whole
   ~98k-bar list once per bar (~1e10 comparisons) and effectively hang.

These fixtures are deterministic schema fixtures only; they are not market
evidence.
"""

from __future__ import annotations

import time
from dataclasses import asdict
from typing import Any, Mapping

from alpha_system.backtest.reference import (
    _is_last_session_bar,
    _last_bar_index_by_session,
    _normalize_bars,
    _sort_bars,
    run_reference_backtest,
)
from tests.fixtures.backtest_reference import (
    SYNTH_INSTRUMENT_MULTIPLIERS,
    multi_session_bars,
    multi_session_signal,
    zero_cost_config,
)


def _old_is_last_session_bar(
    bar: Mapping[str, Any], bars: tuple[Mapping[str, Any], ...]
) -> bool:
    """Original O(N) rescan, preserved here as the semantic oracle."""

    for candidate in bars:
        if str(candidate["instrument_id"]) != str(bar["instrument_id"]):
            continue
        if str(candidate["session_id"]) != str(bar["session_id"]):
            continue
        if int(candidate["bar_index"]) > int(bar["bar_index"]):
            return False
    return True


def test_precompute_matches_legacy_rescan_bar_for_bar() -> None:
    sorted_bars = _sort_bars(_normalize_bars(multi_session_bars(sessions=4, bars_per_session=5)))
    last_index = _last_bar_index_by_session(sorted_bars)

    for bar in sorted_bars:
        assert _is_last_session_bar(bar, last_index) == _old_is_last_session_bar(
            bar, sorted_bars
        )


def test_eod_flat_flattens_every_session_at_its_last_bar() -> None:
    sessions = 4
    bars_per_session = 5
    bars = multi_session_bars(sessions=sessions, bars_per_session=bars_per_session)
    signals = [
        multi_session_signal(session, 0, "entry", signal_id=f"entry-{session}")
        for session in range(sessions)
    ]

    result = run_reference_backtest(
        bars=bars,
        signals=signals,
        config=zero_cost_config(eod_flat=True),
        run_id="eod-flat-multi",
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
    )

    # One eod_flat-closed trade per session, each exiting on that session's last bar.
    assert len(result.trades) == sessions
    assert result.summary.open_positions == 0
    for trade in result.trades:
        assert trade.exit_reason == "eod_flat"
        assert trade.exit_signal_id is None
        assert trade.exit_bar_index == bars_per_session - 1


def test_multi_session_run_completes_at_full_year_scale_quickly() -> None:
    # 250 sessions x 390 bars ~= 97.5k bars: a full RTH trading year. Under the
    # old per-bar rescan this is ~9.5e9 candidate comparisons and would hang.
    sessions = 250
    bars_per_session = 390
    bars = multi_session_bars(sessions=sessions, bars_per_session=bars_per_session)
    assert len(bars) == sessions * bars_per_session

    signals = [
        multi_session_signal(session, 0, "entry", signal_id=f"entry-{session}")
        for session in range(sessions)
    ]

    start = time.perf_counter()
    result = run_reference_backtest(
        bars=bars,
        signals=signals,
        config=zero_cost_config(eod_flat=True),
        run_id="eod-flat-year",
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
    )
    elapsed = time.perf_counter() - start

    assert result.summary.open_positions == 0
    assert len(result.trades) == sessions
    # Generous ceiling: O(N) run is well under a second; O(N^2) would not finish.
    assert elapsed < 30.0, f"full-year eod_flat run too slow: {elapsed:.2f}s"


def test_eod_flat_trades_identical_for_subset_and_full_run() -> None:
    """A full multi-session run yields the same per-session trades as running
    each session independently (eod_flat makes sessions independent), proving the
    precompute did not change cross-session behaviour."""

    sessions = 3
    bars_per_session = 6

    def trades_payload(result: Any) -> list[dict[str, Any]]:
        payload = []
        for trade in result.trades:
            row = asdict(trade)
            # run_id / trade_id / order_ids embed the run_id; they are run-scoped
            # identifiers, not behaviour. Strip them and compare the rest exactly.
            for run_scoped in ("run_id", "trade_id", "entry_order_id", "exit_order_id"):
                row.pop(run_scoped, None)
            payload.append(row)
        return payload

    full = run_reference_backtest(
        bars=multi_session_bars(sessions=sessions, bars_per_session=bars_per_session),
        signals=[
            multi_session_signal(s, 0, "entry", signal_id=f"entry-{s}")
            for s in range(sessions)
        ],
        config=zero_cost_config(eod_flat=True),
        run_id="full",
        instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
    )

    all_bars = multi_session_bars(sessions=sessions, bars_per_session=bars_per_session)
    session_ids = [
        all_bars[session * bars_per_session]["session_id"] for session in range(sessions)
    ]

    per_session_trades: list[dict[str, Any]] = []
    for session, session_id in enumerate(session_ids):
        single = run_reference_backtest(
            bars=[bar for bar in all_bars if bar["session_id"] == session_id],
            signals=[multi_session_signal(session, 0, "entry", signal_id=f"entry-{session}")],
            config=zero_cost_config(eod_flat=True),
            run_id=f"single-{session}",
            instrument_multipliers=SYNTH_INSTRUMENT_MULTIPLIERS,
        )
        per_session_trades.extend(trades_payload(single))

    assert trades_payload(full) == per_session_trades
