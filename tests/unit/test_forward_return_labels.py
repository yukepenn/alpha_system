from __future__ import annotations

from datetime import timedelta

import pytest

from alpha_system.labels.generation import generate_forward_return_labels
from alpha_system.labels.validation import validate_label_record
from tests.fixtures.labels.synthetic_bars import regular_bars


def test_forward_return_labels_are_deterministic_for_standard_horizons() -> None:
    bars = regular_bars(32)
    labels = generate_forward_return_labels(bars)
    by_id = {label.label_id: label for label in labels if label.event_ts == bars[0]["event_ts"]}

    expected = {
        "forward_return_1m": 101 / 100 - 1,
        "forward_return_3m": 103 / 100 - 1,
        "forward_return_5m": 105 / 100 - 1,
        "forward_return_10m": 110 / 100 - 1,
        "forward_return_30m": 130 / 100 - 1,
    }
    assert set(by_id) == set(expected)
    for label_id, value in expected.items():
        label = by_id[label_id]
        assert label.value == pytest.approx(value)
        assert label.label_available_ts == bars[int(label.horizon / timedelta(minutes=1))][
            "available_ts"
        ]
        validate_label_record(label)


def test_forward_return_insufficient_future_is_null_and_clamped() -> None:
    labels = generate_forward_return_labels(regular_bars(3), horizons_minutes=(5,))
    first = labels[0]

    assert first.value is None
    assert first.path_metadata["insufficient_future"] is True
    assert first.path_metadata["clamped_to_session_close"] is True
    assert first.path_metadata["observed_future_bars"] == 2
    validate_label_record(first)
