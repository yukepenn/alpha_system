from __future__ import annotations

from datetime import datetime, timezone

from alpha_system.factors.base import build_factor_from_spec
from alpha_system.factors.compute import compute_factor_values
from tests.fixtures.factors.synthetic import DATA_VERSION, factor_spec, make_bars


def test_session_reset_prevents_cross_session_history_leakage() -> None:
    spec = factor_spec(session_reset=True)
    bars = [
        *make_bars(["100", "101"], session_id="S1"),
        *make_bars(
            ["200", "202"],
            session_id="S2",
            start=datetime(2026, 1, 3, 14, 30, tzinfo=timezone.utc),
        ),
    ]

    values = compute_factor_values(
        spec,
        build_factor_from_spec(spec),
        bars,
        data_version=DATA_VERSION,
    )

    assert [value.value for value in values] == [None, 1.0, None, 2.0]


def test_no_session_reset_allows_history_to_continue_across_sessions() -> None:
    spec = factor_spec(session_reset=False)
    bars = [
        *make_bars(["100", "101"], session_id="S1"),
        *make_bars(
            ["200"],
            session_id="S2",
            start=datetime(2026, 1, 3, 14, 30, tzinfo=timezone.utc),
        ),
    ]

    values = compute_factor_values(
        spec,
        build_factor_from_spec(spec),
        bars,
        data_version=DATA_VERSION,
    )

    assert [value.value for value in values] == [None, 1.0, 99.0]
