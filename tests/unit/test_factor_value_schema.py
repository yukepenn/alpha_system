from __future__ import annotations

from alpha_system.factors.base import FACTOR_VALUE_SCHEMA_FIELDS, build_factor_from_spec
from alpha_system.factors.compute import compute_factor_values
from tests.fixtures.factors.synthetic import DATA_VERSION, factor_spec, make_bars


def test_factor_value_schema_fields_are_present_and_ordered() -> None:
    spec = factor_spec()
    values = compute_factor_values(
        spec,
        build_factor_from_spec(spec),
        make_bars(["100", "101"]),
        data_version=DATA_VERSION,
    )

    payload = values[1].to_dict()

    assert tuple(payload) == FACTOR_VALUE_SCHEMA_FIELDS
    assert payload["factor_id"] == spec.factor_id
    assert payload["factor_version"] == spec.version
    assert payload["instrument_id"] == "SYNTH_FACTOR"
    assert payload["session_id"] == "XNYS:2026-01-02:regular"
    assert payload["bar_index"] == 1
    assert payload["data_version"] == DATA_VERSION
    assert payload["compute_version"] == "factor_compute_sdk_mvp_v1"
