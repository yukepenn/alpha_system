from __future__ import annotations

import pytest

from alpha_system.experiments.feature_sets import FeatureSetError, LabelSpec, validate_label_availability


def test_label_availability_must_not_be_after_decision_time() -> None:
    label_spec = LabelSpec(label_id="forward_return_1", label_version="label:v1")

    with pytest.raises(FeatureSetError, match="availability"):
        validate_label_availability(
            [
                {
                    "decision_ts": "2026-01-02T10:00:00Z",
                    "label_available_ts": "2026-01-02T10:01:00Z",
                }
            ],
            label_spec,
        )


def test_label_available_at_decision_time_is_accepted() -> None:
    validate_label_availability(
        [
            {
                "decision_ts": "2026-01-02T10:00:00Z",
                "label_available_ts": "2026-01-02T10:00:00Z",
            }
        ],
        LabelSpec(label_id="forward_return_1", label_version="label:v1"),
    )
