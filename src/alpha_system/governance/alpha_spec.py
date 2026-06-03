"""AlphaSpec contract and no-code gate."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
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


ALPHA_SPEC_REQUIRED_FIELDS = (
    "alpha_spec_id",
    "hypothesis_id",
    "target_instruments",
    "data_assumptions",
    "factor_inputs",
    "label_references",
    "exclusion_rules",
    "timestamp_assumptions",
    "cost_assumptions",
    "expected_failure_modes",
    "promotion_criteria",
    "created_by",
    "created_at",
)
ALPHA_SPEC_ID_COMPONENT_FIELDS = tuple(
    field for field in ALPHA_SPEC_REQUIRED_FIELDS if field != "alpha_spec_id"
)
ALPHA_SPEC_FIELD_TYPES = {
    "alpha_spec_id": str,
    "hypothesis_id": str,
    "target_instruments": list,
    "data_assumptions": dict,
    "factor_inputs": list,
    "label_references": list,
    "exclusion_rules": list,
    "timestamp_assumptions": dict,
    "cost_assumptions": dict,
    "expected_failure_modes": list,
    "promotion_criteria": list,
    "created_by": str,
    "created_at": str,
}
ALPHA_SPEC_SUBSTANTIVE_FIELDS = (
    "data_assumptions",
    "exclusion_rules",
    "timestamp_assumptions",
    "cost_assumptions",
    "expected_failure_modes",
    "promotion_criteria",
)
REGISTERED_STATE = "REGISTERED"
IMPLEMENTATION_ALLOWED_STATE = "IMPLEMENTATION_ALLOWED"

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


@dataclass(frozen=True, slots=True)
class AlphaSpec:
    """Validated pre-registration record for proposed alpha research."""

    alpha_spec_id: str
    hypothesis_id: str
    target_instruments: list[str]
    data_assumptions: dict[str, JsonValue]
    factor_inputs: list[str]
    label_references: list[str]
    exclusion_rules: list[str]
    timestamp_assumptions: dict[str, JsonValue]
    cost_assumptions: dict[str, JsonValue]
    expected_failure_modes: list[str]
    promotion_criteria: list[str]
    created_by: str
    created_at: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> AlphaSpec:
        """Build an `AlphaSpec` from a mapping after fail-closed validation."""

        return validate_alpha_spec(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> AlphaSpec:
        """Deserialize canonical JSON and validate the resulting `AlphaSpec`."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="AlphaSpec")
        return validate_alpha_spec(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "alpha_spec_id": self.alpha_spec_id,
            "hypothesis_id": self.hypothesis_id,
            "target_instruments": list(self.target_instruments),
            "data_assumptions": dict(self.data_assumptions),
            "factor_inputs": list(self.factor_inputs),
            "label_references": list(self.label_references),
            "exclusion_rules": list(self.exclusion_rules),
            "timestamp_assumptions": dict(self.timestamp_assumptions),
            "cost_assumptions": dict(self.cost_assumptions),
            "expected_failure_modes": list(self.expected_failure_modes),
            "promotion_criteria": list(self.promotion_criteria),
            "created_by": self.created_by,
            "created_at": self.created_at,
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated record through the canonical primitive."""

        return canonical_serialize(self.to_dict())


def generate_alpha_spec_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic `AlphaSpec` ID for a complete payload."""

    mapping = validate_required_fields(
        payload,
        ALPHA_SPEC_ID_COMPONENT_FIELDS,
        object_name="AlphaSpec",
    )
    components = {field: mapping[field] for field in ALPHA_SPEC_ID_COMPONENT_FIELDS}
    return generate_governance_id(GovernanceIdKind.ALPHA_SPEC, components)


def validate_alpha_spec(payload: Mapping[str, Any]) -> AlphaSpec:
    """Validate an `AlphaSpec` mapping fail-closed and return a typed record."""

    mapping = validate_schema(
        payload,
        required_fields=ALPHA_SPEC_REQUIRED_FIELDS,
        field_types=ALPHA_SPEC_FIELD_TYPES,
        allowed_fields=ALPHA_SPEC_REQUIRED_FIELDS,
        object_name="AlphaSpec",
    )

    issues: list[ValidationIssue] = []
    issues.extend(_validate_ids(mapping))
    issues.extend(_validate_non_empty_text(mapping, ("created_by", "created_at")))
    issues.extend(_validate_list_of_text(mapping, "target_instruments", substantive=False))
    issues.extend(_validate_list_of_text(mapping, "factor_inputs", substantive=False))
    issues.extend(_validate_label_references(mapping))
    for field in ("exclusion_rules", "expected_failure_modes", "promotion_criteria"):
        issues.extend(_validate_list_of_text(mapping, field, substantive=True))
    for field in ("data_assumptions", "timestamp_assumptions", "cost_assumptions"):
        issues.extend(_validate_mapping_is_substantive(mapping, field))
    issues.extend(_validate_created_at(mapping["created_at"]))
    issues.extend(_validate_canonical_serializable(mapping))
    if not issues:
        expected_id = generate_alpha_spec_id(mapping)
        if mapping["alpha_spec_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="alpha_spec_id",
                    code="alpha_spec_id_mismatch",
                    message="AlphaSpec.alpha_spec_id must match deterministic AlphaSpec content",
                    expected=expected_id,
                    actual=str(mapping["alpha_spec_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)

    return AlphaSpec(
        alpha_spec_id=mapping["alpha_spec_id"],
        hypothesis_id=mapping["hypothesis_id"],
        target_instruments=list(mapping["target_instruments"]),
        data_assumptions=dict(mapping["data_assumptions"]),
        factor_inputs=list(mapping["factor_inputs"]),
        label_references=list(mapping["label_references"]),
        exclusion_rules=list(mapping["exclusion_rules"]),
        timestamp_assumptions=dict(mapping["timestamp_assumptions"]),
        cost_assumptions=dict(mapping["cost_assumptions"]),
        expected_failure_modes=list(mapping["expected_failure_modes"]),
        promotion_criteria=list(mapping["promotion_criteria"]),
        created_by=mapping["created_by"],
        created_at=mapping["created_at"],
    )


def validate_no_code_gate(
    alpha_spec: AlphaSpec | Mapping[str, Any] | None,
    *,
    from_state: str = REGISTERED_STATE,
    to_state: str = IMPLEMENTATION_ALLOWED_STATE,
) -> AlphaSpec:
    """Block `REGISTERED -> IMPLEMENTATION_ALLOWED` unless `AlphaSpec` validates."""

    issues: list[ValidationIssue] = []
    if from_state != REGISTERED_STATE or to_state != IMPLEMENTATION_ALLOWED_STATE:
        issues.append(
            ValidationIssue(
                field="transition",
                code="unsupported_no_code_gate_transition",
                message=(
                    "no-code gate only evaluates REGISTERED -> IMPLEMENTATION_ALLOWED"
                ),
                expected=f"{REGISTERED_STATE}->{IMPLEMENTATION_ALLOWED_STATE}",
                actual=f"{from_state}->{to_state}",
            )
        )
    if alpha_spec is None:
        issues.append(
            ValidationIssue(
                field="alpha_spec",
                code="missing_alpha_spec",
                message="valid AlphaSpec is required before implementation is allowed",
                expected="validated AlphaSpec",
                actual="missing",
            )
        )

    if issues:
        raise GovernanceValidationError(issues)
    if isinstance(alpha_spec, AlphaSpec):
        return validate_alpha_spec(alpha_spec.to_dict())
    return validate_alpha_spec(alpha_spec)


def assert_implementation_allowed(alpha_spec: AlphaSpec | Mapping[str, Any] | None) -> AlphaSpec:
    """Alias for the pure no-code gate used by implementation preconditions."""

    return validate_no_code_gate(alpha_spec)


def _validate_ids(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    id_checks = (
        ("alpha_spec_id", GovernanceIdKind.ALPHA_SPEC),
        ("hypothesis_id", GovernanceIdKind.HYPOTHESIS_CARD),
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


def _validate_label_references(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    issues = _validate_list_of_text(mapping, "label_references", substantive=False)
    if issues:
        return issues
    for index, value in enumerate(mapping["label_references"]):
        try:
            validate_governance_id(value, expected_kind=GovernanceIdKind.LABEL_SPEC)
        except GovernanceIdError as exc:
            issues.append(
                ValidationIssue(
                    field=f"label_references[{index}]",
                    code=exc.issue.code,
                    message=exc.issue.message,
                    expected=GovernanceIdKind.LABEL_SPEC.value,
                    actual=str(exc.issue.value),
                )
            )
    return issues


def _validate_non_empty_text(
    mapping: Mapping[str, Any],
    fields: tuple[str, ...],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for field in fields:
        value = mapping[field]
        normalized = value.strip().lower()
        if normalized in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"AlphaSpec.{field} must be a non-empty, explicit value",
                    expected="non-empty explicit string",
                    actual=value,
                )
            )
    return issues


def _validate_list_of_text(
    mapping: Mapping[str, Any],
    field: str,
    *,
    substantive: bool,
) -> list[ValidationIssue]:
    values = mapping[field]
    if not values:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"AlphaSpec.{field} must contain at least one entry",
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
                    message=f"AlphaSpec.{item_field} must be a string",
                    expected="str",
                    actual=type(item).__name__,
                )
            )
            continue
        normalized = item.strip().lower()
        if normalized in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="empty_required_field",
                    message=f"AlphaSpec.{item_field} must be explicit",
                    expected="non-empty explicit string",
                    actual=item,
                )
            )
        elif substantive and len(item.strip()) < 12:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="vague_required_field",
                    message=f"AlphaSpec.{item_field} must be substantive, not terse",
                    expected="substantive text",
                    actual=item,
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
                message=f"AlphaSpec.{field} must contain explicit assumptions",
                expected="non-empty mapping",
                actual="empty mapping",
            )
        ]

    issues: list[ValidationIssue] = []
    for key, item in value.items():
        if not isinstance(key, str) or key.strip().lower() in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_assumption_key",
                    message=f"AlphaSpec.{field} keys must be explicit strings",
                    expected="non-empty explicit string key",
                    actual=str(key),
                )
            )
        issues.extend(_validate_substantive_value(item, field=f"{field}.{key}"))
    return issues


def _validate_substantive_value(value: Any, *, field: str) -> list[ValidationIssue]:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in _VAGUE_TEXT or len(value.strip()) < 12:
            return [
                ValidationIssue(
                    field=field,
                    code="vague_required_field",
                    message=f"AlphaSpec.{field} must be substantive, not vague",
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
                    message=f"AlphaSpec.{field} must not be an empty list",
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
                    message=f"AlphaSpec.{field} must not be an empty mapping",
                    expected="non-empty value",
                    actual="empty mapping",
                )
            ]
        issues = []
        for key, item in value.items():
            if not isinstance(key, str) or key.strip().lower() in _VAGUE_TEXT:
                issues.append(
                    ValidationIssue(
                        field=field,
                        code="invalid_assumption_key",
                        message=f"AlphaSpec.{field} nested keys must be explicit strings",
                        expected="non-empty explicit string key",
                        actual=str(key),
                    )
                )
            issues.extend(_validate_substantive_value(item, field=f"{field}.{key}"))
        return issues
    return []


def _validate_created_at(value: str) -> list[ValidationIssue]:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return [
            ValidationIssue(
                field="created_at",
                code="malformed_timestamp",
                message="AlphaSpec.created_at must be an ISO-8601 timestamp",
                expected="ISO-8601 timestamp with timezone",
                actual=value,
            )
        ]
    if parsed.tzinfo is None:
        return [
            ValidationIssue(
                field="created_at",
                code="missing_timestamp_timezone",
                message="AlphaSpec.created_at must include a timezone",
                expected="timezone-aware ISO-8601 timestamp",
                actual=value,
            )
        ]
    return []


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize({field: mapping[field] for field in ALPHA_SPEC_REQUIRED_FIELDS})
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible AlphaSpec",
                actual=exc.issue.path,
            )
        ]
    return []


__all__ = [
    "ALPHA_SPEC_REQUIRED_FIELDS",
    "IMPLEMENTATION_ALLOWED_STATE",
    "REGISTERED_STATE",
    "AlphaSpec",
    "assert_implementation_allowed",
    "generate_alpha_spec_id",
    "validate_alpha_spec",
    "validate_no_code_gate",
]
