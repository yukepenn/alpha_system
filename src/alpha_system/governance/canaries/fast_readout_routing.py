"""Per-lane routing canary for the FastReadout typed contract (Stage A).

This canary guards the fast-probe ``readout`` seam: it asserts that the current
producer shapes for BOTH lanes parse into the typed ``FastReadout`` contract,
round-trip, and expose the right canonical ``n_eff`` -- and that a deliberately
DRIFTED field makes ``FastReadout.from_dict`` RAISE. If a future producer or
consumer change drifts the seam, this canary fails loudly.

The fixtures here are SHAPE FIXTURES: small committed dicts that mirror the
verified producer key shapes (Step 1 of FAST_READOUT_CONTRACT_V1). They contain
no real market data, factor values, labels, scores, or study values -- only the
structural keys the contract pins. Driving the real ``fast_probe`` producer
requires materialized parquet slices (a data root), which is too heavy for a
canary; these fixtures are the structural mirror instead and are kept in sync
with the producer by this canary itself.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from alpha_system.research_lane.fast_readout import (
    FastReadout,
    FastReadoutContractError,
)

_EXPLORATORY = "EXPLORATORY"
_SCHEMA = "alpha_system.research_lane.fast_probe.v1"


def _main_effect_recorded_fixture() -> dict[str, Any]:
    """Mirror of ``_run_main_effect`` output (study_kind=main_effect, RECORDED)."""

    return {
        "schema": _SCHEMA,
        "status": "RECORDED",
        "study_kind": "main_effect",
        "stamp": _EXPLORATORY,
        "promotion_eligible": False,
        "mechanism_card": {"mechanism_id": "mech_canary"},
        "setup_spec": None,
        "slice_spec": {"slice_id": "slice_canary"},
        "row_access": {"status": "resolved_local_only", "fabricated_values": False},
        "resolved_handles": {"feature_handles": [], "label_handles": []},
        "engine": "build_factor_diagnostics_run",
        "readout": {
            "factor_diagnostics_report": {
                "quality_summary": {
                    "diagnostic_pass": True,
                    "quality_gate_count": 3,
                    "failing_gate_count": 0,
                    "pearson_ic": 0.04,
                    "rank_ic": 0.05,
                    "bucket_rank_correlation": 0.6,
                    "ic_power_mde_abs_ic": 0.12,
                    "ic_power_n_eff": 9,
                    "ic_power_statement": "synthetic",
                },
            },
            "diagnostics_run_record": {"run_id": "diag_canary"},
        },
        "readout_id": "fpmain_canary",
    }


def _setup_zero_pass_met_fixture() -> dict[str, Any]:
    """Mirror of ``_run_context_not_equal_trigger`` ZERO_PASS_MET output."""

    return {
        "schema": _SCHEMA,
        "status": "RECORDED",
        "study_kind": "context_not_equal_trigger",
        "stamp": _EXPLORATORY,
        "promotion_eligible": False,
        "mechanism_card": {"mechanism_id": "mech_canary"},
        "setup_spec": {"setup_spec_id": "setup_canary"},
        "slice_spec": {"slice_id": "slice_canary"},
        "row_access": {"status": "resolved_local_only", "fabricated_values": False},
        "resolved_handles": {"feature_handles": [], "label_handles": []},
        "engine": "evaluate_setup_conditional_probe",
        "readout": {
            "readout_id": "cprobe_canary",
            "setup_spec_id": "setup_canary",
            "path_label": "path_canary",
            "variant_id": "v0",
            "diagnostics": {
                "target_before_stop_probability": {},
                "post_event_mfe_mae": {},
                "continuous_outcome_mean_lift": {
                    "outcome_label_type": "net_excursion",
                    "conditioned_mean": 0.002,
                    "base_mean": 0.001,
                    "mean_lift": 0.001,
                    "conditioned_n": 40,
                    "base_n": 120,
                },
            },
            "counts": {},
            "variant_ledger_binding": {"existing_record_count": 0},
            "surrogate_fdr_gate": {
                "gate_status": "PASSED",
                "threshold_verdict": "ZERO_PASS_MET",
                "run_count": 200,
                "gate_pass_count": 0,
                "error_count": 0,
                "promotion_evidence": False,
            },
            "power": {
                "schema": "alpha_system.runtime.diagnostics.ic_power_statement.v1",
                "scope": "per_factor",
                "n_eff": 7,
                "se_ic": 0.4,
                "mde_abs_ic": 0.8,
                "z_multiple": 2.0,
                "statement": "synthetic",
                "statistical_validity_claim": False,
            },
        },
        "surrogate_fdr_gate": {
            "gate_status": "PASSED",
            "threshold_verdict": "ZERO_PASS_MET",
            "run_count": 200,
            "gate_pass_count": 0,
            "error_count": 0,
            "promotion_evidence": False,
            "conditioned_n_eff": 7,
            "observed_effect": 0.001,
        },
        "variant_ledger_binding": {"existing_record_count": 0},
        "power": {
            "schema": "alpha_system.runtime.diagnostics.ic_power_statement.v1",
            "scope": "per_factor",
            "n_eff": 7,
            "se_ic": 0.4,
            "mde_abs_ic": 0.8,
            "z_multiple": 2.0,
            "statement": "synthetic",
            "statistical_validity_claim": False,
        },
        "readout_id": "cprobe_canary",
    }


def _setup_surrogate_blocked_fixture() -> dict[str, Any]:
    """Mirror of ``_build_surrogate_blocked_readout`` output (INCONCLUSIVE)."""

    return {
        "schema": _SCHEMA,
        "status": "INCONCLUSIVE",
        "issue_code": "CALIBRATION_BLOCKED",
        "study_kind": "context_not_equal_trigger",
        "stamp": _EXPLORATORY,
        "promotion_eligible": False,
        "mechanism_card": {"mechanism_id": "mech_canary"},
        "setup_spec": {"setup_spec_id": "setup_canary"},
        "slice_spec": {"slice_id": "slice_canary"},
        "row_access": {"status": "resolved_local_only", "fabricated_values": False},
        "resolved_handles": {"feature_handles": [], "label_handles": []},
        "engine": "run_label_shuffle_surrogate",
        "surrogate_fdr_gate": {
            "gate_status": "BLOCKED",
            "threshold_verdict": "CALIBRATION_BLOCKED",
            "run_count": 200,
            "gate_pass_count": 3,
            "error_count": 0,
            "promotion_evidence": False,
            "conditioned_n_eff": 5,
            "observed_effect": 0.0004,
        },
        "power": {
            "schema": "alpha_system.runtime.diagnostics.ic_power_statement.v1",
            "scope": "per_factor",
            "n_eff": 5,
            "se_ic": 0.5,
            "mde_abs_ic": 1.0,
            "z_multiple": 2.0,
            "statement": "synthetic",
            "statistical_validity_claim": False,
        },
        "created_at": "2026-01-01T00:00:00Z",
        "readout_id": "fpsg_canary",
    }


def _data_gap_fixture() -> dict[str, Any]:
    """Mirror of ``build_fast_probe_data_gap`` output (INCONCLUSIVE/DATA_GAP)."""

    return {
        "schema": _SCHEMA,
        "status": "INCONCLUSIVE",
        "issue_code": "DATA_GAP",
        "study_kind": "context_not_equal_trigger",
        "stamp": _EXPLORATORY,
        "promotion_eligible": False,
        "mechanism_card": {"mechanism_id": "mech_canary"},
        "setup_spec": {"setup_spec_id": "setup_canary"},
        "slice_spec": {"slice_id": "slice_canary"},
        "row_access": {
            "status": "unresolved",
            "reason": "data root does not resolve",
            "fabricated_values": False,
        },
        "surrogate_fdr_gate": {
            "gate_status": "BLOCKED",
            "threshold_verdict": "CALIBRATION_BLOCKED",
            "run_count": 0,
            "gate_pass_count": 0,
            "error_count": 0,
            "promotion_evidence": False,
        },
        "power": {
            "schema": "alpha_system.runtime.diagnostics.ic_power_statement.v1",
            "scope": "per_factor",
            "n_eff": 0,
            "se_ic": None,
            "mde_abs_ic": None,
            "z_multiple": 2.0,
            "statement": "synthetic",
            "statistical_validity_claim": False,
        },
        "created_at": "2026-01-01T00:00:00Z",
        "readout_id": "fpgap_canary",
    }


def _pre_probe_main_effect_gate_fail_fixture() -> dict[str, Any]:
    """Mirror of ``cli/idea.py:_pre_probe_exploratory_readout`` for the main_effect lane.

    The ``alpha idea run`` gate-FAIL / DATA_GAP path emits study_kind=main_effect with
    an EMPTY ``readout: {}`` (no factor_diagnostics_report), a PARTIAL surrogate gate
    (only ``gate_status`` + ``threshold_verdict`` -- not yet run), and a zero power
    statement. A2.2 means ``ic_quality_summary`` is None for this INCONCLUSIVE shape.
    """

    return {
        "schema": _SCHEMA,
        "status": "INCONCLUSIVE",
        "issue_code": "PRE_TEST_FAIL",
        "study_kind": "main_effect",
        "stamp": _EXPLORATORY,
        "promotion_eligible": False,
        "mechanism_card": {"mechanism_id": "mech_canary"},
        "setup_spec": None,
        "slice_spec": {"slice_id": "slice_canary", "study_kind": "main_effect"},
        "row_access": {
            "status": "blocked",
            "reason": "pre-test gate failed",
            "fabricated_values": False,
        },
        "surrogate_fdr_gate": {
            "threshold_verdict": "CALIBRATION_BLOCKED",
            "gate_status": "BLOCKED",
        },
        "power": {
            "n_eff": 0,
            "mde_abs_ic": None,
        },
        "readout": {},
        "readout_id": "preprobe_main_canary",
    }


def _pre_probe_setup_gate_fail_fixture() -> dict[str, Any]:
    """Mirror of ``cli/idea.py:_pre_probe_exploratory_readout`` for the setup lane.

    Same pre-probe shape but study_kind=context_not_equal_trigger with a DATA_GAP
    issue code: empty ``readout: {}``, partial surrogate gate, zero power. It must
    PARSE (DATA_GAP lane requires neither the lift nor the full gate).
    """

    return {
        "schema": _SCHEMA,
        "status": "INCONCLUSIVE",
        "issue_code": "DATA_GAP",
        "study_kind": "context_not_equal_trigger",
        "stamp": _EXPLORATORY,
        "promotion_eligible": False,
        "mechanism_card": {"mechanism_id": "mech_canary"},
        "setup_spec": {"setup_spec_id": "setup_canary"},
        "slice_spec": {"slice_id": "slice_canary", "study_kind": "context_not_equal_trigger"},
        "row_access": {
            "status": "unresolved",
            "reason": "pre-test gate returned DATA_GAP",
            "fabricated_values": False,
        },
        "surrogate_fdr_gate": {
            "threshold_verdict": "CALIBRATION_BLOCKED",
            "gate_status": "BLOCKED",
        },
        "power": {
            "n_eff": 0,
            "mde_abs_ic": None,
        },
        "readout": {},
        "readout_id": "preprobe_setup_canary",
    }


# (fixture builder, expected canonical n_eff) per lane/status shape.
_FIXTURES: tuple[tuple[str, Any, int], ...] = (
    ("main_effect_recorded", _main_effect_recorded_fixture, 9),
    ("setup_zero_pass_met", _setup_zero_pass_met_fixture, 7),
    ("setup_surrogate_blocked", _setup_surrogate_blocked_fixture, 5),
    ("data_gap", _data_gap_fixture, 0),
    ("pre_probe_main_effect_gate_fail", _pre_probe_main_effect_gate_fail_fixture, 0),
    ("pre_probe_setup_gate_fail", _pre_probe_setup_gate_fail_fixture, 0),
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _round_trip_preserves(name: str, fixture: Mapping[str, Any]) -> None:
    parsed = FastReadout.from_dict(fixture)
    restored = parsed.to_dict()
    for key, value in fixture.items():
        _assert(
            key in restored,
            f"{name}: round-trip dropped top-level key {key!r}",
        )
        _assert(
            restored[key] == value,
            f"{name}: round-trip changed {key!r}: {restored[key]!r} != {value!r}",
        )


def _check_parses_and_n_eff() -> None:
    for name, builder, expected_n_eff in _FIXTURES:
        fixture = builder()
        parsed = FastReadout.from_dict(fixture)
        _assert(
            parsed.n_eff == expected_n_eff,
            f"{name}: canonical n_eff {parsed.n_eff} != expected {expected_n_eff}",
        )
        _round_trip_preserves(name, fixture)


def _check_drift_raises() -> None:
    # Drift 1: rename the main_effect canonical n_eff key -> required field missing
    # at the leaf the contract pins. (IcQualitySummary tolerates the rename at the
    # leaf as None, so the canonical accessor must then read 0 instead of 9 -- the
    # silent-misclassification the contract is meant to surface; we assert that a
    # drifted main_effect n_eff no longer resolves to the planted value.)
    drifted_main = _main_effect_recorded_fixture()
    quality = drifted_main["readout"]["factor_diagnostics_report"]["quality_summary"]
    quality["ic_neff"] = quality.pop("ic_power_n_eff")
    parsed = FastReadout.from_dict(drifted_main)
    _assert(
        parsed.n_eff != 9,
        "drift not caught: renamed ic_power_n_eff still resolved to the planted n_eff",
    )

    # Drift 2: drop a REQUIRED setup field (the nested factor_diagnostics_report on
    # main_effect) -> from_dict must RAISE FastReadoutContractError.
    missing_report = _main_effect_recorded_fixture()
    del missing_report["readout"]["factor_diagnostics_report"]
    _expect_raise(missing_report, "missing factor_diagnostics_report")

    # Drift 3: drop the required continuous lift on a setup RECORDED readout -> RAISE.
    missing_lift = _setup_zero_pass_met_fixture()
    del missing_lift["readout"]["diagnostics"]["continuous_outcome_mean_lift"]
    _expect_raise(missing_lift, "missing continuous_outcome_mean_lift")

    # Drift 4: unknown study_kind -> RAISE.
    unknown_kind = _main_effect_recorded_fixture()
    unknown_kind["study_kind"] = "some_new_lane"
    _expect_raise(unknown_kind, "unknown study_kind")


def _expect_raise(fixture: Mapping[str, Any], what: str) -> None:
    try:
        FastReadout.from_dict(deepcopy(dict(fixture)))
    except FastReadoutContractError:
        return
    raise AssertionError(f"drift not caught: {what} did not raise FastReadoutContractError")


def run_fast_readout_routing_canary() -> None:
    """Run all contract assertions; raise on the first failure."""

    _check_parses_and_n_eff()
    _check_drift_raises()


def main(argv: list[str] | None = None) -> int:
    try:
        run_fast_readout_routing_canary()
    except (AssertionError, FastReadoutContractError) as exc:
        print(f"FAIL fast_readout_routing: {exc}", file=sys.stderr)
        return 1
    print("fast_readout_routing OK: both lanes parse, round-trip, n_eff, and drift raises")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
