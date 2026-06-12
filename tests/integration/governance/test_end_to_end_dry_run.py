from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from alpha_system.governance.alpha_spec import AlphaSpec, generate_alpha_spec_id
from alpha_system.governance.canaries.catalog import (
    NegativeControlType,
    expected_failure_for_canary_type,
)
from alpha_system.governance.canaries.harness import run_required_governance_canaries
from alpha_system.governance.canaries.negative_control_result import (
    NegativeControlPassFail,
    NegativeControlResult,
    create_negative_control_result,
)
from alpha_system.governance.claims import (
    UnsupportedClaimError,
    validate_no_unsupported_claims,
)
from alpha_system.governance.duplicate_exposure import (
    ExposureCheckResult,
    ExposureRegistryStatus,
    apply_duplicate_exposure_notes,
    check_duplicate_exposure,
)
from alpha_system.governance.evidence_bundle import (
    EvidenceBundle,
    create_evidence_bundle,
)
from alpha_system.governance.feature_request import FeatureRequest, create_feature_request
from alpha_system.governance.hypothesis_card import (
    HypothesisCard,
    generate_hypothesis_id,
)
from alpha_system.governance.label_leakage_guard import check_label_leakage
from alpha_system.governance.label_spec import LabelSpec, create_label_spec
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
    reachable_states,
    validate_governance_transition,
)
from alpha_system.governance.registry import GovernanceRegistry
from alpha_system.governance.reviewer_verdict import (
    ReviewerVerdict,
    create_reviewer_verdict,
)
from alpha_system.governance.study_spec import StudySpec, create_study_spec
from alpha_system.governance.trial_ledger import (
    TrialLedgerRecord,
    TrialStatus,
    create_trial_ledger_record,
)
from alpha_system.governance.validation import GovernanceValidationError

FIXTURE_PATH = Path("tests/fixtures/governance/end_to_end/synthetic_lifecycle_fixture.json")
FAMILY_ID = "family-end-to-end-dry-run"


@dataclass(frozen=True, slots=True)
class DryRunObjects:
    fixture: dict[str, Any]
    hypothesis: HypothesisCard
    alpha: AlphaSpec
    feature: FeatureRequest
    label: LabelSpec
    study: StudySpec
    trials: tuple[TrialLedgerRecord, ...]
    canaries: tuple[NegativeControlResult, ...]
    verdict: ReviewerVerdict
    bundle: EvidenceBundle
    candidate_decision: PromotionDecision
    validated_decision: PromotionDecision


def test_synthetic_end_to_end_governance_dry_run(tmp_path: Path) -> None:
    objects = _build_dry_run_objects()
    registry_path = tmp_path / "governance.sqlite3"
    registry = GovernanceRegistry(registry_path)

    hypothesis_path = _write_json(tmp_path / "hypothesis-card.json", objects.hypothesis.to_dict())
    alpha_path = _write_json(tmp_path / "alpha-spec.json", objects.alpha.to_dict())

    validate_spec = _run_alpha(
        [
            "governance",
            "validate-spec",
            str(alpha_path),
            "--hypothesis-card",
            str(hypothesis_path),
        ]
    )
    assert validate_spec.returncode == 0, validate_spec.stderr
    assert json.loads(validate_spec.stdout)["validated_transition"] == "DRAFT->REGISTERED"

    registry.save(objects.hypothesis, "DRAFT")
    registry.save(objects.hypothesis, "REGISTERED")
    registry.save(objects.alpha, "REGISTERED")

    duplicate_result = check_duplicate_exposure(objects.feature, [])
    feature = apply_duplicate_exposure_notes(objects.feature, duplicate_result)
    leakage_result = check_label_leakage(
        objects.label,
        objects.fixture["clean_feature_references"],
    )
    assert duplicate_result.has_blocking_findings is False
    assert leakage_result.is_clean is True

    implementation_allowed = validate_governance_transition(
        "REGISTERED",
        "IMPLEMENTATION_ALLOWED",
        PromotionGateContext(
            alpha_spec=objects.alpha,
            duplicate_or_leakage_check_passed=(
                not duplicate_result.has_blocking_findings and leakage_result.is_clean
            ),
        ),
    )
    assert implementation_allowed.next_state is PromotionLifecycleState.IMPLEMENTATION_ALLOWED
    registry.save(objects.alpha, "IMPLEMENTATION_ALLOWED")
    registry.save(feature, "IMPLEMENTATION_ALLOWED")

    implemented = validate_governance_transition(
        "IMPLEMENTATION_ALLOWED",
        "IMPLEMENTED",
        PromotionGateContext(
            implementation_handoff_ref="handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P18.md"
        ),
    )
    assert implemented.next_state is PromotionLifecycleState.IMPLEMENTED
    registry.save(objects.label, "IMPLEMENTED")

    diagnostics_allowed = validate_governance_transition(
        "IMPLEMENTED",
        "DIAGNOSTICS_ALLOWED",
        PromotionGateContext(study_spec=objects.study),
    )
    assert diagnostics_allowed.next_state is PromotionLifecycleState.DIAGNOSTICS_ALLOWED
    registry.save(objects.study, "DIAGNOSTICS_ALLOWED")
    variant_ledger_path = tmp_path / "variant-ledger.jsonl"
    variant_ledger_path.write_text("", encoding="utf-8")

    diagnostics_run = validate_governance_transition(
        "DIAGNOSTICS_ALLOWED",
        "DIAGNOSTICS_RUN",
        PromotionGateContext(
            study_spec=objects.study,
            trial_ledger_records=objects.trials,
            family_id=FAMILY_ID,
            variant_ledger_path=variant_ledger_path,
        ),
    )
    assert set(diagnostics_run.trial_ledger_refs) == {record.trial_id for record in objects.trials}
    for canary in objects.canaries:
        registry.save(canary, "DIAGNOSTICS_RUN")
    for index, record in enumerate(objects.trials):
        trial_path = _write_json(tmp_path / f"trial-{index}.json", record.to_dict())
        trial_result = _run_alpha(
            [
                "governance",
                "register-trial",
                "--registry-path",
                str(registry_path),
                str(trial_path),
            ]
        )
        assert trial_result.returncode == 0, trial_result.stderr

    bundle_path = _write_json(tmp_path / "evidence-bundle.json", objects.bundle.to_dict())
    trial_ledger_path = _trial_ledger_file(tmp_path, objects.trials)
    evidence_result = _run_alpha(
        [
            "governance",
            "build-evidence",
            "--registry-path",
            str(registry_path),
            "--trial-ledger-path",
            str(trial_ledger_path),
            "--family-id",
            FAMILY_ID,
            "--variant-ledger-path",
            str(variant_ledger_path),
            str(bundle_path),
        ]
    )
    assert evidence_result.returncode == 0, evidence_result.stderr
    assert json.loads(evidence_result.stdout)["validated_transition"] == (
        "DIAGNOSTICS_RUN->EVIDENCE_READY"
    )

    verdict_path = _write_json(tmp_path / "reviewer-verdict.json", objects.verdict.to_dict())
    review_result = _run_alpha(
        [
            "governance",
            "review",
            "--registry-path",
            str(registry_path),
            "--implementer-id",
            str(objects.fixture["implementer"]["id"]),
            "--implementer-role",
            str(objects.fixture["implementer"]["role"]),
            str(verdict_path),
        ]
    )
    assert review_result.returncode == 0, review_result.stderr
    assert json.loads(review_result.stdout)["validated_transition"] == ("EVIDENCE_READY->REVIEWED")

    for decision in (objects.candidate_decision, objects.validated_decision):
        decision_path = _write_json(
            tmp_path / f"{decision.next_state.value.lower()}-decision.json",
            decision.to_dict(),
        )
        promote_result = _run_alpha(
            [
                "governance",
                "promote",
                "--registry-path",
                str(registry_path),
                "--implementer-id",
                str(objects.fixture["implementer"]["id"]),
                "--implementer-role",
                str(objects.fixture["implementer"]["role"]),
                str(decision_path),
            ]
        )
        assert promote_result.returncode == 0, promote_result.stderr
        assert json.loads(promote_result.stdout)["validated_transition"] == (
            f"REVIEWED->{decision.next_state.value}"
        )

    final_registry = GovernanceRegistry(registry_path)
    expected_state_objects = {
        "DRAFT": objects.hypothesis.hypothesis_id,
        "REGISTERED": objects.alpha.alpha_spec_id,
        "IMPLEMENTATION_ALLOWED": feature.feature_request_id,
        "IMPLEMENTED": objects.label.label_spec_id,
        "DIAGNOSTICS_ALLOWED": objects.study.study_spec_id,
        "DIAGNOSTICS_RUN": objects.trials[0].trial_id,
        "EVIDENCE_READY": objects.bundle.evidence_bundle_id,
        "REVIEWED": objects.verdict.reviewer_verdict_id,
        "CANDIDATE": objects.candidate_decision.promotion_id,
        "VALIDATED": objects.validated_decision.promotion_id,
    }
    for state, object_id in expected_state_objects.items():
        assert object_id in {
            entry.object_id for entry in final_registry.list_by_lifecycle_state(state)
        }

    _assert_required_blocking_paths(objects)
    _assert_negative_controls_fail_closed(objects.study.study_spec_id)
    _assert_claim_guard_blocks_unsupported_text()
    _assert_canary_runner_passes()


def _build_dry_run_objects() -> DryRunObjects:
    fixture = _load_fixture()
    hypothesis = _hypothesis_card(fixture)
    label = _label_spec(fixture)
    alpha = _alpha_spec(fixture, hypothesis, label)
    feature = _feature_request(fixture, alpha)
    study = _study_spec(fixture, alpha, label)
    trials = _trial_records(fixture, alpha, study)
    canaries = _negative_control_results(study.study_spec_id)
    verdict = _reviewer_verdict(fixture)
    bundle = _evidence_bundle(fixture, alpha, study, trials, canaries, verdict)
    candidate_decision = _promotion_decision(
        fixture,
        alpha,
        bundle,
        trials,
        verdict,
        PromotionLifecycleState.CANDIDATE,
    )
    validated_decision = _promotion_decision(
        fixture,
        alpha,
        bundle,
        trials,
        verdict,
        PromotionLifecycleState.VALIDATED,
    )
    return DryRunObjects(
        fixture=fixture,
        hypothesis=hypothesis,
        alpha=alpha,
        feature=feature,
        label=label,
        study=study,
        trials=trials,
        canaries=canaries,
        verdict=verdict,
        bundle=bundle,
        candidate_decision=candidate_decision,
        validated_decision=validated_decision,
    )


def _assert_required_blocking_paths(objects: DryRunObjects) -> None:
    _assert_blocks(
        "missing_alpha_spec",
        lambda: validate_governance_transition(
            "REGISTERED",
            "IMPLEMENTATION_ALLOWED",
            PromotionGateContext(duplicate_or_leakage_check_passed=True),
        ),
    )
    _assert_blocks(
        "missing_study_spec",
        lambda: validate_governance_transition(
            "IMPLEMENTED",
            "DIAGNOSTICS_ALLOWED",
            PromotionGateContext(),
        ),
    )
    _assert_blocks(
        "missing_trial_ledger_records",
        lambda: validate_governance_transition(
            "DIAGNOSTICS_ALLOWED",
            "DIAGNOSTICS_RUN",
            PromotionGateContext(),
        ),
    )
    _assert_blocks(
        "missing_trial_ledger_records",
        lambda: validate_governance_transition(
            "REVIEWED",
            "VALIDATED",
            PromotionGateContext(
                promotion_decision=objects.validated_decision,
                evidence_bundle=objects.bundle,
                **_reviewer_context(objects),
            ),
        ),
    )
    _assert_blocks(
        "missing_evidence_bundle",
        lambda: validate_governance_transition(
            "REVIEWED",
            "CANDIDATE",
            PromotionGateContext(
                promotion_decision=objects.candidate_decision,
                trial_ledger_records=objects.trials,
                **_reviewer_context(objects),
            ),
        ),
    )
    _assert_blocks(
        "missing_reviewer_verdict",
        lambda: validate_governance_transition(
            "REVIEWED",
            "VALIDATED",
            PromotionGateContext(
                promotion_decision=objects.validated_decision,
                evidence_bundle=objects.bundle,
                trial_ledger_records=objects.trials,
            ),
        ),
    )
    _assert_blocks(
        "reviewer_self_approval",
        lambda: validate_governance_transition(
            "EVIDENCE_READY",
            "REVIEWED",
            PromotionGateContext(
                reviewer_verdict=create_reviewer_verdict(
                    reviewer_id=str(objects.fixture["implementer"]["id"]),
                    role=str(objects.fixture["reviewer"]["role"]),
                    independence_statement=("Synthetic self-approval fixture must be rejected."),
                    verdict="PASS",
                    blocking_issues=[],
                    warnings=["Synthetic governance review record only."],
                    checked_artifacts=["tests/integration/governance/test_end_to_end_dry_run.py"],
                    checked_commands=["python -m pytest tests/integration/governance -q"],
                    timestamp=str(objects.fixture["timestamp"]),
                ),
                implementer_id=str(objects.fixture["implementer"]["id"]),
                implementer_role=str(objects.fixture["implementer"]["role"]),
            ),
        ),
    )
    _assert_blocks(
        "unrecorded_locked_test_contamination",
        lambda: _contaminated_transition(objects),
    )
    _assert_blocks(
        "failed_run_omission",
        lambda: _failed_run_omission_transition(objects),
    )
    for state in PROHIBITED_MVP_STATES:
        assert state not in reachable_states()
        assert all(state not in targets for targets in ALLOWED_TRANSITIONS.values())
        _assert_blocks(
            "prohibited_mvp_state",
            lambda state=state: validate_governance_transition("REVIEWED", state),
        )


def _assert_negative_controls_fail_closed(study_spec_id: str) -> None:
    random_target = create_negative_control_result(
        canary_type=NegativeControlType.RANDOM_TARGET,
        expected_failure=expected_failure_for_canary_type(NegativeControlType.RANDOM_TARGET),
        observed_result=expected_failure_for_canary_type(NegativeControlType.RANDOM_TARGET),
        pass_fail=NegativeControlPassFail.PASS,
        related_study_or_evidence=study_spec_id,
        notes="Synthetic random-target catalog assertion for guard behavior only.",
    )
    executable_results = run_required_governance_canaries()
    observed_types = {result.canary_type for result in executable_results}

    assert random_target.guard_caught_injected_fault is True
    assert observed_types == {
        NegativeControlType.FUTURE_SHIFT,
        NegativeControlType.PERMUTED_LABELS,
        NegativeControlType.OPTIMISTIC_FILL,
    }
    for result in executable_results:
        assert result.guard_caught_injected_fault is True
        assert result.expected_failure_observed is True


def _assert_claim_guard_blocks_unsupported_text() -> None:
    with pytest.raises(UnsupportedClaimError) as exc_info:
        validate_no_unsupported_claims(
            "Synthetic blocked input for the guard: alpha is confirmed.",
            context="ARGOV-P18 negative claim-control text",
        )

    assert any(issue.code == "unsupported_claim:alpha_validity" for issue in exc_info.value.issues)


def _assert_canary_runner_passes() -> None:
    result = subprocess.run(
        [sys.executable, "tools/hooks/canary_runner.py"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "PASS governance_future_shift" in result.stdout
    assert "PASS governance_permuted_labels" in result.stdout
    assert "PASS governance_optimistic_fill" in result.stdout


def _contaminated_transition(objects: DryRunObjects) -> None:
    contaminated = create_trial_ledger_record(
        alpha_spec_id=objects.alpha.alpha_spec_id,
        study_spec_id=objects.study.study_spec_id,
        run_id="diagnostics-run-argov-p18-contaminated",
        variant_id="variant-contaminated",
        status=TrialStatus.COMPLETED,
        parameters={"threshold": 0.35, "window": 15},
        metrics_summary={"coverage": 0.5},
        failure_reason=None,
        oos_touched_flag=False,
        locked_test_contamination_flag=True,
        code_hash=str(objects.fixture["source_hash"]),
        config_hash=str(objects.fixture["config_hash"]),
    )
    bundle = _evidence_bundle(
        objects.fixture,
        objects.alpha,
        objects.study,
        (contaminated,),
        objects.canaries,
        objects.verdict,
    )
    decision = _promotion_decision(
        objects.fixture,
        objects.alpha,
        bundle,
        (contaminated,),
        objects.verdict,
        PromotionLifecycleState.CANDIDATE,
    )
    validate_governance_transition(
        "REVIEWED",
        "CANDIDATE",
        PromotionGateContext(
            promotion_decision=decision,
            evidence_bundle=bundle,
            trial_ledger_records=(contaminated,),
            **_reviewer_context(objects),
        ),
    )


def _failed_run_omission_transition(objects: DryRunObjects) -> None:
    incomplete_decision = create_promotion_decision(
        alpha_spec_id=objects.alpha.alpha_spec_id,
        evidence_bundle_id=objects.bundle.evidence_bundle_id,
        trial_ledger_refs=[objects.trials[0].trial_id],
        previous_state=PromotionLifecycleState.REVIEWED,
        next_state=PromotionLifecycleState.CANDIDATE,
        decision=PromotionDecisionOutcome.CANDIDATE,
        rationale="Synthetic omission control must be rejected by the promotion gate.",
        reviewer_verdict_id=objects.verdict.reviewer_verdict_id,
        warnings=["Synthetic governance decision record only."],
        timestamp=str(objects.fixture["timestamp"]),
    )
    validate_governance_transition(
        "REVIEWED",
        "CANDIDATE",
        PromotionGateContext(
            promotion_decision=incomplete_decision,
            evidence_bundle=objects.bundle,
            trial_ledger_records=objects.trials,
            **_reviewer_context(objects),
        ),
    )


def _hypothesis_card(fixture: dict[str, Any]) -> HypothesisCard:
    payload = dict(fixture["hypothesis_card"])
    payload["hypothesis_id"] = generate_hypothesis_id(payload)
    return HypothesisCard.from_mapping(payload)


def _label_spec(fixture: dict[str, Any]) -> LabelSpec:
    payload = dict(fixture["label_spec"])
    return create_label_spec(
        horizon=str(payload["horizon"]),
        path_rules=dict(payload["path_rules"]),
        cost_model=dict(payload["cost_model"]),
        target_stop_rules=dict(payload["target_stop_rules"]),
        availability_time=str(payload["availability_time"]),
        forbidden_feature_overlap=dict(payload["forbidden_feature_overlap"]),
        leakage_checks=list(payload["leakage_checks"]),
    )


def _alpha_spec(
    fixture: dict[str, Any],
    hypothesis: HypothesisCard,
    label: LabelSpec,
) -> AlphaSpec:
    payload = dict(fixture["alpha_spec"])
    payload["hypothesis_id"] = hypothesis.hypothesis_id
    payload["label_references"] = [label.label_spec_id]
    payload["alpha_spec_id"] = generate_alpha_spec_id(payload)
    return AlphaSpec.from_mapping(payload)


def _feature_request(fixture: dict[str, Any], alpha: AlphaSpec) -> FeatureRequest:
    payload = dict(fixture["feature_request"])
    duplicate_notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=alpha.alpha_spec_id,
        requested_inputs=list(payload["requested_inputs"]),
        formula_sketch=dict(payload["formula_sketch"]),
        availability_assumptions=dict(payload["availability_assumptions"]),
        duplicate_or_equivalent_exposure_notes=duplicate_notes,
        data_requirements=dict(payload["data_requirements"]),
    )


def _study_spec(
    fixture: dict[str, Any],
    alpha: AlphaSpec,
    label: LabelSpec,
) -> StudySpec:
    payload = dict(fixture["study_spec"])
    return create_study_spec(
        alpha_spec_id=alpha.alpha_spec_id,
        label_spec_id=label.label_spec_id,
        dataset_scope=dict(payload["dataset_scope"]),
        split_protocol=dict(payload["split_protocol"]),
        metrics=list(payload["metrics"]),
        cost_assumptions=dict(payload["cost_assumptions"]),
        variant_budget=int(payload["variant_budget"]),
        locked_test_policy=dict(payload["locked_test_policy"]),
        negative_controls=list(payload["negative_controls"]),
        stopping_rules=list(payload["stopping_rules"]),
    )


def _trial_records(
    fixture: dict[str, Any],
    alpha: AlphaSpec,
    study: StudySpec,
) -> tuple[TrialLedgerRecord, ...]:
    return tuple(
        create_trial_ledger_record(
            alpha_spec_id=alpha.alpha_spec_id,
            study_spec_id=study.study_spec_id,
            run_id=str(record["run_id"]),
            variant_id=str(record["variant_id"]),
            status=TrialStatus(str(record["status"])),
            parameters=dict(record["parameters"]),
            metrics_summary=dict(record["metrics_summary"]),
            failure_reason=record["failure_reason"],
            oos_touched_flag=bool(record["oos_touched_flag"]),
            locked_test_contamination_flag=bool(record["locked_test_contamination_flag"]),
            code_hash=str(fixture["source_hash"]),
            config_hash=str(fixture["config_hash"]),
        )
        for record in fixture["trial_records"]
    )


def _negative_control_results(study_spec_id: str) -> tuple[NegativeControlResult, ...]:
    random_target = create_negative_control_result(
        canary_type=NegativeControlType.RANDOM_TARGET,
        expected_failure=expected_failure_for_canary_type(NegativeControlType.RANDOM_TARGET),
        observed_result=expected_failure_for_canary_type(NegativeControlType.RANDOM_TARGET),
        pass_fail=NegativeControlPassFail.PASS,
        related_study_or_evidence=study_spec_id,
        notes="Synthetic random-target catalog assertion for guard behavior only.",
    )
    executable = tuple(
        create_negative_control_result(
            canary_type=result.canary_type,
            expected_failure=result.expected_failure,
            observed_result=result.observed_result,
            pass_fail=result.pass_fail,
            related_study_or_evidence=study_spec_id,
            notes=(f"ARGOV-P18 dry-run record linked to this StudySpec; {result.notes}"),
        )
        for result in run_required_governance_canaries()
    )
    return (random_target, *executable)


def _reviewer_verdict(fixture: dict[str, Any]) -> ReviewerVerdict:
    return create_reviewer_verdict(
        reviewer_id=str(fixture["reviewer"]["id"]),
        role=str(fixture["reviewer"]["role"]),
        independence_statement=(
            "Reviewer identity and role are independent from the Codex executor."
        ),
        verdict="PASS_WITH_WARNINGS",
        blocking_issues=[],
        warnings=["Synthetic governance review record only; not a phase review."],
        checked_artifacts=[
            "tests/integration/governance/test_end_to_end_dry_run.py",
            "docs/governance/END_TO_END_DRY_RUN.md",
        ],
        checked_commands=[
            "python -m pytest tests/integration/governance/test_end_to_end_dry_run.py -q"
        ],
        timestamp=str(fixture["timestamp"]),
    )


def _evidence_bundle(
    fixture: dict[str, Any],
    alpha: AlphaSpec,
    study: StudySpec,
    trials: tuple[TrialLedgerRecord, ...],
    canaries: tuple[NegativeControlResult, ...],
    verdict: ReviewerVerdict,
) -> EvidenceBundle:
    return create_evidence_bundle(
        alpha_spec_id=alpha.alpha_spec_id,
        study_spec_id=study.study_spec_id,
        trial_ids=[record.trial_id for record in trials],
        data_version="synthetic-governance-fixture-v1",
        factor_version="synthetic-feature-metadata-v1",
        label_version="synthetic-label-metadata-v1",
        code_hash=str(fixture["source_hash"]),
        config_hash=str(fixture["config_hash"]),
        diagnostics_summary={
            "diagnostics_run_ref": "argov-p18-synthetic-dry-run",
            "metric_set": "metadata-only governance checklist",
            "negative_control_count": len(canaries),
        },
        negative_control_results=[result.to_dict() for result in canaries],
        limitations=["Synthetic metadata fixture only; no market evidence is produced."],
        artifact_manifest=[
            {
                "logical_name": "dry run summary",
                "role": "curated_summary",
                "reference": "docs/governance/END_TO_END_DRY_RUN.md",
                "content_hash": str(fixture["manifest_hash"]),
            }
        ],
        reviewer_verdict_reference=verdict.reviewer_verdict_id,
    )


def _promotion_decision(
    fixture: dict[str, Any],
    alpha: AlphaSpec,
    bundle: EvidenceBundle,
    trials: tuple[TrialLedgerRecord, ...],
    verdict: ReviewerVerdict,
    target: PromotionLifecycleState,
) -> PromotionDecision:
    return create_promotion_decision(
        alpha_spec_id=alpha.alpha_spec_id,
        evidence_bundle_id=bundle.evidence_bundle_id,
        trial_ledger_refs=[record.trial_id for record in trials],
        previous_state=PromotionLifecycleState.REVIEWED,
        next_state=target,
        decision=PromotionDecisionOutcome(target.value),
        rationale=(
            "Synthetic governance metadata satisfies the gate input checklist for "
            "this controlled transition."
        ),
        reviewer_verdict_id=verdict.reviewer_verdict_id,
        warnings=["Governance metadata only; no live, capital, or production status."],
        timestamp=str(fixture["timestamp"]),
    )


def _reviewer_context(objects: DryRunObjects) -> dict[str, object]:
    return {
        "reviewer_verdict": objects.verdict,
        "implementer_id": str(objects.fixture["implementer"]["id"]),
        "implementer_role": str(objects.fixture["implementer"]["role"]),
    }


def _assert_blocks(expected_code: str, call: Any) -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        call()
    assert any(issue.code == expected_code for issue in exc_info.value.issues)


def _run_alpha(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    return subprocess.run(
        [sys.executable, "-m", "alpha_system.cli", *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def _load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return path


def _trial_ledger_file(tmp_path: Path, records: tuple[TrialLedgerRecord, ...]) -> Path:
    return _write_json(
        tmp_path / "trial-ledger.json",
        {
            "schema": "synthetic-trial-ledger-v1",
            "records": [record.to_dict() for record in records],
        },
    )
