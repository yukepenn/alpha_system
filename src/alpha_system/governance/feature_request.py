"""FeatureRequest contract for requested feature/factor inputs."""

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


FEATURE_REQUEST_REQUIRED_FIELDS = (
    "feature_request_id",
    "alpha_spec_id",
    "requested_inputs",
    "formula_sketch",
    "availability_assumptions",
    "duplicate_or_equivalent_exposure_notes",
    "data_requirements",
    "approval_status",
)
FEATURE_REQUEST_ID_COMPONENT_FIELDS = tuple(
    field for field in FEATURE_REQUEST_REQUIRED_FIELDS if field != "feature_request_id"
)
FEATURE_REQUEST_FIELD_TYPES = {
    "feature_request_id": str,
    "alpha_spec_id": str,
    "requested_inputs": list,
    "formula_sketch": dict,
    "availability_assumptions": dict,
    "duplicate_or_equivalent_exposure_notes": dict,
    "data_requirements": dict,
    "approval_status": str,
}
FEATURE_REQUEST_NOTE_FIELDS = (
    "guard",
    "checked",
    "registry_status",
    "registry_entries_checked",
    "findings",
    "summary",
)

_DUPLICATE_GUARD_NAME = "duplicate_exposure"
_ALLOWED_NOTE_REGISTRY_STATUSES = frozenset({"CHECKED", "EMPTY", "UNAVAILABLE"})
_ALLOWED_FINDING_KINDS = frozenset({"DUPLICATE", "EQUIVALENT"})
_ALLOWED_FINDING_SEVERITIES = frozenset({"BLOCKING", "WARNING"})
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


class FeatureRequestApprovalStatus(StrEnum):
    """Explicit FeatureRequest approval metadata values."""

    PENDING = "PENDING"
    BLOCKED_DUPLICATE = "BLOCKED_DUPLICATE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    APPROVED = "APPROVED"


@dataclass(frozen=True, slots=True)
class FeatureRequest:
    """Validated metadata request for proposed feature/factor inputs."""

    feature_request_id: str
    alpha_spec_id: str
    requested_inputs: list[str]
    formula_sketch: dict[str, JsonValue]
    availability_assumptions: dict[str, JsonValue]
    duplicate_or_equivalent_exposure_notes: dict[str, JsonValue]
    data_requirements: dict[str, JsonValue]
    approval_status: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> FeatureRequest:
        """Build a `FeatureRequest` from a mapping after fail-closed validation."""

        return validate_feature_request(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> FeatureRequest:
        """Deserialize canonical JSON and validate the resulting `FeatureRequest`."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="FeatureRequest")
        return validate_feature_request(mapping)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "feature_request_id": self.feature_request_id,
            "alpha_spec_id": self.alpha_spec_id,
            "requested_inputs": list(self.requested_inputs),
            "formula_sketch": dict(self.formula_sketch),
            "availability_assumptions": dict(self.availability_assumptions),
            "duplicate_or_equivalent_exposure_notes": dict(
                self.duplicate_or_equivalent_exposure_notes
            ),
            "data_requirements": dict(self.data_requirements),
            "approval_status": self.approval_status,
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated record through the canonical primitive."""

        return canonical_serialize(self.to_dict())


def create_feature_request(
    *,
    alpha_spec_id: str,
    requested_inputs: list[str],
    formula_sketch: dict[str, JsonValue],
    availability_assumptions: dict[str, JsonValue],
    duplicate_or_equivalent_exposure_notes: dict[str, JsonValue],
    data_requirements: dict[str, JsonValue],
    approval_status: FeatureRequestApprovalStatus | str = FeatureRequestApprovalStatus.PENDING,
) -> FeatureRequest:
    """Create a validated `FeatureRequest`, defaulting only to `PENDING` status."""

    payload: dict[str, JsonValue] = {
        "alpha_spec_id": alpha_spec_id,
        "requested_inputs": list(requested_inputs),
        "formula_sketch": dict(formula_sketch),
        "availability_assumptions": dict(availability_assumptions),
        "duplicate_or_equivalent_exposure_notes": dict(
            duplicate_or_equivalent_exposure_notes
        ),
        "data_requirements": dict(data_requirements),
        "approval_status": _approval_status_value(approval_status),
    }
    payload["feature_request_id"] = generate_feature_request_id(payload)
    return validate_feature_request(payload)


def generate_feature_request_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic `FeatureRequest` ID for a complete payload."""

    mapping = validate_required_fields(
        payload,
        FEATURE_REQUEST_ID_COMPONENT_FIELDS,
        object_name="FeatureRequest",
    )
    components = {field: mapping[field] for field in FEATURE_REQUEST_ID_COMPONENT_FIELDS}
    return generate_governance_id(GovernanceIdKind.FEATURE_REQUEST, components)


def validate_feature_request(payload: Mapping[str, Any]) -> FeatureRequest:
    """Validate a `FeatureRequest` mapping fail-closed and return a typed record."""

    mapping = validate_schema(
        payload,
        required_fields=FEATURE_REQUEST_REQUIRED_FIELDS,
        field_types=FEATURE_REQUEST_FIELD_TYPES,
        allowed_fields=FEATURE_REQUEST_REQUIRED_FIELDS,
        object_name="FeatureRequest",
    )

    issues: list[ValidationIssue] = []
    issues.extend(_validate_ids(mapping))
    issues.extend(_validate_requested_inputs(mapping))
    for field in ("formula_sketch", "availability_assumptions", "data_requirements"):
        issues.extend(_validate_mapping_is_substantive(mapping, field))
    issues.extend(_validate_duplicate_notes(mapping))
    issues.extend(_validate_approval_status(mapping))
    issues.extend(_validate_status_matches_findings(mapping))
    issues.extend(_validate_canonical_serializable(mapping))
    if not issues:
        expected_id = generate_feature_request_id(mapping)
        if mapping["feature_request_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="feature_request_id",
                    code="feature_request_id_mismatch",
                    message=(
                        "FeatureRequest.feature_request_id must match deterministic "
                        "FeatureRequest content"
                    ),
                    expected=expected_id,
                    actual=str(mapping["feature_request_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)

    return FeatureRequest(
        feature_request_id=mapping["feature_request_id"],
        alpha_spec_id=mapping["alpha_spec_id"],
        requested_inputs=list(mapping["requested_inputs"]),
        formula_sketch=dict(mapping["formula_sketch"]),
        availability_assumptions=dict(mapping["availability_assumptions"]),
        duplicate_or_equivalent_exposure_notes=dict(
            mapping["duplicate_or_equivalent_exposure_notes"]
        ),
        data_requirements=dict(mapping["data_requirements"]),
        approval_status=mapping["approval_status"],
    )


def _validate_ids(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    id_checks = (
        ("feature_request_id", GovernanceIdKind.FEATURE_REQUEST),
        ("alpha_spec_id", GovernanceIdKind.ALPHA_SPEC),
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


def _validate_requested_inputs(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    values = mapping["requested_inputs"]
    if not values:
        return [
            ValidationIssue(
                field="requested_inputs",
                code="empty_required_field",
                message="FeatureRequest.requested_inputs must contain at least one entry",
                expected="non-empty list",
                actual="empty list",
            )
        ]

    issues: list[ValidationIssue] = []
    for index, item in enumerate(values):
        item_field = f"requested_inputs[{index}]"
        if type(item) is not str:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="invalid_item_type",
                    message=f"FeatureRequest.{item_field} must be a string",
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
                    message=f"FeatureRequest.{item_field} must be explicit",
                    expected="non-empty explicit string",
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
                message=f"FeatureRequest.{field} must contain explicit metadata",
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
                    message=f"FeatureRequest.{field} keys must be explicit strings",
                    expected="non-empty explicit string key",
                    actual=str(key),
                )
            )
        issues.extend(_validate_substantive_value(item, field=f"{field}.{key}"))
    return issues


def _validate_substantive_value(value: Any, *, field: str) -> list[ValidationIssue]:
    if isinstance(value, str):
        normalized = _normalize_text(value)
        if normalized in _VAGUE_TEXT:
            return [
                ValidationIssue(
                    field=field,
                    code="vague_required_field",
                    message=f"FeatureRequest.{field} must be explicit, not vague",
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
                    message=f"FeatureRequest.{field} must not be an empty list",
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
                    message=f"FeatureRequest.{field} must not be an empty mapping",
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
                        message=f"FeatureRequest.{field} nested keys must be explicit strings",
                        expected="non-empty explicit string key",
                        actual=str(key),
                    )
                )
            issues.extend(_validate_substantive_value(item, field=f"{field}.{key}"))
        return issues
    return []


def _validate_duplicate_notes(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    notes = mapping["duplicate_or_equivalent_exposure_notes"]
    if not notes:
        return [
            ValidationIssue(
                field="duplicate_or_equivalent_exposure_notes",
                code="empty_required_field",
                message=(
                    "FeatureRequest.duplicate_or_equivalent_exposure_notes must contain "
                    "duplicate-exposure guard metadata"
                ),
                expected="non-empty guard notes",
                actual="empty mapping",
            )
        ]

    issues: list[ValidationIssue] = []
    for field in FEATURE_REQUEST_NOTE_FIELDS:
        if field not in notes:
            issues.append(
                ValidationIssue(
                    field=f"duplicate_or_equivalent_exposure_notes.{field}",
                    code="missing_required_field",
                    message=f"duplicate-exposure notes require {field}",
                    expected="present guard note field",
                    actual="missing",
                )
            )

    if issues:
        return issues

    if notes["guard"] != _DUPLICATE_GUARD_NAME:
        issues.append(
            ValidationIssue(
                field="duplicate_or_equivalent_exposure_notes.guard",
                code="invalid_guard_name",
                message="duplicate-exposure notes must be produced by the duplicate guard",
                expected=_DUPLICATE_GUARD_NAME,
                actual=str(notes["guard"]),
            )
        )
    if notes["checked"] is not True:
        issues.append(
            ValidationIssue(
                field="duplicate_or_equivalent_exposure_notes.checked",
                code="unchecked_duplicate_exposure",
                message="FeatureRequest cannot be treated as clean without a guard check",
                expected="True",
                actual=str(notes["checked"]),
            )
        )
    if notes["registry_status"] not in _ALLOWED_NOTE_REGISTRY_STATUSES:
        issues.append(
            ValidationIssue(
                field="duplicate_or_equivalent_exposure_notes.registry_status",
                code="invalid_registry_status",
                message="duplicate-exposure notes registry_status is not allowed",
                expected="CHECKED | EMPTY | UNAVAILABLE",
                actual=str(notes["registry_status"]),
            )
        )
    if type(notes["registry_entries_checked"]) is not int or notes["registry_entries_checked"] < 0:
        issues.append(
            ValidationIssue(
                field="duplicate_or_equivalent_exposure_notes.registry_entries_checked",
                code="invalid_registry_entry_count",
                message="duplicate-exposure notes registry_entries_checked must be non-negative",
                expected="non-negative int",
                actual=type(notes["registry_entries_checked"]).__name__,
            )
        )
    if type(notes["summary"]) is not str or _normalize_text(notes["summary"]) in _VAGUE_TEXT:
        issues.append(
            ValidationIssue(
                field="duplicate_or_equivalent_exposure_notes.summary",
                code="empty_required_field",
                message="duplicate-exposure notes summary must be explicit",
                expected="non-empty explicit string",
                actual=str(notes["summary"]),
            )
        )
    issues.extend(_validate_findings(notes["findings"]))
    return issues


def _validate_findings(value: Any) -> list[ValidationIssue]:
    if type(value) is not list:
        return [
            ValidationIssue(
                field="duplicate_or_equivalent_exposure_notes.findings",
                code="invalid_field_type",
                message="duplicate-exposure notes findings must be a list",
                expected="list",
                actual=type(value).__name__,
            )
        ]

    issues: list[ValidationIssue] = []
    for index, item in enumerate(value):
        item_field = f"duplicate_or_equivalent_exposure_notes.findings[{index}]"
        if not isinstance(item, Mapping):
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="invalid_item_type",
                    message="duplicate-exposure finding must be a mapping",
                    expected="mapping",
                    actual=type(item).__name__,
                )
            )
            continue
        issues.extend(_validate_finding(item, item_field))
    return issues


def _validate_finding(finding: Mapping[str, Any], field: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    required = ("kind", "severity", "matched_registry_reference", "rationale")
    for required_field in required:
        if required_field not in finding:
            issues.append(
                ValidationIssue(
                    field=f"{field}.{required_field}",
                    code="missing_required_field",
                    message=f"duplicate-exposure finding requires {required_field}",
                    expected="present finding field",
                    actual="missing",
                )
            )
    if issues:
        return issues

    if finding["kind"] not in _ALLOWED_FINDING_KINDS:
        issues.append(
            ValidationIssue(
                field=f"{field}.kind",
                code="invalid_finding_kind",
                message="duplicate-exposure finding kind is not allowed",
                expected="DUPLICATE | EQUIVALENT",
                actual=str(finding["kind"]),
            )
        )
    if finding["severity"] not in _ALLOWED_FINDING_SEVERITIES:
        issues.append(
            ValidationIssue(
                field=f"{field}.severity",
                code="invalid_finding_severity",
                message="duplicate-exposure finding severity is not allowed",
                expected="BLOCKING | WARNING",
                actual=str(finding["severity"]),
            )
        )
    if not isinstance(finding["matched_registry_reference"], Mapping):
        issues.append(
            ValidationIssue(
                field=f"{field}.matched_registry_reference",
                code="invalid_field_type",
                message="matched_registry_reference must be a mapping",
                expected="mapping",
                actual=type(finding["matched_registry_reference"]).__name__,
            )
        )
    if (
        type(finding["rationale"]) is not str
        or _normalize_text(finding["rationale"]) in _VAGUE_TEXT
    ):
        issues.append(
            ValidationIssue(
                field=f"{field}.rationale",
                code="empty_required_field",
                message="duplicate-exposure finding rationale must be explicit",
                expected="non-empty explicit string",
                actual=str(finding["rationale"]),
            )
        )
    return issues


def _validate_approval_status(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        FeatureRequestApprovalStatus(mapping["approval_status"])
    except ValueError:
        return [
            ValidationIssue(
                field="approval_status",
                code="invalid_approval_status",
                message="FeatureRequest.approval_status is not an allowed value",
                expected="PENDING | BLOCKED_DUPLICATE | NEEDS_REVIEW | APPROVED",
                actual=str(mapping["approval_status"]),
            )
        ]
    return []


def _validate_status_matches_findings(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    status = mapping["approval_status"]
    notes = mapping["duplicate_or_equivalent_exposure_notes"]
    blocking = _notes_have_blocking_finding(notes)
    registry_status = notes.get("registry_status")
    if status == FeatureRequestApprovalStatus.APPROVED and blocking:
        return [
            ValidationIssue(
                field="approval_status",
                code="approved_with_blocking_duplicate",
                message="FeatureRequest with blocking duplicate findings cannot be approved",
                expected="PENDING | BLOCKED_DUPLICATE | NEEDS_REVIEW",
                actual=status,
            )
        ]
    if status == FeatureRequestApprovalStatus.APPROVED and registry_status == "UNAVAILABLE":
        return [
            ValidationIssue(
                field="approval_status",
                code="approved_without_available_registry_check",
                message="FeatureRequest cannot be approved when the registry check was unavailable",
                expected="PENDING | NEEDS_REVIEW",
                actual=status,
            )
        ]
    if status == FeatureRequestApprovalStatus.BLOCKED_DUPLICATE and not blocking:
        return [
            ValidationIssue(
                field="approval_status",
                code="blocked_duplicate_without_blocking_finding",
                message="BLOCKED_DUPLICATE requires at least one blocking duplicate finding",
                expected="blocking duplicate finding",
                actual="no blocking finding",
            )
        ]
    return []


def _notes_have_blocking_finding(notes: Mapping[str, Any]) -> bool:
    findings = notes.get("findings")
    if type(findings) is not list:
        return False
    return any(
        isinstance(finding, Mapping) and finding.get("severity") == "BLOCKING"
        for finding in findings
    )


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize({field: mapping[field] for field in FEATURE_REQUEST_REQUIRED_FIELDS})
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible FeatureRequest",
                actual=exc.issue.path,
            )
        ]
    return []


def _approval_status_value(value: FeatureRequestApprovalStatus | str) -> str:
    if isinstance(value, FeatureRequestApprovalStatus):
        return value.value
    return value


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


__all__ = [
    "FEATURE_REQUEST_REQUIRED_FIELDS",
    "FeatureRequest",
    "FeatureRequestApprovalStatus",
    "create_feature_request",
    "generate_feature_request_id",
    "validate_feature_request",
]
