from __future__ import annotations

import pytest

from alpha_system.labels.alignment import (
    ALIGNMENT_KEY_FIELDS,
    LabelAlignmentError,
    assert_research_join_purpose,
    reject_labels_as_factor_inputs,
    research_label_join_index,
)
from alpha_system.labels.generation import generate_forward_return_labels
from tests.fixtures.labels.synthetic_bars import regular_bars


def test_labels_are_rejected_as_live_factor_inputs() -> None:
    label = generate_forward_return_labels(regular_bars(4), horizons_minutes=(1,))[0]

    with pytest.raises(LabelAlignmentError, match="factor inputs"):
        reject_labels_as_factor_inputs([label])
    with pytest.raises(LabelAlignmentError, match="factor inputs"):
        reject_labels_as_factor_inputs([{"name": "future_label", "domain": "label"}])


def test_research_join_requires_alignment_keys_and_rejects_live_purpose() -> None:
    label = generate_forward_return_labels(regular_bars(4), horizons_minutes=(1,))[0]

    assert ALIGNMENT_KEY_FIELDS == (
        "instrument_id",
        "event_ts",
        "session_id",
        "horizon",
        "data_version",
        "label_version",
    )
    assert research_label_join_index([label])
    assert_research_join_purpose("research")
    with pytest.raises(LabelAlignmentError, match="cannot be live inputs"):
        assert_research_join_purpose("live_factor_input")
