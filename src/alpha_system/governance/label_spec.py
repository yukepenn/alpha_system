"""LabelSpec contract and fail-closed validation."""

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


LABEL_SPEC_REQUIRED_FIELDS = (
    "label_spec_id",
    "horizon",
    "path_rules",
    "cost_model",
    "target_stop_rules",
    "availability_time",
    "forbidden_feature_overlap",
    "leakage_checks",
)
LABEL_SPEC_OPTIONAL_FIELDS = ("alpha_spec_id",)
LABEL_SPEC_ALLOWED_FIELDS = (
    "label_spec_id",
    "alpha_spec_id",
    "horizon",
    "path_rules",
    "cost_model",
    "target_stop_rules",
    "availability_time",
    "forbidden_feature_overlap",
    "leakage_checks",
)
LABEL_SPEC_ID_COMPONENT_FIELDS = tuple(
    field for field in LABEL_SPEC_REQUIRED_FIELDS if field != "label_spec_id"
)
LABEL_SPEC_FIELD_TYPES = {
    "label_spec_id": str,
    "alpha_spec_id": str,
    "horizon": str,
    "path_rules": dict,
    "cost_model": dict,
    "target_stop_rules": dict,
    "availability_time": str,
    "forbidden_feature_overlap": dict,
    "leakage_checks": list,
}
REQUIRED_LEAKAGE_CHECKS = frozenset({"label_as_feature", "availability_time"})

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
class LabelSpec:
    """Validated metadata contract for a governed label definition."""

    label_spec_id: str
    horizon: str
    path_rules: dict[str, JsonValue]
    cost_model: dict[str, JsonValue]
    target_stop_rules: dict[str, JsonValue]
    availability_time: str
    forbidden_feature_overlap: dict[str, JsonValue]
    leakage_checks: list[str]
    alpha_spec_id: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> LabelSpec:
        """Build a `LabelSpec` from a mapping after fail-closed validation."""

        return validate_label_spec(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> LabelSpec:
        """Deserialize canonical JSON and validate the resulting `LabelSpec`."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="LabelSpec")
        return validate_label_spec(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        payload: dict[str, JsonValue] = {
            "label_spec_id": self.label_spec_id,
            "horizon": self.horizon,
            "path_rules": dict(self.path_rules),
            "cost_model": dict(self.cost_model),
            "target_stop_rules": dict(self.target_stop_rules),
            "availability_time": self.availability_time,
            "forbidden_feature_overlap": dict(self.forbidden_feature_overlap),
            "leakage_checks": list(self.leakage_checks),
        }
        if self.alpha_spec_id is not None:
            payload["alpha_spec_id"] = self.alpha_spec_id
        return payload

    def to_canonical_json(self) -> str:
        """Serialize the validated record through the canonical primitive."""

        return canonical_serialize(self.to_dict())


def create_label_spec(
    *,
    horizon: str,
    path_rules: dict[str, JsonValue],
    cost_model: dict[str, JsonValue],
    target_stop_rules: dict[str, JsonValue],
    availability_time: str,
    forbidden_feature_overlap: dict[str, JsonValue],
    leakage_checks: list[str],
    alpha_spec_id: str | None = None,
) -> LabelSpec:
    """Create a validated `LabelSpec` without asserting label quality."""

    payload: dict[str, JsonValue] = {
        "horizon": horizon,
        "path_rules": dict(path_rules),
        "cost_model": dict(cost_model),
        "target_stop_rules": dict(target_stop_rules),
        "availability_time": availability_time,
        "forbidden_feature_overlap": dict(forbidden_feature_overlap),
        "leakage_checks": list(leakage_checks),
    }
    if alpha_spec_id is not None:
        payload["alpha_spec_id"] = alpha_spec_id
    payload["label_spec_id"] = generate_label_spec_id(payload)
    return validate_label_spec(payload)


def generate_label_spec_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic `LabelSpec` ID for a complete payload."""

    mapping = validate_required_fields(
        payload,
        LABEL_SPEC_ID_COMPONENT_FIELDS,
        object_name="LabelSpec",
    )
    component_fields = _id_component_fields(mapping)
    components = {field: mapping[field] for field in component_fields}
    return generate_governance_id(GovernanceIdKind.LABEL_SPEC, components)


def validate_label_spec(payload: Mapping[str, Any]) -> LabelSpec:
    """Validate a `LabelSpec` mapping fail-closed and return a typed record."""

    mapping = validate_schema(
        payload,
        required_fields=LABEL_SPEC_REQUIRED_FIELDS,
        field_types=LABEL_SPEC_FIELD_TYPES,
        allowed_fields=LABEL_SPEC_ALLOWED_FIELDS,
        object_name="LabelSpec",
    )

    issues: list[ValidationIssue] = []
    issues.extend(_validate_ids(mapping))
    issues.extend(_validate_non_empty_text(mapping, ("horizon", "availability_time")))
    issues.extend(_validate_availability_time(mapping["availability_time"]))
    for field in (
        "path_rules",
        "cost_model",
        "target_stop_rules",
        "forbidden_feature_overlap",
    ):
        issues.extend(_validate_mapping_is_substantive(mapping, field))
    issues.extend(_validate_forbidden_feature_overlap(mapping))
    issues.extend(_validate_leakage_checks(mapping))
    issues.extend(_validate_canonical_serializable(mapping))
    if not issues:
        expected_id = generate_label_spec_id(mapping)
        if mapping["label_spec_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="label_spec_id",
                    code="label_spec_id_mismatch",
                    message=(
                        "LabelSpec.label_spec_id must match deterministic "
                        "LabelSpec content"
                    ),
                    expected=expected_id,
                    actual=str(mapping["label_spec_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)

    return LabelSpec(
        label_spec_id=mapping["label_spec_id"],
        alpha_spec_id=mapping.get("alpha_spec_id"),
        horizon=mapping["horizon"],
        path_rules=dict(mapping["path_rules"]),
        cost_model=dict(mapping["cost_model"]),
        target_stop_rules=dict(mapping["target_stop_rules"]),
        availability_time=mapping["availability_time"],
        forbidden_feature_overlap=dict(mapping["forbidden_feature_overlap"]),
        leakage_checks=list(mapping["leakage_checks"]),
    )


def _id_component_fields(mapping: Mapping[str, Any]) -> tuple[str, ...]:
    fields: list[str] = []
    if "alpha_spec_id" in mapping:
        fields.append("alpha_spec_id")
    fields.extend(LABEL_SPEC_ID_COMPONENT_FIELDS)
    return tuple(fields)


def _validate_ids(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    id_checks: list[tuple[str, GovernanceIdKind]] = [
        ("label_spec_id", GovernanceIdKind.LABEL_SPEC)
    ]
    if "alpha_spec_id" in mapping:
        id_checks.append(("alpha_spec_id", GovernanceIdKind.ALPHA_SPEC))
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


def _validate_non_empty_text(
    mapping: Mapping[str, Any],
    fields: tuple[str, ...],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for field in fields:
        value = mapping[field]
        if _normalize_text(value) in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"LabelSpec.{field} must be a non-empty, explicit value",
                    expected="non-empty explicit string",
                    actual=value,
                )
            )
    if "alpha_spec_id" in mapping and _normalize_text(mapping["alpha_spec_id"]) in _VAGUE_TEXT:
        issues.append(
            ValidationIssue(
                field="alpha_spec_id",
                code="empty_optional_reference",
                message="LabelSpec.alpha_spec_id must be explicit when present",
                expected="well-formed aspec_ governance ID",
                actual=str(mapping["alpha_spec_id"]),
            )
        )
    return issues


def _validate_availability_time(value: str) -> list[ValidationIssue]:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return [
            ValidationIssue(
                field="availability_time",
                code="malformed_availability_time",
                message="LabelSpec.availability_time must be an ISO-8601 timestamp",
                expected="timezone-aware ISO-8601 timestamp",
                actual=value,
            )
        ]
    if parsed.tzinfo is None:
        return [
            ValidationIssue(
                field="availability_time",
                code="missing_availability_timezone",
                message="LabelSpec.availability_time must include a timezone",
                expected="timezone-aware ISO-8601 timestamp",
                actual=value,
            )
        ]
    return []


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
                message=f"LabelSpec.{field} must contain explicit metadata",
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
                    message=f"LabelSpec.{field} keys must be explicit strings",
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
                message=f"LabelSpec.{field} must not be null",
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
                    message=f"LabelSpec.{field} must be explicit, not vague",
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
                    message=f"LabelSpec.{field} must not be an empty list",
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
                    message=f"LabelSpec.{field} must not be an empty mapping",
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
                        message=f"LabelSpec.{field} nested keys must be explicit strings",
                        expected="non-empty explicit string key",
                        actual=str(key),
                    )
                )
            issues.extend(_validate_substantive_value(item, field=f"{field}.{key}"))
        return issues
    return []


def _validate_forbidden_feature_overlap(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    declared = tuple(_declared_strings(mapping["forbidden_feature_overlap"]))
    if not declared:
        return [
            ValidationIssue(
                field="forbidden_feature_overlap",
                code="missing_forbidden_overlap_reference",
                message="LabelSpec.forbidden_feature_overlap must declare blocked references",
                expected="at least one forbidden label reference, alias, or transform",
                actual="no declared reference strings",
            )
        ]
    return []


def _validate_leakage_checks(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    checks = mapping["leakage_checks"]
    if not checks:
        return [
            ValidationIssue(
                field="leakage_checks",
                code="empty_required_field",
                message="LabelSpec.leakage_checks must contain at least one check",
                expected="non-empty list",
                actual="empty list",
            )
        ]

    issues: list[ValidationIssue] = []
    normalized_checks: set[str] = set()
    for index, item in enumerate(checks):
        item_field = f"leakage_checks[{index}]"
        if type(item) is not str:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="invalid_item_type",
                    message=f"LabelSpec.{item_field} must be a string",
                    expected="str",
                    actual=type(item).__name__,
                )
            )
            continue
        normalized = _normalize_check(item)
        if normalized in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="empty_required_field",
                    message=f"LabelSpec.{item_field} must be explicit",
                    expected="non-empty explicit string",
                    actual=item,
                )
            )
        normalized_checks.add(normalized)

    missing_checks = REQUIRED_LEAKAGE_CHECKS - normalized_checks
    for missing_check in sorted(missing_checks):
        issues.append(
            ValidationIssue(
                field="leakage_checks",
                code="missing_leakage_check",
                message=f"LabelSpec.leakage_checks must include {missing_check}",
                expected="label_as_feature and availability_time",
                actual=", ".join(sorted(normalized_checks)) or "none",
            )
        )
    return issues


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize(
            {field: mapping[field] for field in LABEL_SPEC_ALLOWED_FIELDS if field in mapping}
        )
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible LabelSpec",
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


def _normalize_check(value: str) -> str:
    return "_".join(_normalize_text(value).replace("-", "_").split())


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


__all__ = [
    "LABEL_SPEC_ALLOWED_FIELDS",
    "LABEL_SPEC_OPTIONAL_FIELDS",
    "LABEL_SPEC_REQUIRED_FIELDS",
    "REQUIRED_LEAKAGE_CHECKS",
    "LabelSpec",
    "create_label_spec",
    "generate_label_spec_id",
    "validate_label_spec",
]
