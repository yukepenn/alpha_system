from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.governance.serialization import deserialize
from alpha_system.governance.study_spec import (
    StudyBudgetStatus,
    StudySpec,
    generate_study_spec_id,
    validate_study_spec,
)
from alpha_system.governance.trial_ledger import TrialLedgerRecord, create_trial_ledger_record
from alpha_system.governance.validation import GovernanceValidationError
from alpha_system.governance.variant_ledger import (
    BudgetAmendmentType,
    FamilyBudgetCheck,
    VariantLedger,
    VariantLedgerRecord,
    VariantLedgerStatus,
    create_budget_amendment_record,
    evaluate_family_budget,
    validate_variant_and_family_budget,
    validate_variant_ledger_record,
    variant_ledger_records_from_trial_ledger,
)

FIXTURE_PATH = Path("tests/fixtures/governance/study_spec_valid.json")
CODE_HASH = "a" * 64
CONFIG_HASH = "b" * 64
CREATED_AT = "2026-06-11T12:00:00Z"
AMENDED_AT = "2026-06-10T12:00:00Z"
FAMILY_ID = "family-rigor-floor"


def study_spec(
    *,
    variant_budget: int = 4,
    family_budget: int | None = None,
    metric_suffix: str = "",
) -> StudySpec:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["variant_budget"] = variant_budget
    if metric_suffix:
        payload["metrics"] = [*payload["metrics"], f"synthetic_{metric_suffix}"]
    if family_budget is not None:
        payload["family_budget"] = family_budget
    else:
        payload.pop("family_budget", None)
    payload["study_spec_id"] = generate_study_spec_id(payload)
    return validate_study_spec(payload)


def trial_record(
    spec: StudySpec,
    *,
    run_id: str,
    variant_id: str,
) -> TrialLedgerRecord:
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


def test_variant_ledger_record_round_trips_from_trial_accounting() -> None:
    spec = study_spec()
    trial = trial_record(spec, run_id="diagnostics-run-vl-001", variant_id="variant-a")

    budget_check, records = variant_ledger_records_from_trial_ledger(
        (trial,),
        study_spec=spec,
        family_id=FAMILY_ID,
        created_at=CREATED_AT,
    )

    assert budget_check.status is StudyBudgetStatus.RESPECTED
    assert len(records) == 1
    record = records[0]
    assert isinstance(record, VariantLedgerRecord)
    assert record.variant_id == "variant-a"
    assert record.trial_ids == (trial.trial_id,)
    assert record.status is VariantLedgerStatus.COMPLETED
    assert VariantLedgerRecord.from_canonical_json(record.to_canonical_json()) == record
    assert deserialize(record.to_canonical_json()) == record.to_dict()


def test_variant_ledger_record_rejects_bad_trial_ref_and_attempt_count() -> None:
    spec = study_spec()
    trial = trial_record(spec, run_id="diagnostics-run-vl-002", variant_id="variant-a")
    payload = {
        "variant_id": "variant-a",
        "alpha_spec_id": spec.alpha_spec_id,
        "study_spec_id": spec.study_spec_id,
        "family_id": FAMILY_ID,
        "attempt_count": 2,
        "trial_ids": [trial.trial_id],
        "status": "COMPLETED",
        "created_at": CREATED_AT,
    }

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_variant_ledger_record(payload)

    assert exc_info.value.issues[0].code == "attempt_count_trial_ids_mismatch"


def test_variant_ledger_jsonl_persistence_and_summary(tmp_path: Path) -> None:
    ledger_path = tmp_path / "variant-ledger.jsonl"
    ledger_path.write_text("", encoding="utf-8")
    spec = study_spec()
    records = (
        trial_record(spec, run_id="diagnostics-run-vl-003", variant_id="variant-a"),
        trial_record(spec, run_id="diagnostics-run-vl-004", variant_id="variant-b"),
    )

    result = validate_variant_and_family_budget(
        spec,
        trial_ledger_records=records,
        family_id=FAMILY_ID,
        variant_ledger_path=ledger_path,
        created_at=CREATED_AT,
    )

    ledger = VariantLedger(ledger_path)
    assert result.study_budget_check.observed_count == 2
    assert len(ledger.load_records()) == 2
    assert ledger.summary()["families"][FAMILY_ID]["observed_variant_count"] == 2


def test_family_budget_rolls_up_across_studies(tmp_path: Path) -> None:
    ledger_path = tmp_path / "variant-ledger.jsonl"
    ledger_path.write_text("", encoding="utf-8")
    first = study_spec(variant_budget=2, family_budget=2, metric_suffix="first")
    second = study_spec(variant_budget=2, family_budget=2, metric_suffix="second")
    validate_variant_and_family_budget(
        first,
        trial_ledger_records=(
            trial_record(first, run_id="diagnostics-run-vl-005", variant_id="variant-a"),
        ),
        family_id=FAMILY_ID,
        variant_ledger_path=ledger_path,
        created_at=CREATED_AT,
    )
    validate_variant_and_family_budget(
        second,
        trial_ledger_records=(
            trial_record(second, run_id="diagnostics-run-vl-006", variant_id="variant-b"),
        ),
        family_id=FAMILY_ID,
        variant_ledger_path=ledger_path,
        created_at=CREATED_AT,
    )

    check = evaluate_family_budget(
        family_id=FAMILY_ID,
        family_budget=1,
        records=VariantLedger(ledger_path).load_records(),
    )

    assert isinstance(check, FamilyBudgetCheck)
    assert check.status is StudyBudgetStatus.OVERRUN
    assert check.observed_count == 2
    assert check.overrun_by == 1


def test_family_budget_counts_same_variant_label_per_study(tmp_path: Path) -> None:
    ledger_path = tmp_path / "variant-ledger.jsonl"
    ledger_path.write_text("", encoding="utf-8")
    first = study_spec(variant_budget=2, family_budget=2, metric_suffix="first")
    second = study_spec(variant_budget=2, family_budget=2, metric_suffix="second")
    for index, spec in enumerate((first, second), start=1):
        validate_variant_and_family_budget(
            spec,
            trial_ledger_records=(
                trial_record(
                    spec,
                    run_id=f"diagnostics-run-vl-same-label-{index}",
                    variant_id="variant-local-001",
                ),
            ),
            family_id=FAMILY_ID,
            variant_ledger_path=ledger_path,
            created_at=CREATED_AT,
        )

    ledger = VariantLedger(ledger_path)
    check = evaluate_family_budget(
        family_id=FAMILY_ID,
        family_budget=1,
        records=ledger.load_records(),
    )
    summary = ledger.summary()["families"][FAMILY_ID]

    assert check.status is StudyBudgetStatus.OVERRUN
    assert check.observed_count == 2
    assert check.overrun_by == 1
    assert summary["observed_variant_count"] == 2
    assert summary["variant_ids"] == ["variant-local-001"]
    assert len(summary["variant_exposure_keys"]) == 2


def test_entry_hook_blocks_missing_and_unwritable_ledger(tmp_path: Path) -> None:
    spec = study_spec()
    trial = trial_record(spec, run_id="diagnostics-run-vl-007", variant_id="variant-a")

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_variant_and_family_budget(
            spec,
            trial_ledger_records=(trial,),
            family_id=FAMILY_ID,
            variant_ledger_path=tmp_path / "missing.jsonl",
        )
    assert exc_info.value.issues[0].code == "missing_variant_ledger"

    ledger_path = tmp_path / "variant-ledger.jsonl"
    ledger_path.write_text("", encoding="utf-8")
    ledger_path.chmod(0o444)
    try:
        with pytest.raises(GovernanceValidationError) as unwritable:
            validate_variant_and_family_budget(
                spec,
                trial_ledger_records=(trial,),
                family_id=FAMILY_ID,
                variant_ledger_path=ledger_path,
            )
        assert unwritable.value.issues[0].code == "unwritable_variant_ledger"
    finally:
        ledger_path.chmod(0o644)


def test_entry_hook_blocks_variant_overrun_without_amendment(tmp_path: Path) -> None:
    ledger_path = tmp_path / "variant-ledger.jsonl"
    ledger_path.write_text("", encoding="utf-8")
    spec = study_spec(variant_budget=1)
    records = (
        trial_record(spec, run_id="diagnostics-run-vl-008", variant_id="variant-a"),
        trial_record(spec, run_id="diagnostics-run-vl-009", variant_id="variant-b"),
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_variant_and_family_budget(
            spec,
            trial_ledger_records=records,
            family_id=FAMILY_ID,
            variant_ledger_path=ledger_path,
            created_at=CREATED_AT,
        )

    assert exc_info.value.issues[0].code == "variant_budget_overrun"
    assert VariantLedger(ledger_path).load_records() == ()


def test_predeclared_amendment_allows_overrun_and_tamper_is_detected(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / "variant-ledger.jsonl"
    ledger_path.write_text("", encoding="utf-8")
    spec = study_spec(variant_budget=1)
    records = (
        trial_record(spec, run_id="diagnostics-run-vl-010", variant_id="variant-a"),
        trial_record(spec, run_id="diagnostics-run-vl-011", variant_id="variant-b"),
    )
    amendment = create_budget_amendment_record(
        budget_type=BudgetAmendmentType.VARIANT,
        target_id=spec.study_spec_id,
        prior_budget=1,
        new_budget=2,
        actor="research-governance-owner",
        rationale="Synthetic predeclared budget increase for this test only.",
        created_at=AMENDED_AT,
    )

    result = validate_variant_and_family_budget(
        spec,
        trial_ledger_records=records,
        family_id=FAMILY_ID,
        variant_ledger_path=ledger_path,
        amendments=(amendment,),
        created_at=CREATED_AT,
    )

    assert result.amended is True
    assert result.amendments_applied == (amendment.amendment_id,)
    tampered = amendment.to_dict()
    tampered["new_budget"] = 3
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
