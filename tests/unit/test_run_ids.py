from __future__ import annotations

from datetime import datetime, timezone

import pytest

from alpha_system.core.run_ids import generate_run_id


FIXED_TS = datetime(2026, 6, 2, 1, 20, 7, tzinfo=timezone.utc)


def test_generate_run_id_is_deterministic_with_injected_inputs() -> None:
    first = generate_run_id(
        "Backtest Run",
        timestamp=FIXED_TS,
        seed="seed-1",
        components={"strategy": "s1", "version": "v1"},
    )
    second = generate_run_id(
        "Backtest Run",
        timestamp=FIXED_TS,
        seed="seed-1",
        components={"version": "v1", "strategy": "s1"},
    )

    assert first == second
    assert first.startswith("backtest_run_20260602T012007000000Z_")


def test_generate_run_id_changes_when_seed_changes() -> None:
    first = generate_run_id("run", timestamp=FIXED_TS, seed="seed-1")
    second = generate_run_id("run", timestamp=FIXED_TS, seed="seed-2")

    assert first != second


def test_generate_run_id_uses_injected_clock() -> None:
    run_id = generate_run_id("study", clock=lambda: FIXED_TS, seed="clocked")

    assert run_id.startswith("study_20260602T012007000000Z_")


def test_generate_run_id_rejects_ambiguous_time_inputs() -> None:
    with pytest.raises(ValueError, match="either timestamp or clock"):
        generate_run_id("run", timestamp=FIXED_TS, clock=lambda: FIXED_TS)
