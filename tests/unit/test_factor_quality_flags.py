from __future__ import annotations

from alpha_system.factors.base import build_factor_from_spec
from alpha_system.factors.compute import compute_factor_values
from alpha_system.factors.quality import merge_quality_flags, normalize_quality_flags
from tests.fixtures.factors.synthetic import DATA_VERSION, factor_spec, make_bars


def test_quality_flags_are_normalized_and_deduplicated() -> None:
    assert normalize_quality_flags(("gap", "gap", "", None, "synthetic")) == (
        "gap",
        "synthetic",
    )
    assert merge_quality_flags(("gap",), ("gap", "late")) == ("gap", "late")


def test_bar_quality_flags_propagate_to_factor_values() -> None:
    spec = factor_spec()
    bars = make_bars(["100", "101"], quality_flags=("synthetic", "gap"))

    values = compute_factor_values(
        spec,
        build_factor_from_spec(spec),
        bars,
        data_version=DATA_VERSION,
    )

    assert "input_quality" in values[1].quality_flags
    assert "synthetic" in values[1].quality_flags
    assert "gap" in values[1].quality_flags
    assert "insufficient_warmup" in values[0].quality_flags
