from __future__ import annotations

from alpha_system.factors.base import build_factor_from_spec
from alpha_system.factors.compute import compute_factor_values
from tests.fixtures.factors.synthetic import DATA_VERSION, factor_spec, make_bars


def test_factor_compute_is_deterministic_on_tiny_fixture() -> None:
    spec = factor_spec()
    factor = build_factor_from_spec(spec)
    bars = make_bars(["100", "101", "103"])

    first = compute_factor_values(spec, factor, bars, data_version=DATA_VERSION)
    second = compute_factor_values(spec, factor, bars, data_version=DATA_VERSION)

    assert [value.to_dict() for value in first] == [value.to_dict() for value in second]
    assert [value.value for value in first] == [None, 1.0, 2.0]
    assert [value.normalized_value for value in first] == [None, 1.0, 2.0]
    assert all(value.compute_version == "factor_compute_sdk_mvp_v1" for value in first)
