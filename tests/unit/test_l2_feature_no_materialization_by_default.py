from __future__ import annotations

import pytest

from alpha_system.l2.feature_validation import (
    L2FeatureMaterializationError,
    l2_feature_materialization_enabled_by_default,
    require_no_l2_feature_materialization_request,
)
from alpha_system.l2.features import materialize_l2_feature_values_by_default


def test_l2_feature_materialization_is_disabled_by_default() -> None:
    assert l2_feature_materialization_enabled_by_default() is False


def test_l2_feature_materialization_requests_fail_closed(tmp_path) -> None:
    with pytest.raises(L2FeatureMaterializationError, match="does not materialize"):
        require_no_l2_feature_materialization_request(output_path=tmp_path / "l2.jsonl")

    with pytest.raises(L2FeatureMaterializationError, match="does not materialize"):
        materialize_l2_feature_values_by_default(persist=True)
