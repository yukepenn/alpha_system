from __future__ import annotations

import pytest

from alpha_system.l2.features import compute_quote_update_intensity
from alpha_system.l2.fixtures import synthetic_l2_delta_rows


def test_quote_update_intensity_is_available_ts_ordered() -> None:
    values = compute_quote_update_intensity(synthetic_l2_delta_rows())

    assert [value.factor_id for value in values] == [
        "l2_quote_update_intensity",
        "l2_quote_update_intensity",
        "l2_quote_update_intensity",
    ]
    assert [value.value for value in values] == pytest.approx([1.0, 2.0, 2.0])
    assert [value.bar_index for value in values] == [0, 1, 2]
    assert values[0].available_ts <= values[1].available_ts <= values[2].available_ts
