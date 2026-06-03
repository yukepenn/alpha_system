from __future__ import annotations

import pytest

from alpha_system.l2.feature_validation import L2FeatureValidationError
from alpha_system.l2.features import compute_top_of_book_spread, l2_feature_scope
from alpha_system.l2.fixtures import synthetic_l2_snapshot_rows


def test_l2_feature_scope_remains_design_and_fixture_only() -> None:
    scope = l2_feature_scope()

    assert scope.fixture_only is True
    assert scope.design_only is True
    assert scope.materialize_by_default is False
    assert scope.replay_engine is False
    assert scope.queue_model is False
    assert scope.passive_fill_model is False
    assert scope.broker_or_live_scope is False


def test_l2_feature_skeleton_rejects_non_synthetic_data_version() -> None:
    rows = [dict(row) for row in synthetic_l2_snapshot_rows()]
    rows[0]["data_version"] = "vendor:real:l2:2026-01-02"

    with pytest.raises(L2FeatureValidationError, match="synthetic fixture"):
        compute_top_of_book_spread(rows)
