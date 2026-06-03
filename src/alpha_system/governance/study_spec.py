"""StudySpec contract, study-budget accounting, and diagnostics gate."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
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
from alpha_system.governance.validation import (
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
    validate_required_fields,
    validate_schema,
)


STUDY_SPEC_REQUIRED_FIELDS = (
    "study_spec_id",
    "alpha_spec_id",
    "label_spec_id",
    "dataset_scope",
    "split_protocol",
    "metrics",
    "cost_assumptions",
    "variant_budget",
    "locked_test_policy",
    "negative_controls",
    "stopping_rules",
)
STUDY_SPEC_ID_COMPONENT_FIELDS = tuple(
    field for field in STUDY_SPEC_REQUIRED_FIELDS if field != "study_spec_id"
)
STUDY_SPEC_FIELD_TYPES = {
    "study_spec_id": str,
    "alpha_spec_id": str,
    "label_spec_id": str,
    "dataset_scope": dict,
    "split_protocol": dict,
    "metrics": list,
    "cost_assumptions": dict,
    "variant_budget": int,
    "locked_test_policy": dict,
    "negative_controls": list,
    "stopping_rules": list,
}
IMPLEMENTED_STATE = "IMPLEMENTED"
DIAGNOSTICS_ALLOWED_STATE = "DIAGNOSTICS_ALLOWED"

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


class StudyBudgetStatus(StrEnum):
    """Status values for declared study-budget accounting."""

    RESPECTED = "RESPECTED"
    OVERRUN = "OVERRUN"


@dataclass(frozen=True, slots=True)
class StudyBudgetCheck:
    """Pure metadata result for observed variants versus a declared budget."""

    variant_budget: int
    observed_count: int
    status: StudyBudgetStatus
    variants_remaining: int
    overrun_by: int

    @property
    def respected(self) -> bool:
        """Return true only when observed variants are within the declared cap."""

        return self.status is StudyBudgetStatus.RESPECTED

    @property
    def overrun(self) -> bool:
        """Return true only when observed variants exceed the declared cap."""

        return self.status is StudyBudgetStatus.OVERRUN

    def to_dict(self) -> dict[str, JsonValue]:
        """Return explicit budget-accounting metadata."""

        return {
            "variant_budget": self.variant_budget,
            "observed_count": self.observed_count,
            "status": self.status.value,
            "respected": self.respected,
            "overrun": self.overrun,
            "variants_remaining": self.variants_remaining,
            "overrun_by": self.overrun_by,
        }


@dataclass(frozen=True, slots=True)
class StudySpec:
    """Validated metadata plan required before diagnostics may be allowed."""

    study_spec_id: str
    alpha_spec_id: str
    label_spec_id: str
    dataset_scope: dict[str, JsonValue]
    split_protocol: dict[str, JsonValue]
    metrics: list[str]
    cost_assumptions: dict[str, JsonValue]
    variant_budget: int
    locked_test_policy: dict[str, JsonValue]
    negative_controls: list[str]
    stopping_rules: list[str]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> StudySpec:
        """Build a `StudySpec` from a mapping after fail-closed validation."""

        return validate_study_spec(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> StudySpec:
        """Deserialize canonical JSON and validate the resulting `StudySpec`."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="StudySpec")
        return validate_study_spec(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "study_spec_id": self.study_spec_id,
            "alpha_spec_id": self.alpha_spec_id,
            "label_spec_id": self.label_spec_id,
            "dataset_scope": dict(self.dataset_scope),
            "split_protocol": dict(self.split_protocol),
            "metrics": list(self.metrics),
            "cost_assumptions": dict(self.cost_assumptions),
            "variant_budget": self.variant_budget,
            "locked_test_policy": dict(self.locked_test_policy),
            "negative_controls": list(self.negative_controls),
            "stopping_rules": list(self.stopping_rules),
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated record through the canonical primitive."""

        return canonical_serialize(self.to_dict())


def create_study_spec(
    *,
    alpha_spec_id: str,
    label_spec_id: str,
    dataset_scope: dict[str, JsonValue],
    split_protocol: dict[str, JsonValue],
    metrics: list[str],
    cost_assumptions: dict[str, JsonValue],
    variant_budget: int,
    locked_test_policy: dict[str, JsonValue],
    negative_controls: list[str],
    stopping_rules: list[str],
) -> StudySpec:
    """Create a validated `StudySpec` without running diagnostics."""

    payload: dict[str, JsonValue] = {
        "alpha_spec_id": alpha_spec_id,
        "label_spec_id": label_spec_id,
        "dataset_scope": dict(dataset_scope),
        "split_protocol": dict(split_protocol),
        "metrics": list(metrics),
        "cost_assumptions": dict(cost_assumptions),
        "variant_budget": variant_budget,
        "locked_test_policy": dict(locked_test_policy),
        "negative_controls": list(negative_controls),
        "stopping_rules": list(stopping_rules),
    }
    payload["study_spec_id"] = generate_study_spec_id(payload)
    return validate_study_spec(payload)


def generate_study_spec_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic `StudySpec` ID for a complete payload."""

    mapping = validate_required_fields(
        payload,
        STUDY_SPEC_ID_COMPONENT_FIELDS,
        object_name="StudySpec",
    )
    components = {field: mapping[field] for field in STUDY_SPEC_ID_COMPONENT_FIELDS}
    return generate_governance_id(GovernanceIdKind.STUDY_SPEC, components)


def validate_study_spec(payload: Mapping[str, Any]) -> StudySpec:
    """Validate a `StudySpec` mapping fail-closed and return a typed record."""

    mapping = validate_schema(
        payload,
        required_fields=STUDY_SPEC_REQUIRED_FIELDS,
        field_types=STUDY_SPEC_FIELD_TYPES,
        allowed_fields=STUDY_SPEC_REQUIRED_FIELDS,
        object_name="StudySpec",
    )

    issues: list[ValidationIssue] = []
    issues.extend(_validate_ids(mapping))
    for field in (
        "dataset_scope",
        "split_protocol",
        "cost_assumptions",
        "locked_test_policy",
    ):
        issues.extend(_validate_mapping_is_substantive(mapping, field))
    issues.extend(_validate_variant_budget(mapping["variant_budget"]))
    for field in ("metrics", "negative_controls", "stopping_rules"):
        issues.extend(_validate_list_of_text(mapping, field))
    issues.extend(_validate_locked_test_policy(mapping))
    issues.extend(_validate_canonical_serializable(mapping))
    if not issues:
        expected_id = generate_study_spec_id(mapping)
        if mapping["study_spec_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="study_spec_id",
                    code="study_spec_id_mismatch",
                    message=(
                        "StudySpec.study_spec_id must match deterministic "
                        "StudySpec content"
                    ),
                    expected=expected_id,
                    actual=str(mapping["study_spec_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)

    return StudySpec(
        study_spec_id=mapping["study_spec_id"],
        alpha_spec_id=mapping["alpha_spec_id"],
        label_spec_id=mapping["label_spec_id"],
        dataset_scope=dict(mapping["dataset_scope"]),
        split_protocol=dict(mapping["split_protocol"]),
        metrics=list(mapping["metrics"]),
        cost_assumptions=dict(mapping["cost_assumptions"]),
        variant_budget=mapping["variant_budget"],
        locked_test_policy=dict(mapping["locked_test_policy"]),
        negative_controls=list(mapping["negative_controls"]),
        stopping_rules=list(mapping["stopping_rules"]),
    )


def evaluate_variant_budget(variant_budget: int, observed_count: int) -> StudyBudgetCheck:
    """Return explicit metadata for observed variants versus a declared cap."""

    issues = _validate_variant_budget(variant_budget)
    issues.extend(_validate_observed_count(observed_count))
    if issues:
        raise GovernanceValidationError(issues)

    if observed_count <= variant_budget:
        return StudyBudgetCheck(
            variant_budget=variant_budget,
            observed_count=observed_count,
            status=StudyBudgetStatus.RESPECTED,
            variants_remaining=variant_budget - observed_count,
            overrun_by=0,
        )
    return StudyBudgetCheck(
        variant_budget=variant_budget,
        observed_count=observed_count,
        status=StudyBudgetStatus.OVERRUN,
        variants_remaining=0,
        overrun_by=observed_count - variant_budget,
    )


def check_variant_budget(variant_budget: int, observed_count: int) -> StudyBudgetCheck:
    """Alias for study-budget accounting over a declared cap and observed count."""

    return evaluate_variant_budget(variant_budget, observed_count)


def validate_diagnostics_gate(
    study_spec: StudySpec | Mapping[str, Any] | None,
    *,
    from_state: str = IMPLEMENTED_STATE,
    to_state: str = DIAGNOSTICS_ALLOWED_STATE,
) -> StudySpec:
    """Block `IMPLEMENTED -> DIAGNOSTICS_ALLOWED` unless `StudySpec` validates."""

    issues: list[ValidationIssue] = []
    if from_state != IMPLEMENTED_STATE or to_state != DIAGNOSTICS_ALLOWED_STATE:
        issues.append(
            ValidationIssue(
                field="transition",
                code="unsupported_diagnostics_gate_transition",
                message=(
                    "diagnostics gate only evaluates "
                    "IMPLEMENTED -> DIAGNOSTICS_ALLOWED"
                ),
                expected=f"{IMPLEMENTED_STATE}->{DIAGNOSTICS_ALLOWED_STATE}",
                actual=f"{from_state}->{to_state}",
            )
        )
    if study_spec is None:
        issues.append(
            ValidationIssue(
                field="study_spec",
                code="missing_study_spec",
                message="valid StudySpec is required before diagnostics are allowed",
                expected="validated StudySpec",
                actual="missing",
            )
        )

    if issues:
        raise GovernanceValidationError(issues)
    if isinstance(study_spec, StudySpec):
        return validate_study_spec(study_spec.to_dict())
    return validate_study_spec(study_spec)


def assert_diagnostics_allowed(
    study_spec: StudySpec | Mapping[str, Any] | None,
) -> StudySpec:
    """Alias for the pure no-StudySpec-no-diagnostics gate."""

    return validate_diagnostics_gate(study_spec)


def _validate_ids(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    id_checks = (
        ("study_spec_id", GovernanceIdKind.STUDY_SPEC),
        ("alpha_spec_id", GovernanceIdKind.ALPHA_SPEC),
        ("label_spec_id", GovernanceIdKind.LABEL_SPEC),
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


def _validate_mapping_is_substantive(
    mapping: Mapping[str, Any],
    field: str,
) -> list[ValidationIssue]:
    value = mapping[field]
    if not value:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"StudySpec.{field} must contain explicit metadata",
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
                    message=f"StudySpec.{field} keys must be explicit strings",
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
                message=f"StudySpec.{field} must not be null",
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
                    message=f"StudySpec.{field} must be explicit, not vague",
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
                    message=f"StudySpec.{field} must not be an empty list",
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
                    message=f"StudySpec.{field} must not be an empty mapping",
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
                        message=f"StudySpec.{field} nested keys must be explicit strings",
                        expected="non-empty explicit string key",
                        actual=str(key),
                    )
                )
            issues.extend(_validate_substantive_value(item, field=f"{field}.{key}"))
        return issues
    return []


def _validate_variant_budget(value: int) -> list[ValidationIssue]:
    if type(value) is not int:
        return [
            ValidationIssue(
                field="variant_budget",
                code="invalid_variant_budget_type",
                message="StudySpec.variant_budget must be an exact integer cap",
                expected="positive int",
                actual=type(value).__name__,
            )
        ]
    if value <= 0:
        return [
            ValidationIssue(
                field="variant_budget",
                code="invalid_variant_budget",
                message="StudySpec.variant_budget must be a positive bounded integer cap",
                expected="positive int",
                actual=str(value),
            )
        ]
    return []


def _validate_observed_count(value: int) -> list[ValidationIssue]:
    if type(value) is not int:
        return [
            ValidationIssue(
                field="observed_count",
                code="invalid_observed_count_type",
                message="observed variant count must be an exact integer",
                expected="non-negative int",
                actual=type(value).__name__,
            )
        ]
    if value < 0:
        return [
            ValidationIssue(
                field="observed_count",
                code="invalid_observed_count",
                message="observed variant count must be non-negative",
                expected="non-negative int",
                actual=str(value),
            )
        ]
    return []


def _validate_list_of_text(
    mapping: Mapping[str, Any],
    field: str,
) -> list[ValidationIssue]:
    values = mapping[field]
    if not values:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"StudySpec.{field} must contain at least one entry",
                expected="non-empty list",
                actual="empty list",
            )
        ]

    issues: list[ValidationIssue] = []
    for index, item in enumerate(values):
        item_field = f"{field}[{index}]"
        if type(item) is not str:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="invalid_item_type",
                    message=f"StudySpec.{item_field} must be a string",
                    expected="str",
                    actual=type(item).__name__,
                )
            )
            continue
        normalized = _normalize_text(item)
        if normalized in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="empty_required_field",
                    message=f"StudySpec.{item_field} must be explicit",
                    expected="non-empty explicit string",
                    actual=item,
                )
            )
    return issues


def _validate_locked_test_policy(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    declared = _declared_strings(mapping["locked_test_policy"])
    if not declared:
        return [
            ValidationIssue(
                field="locked_test_policy",
                code="missing_locked_test_declaration",
                message=(
                    "StudySpec.locked_test_policy must explicitly declare "
                    "OOS or locked-test handling"
                ),
                expected="at least one explicit policy string",
                actual="no declared policy strings",
            )
        ]
    return []


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize({field: mapping[field] for field in STUDY_SPEC_REQUIRED_FIELDS})
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible StudySpec",
                actual=exc.issue.path,
            )
        ]
    return []


def _declared_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [] if _normalize_text(value) in _VAGUE_TEXT else [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_declared_strings(item))
        return result
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(_declared_strings(item))
        return result
    return []


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


__all__ = [
    "DIAGNOSTICS_ALLOWED_STATE",
    "IMPLEMENTED_STATE",
    "STUDY_SPEC_REQUIRED_FIELDS",
    "StudyBudgetCheck",
    "StudyBudgetStatus",
    "StudySpec",
    "assert_diagnostics_allowed",
    "check_variant_budget",
    "create_study_spec",
    "evaluate_variant_budget",
    "generate_study_spec_id",
    "validate_diagnostics_gate",
    "validate_study_spec",
]
