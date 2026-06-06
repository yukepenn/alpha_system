from __future__ import annotations

from decimal import Decimal

import pytest

from alpha_system.runtime.probe import (
    DirectionPolicy,
    FillPolicy,
    FillTiming,
    SignalProbeContractError,
    SignalProbeFillError,
    build_next_bar_position_series,
)


def test_signal_probe_entry_and_exit_use_next_eligible_bar() -> None:
    series = build_next_bar_position_series(
        _rows(),
        threshold=Decimal("0.5"),
        direction_policy=DirectionPolicy.LONG_SHORT_FLAT,
        fill_policy=FillPolicy(),
    )

    assert series.positions[0] == 0
    assert series.positions[1] == 1
    assert series.origin_signal_indices[1] == 0
    assert series.positions[2] == -1
    assert series.origin_signal_indices[2] == 1
    assert series.positions[3] == 0
    assert series.origin_signal_indices[3] == 2
    assert all(fill.fill_index > fill.origin_signal_index for fill in series.fills)
    assert series.to_summary()["same_bar_fill_count"] == 0


def test_signal_probe_rejects_same_bar_fill_policy() -> None:
    with pytest.raises(SignalProbeContractError, match="same-bar"):
        FillPolicy(timing=FillTiming.EXPLICIT_DELAY, delay_bars=0)


def test_signal_available_ts_must_not_be_later_than_fill_bar_event_ts() -> None:
    rows = list(_rows())
    rows[0] = {
        **rows[0],
        "available_ts": "2026-01-02T14:32:30+00:00",
    }

    with pytest.raises(SignalProbeFillError, match="available_ts"):
        build_next_bar_position_series(
            rows,
            threshold=Decimal("0.5"),
            direction_policy=DirectionPolicy.LONG_SHORT_FLAT,
            fill_policy=FillPolicy(),
        )


def _rows() -> tuple[dict[str, object], ...]:
    return (
        _row(0, "0.7", "0.0"),
        _row(1, "-0.7", "0.1"),
        _row(2, "0.0", "-0.1"),
        _row(3, "0.7", "0.0"),
    )


def _row(index: int, feature: str, label: str) -> dict[str, object]:
    minute = 30 + index
    return {
        "event_ts": f"2026-01-02T14:{minute:02d}:00+00:00",
        "available_ts": f"2026-01-02T14:{minute:02d}:05+00:00",
        "label_available_ts": f"2026-01-02T14:{minute + 5:02d}:00+00:00",
        "feature_value": feature,
        "label_value": label,
        "price": "1",
    }
