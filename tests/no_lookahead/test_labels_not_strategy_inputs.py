from __future__ import annotations

import pytest

from alpha_system.labels.alignment import LabelAlignmentError, reject_labels_as_strategy_inputs
from alpha_system.labels.generation import generate_forward_return_labels
from tests.fixtures.labels.synthetic_bars import regular_bars


def test_labels_are_rejected_as_live_strategy_inputs() -> None:
    label = generate_forward_return_labels(regular_bars(4), horizons_minutes=(1,))[0]

    with pytest.raises(LabelAlignmentError, match="strategy inputs"):
        reject_labels_as_strategy_inputs([label])
    with pytest.raises(LabelAlignmentError, match="strategy inputs"):
        reject_labels_as_strategy_inputs([{"label_type": "forward_return_1m"}])
    with pytest.raises(LabelAlignmentError, match="strategy inputs"):
        reject_labels_as_strategy_inputs(["label_available_ts"])
