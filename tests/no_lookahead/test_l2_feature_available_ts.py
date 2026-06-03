from __future__ import annotations

from datetime import timedelta

import pytest

from alpha_system.l2.feature_validation import (
    L2FeatureValidationError,
    assert_l2_feature_available,
)
from alpha_system.l2.features import (
    compute_quote_update_intensity,
    compute_top_of_book_spread,
)
from alpha_system.l2.fixtures import synthetic_l2_delta_rows, synthetic_l2_snapshot_rows


def test_l2_feature_available_ts_is_latest_used_input_availability() -> None:
    rows = [dict(row) for row in synthetic_l2_snapshot_rows()]
    rows[1]["available_ts"] = rows[1]["available_ts"] + timedelta(seconds=1)

    value = compute_top_of_book_spread(rows)

    assert value.available_ts == rows[1]["available_ts"]
    with pytest.raises(L2FeatureValidationError, match="before available_ts"):
        assert_l2_feature_available(
            value,
            as_of=value.available_ts - timedelta(microseconds=1),
        )
    assert_l2_feature_available(value, as_of=value.available_ts)


def test_event_rate_feature_does_not_count_future_available_deltas() -> None:
    values = compute_quote_update_intensity(synthetic_l2_delta_rows())

    assert values[0].value == pytest.approx(1.0)
    assert values[0].available_ts < values[-1].available_ts
