"""Promotion-gate state machine for the governance lifecycle."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from alpha_system.governance.alpha_spec import AlphaSpec, validate_no_code_gate
from alpha_system.governance.evidence_bundle import (
    EvidenceBundle,
    validate_evidence_bundle,
    validate_evidence_ready_gate,
)
from alpha_system.governance.hypothesis_card import (
    HypothesisCard,
    validate_pre_registration,
)
from alpha_system.governance.ids import (
    GovernanceIdError,
    GovernanceIdKind,
    validate_governance_id,
)
from alpha_system.governance.promotion import (
    GOVERNANCE_LIFECYCLE_STATES,
    PROHIBITED_MVP_STATES,
    PROMOTION_DECISION_TARGET_STATES,
    PROMOTION_REVIEW_SOURCE_STATE,
    PromotionDecision,
    PromotionLifecycleState,
    validate_promotion_decision,
)
from alpha_system.governance.rejected_idea import (
    RejectedIdeaRecord,
    validate_rejected_idea_record,
)
from alpha_system.governance.study_spec import StudySpec, validate_diagnostics_gate
from alpha_system.governance.trial_ledger import (
    FAILED_TRIAL_STATUSES,
    TrialLedgerRecord,
    validate_trial_ledger_record,
)
from alpha_system.governance.validation import (
    GovernanceValidationError,
    ValidationIssue,
)

IMPLEMENTATION_HANDOFF_REQUIRED_STATE = "IMPLEMENTED"
DIAGNOSTICS_RUN_REQUIRED_STATE = "DIAGNOSTICS_RUN"
REVIEWER_VERDICT_INDEPENDENCE_DEFERRED_TO = "ARGOV-P12"

ALLOWED_TRANSITIONS = MappingProxyType(
    {
        "DRAFT": ("REGISTERED",),
        "REGISTERED": ("IMPLEMENTATION_ALLOWED",),
        "IMPLEMENTATION_ALLOWED": ("IMPLEMENTED",),
        "IMPLEMENTED": ("DIAGNOSTICS_ALLOWED",),
        "DIAGNOSTICS_ALLOWED": ("DIAGNOSTICS_RUN",),
        "DIAGNOSTICS_RUN": ("EVIDENCE_READY",),
        "EVIDENCE_READY": ("REVIEWED",),
        "REVIEWED": PROMOTION_DECISION_TARGET_STATES,
    }
)
REACHABLE_STATES = GOVERNANCE_LIFECYCLE_STATES

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
class PromotionGateContext:
    """Inputs used by pure lifecycle transition validation."""

    hypothesis_card: HypothesisCard | Mapping[str, Any] | None = None
    alpha_spec: AlphaSpec | Mapping[str, Any] | None = None
    duplicate_or_leakage_check_passed: bool | None = None
    implementation_handoff_ref: str | None = None
    study_spec: StudySpec | Mapping[str, Any] | None = None
    trial_ledger_records: tuple[TrialLedgerRecord | Mapping[str, Any], ...] = ()
    evidence_bundle: EvidenceBundle | Mapping[str, Any] | None = None
    reviewer_verdict_id: str | None = None
    promotion_decision: PromotionDecision | Mapping[str, Any] | None = None
    rejected_idea_record: RejectedIdeaRecord | Mapping[str, Any] | None = None
    rejection_reason: str | None = None
    locked_test_contamination_metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class GovernanceTransition:
    """Validated lifecycle transition metadata."""

    previous_state: PromotionLifecycleState
    next_state: PromotionLifecycleState
    promotion_decision: PromotionDecision | None = None
    evidence_bundle: EvidenceBundle | None = None
    rejected_idea_record: RejectedIdeaRecord | None = None
    trial_ledger_refs: tuple[str, ...] = ()
    reviewer_verdict_id: str = ""

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible summary of the accepted transition."""

        return {
            "previous_state": self.previous_state.value,
            "next_state": self.next_state.value,
            "promotion_decision_id": (
                self.promotion_decision.promotion_id if self.promotion_decision is not None else ""
            ),
            "evidence_bundle_id": (
                self.evidence_bundle.evidence_bundle_id if self.evidence_bundle is not None else ""
            ),
            "rejected_id": (
                self.rejected_idea_record.rejected_id
                if self.rejected_idea_record is not None
                else ""
            ),
            "trial_ledger_refs": list(self.trial_ledger_refs),
            "reviewer_verdict_id": self.reviewer_verdict_id,
        }


def validate_governance_transition(
    from_state: PromotionLifecycleState | str,
    to_state: PromotionLifecycleState | str,
    context: PromotionGateContext | None = None,
) -> GovernanceTransition:
    """Validate one governance lifecycle transition and fail closed."""

    active_context = context or PromotionGateContext()
    issues: list[ValidationIssue] = []
    previous_state = _parse_state(from_state, "from_state", issues)
    next_state = _parse_state(to_state, "to_state", issues)
    if issues:
        raise GovernanceValidationError(issues)
    assert previous_state is not None
    assert next_state is not None

    if not _transition_is_allowed(previous_state, next_state):
        raise GovernanceValidationError(
            ValidationIssue(
                field="transition",
                code="invalid_transition",
                message="governance lifecycle transition is not declared",
                expected=_expected_targets(previous_state),
                actual=f"{previous_state.value}->{next_state.value}",
            )
        )

    if next_state is PromotionLifecycleState.REJECTED:
        return _validate_rejected_transition(previous_state, next_state, active_context)

    if previous_state is PromotionLifecycleState.DRAFT:
        validate_pre_registration(
            active_context.hypothesis_card,
            active_context.alpha_spec,
        )
        return GovernanceTransition(previous_state, next_state)

    if previous_state is PromotionLifecycleState.REGISTERED:
        validate_no_code_gate(active_context.alpha_spec)
        _validate_duplicate_leakage_clearance(active_context)
        return GovernanceTransition(previous_state, next_state)

    if previous_state is PromotionLifecycleState.IMPLEMENTATION_ALLOWED:
        _validate_implementation_handoff(active_context)
        return GovernanceTransition(previous_state, next_state)

    if previous_state is PromotionLifecycleState.IMPLEMENTED:
        validate_diagnostics_gate(active_context.study_spec)
        return GovernanceTransition(previous_state, next_state)

    if previous_state is PromotionLifecycleState.DIAGNOSTICS_ALLOWED:
        trial_records = _validate_trial_records(
            active_context.trial_ledger_records,
            require_non_empty=True,
        )
        return GovernanceTransition(
            previous_state,
            next_state,
            trial_ledger_refs=tuple(record.trial_id for record in trial_records),
        )

    if previous_state is PromotionLifecycleState.DIAGNOSTICS_RUN:
        evidence_bundle = validate_evidence_ready_gate(active_context.evidence_bundle)
        return GovernanceTransition(
            previous_state,
            next_state,
            evidence_bundle=evidence_bundle,
            trial_ledger_refs=tuple(evidence_bundle.trial_ids),
        )

    if previous_state is PromotionLifecycleState.EVIDENCE_READY:
        reviewer_verdict_id = _validate_reviewer_verdict_id(
            active_context.reviewer_verdict_id,
        )
        return GovernanceTransition(
            previous_state,
            next_state,
            reviewer_verdict_id=reviewer_verdict_id,
        )

    if previous_state is PromotionLifecycleState.REVIEWED:
        promotion_decision = _validate_reviewed_promotion_decision(
            next_state,
            active_context,
        )
        if next_state in {
            PromotionLifecycleState.CANDIDATE,
            PromotionLifecycleState.VALIDATED,
        }:
            evidence_bundle, trial_refs = _validate_candidate_or_validated_gate(
                promotion_decision,
                active_context,
            )
            return GovernanceTransition(
                previous_state,
                next_state,
                promotion_decision=promotion_decision,
                evidence_bundle=evidence_bundle,
                trial_ledger_refs=trial_refs,
                reviewer_verdict_id=promotion_decision.reviewer_verdict_id,
            )
        return GovernanceTransition(
            previous_state,
            next_state,
            promotion_decision=promotion_decision,
            trial_ledger_refs=promotion_decision.trial_ledger_refs,
            reviewer_verdict_id=promotion_decision.reviewer_verdict_id,
        )

    raise GovernanceValidationError(
        ValidationIssue(
            field="transition",
            code="unhandled_transition",
            message="governance lifecycle transition has no implemented handler",
            expected="declared transition handler",
            actual=f"{previous_state.value}->{next_state.value}",
        )
    )


def assert_promotion_gate(
    from_state: PromotionLifecycleState | str,
    to_state: PromotionLifecycleState | str,
    context: PromotionGateContext | None = None,
) -> GovernanceTransition:
    """Alias for fail-closed state-machine validation."""

    return validate_governance_transition(from_state, to_state, context)


def reachable_states() -> tuple[str, ...]:
    """Return all reachable MVP lifecycle states."""

    return REACHABLE_STATES


def prohibited_mvp_states() -> tuple[str, ...]:
    """Return future-only state names that are not reachable in this MVP."""

    return PROHIBITED_MVP_STATES


def reachable_transition_targets(from_state: PromotionLifecycleState | str) -> tuple[str, ...]:
    """Return declared targets for a reachable source state."""

    previous_state = _parse_state_or_raise(from_state, field="from_state")
    targets = set(ALLOWED_TRANSITIONS.get(previous_state.value, ()))
    targets.add(PromotionLifecycleState.REJECTED.value)
    return tuple(sorted(targets))


def _validate_rejected_transition(
    previous_state: PromotionLifecycleState,
    next_state: PromotionLifecycleState,
    context: PromotionGateContext,
) -> GovernanceTransition:
    rejected_record = _validate_rejected_record(context.rejected_idea_record)
    _validate_rejection_reason(context.rejection_reason)
    promotion_decision = None
    if previous_state is PromotionLifecycleState.REVIEWED:
        promotion_decision = _validate_reviewed_promotion_decision(next_state, context)
    return GovernanceTransition(
        previous_state,
        next_state,
        promotion_decision=promotion_decision,
        rejected_idea_record=rejected_record,
        trial_ledger_refs=(
            promotion_decision.trial_ledger_refs if promotion_decision is not None else ()
        ),
        reviewer_verdict_id=(
            promotion_decision.reviewer_verdict_id if promotion_decision is not None else ""
        ),
    )


def _validate_reviewed_promotion_decision(
    next_state: PromotionLifecycleState,
    context: PromotionGateContext,
) -> PromotionDecision:
    if context.promotion_decision is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="promotion_decision",
                code="missing_promotion_decision",
                message="PromotionDecision is required for REVIEWED promotion decisions",
                expected="validated PromotionDecision",
                actual="missing",
            )
        )
    if isinstance(context.promotion_decision, PromotionDecision):
        promotion_decision = validate_promotion_decision(context.promotion_decision.to_dict())
    else:
        promotion_decision = validate_promotion_decision(context.promotion_decision)

    issues: list[ValidationIssue] = []
    if promotion_decision.previous_state.value != PROMOTION_REVIEW_SOURCE_STATE:
        issues.append(
            ValidationIssue(
                field="promotion_decision.previous_state",
                code="promotion_decision_source_mismatch",
                message="PromotionDecision.previous_state must match the transition source",
                expected=PROMOTION_REVIEW_SOURCE_STATE,
                actual=promotion_decision.previous_state.value,
            )
        )
    if promotion_decision.next_state is not next_state:
        issues.append(
            ValidationIssue(
                field="promotion_decision.next_state",
                code="promotion_decision_target_mismatch",
                message="PromotionDecision.next_state must match the transition target",
                expected=next_state.value,
                actual=promotion_decision.next_state.value,
            )
        )
    if issues:
        raise GovernanceValidationError(issues)
    return promotion_decision


def _validate_candidate_or_validated_gate(
    promotion_decision: PromotionDecision,
    context: PromotionGateContext,
) -> tuple[EvidenceBundle, tuple[str, ...]]:
    issues: list[ValidationIssue] = []
    evidence_bundle = _validate_required_evidence_bundle(context.evidence_bundle, issues)
    trial_records = _validate_trial_records(
        context.trial_ledger_records,
        require_non_empty=False,
        issues=issues,
    )
    if not trial_records:
        issues.append(
            ValidationIssue(
                field="trial_ledger_records",
                code="missing_trial_ledger_records",
                message="complete TrialLedger records are required before promotion",
                expected="one or more validated TrialLedgerRecord entries",
                actual="missing",
            )
        )

    if evidence_bundle is not None:
        if promotion_decision.evidence_bundle_id != evidence_bundle.evidence_bundle_id:
            issues.append(
                ValidationIssue(
                    field="evidence_bundle_id",
                    code="evidence_bundle_id_mismatch",
                    message="PromotionDecision.evidence_bundle_id must match the EvidenceBundle",
                    expected=evidence_bundle.evidence_bundle_id,
                    actual=promotion_decision.evidence_bundle_id,
                )
            )
        if promotion_decision.alpha_spec_id != evidence_bundle.alpha_spec_id:
            issues.append(
                ValidationIssue(
                    field="alpha_spec_id",
                    code="alpha_spec_id_mismatch",
                    message="PromotionDecision.alpha_spec_id must match the EvidenceBundle",
                    expected=evidence_bundle.alpha_spec_id,
                    actual=promotion_decision.alpha_spec_id,
                )
            )

    if trial_records and evidence_bundle is not None:
        issues.extend(
            _validate_complete_trial_reference_set(
                promotion_decision,
                evidence_bundle,
                trial_records,
            )
        )
        issues.extend(
            _validate_locked_test_contamination_metadata(
                trial_records,
                context.locked_test_contamination_metadata,
            )
        )

    if issues:
        raise GovernanceValidationError(issues)
    assert evidence_bundle is not None
    return evidence_bundle, tuple(promotion_decision.trial_ledger_refs)


def _validate_required_evidence_bundle(
    value: EvidenceBundle | Mapping[str, Any] | None,
    issues: list[ValidationIssue],
) -> EvidenceBundle | None:
    if value is None:
        issues.append(
            ValidationIssue(
                field="evidence_bundle",
                code="missing_evidence_bundle",
                message="valid EvidenceBundle is required before candidate or validated status",
                expected="validated EvidenceBundle",
                actual="missing",
            )
        )
        return None
    try:
        if isinstance(value, EvidenceBundle):
            return validate_evidence_bundle(value.to_dict())
        return validate_evidence_bundle(value)
    except GovernanceValidationError as exc:
        issues.extend(exc.issues)
        return None


def _validate_trial_records(
    values: Iterable[TrialLedgerRecord | Mapping[str, Any]],
    *,
    require_non_empty: bool,
    issues: list[ValidationIssue] | None = None,
) -> tuple[TrialLedgerRecord, ...]:
    active_issues: list[ValidationIssue] = [] if issues is None else issues
    if isinstance(values, Mapping) or isinstance(values, str) or values is None:
        active_issues.append(
            ValidationIssue(
                field="trial_ledger_records",
                code="invalid_trial_ledger_records_type",
                message="trial ledger records must be an iterable of TrialLedgerRecord mappings",
                expected="iterable of TrialLedgerRecord or mapping",
                actual=type(values).__name__,
            )
        )
        if issues is None:
            raise GovernanceValidationError(active_issues)
        return ()

    validated: list[TrialLedgerRecord] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        try:
            record = (
                validate_trial_ledger_record(item.to_dict())
                if isinstance(item, TrialLedgerRecord)
                else validate_trial_ledger_record(item)
            )
        except GovernanceValidationError as exc:
            active_issues.extend(exc.issues)
            continue
        if record.trial_id in seen:
            active_issues.append(
                ValidationIssue(
                    field=f"trial_ledger_records[{index}].trial_id",
                    code="duplicate_trial_ledger_record",
                    message="trial ledger records must not repeat a TrialLedgerRecord ID",
                    expected="unique TrialLedgerRecord IDs",
                    actual=record.trial_id,
                )
            )
        seen.add(record.trial_id)
        validated.append(record)

    if require_non_empty and not validated:
        active_issues.append(
            ValidationIssue(
                field="trial_ledger_records",
                code="missing_trial_ledger_records",
                message="diagnostics runs must be recorded in the TrialLedger",
                expected="one or more validated TrialLedgerRecord entries",
                actual="empty",
            )
        )

    if active_issues and issues is None:
        raise GovernanceValidationError(active_issues)
    return tuple(validated)


def _validate_complete_trial_reference_set(
    promotion_decision: PromotionDecision,
    evidence_bundle: EvidenceBundle,
    trial_records: tuple[TrialLedgerRecord, ...],
) -> list[ValidationIssue]:
    record_ids = {record.trial_id for record in trial_records}
    decision_refs = set(promotion_decision.trial_ledger_refs)
    evidence_refs = set(evidence_bundle.trial_ids)
    failed_record_ids = {
        record.trial_id for record in trial_records if record.status in FAILED_TRIAL_STATUSES
    }
    missing_failed_from_decision = failed_record_ids - decision_refs
    missing_failed_from_evidence = failed_record_ids - evidence_refs
    if missing_failed_from_decision or missing_failed_from_evidence:
        return [
            ValidationIssue(
                field="trial_ledger_refs",
                code="failed_run_omission",
                message="failed and abandoned TrialLedger records must remain referenced",
                expected=", ".join(sorted(failed_record_ids)),
                actual=(
                    "decision missing "
                    f"{sorted(missing_failed_from_decision)}; evidence missing "
                    f"{sorted(missing_failed_from_evidence)}"
                ),
            )
        ]

    issues: list[ValidationIssue] = []
    if decision_refs != record_ids:
        issues.append(
            ValidationIssue(
                field="trial_ledger_refs",
                code="trial_ledger_ref_set_incomplete",
                message="PromotionDecision.trial_ledger_refs must match all TrialLedger records",
                expected=", ".join(sorted(record_ids)),
                actual=", ".join(sorted(decision_refs)),
            )
        )
    if evidence_refs != record_ids:
        issues.append(
            ValidationIssue(
                field="evidence_bundle.trial_ids",
                code="evidence_bundle_trial_ref_set_incomplete",
                message="EvidenceBundle.trial_ids must match all TrialLedger records",
                expected=", ".join(sorted(record_ids)),
                actual=", ".join(sorted(evidence_refs)),
            )
        )
    return issues


def _validate_locked_test_contamination_metadata(
    trial_records: tuple[TrialLedgerRecord, ...],
    metadata: Mapping[str, Any] | None,
) -> list[ValidationIssue]:
    contaminated_ids = [
        record.trial_id for record in trial_records if record.locked_test_contamination_flag
    ]
    if not contaminated_ids:
        return []
    metadata_issues = _validate_substantive_metadata(
        metadata,
        field="locked_test_contamination_metadata",
    )
    if metadata_issues:
        return [
            ValidationIssue(
                field="locked_test_contamination_metadata",
                code="unrecorded_locked_test_contamination",
                message=("locked-test contamination must have explicit metadata before promotion"),
                expected=", ".join(contaminated_ids),
                actual="missing or non-substantive metadata",
            )
        ]
    return []


def _validate_duplicate_leakage_clearance(context: PromotionGateContext) -> None:
    if context.duplicate_or_leakage_check_passed is True:
        return
    if context.duplicate_or_leakage_check_passed is False:
        raise GovernanceValidationError(
            ValidationIssue(
                field="duplicate_or_leakage_check_passed",
                code="blocking_duplicate_or_leakage_issue",
                message="blocking duplicate or leakage issue prevents implementation",
                expected="True",
                actual="False",
            )
        )
    raise GovernanceValidationError(
        ValidationIssue(
            field="duplicate_or_leakage_check_passed",
            code="missing_duplicate_leakage_clearance",
            message="duplicate and leakage clearance must be explicit",
            expected="True after checks",
            actual="missing",
        )
    )


def _validate_implementation_handoff(context: PromotionGateContext) -> None:
    if _is_substantive_text(context.implementation_handoff_ref):
        return
    raise GovernanceValidationError(
        ValidationIssue(
            field="implementation_handoff_ref",
            code="missing_implementation_handoff",
            message="scoped implementation handoff reference is required",
            expected="explicit handoff reference",
            actual=str(context.implementation_handoff_ref),
        )
    )


def _validate_reviewer_verdict_id(value: str | None) -> str:
    if value is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="reviewer_verdict_id",
                code="missing_reviewer_verdict_id",
                message="ReviewerVerdict ID is required before REVIEWED status",
                expected=GovernanceIdKind.REVIEWER_VERDICT.value,
                actual="missing",
            )
        )
    try:
        validate_governance_id(value, expected_kind=GovernanceIdKind.REVIEWER_VERDICT)
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
    return value


def _validate_rejected_record(
    value: RejectedIdeaRecord | Mapping[str, Any] | None,
) -> RejectedIdeaRecord:
    if value is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="rejected_idea_record",
                code="missing_rejected_idea_record",
                message="RejectedIdeaRecord is required for transition to REJECTED",
                expected="validated RejectedIdeaRecord",
                actual="missing",
            )
        )
    if isinstance(value, RejectedIdeaRecord):
        return validate_rejected_idea_record(value.to_dict())
    return validate_rejected_idea_record(value)


def _validate_rejection_reason(value: str | None) -> None:
    if _is_substantive_text(value):
        return
    raise GovernanceValidationError(
        ValidationIssue(
            field="rejection_reason",
            code="missing_rejection_reason",
            message="explicit rejection reason is required for transition to REJECTED",
            expected="non-empty explicit reason",
            actual=str(value),
        )
    )


def _validate_substantive_metadata(
    metadata: Mapping[str, Any] | None,
    *,
    field: str,
) -> list[ValidationIssue]:
    if metadata is None or not isinstance(metadata, Mapping) or not metadata:
        return [
            ValidationIssue(
                field=field,
                code="missing_metadata",
                message=f"{field} must contain explicit metadata",
                expected="non-empty mapping",
                actual=type(metadata).__name__,
            )
        ]
    issues: list[ValidationIssue] = []
    for key, value in metadata.items():
        key_field = f"{field}.{key}"
        if not isinstance(key, str) or _normalize_text(key) in _VAGUE_TEXT:
            issues.append(
                ValidationIssue(
                    field=field,
                    code="invalid_metadata_key",
                    message=f"{field} keys must be explicit strings",
                    expected="non-empty explicit string key",
                    actual=str(key),
                )
            )
            continue
        if isinstance(value, str):
            if _normalize_text(value) in _VAGUE_TEXT:
                issues.append(
                    ValidationIssue(
                        field=key_field,
                        code="vague_metadata_value",
                        message=f"{key_field} must be explicit",
                        expected="substantive metadata value",
                        actual=value,
                    )
                )
        elif value is None:
            issues.append(
                ValidationIssue(
                    field=key_field,
                    code="null_metadata_value",
                    message=f"{key_field} must not be null",
                    expected="substantive metadata value",
                    actual="NoneType",
                )
            )
    return issues


def _transition_is_allowed(
    previous_state: PromotionLifecycleState,
    next_state: PromotionLifecycleState,
) -> bool:
    if next_state is PromotionLifecycleState.REJECTED:
        return True
    return next_state.value in ALLOWED_TRANSITIONS.get(previous_state.value, ())


def _parse_state(
    value: PromotionLifecycleState | str,
    field: str,
    issues: list[ValidationIssue],
) -> PromotionLifecycleState | None:
    if value in PROHIBITED_MVP_STATES:
        issues.append(
            ValidationIssue(
                field=field,
                code="prohibited_mvp_state",
                message=f"{value} is prohibited and unreachable in the governance MVP",
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
                message="governance transition states must be declared lifecycle states",
                expected=" | ".join(GOVERNANCE_LIFECYCLE_STATES),
                actual=str(value),
            )
        )
        return None


def _parse_state_or_raise(
    value: PromotionLifecycleState | str,
    *,
    field: str,
) -> PromotionLifecycleState:
    issues: list[ValidationIssue] = []
    state = _parse_state(value, field, issues)
    if issues:
        raise GovernanceValidationError(issues)
    assert state is not None
    return state


def _expected_targets(previous_state: PromotionLifecycleState) -> str:
    targets = reachable_transition_targets(previous_state)
    return " | ".join(targets) if targets else "no declared transition"


def _is_substantive_text(value: object) -> bool:
    return isinstance(value, str) and _normalize_text(value) not in _VAGUE_TEXT


def _normalize_text(value: object) -> str:
    if isinstance(value, str):
        return " ".join(value.strip().lower().split())
    return str(value).strip().lower()


__all__ = [
    "ALLOWED_TRANSITIONS",
    "IMPLEMENTATION_HANDOFF_REQUIRED_STATE",
    "DIAGNOSTICS_RUN_REQUIRED_STATE",
    "REACHABLE_STATES",
    "REVIEWER_VERDICT_INDEPENDENCE_DEFERRED_TO",
    "GovernanceTransition",
    "PromotionGateContext",
    "assert_promotion_gate",
    "prohibited_mvp_states",
    "reachable_states",
    "reachable_transition_targets",
    "validate_governance_transition",
]
