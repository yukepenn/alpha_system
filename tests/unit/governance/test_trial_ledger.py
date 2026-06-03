from __future__ import annotations

from copy import deepcopy

import pytest

from alpha_system.governance.serialization import canonical_serialize, deserialize
from alpha_system.governance.study_spec import StudyBudgetStatus
from alpha_system.governance.trial_ledger import (
    FAILED_TRIAL_STATUSES,
    TRIAL_LEDGER_REQUIRED_FIELDS,
    TrialLedgerAccounting,
    TrialLedgerRecord,
    TrialStatus,
    account_trial_ledger,
    create_trial_ledger_record,
    generate_trial_ledger_id,
    validate_trial_ledger_record,
)
from alpha_system.governance.validation import GovernanceValidationError

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_ID = "sspec_438ceffd40855205de5497f0"
CODE_HASH = "a" * 64
CONFIG_HASH = "b" * 64


def valid_trial_payload(
    *,
    status: TrialStatus | str = TrialStatus.COMPLETED,
    run_id: str = "diagnostics-run-001",
    variant_id: str = "variant-001",
    parameters: dict[str, object] | None = None,
    metrics_summary: dict[str, object] | None = None,
    failure_reason: str | None = None,
    oos_touched_flag: bool = False,
    locked_test_contamination_flag: bool = False,
) -> dict[str, object]:
    active_parameters = {"threshold": 0.25, "window": 20} if parameters is None else parameters
    active_metrics = {"coverage": 0.75} if metrics_summary is None else metrics_summary
    record = create_trial_ledger_record(
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        run_id=run_id,
        variant_id=variant_id,
        status=status,
        parameters=dict(active_parameters),
        metrics_summary=dict(active_metrics),
        failure_reason=failure_reason,
        oos_touched_flag=oos_touched_flag,
        locked_test_contamination_flag=locked_test_contamination_flag,
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
    )
    return record.to_dict()


def payload_with_generated_id(payload: dict[str, object]) -> dict[str, object]:
    updated = deepcopy(payload)
    updated["trial_id"] = generate_trial_ledger_id(updated)
    return updated


def test_valid_trial_ledger_record_contains_all_required_fields() -> None:
    payload = valid_trial_payload()

    record = validate_trial_ledger_record(payload)

    assert isinstance(record, TrialLedgerRecord)
    assert tuple(record.to_dict()) == TRIAL_LEDGER_REQUIRED_FIELDS
    assert record.trial_id == generate_trial_ledger_id(payload)
    assert record.trial_id.startswith("trial_")
    assert record.alpha_spec_id.startswith("aspec_")
    assert record.study_spec_id.startswith("sspec_")
    assert record.status is TrialStatus.COMPLETED
    assert record.failure_reason is None


@pytest.mark.parametrize("field", TRIAL_LEDGER_REQUIRED_FIELDS)
def test_trial_ledger_rejects_each_missing_required_field(field: str) -> None:
    payload = valid_trial_payload()
    del payload[field]

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_trial_ledger_record(payload)

    assert exc_info.value.issues[0].code == "missing_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize(
    "field",
    [field for field in TRIAL_LEDGER_REQUIRED_FIELDS if field != "failure_reason"],
)
def test_trial_ledger_rejects_null_required_fields_except_failure_reason(
    field: str,
) -> None:
    payload = valid_trial_payload()
    payload[field] = None

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_trial_ledger_record(payload)

    assert exc_info.value.issues[0].code == "null_required_field"
    assert exc_info.value.issues[0].field == field


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("trial_id", "sspec_438ceffd40855205de5497f0", "unexpected_kind"),
        ("alpha_spec_id", "trial_e49649b00c617b1f713df3fa", "unexpected_kind"),
        ("study_spec_id", "aspec_af848bc999a4c4b11a421bd0", "unexpected_kind"),
        (
            "run_id",
            "runs/2026-06-03T135209Z_ALPHA_RESEARCH_GOVERNANCE_MVP",
            "run_id_must_not_be_path",
        ),
        ("variant_id", "", "empty_required_field"),
        ("status", "SKIPPED", "invalid_trial_status"),
        ("parameters", {}, "empty_required_field"),
        ("metrics_summary", {"": 1.0}, "invalid_metadata_key"),
        ("oos_touched_flag", 1, "invalid_field_type"),
        ("locked_test_contamination_flag", 0, "invalid_field_type"),
        ("code_hash", "not-a-sha256", "invalid_content_hash"),
        ("config_hash", "A" * 64, "invalid_content_hash"),
    ],
)
def test_trial_ledger_rejects_invalid_required_fields(
    field: str,
    value: object,
    code: str,
) -> None:
    payload = valid_trial_payload()
    payload[field] = value

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_trial_ledger_record(payload)

    assert exc_info.value.issues[0].code == code
    assert exc_info.value.issues[0].field.startswith(field)


def test_trial_ledger_rejects_unknown_fields_without_dropping_them() -> None:
    payload = valid_trial_payload()
    payload["promotion_ready"] = True

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_trial_ledger_record(payload)

    assert exc_info.value.issues[0].code == "unknown_field"
    assert "promotion_ready" in payload


def test_trial_ledger_rejects_id_that_does_not_match_content() -> None:
    payload = valid_trial_payload()
    changed = deepcopy(payload)
    changed["parameters"] = {"threshold": 0.50, "window": 20}

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_trial_ledger_record(changed)

    assert exc_info.value.issues[0].code == "trial_id_mismatch"
    assert exc_info.value.issues[0].field == "trial_id"


def test_trial_ledger_canonical_round_trip_is_deterministic() -> None:
    payload = valid_trial_payload()
    reordered = dict(reversed(list(payload.items())))

    record = validate_trial_ledger_record(payload)
    serialized = record.to_canonical_json()
    round_tripped = TrialLedgerRecord.from_canonical_json(serialized)

    assert round_tripped == record
    assert deserialize(serialized) == record.to_dict()
    assert canonical_serialize(reordered) == serialized


def test_create_trial_ledger_record_generates_content_bound_id() -> None:
    payload = valid_trial_payload()

    record = create_trial_ledger_record(
        alpha_spec_id=str(payload["alpha_spec_id"]),
        study_spec_id=str(payload["study_spec_id"]),
        run_id=str(payload["run_id"]),
        variant_id=str(payload["variant_id"]),
        status=TrialStatus.COMPLETED,
        parameters=dict(payload["parameters"]),
        metrics_summary=dict(payload["metrics_summary"]),
        failure_reason=None,
        oos_touched_flag=bool(payload["oos_touched_flag"]),
        locked_test_contamination_flag=bool(payload["locked_test_contamination_flag"]),
        code_hash=str(payload["code_hash"]),
        config_hash=str(payload["config_hash"]),
    )

    assert record.trial_id == payload["trial_id"]
    assert record.trial_id.startswith("trial_")


def test_trial_status_enum_is_closed_and_marks_failed_outcomes() -> None:
    assert {status.value for status in TrialStatus} == {
        "PLANNED",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "ABANDONED",
    }
    assert FAILED_TRIAL_STATUSES == {
        TrialStatus.FAILED,
        TrialStatus.ABANDONED,
    }


@pytest.mark.parametrize("status", [TrialStatus.FAILED, TrialStatus.ABANDONED])
def test_failed_or_abandoned_trials_are_recorded_with_empty_metrics(
    status: TrialStatus,
) -> None:
    payload = valid_trial_payload(
        status=status,
        metrics_summary={},
        failure_reason="synthetic setup failed before metrics were available",
    )

    record = validate_trial_ledger_record(payload)

    assert record.status is status
    assert record.metrics_summary == {}
    assert record.failure_reason == "synthetic setup failed before metrics were available"


@pytest.mark.parametrize("failure_reason", [None, "", "n/a", "unknown"])
def test_failed_trial_requires_substantive_failure_reason(
    failure_reason: str | None,
) -> None:
    payload = valid_trial_payload()
    payload["status"] = TrialStatus.FAILED.value
    payload["metrics_summary"] = {}
    payload["failure_reason"] = failure_reason
    payload = payload_with_generated_id(payload)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_trial_ledger_record(payload)

    assert exc_info.value.issues[0].code == "failure_reason_required"
    assert exc_info.value.issues[0].field == "failure_reason"


def test_non_failed_trial_requires_empty_failure_reason() -> None:
    payload = valid_trial_payload()
    payload["failure_reason"] = "not applicable because the record is completed"
    payload = payload_with_generated_id(payload)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_trial_ledger_record(payload)

    assert exc_info.value.issues[0].code == "failure_reason_must_be_empty"
    assert exc_info.value.issues[0].field == "failure_reason"


def test_trial_ledger_accounting_counts_failed_and_abandoned_trials() -> None:
    completed = validate_trial_ledger_record(
        valid_trial_payload(
            variant_id="variant-a",
            metrics_summary={"coverage": 0.75},
        )
    )
    failed = validate_trial_ledger_record(
        valid_trial_payload(
            status=TrialStatus.FAILED,
            run_id="diagnostics-run-002",
            variant_id="variant-b",
            metrics_summary={},
            failure_reason="synthetic dependency check failed before metrics existed",
            oos_touched_flag=True,
        )
    )
    abandoned = validate_trial_ledger_record(
        valid_trial_payload(
            status=TrialStatus.ABANDONED,
            run_id="diagnostics-run-003",
            variant_id="variant-b",
            metrics_summary={},
            failure_reason="synthetic budget stop abandoned this variant",
            locked_test_contamination_flag=True,
        )
    )

    accounting = account_trial_ledger(
        [completed.to_dict(), failed, abandoned],
        study_spec_id=STUDY_SPEC_ID,
        variant_budget=1,
    )

    assert isinstance(accounting, TrialLedgerAccounting)
    assert accounting.attempt_count == 3
    assert accounting.variant_attempt_count == 3
    assert accounting.observed_variant_count == 2
    assert accounting.variant_ids == ("variant-a", "variant-b")
    assert accounting.variant_counts == {"variant-a": 1, "variant-b": 2}
    assert accounting.status_counts == {
        "PLANNED": 0,
        "RUNNING": 0,
        "COMPLETED": 1,
        "FAILED": 1,
        "ABANDONED": 1,
    }
    assert accounting.failed_count == 1
    assert accounting.abandoned_count == 1
    assert accounting.failed_or_abandoned_count == 2
    assert accounting.budget_check.status is StudyBudgetStatus.OVERRUN
    assert accounting.budget_check.observed_count == 2
    assert accounting.budget_check.overrun_by == 1


def test_trial_ledger_accounting_surfaces_oos_and_contamination_flags() -> None:
    oos_record = validate_trial_ledger_record(
        valid_trial_payload(
            variant_id="variant-oos",
            oos_touched_flag=True,
        )
    )
    contaminated_record = validate_trial_ledger_record(
        valid_trial_payload(
            run_id="diagnostics-run-004",
            variant_id="variant-contaminated",
            locked_test_contamination_flag=True,
        )
    )

    accounting = account_trial_ledger(
        [oos_record, contaminated_record],
        study_spec_id=STUDY_SPEC_ID,
        variant_budget=3,
    )

    assert accounting.oos_touched_count == 1
    assert accounting.locked_test_contamination_count == 1
    assert accounting.any_oos_touched is True
    assert accounting.any_locked_test_contamination is True
    assert accounting.to_dict()["oos_touched_count"] == 1
    assert accounting.to_dict()["locked_test_contamination_count"] == 1


def test_trial_ledger_accounting_blocks_missing_ledger_for_study() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        account_trial_ledger([], study_spec_id=STUDY_SPEC_ID, variant_budget=1)

    assert exc_info.value.issues[0].code == "missing_trial_ledger_records"
    assert exc_info.value.issues[0].field == "records"
