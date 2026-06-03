from __future__ import annotations

import pytest

from alpha_system.governance.evidence_bundle import EvidenceBundle, create_evidence_bundle
from alpha_system.governance.promotion import (
    PromotionDecision,
    PromotionDecisionOutcome,
    PromotionLifecycleState,
    create_promotion_decision,
)
from alpha_system.governance.promotion_gate import (
    PromotionGateContext,
    validate_governance_transition,
)
from alpha_system.governance.reviewer_verdict import (
    ReviewerVerdict,
    ReviewerVerdictOutcome,
    create_reviewer_verdict,
)
from alpha_system.governance.trial_ledger import (
    TrialLedgerRecord,
    TrialStatus,
    create_trial_ledger_record,
)
from alpha_system.governance.validation import GovernanceValidationError

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_ID = "sspec_438ceffd40855205de5497f0"
IMPLEMENTER_ID = "codex:argov-p12-executor"
IMPLEMENTER_ROLE = "codex_executor"
REVIEWER_ID = "claude:independent-governance-reviewer"
REVIEWER_ROLE = "claude_reviewer"
CODE_HASH = "a" * 64
CONFIG_HASH = "b" * 64
MANIFEST_HASH = "c" * 64
TIMESTAMP = "2026-06-03T13:52:09Z"


def reviewer_verdict(
    *,
    reviewer_id: str = REVIEWER_ID,
    role: str = REVIEWER_ROLE,
    verdict: ReviewerVerdictOutcome | str = ReviewerVerdictOutcome.PASS,
    blocking_issues: list[str] | None = None,
    warnings: list[str] | None = None,
) -> ReviewerVerdict:
    return create_reviewer_verdict(
        reviewer_id=reviewer_id,
        role=role,
        independence_statement=(
            "Reviewer identity and role are independent from the Codex implementer."
        ),
        verdict=verdict,
        blocking_issues=[] if blocking_issues is None else blocking_issues,
        warnings=(
            ["Synthetic governance review only; no market claim is made."]
            if warnings is None
            else warnings
        ),
        checked_artifacts=[
            "src/alpha_system/governance/reviewer_verdict.py",
            "src/alpha_system/governance/promotion_gate.py",
        ],
        checked_commands=[
            "python -m pytest tests/unit/governance/test_reviewer_independence.py -q"
        ],
        timestamp=TIMESTAMP,
    )


def trial_record() -> TrialLedgerRecord:
    return create_trial_ledger_record(
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        run_id="diagnostics-run-argov-p12",
        variant_id="variant-independent-review",
        status=TrialStatus.COMPLETED,
        parameters={"threshold": 0.25, "window": 20},
        metrics_summary={"coverage": 0.75},
        failure_reason=None,
        oos_touched_flag=False,
        locked_test_contamination_flag=False,
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
    )


def evidence_bundle(
    records: tuple[TrialLedgerRecord, ...],
    verdict: ReviewerVerdict,
) -> EvidenceBundle:
    return create_evidence_bundle(
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        trial_ids=[record.trial_id for record in records],
        data_version="synthetic-data-v1",
        factor_version="synthetic-factor-v1",
        label_version="synthetic-label-v1",
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
        diagnostics_summary={
            "diagnostics_run_ref": "diagnostics-run-argov-p12",
            "metric_set": "synthetic governance smoke metrics",
        },
        negative_control_results=[
            {
                "control_name": "permuted labels control",
                "result": "failed closed",
                "summary": "synthetic control did not create admissible evidence",
            }
        ],
        limitations=["synthetic metadata fixture only"],
        artifact_manifest=[
            {
                "logical_name": "diagnostics summary",
                "role": "diagnostics_summary",
                "reference": "local/evidence/diagnostics-summary.json",
                "content_hash": MANIFEST_HASH,
            }
        ],
        reviewer_verdict_reference=verdict.reviewer_verdict_id,
    )


def promotion_decision(
    *,
    bundle: EvidenceBundle,
    records: tuple[TrialLedgerRecord, ...],
    verdict: ReviewerVerdict,
    target: PromotionLifecycleState = PromotionLifecycleState.VALIDATED,
) -> PromotionDecision:
    return create_promotion_decision(
        alpha_spec_id=ALPHA_SPEC_ID,
        evidence_bundle_id=bundle.evidence_bundle_id,
        trial_ledger_refs=[record.trial_id for record in records],
        previous_state=PromotionLifecycleState.REVIEWED,
        next_state=target,
        decision=PromotionDecisionOutcome(target.value),
        rationale="Synthetic governance metadata supports this controlled state transition.",
        reviewer_verdict_id=verdict.reviewer_verdict_id,
        warnings=["This decision is not live, capital, or production approval."],
        timestamp=TIMESTAMP,
    )


def reviewer_context(verdict: ReviewerVerdict) -> PromotionGateContext:
    return PromotionGateContext(
        reviewer_verdict=verdict,
        implementer_id=IMPLEMENTER_ID,
        implementer_role=IMPLEMENTER_ROLE,
    )


def test_evidence_ready_to_reviewed_requires_independent_verdict() -> None:
    verdict = reviewer_verdict()

    transition = validate_governance_transition(
        "EVIDENCE_READY",
        "REVIEWED",
        reviewer_context(verdict),
    )

    assert transition.next_state is PromotionLifecycleState.REVIEWED
    assert transition.reviewer_verdict_id == verdict.reviewer_verdict_id


def test_evidence_ready_to_reviewed_blocks_missing_verdict() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "EVIDENCE_READY",
            "REVIEWED",
            PromotionGateContext(
                implementer_id=IMPLEMENTER_ID,
                implementer_role=IMPLEMENTER_ROLE,
            ),
        )

    assert exc_info.value.issues[0].code == "missing_reviewer_verdict"


def test_self_approval_by_reviewer_identity_is_blocked() -> None:
    verdict = reviewer_verdict(reviewer_id=IMPLEMENTER_ID)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "EVIDENCE_READY",
            "REVIEWED",
            reviewer_context(verdict),
        )

    assert any(issue.code == "reviewer_self_approval" for issue in exc_info.value.issues)


def test_reviewer_role_matching_implementer_role_is_rejected() -> None:
    verdict = reviewer_verdict(role=IMPLEMENTER_ROLE)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "EVIDENCE_READY",
            "REVIEWED",
            reviewer_context(verdict),
        )

    assert any(
        issue.code == "reviewer_role_not_independent" for issue in exc_info.value.issues
    )


def test_validated_promotion_requires_independent_merge_eligible_verdict() -> None:
    verdict = reviewer_verdict(verdict=ReviewerVerdictOutcome.PASS_WITH_WARNINGS)
    records = (trial_record(),)
    bundle = evidence_bundle(records, verdict)
    decision = promotion_decision(bundle=bundle, records=records, verdict=verdict)

    transition = validate_governance_transition(
        "REVIEWED",
        "VALIDATED",
        PromotionGateContext(
            promotion_decision=decision,
            evidence_bundle=bundle,
            trial_ledger_records=records,
            reviewer_verdict=verdict,
            implementer_id=IMPLEMENTER_ID,
            implementer_role=IMPLEMENTER_ROLE,
        ),
    )

    assert transition.next_state is PromotionLifecycleState.VALIDATED
    assert transition.reviewer_verdict_id == verdict.reviewer_verdict_id


def test_validated_promotion_blocks_missing_verdict() -> None:
    verdict = reviewer_verdict()
    records = (trial_record(),)
    bundle = evidence_bundle(records, verdict)
    decision = promotion_decision(bundle=bundle, records=records, verdict=verdict)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "REVIEWED",
            "VALIDATED",
            PromotionGateContext(
                promotion_decision=decision,
                evidence_bundle=bundle,
                trial_ledger_records=records,
                implementer_id=IMPLEMENTER_ID,
                implementer_role=IMPLEMENTER_ROLE,
            ),
        )

    assert exc_info.value.issues[0].code == "missing_reviewer_verdict"


def test_validated_promotion_blocks_non_merge_eligible_verdict() -> None:
    verdict = reviewer_verdict(
        verdict=ReviewerVerdictOutcome.REWORK,
        blocking_issues=["Synthetic reviewer requested governance rework."],
        warnings=[],
    )
    records = (trial_record(),)
    bundle = evidence_bundle(records, verdict)
    decision = promotion_decision(bundle=bundle, records=records, verdict=verdict)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "REVIEWED",
            "VALIDATED",
            PromotionGateContext(
                promotion_decision=decision,
                evidence_bundle=bundle,
                trial_ledger_records=records,
                reviewer_verdict=verdict,
                implementer_id=IMPLEMENTER_ID,
                implementer_role=IMPLEMENTER_ROLE,
            ),
        )

    assert any(
        issue.code == "reviewer_verdict_not_merge_eligible"
        for issue in exc_info.value.issues
    )


def test_promotion_decision_reviewer_verdict_id_must_match_verdict() -> None:
    referenced_verdict = reviewer_verdict()
    presented_verdict = reviewer_verdict(warnings=["Different review content changes the ID."])
    records = (trial_record(),)
    bundle = evidence_bundle(records, referenced_verdict)
    decision = promotion_decision(
        bundle=bundle,
        records=records,
        verdict=referenced_verdict,
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "REVIEWED",
            "VALIDATED",
            PromotionGateContext(
                promotion_decision=decision,
                evidence_bundle=bundle,
                trial_ledger_records=records,
                reviewer_verdict=presented_verdict,
                implementer_id=IMPLEMENTER_ID,
                implementer_role=IMPLEMENTER_ROLE,
            ),
        )

    assert any(issue.code == "reviewer_verdict_id_mismatch" for issue in exc_info.value.issues)


def test_reviewer_verdict_does_not_imply_market_truth_or_profitability() -> None:
    verdict = reviewer_verdict()

    assert verdict.implies_market_truth is False
    assert verdict.implies_profitability is False
    assert verdict.implies_tradability is False
    assert verdict.implies_production_readiness is False
