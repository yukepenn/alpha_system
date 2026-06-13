"""Promotion-gate state machine for the governance lifecycle."""

from __future__ import annotations

import json
import stat
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
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
from alpha_system.governance.promotion import (
    GOVERNANCE_LIFECYCLE_STATES,
    PROHIBITED_MVP_STATES,
    PROMOTION_DECISION_TARGET_STATES,
    PROMOTION_REVIEW_SOURCE_STATE,
    PromotionDecision,
    PromotionLifecycleState,
    reject_exploratory_promotion_artifacts,
    validate_promotion_decision,
)
from alpha_system.governance.rejected_idea import (
    RejectedIdeaRecord,
    validate_rejected_idea_record,
)
from alpha_system.governance.reviewer_verdict import (
    MERGE_ELIGIBLE_REVIEWER_VERDICTS,
    ReviewerVerdict,
    validate_reviewer_verdict,
)
from alpha_system.governance.sealed_holdout import (
    SealedHoldoutRegistry,
    SealedHoldoutStatus,
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
from alpha_system.governance.variant_ledger import (
    BudgetAmendmentRecord,
    validate_variant_and_family_budget,
)

IMPLEMENTATION_HANDOFF_REQUIRED_STATE = "IMPLEMENTED"
DIAGNOSTICS_RUN_REQUIRED_STATE = "DIAGNOSTICS_RUN"
POSITIVE_PROMOTION_TARGET_STATES = (
    "CANDIDATE",
    "VALIDATED",
)

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
    reviewer_verdict: ReviewerVerdict | Mapping[str, Any] | None = None
    implementer_id: str | None = None
    implementer_role: str | None = None
    promotion_decision: PromotionDecision | Mapping[str, Any] | None = None
    rejected_idea_record: RejectedIdeaRecord | Mapping[str, Any] | None = None
    rejection_reason: str | None = None
    locked_test_contamination_metadata: Mapping[str, Any] | None = None
    trial_ledger_path: str | Path | None = None
    family_id: str | None = None
    variant_ledger_path: str | Path | None = None
    budget_amendments: tuple[BudgetAmendmentRecord | Mapping[str, Any], ...] = ()
    sealed_holdout_registry_path: str | Path | None = None
    require_sealed_holdout: bool = False
    promotion_artifacts: tuple[Any, ...] = ()


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
    _reject_exploratory_artifacts(active_context)

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
        _validate_variant_budget_context(
            active_context,
            trial_records=trial_records,
            persist=True,
            require_recorded=False,
        )
        return GovernanceTransition(
            previous_state,
            next_state,
            trial_ledger_refs=tuple(record.trial_id for record in trial_records),
        )

    if previous_state is PromotionLifecycleState.DIAGNOSTICS_RUN:
        require_trial_ledger_present(active_context.trial_ledger_path)
        evidence_bundle = validate_evidence_ready_gate(active_context.evidence_bundle)
        trial_records = _validate_trial_records(
            active_context.trial_ledger_records,
            require_non_empty=True,
        )
        _validate_evidence_ready_holdout_gate(active_context, trial_records)
        _validate_variant_budget_context(
            active_context,
            trial_records=trial_records,
            persist=False,
            require_recorded=True,
        )
        return GovernanceTransition(
            previous_state,
            next_state,
            evidence_bundle=evidence_bundle,
            trial_ledger_refs=tuple(evidence_bundle.trial_ids),
        )

    if previous_state is PromotionLifecycleState.EVIDENCE_READY:
        reviewer_verdict = _validate_independent_reviewer_verdict(active_context)
        return GovernanceTransition(
            previous_state,
            next_state,
            reviewer_verdict_id=reviewer_verdict.reviewer_verdict_id,
        )

    if previous_state is PromotionLifecycleState.REVIEWED:
        promotion_decision = _validate_reviewed_promotion_decision(
            next_state,
            active_context,
        )
        reviewer_verdict = _validate_independent_reviewer_verdict(active_context)
        _validate_promotion_verdict_link(
            promotion_decision,
            reviewer_verdict,
            next_state,
        )
        if next_state in {
            PromotionLifecycleState.CANDIDATE,
            PromotionLifecycleState.VALIDATED,
        }:
            evidence_bundle, trial_refs = _validate_candidate_or_validated_gate(
                promotion_decision,
                active_context,
                reviewer_verdict,
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


def _reject_exploratory_artifacts(context: PromotionGateContext) -> None:
    reject_exploratory_promotion_artifacts(
        {
            "alpha_spec": context.alpha_spec,
            "study_spec": context.study_spec,
            "evidence_bundle": context.evidence_bundle,
            "promotion_decision": context.promotion_decision,
            "reviewer_verdict": context.reviewer_verdict,
            "trial_ledger_records": context.trial_ledger_records,
            "promotion_artifacts": context.promotion_artifacts,
        }
    )


def _validate_variant_budget_context(
    context: PromotionGateContext,
    *,
    trial_records: tuple[TrialLedgerRecord, ...],
    persist: bool,
    require_recorded: bool,
) -> None:
    validate_variant_and_family_budget(
        context.study_spec,
        trial_ledger_records=trial_records,
        family_id=context.family_id,
        variant_ledger_path=context.variant_ledger_path,
        amendments=context.budget_amendments,
        persist=persist,
        require_recorded=require_recorded,
    )


def _validate_evidence_ready_holdout_gate(
    context: PromotionGateContext,
    trial_records: tuple[TrialLedgerRecord, ...],
) -> None:
    issues: list[ValidationIssue] = []
    contaminated_ids = [
        record.trial_id for record in trial_records if record.locked_test_contamination_flag
    ]
    if contaminated_ids:
        issues.append(
            ValidationIssue(
                field="trial_ledger_records",
                code="locked_test_contamination_blocks_evidence_ready",
                message=(
                    "locked-test contamination blocks EVIDENCE_READY with no waiver "
                    "path in this campaign"
                ),
                expected="no TrialLedgerRecord.locked_test_contamination_flag values",
                actual=", ".join(contaminated_ids),
            )
        )

    if context.sealed_holdout_registry_path is None and context.require_sealed_holdout:
        issues.append(
            ValidationIssue(
                field="sealed_holdout_registry_path",
                code="missing_sealed_holdout_registry_path",
                message="sealed holdout declaration is required before EVIDENCE_READY",
                expected="path to a sealed holdout declaration registry",
                actual="missing",
            )
        )
    elif context.sealed_holdout_registry_path is not None:
        try:
            window = SealedHoldoutRegistry(context.sealed_holdout_registry_path).gate_window()
        except GovernanceValidationError as exc:
            issues.extend(exc.issues)
        else:
            if window.status is SealedHoldoutStatus.BREACHED:
                issues.append(
                    ValidationIssue(
                        field="sealed_holdout_window.status",
                        code="sealed_holdout_window_breached",
                        message="BREACHED sealed holdout window blocks EVIDENCE_READY",
                        expected="DECLARED or SEALED",
                        actual=f"{window.window_id}:BREACHED",
                    )
                )

    if issues:
        raise GovernanceValidationError(issues)


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


def require_trial_ledger_present(ledger_path: str | Path | None) -> Path:
    """Require a present, readable, parseable, non-destructively writable ledger."""

    if ledger_path is None or not _is_substantive_text(str(ledger_path)):
        _raise_ledger_issue(
            ledger_path,
            "missing_trial_ledger_path",
            "trial ledger path is required before evidence-ready transition",
            expected="path to an existing writable trial ledger JSON file",
            actual="missing",
        )

    path = Path(ledger_path)
    try:
        metadata = path.stat()
    except FileNotFoundError:
        _raise_ledger_issue(
            path,
            "missing_trial_ledger",
            "trial ledger file is missing",
            expected="existing trial ledger JSON file",
            actual=str(path),
        )
    except OSError as exc:
        _raise_ledger_issue(
            path,
            "unreadable_trial_ledger",
            "trial ledger file metadata could not be read",
            expected="readable trial ledger JSON file",
            actual=f"{path}: {exc}",
        )

    if not stat.S_ISREG(metadata.st_mode):
        _raise_ledger_issue(
            path,
            "invalid_trial_ledger_path",
            "trial ledger path must point to a regular file",
            expected="regular JSON file",
            actual=str(path),
        )
    if metadata.st_mode & (stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH) == 0:
        _raise_ledger_issue(
            path,
            "unreadable_trial_ledger",
            "trial ledger file has no read permission bits set",
            expected="readable trial ledger JSON file",
            actual=str(path),
        )
    if metadata.st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH) == 0:
        _raise_ledger_issue(
            path,
            "unwritable_trial_ledger",
            "trial ledger file has no write permission bits set",
            expected="non-destructively writable trial ledger JSON file",
            actual=str(path),
        )

    try:
        with path.open("r+", encoding="utf-8") as handle:
            content = handle.read()
    except PermissionError as exc:
        _raise_ledger_issue(
            path,
            "unwritable_trial_ledger",
            "trial ledger file could not be opened read/write without truncation",
            expected="non-destructively writable trial ledger JSON file",
            actual=f"{path}: {exc}",
        )
    except OSError as exc:
        _raise_ledger_issue(
            path,
            "unreadable_trial_ledger",
            "trial ledger file could not be opened for validation",
            expected="readable and writable trial ledger JSON file",
            actual=f"{path}: {exc}",
        )

    try:
        json.loads(content)
    except json.JSONDecodeError as exc:
        _raise_ledger_issue(
            path,
            "unparseable_trial_ledger",
            "trial ledger file is not parseable JSON",
            expected="parseable JSON trial ledger",
            actual=f"{path}: {exc.msg}",
        )

    return path


def _validate_rejected_transition(
    previous_state: PromotionLifecycleState,
    next_state: PromotionLifecycleState,
    context: PromotionGateContext,
) -> GovernanceTransition:
    rejected_record = _validate_rejected_record(context.rejected_idea_record)
    _validate_rejection_reason(context.rejection_reason)
    promotion_decision = None
    reviewer_verdict_id = ""
    if previous_state is PromotionLifecycleState.REVIEWED:
        promotion_decision = _validate_reviewed_promotion_decision(next_state, context)
        reviewer_verdict = _validate_independent_reviewer_verdict(context)
        _validate_promotion_verdict_link(
            promotion_decision,
            reviewer_verdict,
            next_state,
        )
        reviewer_verdict_id = reviewer_verdict.reviewer_verdict_id
    return GovernanceTransition(
        previous_state,
        next_state,
        promotion_decision=promotion_decision,
        rejected_idea_record=rejected_record,
        trial_ledger_refs=(
            promotion_decision.trial_ledger_refs if promotion_decision is not None else ()
        ),
        reviewer_verdict_id=reviewer_verdict_id,
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
    reviewer_verdict: ReviewerVerdict,
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
        if evidence_bundle.reviewer_verdict_reference != reviewer_verdict.reviewer_verdict_id:
            issues.append(
                ValidationIssue(
                    field="evidence_bundle.reviewer_verdict_reference",
                    code="reviewer_verdict_reference_mismatch",
                    message="EvidenceBundle.reviewer_verdict_reference must match the verdict",
                    expected=reviewer_verdict.reviewer_verdict_id,
                    actual=evidence_bundle.reviewer_verdict_reference,
                )
            )
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


def _validate_independent_reviewer_verdict(context: PromotionGateContext) -> ReviewerVerdict:
    issues: list[ValidationIssue] = []
    reviewer_verdict = _coerce_reviewer_verdict(context.reviewer_verdict, issues)
    if reviewer_verdict is not None:
        issues.extend(_validate_reviewer_independence(reviewer_verdict, context))
    if issues:
        raise GovernanceValidationError(issues)
    assert reviewer_verdict is not None
    return reviewer_verdict


def _coerce_reviewer_verdict(
    value: ReviewerVerdict | Mapping[str, Any] | None,
    issues: list[ValidationIssue],
) -> ReviewerVerdict | None:
    if value is None:
        issues.append(
            ValidationIssue(
                field="reviewer_verdict",
                code="missing_reviewer_verdict",
                message="independent ReviewerVerdict is required before reviewed promotion",
                expected="validated ReviewerVerdict",
                actual="missing",
            )
        )
        return None
    try:
        if isinstance(value, ReviewerVerdict):
            return validate_reviewer_verdict(value.to_dict())
        if isinstance(value, Mapping):
            return validate_reviewer_verdict(value)
    except GovernanceValidationError as exc:
        issues.extend(exc.issues)
        return None

    issues.append(
        ValidationIssue(
            field="reviewer_verdict",
            code="invalid_reviewer_verdict_type",
            message="reviewer_verdict must be a ReviewerVerdict or mapping",
            expected="ReviewerVerdict or mapping",
            actual=type(value).__name__,
        )
    )
    return None


def _validate_reviewer_independence(
    reviewer_verdict: ReviewerVerdict,
    context: PromotionGateContext,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not _is_substantive_text(context.implementer_id):
        issues.append(
            ValidationIssue(
                field="implementer_id",
                code="missing_implementer_id",
                message="implementer identity is required to enforce reviewer independence",
                expected="non-empty implementer identity",
                actual=str(context.implementer_id),
            )
        )
    if not _is_substantive_text(context.implementer_role):
        issues.append(
            ValidationIssue(
                field="implementer_role",
                code="missing_implementer_role",
                message="implementer role is required to enforce reviewer independence",
                expected="non-empty implementer role",
                actual=str(context.implementer_role),
            )
        )
    if issues:
        return issues

    assert context.implementer_id is not None
    assert context.implementer_role is not None
    if _normalize_text(reviewer_verdict.reviewer_id) == _normalize_text(context.implementer_id):
        issues.append(
            ValidationIssue(
                field="reviewer_id",
                code="reviewer_self_approval",
                message="ReviewerVerdict.reviewer_id must differ from implementer_id",
                expected="independent reviewer identity",
                actual=reviewer_verdict.reviewer_id,
            )
        )
    if _normalize_text(reviewer_verdict.role) == _normalize_text(context.implementer_role):
        issues.append(
            ValidationIssue(
                field="role",
                code="reviewer_role_not_independent",
                message="ReviewerVerdict.role must differ from implementer_role",
                expected="independent reviewer role",
                actual=reviewer_verdict.role,
            )
        )
    return issues


def _validate_promotion_verdict_link(
    promotion_decision: PromotionDecision,
    reviewer_verdict: ReviewerVerdict,
    next_state: PromotionLifecycleState,
) -> None:
    issues: list[ValidationIssue] = []
    if promotion_decision.reviewer_verdict_id != reviewer_verdict.reviewer_verdict_id:
        issues.append(
            ValidationIssue(
                field="reviewer_verdict_id",
                code="reviewer_verdict_id_mismatch",
                message="PromotionDecision.reviewer_verdict_id must match the verdict",
                expected=reviewer_verdict.reviewer_verdict_id,
                actual=promotion_decision.reviewer_verdict_id,
            )
        )
    if (
        next_state.value in POSITIVE_PROMOTION_TARGET_STATES
        and not reviewer_verdict.is_merge_eligible
    ):
        issues.append(
            ValidationIssue(
                field="reviewer_verdict.verdict",
                code="reviewer_verdict_not_merge_eligible",
                message="candidate or validated promotion requires a merge-eligible verdict",
                expected=" | ".join(verdict.value for verdict in MERGE_ELIGIBLE_REVIEWER_VERDICTS),
                actual=reviewer_verdict.verdict.value,
            )
        )
    if issues:
        raise GovernanceValidationError(issues)


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


def _raise_ledger_issue(
    ledger_path: str | Path | None,
    code: str,
    message: str,
    *,
    expected: str,
    actual: str,
) -> None:
    raise GovernanceValidationError(
        ValidationIssue(
            field="trial_ledger_path",
            code=code,
            message=f"{message}: {ledger_path}",
            expected=expected,
            actual=actual,
        )
    )


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
    "POSITIVE_PROMOTION_TARGET_STATES",
    "REACHABLE_STATES",
    "GovernanceTransition",
    "PromotionGateContext",
    "require_trial_ledger_present",
    "assert_promotion_gate",
    "prohibited_mvp_states",
    "reachable_states",
    "reachable_transition_targets",
    "validate_governance_transition",
]
