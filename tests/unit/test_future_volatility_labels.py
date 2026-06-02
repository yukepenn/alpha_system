from __future__ import annotations

from math import sqrt

import pytest

from alpha_system.labels.generation import generate_future_realized_volatility_labels
from alpha_system.labels.validation import validate_label_record
from tests.fixtures.labels.synthetic_bars import make_bars


def test_future_realized_volatility_uses_future_returns_only() -> None:
    bars = make_bars([100, 102, 101, 105])
    labels = generate_future_realized_volatility_labels(bars, horizons_minutes=(3,))
    first = next(label for label in labels if label.event_ts == bars[0]["event_ts"])

    returns = [102 / 100 - 1, 101 / 102 - 1, 105 / 101 - 1]
    mean = sum(returns) / len(returns)
    expected = sqrt(sum((item - mean) ** 2 for item in returns) / len(returns))

    assert first.value == pytest.approx(expected)
    assert first.path_metadata["return_count"] == 3
    validate_label_record(first)


def test_future_realized_volatility_is_null_when_horizon_is_incomplete() -> None:
    bars = make_bars([100, 102])
    labels = generate_future_realized_volatility_labels(bars, horizons_minutes=(3,))

    assert labels[0].value is None
    assert labels[0].path_metadata["insufficient_future"] is True
