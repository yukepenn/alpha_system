"""PromotionDecision contract and promotion-gate entry points."""

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
    validate_required_fields,
    validate_schema,
)

PROMOTION_DECISION_REQUIRED_FIELDS = (
    "promotion_id",
    "alpha_spec_id",
    "evidence_bundle_id",
    "trial_ledger_refs",
    "previous_state",
    "next_state",
    "decision",
    "rationale",
    "reviewer_verdict_id",
    "warnings",
    "timestamp",
)
PROMOTION_DECISION_ID_COMPONENT_FIELDS = tuple(
    field for field in PROMOTION_DECISION_REQUIRED_FIELDS if field != "promotion_id"
)
PROMOTION_DECISION_FIELD_TYPES: dict[str, ExpectedType] = {
    "promotion_id": str,
    "alpha_spec_id": str,
    "evidence_bundle_id": str,
    "trial_ledger_refs": list,
    "previous_state": str,
    "next_state": str,
    "decision": str,
    "rationale": str,
    "reviewer_verdict_id": str,
    "warnings": list,
    "timestamp": str,
}
PROMOTION_REVIEW_SOURCE_STATE = "REVIEWED"
PROMOTION_DECISION_TARGET_STATES = (
    "REJECTED",
    "WATCH",
    "CANDIDATE",
    "VALIDATED",
)
PROHIBITED_MVP_STATES = (
    "LIVE_APPROVED",
    "CAPITAL_ALLOCATED",
    "PRODUCTION_READY",
)
PROMOTION_IMPLIES_LIVE_APPROVAL = False
PROMOTION_IMPLIES_CAPITAL_ALLOCATION = False
PROMOTION_IMPLIES_PRODUCTION_READINESS = False

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


class PromotionLifecycleState(StrEnum):
    """Reachable governance lifecycle states for the MVP promotion protocol."""

    DRAFT = "DRAFT"
    REGISTERED = "REGISTERED"
    IMPLEMENTATION_ALLOWED = "IMPLEMENTATION_ALLOWED"
    IMPLEMENTED = "IMPLEMENTED"
    DIAGNOSTICS_ALLOWED = "DIAGNOSTICS_ALLOWED"
    DIAGNOSTICS_RUN = "DIAGNOSTICS_RUN"
    EVIDENCE_READY = "EVIDENCE_READY"
    REVIEWED = "REVIEWED"
    REJECTED = "REJECTED"
    WATCH = "WATCH"
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"


class PromotionDecisionOutcome(StrEnum):
    """Closed target outcomes for a PromotionDecision."""

    REJECTED = "REJECTED"
    WATCH = "WATCH"
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"


GOVERNANCE_LIFECYCLE_STATES = tuple(state.value for state in PromotionLifecycleState)


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    """Validated metadata record for a reviewed lifecycle transition."""

    promotion_id: str
    alpha_spec_id: str
    evidence_bundle_id: str
    trial_ledger_refs: tuple[str, ...]
    previous_state: PromotionLifecycleState
    next_state: PromotionLifecycleState
    decision: PromotionDecisionOutcome
    rationale: str
    reviewer_verdict_id: str
    warnings: tuple[str, ...]
    timestamp: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> PromotionDecision:
        """Build a `PromotionDecision` from a mapping after fail-closed validation."""

        return validate_promotion_decision(payload)

    @classmethod
    def from_canonical_json(cls, text: str) -> PromotionDecision:
        """Deserialize canonical JSON and validate the resulting decision."""

        value = deserialize(text)
        mapping = require_mapping(value, object_name="PromotionDecision")
        return validate_promotion_decision(mapping)

    @property
    def implies_live_approval(self) -> bool:
        """PromotionDecision does not authorize live trading."""

        return PROMOTION_IMPLIES_LIVE_APPROVAL

    @property
    def implies_capital_allocation(self) -> bool:
        """PromotionDecision does not allocate capital."""

        return PROMOTION_IMPLIES_CAPITAL_ALLOCATION

    @property
    def implies_production_readiness(self) -> bool:
        """PromotionDecision does not mark production readiness."""

        return PROMOTION_IMPLIES_PRODUCTION_READINESS

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "promotion_id": self.promotion_id,
            "alpha_spec_id": self.alpha_spec_id,
            "evidence_bundle_id": self.evidence_bundle_id,
            "trial_ledger_refs": list(self.trial_ledger_refs),
            "previous_state": self.previous_state.value,
            "next_state": self.next_state.value,
            "decision": self.decision.value,
            "rationale": self.rationale,
            "reviewer_verdict_id": self.reviewer_verdict_id,
            "warnings": list(self.warnings),
            "timestamp": self.timestamp,
        }

    def to_canonical_json(self) -> str:
        """Serialize the validated decision through the canonical primitive."""

        return canonical_serialize(self.to_dict())


def create_promotion_decision(
    *,
    alpha_spec_id: str,
    evidence_bundle_id: str,
    trial_ledger_refs: list[str],
    previous_state: PromotionLifecycleState | str,
    next_state: PromotionLifecycleState | str,
    decision: PromotionDecisionOutcome | str,
    rationale: str,
    reviewer_verdict_id: str,
    warnings: list[str],
    timestamp: str,
) -> PromotionDecision:
    """Create a validated `PromotionDecision` without changing lifecycle state."""

    payload: dict[str, JsonValue] = {
        "alpha_spec_id": alpha_spec_id,
        "evidence_bundle_id": evidence_bundle_id,
        "trial_ledger_refs": list(trial_ledger_refs),
        "previous_state": _state_value(previous_state),
        "next_state": _state_value(next_state),
        "decision": _decision_value(decision),
        "rationale": rationale,
        "reviewer_verdict_id": reviewer_verdict_id,
        "warnings": list(warnings),
        "timestamp": timestamp,
    }
    payload["promotion_id"] = generate_promotion_decision_id(payload)
    return validate_promotion_decision(payload)


def generate_promotion_decision_id(payload: Mapping[str, Any]) -> str:
    """Generate the deterministic PromotionDecision ID from content fields."""

    mapping = validate_required_fields(
        payload,
        PROMOTION_DECISION_ID_COMPONENT_FIELDS,
        object_name="PromotionDecision",
    )
    components = {
        field: _normalize_id_component(field, mapping[field])
        for field in PROMOTION_DECISION_ID_COMPONENT_FIELDS
    }
    return generate_governance_id(GovernanceIdKind.PROMOTION_DECISION, components)


def validate_promotion_decision(payload: Mapping[str, Any]) -> PromotionDecision:
    """Validate a `PromotionDecision` mapping fail-closed and return a record."""

    mapping = validate_schema(
        payload,
        required_fields=PROMOTION_DECISION_REQUIRED_FIELDS,
        field_types=PROMOTION_DECISION_FIELD_TYPES,
        allowed_fields=PROMOTION_DECISION_REQUIRED_FIELDS,
        object_name="PromotionDecision",
    )

    issues: list[ValidationIssue] = []
    issues.extend(_validate_ids(mapping))
    issues.extend(_validate_trial_ledger_refs(mapping["trial_ledger_refs"]))
    previous_state = _parse_lifecycle_state(mapping["previous_state"], "previous_state", issues)
    next_state = _parse_lifecycle_state(mapping["next_state"], "next_state", issues)
    decision = _parse_decision(mapping["decision"], issues)
    issues.extend(_validate_text_field(mapping, "rationale"))
    issues.extend(_validate_warnings(mapping["warnings"]))
    issues.extend(_validate_timestamp(mapping["timestamp"]))
    issues.extend(_validate_canonical_serializable(mapping))

    if previous_state is not None and previous_state.value != PROMOTION_REVIEW_SOURCE_STATE:
        issues.append(
            ValidationIssue(
                field="previous_state",
                code="invalid_promotion_source_state",
                message="PromotionDecision.previous_state must be REVIEWED",
                expected=PROMOTION_REVIEW_SOURCE_STATE,
                actual=previous_state.value,
            )
        )
    if next_state is not None and next_state.value not in PROMOTION_DECISION_TARGET_STATES:
        issues.append(
            ValidationIssue(
                field="next_state",
                code="invalid_promotion_target_state",
                message="PromotionDecision.next_state must be a declared promotion target",
                expected=" | ".join(PROMOTION_DECISION_TARGET_STATES),
                actual=next_state.value,
            )
        )
    if decision is not None and next_state is not None and decision.value != next_state.value:
        issues.append(
            ValidationIssue(
                field="decision",
                code="decision_target_mismatch",
                message="PromotionDecision.decision must match next_state",
                expected=next_state.value,
                actual=decision.value,
            )
        )

    if not issues:
        expected_id = generate_promotion_decision_id(mapping)
        if mapping["promotion_id"] != expected_id:
            issues.append(
                ValidationIssue(
                    field="promotion_id",
                    code="promotion_id_mismatch",
                    message=(
                        "PromotionDecision.promotion_id must match deterministic "
                        "PromotionDecision content"
                    ),
                    expected=expected_id,
                    actual=str(mapping["promotion_id"]),
                )
            )

    if issues:
        raise GovernanceValidationError(issues)

    assert previous_state is not None
    assert next_state is not None
    assert decision is not None
    return PromotionDecision(
        promotion_id=mapping["promotion_id"],
        alpha_spec_id=mapping["alpha_spec_id"],
        evidence_bundle_id=mapping["evidence_bundle_id"],
        trial_ledger_refs=tuple(mapping["trial_ledger_refs"]),
        previous_state=previous_state,
        next_state=next_state,
        decision=decision,
        rationale=mapping["rationale"],
        reviewer_verdict_id=mapping["reviewer_verdict_id"],
        warnings=tuple(mapping["warnings"]),
        timestamp=mapping["timestamp"],
    )


def validate_promotion_transition(*args: Any, **kwargs: Any) -> Any:
    """Entry point for the promotion-gate state machine.

    The import stays local so `promotion_gate` can import the PromotionDecision
    object without a module-load cycle.
    """

    from alpha_system.governance.promotion_gate import validate_governance_transition

    return validate_governance_transition(*args, **kwargs)


def _validate_ids(mapping: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    id_checks = (
        ("promotion_id", GovernanceIdKind.PROMOTION_DECISION),
        ("alpha_spec_id", GovernanceIdKind.ALPHA_SPEC),
        ("evidence_bundle_id", GovernanceIdKind.EVIDENCE_BUNDLE),
        ("reviewer_verdict_id", GovernanceIdKind.REVIEWER_VERDICT),
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


def _validate_trial_ledger_refs(values: list[Any]) -> list[ValidationIssue]:
    if not values:
        return [
            ValidationIssue(
                field="trial_ledger_refs",
                code="empty_required_field",
                message="PromotionDecision.trial_ledger_refs must reference TrialLedger records",
                expected="non-empty list of TrialLedgerRecord IDs",
                actual="empty list",
            )
        ]

    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        field = f"trial_ledger_refs[{index}]"
        if type(item) is not str:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_item_type",
                    message=f"PromotionDecision.{field} must be a string",
                    expected="TrialLedgerRecord ID string",
                    actual=type(item).__name__,
                )
            )
            continue
        try:
            validate_governance_id(item, expected_kind=GovernanceIdKind.TRIAL_LEDGER_RECORD)
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
        if item in seen:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="duplicate_trial_ledger_ref",
                    message="PromotionDecision.trial_ledger_refs must be unique",
                    expected="unique TrialLedgerRecord IDs",
                    actual=item,
                )
            )
        seen.add(item)
    return issues


def _parse_lifecycle_state(
    value: Any,
    field: str,
    issues: list[ValidationIssue],
) -> PromotionLifecycleState | None:
    if value in PROHIBITED_MVP_STATES:
        issues.append(
            ValidationIssue(
                field=field,
                code="prohibited_mvp_state",
                message=f"{value} is not reachable in the governance MVP",
                expected=" | ".join(GOVERNANCE_LIFECYCLE_STATES),
                actual=str(value),
            )
        )
        return None
    try:
        return PromotionLifecycleState(value)
    except ValueError:
        issues.append(
            ValidationIssue(
                field=field,
                code="invalid_lifecycle_state",
                message="PromotionDecision state fields must use declared lifecycle states",
                expected=" | ".join(GOVERNANCE_LIFECYCLE_STATES),
                actual=str(value),
            )
        )
        return None


def _parse_decision(
    value: Any,
    issues: list[ValidationIssue],
) -> PromotionDecisionOutcome | None:
    try:
        return PromotionDecisionOutcome(value)
    except ValueError:
        issues.append(
            ValidationIssue(
                field="decision",
                code="invalid_promotion_decision",
                message="PromotionDecision.decision must be a declared promotion outcome",
                expected=" | ".join(outcome.value for outcome in PromotionDecisionOutcome),
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
            message=f"PromotionDecision.{field} must be explicit",
            expected="non-empty explicit string",
            actual=str(value),
        )
    ]


def _validate_warnings(values: list[Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        field = f"warnings[{index}]"
        if type(item) is not str:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_item_type",
                    message=f"PromotionDecision.{field} must be a string",
                    expected="explicit warning string",
                    actual=type(item).__name__,
                )
            )
            continue
        if _normalize_text(item) in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="empty_required_field",
                    message=f"PromotionDecision.{field} must be explicit when present",
                    expected="non-empty explicit warning",
                    actual=item,
                )
            )
            continue
        if item in seen:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="duplicate_warning",
                    message="PromotionDecision.warnings must not contain duplicate entries",
                    expected="unique explicit warnings",
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
                message="PromotionDecision.timestamp must be explicit",
                expected="UTC timestamp in YYYY-MM-DDTHH:MM:SSZ format",
                actual=str(value),
            )
        ]
    if _UTC_SECONDS_PATTERN.fullmatch(value) is None:
        return [
            ValidationIssue(
                field="timestamp",
                code="invalid_timestamp",
                message="PromotionDecision.timestamp must use UTC YYYY-MM-DDTHH:MM:SSZ format",
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
                message="PromotionDecision.timestamp must be a real UTC timestamp",
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
                for field in PROMOTION_DECISION_REQUIRED_FIELDS
                if field in mapping
            }
        )
    except GovernanceSerializationError as exc:
        return [
            ValidationIssue(
                field=exc.issue.path,
                code=exc.issue.code,
                message=exc.issue.message,
                expected="canonical JSON-compatible PromotionDecision",
                actual=exc.issue.path,
            )
        ]
    return []


def _normalize_id_component(field: str, value: Any) -> JsonValue:
    if field in {"previous_state", "next_state"}:
        return _state_value(value)
    if field == "decision":
        return _decision_value(value)
    if field in {"trial_ledger_refs", "warnings"}:
        return [cast(JsonValue, item) for item in value]
    return cast(JsonValue, value)


def _normalize_serialization_component(field: str, value: Any) -> JsonValue:
    if field in {"previous_state", "next_state"} and isinstance(value, PromotionLifecycleState):
        return value.value
    if field == "decision" and isinstance(value, PromotionDecisionOutcome):
        return value.value
    if field in {"trial_ledger_refs", "warnings"}:
        return [cast(JsonValue, item) for item in value]
    return cast(JsonValue, value)


def _state_value(state: PromotionLifecycleState | str | Any) -> str:
    try:
        return PromotionLifecycleState(state).value
    except ValueError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="state",
                code="invalid_lifecycle_state",
                message="promotion states must be declared lifecycle states",
                expected=" | ".join(GOVERNANCE_LIFECYCLE_STATES),
                actual=str(state),
            )
        ) from exc


def _decision_value(decision: PromotionDecisionOutcome | str | Any) -> str:
    try:
        return PromotionDecisionOutcome(decision).value
    except ValueError as exc:
        raise GovernanceValidationError(
            ValidationIssue(
                field="decision",
                code="invalid_promotion_decision",
                message="PromotionDecision.decision must be a declared promotion outcome",
                expected=" | ".join(outcome.value for outcome in PromotionDecisionOutcome),
                actual=str(decision),
            )
        ) from exc


def _normalize_text(value: object) -> str:
    if isinstance(value, str):
        return " ".join(value.strip().lower().split())
    return str(value).strip().lower()


__all__ = [
    "GOVERNANCE_LIFECYCLE_STATES",
    "PROHIBITED_MVP_STATES",
    "PROMOTION_DECISION_ID_COMPONENT_FIELDS",
    "PROMOTION_DECISION_REQUIRED_FIELDS",
    "PROMOTION_DECISION_TARGET_STATES",
    "PROMOTION_IMPLIES_CAPITAL_ALLOCATION",
    "PROMOTION_IMPLIES_LIVE_APPROVAL",
    "PROMOTION_IMPLIES_PRODUCTION_READINESS",
    "PROMOTION_REVIEW_SOURCE_STATE",
    "PromotionDecision",
    "PromotionDecisionOutcome",
    "PromotionLifecycleState",
    "create_promotion_decision",
    "generate_promotion_decision_id",
    "validate_promotion_decision",
    "validate_promotion_transition",
]
