"""NegativeControlResult contract for catalogued governance canaries."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

from alpha_system.governance.canaries.catalog import (
    REQUIRED_NEGATIVE_CONTROL_TYPES,
    NegativeControlType,
    expected_failure_for_canary_type,
)
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
    ExpectedType,
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
    validate_required_fields,
    validate_schema,
)


NEGATIVE_CONTROL_RESULT_REQUIRED_FIELDS = (
    "canary_id",
    "canary_type",
    "expected_failure",
    "observed_result",
    "pass_fail",
    "related_study_or_evidence",
    "notes",
)
NEGATIVE_CONTROL_RESULT_ID_COMPONENT_FIELDS = tuple(
    field for field in NEGATIVE_CONTROL_RESULT_REQUIRED_FIELDS if field != "canary_id"
)
NEGATIVE_CONTROL_RESULT_FIELD_TYPES: dict[str, ExpectedType] = {
    "canary_id": str,
    "canary_type": str,
    "expected_failure": str,
    "observed_result": str,
    "pass_fail": str,
    "related_study_or_evidence": str,
    "notes": str,
}
NEGATIVE_CONTROL_RESULT_IMPLIES_ALPHA_VALIDITY = False

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


class NegativeControlPassFail(StrEnum):
    """Closed result vocabulary for fail-closed canary behavior."""

    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class NegativeControlResult:
    """Record whether a known-bad control was caught by a governance guard."""

    canary_id: str
    canary_type: NegativeControlType
    expected_failure: str
    observed_result: str
    pass_fail: NegativeControlPassFail
    related_study_or_evidence: str
    notes: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> NegativeControlResult:
        """Build a `NegativeControlResult` after fail-closed validation."""

        return validate_negative_control_result(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> NegativeControlResult:
        """Deserialize canonical JSON and validate the resulting record."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="NegativeControlResult")
        return validate_negative_control_result(mapping)

    @property
    def expected_failure_observed(self) -> bool:
        """Return whether the observed result matches the expected guard failure."""

        return self.observed_result == self.expected_failure

    @property
    def guard_caught_injected_fault(self) -> bool:
        """Return true only when the guard caught the injected known-bad fault."""

        return self.pass_fail is NegativeControlPassFail.PASS

    @property
    def implies_alpha_validity(self) -> bool:
        """Negative controls validate guard behavior only, not alpha validity."""

        return NEGATIVE_CONTROL_RESULT_IMPLIES_ALPHA_VALIDITY

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "canary_id": self.canary_id,
            "canary_type": self.canary_type.value,
            "expected_failure": self.expected_failure,
            "observed_result": self.observed_result,
            "pass_fail": self.pass_fail.value,
            "related_study_or_evidence": self.related_study_or_evidence,
            "notes": self.notes,
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated result through the canonical primitive."""

        return canonical_serialize(self.to_dict())


def create_negative_control_result(
    *,
    canary_type: NegativeControlType | str,
    expected_failure: str,
    observed_result: str,
    pass_fail: NegativeControlPassFail | str,
    related_study_or_evidence: str,
    notes: str,
) -> NegativeControlResult:
    """Create a validated `NegativeControlResult` without executing a canary."""

    payload: dict[str, JsonValue] = {
        "canary_type": _canary_type_value(canary_type),
        "expected_failure": expected_failure,
        "observed_result": observed_result,
        "pass_fail": _pass_fail_value(pass_fail),
        "related_study_or_evidence": related_study_or_evidence,
        "notes": notes,
    }
    payload["canary_id"] = generate_negative_control_result_id(payload)
    return validate_negative_control_result(payload)


def generate_negative_control_result_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic `nctrl_...` ID from result content."""

    mapping = validate_required_fields(
        payload,
        NEGATIVE_CONTROL_RESULT_ID_COMPONENT_FIELDS,
        object_name="NegativeControlResult",
    )
    components = {
        field: _normalize_id_component(field, mapping[field])
        for field in NEGATIVE_CONTROL_RESULT_ID_COMPONENT_FIELDS
    }
    try:
        return generate_governance_id(GovernanceIdKind.NEGATIVE_CONTROL_RESULT, components)
    except GovernanceIdError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="canary_id",
                code=exc.issue.code,
                message=exc.issue.message,
                expected=GovernanceIdKind.NEGATIVE_CONTROL_RESULT.value,
                actual=str(exc.issue.value),
            )
        ) from exc


def validate_negative_control_result(payload: Mapping[str, Any]) -> NegativeControlResult:
    """Validate a `NegativeControlResult` mapping fail-closed and return a record."""

    mapping = validate_schema(
        payload,
        required_fields=NEGATIVE_CONTROL_RESULT_REQUIRED_FIELDS,
        field_types=NEGATIVE_CONTROL_RESULT_FIELD_TYPES,
        allowed_fields=NEGATIVE_CONTROL_RESULT_REQUIRED_FIELDS,
        object_name="NegativeControlResult",
    )

    issues: list[ValidationIssue] = []
    issues.extend(_validate_canary_id(mapping))
    canary_type = _parse_canary_type(mapping["canary_type"], issues)
    pass_fail = _parse_pass_fail(mapping["pass_fail"], issues)
    for field in (
        "expected_failure",
        "observed_result",
        "related_study_or_evidence",
        "notes",
    ):
        issues.extend(_validate_text_field(mapping, field))
    issues.extend(_validate_related_reference(mapping["related_study_or_evidence"]))

    if canary_type is not None:
        expected_failure = expected_failure_for_canary_type(canary_type)
        if mapping["expected_failure"] != expected_failure:
            issues.append(
                ValidationIssue(
                    field="expected_failure",
                    code="unexpected_expected_failure",
                    message=(
                        "NegativeControlResult.expected_failure must match the "
                        "catalog entry for canary_type"
                    ),
                    expected=expected_failure,
                    actual=str(mapping["expected_failure"]),
                )
            )

    if pass_fail is not None:
        issues.extend(_validate_pass_fail_semantics(mapping, pass_fail))
    issues.extend(_validate_canonical_serializable(mapping))

    if not issues:
        expected_id = generate_negative_control_result_id(mapping)
        if mapping["canary_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="canary_id",
                    code="negative_control_result_id_mismatch",
                    message=(
                        "NegativeControlResult.canary_id must match deterministic "
                        "NegativeControlResult content"
                    ),
                    expected=expected_id,
                    actual=str(mapping["canary_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)

    assert canary_type is not None
    assert pass_fail is not None
    return NegativeControlResult(
        canary_id=mapping["canary_id"],
        canary_type=canary_type,
        expected_failure=mapping["expected_failure"],
        observed_result=mapping["observed_result"],
        pass_fail=pass_fail,
        related_study_or_evidence=mapping["related_study_or_evidence"],
        notes=mapping["notes"],
    )


def validate_negative_control_result_id(value: str) -> str:
    """Validate a `NegativeControlResult` ID string."""

    try:
        return validate_governance_id(
            value,
            expected_kind=GovernanceIdKind.NEGATIVE_CONTROL_RESULT,
        )
    except GovernanceIdError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="canary_id",
                code=exc.issue.code,
                message=exc.issue.message,
                expected=GovernanceIdKind.NEGATIVE_CONTROL_RESULT.value,
                actual=str(exc.issue.value),
            )
        ) from exc


def _validate_canary_id(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        validate_governance_id(
            mapping["canary_id"],
            expected_kind=GovernanceIdKind.NEGATIVE_CONTROL_RESULT,
        )
    except GovernanceIdError as exc:
        return [
            ValidationIssue(
                field="canary_id",
                code=exc.issue.code,
                message=exc.issue.message,
                expected=GovernanceIdKind.NEGATIVE_CONTROL_RESULT.value,
                actual=str(exc.issue.value),
            )
        ]
    return []


def _parse_canary_type(
    value: str,
    issues: list[ValidationIssue],
) -> NegativeControlType | None:
    try:
        return NegativeControlType(value)
    except ValueError:
        issues.append(
            ValidationIssue(
                field="canary_type",
                code="invalid_canary_type",
                message="NegativeControlResult.canary_type must be catalogued",
                expected=" | ".join(REQUIRED_NEGATIVE_CONTROL_TYPES),
                actual=str(value),
            )
        )
        return None


def _parse_pass_fail(
    value: str,
    issues: list[ValidationIssue],
) -> NegativeControlPassFail | None:
    try:
        return NegativeControlPassFail(value)
    except ValueError:
        issues.append(
            ValidationIssue(
                field="pass_fail",
                code="invalid_pass_fail",
                message="NegativeControlResult.pass_fail must use the closed vocabulary",
                expected=" | ".join(outcome.value for outcome in NegativeControlPassFail),
                actual=str(value),
            )
        )
        return None


def _validate_text_field(mapping: Mapping[str, Any], field: str) -> list[ValidationIssue]:
    value = mapping[field]
    if _normalize_text(value) not in _VAGUE_TEXT:
        return []
    return [
        ValidationIssue(
            field=field,
            code="empty_required_field",
            message=f"NegativeControlResult.{field} must be explicit",
            expected="non-empty explicit string",
            actual=str(value),
        )
    ]


def _validate_related_reference(value: str) -> list[ValidationIssue]:
    for kind in (GovernanceIdKind.STUDY_SPEC, GovernanceIdKind.EVIDENCE_BUNDLE):
        try:
            validate_governance_id(value, expected_kind=kind)
            return []
        except GovernanceIdError:
            continue
    return [
        ValidationIssue(
            field="related_study_or_evidence",
            code="invalid_related_study_or_evidence",
            message=(
                "NegativeControlResult.related_study_or_evidence must reference "
                "a StudySpec or EvidenceBundle governance ID"
            ),
            expected="StudySpec or EvidenceBundle governance ID",
            actual=value,
        )
    ]


def _validate_pass_fail_semantics(
    mapping: Mapping[str, Any],
    pass_fail: NegativeControlPassFail,
) -> list[ValidationIssue]:
    expected_pass_fail = (
        NegativeControlPassFail.PASS
        if mapping["observed_result"] == mapping["expected_failure"]
        else NegativeControlPassFail.FAIL
    )
    if pass_fail is expected_pass_fail:
        return []
    return [
        ValidationIssue(
            field="pass_fail",
            code="inconsistent_pass_fail",
            message=(
                "NegativeControlResult.pass_fail must be PASS only when the "
                "observed result matches expected_failure; mismatches are FAIL"
            ),
            expected=expected_pass_fail.value,
            actual=pass_fail.value,
        )
    ]


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize(
            {
                field: _normalize_serialization_component(field, mapping[field])
                for field in NEGATIVE_CONTROL_RESULT_REQUIRED_FIELDS
                if field in mapping
            }
        )
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible NegativeControlResult",
                actual=exc.issue.path,
            )
        ]
    return []


def _normalize_id_component(field: str, value: Any) -> JsonValue:
    if field == "canary_type":
        return _canary_type_value(value)
    if field == "pass_fail":
        return _pass_fail_value(value)
    return cast(JsonValue, value)


def _normalize_serialization_component(field: str, value: Any) -> JsonValue:
    if field == "canary_type" and isinstance(value, NegativeControlType):
        return value.value
    if field == "pass_fail" and isinstance(value, NegativeControlPassFail):
        return value.value
    return cast(JsonValue, value)


def _canary_type_value(canary_type: NegativeControlType | str | Any) -> str:
    try:
        return NegativeControlType(canary_type).value
    except ValueError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="canary_type",
                code="invalid_canary_type",
                message="NegativeControlResult.canary_type must be catalogued",
                expected=" | ".join(REQUIRED_NEGATIVE_CONTROL_TYPES),
                actual=str(canary_type),
            )
        ) from exc


def _pass_fail_value(pass_fail: NegativeControlPassFail | str | Any) -> str:
    try:
        return NegativeControlPassFail(pass_fail).value
    except ValueError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="pass_fail",
                code="invalid_pass_fail",
                message="NegativeControlResult.pass_fail must use the closed vocabulary",
                expected=" | ".join(outcome.value for outcome in NegativeControlPassFail),
                actual=str(pass_fail),
            )
        ) from exc


def _normalize_text(value: object) -> str:
    if isinstance(value, str):
        return " ".join(value.strip().lower().split())
    return str(value).strip().lower()


__all__ = [
    "NEGATIVE_CONTROL_RESULT_FIELD_TYPES",
    "NEGATIVE_CONTROL_RESULT_ID_COMPONENT_FIELDS",
    "NEGATIVE_CONTROL_RESULT_IMPLIES_ALPHA_VALIDITY",
    "NEGATIVE_CONTROL_RESULT_REQUIRED_FIELDS",
    "NegativeControlPassFail",
    "NegativeControlResult",
    "create_negative_control_result",
    "generate_negative_control_result_id",
    "validate_negative_control_result",
    "validate_negative_control_result_id",
]
