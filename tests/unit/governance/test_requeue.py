from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.cli.main import main
from alpha_system.governance.requeue import (
    MATERIALITY_MIN_ACCRUED_MONTHS,
    MATERIALITY_MIN_POWER_DELTA,
    REQUEUE_REASON,
    RequeuedVerdictRecord,
    estimate_planning_prior_power,
    materiality_rule,
    scan_requeue_candidates,
)
from alpha_system.governance.validation import GovernanceValidationError

FIXTURE_ROOT = Path("tests/unit/discovery_rigor_floor/fixtures/requeue")
ANNOTATION_ROOT = FIXTURE_ROOT / "annotations"
ACCEPTANCE_EVIDENCE = FIXTURE_ROOT / "acceptance_evidence.json"
FIXED_CREATED_AT = "2026-06-12T12:00:00Z"


def test_requeued_verdict_record_schema_round_trips() -> None:
    payload = {
        "original_verdict_ref": "synthetic/reviewer_verdicts/example.json",
        "requeue_reason": REQUEUE_REASON,
        "prior_power_estimate": 0.35,
        "new_power_estimate": 0.8,
        "data_accrued_months": 18,
        "eligible": True,
        "created_at": FIXED_CREATED_AT,
    }

    record = RequeuedVerdictRecord.from_dict(payload)

    assert record.to_dict() == payload
    assert RequeuedVerdictRecord.from_canonical_json(record.to_canonical_json()) == record


def test_requeued_verdict_record_rejects_unknown_fields_and_wrong_reason() -> None:
    payload = {
        "original_verdict_ref": "synthetic/reviewer_verdicts/example.json",
        "requeue_reason": REQUEUE_REASON,
        "prior_power_estimate": 0.35,
        "new_power_estimate": 0.8,
        "data_accrued_months": 18,
        "eligible": True,
        "created_at": FIXED_CREATED_AT,
        "extra": "not allowed",
    }

    with pytest.raises(GovernanceValidationError) as exc_info:
        RequeuedVerdictRecord.from_dict(payload)

    assert exc_info.value.issues[0].code == "unknown_field"


def test_requeued_verdict_record_rejects_wrong_reason() -> None:
    payload = {
        "original_verdict_ref": "synthetic/reviewer_verdicts/example.json",
        "requeue_reason": "manual retest",
        "prior_power_estimate": 0.35,
        "new_power_estimate": 0.8,
        "data_accrued_months": 18,
        "eligible": True,
        "created_at": FIXED_CREATED_AT,
    }

    with pytest.raises(GovernanceValidationError) as exc_info:
        RequeuedVerdictRecord.from_dict(payload)

    assert exc_info.value.issues[0].code == "invalid_requeue_reason"


def test_planning_power_estimator_handles_n_eff_and_metadata_absent_paths() -> None:
    n_eff_aware = estimate_planning_prior_power(
        sr_prior=0.5,
        data_months=48,
        n_eff=100,
        observation_count=400,
    )
    metadata_absent = estimate_planning_prior_power(sr_prior=0.5, data_months=48)
    metadata_partial = estimate_planning_prior_power(sr_prior=0.5, data_months=48, n_eff=100)

    assert n_eff_aware.estimate == 0.5
    assert n_eff_aware.effective_years == 1.0
    assert n_eff_aware.n_eff_ratio == 0.25
    assert n_eff_aware.metadata_status == "N_EFF_METADATA_USED"
    assert metadata_absent.estimate == 1.0
    assert metadata_absent.metadata_status == "N_EFF_METADATA_ABSENT"
    assert metadata_partial.estimate == 1.0
    assert metadata_partial.metadata_status == "N_EFF_METADATA_PARTIAL"


def test_requeue_scan_is_deterministic_and_respects_materiality_rule() -> None:
    first = scan_requeue_candidates(
        annotation_paths=[ANNOTATION_ROOT],
        acceptance_evidence_path=ACCEPTANCE_EVIDENCE,
        created_at=FIXED_CREATED_AT,
    )
    second = scan_requeue_candidates(
        annotation_paths=[ANNOTATION_ROOT],
        acceptance_evidence_path=ACCEPTANCE_EVIDENCE,
        created_at=FIXED_CREATED_AT,
    )

    assert first.render_table() == second.render_table()
    assert first.records_json() == second.records_json()
    assert materiality_rule()["min_accrued_accepted_months"] == MATERIALITY_MIN_ACCRUED_MONTHS
    assert materiality_rule()["min_power_estimate_delta"] == MATERIALITY_MIN_POWER_DELTA
    assert [row.study_spec_id for row in first.rows] == [
        "sspec_requeue_eligible",
        "sspec_requeue_not_eligible",
    ]
    by_study = {row.study_spec_id: row for row in first.rows}
    assert by_study["sspec_requeue_eligible"].eligible is True
    assert by_study["sspec_requeue_eligible"].data_accrued_months == 18
    assert by_study["sspec_requeue_eligible"].prior_power_estimate == 0.353553
    assert by_study["sspec_requeue_eligible"].new_power_estimate == 0.790569
    assert by_study["sspec_requeue_not_eligible"].eligible is False
    assert by_study["sspec_requeue_not_eligible"].data_accrued_months == 3


def test_requeue_scan_does_not_mutate_inputs() -> None:
    inputs = sorted(ANNOTATION_ROOT.glob("*.json")) + [ACCEPTANCE_EVIDENCE]
    before = {path: path.read_bytes() for path in inputs}

    scan_requeue_candidates(
        annotation_paths=[ANNOTATION_ROOT],
        acceptance_evidence_path=ACCEPTANCE_EVIDENCE,
        created_at=FIXED_CREATED_AT,
    )

    assert {path: path.read_bytes() for path in inputs} == before


def test_requeue_scan_fails_closed_on_missing_candidate_acceptance(tmp_path: Path) -> None:
    acceptance = tmp_path / "acceptance.json"
    acceptance.write_text(
        json.dumps(
            {
                "schema": "discovery_rigor_floor.dataset_acceptance_evidence.v1",
                "accepted_data": [
                    {
                        "study_spec_id": "sspec_other",
                        "accepted_data_months": 30,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        scan_requeue_candidates(
            annotation_paths=[ANNOTATION_ROOT],
            acceptance_evidence_path=acceptance,
            created_at=FIXED_CREATED_AT,
        )

    assert exc_info.value.issues[0].code == "missing_candidate_acceptance_evidence"


def test_requeue_scan_cli_prints_table_and_writes_records(
    tmp_path: Path,
    capsys,
) -> None:
    output_path = tmp_path / "requeue-records.json"

    code = main(
        [
            "governance",
            "requeue-scan",
            "--annotations",
            str(ANNOTATION_ROOT),
            "--acceptance-evidence",
            str(ACCEPTANCE_EVIDENCE),
            "--created-at",
            FIXED_CREATED_AT,
            "--out",
            str(output_path),
        ]
    )
    captured = capsys.readouterr()

    assert code == 0
    assert "Requeue Eligibility" in captured.out
    assert "sspec_requeue_eligible" in captured.out
    assert "sspec_requeue_substrate_gap" not in captured.out
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["requeued_verdict_records"][0]["eligible"] is True
    assert written["requeued_verdict_records"][1]["eligible"] is False


def test_requeue_scan_cli_fails_closed_on_missing_inputs(capsys) -> None:
    code = main(
        [
            "governance",
            "requeue-scan",
            "--annotations",
            "missing/requeue/annotations",
            "--acceptance-evidence",
            str(ACCEPTANCE_EVIDENCE),
            "--created-at",
            FIXED_CREATED_AT,
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.err)

    assert code == 2
    assert payload["status"] == "rejected"
    assert payload["issues"][0]["code"] == "missing_requeue_input_path"


def test_requeue_estimator_is_not_imported_by_promotion_gate() -> None:
    source = Path("src/alpha_system/governance/promotion_gate.py").read_text(encoding="utf-8")

    assert "governance.requeue" not in source
    assert "estimate_planning_prior_power" not in source
    assert "RequeuedVerdictRecord" not in source
