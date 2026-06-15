from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from alpha_system.cli.main import main as cli_main
from alpha_system.governance.idea_draft import build_idea_validation_bundle
from alpha_system.governance.verdict_reason_code import validate_verdict_reason_code
from alpha_system.research_lane import verdict_report as verdict_report_module
from alpha_system.research_lane.testability_gate import (
    CHECK_FEATURES_MATERIALIZED,
    CHECK_LABELS_EXIST,
    CHECK_N_EFF_MDE_DEDUP,
    CHECK_NO_LOOKAHEAD_SURROGATE,
    CHECK_PATH_LABEL_TWO_CLASS,
)
from alpha_system.research_lane.verdict_report import render_verdict_report

FIXTURE_IDEA = Path("research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml")


def test_verdict_report_matches_golden_research_only_report() -> None:
    bundle = _bundle()

    report = render_verdict_report(bundle.idea_draft, _gate_result(), _fast_readout())

    assert report == _expected_report(bundle)
    assert "- reason_code: REGIME_UNSTABLE" in report
    assert validate_verdict_reason_code("REGIME_UNSTABLE").value in report
    lowered = report.lower()
    assert "profit" not in lowered
    assert "tradab" not in lowered
    assert "production" not in lowered
    assert "paper trading" not in lowered
    assert "live trading" not in lowered


def test_verdict_report_single_class_is_self_evident_data_gap() -> None:
    report = render_verdict_report(
        _bundle().idea_draft,
        _gate_result(class_count=1, minority_count=0),
        _fast_readout(verdict="WATCH"),
    )

    assert "- class_count: 1" in report
    assert "- minority_count: 0" in report
    assert "- verdict: DATA_GAP" in report
    assert "- reason_code: DATA_QUALITY" in report
    assert "- verdict: WATCH" not in report
    assert "- verdict: CANDIDATE" not in report
    assert "- verdict: INCONCLUSIVE" not in report


def test_verdict_report_data_gap_fabricates_no_metric_value() -> None:
    report = render_verdict_report(
        _bundle().idea_draft,
        _gate_result(),
        _fast_readout(
            status="INCONCLUSIVE",
            issue_code="DATA_GAP",
            verdict=None,
            row_access={
                "status": "unresolved",
                "reason": "bounded slice rows unavailable",
                "fabricated_values": False,
            },
            surrogate_fdr_gate={
                "threshold_verdict": "CALIBRATION_BLOCKED",
                "gate_status": "BLOCKED",
            },
            power={"n_eff": 0, "minimum_detectable_abs_ic": None},
            readout={"fabricated_metric": 999},
        ),
    )

    assert "- verdict: DATA_GAP" in report
    assert "- n_eff: 0" in report
    assert "fabricated_metric" not in report
    assert "999" not in report


def test_alpha_idea_report_cli_writes_report_from_fixture_readouts(tmp_path) -> None:
    gate_path = tmp_path / "gate.json"
    readout_path = tmp_path / "fast_readout.json"
    output_path = tmp_path / "REPORT.md"
    gate_path.write_text(json.dumps(_gate_result()), encoding="utf-8")
    readout_path.write_text(json.dumps(_fast_readout()), encoding="utf-8")

    exit_code = cli_main(
        [
            "idea",
            "report",
            FIXTURE_IDEA.as_posix(),
            "--testability-json",
            gate_path.as_posix(),
            "--fast-readout-json",
            readout_path.as_posix(),
            "--output",
            output_path.as_posix(),
        ]
    )

    assert exit_code == 0
    assert output_path.read_text(encoding="utf-8") == _expected_report(_bundle())


def test_verdict_report_source_stays_value_loader_free() -> None:
    source = inspect.getsource(verdict_report_module)

    assert "core.value_store" not in source
    assert "load_parquet_values" not in source
    assert "read_parquet" not in source
    assert "numpy" not in source
    assert "pandas" not in source
    assert "polars" not in source


def _main_effect_quality(
    *,
    pearson_ic: float,
    rank_ic: float,
    mde: float = 0.0034,
    n_eff: int = 327155,
    diagnostic_pass: bool = True,
    failing_gate_count: int = 0,
    bucket_rank_correlation: float = -0.8,
) -> dict[str, object]:
    return {
        "pearson_ic": pearson_ic,
        "rank_ic": rank_ic,
        "ic_power_mde_abs_ic": mde,
        "ic_power_n_eff": n_eff,
        "diagnostic_pass": diagnostic_pass,
        "failing_gate_count": failing_gate_count,
        "bucket_rank_correlation": bucket_rank_correlation,
    }


def _main_effect_report(quality: dict[str, object]) -> dict[str, str]:
    report = render_verdict_report(
        _bundle().idea_draft,
        _gate_result(),
        _fast_readout(
            verdict=None,
            readout={"factor_diagnostics_report": {"quality_summary": quality}},
        ),
    )
    section: dict[str, str] = {}
    in_final = False
    for raw in report.splitlines():
        line = raw.strip()
        if line == "## Final Verdict":
            in_final = True
            continue
        if in_final and line.startswith("## "):
            break
        if in_final and line.startswith("- ") and ": " in line:
            key, value = line[2:].split(": ", 1)
            section[key.strip()] = value.strip()
    return section


def test_main_effect_well_powered_signal_is_signal_pending_reviewer() -> None:
    section = _main_effect_report(
        _main_effect_quality(pearson_ic=-0.0557, rank_ic=-0.0150)
    )

    assert section["verdict"] == "INCONCLUSIVE"
    assert section["reason_code"] == "SIGNAL_PENDING_REVIEWER"


def test_main_effect_well_powered_null_is_reject() -> None:
    section = _main_effect_report(
        _main_effect_quality(pearson_ic=0.0009, rank_ic=-0.0005)
    )

    assert section["verdict"] == "REJECT"
    assert section["reason_code"] == "WELL_POWERED_NULL"


def test_main_effect_underpowered_is_inconclusive_underpowered() -> None:
    section = _main_effect_report(
        _main_effect_quality(pearson_ic=-0.05, rank_ic=-0.05, mde=0.0, n_eff=1)
    )

    assert section["verdict"] == "INCONCLUSIVE"
    assert section["reason_code"] == "UNDERPOWERED"


def test_main_effect_mixed_detectability_is_review_needed() -> None:
    # pearson resolves above the floor, rank does not -> ambiguous, reviewer must decide.
    section = _main_effect_report(
        _main_effect_quality(pearson_ic=-0.05, rank_ic=0.0010)
    )

    assert section["verdict"] == "INCONCLUSIVE"
    assert section["reason_code"] == "REVIEW_NEEDED"


def test_main_effect_sign_conflict_is_review_needed() -> None:
    # both ICs resolve above the floor but disagree in sign -> reviewer must decide.
    section = _main_effect_report(
        _main_effect_quality(pearson_ic=0.05, rank_ic=-0.05)
    )

    assert section["verdict"] == "INCONCLUSIVE"
    assert section["reason_code"] == "REVIEW_NEEDED"


def test_main_effect_failed_diagnostic_gate_is_data_quality() -> None:
    section = _main_effect_report(
        _main_effect_quality(
            pearson_ic=-0.05, rank_ic=-0.05, diagnostic_pass=False, failing_gate_count=1
        )
    )

    assert section["verdict"] == "INCONCLUSIVE"
    assert section["reason_code"] == "DATA_QUALITY"


def _bundle():
    return build_idea_validation_bundle(
        json.loads(FIXTURE_IDEA.read_text(encoding="utf-8")),
        source=FIXTURE_IDEA.as_posix(),
    )


def _gate_result(
    *,
    class_count: int = 2,
    minority_count: int = 1,
) -> dict[str, object]:
    class_status = "PASS" if class_count >= 2 else "DATA_GAP"
    overall = "PASS" if class_count >= 2 else "DATA_GAP"
    return {
        "overall_status": overall,
        "verdict": overall,
        "pre_test": True,
        "shot_spent": False,
        "probe_invoked": False,
        "idea_draft": "fixture",
        "slice_id": "unit-slice",
        "checks": [
            {
                "check_id": CHECK_FEATURES_MATERIALIZED,
                "status": "PASS",
                "detail": {"message": "feature pack handles resolved"},
            },
            {
                "check_id": CHECK_LABELS_EXIST,
                "status": "PASS",
                "detail": {"message": "label pack handles resolved"},
            },
            {
                "check_id": CHECK_PATH_LABEL_TWO_CLASS,
                "status": class_status,
                "detail": {
                    "message": "path-label class balance summarized",
                    "class_balance": {
                        "class_count": class_count,
                        "majority_class_count": 3,
                        "minority_class_count": minority_count,
                        "observed_outcome_count": 4,
                    },
                },
            },
            {
                "check_id": CHECK_N_EFF_MDE_DEDUP,
                "status": "PASS",
                "detail": {
                    "message": "N_eff/MDE metadata are plausible",
                    "n_eff": 24,
                    "minimum_detectable_effect": 0.25,
                    "duplicate_exposure_status": "bounded",
                },
            },
            {
                "check_id": CHECK_NO_LOOKAHEAD_SURROGATE,
                "status": "PASS",
                "detail": {
                    "message": "available_ts and surrogate readiness known",
                    "surrogate_fdr_requirement": "ZERO_PASS_MET",
                },
            },
        ],
    }


def _fast_readout(
    *,
    status: str = "RECORDED",
    issue_code: str | None = None,
    verdict: str | None = "WATCH",
    row_access: dict[str, object] | None = None,
    surrogate_fdr_gate: dict[str, object] | None = None,
    power: dict[str, object] | None = None,
    readout: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "alpha_system.research_lane.fast_probe.v1",
        "status": status,
        "issue_code": issue_code,
        "study_kind": "main_effect",
        "promotion_eligible": False,
        "mechanism_card": {
            "duplicate_exposure": {
                "family_id": "fixture_family",
                "status": "bounded",
                "variant_id": "baseline",
            }
        },
        "slice_spec": {
            "slice_id": "unit-slice",
            "study_kind": "main_effect",
            "dataset_version_id": "dsv_fixture",
            "partition_id": "partition_fixture",
            "instrument_id": "ES",
            "session_id": "RTH",
            "data_version": "dsv_fixture",
            "feature_inputs": [
                {
                    "role": "factor",
                    "factor_id": "session_calendar_roll_day_of_week",
                    "factor_version": "v1",
                    "pack_ref": "fver_fixture",
                    "feature_request_id": "freq_fixture",
                }
            ],
            "label_inputs": [
                {
                    "role": "label",
                    "label_id": "fixed_horizon_midprice_forward",
                    "pack_ref": "lver_fixture",
                    "label_spec_id": "lspec_fixture",
                }
            ],
            "horizon_seconds": 1800,
            "required_future_bars": 3,
            "created_at": "2026-06-14T00:00:00Z",
        },
        "row_access": row_access
        or {
            "status": "resolved",
            "fabricated_values": False,
        },
        "engine": "fixture_fast_probe",
        "surrogate_fdr_gate": surrogate_fdr_gate
        or {
            "threshold_verdict": "ZERO_PASS_MET",
            "gate_status": "PASS",
        },
        "power": power or {"n_eff": 24, "minimum_detectable_abs_ic": 0.25},
        "readout": readout or {},
    }
    if verdict is not None:
        payload.update(
            {
                "verdict": verdict,
                "reason_code": "REGIME_UNSTABLE",
                "why": "Upstream governed readout requested bounded watch routing.",
                "next_action": "Keep as research-only watch item for reviewer routing.",
            }
        )
    return payload


def _expected_report(bundle) -> str:
    idea = bundle.idea_draft
    return f"""# Idea Verdict Report

## Idea Summary
- alpha_spec_id: {idea.alpha_spec_id}
- mechanism_id: {idea.mechanism_id}
- setup_spec_id: n/a
- hypothesis_id: {idea.hypothesis_id}
- source: research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml

## Study Kind
- study_kind: main_effect

## Slice
- slice_id: unit-slice
- instrument: ES
- session: RTH
- window: horizon_seconds=1800; required_future_bars=3; created_at=2026-06-14T00:00:00Z
- dataset_version_id: dsv_fixture
- partition_id: partition_fixture
- feature_pack_refs: fver_fixture
- label_pack_refs: lver_fixture

## Data / Features / Labels Used
- data_version: dsv_fixture
- features:
  - role=factor; factor_id=session_calendar_roll_day_of_week; factor_version=v1; pack_ref=fver_fixture; feature_request_id=freq_fixture
- labels:
  - role=label; label_id=fixed_horizon_midprice_forward; pack_ref=lver_fixture; label_spec_id=lspec_fixture

## Dedup Outcome
- family_id: fixture_family
- status: bounded
- variant_id: baseline

## Testability Gates
- features_materialized: PASS - feature pack handles resolved
- labels_path_labels_exist: PASS - label pack handles resolved
- path_label_two_class: PASS - path-label class balance summarized
- n_eff_mde_plausible_and_dedup_known: PASS - N_eff/MDE metadata are plausible
- available_ts_and_surrogate_fdr_known: PASS - available_ts and surrogate readiness known

## Fast Readout
- status: RECORDED
- issue_code: n/a
- engine: fixture_fast_probe
- class_count: 2
- minority_count: 1
- row_access: status=resolved; fabricated_values=false

## N_eff / MDE
- n_eff: 24
- mde: 0.25

## Surrogate State
- state: ZERO_PASS_MET
- threshold_verdict: ZERO_PASS_MET
- gate_status: PASS

## Final Verdict
- verdict: WATCH
- reason_code: REGIME_UNSTABLE
- why: Upstream governed readout requested bounded watch routing.
- next_action: Keep as research-only watch item for reviewer routing.
"""
