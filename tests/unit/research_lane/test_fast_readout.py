"""Unit tests for the FastReadout typed contract (Stage A, additive)."""

from __future__ import annotations

import copy

import pytest

from alpha_system.governance.canaries.fast_readout_routing import (
    _data_gap_fixture,
    _main_effect_recorded_fixture,
    _setup_surrogate_blocked_fixture,
    _setup_zero_pass_met_fixture,
)
from alpha_system.research_lane.fast_readout import (
    ContinuousLiftSummary,
    FastReadout,
    FastReadoutContractError,
    IcQualitySummary,
    SurrogateFdrGate,
    validate_fast_readout,
)


def _assert_round_trip(fixture: dict) -> FastReadout:
    parsed = FastReadout.from_dict(fixture)
    restored = parsed.to_dict()
    assert restored == fixture
    return parsed


def test_main_effect_recorded_round_trip_and_typed_fields() -> None:
    fixture = _main_effect_recorded_fixture()
    parsed = _assert_round_trip(fixture)
    assert parsed.study_kind == "main_effect"
    assert parsed.status == "RECORDED"
    assert isinstance(parsed.ic_quality_summary, IcQualitySummary)
    assert parsed.ic_quality_summary.pearson_ic == 0.04
    assert parsed.ic_quality_summary.rank_ic == 0.05
    assert parsed.ic_quality_summary.bucket_rank_correlation == 0.6
    assert parsed.ic_quality_summary.diagnostic_pass is True
    assert parsed.ic_quality_summary.failing_gate_count == 0
    # main_effect carries no continuous lift / surrogate gate.
    assert parsed.continuous_lift_summary is None
    assert parsed.surrogate_fdr_gate is None


def test_setup_zero_pass_met_round_trip_and_typed_fields() -> None:
    fixture = _setup_zero_pass_met_fixture()
    parsed = _assert_round_trip(fixture)
    assert parsed.study_kind == "context_not_equal_trigger"
    assert parsed.status == "RECORDED"
    assert isinstance(parsed.continuous_lift_summary, ContinuousLiftSummary)
    assert parsed.continuous_lift_summary.outcome_label_type == "net_excursion"
    assert parsed.continuous_lift_summary.mean_lift == 0.001
    assert parsed.continuous_lift_summary.conditioned_n == 40
    assert parsed.continuous_lift_summary.base_n == 120
    assert isinstance(parsed.surrogate_fdr_gate, SurrogateFdrGate)
    assert parsed.surrogate_fdr_gate.threshold_verdict == "ZERO_PASS_MET"
    assert parsed.surrogate_fdr_gate.conditioned_n_eff == 7
    assert parsed.surrogate_fdr_gate.observed_effect == 0.001


def test_setup_surrogate_blocked_round_trip() -> None:
    fixture = _setup_surrogate_blocked_fixture()
    parsed = _assert_round_trip(fixture)
    assert parsed.status == "INCONCLUSIVE"
    assert parsed.issue_code == "CALIBRATION_BLOCKED"
    assert parsed.continuous_lift_summary is None
    assert parsed.surrogate_fdr_gate is not None
    assert parsed.surrogate_fdr_gate.gate_status == "BLOCKED"


def test_data_gap_round_trip() -> None:
    fixture = _data_gap_fixture()
    parsed = _assert_round_trip(fixture)
    assert parsed.status == "INCONCLUSIVE"
    assert parsed.issue_code == "DATA_GAP"
    assert parsed.ic_quality_summary is None
    assert parsed.continuous_lift_summary is None


def test_validate_fast_readout_is_from_dict() -> None:
    fixture = _main_effect_recorded_fixture()
    assert validate_fast_readout(fixture).to_dict() == fixture


@pytest.mark.parametrize(
    ("builder", "expected"),
    [
        (_main_effect_recorded_fixture, 9),
        (_setup_zero_pass_met_fixture, 7),
        (_setup_surrogate_blocked_fixture, 5),
        (_data_gap_fixture, 0),
    ],
)
def test_canonical_n_eff_resolution_per_lane(builder, expected) -> None:
    parsed = FastReadout.from_dict(builder())
    assert parsed.n_eff == expected


def test_main_effect_n_eff_reads_ic_quality_not_top_level_power() -> None:
    # A main_effect readout has no top-level power; n_eff must come from the IC
    # quality summary, never a recursive search that could grab another n_eff.
    fixture = _main_effect_recorded_fixture()
    assert "power" not in fixture
    assert FastReadout.from_dict(fixture).n_eff == 9


def test_raise_on_unknown_study_kind() -> None:
    fixture = _main_effect_recorded_fixture()
    fixture["study_kind"] = "some_new_lane"
    with pytest.raises(FastReadoutContractError, match="unknown study_kind"):
        FastReadout.from_dict(fixture)


def test_raise_on_missing_required_top_level_field() -> None:
    fixture = _main_effect_recorded_fixture()
    del fixture["status"]
    with pytest.raises(FastReadoutContractError, match="missing required field 'status'"):
        FastReadout.from_dict(fixture)


def test_raise_on_missing_main_effect_quality_summary() -> None:
    fixture = _main_effect_recorded_fixture()
    del fixture["readout"]["factor_diagnostics_report"]
    with pytest.raises(FastReadoutContractError, match="factor_diagnostics_report"):
        FastReadout.from_dict(fixture)


def test_raise_on_missing_setup_continuous_lift() -> None:
    fixture = _setup_zero_pass_met_fixture()
    del fixture["readout"]["diagnostics"]["continuous_outcome_mean_lift"]
    with pytest.raises(FastReadoutContractError, match="continuous_outcome_mean_lift"):
        FastReadout.from_dict(fixture)


def test_raise_on_setup_recorded_missing_power() -> None:
    fixture = _setup_zero_pass_met_fixture()
    del fixture["power"]
    with pytest.raises(FastReadoutContractError, match="requires a power statement"):
        FastReadout.from_dict(fixture)


def test_drifted_main_effect_n_eff_key_no_longer_resolves_planted_value() -> None:
    # Renaming the canonical ic_power_n_eff key drifts the contract: the typed
    # leaf reads None, so n_eff falls back to 0 rather than silently grabbing the
    # planted value via a recursive search. This is the drift the contract surfaces.
    fixture = _main_effect_recorded_fixture()
    quality = fixture["readout"]["factor_diagnostics_report"]["quality_summary"]
    quality["ic_neff"] = quality.pop("ic_power_n_eff")
    assert FastReadout.from_dict(fixture).n_eff != 9


def test_sub_object_round_trips_independently() -> None:
    gate = _setup_zero_pass_met_fixture()["surrogate_fdr_gate"]
    assert SurrogateFdrGate.from_dict(gate).to_dict() == gate
    lift = _setup_zero_pass_met_fixture()["readout"]["diagnostics"]["continuous_outcome_mean_lift"]
    assert ContinuousLiftSummary.from_dict(lift).to_dict() == lift


def test_fixtures_are_not_mutated_by_parsing() -> None:
    fixture = _setup_zero_pass_met_fixture()
    snapshot = copy.deepcopy(fixture)
    FastReadout.from_dict(fixture)
    assert fixture == snapshot
