from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.governance.canaries import (
    REQUIRED_NEGATIVE_CONTROL_TYPES,
    NegativeControlPassFail,
    create_negative_control_result,
    expected_failure_for_canary_type,
)
from alpha_system.governance.evidence_bundle import create_evidence_bundle
from alpha_system.governance.promotion_gate import (
    PromotionGateContext,
    validate_governance_transition,
)
from alpha_system.governance.study_spec import (
    StudySpec,
    generate_study_spec_id,
    validate_study_spec,
)
from alpha_system.governance.trial_ledger import TrialLedgerRecord, create_trial_ledger_record
from alpha_system.governance.validation import GovernanceValidationError
from alpha_system.governance.variant_ledger import (
    BudgetAmendmentType,
    create_budget_amendment_record,
    validate_variant_and_family_budget,
)

FIXTURE_PATH = Path("tests/fixtures/governance/study_spec_valid.json")
CODE_HASH = "a" * 64
CONFIG_HASH = "b" * 64
MANIFEST_HASH = "c" * 64
CREATED_AT = "2026-06-11T12:00:00Z"
AMENDED_AT = "2026-06-10T12:00:00Z"
FAMILY_ID = "family-rigor-p02-canary"


def study_spec(*, variant_budget: int = 1) -> StudySpec:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["variant_budget"] = variant_budget
    payload["study_spec_id"] = generate_study_spec_id(payload)
    return validate_study_spec(payload)


def trial_record(spec: StudySpec, *, run_id: str, variant_id: str) -> TrialLedgerRecord:
    return create_trial_ledger_record(
        alpha_spec_id=spec.alpha_spec_id,
        study_spec_id=spec.study_spec_id,
        run_id=run_id,
        variant_id=variant_id,
        status="COMPLETED",
        parameters={"threshold": 0.25, "window": 20},
        metrics_summary={"coverage": 0.75},
        failure_reason=None,
        oos_touched_flag=False,
        locked_test_contamination_flag=False,
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
    )


def evidence_bundle(records: tuple[TrialLedgerRecord, ...]) -> dict[str, object]:
    study_spec_id = records[0].study_spec_id
    return create_evidence_bundle(
        alpha_spec_id=records[0].alpha_spec_id,
        study_spec_id=study_spec_id,
        trial_ids=[record.trial_id for record in records],
        data_version="synthetic-data-v1",
        factor_version="synthetic-factor-v1",
        label_version="synthetic-label-v1",
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
        diagnostics_summary={
            "diagnostics_run_ref": "diagnostics-run-rigor-p02-canary",
            "metric_set": "synthetic governance smoke metrics",
        },
        negative_control_results=negative_control_results(study_spec_id),
        limitations=["synthetic metadata fixture only"],
        artifact_manifest=[
            {
                "logical_name": "diagnostics summary",
                "role": "diagnostics_summary",
                "reference": "local/evidence/diagnostics-summary.json",
                "content_hash": MANIFEST_HASH,
            }
        ],
        reviewer_verdict_reference="rver_0123456789abcdef01234567",
    ).to_dict()


def negative_control_results(study_spec_id: str) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for control_type in REQUIRED_NEGATIVE_CONTROL_TYPES:
        expected_failure = expected_failure_for_canary_type(control_type)
        results.append(
            create_negative_control_result(
                canary_type=control_type,
                expected_failure=expected_failure,
                observed_result=expected_failure,
                pass_fail=NegativeControlPassFail.PASS,
                related_study_or_evidence=study_spec_id,
                notes=f"Synthetic {control_type} control result for P02 canaries.",
            ).to_dict()
        )
    return results


def trial_ledger_file(tmp_path: Path) -> Path:
    path = tmp_path / "trial-ledger.json"
    path.write_text(
        json.dumps(
            {
                "schema": "synthetic-trial-ledger-v1",
                "records": [],
            },
            sort_keys=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def test_entry_hook_canary_blocks_variant_budget_overrun(tmp_path: Path) -> None:
    spec = study_spec(variant_budget=1)
    records = (
        trial_record(spec, run_id="diagnostics-run-canary-001", variant_id="variant-a"),
        trial_record(spec, run_id="diagnostics-run-canary-002", variant_id="variant-b"),
    )
    ledger_path = tmp_path / "variant-ledger.jsonl"
    ledger_path.write_text("", encoding="utf-8")

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_variant_and_family_budget(
            spec,
            trial_ledger_records=records,
            family_id=FAMILY_ID,
            variant_ledger_path=ledger_path,
            created_at=CREATED_AT,
        )

    assert exc_info.value.issues[0].code == "variant_budget_overrun"
    assert ledger_path.read_text(encoding="utf-8") == ""


def test_promotion_gate_canary_blocks_unrecorded_variant_ledger(tmp_path: Path) -> None:
    spec = study_spec(variant_budget=2)
    records = (
        trial_record(spec, run_id="diagnostics-run-canary-003", variant_id="variant-a"),
    )
    ledger_path = tmp_path / "variant-ledger.jsonl"
    ledger_path.write_text("", encoding="utf-8")

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "DIAGNOSTICS_RUN",
            "EVIDENCE_READY",
            PromotionGateContext(
                evidence_bundle=evidence_bundle(records),
                study_spec=spec,
                trial_ledger_records=records,
                trial_ledger_path=trial_ledger_file(tmp_path),
                family_id=FAMILY_ID,
                variant_ledger_path=ledger_path,
            ),
        )

    assert exc_info.value.issues[0].code == "variant_ledger_missing_records"


def test_budget_amendment_canary_detects_tampering(tmp_path: Path) -> None:
    spec = study_spec(variant_budget=1)
    records = (
        trial_record(spec, run_id="diagnostics-run-canary-004", variant_id="variant-a"),
        trial_record(spec, run_id="diagnostics-run-canary-005", variant_id="variant-b"),
    )
    amendment = create_budget_amendment_record(
        budget_type=BudgetAmendmentType.VARIANT,
        target_id=spec.study_spec_id,
        prior_budget=1,
        new_budget=2,
        actor="research-governance-owner",
        rationale="Synthetic predeclared budget increase for canary coverage.",
        created_at=AMENDED_AT,
    )
    tampered = amendment.to_dict()
    tampered["actor"] = "retroactive-editor"
    ledger_path = tmp_path / "variant-ledger.jsonl"
    ledger_path.write_text("", encoding="utf-8")

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_variant_and_family_budget(
            spec,
            trial_ledger_records=records,
            family_id=FAMILY_ID,
            variant_ledger_path=ledger_path,
            amendments=(tampered,),
            created_at=CREATED_AT,
        )

    assert exc_info.value.issues[0].code == "budget_amendment_id_mismatch"


def test_recorded_budget_canary_detects_study_spec_budget_tampering() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["family_budget"] = 2
    payload["study_spec_id"] = generate_study_spec_id(payload)
    tampered = dict(payload)
    tampered["family_budget"] = 3

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_study_spec(tampered)

    assert exc_info.value.issues[0].code == "study_spec_id_mismatch"


def test_unwritable_ledger_canary_blocks_entry_hook(tmp_path: Path) -> None:
    spec = study_spec(variant_budget=2)
    record = trial_record(
        spec,
        run_id="diagnostics-run-canary-006",
        variant_id="variant-a",
    )
    ledger_path = tmp_path / "variant-ledger.jsonl"
    ledger_path.write_text("", encoding="utf-8")
    ledger_path.chmod(0o444)
    try:
        with pytest.raises(GovernanceValidationError) as exc_info:
            validate_variant_and_family_budget(
                spec,
                trial_ledger_records=(record,),
                family_id=FAMILY_ID,
                variant_ledger_path=ledger_path,
                created_at=CREATED_AT,
            )
        assert exc_info.value.issues[0].code == "unwritable_variant_ledger"
    finally:
        ledger_path.chmod(0o644)
