from __future__ import annotations

from datetime import timedelta

import pytest

from alpha_system.labels.generation import generate_forward_return_labels
from alpha_system.labels.spec import LabelSpec
from alpha_system.labels.validation import (
    LabelValidationError,
    assert_label_not_available_before,
    validate_label_record,
    validate_no_lookahead,
)
from tests.fixtures.labels.synthetic_bars import regular_bars


def test_label_available_ts_is_after_horizon_completion() -> None:
    labels = generate_forward_return_labels(regular_bars(6), horizons_minutes=(3,))
    first = labels[0]

    assert first.label_available_ts >= first.event_ts + first.horizon
    assert first.label_available_ts == regular_bars(6)[3]["available_ts"]
    validate_no_lookahead(labels)


def test_label_cannot_be_read_before_available_ts() -> None:
    label = generate_forward_return_labels(regular_bars(6), horizons_minutes=(3,))[0]

    with pytest.raises(LabelValidationError, match="not available"):
        assert_label_not_available_before(
            label,
            as_of_ts=label.label_available_ts - timedelta(seconds=1),
        )
    assert_label_not_available_before(label, as_of_ts=label.label_available_ts)


def test_forged_early_available_ts_is_rejected() -> None:
    label = generate_forward_return_labels(regular_bars(6), horizons_minutes=(3,))[0]
    payload = label.to_dict()
    payload["label_available_ts"] = "2026-01-02T14:32:05Z"
    forged = LabelSpec.from_mapping(payload)

    with pytest.raises(LabelValidationError, match="horizon_end_ts"):
        validate_label_record(forged)
