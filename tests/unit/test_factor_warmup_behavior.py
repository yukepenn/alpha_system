from __future__ import annotations

from alpha_system.factors.base import build_factor_from_spec
from alpha_system.factors.compute import compute_factor_values
from tests.fixtures.factors.synthetic import DATA_VERSION, factor_spec, make_bars


def test_insufficient_warmup_emits_null_and_quality_flag_without_lookahead() -> None:
    spec = factor_spec(warmup_bars=3)
    factor = build_factor_from_spec(spec)
    bars = make_bars(["100", "101", "10000"])

    values = compute_factor_values(spec, factor, bars, data_version=DATA_VERSION)

    assert values[0].value is None
    assert values[0].normalized_value is None
    assert "insufficient_warmup" in values[0].quality_flags
    assert values[1].value is None
    assert "insufficient_warmup" in values[1].quality_flags
    assert values[2].value == 9899.0
