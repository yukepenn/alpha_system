from __future__ import annotations

import pytest

from alpha_system.labels.generation import generate_future_spread_liquidity_labels
from alpha_system.labels.validation import validate_label_record
from tests.fixtures.labels.synthetic_bars import make_bars


def test_future_spread_liquidity_uses_future_path_metrics() -> None:
    bars = make_bars(
        [100, 101, 102, 103],
        spreads=["0.10", "0.20", "0.30", "0.40"],
        volumes=[1000, 1100, 1200, 1300],
    )
    labels = generate_future_spread_liquidity_labels(bars, horizons_minutes=(3,))
    first = next(label for label in labels if label.event_ts == bars[0]["event_ts"])

    assert first.value == pytest.approx(0.30)
    assert first.path_metadata["average_spread"] == "0.30"
    assert first.path_metadata["total_volume"] == "3600"
    assert first.path_metadata["average_trade_count"] == 12
    validate_label_record(first)


def test_future_spread_liquidity_is_null_for_incomplete_future() -> None:
    labels = generate_future_spread_liquidity_labels(make_bars([100, 101]), horizons_minutes=(3,))

    assert labels[0].value is None
    assert labels[0].path_metadata["insufficient_future"] is True
