"""TrialLedgerRecord contract and pure variant-accounting metadata."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import NoneType
from typing import Any, cast

from alpha_system.governance.ids import (
    GovernanceIdError,
    GovernanceIdKind,
    generate_governance_id,
    validate_governance_id,
)
from alpha_system.governance.serialization import (
    GovernanceSerializationError,
    JsonValue,
    canonical_serialize,
    deserialize,
)
from alpha_system.governance.study_spec import (
    StudyBudgetCheck,
    evaluate_variant_budget,
)
from alpha_system.governance.validation import (
    ExpectedType,
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
    validate_schema,
)

TRIAL_LEDGER_REQUIRED_FIELDS = (
    "trial_id",
    "alpha_spec_id",
    "study_spec_id",
    "run_id",
    "variant_id",
    "status",
    "parameters",
    "metrics_summary",
    "failure_reason",
    "oos_touched_flag",
    "locked_test_contamination_flag",
    "code_hash",
    "config_hash",
)
TRIAL_LEDGER_ID_COMPONENT_FIELDS = tuple(
    field for field in TRIAL_LEDGER_REQUIRED_FIELDS if field != "trial_id"
)
TRIAL_LEDGER_NON_NULL_REQUIRED_FIELDS = tuple(
    field for field in TRIAL_LEDGER_REQUIRED_FIELDS if field != "failure_reason"
)
_SHA256_HEX_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_VAGUE_TEXT = {
    "",
    "-",
    "n/a",
    "na",
    "none",
    "null",
    "tbd",
    "todo",
    "unknown",
    "placeholder",
    "to be defined",
    "to be determined",
}


class TrialStatus(StrEnum):
    """Closed trial outcome values for TrialLedger records."""

    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"


FAILED_TRIAL_STATUSES = frozenset(
    {
        TrialStatus.FAILED,
        TrialStatus.ABANDONED,
    }
)
TRIAL_LEDGER_FIELD_TYPES: dict[str, ExpectedType] = {
    "trial_id": str,
    "alpha_spec_id": str,
    "study_spec_id": str,
    "run_id": str,
    "variant_id": str,
    "status": (str, TrialStatus),
    "parameters": dict,
    "metrics_summary": dict,
    "failure_reason": (str, NoneType),
    "oos_touched_flag": bool,
    "locked_test_contamination_flag": bool,
    "code_hash": str,
    "config_hash": str,
}


@dataclass(frozen=True, slots=True)
class TrialLedgerRecord:
    """Validated metadata record for one research attempt or variant."""

    trial_id: str
    alpha_spec_id: str
    study_spec_id: str
    run_id: str
    variant_id: str
    status: TrialStatus
    parameters: dict[str, JsonValue]
    metrics_summary: dict[str, JsonValue]
    failure_reason: str | None
    oos_touched_flag: bool
    locked_test_contamination_flag: bool
    code_hash: str
    config_hash: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> TrialLedgerRecord:
        """Build a `TrialLedgerRecord` from a mapping after validation."""

        return validate_trial_ledger_record(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> TrialLedgerRecord:
        """Deserialize canonical JSON and validate the resulting record."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="TrialLedgerRecord")
        return validate_trial_ledger_record(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "trial_id": self.trial_id,
            "alpha_spec_id": self.alpha_spec_id,
            "study_spec_id": self.study_spec_id,
            "run_id": self.run_id,
            "variant_id": self.variant_id,
            "status": self.status.value,
            "parameters": dict(self.parameters),
            "metrics_summary": dict(self.metrics_summary),
            "failure_reason": self.failure_reason,
            "oos_touched_flag": self.oos_touched_flag,
            "locked_test_contamination_flag": self.locked_test_contamination_flag,
            "code_hash": self.code_hash,
            "config_hash": self.config_hash,
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated record through the canonical primitive."""

        return canonical_serialize(self.to_dict())


@dataclass(frozen=True, slots=True)
class TrialLedgerAccounting:
    """Pure metadata summary for trial attempts and observed variants."""

    study_spec_id: str
    variant_budget: int
    attempt_count: int
    observed_variant_count: int
    variant_attempt_count: int
    variant_ids: tuple[str, ...]
    variant_counts: dict[str, int]
    status_counts: dict[str, int]
    failed_count: int
    abandoned_count: int
    failed_or_abandoned_count: int
    oos_touched_count: int
    locked_test_contamination_count: int
    any_oos_touched: bool
    any_locked_test_contamination: bool
    budget_check: StudyBudgetCheck

    def to_dict(self) -> dict[str, JsonValue]:
        """Return explicit accounting metadata for downstream governance gates."""

        return {
            "study_spec_id": self.study_spec_id,
            "variant_budget": self.variant_budget,
            "attempt_count": self.attempt_count,
            "observed_variant_count": self.observed_variant_count,
            "variant_attempt_count": self.variant_attempt_count,
            "variant_ids": list(self.variant_ids),
            "variant_counts": dict(self.variant_counts),
            "status_counts": dict(self.status_counts),
            "failed_count": self.failed_count,
            "abandoned_count": self.abandoned_count,
            "failed_or_abandoned_count": self.failed_or_abandoned_count,
            "oos_touched_count": self.oos_touched_count,
            "locked_test_contamination_count": self.locked_test_contamination_count,
            "any_oos_touched": self.any_oos_touched,
            "any_locked_test_contamination": self.any_locked_test_contamination,
            "budget_check": self.budget_check.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class TrialLedgerVariantSummary:
    """Trial-ledger variant roll-up derived from `TrialLedgerAccounting`."""

    variant_id: str
    attempt_count: int
    trial_ids: tuple[str, ...]
    statuses: tuple[TrialStatus, ...]

    def to_dict(self) -> dict[str, JsonValue]:
        """Return explicit variant-attempt metadata."""

        return {
            "variant_id": self.variant_id,
            "attempt_count": self.attempt_count,
            "trial_ids": list(self.trial_ids),
            "statuses": [status.value for status in self.statuses],
        }


def create_trial_ledger_record(
    *,
    alpha_spec_id: str,
    study_spec_id: str,
    run_id: str,
    variant_id: str,
    status: TrialStatus | str,
    parameters: dict[str, JsonValue],
    metrics_summary: dict[str, JsonValue],
    failure_reason: str | None,
    oos_touched_flag: bool,
    locked_test_contamination_flag: bool,
    code_hash: str,
    config_hash: str,
) -> TrialLedgerRecord:
    """Create a validated `TrialLedgerRecord` without running a study."""

    payload: dict[str, JsonValue] = {
        "alpha_spec_id": alpha_spec_id,
        "study_spec_id": study_spec_id,
        "run_id": run_id,
        "variant_id": variant_id,
        "status": _status_value(status),
        "parameters": dict(parameters),
        "metrics_summary": dict(metrics_summary),
        "failure_reason": failure_reason,
        "oos_touched_flag": oos_touched_flag,
        "locked_test_contamination_flag": locked_test_contamination_flag,
        "code_hash": code_hash,
        "config_hash": config_hash,
    }
    payload["trial_id"] = generate_trial_ledger_id(payload)
    return validate_trial_ledger_record(payload)


def generate_trial_ledger_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic TrialLedgerRecord ID from content fields."""

    mapping = _validate_id_components_present(payload)
    components = {
        field: _normalize_id_component(field, mapping[field])
        for field in TRIAL_LEDGER_ID_COMPONENT_FIELDS
    }
    return generate_governance_id(GovernanceIdKind.TRIAL_LEDGER_RECORD, components)


def validate_trial_ledger_record(payload: Mapping[str, Any]) -> TrialLedgerRecord:
    """Validate a `TrialLedgerRecord` mapping fail-closed and return a record."""

    mapping = validate_schema(
        payload,
        required_fields=TRIAL_LEDGER_NON_NULL_REQUIRED_FIELDS,
        field_types=TRIAL_LEDGER_FIELD_TYPES,
        allowed_fields=TRIAL_LEDGER_REQUIRED_FIELDS,
        object_name="TrialLedgerRecord",
    )

    issues: list[ValidationIssue] = []
    if "failure_reason" not in mapping:
        issues.append(
            ValidationIssue(
                field="failure_reason",
                code="missing_required_field",
                message="TrialLedgerRecord.failure_reason is required",
                expected="present explicit empty, null, or substantive reason",
                actual="missing",
            )
        )

    issues.extend(_validate_ids(mapping))
    status = _parse_status(mapping.get("status"), issues)
    issues.extend(_validate_text_field(mapping, "run_id", disallow_paths=True))
    issues.extend(_validate_text_field(mapping, "variant_id", disallow_paths=False))
    issues.extend(_validate_metadata_mapping(mapping, "parameters", allow_empty=False))
    issues.extend(_validate_metadata_mapping(mapping, "metrics_summary", allow_empty=True))
    if status is not None and "failure_reason" in mapping:
        issues.extend(_validate_failure_reason(mapping["failure_reason"], status))
    for field in ("code_hash", "config_hash"):
        issues.extend(_validate_hash_field(mapping, field))
    issues.extend(_validate_canonical_serializable(mapping))
    if not issues:
        expected_id = generate_trial_ledger_id(mapping)
        if mapping["trial_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="trial_id",
                    code="trial_id_mismatch",
                    message=(
                        "TrialLedgerRecord.trial_id must match deterministic "
                        "TrialLedgerRecord content"
                    ),
                    expected=expected_id,
                    actual=str(mapping["trial_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)

    assert status is not None
    return TrialLedgerRecord(
        trial_id=mapping["trial_id"],
        alpha_spec_id=mapping["alpha_spec_id"],
        study_spec_id=mapping["study_spec_id"],
        run_id=mapping["run_id"],
        variant_id=mapping["variant_id"],
        status=status,
        parameters=dict(mapping["parameters"]),
        metrics_summary=dict(mapping["metrics_summary"]),
        failure_reason=mapping["failure_reason"],
        oos_touched_flag=mapping["oos_touched_flag"],
        locked_test_contamination_flag=mapping["locked_test_contamination_flag"],
        code_hash=mapping["code_hash"],
        config_hash=mapping["config_hash"],
    )


def account_trial_ledger(
    records: Iterable[TrialLedgerRecord | Mapping[str, Any]],
    *,
    study_spec_id: str,
    variant_budget: int,
) -> TrialLedgerAccounting:
    """Aggregate all TrialLedger records for a study without dropping failures."""

    issues: list[ValidationIssue] = []
    try:
        validate_governance_id(study_spec_id, expected_kind=GovernanceIdKind.STUDY_SPEC)
    except GovernanceIdError as exc:
        issues.append(
            ValidationIssue(
                field="study_spec_id",
                code=exc.issue.code,
                message=exc.issue.message,
                expected=GovernanceIdKind.STUDY_SPEC.value,
                actual=str(exc.issue.value),
            )
        )
    try:
        budget_check_for_validation = evaluate_variant_budget(
            variant_budget,
            observed_count=0,
        )
    except GovernanceValidationError as exc:
        issues.extend(exc.issues)
        budget_check_for_validation = None

    if isinstance(records, Mapping) or isinstance(records, str) or records is None:
        issues.append(
            ValidationIssue(
                field="records",
                code="invalid_records_type",
                message="trial ledger accounting requires an iterable of records",
                expected="iterable of TrialLedgerRecord mappings",
                actual=type(records).__name__,
            )
        )
    if issues:
        raise GovernanceValidationError(issues)
    assert budget_check_for_validation is not None

    validated_records = _validate_records(records)
    study_records = [
        record for record in validated_records if record.study_spec_id == study_spec_id
    ]
    if not study_records:
        raise GovernanceValidationError(
            ValidationIssue(
                field="records",
                code="missing_trial_ledger_records",
                message="at least one TrialLedgerRecord is required for the study",
                expected="one or more matching TrialLedgerRecord entries",
                actual="0 matching records",
            )
        )

    variant_counts: dict[str, int] = {}
    status_counts = {status.value: 0 for status in TrialStatus}
    oos_touched_count = 0
    locked_test_contamination_count = 0
    for record in study_records:
        variant_counts[record.variant_id] = variant_counts.get(record.variant_id, 0) + 1
        status_counts[record.status.value] += 1
        if record.oos_touched_flag:
            oos_touched_count += 1
        if record.locked_test_contamination_flag:
            locked_test_contamination_count += 1

    variant_ids = tuple(sorted(variant_counts))
    failed_count = status_counts[TrialStatus.FAILED.value]
    abandoned_count = status_counts[TrialStatus.ABANDONED.value]
    observed_variant_count = len(variant_ids)
    budget_check = evaluate_variant_budget(variant_budget, observed_variant_count)
    return TrialLedgerAccounting(
        study_spec_id=study_spec_id,
        variant_budget=variant_budget,
        attempt_count=len(study_records),
        observed_variant_count=observed_variant_count,
        variant_attempt_count=len(study_records),
        variant_ids=variant_ids,
        variant_counts=dict(sorted(variant_counts.items())),
        status_counts=status_counts,
        failed_count=failed_count,
        abandoned_count=abandoned_count,
        failed_or_abandoned_count=failed_count + abandoned_count,
        oos_touched_count=oos_touched_count,
        locked_test_contamination_count=locked_test_contamination_count,
        any_oos_touched=oos_touched_count > 0,
        any_locked_test_contamination=locked_test_contamination_count > 0,
        budget_check=budget_check,
    )


def evaluate_trial_ledger_accounting(
    records: Iterable[TrialLedgerRecord | Mapping[str, Any]],
    *,
    study_spec_id: str,
    variant_budget: int,
) -> TrialLedgerAccounting:
    """Alias for pure TrialLedger variant and contamination accounting."""

    return account_trial_ledger(
        records,
        study_spec_id=study_spec_id,
        variant_budget=variant_budget,
    )


def summarize_trial_ledger_variants(
    records: Iterable[TrialLedgerRecord | Mapping[str, Any]],
    *,
    study_spec_id: str,
    variant_budget: int,
) -> tuple[TrialLedgerAccounting, tuple[TrialLedgerVariantSummary, ...]]:
    """Return accounting plus per-variant trial refs from the same validated input."""

    materialized_records = (
        records
        if isinstance(records, Mapping) or isinstance(records, str) or records is None
        else tuple(records)
    )
    accounting = account_trial_ledger(
        materialized_records,
        study_spec_id=study_spec_id,
        variant_budget=variant_budget,
    )
    validated_records = _validate_records(materialized_records)
    study_records = [
        record for record in validated_records if record.study_spec_id == study_spec_id
    ]
    grouped: dict[str, list[TrialLedgerRecord]] = {}
    for record in study_records:
        grouped.setdefault(record.variant_id, []).append(record)

    summaries: list[TrialLedgerVariantSummary] = []
    issues: list[ValidationIssue] = []
    for variant_id in accounting.variant_ids:
        variant_records = grouped.get(variant_id, [])
        attempt_count = accounting.variant_counts[variant_id]
        if len(variant_records) != attempt_count:
            issues.append(
                ValidationIssue(
                    field="variant_counts",
                    code="variant_accounting_diverged",
                    message=(
                        "TrialLedgerAccounting.variant_counts must match the "
                        "validated TrialLedgerRecord grouping"
                    ),
                    expected=str(attempt_count),
                    actual=str(len(variant_records)),
                )
            )
            continue
        ordered = tuple(sorted(variant_records, key=lambda record: record.trial_id))
        summaries.append(
            TrialLedgerVariantSummary(
                variant_id=variant_id,
                attempt_count=attempt_count,
                trial_ids=tuple(record.trial_id for record in ordered),
                statuses=tuple(record.status for record in ordered),
            )
        )
    if issues:
        raise GovernanceValidationError(issues)
    return accounting, tuple(summaries)


def _validate_id_components_present(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    mapping = require_mapping(payload, object_name="TrialLedgerRecord")
    issues: list[ValidationIssue] = []
    for field in TRIAL_LEDGER_ID_COMPONENT_FIELDS:
        if field not in mapping:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="missing_required_field",
                    message=f"TrialLedgerRecord.{field} is required",
                    expected="present ID component",
                    actual="missing",
                )
            )
        elif mapping[field] is None and field != "failure_reason":
            issues.append(
                ValidationIssue(
                    field=field,
                    code="null_required_field",
                    message=f"TrialLedgerRecord.{field} must not be null",
                    expected="present non-null ID component",
                    actual="NoneType",
                )
            )
    if issues:
        raise GovernanceValidationError(issues)
    return mapping


def _normalize_id_component(field: str, value: Any) -> JsonValue:
    if field == "status":
        return _status_value(value)
    if isinstance(value, TrialStatus):
        return value.value
    return cast(JsonValue, value)


def _validate_ids(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    id_checks = (
        ("trial_id", GovernanceIdKind.TRIAL_LEDGER_RECORD),
        ("alpha_spec_id", GovernanceIdKind.ALPHA_SPEC),
        ("study_spec_id", GovernanceIdKind.STUDY_SPEC),
    )
    for field, kind in id_checks:
        try:
            validate_governance_id(mapping[field], expected_kind=kind)
        except GovernanceIdError as exc:
            issues.append(
                ValidationIssue(
                    field=field,
                    code=exc.issue.code,
                    message=exc.issue.message,
                    expected=kind.value,
                    actual=str(exc.issue.value),
                )
            )
    return issues


def _parse_status(value: Any, issues: list[ValidationIssue]) -> TrialStatus | None:
    try:
        return TrialStatus(value)
    except ValueError:
        issues.append(
            ValidationIssue(
                field="status",
                code="invalid_trial_status",
                message="TrialLedgerRecord.status must be a declared TrialStatus",
                expected=" | ".join(status.value for status in TrialStatus),
                actual=str(value),
            )
        )
        return None


def _status_value(status: TrialStatus | str | Any) -> str:
    try:
        return TrialStatus(status).value
    except ValueError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="status",
                code="invalid_trial_status",
                message="TrialLedgerRecord.status must be a declared TrialStatus",
                expected=" | ".join(value.value for value in TrialStatus),
                actual=str(status),
            )
        ) from exc


def _validate_text_field(
    mapping: Mapping[str, Any],
    field: str,
    *,
    disallow_paths: bool,
) -> list[ValidationIssue]:
    value = mapping[field]
    normalized = _normalize_text(value)
    if normalized in _VAGUE_TEXT:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"TrialLedgerRecord.{field} must be explicit",
                expected="non-empty explicit string",
                actual=str(value),
            )
        ]
    if disallow_paths and ("/" in value or "\\" in value or normalized == "runs"):
        return [
            ValidationIssue(
                field=field,
                code="run_id_must_not_be_path",
                message="TrialLedgerRecord.run_id must be an opaque reference, not a path",
                expected="opaque non-path run reference",
                actual=value,
            )
        ]
    return []


def _validate_metadata_mapping(
    mapping: Mapping[str, Any],
    field: str,
    *,
    allow_empty: bool,
) -> list[ValidationIssue]:
    value = mapping[field]
    if not value:
        if allow_empty:
            return []
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"TrialLedgerRecord.{field} must contain explicit metadata",
                expected="non-empty mapping",
                actual="empty mapping",
            )
        ]

    issues: list[ValidationIssue] = []
    for key, item in value.items():
        if not isinstance(key, str) or _normalize_text(key) in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_metadata_key",
                    message=f"TrialLedgerRecord.{field} keys must be explicit strings",
                    expected="non-empty explicit string key",
                    actual=str(key),
                )
            )
        issues.extend(_validate_substantive_value(item, field=f"{field}.{key}"))
    return issues


def _validate_substantive_value(value: Any, *, field: str) -> list[ValidationIssue]:
    if value is None:
        return [
            ValidationIssue(
                field=field,
                code="null_required_field",
                message=f"TrialLedgerRecord.{field} must not be null",
                expected="explicit metadata value",
                actual="NoneType",
            )
        ]
    if isinstance(value, str):
        if _normalize_text(value) in _VAGUE_TEXT:
            return [
                ValidationIssue(
                    field=field,
                    code="vague_required_field",
                    message=f"TrialLedgerRecord.{field} must be explicit, not vague",
                    expected="substantive explicit value",
                    actual=value,
                )
            ]
        return []
    if isinstance(value, list):
        if not value:
            return [
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"TrialLedgerRecord.{field} must not be an empty list",
                    expected="non-empty value",
                    actual="empty list",
                )
            ]
        issues: list[ValidationIssue] = []
        for index, item in enumerate(value):
            issues.extend(_validate_substantive_value(item, field=f"{field}[{index}]"))
        return issues
    if isinstance(value, dict):
        if not value:
            return [
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"TrialLedgerRecord.{field} must not be an empty mapping",
                    expected="non-empty value",
                    actual="empty mapping",
                )
            ]
        issues = []
        for key, item in value.items():
            if not isinstance(key, str) or _normalize_text(key) in _VAGUE_TEXT:
                issues.append(
                    ValidationIssue(
                        field=field,
                        code="invalid_metadata_key",
                        message=(f"TrialLedgerRecord.{field} nested keys must be explicit strings"),
                        expected="non-empty explicit string key",
                        actual=str(key),
                    )
                )
            issues.extend(_validate_substantive_value(item, field=f"{field}.{key}"))
        return issues
    return []


def _validate_failure_reason(value: str | None, status: TrialStatus) -> list[ValidationIssue]:
    if status in FAILED_TRIAL_STATUSES:
        if value is None or _normalize_text(value) in _VAGUE_TEXT:
            return [
                ValidationIssue(
                    field="failure_reason",
                    code="failure_reason_required",
                    message=(
                        "TrialLedgerRecord.failure_reason is required for failed "
                        "or abandoned trials"
                    ),
                    expected="substantive failure reason",
                    actual="null or empty",
                )
            ]
        return []

    if value is None or _normalize_text(value) == "":
        return []
    return [
        ValidationIssue(
            field="failure_reason",
            code="failure_reason_must_be_empty",
            message=(
                "TrialLedgerRecord.failure_reason must be empty or null for non-failed statuses"
            ),
            expected="None or empty string",
            actual=str(value),
        )
    ]


def _validate_hash_field(mapping: Mapping[str, Any], field: str) -> list[ValidationIssue]:
    value = mapping[field]
    if _SHA256_HEX_PATTERN.fullmatch(value) is not None:
        return []
    return [
        ValidationIssue(
            field=field,
            code="invalid_content_hash",
            message=f"TrialLedgerRecord.{field} must be a lowercase SHA-256 hex digest",
            expected="64 lowercase hexadecimal characters",
            actual=value,
        )
    ]


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize(
            {
                field: _normalize_id_component(field, mapping[field])
                for field in TRIAL_LEDGER_REQUIRED_FIELDS
                if field in mapping
            }
        )
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible TrialLedgerRecord",
                actual=exc.issue.path,
            )
        ]
    return []


def _validate_records(
    records: Iterable[TrialLedgerRecord | Mapping[str, Any]],
) -> list[TrialLedgerRecord]:
    validated: list[TrialLedgerRecord] = []
    for index, record in enumerate(records):
        if isinstance(record, TrialLedgerRecord):
            validated.append(validate_trial_ledger_record(record.to_dict()))
            continue
        if isinstance(record, Mapping):
            validated.append(validate_trial_ledger_record(record))
            continue
        raise GovernanceValidationError(
            ValidationIssue(
                field=f"records[{index}]",
                code="invalid_record_type",
                message="trial ledger accounting accepts only TrialLedgerRecord mappings",
                expected="TrialLedgerRecord or mapping",
                actual=type(record).__name__,
            )
        )
    return validated


def _normalize_text(value: object) -> str:
    if isinstance(value, str):
        return " ".join(value.strip().lower().split())
    return str(value).strip().lower()


__all__ = [
    "FAILED_TRIAL_STATUSES",
    "TRIAL_LEDGER_ID_COMPONENT_FIELDS",
    "TRIAL_LEDGER_REQUIRED_FIELDS",
    "TrialLedgerAccounting",
    "TrialLedgerRecord",
    "TrialLedgerVariantSummary",
    "TrialStatus",
    "account_trial_ledger",
    "create_trial_ledger_record",
    "evaluate_trial_ledger_accounting",
    "generate_trial_ledger_id",
    "summarize_trial_ledger_variants",
    "validate_trial_ledger_record",
]
