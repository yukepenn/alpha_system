from __future__ import annotations

import pytest

from alpha_system.runtime.diagnostics.power import (
    DEFAULT_IC_MDE_Z_MULTIPLE,
    ICPowerStatementError,
    build_detection_power_report,
    build_ic_power_statement,
    estimate_ic_standard_error,
    minimum_detectable_abs_ic,
)


def test_ic_power_statement_math_and_edges() -> None:
    assert estimate_ic_standard_error(0) is None
    assert estimate_ic_standard_error(1) is None
    assert estimate_ic_standard_error(5) == pytest.approx(0.5)
    assert minimum_detectable_abs_ic(5, z_multiple=2.0) == pytest.approx(1.0)

    block = build_ic_power_statement(n_eff=5, z_multiple=2.0)
    assert block["se_ic"] == pytest.approx(0.5)
    assert block["mde_abs_ic"] == pytest.approx(1.0)
    assert block["statistical_validity_claim"] is False
    assert "Could have detected IC down to" in str(block["statement"])


def test_mde_monotonically_decreases_as_n_eff_grows() -> None:
    small = minimum_detectable_abs_ic(5)
    medium = minimum_detectable_abs_ic(26)
    large = minimum_detectable_abs_ic(101)

    assert small is not None
    assert medium is not None
    assert large is not None
    assert small > medium > large


def test_detection_power_report_carries_stacked_and_per_factor_blocks() -> None:
    report = build_detection_power_report(
        stacked_n_eff=101,
        per_factor_inputs=(
            {"factor_id": "factor_a", "factor_version": "v1", "n_eff": 26},
            {"factor_id": "factor_b", "factor_version": "v2", "n_eff": 101},
        ),
    )

    assert report["stacked"]["n_eff"] == 101
    assert report["stacked"]["z_multiple"] == DEFAULT_IC_MDE_Z_MULTIPLE
    assert len(report["per_factor"]) == 2
    assert report["per_factor"][0]["factor_id"] == "factor_a"
    assert report["per_factor"][0]["mde_abs_ic"] > report["per_factor"][1]["mde_abs_ic"]
    assert report["statistical_validity_claim"] is False


def test_power_inputs_fail_closed_on_invalid_n_eff() -> None:
    with pytest.raises(ICPowerStatementError, match="n_eff"):
        build_ic_power_statement(n_eff=-1)
