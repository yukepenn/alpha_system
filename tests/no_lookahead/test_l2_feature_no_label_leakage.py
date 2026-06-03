from __future__ import annotations

import pytest

from alpha_system.l2.feature_specs import all_l2_feature_declarations
from alpha_system.l2.feature_validation import (
    L2FeatureValidationError,
    validate_l2_feature_declarations,
)
from alpha_system.l2.features import compute_top_of_book_spread
from alpha_system.l2.fixtures import synthetic_l2_snapshot_rows


def test_l2_feature_inputs_reject_label_available_ts() -> None:
    rows = [dict(row) for row in synthetic_l2_snapshot_rows()]
    rows[0]["label_available_ts"] = rows[0]["available_ts"]

    with pytest.raises(L2FeatureValidationError, match="label_available_ts"):
        compute_top_of_book_spread(rows)


def test_l2_feature_specs_do_not_declare_label_inputs() -> None:
    validate_l2_feature_declarations(all_l2_feature_declarations())
