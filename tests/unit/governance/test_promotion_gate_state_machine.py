from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.governance.alpha_spec import (
    generate_alpha_spec_id,
    validate_alpha_spec,
)
from alpha_system.governance.evidence_bundle import (
    EvidenceBundle,
    create_evidence_bundle,
)
from alpha_system.governance.hypothesis_card import validate_hypothesis_card
from alpha_system.governance.promotion import (
    PROHIBITED_MVP_STATES,
    PromotionDecision,
    PromotionDecisionOutcome,
    PromotionLifecycleState,
    create_promotion_decision,
)
from alpha_system.governance.promotion_gate import (
    ALLOWED_TRANSITIONS,
    PromotionGateContext,
    prohibited_mvp_states,
    reachable_states,
    validate_governance_transition,
)
from alpha_system.governance.rejected_idea import (
    RejectedIdeaReasonCategory,
    create_rejected_idea_record,
)
from alpha_system.governance.study_spec import validate_study_spec
from alpha_system.governance.trial_ledger import (
    TrialLedgerRecord,
    TrialStatus,
    create_trial_ledger_record,
)
from alpha_system.governance.validation import GovernanceValidationError

HYPOTHESIS_FIXTURE = Path("tests/fixtures/governance/hypothesis_card_valid.json")
ALPHA_SPEC_FIXTURE = Path("tests/fixtures/governance/alpha_spec_valid.json")
STUDY_SPEC_FIXTURE = Path("tests/fixtures/governance/study_spec_valid.json")

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_ID = "sspec_438ceffd40855205de5497f0"
HYPOTHESIS_ID = "hyp_438ceffd40855205de5497f0"
REVIEWER_VERDICT_ID = "rver_aaaaaaaaaaaaaaaaaaaaaaaa"
CODE_HASH = "a" * 64
CONFIG_HASH = "b" * 64
MANIFEST_HASH = "c" * 64
TIMESTAMP = "2026-06-03T13:52:09Z"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def linked_registration_payloads() -> tuple[dict[str, object], dict[str, object]]:
    hypothesis_payload = load_json(HYPOTHESIS_FIXTURE)
    alpha_payload = load_json(ALPHA_SPEC_FIXTURE)
    alpha_payload["hypothesis_id"] = hypothesis_payload["hypothesis_id"]
    alpha_payload["alpha_spec_id"] = generate_alpha_spec_id(alpha_payload)
    return hypothesis_payload, alpha_payload


def valid_alpha_spec_payload() -> dict[str, object]:
    return load_json(ALPHA_SPEC_FIXTURE)


def valid_study_spec_payload() -> dict[str, object]:
    return load_json(STUDY_SPEC_FIXTURE)


def trial_record(
    *,
    run_id: str = "diagnostics-run-001",
    variant_id: str = "variant-001",
    status: TrialStatus = TrialStatus.COMPLETED,
    failure_reason: str | None = None,
    locked_test_contamination_flag: bool = False,
) -> TrialLedgerRecord:
    return create_trial_ledger_record(
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        run_id=run_id,
        variant_id=variant_id,
        status=status,
        parameters={"threshold": 0.25, "window": 20},
        metrics_summary={} if status is not TrialStatus.COMPLETED else {"coverage": 0.75},
        failure_reason=failure_reason,
        oos_touched_flag=False,
        locked_test_contamination_flag=locked_test_contamination_flag,
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
    )


def evidence_bundle(records: tuple[TrialLedgerRecord, ...]) -> EvidenceBundle:
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
            "diagnostics_run_ref": "diagnostics-run-001",
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
        reviewer_verdict_reference=REVIEWER_VERDICT_ID,
    )


def promotion_decision(
    *,
    target: PromotionLifecycleState = PromotionLifecycleState.CANDIDATE,
    bundle: EvidenceBundle,
    trial_refs: list[str],
) -> PromotionDecision:
    return create_promotion_decision(
        alpha_spec_id=ALPHA_SPEC_ID,
        evidence_bundle_id=bundle.evidence_bundle_id,
        trial_ledger_refs=trial_refs,
        previous_state=PromotionLifecycleState.REVIEWED,
        next_state=target,
        decision=PromotionDecisionOutcome(target.value),
        rationale="Synthetic governance metadata supports this controlled state transition.",
        reviewer_verdict_id=REVIEWER_VERDICT_ID,
        warnings=["This decision is not live, capital, or production approval."],
        timestamp=TIMESTAMP,
    )


def rejected_record(
    bundle: EvidenceBundle, records: tuple[TrialLedgerRecord, ...]
) -> dict[str, object]:
    return create_rejected_idea_record(
        alpha_spec_id_or_hypothesis_id=ALPHA_SPEC_ID,
        reason_category=RejectedIdeaReasonCategory.WEAK_EVIDENCE,
        evidence_references=[bundle.evidence_bundle_id, records[0].trial_id],
        duplicate_links=[HYPOTHESIS_ID],
        leakage_cost_weakness_notes=["Synthetic evidence did not meet the review threshold."],
        reviewer="reviewer:independent-governance-reviewer",
        created_at=TIMESTAMP,
    ).to_dict()


def completed_and_failed_records() -> tuple[TrialLedgerRecord, TrialLedgerRecord]:
    completed = trial_record(run_id="diagnostics-run-001", variant_id="variant-a")
    failed = trial_record(
        run_id="diagnostics-run-002",
        variant_id="variant-b",
        status=TrialStatus.FAILED,
        failure_reason="synthetic dependency check failed before metrics existed",
    )
    return completed, failed


def test_reachable_state_set_excludes_prohibited_mvp_states() -> None:
    assert prohibited_mvp_states() == PROHIBITED_MVP_STATES
    assert not (set(reachable_states()) & set(PROHIBITED_MVP_STATES))
    for targets in ALLOWED_TRANSITIONS.values():
        assert not (set(targets) & set(PROHIBITED_MVP_STATES))


@pytest.mark.parametrize(
    ("from_state", "to_state"),
    [
        ("LIVE_APPROVED", "CANDIDATE"),
        ("REVIEWED", "CAPITAL_ALLOCATED"),
        ("PRODUCTION_READY", "REJECTED"),
    ],
)
def test_prohibited_mvp_states_are_unreachable(from_state: str, to_state: str) -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(from_state, to_state)

    assert exc_info.value.issues[0].code == "prohibited_mvp_state"


def test_draft_to_registered_requires_valid_hypothesis_and_alpha_spec() -> None:
    hypothesis_payload, alpha_payload = linked_registration_payloads()

    transition = validate_governance_transition(
        "DRAFT",
        "REGISTERED",
        PromotionGateContext(
            hypothesis_card=validate_hypothesis_card(hypothesis_payload),
            alpha_spec=validate_alpha_spec(alpha_payload),
        ),
    )

    assert transition.previous_state is PromotionLifecycleState.DRAFT
    assert transition.next_state is PromotionLifecycleState.REGISTERED


def test_registered_to_implementation_allowed_requires_alpha_and_clearance() -> None:
    transition = validate_governance_transition(
        "REGISTERED",
        "IMPLEMENTATION_ALLOWED",
        PromotionGateContext(
            alpha_spec=validate_alpha_spec(valid_alpha_spec_payload()),
            duplicate_or_leakage_check_passed=True,
        ),
    )

    assert transition.next_state is PromotionLifecycleState.IMPLEMENTATION_ALLOWED


def test_registered_to_implementation_allowed_blocks_missing_clearance() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "REGISTERED",
            "IMPLEMENTATION_ALLOWED",
            PromotionGateContext(alpha_spec=validate_alpha_spec(valid_alpha_spec_payload())),
        )

    assert exc_info.value.issues[0].code == "missing_duplicate_leakage_clearance"


def test_implementation_allowed_to_implemented_requires_handoff_ref() -> None:
    transition = validate_governance_transition(
        "IMPLEMENTATION_ALLOWED",
        "IMPLEMENTED",
        PromotionGateContext(implementation_handoff_ref="handoffs/synthetic-implementation.md"),
    )

    assert transition.next_state is PromotionLifecycleState.IMPLEMENTED


def test_implemented_to_diagnostics_allowed_requires_study_spec() -> None:
    transition = validate_governance_transition(
        "IMPLEMENTED",
        "DIAGNOSTICS_ALLOWED",
        PromotionGateContext(study_spec=validate_study_spec(valid_study_spec_payload())),
    )

    assert transition.next_state is PromotionLifecycleState.DIAGNOSTICS_ALLOWED


def test_diagnostics_allowed_to_diagnostics_run_requires_trial_ledger() -> None:
    record = trial_record()

    transition = validate_governance_transition(
        "DIAGNOSTICS_ALLOWED",
        "DIAGNOSTICS_RUN",
        PromotionGateContext(trial_ledger_records=(record,)),
    )

    assert transition.next_state is PromotionLifecycleState.DIAGNOSTICS_RUN
    assert transition.trial_ledger_refs == (record.trial_id,)


def test_diagnostics_run_to_evidence_ready_requires_valid_evidence_bundle() -> None:
    records = (trial_record(),)
    bundle = evidence_bundle(records)

    transition = validate_governance_transition(
        "DIAGNOSTICS_RUN",
        "EVIDENCE_READY",
        PromotionGateContext(evidence_bundle=bundle),
    )

    assert transition.next_state is PromotionLifecycleState.EVIDENCE_READY
    assert transition.evidence_bundle == bundle
    assert transition.trial_ledger_refs == (records[0].trial_id,)


def test_evidence_ready_to_reviewed_requires_reviewer_verdict_id_seam() -> None:
    transition = validate_governance_transition(
        "EVIDENCE_READY",
        "REVIEWED",
        PromotionGateContext(reviewer_verdict_id=REVIEWER_VERDICT_ID),
    )

    assert transition.next_state is PromotionLifecycleState.REVIEWED
    assert transition.reviewer_verdict_id == REVIEWER_VERDICT_ID


def test_reviewed_to_candidate_requires_complete_promotion_gate() -> None:
    records = completed_and_failed_records()
    bundle = evidence_bundle(records)
    decision = promotion_decision(
        target=PromotionLifecycleState.CANDIDATE,
        bundle=bundle,
        trial_refs=[record.trial_id for record in records],
    )

    transition = validate_governance_transition(
        "REVIEWED",
        "CANDIDATE",
        PromotionGateContext(
            promotion_decision=decision,
            evidence_bundle=bundle,
            trial_ledger_records=records,
        ),
    )

    assert transition.next_state is PromotionLifecycleState.CANDIDATE
    assert transition.promotion_decision == decision
    assert transition.evidence_bundle == bundle
    assert set(transition.trial_ledger_refs) == {record.trial_id for record in records}


def test_reviewed_to_validated_is_governance_only_not_production_status() -> None:
    records = (trial_record(),)
    bundle = evidence_bundle(records)
    decision = promotion_decision(
        target=PromotionLifecycleState.VALIDATED,
        bundle=bundle,
        trial_refs=[record.trial_id for record in records],
    )

    transition = validate_governance_transition(
        "REVIEWED",
        "VALIDATED",
        PromotionGateContext(
            promotion_decision=decision,
            evidence_bundle=bundle,
            trial_ledger_records=records,
        ),
    )

    assert transition.next_state is PromotionLifecycleState.VALIDATED
    assert transition.promotion_decision is not None
    assert transition.promotion_decision.implies_live_approval is False
    assert transition.promotion_decision.implies_capital_allocation is False
    assert transition.promotion_decision.implies_production_readiness is False


def test_reviewed_to_watch_requires_promotion_decision() -> None:
    records = (trial_record(),)
    bundle = evidence_bundle(records)
    decision = promotion_decision(
        target=PromotionLifecycleState.WATCH,
        bundle=bundle,
        trial_refs=[record.trial_id for record in records],
    )

    transition = validate_governance_transition(
        "REVIEWED",
        "WATCH",
        PromotionGateContext(promotion_decision=decision),
    )

    assert transition.next_state is PromotionLifecycleState.WATCH
    assert transition.promotion_decision == decision


def test_reviewed_promotion_blocks_without_promotion_decision() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition("REVIEWED", "CANDIDATE", PromotionGateContext())

    assert exc_info.value.issues[0].code == "missing_promotion_decision"


def test_candidate_blocks_without_evidence_bundle() -> None:
    records = (trial_record(),)
    bundle = evidence_bundle(records)
    decision = promotion_decision(
        target=PromotionLifecycleState.CANDIDATE,
        bundle=bundle,
        trial_refs=[record.trial_id for record in records],
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "REVIEWED",
            "CANDIDATE",
            PromotionGateContext(
                promotion_decision=decision,
                trial_ledger_records=records,
            ),
        )

    assert exc_info.value.issues[0].code == "missing_evidence_bundle"


def test_candidate_blocks_without_trial_ledger_records() -> None:
    records = (trial_record(),)
    bundle = evidence_bundle(records)
    decision = promotion_decision(
        target=PromotionLifecycleState.CANDIDATE,
        bundle=bundle,
        trial_refs=[record.trial_id for record in records],
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "REVIEWED",
            "CANDIDATE",
            PromotionGateContext(
                promotion_decision=decision,
                evidence_bundle=bundle,
            ),
        )

    assert exc_info.value.issues[0].code == "missing_trial_ledger_records"


def test_candidate_blocks_failed_run_omission_from_decision_refs() -> None:
    records = completed_and_failed_records()
    bundle = evidence_bundle(records)
    decision = promotion_decision(
        target=PromotionLifecycleState.CANDIDATE,
        bundle=bundle,
        trial_refs=[records[0].trial_id],
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "REVIEWED",
            "CANDIDATE",
            PromotionGateContext(
                promotion_decision=decision,
                evidence_bundle=bundle,
                trial_ledger_records=records,
            ),
        )

    assert exc_info.value.issues[0].code == "failed_run_omission"


def test_candidate_blocks_failed_run_omission_from_evidence_bundle() -> None:
    records = completed_and_failed_records()
    incomplete_bundle = evidence_bundle((records[0],))
    decision = promotion_decision(
        target=PromotionLifecycleState.CANDIDATE,
        bundle=incomplete_bundle,
        trial_refs=[record.trial_id for record in records],
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "REVIEWED",
            "CANDIDATE",
            PromotionGateContext(
                promotion_decision=decision,
                evidence_bundle=incomplete_bundle,
                trial_ledger_records=records,
            ),
        )

    assert exc_info.value.issues[0].code == "failed_run_omission"


def test_candidate_blocks_unrecorded_locked_test_contamination() -> None:
    records = (
        trial_record(
            run_id="diagnostics-run-004",
            variant_id="variant-contaminated",
            locked_test_contamination_flag=True,
        ),
    )
    bundle = evidence_bundle(records)
    decision = promotion_decision(
        target=PromotionLifecycleState.CANDIDATE,
        bundle=bundle,
        trial_refs=[record.trial_id for record in records],
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "REVIEWED",
            "CANDIDATE",
            PromotionGateContext(
                promotion_decision=decision,
                evidence_bundle=bundle,
                trial_ledger_records=records,
            ),
        )

    assert exc_info.value.issues[0].code == "unrecorded_locked_test_contamination"


def test_candidate_accepts_recorded_locked_test_contamination_metadata() -> None:
    records = (
        trial_record(
            run_id="diagnostics-run-004",
            variant_id="variant-contaminated",
            locked_test_contamination_flag=True,
        ),
    )
    bundle = evidence_bundle(records)
    decision = promotion_decision(
        target=PromotionLifecycleState.CANDIDATE,
        bundle=bundle,
        trial_refs=[record.trial_id for record in records],
    )

    transition = validate_governance_transition(
        "REVIEWED",
        "CANDIDATE",
        PromotionGateContext(
            promotion_decision=decision,
            evidence_bundle=bundle,
            trial_ledger_records=records,
            locked_test_contamination_metadata={
                "recorded_trial_id": records[0].trial_id,
                "summary": "Synthetic locked-test contact was recorded before promotion.",
            },
        ),
    )

    assert transition.next_state is PromotionLifecycleState.CANDIDATE


def test_any_state_to_rejected_requires_rejected_record_and_reason() -> None:
    records = (trial_record(),)
    bundle = evidence_bundle(records)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition("DRAFT", "REJECTED", PromotionGateContext())
    assert exc_info.value.issues[0].code == "missing_rejected_idea_record"

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "DRAFT",
            "REJECTED",
            PromotionGateContext(rejected_idea_record=rejected_record(bundle, records)),
        )
    assert exc_info.value.issues[0].code == "missing_rejection_reason"

    transition = validate_governance_transition(
        "DRAFT",
        "REJECTED",
        PromotionGateContext(
            rejected_idea_record=rejected_record(bundle, records),
            rejection_reason="Synthetic evidence is insufficient for this idea.",
        ),
    )
    assert transition.next_state is PromotionLifecycleState.REJECTED


def test_reviewed_to_rejected_requires_promotion_decision_plus_rejection_record() -> None:
    records = (trial_record(),)
    bundle = evidence_bundle(records)
    rejection = rejected_record(bundle, records)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "REVIEWED",
            "REJECTED",
            PromotionGateContext(
                rejected_idea_record=rejection,
                rejection_reason="Synthetic evidence is insufficient for promotion.",
            ),
        )
    assert exc_info.value.issues[0].code == "missing_promotion_decision"

    decision = promotion_decision(
        target=PromotionLifecycleState.REJECTED,
        bundle=bundle,
        trial_refs=[record.trial_id for record in records],
    )
    transition = validate_governance_transition(
        "REVIEWED",
        "REJECTED",
        PromotionGateContext(
            promotion_decision=decision,
            rejected_idea_record=rejection,
            rejection_reason="Synthetic evidence is insufficient for promotion.",
        ),
    )
    assert transition.next_state is PromotionLifecycleState.REJECTED
    assert transition.promotion_decision == decision


def test_undeclared_transition_fails_closed() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition("CANDIDATE", "VALIDATED", PromotionGateContext())

    assert exc_info.value.issues[0].code == "invalid_transition"
