from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.core.registry import connect_registry
from alpha_system.governance.alpha_spec import AlphaSpec
from alpha_system.governance.canaries.catalog import (
    NegativeControlType,
    expected_failure_for_canary_type,
)
from alpha_system.governance.canaries.negative_control_result import (
    create_negative_control_result,
)
from alpha_system.governance.evidence_bundle import create_evidence_bundle
from alpha_system.governance.feature_request import FeatureRequest
from alpha_system.governance.hypothesis_card import HypothesisCard
from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.label_spec import LabelSpec
from alpha_system.governance.promotion import (
    PromotionDecisionOutcome,
    PromotionLifecycleState,
    create_promotion_decision,
)
from alpha_system.governance.promotion_gate import PromotionGateContext
from alpha_system.governance.registry import (
    GOVERNANCE_LIFECYCLE_TABLE,
    GOVERNANCE_OBJECT_TABLE,
    GovernanceRegistry,
    ensure_governance_registry_schema,
)
from alpha_system.governance.rejected_idea import (
    RejectedIdeaReasonCategory,
    create_rejected_idea_record,
)
from alpha_system.governance.reviewer_verdict import create_reviewer_verdict
from alpha_system.governance.study_spec import StudySpec
from alpha_system.governance.trial_ledger import (
    TrialStatus,
    create_trial_ledger_record,
)
from alpha_system.governance.validation import GovernanceValidationError

FIXTURE_ROOT = Path("tests/fixtures/governance")
ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_ID = "sspec_438ceffd40855205de5497f0"
IMPLEMENTER_ID = "codex:argov-p15-executor"
IMPLEMENTER_ROLE = "codex_executor"
REVIEWER_ID = "claude:independent-governance-reviewer"
REVIEWER_ROLE = "claude_reviewer"
CODE_HASH = "a" * 64
CONFIG_HASH = "b" * 64
MANIFEST_HASH = "c" * 64
TIMESTAMP = "2026-06-03T13:52:09Z"


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def _reviewer_verdict():
    return create_reviewer_verdict(
        reviewer_id=REVIEWER_ID,
        role=REVIEWER_ROLE,
        independence_statement=(
            "Reviewer identity and role are independent from the Codex implementer."
        ),
        verdict="PASS",
        blocking_issues=[],
        warnings=["Synthetic governance review only; no market claim is made."],
        checked_artifacts=[
            "src/alpha_system/governance/registry.py",
            "tests/integration/governance/test_registry_integration.py",
        ],
        checked_commands=["python -m pytest tests/integration/governance -q"],
        timestamp=TIMESTAMP,
    )


def _reviewer_context(verdict) -> PromotionGateContext:
    return PromotionGateContext(
        reviewer_verdict=verdict,
        implementer_id=IMPLEMENTER_ID,
        implementer_role=IMPLEMENTER_ROLE,
    )


def _trial_record():
    return create_trial_ledger_record(
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        run_id="diagnostics-run-argov-p15",
        variant_id="variant-registry-integration",
        status=TrialStatus.COMPLETED,
        parameters={"threshold": 0.25, "window": 20},
        metrics_summary={"coverage": 0.75},
        failure_reason=None,
        oos_touched_flag=False,
        locked_test_contamination_flag=False,
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
    )


def _evidence_bundle(record, verdict):
    return create_evidence_bundle(
        alpha_spec_id=ALPHA_SPEC_ID,
        study_spec_id=STUDY_SPEC_ID,
        trial_ids=[record.trial_id],
        data_version="synthetic-data-v1",
        factor_version="synthetic-factor-v1",
        label_version="synthetic-label-v1",
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
        diagnostics_summary={
            "diagnostics_run_ref": "diagnostics-run-argov-p15",
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


def _promotion_decision(record, bundle, verdict):
    return create_promotion_decision(
        alpha_spec_id=ALPHA_SPEC_ID,
        evidence_bundle_id=bundle.evidence_bundle_id,
        trial_ledger_refs=[record.trial_id],
        previous_state=PromotionLifecycleState.REVIEWED,
        next_state=PromotionLifecycleState.CANDIDATE,
        decision=PromotionDecisionOutcome.CANDIDATE,
        rationale="Synthetic governance metadata supports this controlled state transition.",
        reviewer_verdict_id=verdict.reviewer_verdict_id,
        warnings=["This decision is not live, capital, or production approval."],
        timestamp=TIMESTAMP,
    )


def test_registry_persists_and_resolves_governance_objects_by_id_and_state(
    tmp_path: Path,
) -> None:
    registry = GovernanceRegistry(tmp_path / "governance-registry.sqlite3")
    hypothesis = HypothesisCard.from_mapping(_load_fixture("hypothesis_card_valid.json"))
    alpha = AlphaSpec.from_mapping(_load_fixture("alpha_spec_valid.json"))
    feature = FeatureRequest.from_mapping(_load_fixture("feature_request_valid.json"))
    label = LabelSpec.from_mapping(_load_fixture("label_spec_valid.json"))
    study = StudySpec.from_mapping(_load_fixture("study_spec_valid.json"))
    verdict = _reviewer_verdict()
    trial = _trial_record()
    bundle = _evidence_bundle(trial, verdict)
    decision = _promotion_decision(trial, bundle, verdict)
    rejected = create_rejected_idea_record(
        alpha_spec_id_or_hypothesis_id=ALPHA_SPEC_ID,
        reason_category=RejectedIdeaReasonCategory.WEAK_EVIDENCE,
        evidence_references=[bundle.evidence_bundle_id, trial.trial_id],
        duplicate_links=[hypothesis.hypothesis_id],
        leakage_cost_weakness_notes=["Synthetic evidence did not meet a later review threshold."],
        reviewer="reviewer:independent-governance-reviewer",
        created_at=TIMESTAMP,
    )
    canary = create_negative_control_result(
        canary_type=NegativeControlType.RANDOM_TARGET,
        expected_failure=expected_failure_for_canary_type(NegativeControlType.RANDOM_TARGET),
        observed_result=expected_failure_for_canary_type(NegativeControlType.RANDOM_TARGET),
        pass_fail="PASS",
        related_study_or_evidence=study.study_spec_id,
        notes="Synthetic metadata record; validates guard behavior only.",
    )

    registry.save(hypothesis, "DRAFT")
    registry.save(alpha, "REGISTERED")
    registry.save(feature, "IMPLEMENTATION_ALLOWED")
    registry.save(label, "IMPLEMENTED")
    registry.save(study, "DIAGNOSTICS_ALLOWED")
    registry.save(trial, "DIAGNOSTICS_RUN")
    registry.save(canary, "DIAGNOSTICS_RUN")
    registry.save(bundle, "EVIDENCE_READY")
    registry.save(verdict, "REVIEWED", gate_context=_reviewer_context(verdict))
    registry.save(
        decision,
        "CANDIDATE",
        gate_context=PromotionGateContext(
            promotion_decision=decision,
            reviewer_verdict=verdict,
            implementer_id=IMPLEMENTER_ID,
            implementer_role=IMPLEMENTER_ROLE,
            evidence_bundle=bundle,
            trial_ledger_records=(trial,),
        ),
    )
    registry.save(rejected, "REJECTED")

    assert registry.get_object(alpha.alpha_spec_id) == alpha
    assert registry.get_object(verdict.reviewer_verdict_id) == verdict
    assert registry.get_object(decision.promotion_id) == decision
    assert registry.get(decision.promotion_id).latest_lifecycle_state == "CANDIDATE"

    diagnostics_entries = registry.list_by_lifecycle_state("DIAGNOSTICS_RUN")
    assert {entry.object_id for entry in diagnostics_entries} == {
        trial.trial_id,
        canary.canary_id,
    }

    reviewed_verdicts = registry.list_by_lifecycle_state(
        "REVIEWED",
        object_kind=GovernanceIdKind.REVIEWER_VERDICT,
    )
    assert [entry.object_id for entry in reviewed_verdicts] == [verdict.reviewer_verdict_id]

    candidate_decisions = registry.list_by_lifecycle_state("CANDIDATE")
    assert [entry.object_id for entry in candidate_decisions] == [decision.promotion_id]


def test_registry_rejects_invalid_writes_and_missing_records(tmp_path: Path) -> None:
    registry = GovernanceRegistry(tmp_path / "governance-registry.sqlite3")
    alpha_payload = _load_fixture("alpha_spec_valid.json")
    alpha_payload["alpha_spec_id"] = "aspec_000000000000000000000000"

    with pytest.raises(GovernanceValidationError) as invalid_write:
        registry.save(alpha_payload, "REGISTERED", object_kind=GovernanceIdKind.ALPHA_SPEC)

    assert invalid_write.value.issues[0].code == "alpha_spec_id_mismatch"

    missing_id = "aspec_111111111111111111111111"
    with pytest.raises(GovernanceValidationError) as missing_read:
        registry.get_object(missing_id)

    assert missing_read.value.issues[0].code == "governance_record_not_found"

    valid_alpha = AlphaSpec.from_mapping(_load_fixture("alpha_spec_valid.json"))
    with pytest.raises(GovernanceValidationError) as prohibited_state:
        registry.save(valid_alpha, "LIVE_APPROVED")

    assert prohibited_state.value.issues[0].code == "prohibited_mvp_state"


def test_registry_requires_gate_context_for_review_and_promotion_writes(
    tmp_path: Path,
) -> None:
    registry = GovernanceRegistry(tmp_path / "governance-registry.sqlite3")
    verdict = _reviewer_verdict()
    trial = _trial_record()
    bundle = _evidence_bundle(trial, verdict)
    decision = _promotion_decision(trial, bundle, verdict)

    with pytest.raises(GovernanceValidationError) as missing_verdict_context:
        registry.save(verdict, "REVIEWED")

    assert missing_verdict_context.value.issues[0].code == "gate_context_required"

    self_review = create_reviewer_verdict(
        reviewer_id=IMPLEMENTER_ID,
        role=REVIEWER_ROLE,
        independence_statement="Reviewer identity is intentionally not independent.",
        verdict="PASS",
        blocking_issues=[],
        warnings=["Synthetic governance review only; no market claim is made."],
        checked_artifacts=["src/alpha_system/governance/registry.py"],
        checked_commands=["python -m pytest tests/integration/governance -q"],
        timestamp=TIMESTAMP,
    )
    with pytest.raises(GovernanceValidationError) as self_approval:
        registry.save(
            self_review,
            "REVIEWED",
            gate_context=_reviewer_context(self_review),
        )

    assert any(issue.code == "reviewer_self_approval" for issue in self_approval.value.issues)

    with pytest.raises(GovernanceValidationError) as missing_decision_context:
        registry.save(decision, "CANDIDATE")

    assert missing_decision_context.value.issues[0].code == "gate_context_required"


def test_registry_malformed_rows_fail_closed_on_read(tmp_path: Path) -> None:
    registry_path = tmp_path / "governance-registry.sqlite3"
    registry = GovernanceRegistry(registry_path)
    bad_id = generate_governance_id(
        GovernanceIdKind.ALPHA_SPEC,
        {"fixture": "malformed-registry-row"},
    )

    with connect_registry(registry_path) as connection:
        ensure_governance_registry_schema(connection)
        connection.execute(
            f"""
            INSERT INTO {GOVERNANCE_OBJECT_TABLE} (
                object_id, object_kind, payload_json, content_hash
            )
            VALUES (?, ?, ?, ?)
            """,
            (bad_id, GovernanceIdKind.ALPHA_SPEC.value, "{", "not-a-real-hash"),
        )
        connection.execute(
            f"""
            INSERT INTO {GOVERNANCE_LIFECYCLE_TABLE} (
                object_id, object_kind, lifecycle_state
            )
            VALUES (?, ?, ?)
            """,
            (bad_id, GovernanceIdKind.ALPHA_SPEC.value, "REGISTERED"),
        )

    with pytest.raises(GovernanceValidationError) as malformed_read:
        registry.get_object(bad_id)

    assert malformed_read.value.issues[0].code == "malformed_governance_registry_payload"
