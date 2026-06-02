from __future__ import annotations

import pytest

from alpha_system.core.enums import LabelType
from alpha_system.labels.generation import generate_mfe_mae_labels
from alpha_system.labels.validation import validate_label_record
from tests.fixtures.labels.synthetic_bars import make_bars


def test_mfe_and_mae_labels_include_path_metadata() -> None:
    bars = make_bars(
        [100, 100, 100, 100],
        highs=[100, 102, 101.5, 103],
        lows=[100, 99, 98, 99.5],
    )

    labels = generate_mfe_mae_labels(bars, horizons_minutes=(3,))
    first_labels = [label for label in labels if label.event_ts == bars[0]["event_ts"]]
    mfe = next(label for label in first_labels if label.label_type == LabelType.MFE_BY_HORIZON)
    mae = next(label for label in first_labels if label.label_type == LabelType.MAE_BY_HORIZON)

    assert mfe.value == pytest.approx(0.03)
    assert mae.value == pytest.approx(-0.02)
    assert mfe.path_metadata["max_high"] == "103"
    assert mae.path_metadata["min_low"] == "98"
    assert mfe.path_metadata["path_bar_count"] == 3
    validate_label_record(mfe)
    validate_label_record(mae)
