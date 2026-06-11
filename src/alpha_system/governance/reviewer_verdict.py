"""ReviewerVerdict contract and independent-review verdict vocabulary."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
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
from alpha_system.governance.validation import (
    ExpectedType,
    GovernanceValidationError,
    ValidationIssue,
    require_mapping,
    validate_schema,
)
from alpha_system.governance.verdict_reason_code import (
    VerdictReasonCode,
    missing_inconclusive_reason_issue,
    validate_optional_verdict_reason_code,
    validate_verdict_reason_code,
)

REVIEWER_VERDICT_REQUIRED_FIELDS = (
    "reviewer_id",
    "role",
    "independence_statement",
    "verdict",
    "blocking_issues",
    "warnings",
    "checked_artifacts",
    "checked_commands",
    "timestamp",
)
REVIEWER_VERDICT_OPTIONAL_FIELDS = ("reason_code",)
REVIEWER_VERDICT_ALLOWED_FIELDS = REVIEWER_VERDICT_REQUIRED_FIELDS + REVIEWER_VERDICT_OPTIONAL_FIELDS
REVIEWER_VERDICT_ID_COMPONENT_FIELDS = REVIEWER_VERDICT_ALLOWED_FIELDS
REVIEWER_VERDICT_FIELD_TYPES: dict[str, ExpectedType] = {
    "reviewer_id": str,
    "role": str,
    "independence_statement": str,
    "verdict": str,
    "blocking_issues": list,
    "warnings": list,
    "checked_artifacts": list,
    "checked_commands": list,
    "timestamp": str,
    "reason_code": (str, VerdictReasonCode),
}
REVIEWER_VERDICT_IMPLIES_MARKET_TRUTH = False
REVIEWER_VERDICT_IMPLIES_PROFITABILITY = False
REVIEWER_VERDICT_IMPLIES_TRADABILITY = False
REVIEWER_VERDICT_IMPLIES_PRODUCTION_READINESS = False

_UTC_SECONDS_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
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


class ReviewerVerdictOutcome(StrEnum):
    """Closed semantic-review verdict vocabulary."""

    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    REWORK = "REWORK"
    BLOCKED = "BLOCKED"
    INCONCLUSIVE = "INCONCLUSIVE"


MERGE_ELIGIBLE_REVIEWER_VERDICTS = (
    ReviewerVerdictOutcome.PASS,
    ReviewerVerdictOutcome.PASS_WITH_WARNINGS,
)


@dataclass(frozen=True, slots=True)
class ReviewerVerdict:
    """Validated metadata record for an independent semantic review."""

    reviewer_id: str
    role: str
    independence_statement: str
    verdict: ReviewerVerdictOutcome
    blocking_issues: tuple[str, ...]
    warnings: tuple[str, ...]
    checked_artifacts: tuple[str, ...]
    checked_commands: tuple[str, ...]
    timestamp: str
    reason_code: VerdictReasonCode | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> ReviewerVerdict:
        """Build a `ReviewerVerdict` from a mapping after fail-closed validation."""

        return validate_reviewer_verdict(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> ReviewerVerdict:
        """Deserialize canonical JSON and validate the resulting verdict."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="ReviewerVerdict")
        return validate_reviewer_verdict(mapping)

    @property
    def reviewer_verdict_id(self) -> str:
        """Return the deterministic `rver_...` ID for this verdict content."""

        return generate_reviewer_verdict_id(self.to_dict())

    @property
    def is_merge_eligible(self) -> bool:
        """Return whether the verdict may support merge-eligible promotion."""

        return self.verdict in MERGE_ELIGIBLE_REVIEWER_VERDICTS

    @property
    def implies_market_truth(self) -> bool:
        """ReviewerVerdict records review judgment, not market truth."""

        return REVIEWER_VERDICT_IMPLIES_MARKET_TRUTH

    @property
    def implies_profitability(self) -> bool:
        """ReviewerVerdict does not assert profitability."""

        return REVIEWER_VERDICT_IMPLIES_PROFITABILITY

    @property
    def implies_tradability(self) -> bool:
        """ReviewerVerdict does not assert tradability."""

        return REVIEWER_VERDICT_IMPLIES_TRADABILITY

    @property
    def implies_production_readiness(self) -> bool:
        """ReviewerVerdict does not mark production readiness."""

        return REVIEWER_VERDICT_IMPLIES_PRODUCTION_READINESS

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        payload: dict[str, JsonValue] = {
            "reviewer_id": self.reviewer_id,
            "role": self.role,
            "independence_statement": self.independence_statement,
            "verdict": self.verdict.value,
            "blocking_issues": list(self.blocking_issues),
            "warnings": list(self.warnings),
            "checked_artifacts": list(self.checked_artifacts),
            "checked_commands": list(self.checked_commands),
            "timestamp": self.timestamp,
        }
        if self.reason_code is not None:
            payload["reason_code"] = self.reason_code.value
        return payload

    def to_canonical_json(self) -> str:
        """Serialize the validated verdict through the canonical primitive."""

        return canonical_serialize(self.to_dict())


def create_reviewer_verdict(
    *,
    reviewer_id: str,
    role: str,
    independence_statement: str,
    verdict: ReviewerVerdictOutcome | str,
    blocking_issues: list[str],
    warnings: list[str],
    checked_artifacts: list[str],
    checked_commands: list[str],
    timestamp: str,
    reason_code: VerdictReasonCode | str | None = None,
) -> ReviewerVerdict:
    """Create a validated `ReviewerVerdict` without implying market truth."""

    payload: dict[str, JsonValue] = {
        "reviewer_id": reviewer_id,
        "role": role,
        "independence_statement": independence_statement,
        "verdict": _verdict_value(verdict),
        "blocking_issues": list(blocking_issues),
        "warnings": list(warnings),
        "checked_artifacts": list(checked_artifacts),
        "checked_commands": list(checked_commands),
        "timestamp": timestamp,
    }
    if reason_code is not None:
        payload["reason_code"] = validate_optional_verdict_reason_code(reason_code).value
    return validate_reviewer_verdict(payload)


def generate_reviewer_verdict_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic ReviewerVerdict ID from content fields."""

    mapping = validate_reviewer_verdict(payload).to_dict()
    components = {
        field: _normalize_id_component(field, mapping[field])
        for field in REVIEWER_VERDICT_ID_COMPONENT_FIELDS
        if field in mapping
    }
    try:
        return generate_governance_id(GovernanceIdKind.REVIEWER_VERDICT, components)
    except GovernanceIdError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="reviewer_verdict_id",
                code=exc.issue.code,
                message=exc.issue.message,
                expected=GovernanceIdKind.REVIEWER_VERDICT.value,
                actual=str(exc.issue.value),
            )
        ) from exc


def validate_reviewer_verdict(payload: Mapping[str, Any]) -> ReviewerVerdict:
    """Validate a `ReviewerVerdict` mapping fail-closed and return a record."""

    mapping = validate_schema(
        payload,
        required_fields=REVIEWER_VERDICT_REQUIRED_FIELDS,
        field_types=REVIEWER_VERDICT_FIELD_TYPES,
        allowed_fields=REVIEWER_VERDICT_ALLOWED_FIELDS,
        object_name="ReviewerVerdict",
    )

    issues: list[ValidationIssue] = []
    issues.extend(_validate_text_field(mapping, "reviewer_id"))
    issues.extend(_validate_text_field(mapping, "role"))
    issues.extend(_validate_text_field(mapping, "independence_statement"))
    verdict = _parse_verdict(mapping["verdict"], issues)
    reason_code = _parse_optional_reason_code(mapping, issues)
    issues.extend(_validate_string_list(mapping["blocking_issues"], field="blocking_issues"))
    issues.extend(_validate_string_list(mapping["warnings"], field="warnings"))
    issues.extend(
        _validate_string_list(
            mapping["checked_artifacts"],
            field="checked_artifacts",
            require_non_empty=True,
        )
    )
    issues.extend(
        _validate_string_list(
            mapping["checked_commands"],
            field="checked_commands",
            require_non_empty=True,
        )
    )
    issues.extend(_validate_timestamp(mapping["timestamp"]))
    if verdict is ReviewerVerdictOutcome.INCONCLUSIVE and reason_code is None:
        issues.append(
            missing_inconclusive_reason_issue(state_field="ReviewerVerdict.verdict")
        )
    issues.extend(_validate_canonical_serializable(mapping))

    if issues:
        raise GovernanceValidationError(issues)

    assert verdict is not None
    return ReviewerVerdict(
        reviewer_id=mapping["reviewer_id"],
        role=mapping["role"],
        independence_statement=mapping["independence_statement"],
        verdict=verdict,
        blocking_issues=tuple(mapping["blocking_issues"]),
        warnings=tuple(mapping["warnings"]),
        checked_artifacts=tuple(mapping["checked_artifacts"]),
        checked_commands=tuple(mapping["checked_commands"]),
        timestamp=mapping["timestamp"],
        reason_code=reason_code,
    )


def validate_reviewer_verdict_id(value: str) -> str:
    """Validate a `ReviewerVerdict` ID string."""

    try:
        return validate_governance_id(value, expected_kind=GovernanceIdKind.REVIEWER_VERDICT)
    except GovernanceIdError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="reviewer_verdict_id",
                code=exc.issue.code,
                message=exc.issue.message,
                expected=GovernanceIdKind.REVIEWER_VERDICT.value,
                actual=str(exc.issue.value),
            )
        ) from exc


def _parse_verdict(
    value: Any,
    issues: list[ValidationIssue],
) -> ReviewerVerdictOutcome | None:
    try:
        return ReviewerVerdictOutcome(value)
    except ValueError:
        issues.append(
            ValidationIssue(
                field="verdict",
                code="invalid_reviewer_verdict",
                message="ReviewerVerdict.verdict must use the closed review vocabulary",
                expected=" | ".join(outcome.value for outcome in ReviewerVerdictOutcome),
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
            message=f"ReviewerVerdict.{field} must be explicit",
            expected="non-empty explicit string",
            actual=str(value),
        )
    ]


def _validate_string_list(
    values: list[Any],
    *,
    field: str,
    require_non_empty: bool = False,
) -> list[ValidationIssue]:
    if require_non_empty and not values:
        return [
            ValidationIssue(
                field=field,
                code="empty_required_field",
                message=f"ReviewerVerdict.{field} must contain at least one explicit item",
                expected="non-empty list of explicit strings",
                actual="empty list",
            )
        ]

    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        item_field = f"{field}[{index}]"
        if type(item) is not str:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="invalid_item_type",
                    message=f"ReviewerVerdict.{item_field} must be a string",
                    expected="explicit string",
                    actual=type(item).__name__,
                )
            )
            continue
        if _normalize_text(item) in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="empty_required_field",
                    message=f"ReviewerVerdict.{item_field} must be explicit",
                    expected="non-empty explicit string",
                    actual=item,
                )
            )
            continue
        if item in seen:
            issues.append(
                ValidationIssue(
                    field=item_field,
                    code="duplicate_list_item",
                    message=f"ReviewerVerdict.{field} must not contain duplicate entries",
                    expected="unique explicit strings",
                    actual=item,
                )
            )
        seen.add(item)
    return issues


def _validate_timestamp(value: str) -> list[ValidationIssue]:
    if _normalize_text(value) in _VAGUE_TEXT:
        return [
            ValidationIssue(
                field="timestamp",
                code="empty_required_field",
                message="ReviewerVerdict.timestamp must be explicit",
                expected="UTC timestamp in YYYY-MM-DDTHH:MM:SSZ format",
                actual=str(value),
            )
        ]
    if _UTC_SECONDS_PATTERN.fullmatch(value) is None:
        return [
            ValidationIssue(
                field="timestamp",
                code="invalid_timestamp",
                message="ReviewerVerdict.timestamp must use UTC YYYY-MM-DDTHH:MM:SSZ format",
                expected="YYYY-MM-DDTHH:MM:SSZ",
                actual=value,
            )
        ]
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return [
            ValidationIssue(
                field="timestamp",
                code="invalid_timestamp",
                message="ReviewerVerdict.timestamp must be a real UTC timestamp",
                expected="valid UTC timestamp",
                actual=value,
            )
        ]
    return []


def _validate_canonical_serializable(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    try:
        canonical_serialize(
            {
                field: _normalize_serialization_component(field, mapping[field])
                for field in REVIEWER_VERDICT_ID_COMPONENT_FIELDS
                if field in mapping
            }
        )
    except GovernanceValidationError as exc:
        return list(exc.issues)
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible ReviewerVerdict",
                actual=exc.issue.path,
            )
        ]
    return []


def _normalize_id_component(field: str, value: Any) -> JsonValue:
    if field == "verdict":
        return _verdict_value(value)
    if field == "reason_code":
        return validate_verdict_reason_code(value).value
    if field in {
        "blocking_issues",
        "warnings",
        "checked_artifacts",
        "checked_commands",
    }:
        return [cast(JsonValue, item) for item in value]
    return cast(JsonValue, value)


def _normalize_serialization_component(field: str, value: Any) -> JsonValue:
    if field == "verdict" and isinstance(value, ReviewerVerdictOutcome):
        return value.value
    if field == "reason_code":
        return validate_verdict_reason_code(value).value
    if field in {
        "blocking_issues",
        "warnings",
        "checked_artifacts",
        "checked_commands",
    }:
        return [cast(JsonValue, item) for item in value]
    return cast(JsonValue, value)


def _verdict_value(verdict: ReviewerVerdictOutcome | str | Any) -> str:
    try:
        return ReviewerVerdictOutcome(verdict).value
    except ValueError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="verdict",
                code="invalid_reviewer_verdict",
                message="ReviewerVerdict.verdict must use the closed review vocabulary",
                expected=" | ".join(outcome.value for outcome in ReviewerVerdictOutcome),
                actual=str(verdict),
            )
        ) from exc


def _parse_optional_reason_code(
    mapping: Mapping[str, Any],
    issues: list[ValidationIssue],
) -> VerdictReasonCode | None:
    if "reason_code" not in mapping:
        return None
    try:
        return validate_optional_verdict_reason_code(mapping["reason_code"])
    except GovernanceValidationError as exc:
        issues.extend(exc.issues)
        return None


def _normalize_text(value: object) -> str:
    if isinstance(value, str):
        return " ".join(value.strip().lower().split())
    return str(value).strip().lower()


__all__ = [
    "MERGE_ELIGIBLE_REVIEWER_VERDICTS",
    "REVIEWER_VERDICT_FIELD_TYPES",
    "REVIEWER_VERDICT_ALLOWED_FIELDS",
    "REVIEWER_VERDICT_ID_COMPONENT_FIELDS",
    "REVIEWER_VERDICT_IMPLIES_MARKET_TRUTH",
    "REVIEWER_VERDICT_IMPLIES_PRODUCTION_READINESS",
    "REVIEWER_VERDICT_IMPLIES_PROFITABILITY",
    "REVIEWER_VERDICT_IMPLIES_TRADABILITY",
    "REVIEWER_VERDICT_OPTIONAL_FIELDS",
    "REVIEWER_VERDICT_REQUIRED_FIELDS",
    "ReviewerVerdict",
    "ReviewerVerdictOutcome",
    "create_reviewer_verdict",
    "generate_reviewer_verdict_id",
    "validate_reviewer_verdict",
    "validate_reviewer_verdict_id",
]
