"""First-class VariantLedger records, family budgets, and fail-closed hook."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

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
    StudyBudgetStatus,
    StudySpec,
    validate_study_spec,
)
from alpha_system.governance.trial_ledger import (
    TrialLedgerRecord,
    TrialStatus,
    summarize_trial_ledger_variants,
)
from alpha_system.governance.validation import (
    ExpectedType,
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
    validate_schema,
)

VARIANT_LEDGER_RECORD_REQUIRED_FIELDS = (
    "variant_id",
    "alpha_spec_id",
    "study_spec_id",
    "family_id",
    "attempt_count",
    "trial_ids",
    "status",
    "created_at",
)
VARIANT_LEDGER_RECORD_FIELD_TYPES: dict[str, ExpectedType] = {
    "variant_id": str,
    "alpha_spec_id": str,
    "study_spec_id": str,
    "family_id": str,
    "attempt_count": int,
    "trial_ids": list,
    "status": (str, TrialStatus),
    "created_at": str,
}
BUDGET_AMENDMENT_RECORD_REQUIRED_FIELDS = (
    "amendment_id",
    "budget_type",
    "target_id",
    "prior_budget",
    "new_budget",
    "actor",
    "rationale",
    "created_at",
)
BUDGET_AMENDMENT_RECORD_ID_COMPONENT_FIELDS = tuple(
    field for field in BUDGET_AMENDMENT_RECORD_REQUIRED_FIELDS if field != "amendment_id"
)
BUDGET_AMENDMENT_RECORD_FIELD_TYPES: dict[str, ExpectedType] = {
    "amendment_id": str,
    "budget_type": str,
    "target_id": str,
    "prior_budget": int,
    "new_budget": int,
    "actor": str,
    "rationale": str,
    "created_at": str,
}
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
    "unbounded",
    "unlimited",
}


class VariantLedgerStatus(StrEnum):
    """Closed status values aligned with TrialLedger status conventions."""

    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"


class BudgetAmendmentType(StrEnum):
    """Budget scopes an amendment may authorize."""

    VARIANT = "VARIANT"
    FAMILY = "FAMILY"


@dataclass(frozen=True, slots=True)
class VariantLedgerRecord:
    """Validated platform-cumulative variant exposure record."""

    variant_id: str
    alpha_spec_id: str
    study_spec_id: str
    family_id: str
    attempt_count: int
    trial_ids: tuple[str, ...]
    status: VariantLedgerStatus
    created_at: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> VariantLedgerRecord:
        """Build a `VariantLedgerRecord` from a mapping after validation."""

        return validate_variant_ledger_record(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> VariantLedgerRecord:
        """Deserialize canonical JSON and validate the resulting record."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="VariantLedgerRecord")
        return validate_variant_ledger_record(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "variant_id": self.variant_id,
            "alpha_spec_id": self.alpha_spec_id,
            "study_spec_id": self.study_spec_id,
            "family_id": self.family_id,
            "attempt_count": self.attempt_count,
            "trial_ids": list(self.trial_ids),
            "status": self.status.value,
            "created_at": self.created_at,
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated record through the canonical primitive."""

        return canonical_serialize(self.to_dict())


@dataclass(frozen=True, slots=True)
class BudgetAmendmentRecord:
    """Pre-declared provenance record authorizing a bounded budget increase."""

    amendment_id: str
    budget_type: BudgetAmendmentType
    target_id: str
    prior_budget: int
    new_budget: int
    actor: str
    rationale: str
    created_at: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> BudgetAmendmentRecord:
        """Build a `BudgetAmendmentRecord` from a mapping after validation."""

        return validate_budget_amendment_record(payload)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "amendment_id": self.amendment_id,
            "budget_type": self.budget_type.value,
            "target_id": self.target_id,
            "prior_budget": self.prior_budget,
            "new_budget": self.new_budget,
            "actor": self.actor,
            "rationale": self.rationale,
            "created_at": self.created_at,
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated record through the canonical primitive."""

        return canonical_serialize(self.to_dict())


@dataclass(frozen=True, slots=True)
class FamilyBudgetCheck:
    """Pure metadata result for family-wide observed variants versus budget."""

    family_id: str
    family_budget: int
    observed_count: int
    status: StudyBudgetStatus
    variants_remaining: int
    overrun_by: int
    issues: tuple[ValidationIssue, ...] = ()

    @property
    def respected(self) -> bool:
        """Return true only when observed variants are within the family cap."""

        return self.status is StudyBudgetStatus.RESPECTED

    @property
    def overrun(self) -> bool:
        """Return true only when observed variants exceed the family cap."""

        return self.status is StudyBudgetStatus.OVERRUN

    def to_dict(self) -> dict[str, JsonValue]:
        """Return explicit family-budget accounting metadata."""

        return {
            "family_id": self.family_id,
            "family_budget": self.family_budget,
            "observed_count": self.observed_count,
            "status": self.status.value,
            "respected": self.respected,
            "overrun": self.overrun,
            "variants_remaining": self.variants_remaining,
            "overrun_by": self.overrun_by,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True, slots=True)
class VariantBudgetValidationResult:
    """Accepted result for entry/promotion variant-budget enforcement."""

    ledger_path: str
    study_budget_check: StudyBudgetCheck
    family_budget_check: FamilyBudgetCheck | None
    variant_records: tuple[VariantLedgerRecord, ...]
    amendments_applied: tuple[str, ...] = ()

    @property
    def amended(self) -> bool:
        """Return true when at least one budget amendment authorized an overrun."""

        return bool(self.amendments_applied)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return explicit hook metadata."""

        return {
            "ledger_path": self.ledger_path,
            "study_budget_check": self.study_budget_check.to_dict(),
            "family_budget_check": (
                self.family_budget_check.to_dict()
                if self.family_budget_check is not None
                else None
            ),
            "variant_records": [record.to_dict() for record in self.variant_records],
            "amended": self.amended,
            "amendments_applied": list(self.amendments_applied),
        }


class VariantLedger:
    """Append-friendly JSONL persistence for validated VariantLedger records."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = resolve_variant_ledger_path(path)

    def load_records(self) -> tuple[VariantLedgerRecord, ...]:
        """Read all JSONL records fail-closed from the ledger path."""

        _require_existing_file(self.path)
        records: list[VariantLedgerRecord] = []
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="variant_ledger_path",
                    code="variant_ledger_read_failed",
                    message="VariantLedger path could not be read",
                    expected="readable text JSONL ledger",
                    actual=f"{self.path}: {exc}",
                )
            ) from exc
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                value = deserialize(line)
                mapping = require_mapping(value, object_name="VariantLedgerRecord")
                records.append(validate_variant_ledger_record(mapping))
            except (GovernanceSerializationError, GovernanceValidationError) as exc:
                raise GovernanceValidationError(
                    ValidationIssue(
                        field=f"variant_ledger_path:{line_number}",
                        code="invalid_variant_ledger_row",
                        message="VariantLedger row is not a valid canonical record",
                        expected="canonical VariantLedgerRecord JSON line",
                        actual=str(exc),
                    )
                ) from exc
        return tuple(records)

    def require_writable(self) -> None:
        """Fail closed unless the ledger exists and can be appended to."""

        _require_existing_file(self.path)
        _require_writable_file(self.path)

    def append_records(self, records: Iterable[VariantLedgerRecord]) -> tuple[VariantLedgerRecord, ...]:
        """Append records not already represented by variant/study/trial key."""

        existing = self.load_records()
        self.require_writable()
        existing_keys = {_record_key(record) for record in existing}
        to_append = tuple(record for record in records if _record_key(record) not in existing_keys)
        if not to_append:
            return ()
        try:
            with self.path.open("a", encoding="utf-8") as handle:
                for record in to_append:
                    handle.write(record.to_canonical_json())
                    handle.write("\n")
        except OSError as exc:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="variant_ledger_path",
                    code="variant_ledger_append_failed",
                    message="VariantLedger path could not be appended",
                    expected="appendable text JSONL ledger",
                    actual=f"{self.path}: {exc}",
                )
            ) from exc
        return to_append

    def family_budget_check(self, *, family_id: str, family_budget: int) -> FamilyBudgetCheck:
        """Evaluate family budget using the current ledger contents."""

        return evaluate_family_budget(
            family_id=family_id,
            family_budget=family_budget,
            records=self.load_records(),
        )

    def summary(self) -> dict[str, JsonValue]:
        """Return a value-free summary of ledger exposure by family."""

        records = self.load_records()
        families: dict[str, dict[str, Any]] = {}
        for record in records:
            item = families.setdefault(
                record.family_id,
                {
                    "variant_exposure_keys": set(),
                    "variant_ids": set(),
                    "study_spec_ids": set(),
                    "attempt_count": 0,
                    "record_count": 0,
                },
            )
            item["variant_exposure_keys"].add(_family_exposure_key(record))
            item["variant_ids"].add(record.variant_id)
            item["study_spec_ids"].add(record.study_spec_id)
            item["attempt_count"] += record.attempt_count
            item["record_count"] += 1
        family_payload = {
            family_id: {
                "observed_variant_count": len(values["variant_exposure_keys"]),
                "attempt_count": int(values["attempt_count"]),
                "record_count": int(values["record_count"]),
                "study_spec_ids": sorted(values["study_spec_ids"]),
                "variant_ids": sorted(values["variant_ids"]),
                "variant_exposure_keys": [
                    f"{study_spec_id}:{variant_id}"
                    for study_spec_id, variant_id in sorted(values["variant_exposure_keys"])
                ],
            }
            for family_id, values in sorted(families.items())
        }
        return {
            "ledger_path": str(self.path),
            "record_count": len(records),
            "family_count": len(family_payload),
            "families": family_payload,
        }


def resolve_variant_ledger_path(path: str | Path | None = None) -> Path:
    """Resolve the explicitly supplied ledger path fail-closed."""

    if path is None or _normalize_text(path) in _VAGUE_TEXT:
        raise GovernanceValidationError(
            ValidationIssue(
                field="variant_ledger_path",
                code="missing_variant_ledger_path",
                message="VariantLedger path is required for budget enforcement",
                expected="explicit path to an existing writable VariantLedger JSONL file",
                actual="missing",
            )
        )
    return Path(path).expanduser()


def validate_variant_ledger_record(payload: Mapping[str, Any]) -> VariantLedgerRecord:
    """Validate a `VariantLedgerRecord` mapping fail-closed and return a record."""

    mapping = validate_schema(
        payload,
        required_fields=VARIANT_LEDGER_RECORD_REQUIRED_FIELDS,
        field_types=VARIANT_LEDGER_RECORD_FIELD_TYPES,
        allowed_fields=VARIANT_LEDGER_RECORD_REQUIRED_FIELDS,
        object_name="VariantLedgerRecord",
    )

    issues: list[ValidationIssue] = []
    issues.extend(_validate_governance_ids(mapping))
    issues.extend(_validate_text_field(mapping, "variant_id"))
    issues.extend(_validate_text_field(mapping, "family_id"))
    issues.extend(_validate_attempt_count(mapping["attempt_count"]))
    status = _parse_variant_status(mapping["status"], issues)
    trial_ids = _validate_trial_ids(mapping["trial_ids"], issues)
    issues.extend(_validate_utc_timestamp(mapping["created_at"], field="created_at"))
    if trial_ids and mapping["attempt_count"] != len(trial_ids):
        issues.append(
            ValidationIssue(
                field="attempt_count",
                code="attempt_count_trial_ids_mismatch",
                message="VariantLedgerRecord.attempt_count must match trial_ids length",
                expected=str(len(trial_ids)),
                actual=str(mapping["attempt_count"]),
            )
        )
    issues.extend(_validate_variant_record_serializable(mapping))
    if issues:
        raise GovernanceValidationError(issues)

    assert status is not None
    assert trial_ids is not None
    return VariantLedgerRecord(
        variant_id=mapping["variant_id"],
        alpha_spec_id=mapping["alpha_spec_id"],
        study_spec_id=mapping["study_spec_id"],
        family_id=mapping["family_id"],
        attempt_count=mapping["attempt_count"],
        trial_ids=trial_ids,
        status=status,
        created_at=mapping["created_at"],
    )


def create_budget_amendment_record(
    *,
    budget_type: BudgetAmendmentType | str,
    target_id: str,
    prior_budget: int,
    new_budget: int,
    actor: str,
    rationale: str,
    created_at: str,
) -> BudgetAmendmentRecord:
    """Create a validated budget-amendment record with a deterministic ID."""

    payload: dict[str, JsonValue] = {
        "budget_type": BudgetAmendmentType(budget_type).value,
        "target_id": target_id,
        "prior_budget": prior_budget,
        "new_budget": new_budget,
        "actor": actor,
        "rationale": rationale,
        "created_at": created_at,
    }
    payload["amendment_id"] = generate_budget_amendment_id(payload)
    return validate_budget_amendment_record(payload)


def generate_budget_amendment_id(payload: Mapping[str, Any]) -> str:
    """Generate a deterministic BudgetAmendmentRecord ID from content fields."""

    mapping = require_mapping(payload, object_name="BudgetAmendmentRecord")
    components = {
        field: _amendment_id_component(field, mapping[field])
        for field in BUDGET_AMENDMENT_RECORD_ID_COMPONENT_FIELDS
        if field in mapping
    }
    return generate_governance_id(GovernanceIdKind.BUDGET_AMENDMENT_RECORD, components)


def validate_budget_amendment_record(payload: Mapping[str, Any]) -> BudgetAmendmentRecord:
    """Validate a provenance-carrying budget amendment fail-closed."""

    mapping = validate_schema(
        payload,
        required_fields=BUDGET_AMENDMENT_RECORD_REQUIRED_FIELDS,
        field_types=BUDGET_AMENDMENT_RECORD_FIELD_TYPES,
        allowed_fields=BUDGET_AMENDMENT_RECORD_REQUIRED_FIELDS,
        object_name="BudgetAmendmentRecord",
    )

    issues: list[ValidationIssue] = []
    try:
        validate_governance_id(
            mapping["amendment_id"],
            expected_kind=GovernanceIdKind.BUDGET_AMENDMENT_RECORD,
        )
    except GovernanceIdError as exc:
        issues.append(
            ValidationIssue(
                field="amendment_id",
                code=exc.issue.code,
                message=exc.issue.message,
                expected=GovernanceIdKind.BUDGET_AMENDMENT_RECORD.value,
                actual=str(exc.issue.value),
            )
        )

    budget_type = _parse_budget_type(mapping["budget_type"], issues)
    if budget_type is BudgetAmendmentType.VARIANT:
        try:
            validate_governance_id(mapping["target_id"], expected_kind=GovernanceIdKind.STUDY_SPEC)
        except GovernanceIdError as exc:
            issues.append(
                ValidationIssue(
                    field="target_id",
                    code=exc.issue.code,
                    message=exc.issue.message,
                    expected=GovernanceIdKind.STUDY_SPEC.value,
                    actual=str(exc.issue.value),
                )
            )
    elif budget_type is BudgetAmendmentType.FAMILY:
        issues.extend(_validate_text_value(mapping["target_id"], field="target_id"))

    issues.extend(_validate_positive_budget(mapping["prior_budget"], field="prior_budget"))
    issues.extend(_validate_positive_budget(mapping["new_budget"], field="new_budget"))
    if (
        type(mapping["prior_budget"]) is int
        and type(mapping["new_budget"]) is int
        and mapping["new_budget"] <= mapping["prior_budget"]
    ):
        issues.append(
            ValidationIssue(
                field="new_budget",
                code="budget_amendment_not_increasing",
                message="BudgetAmendmentRecord.new_budget must exceed prior_budget",
                expected=f"> {mapping['prior_budget']}",
                actual=str(mapping["new_budget"]),
            )
        )
    issues.extend(_validate_text_value(mapping["actor"], field="actor"))
    issues.extend(_validate_text_value(mapping["rationale"], field="rationale"))
    issues.extend(_validate_utc_timestamp(mapping["created_at"], field="created_at"))
    issues.extend(_validate_amendment_serializable(mapping))
    if not issues:
        expected_id = generate_budget_amendment_id(mapping)
        if mapping["amendment_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="amendment_id",
                    code="budget_amendment_id_mismatch",
                    message=(
                        "BudgetAmendmentRecord.amendment_id must match deterministic "
                        "BudgetAmendmentRecord content"
                    ),
                    expected=expected_id,
                    actual=str(mapping["amendment_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)
    assert budget_type is not None
    return BudgetAmendmentRecord(
        amendment_id=mapping["amendment_id"],
        budget_type=budget_type,
        target_id=mapping["target_id"],
        prior_budget=mapping["prior_budget"],
        new_budget=mapping["new_budget"],
        actor=mapping["actor"],
        rationale=mapping["rationale"],
        created_at=mapping["created_at"],
    )


def variant_ledger_records_from_trial_ledger(
    records: Iterable[TrialLedgerRecord | Mapping[str, Any]],
    *,
    study_spec: StudySpec | Mapping[str, Any],
    family_id: str,
    created_at: str | None = None,
) -> tuple[StudyBudgetCheck, tuple[VariantLedgerRecord, ...]]:
    """Derive VariantLedger records from the existing TrialLedgerAccounting surface."""

    active_study_spec = _coerce_study_spec(study_spec)
    active_family_id = _require_family_id(family_id)
    active_created_at = created_at or utc_now_iso()
    _raise_if_issues(_validate_utc_timestamp(active_created_at, field="created_at"))
    accounting, summaries = summarize_trial_ledger_variants(
        records,
        study_spec_id=active_study_spec.study_spec_id,
        variant_budget=active_study_spec.variant_budget,
    )
    variant_records = tuple(
        validate_variant_ledger_record(
            {
                "variant_id": summary.variant_id,
                "alpha_spec_id": active_study_spec.alpha_spec_id,
                "study_spec_id": active_study_spec.study_spec_id,
                "family_id": active_family_id,
                "attempt_count": summary.attempt_count,
                "trial_ids": list(summary.trial_ids),
                "status": _rollup_status(summary.statuses).value,
                "created_at": active_created_at,
            }
        )
        for summary in summaries
    )
    return accounting.budget_check, variant_records


def evaluate_family_budget(
    *,
    family_id: str,
    family_budget: int,
    records: Iterable[VariantLedgerRecord | Mapping[str, Any]],
) -> FamilyBudgetCheck:
    """Roll up observed variants across all studies sharing a family ID."""

    active_family_id = _require_family_id(family_id)
    issues = _validate_positive_budget(family_budget, field="family_budget")
    if issues:
        raise GovernanceValidationError(issues)

    validated_records = _validate_variant_records(records)
    observed_variant_keys = {
        _family_exposure_key(record)
        for record in validated_records
        if record.family_id == active_family_id
    }
    observed_count = len(observed_variant_keys)
    if observed_count <= family_budget:
        return FamilyBudgetCheck(
            family_id=active_family_id,
            family_budget=family_budget,
            observed_count=observed_count,
            status=StudyBudgetStatus.RESPECTED,
            variants_remaining=family_budget - observed_count,
            overrun_by=0,
        )
    return FamilyBudgetCheck(
        family_id=active_family_id,
        family_budget=family_budget,
        observed_count=observed_count,
        status=StudyBudgetStatus.OVERRUN,
        variants_remaining=0,
        overrun_by=observed_count - family_budget,
    )


def validate_variant_and_family_budget(
    study_spec: StudySpec | Mapping[str, Any] | None,
    *,
    trial_ledger_records: Iterable[TrialLedgerRecord | Mapping[str, Any]],
    family_id: str | None,
    variant_ledger_path: str | Path | None,
    amendments: Iterable[BudgetAmendmentRecord | Mapping[str, Any]] = (),
    created_at: str | None = None,
    persist: bool = True,
    require_recorded: bool = False,
) -> VariantBudgetValidationResult:
    """Fail closed unless variant and optional family budgets are enforceable."""

    active_study_spec = _coerce_study_spec(study_spec)
    active_family_id = _require_family_id(family_id)
    ledger = VariantLedger(variant_ledger_path)
    existing_records = ledger.load_records()
    ledger.require_writable()
    amendment_records = _coerce_amendments(amendments)
    study_budget_check, variant_records = variant_ledger_records_from_trial_ledger(
        trial_ledger_records,
        study_spec=active_study_spec,
        family_id=active_family_id,
        created_at=created_at,
    )

    issues: list[ValidationIssue] = []
    if require_recorded:
        existing_keys = {_record_key(record) for record in existing_records}
        missing = [
            record for record in variant_records if _record_key(record) not in existing_keys
        ]
        if missing:
            issues.append(
                ValidationIssue(
                    field="variant_ledger_records",
                    code="variant_ledger_missing_records",
                    message="VariantLedger must already contain records for evidence trials",
                    expected=", ".join(record.variant_id for record in variant_records),
                    actual=", ".join(record.variant_id for record in missing),
                )
            )

    amendments_applied: list[str] = []
    if study_budget_check.overrun:
        amendment = _find_covering_amendment(
            amendment_records,
            budget_type=BudgetAmendmentType.VARIANT,
            target_id=active_study_spec.study_spec_id,
            prior_budget=active_study_spec.variant_budget,
            required_budget=study_budget_check.observed_count,
            variant_records=variant_records,
        )
        if amendment is None:
            issues.append(
                ValidationIssue(
                    field="variant_budget",
                    code="variant_budget_overrun",
                    message="study variant budget is overrun without a pre-declared amendment",
                    expected=(
                        f"observed variants <= {active_study_spec.variant_budget} "
                        "or valid BudgetAmendmentRecord"
                    ),
                    actual=(
                        f"observed={study_budget_check.observed_count}; "
                        f"overrun_by={study_budget_check.overrun_by}"
                    ),
                )
            )
        else:
            amendments_applied.append(amendment.amendment_id)

    family_budget_check = None
    if active_study_spec.family_budget is not None:
        combined_records = tuple(_dedupe_records((*existing_records, *variant_records)))
        family_budget_check = evaluate_family_budget(
            family_id=active_family_id,
            family_budget=active_study_spec.family_budget,
            records=combined_records,
        )
        if family_budget_check.overrun:
            amendment = _find_covering_amendment(
                amendment_records,
                budget_type=BudgetAmendmentType.FAMILY,
                target_id=active_family_id,
                prior_budget=active_study_spec.family_budget,
                required_budget=family_budget_check.observed_count,
                variant_records=variant_records,
            )
            if amendment is None:
                issues.append(
                    ValidationIssue(
                        field="family_budget",
                        code="family_budget_overrun",
                        message="family variant budget is overrun without a pre-declared amendment",
                        expected=(
                            f"observed family variants <= {active_study_spec.family_budget} "
                            "or valid BudgetAmendmentRecord"
                        ),
                        actual=(
                            f"observed={family_budget_check.observed_count}; "
                            f"overrun_by={family_budget_check.overrun_by}"
                        ),
                    )
                )
            else:
                amendments_applied.append(amendment.amendment_id)

    if issues:
        raise GovernanceValidationError(issues)

    if persist:
        ledger.append_records(variant_records)
    return VariantBudgetValidationResult(
        ledger_path=str(ledger.path),
        study_budget_check=study_budget_check,
        family_budget_check=family_budget_check,
        variant_records=variant_records,
        amendments_applied=tuple(dict.fromkeys(amendments_applied)),
    )


def utc_now_iso() -> str:
    """Return a second-resolution UTC ISO-8601 timestamp ending in Z."""

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _coerce_study_spec(value: StudySpec | Mapping[str, Any] | None) -> StudySpec:
    if value is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="study_spec",
                code="missing_study_spec",
                message="valid StudySpec is required for variant-budget enforcement",
                expected="validated StudySpec",
                actual="missing",
            )
        )
    if isinstance(value, StudySpec):
        return validate_study_spec(value.to_dict())
    if isinstance(value, Mapping):
        return validate_study_spec(value)
    raise GovernanceValidationError(
        ValidationIssue(
            field="study_spec",
            code="invalid_study_spec_type",
            message="study_spec must be a StudySpec or mapping",
            expected="StudySpec or mapping",
            actual=type(value).__name__,
        )
    )


def _coerce_amendments(
    values: Iterable[BudgetAmendmentRecord | Mapping[str, Any]],
) -> tuple[BudgetAmendmentRecord, ...]:
    if isinstance(values, Mapping) or isinstance(values, str) or values is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="amendments",
                code="invalid_amendments_type",
                message="budget amendments must be an iterable of records",
                expected="iterable of BudgetAmendmentRecord or mapping",
                actual=type(values).__name__,
            )
        )
    result: list[BudgetAmendmentRecord] = []
    for item in values:
        if isinstance(item, BudgetAmendmentRecord):
            result.append(validate_budget_amendment_record(item.to_dict()))
        elif isinstance(item, Mapping):
            result.append(validate_budget_amendment_record(item))
        else:
            raise GovernanceValidationError(
                ValidationIssue(
                    field="amendments",
                    code="invalid_amendment_record_type",
                    message="budget amendments must be records or mappings",
                    expected="BudgetAmendmentRecord or mapping",
                    actual=type(item).__name__,
                )
            )
    return tuple(result)


def _validate_governance_ids(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    id_checks = (
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


def _validate_text_field(mapping: Mapping[str, Any], field: str) -> list[ValidationIssue]:
    return _validate_text_value(mapping[field], field=field)


def _validate_text_value(value: object, *, field: str) -> list[ValidationIssue]:
    if not isinstance(value, str) or _normalize_text(value) in _VAGUE_TEXT:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"{field} must be an explicit non-empty string",
                expected="non-empty explicit string",
                actual=str(value),
            )
        ]
    return []


def _require_family_id(value: str | None) -> str:
    issues = _validate_text_value(value, field="family_id")
    if issues:
        raise GovernanceValidationError(issues)
    assert isinstance(value, str)
    return value


def _validate_attempt_count(value: int) -> list[ValidationIssue]:
    if type(value) is not int:
        return [
            ValidationIssue(
                field="attempt_count",
                code="invalid_attempt_count_type",
                message="VariantLedgerRecord.attempt_count must be an exact integer",
                expected="positive int",
                actual=type(value).__name__,
            )
        ]
    if value <= 0:
        return [
            ValidationIssue(
                field="attempt_count",
                code="invalid_attempt_count",
                message="VariantLedgerRecord.attempt_count must be positive",
                expected="positive int",
                actual=str(value),
            )
        ]
    return []


def _validate_positive_budget(value: int, *, field: str) -> list[ValidationIssue]:
    if type(value) is not int:
        return [
            ValidationIssue(
                field=field,
                code=f"invalid_{field}_type",
                message=f"{field} must be an exact integer",
                expected="positive int",
                actual=type(value).__name__,
            )
        ]
    if value <= 0:
        return [
            ValidationIssue(
                field=field,
                code=f"invalid_{field}",
                message=f"{field} must be positive",
                expected="positive int",
                actual=str(value),
            )
        ]
    return []


def _parse_variant_status(value: object, issues: list[ValidationIssue]) -> VariantLedgerStatus | None:
    try:
        return VariantLedgerStatus(value)
    except ValueError:
        issues.append(
            ValidationIssue(
                field="status",
                code="invalid_variant_ledger_status",
                message="VariantLedgerRecord.status must be declared",
                expected=" | ".join(status.value for status in VariantLedgerStatus),
                actual=str(value),
            )
        )
        return None


def _parse_budget_type(value: object, issues: list[ValidationIssue]) -> BudgetAmendmentType | None:
    try:
        return BudgetAmendmentType(value)
    except ValueError:
        issues.append(
            ValidationIssue(
                field="budget_type",
                code="invalid_budget_amendment_type",
                message="BudgetAmendmentRecord.budget_type must be declared",
                expected=" | ".join(item.value for item in BudgetAmendmentType),
                actual=str(value),
            )
        )
        return None


def _validate_trial_ids(values: list[Any], issues: list[ValidationIssue]) -> tuple[str, ...] | None:
    if not values:
        issues.append(
            ValidationIssue(
                field="trial_ids",
                code="empty_required_field",
                message="VariantLedgerRecord.trial_ids must contain at least one trial ID",
                expected="non-empty list of TrialLedgerRecord IDs",
                actual="empty",
            )
        )
        return None
    seen: set[str] = set()
    trial_ids: list[str] = []
    for index, value in enumerate(values):
        field = f"trial_ids[{index}]"
        if not isinstance(value, str):
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_trial_id_type",
                    message="VariantLedgerRecord.trial_ids entries must be strings",
                    expected="TrialLedgerRecord ID string",
                    actual=type(value).__name__,
                )
            )
            continue
        try:
            validate_governance_id(value, expected_kind=GovernanceIdKind.TRIAL_LEDGER_RECORD)
        except GovernanceIdError as exc:
            issues.append(
                ValidationIssue(
                    field=field,
                    code=exc.issue.code,
                    message=exc.issue.message,
                    expected=GovernanceIdKind.TRIAL_LEDGER_RECORD.value,
                    actual=str(exc.issue.value),
                )
            )
            continue
        if value in seen:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="duplicate_trial_id",
                    message="VariantLedgerRecord.trial_ids must be unique",
                    expected="unique trial IDs",
                    actual=value,
                )
            )
        seen.add(value)
        trial_ids.append(value)
    return tuple(trial_ids)


def _validate_utc_timestamp(value: object, *, field: str) -> list[ValidationIssue]:
    if not isinstance(value, str) or not value.endswith("Z"):
        return [
            ValidationIssue(
                field=field,
                code="invalid_utc_timestamp",
                message=f"{field} must be an ISO-8601 UTC timestamp ending in Z",
                expected="YYYY-MM-DDTHH:MM:SSZ",
                actual=str(value),
            )
        ]
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return [
            ValidationIssue(
                field=field,
                code="invalid_utc_timestamp",
                message=f"{field} must be a parseable ISO-8601 UTC timestamp",
                expected="YYYY-MM-DDTHH:MM:SSZ",
                actual=value,
            )
        ]
    if parsed.tzinfo is None or parsed.utcoffset() != datetime.now(UTC).utcoffset():
        return [
            ValidationIssue(
                field=field,
                code="invalid_utc_timestamp",
                message=f"{field} must use UTC timezone",
                expected="UTC timestamp ending in Z",
                actual=value,
            )
        ]
    return []


def _utc_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _validate_variant_record_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize(
            {
                field: _variant_record_component(field, mapping[field])
                for field in VARIANT_LEDGER_RECORD_REQUIRED_FIELDS
            }
        )
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible VariantLedgerRecord",
                actual=exc.issue.path,
            )
        ]
    return []


def _validate_amendment_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize(
            {
                field: _amendment_id_component(field, mapping[field])
                for field in BUDGET_AMENDMENT_RECORD_REQUIRED_FIELDS
            }
        )
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible BudgetAmendmentRecord",
                actual=exc.issue.path,
            )
        ]
    return []


def _variant_record_component(field: str, value: Any) -> JsonValue:
    if field == "status":
        return VariantLedgerStatus(value).value
    return value


def _amendment_id_component(field: str, value: Any) -> JsonValue:
    if field == "budget_type":
        return BudgetAmendmentType(value).value
    return value


def _validate_variant_records(
    records: Iterable[VariantLedgerRecord | Mapping[str, Any]],
) -> tuple[VariantLedgerRecord, ...]:
    if isinstance(records, Mapping) or isinstance(records, str) or records is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="records",
                code="invalid_variant_ledger_records_type",
                message="variant ledger records must be an iterable",
                expected="iterable of VariantLedgerRecord or mapping",
                actual=type(records).__name__,
            )
        )
    validated: list[VariantLedgerRecord] = []
    for index, record in enumerate(records):
        if isinstance(record, VariantLedgerRecord):
            validated.append(validate_variant_ledger_record(record.to_dict()))
        elif isinstance(record, Mapping):
            validated.append(validate_variant_ledger_record(record))
        else:
            raise GovernanceValidationError(
                ValidationIssue(
                    field=f"records[{index}]",
                    code="invalid_variant_ledger_record_type",
                    message="variant ledger records must be records or mappings",
                    expected="VariantLedgerRecord or mapping",
                    actual=type(record).__name__,
                )
            )
    return tuple(validated)


def _record_key(record: VariantLedgerRecord) -> tuple[str, str, str, str, int, tuple[str, ...]]:
    return (
        record.variant_id,
        record.alpha_spec_id,
        record.study_spec_id,
        record.family_id,
        record.attempt_count,
        tuple(record.trial_ids),
    )


def _family_exposure_key(record: VariantLedgerRecord) -> tuple[str, str]:
    return (record.study_spec_id, record.variant_id)


def _dedupe_records(
    records: Iterable[VariantLedgerRecord],
) -> tuple[VariantLedgerRecord, ...]:
    result: dict[tuple[str, str, str, str, int, tuple[str, ...]], VariantLedgerRecord] = {}
    for record in records:
        result.setdefault(_record_key(record), record)
    return tuple(result.values())


def _find_covering_amendment(
    amendments: tuple[BudgetAmendmentRecord, ...],
    *,
    budget_type: BudgetAmendmentType,
    target_id: str,
    prior_budget: int,
    required_budget: int,
    variant_records: tuple[VariantLedgerRecord, ...],
) -> BudgetAmendmentRecord | None:
    if not variant_records:
        return None
    earliest_attempt = min(_utc_datetime(record.created_at) for record in variant_records)
    for amendment in amendments:
        if amendment.budget_type is not budget_type:
            continue
        if amendment.target_id != target_id:
            continue
        if amendment.prior_budget != prior_budget:
            continue
        if amendment.new_budget < required_budget:
            continue
        if _utc_datetime(amendment.created_at) >= earliest_attempt:
            continue
        return amendment
    return None


def _rollup_status(statuses: tuple[TrialStatus, ...]) -> VariantLedgerStatus:
    if TrialStatus.RUNNING in statuses:
        return VariantLedgerStatus.RUNNING
    if TrialStatus.PLANNED in statuses:
        return VariantLedgerStatus.PLANNED
    if TrialStatus.COMPLETED in statuses:
        return VariantLedgerStatus.COMPLETED
    if TrialStatus.FAILED in statuses:
        return VariantLedgerStatus.FAILED
    return VariantLedgerStatus.ABANDONED


def _require_existing_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise GovernanceValidationError(
            ValidationIssue(
                field="variant_ledger_path",
                code="missing_variant_ledger",
                message="VariantLedger file is required for fail-closed budget enforcement",
                expected="existing text JSONL ledger file",
                actual=str(path),
            )
        )


def _require_writable_file(path: Path) -> None:
    try:
        mode = path.stat().st_mode
    except OSError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="variant_ledger_path",
                code="unwritable_variant_ledger",
                message="VariantLedger file permissions could not be inspected",
                expected="writable text JSONL ledger file",
                actual=f"{path}: {exc}",
            )
        ) from exc
    if mode & 0o222 == 0:
        raise GovernanceValidationError(
            ValidationIssue(
                field="variant_ledger_path",
                code="unwritable_variant_ledger",
                message="VariantLedger file must be writable before budget enforcement",
                expected="writable text JSONL ledger file",
                actual=str(path),
            )
        )
    try:
        with path.open("a", encoding="utf-8"):
            pass
    except OSError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="variant_ledger_path",
                code="unwritable_variant_ledger",
                message="VariantLedger file could not be opened for append",
                expected="writable text JSONL ledger file",
                actual=f"{path}: {exc}",
            )
        ) from exc


def _raise_if_issues(issues: list[ValidationIssue]) -> None:
    if issues:
        raise GovernanceValidationError(issues)


def _normalize_text(value: object) -> str:
    if isinstance(value, str):
        return " ".join(value.strip().lower().split())
    return str(value).strip().lower()


__all__ = [
    "BUDGET_AMENDMENT_RECORD_REQUIRED_FIELDS",
    "VARIANT_LEDGER_RECORD_REQUIRED_FIELDS",
    "BudgetAmendmentRecord",
    "BudgetAmendmentType",
    "FamilyBudgetCheck",
    "VariantBudgetValidationResult",
    "VariantLedger",
    "VariantLedgerRecord",
    "VariantLedgerStatus",
    "create_budget_amendment_record",
    "evaluate_family_budget",
    "generate_budget_amendment_id",
    "resolve_variant_ledger_path",
    "utc_now_iso",
    "validate_budget_amendment_record",
    "validate_variant_and_family_budget",
    "validate_variant_ledger_record",
    "variant_ledger_records_from_trial_ledger",
]
