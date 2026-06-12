from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from alpha_system.cli.main import main
from alpha_system.governance.alpha_spec import generate_alpha_spec_id
from alpha_system.governance.evidence_bundle import EvidenceBundle, create_evidence_bundle
from alpha_system.governance.promotion import (
    PromotionDecisionOutcome,
    PromotionLifecycleState,
    create_promotion_decision,
)
from alpha_system.governance.promotion_gate import PromotionGateContext
from alpha_system.governance.registry import GovernanceRegistry
from alpha_system.governance.reviewer_verdict import ReviewerVerdict, create_reviewer_verdict
from alpha_system.governance.study_spec import StudySpec
from alpha_system.governance.trial_ledger import (
    TrialLedgerRecord,
    TrialStatus,
    create_trial_ledger_record,
)
from alpha_system.governance.variant_ledger import validate_variant_and_family_budget

FIXTURE_ROOT = Path("tests/fixtures/governance")
HYPOTHESIS_FIXTURE = FIXTURE_ROOT / "hypothesis_card_valid.json"
ALPHA_FIXTURE = FIXTURE_ROOT / "alpha_spec_valid.json"
STUDY_FIXTURE = FIXTURE_ROOT / "study_spec_valid.json"

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_ID = "sspec_438ceffd40855205de5497f0"
IMPLEMENTER_ID = "codex:argov-p16-executor"
IMPLEMENTER_ROLE = "codex_executor"
REVIEWER_ID = "claude:independent-governance-reviewer"
REVIEWER_ROLE = "claude_reviewer"
CODE_HASH = "a" * 64
CONFIG_HASH = "b" * 64
MANIFEST_HASH = "c" * 64
TIMESTAMP = "2026-06-03T13:52:09Z"


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return path


def _trial_ledger_file(tmp_path: Path) -> Path:
    return _write_json(
        tmp_path / "trial-ledger.json",
        {
            "schema": "synthetic-trial-ledger-v1",
            "records": [],
        },
    )


def _linked_alpha_spec(tmp_path: Path) -> Path:
    hypothesis = _load_json(HYPOTHESIS_FIXTURE)
    alpha = _load_json(ALPHA_FIXTURE)
    alpha["hypothesis_id"] = hypothesis["hypothesis_id"]
    alpha["alpha_spec_id"] = generate_alpha_spec_id(alpha)
    return _write_json(tmp_path / "linked-alpha-spec.json", alpha)


def _trial_record(
    *,
    run_id: str = "diagnostics-run-cli-001",
    variant_id: str = "variant-cli-001",
    status: TrialStatus = TrialStatus.COMPLETED,
    failure_reason: str | None = None,
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
        locked_test_contamination_flag=False,
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
    )


def _reviewer_verdict(
    *,
    reviewer_id: str = REVIEWER_ID,
    role: str = REVIEWER_ROLE,
) -> ReviewerVerdict:
    return create_reviewer_verdict(
        reviewer_id=reviewer_id,
        role=role,
        independence_statement="Reviewer identity and role are independent from the implementer.",
        verdict="PASS",
        blocking_issues=[],
        warnings=["Synthetic governance review only; no market claim is made."],
        checked_artifacts=["src/alpha_system/cli/governance.py"],
        checked_commands=["python -m pytest tests/unit/governance/test_cli.py -q"],
        timestamp=TIMESTAMP,
    )


def _reviewer_context(verdict: ReviewerVerdict) -> PromotionGateContext:
    return PromotionGateContext(
        reviewer_verdict=verdict,
        implementer_id=IMPLEMENTER_ID,
        implementer_role=IMPLEMENTER_ROLE,
    )


def _evidence_bundle(
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
            "diagnostics_run_ref": "diagnostics-run-cli-001",
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


def _run_cli(argv: list[str], capsys) -> tuple[int, dict[str, object]]:
    code = main(argv)
    captured = capsys.readouterr()
    stream = captured.out if code == 0 else captured.err
    return code, json.loads(stream)


def test_validate_spec_accepts_linked_hypothesis_and_alpha_spec(
    tmp_path: Path,
    capsys,
) -> None:
    alpha_path = _linked_alpha_spec(tmp_path)

    code, payload = _run_cli(
        [
            "governance",
            "validate-spec",
            str(alpha_path),
            "--hypothesis-card",
            str(HYPOTHESIS_FIXTURE),
        ],
        capsys,
    )

    assert code == 0
    assert payload["status"] == "ok"
    assert payload["validated_transition"] == "DRAFT->REGISTERED"


def test_validate_spec_rejects_mismatched_hypothesis_reference(capsys) -> None:
    code, payload = _run_cli(
        [
            "governance",
            "validate-spec",
            str(ALPHA_FIXTURE),
            "--hypothesis-card",
            str(HYPOTHESIS_FIXTURE),
        ],
        capsys,
    )

    assert code == 2
    assert payload["status"] == "rejected"
    assert payload["issues"][0]["code"] == "hypothesis_id_mismatch"


def test_register_trial_persists_failed_trials_without_dropping_variant_metadata(
    tmp_path: Path,
    capsys,
) -> None:
    registry_path = tmp_path / "governance.sqlite3"
    failed = _trial_record(
        run_id="diagnostics-run-cli-failed",
        variant_id="variant-cli-failed",
        status=TrialStatus.FAILED,
        failure_reason="synthetic dependency check failed before metrics existed",
    )
    trial_path = _write_json(tmp_path / "failed-trial.json", failed.to_dict())

    code, payload = _run_cli(
        [
            "governance",
            "register-trial",
            "--registry-path",
            str(registry_path),
            str(trial_path),
        ],
        capsys,
    )

    assert code == 0
    assert payload["entry"]["object_id"] == failed.trial_id
    stored = GovernanceRegistry(registry_path).get_object(failed.trial_id)
    assert isinstance(stored, TrialLedgerRecord)
    assert stored.status is TrialStatus.FAILED
    assert stored.variant_id == "variant-cli-failed"


def test_build_evidence_requires_complete_manifest_hash_and_version_fields(
    tmp_path: Path,
    capsys,
) -> None:
    registry_path = tmp_path / "governance.sqlite3"
    bundle = _evidence_bundle((_trial_record(),), _reviewer_verdict()).to_dict()
    del bundle["artifact_manifest"]
    bundle_path = _write_json(tmp_path / "incomplete-evidence.json", bundle)

    code, payload = _run_cli(
        [
            "governance",
            "build-evidence",
            "--registry-path",
            str(registry_path),
            str(bundle_path),
        ],
        capsys,
    )

    assert code == 2
    assert payload["issues"][0]["field"] == "artifact_manifest"
    assert payload["issues"][0]["code"] == "missing_required_field"


def test_build_evidence_requires_existing_study_and_trial_refs(
    tmp_path: Path,
    capsys,
) -> None:
    registry_path = tmp_path / "governance.sqlite3"
    registry = GovernanceRegistry(registry_path)
    registry.save(StudySpec.from_mapping(_load_json(STUDY_FIXTURE)), "DIAGNOSTICS_ALLOWED")
    bundle_path = _write_json(
        tmp_path / "evidence-missing-trial.json",
        _evidence_bundle((_trial_record(),), _reviewer_verdict()).to_dict(),
    )

    code, payload = _run_cli(
        [
            "governance",
            "build-evidence",
            "--registry-path",
            str(registry_path),
            str(bundle_path),
        ],
        capsys,
    )

    assert code == 2
    assert payload["issues"][0]["code"] == "governance_record_not_found"


def test_build_evidence_without_trial_ledger_path_rejects_at_gate(
    tmp_path: Path,
    capsys,
) -> None:
    registry_path = tmp_path / "governance.sqlite3"
    registry = GovernanceRegistry(registry_path)
    trial = _trial_record()
    registry.save(StudySpec.from_mapping(_load_json(STUDY_FIXTURE)), "DIAGNOSTICS_ALLOWED")
    registry.save(trial, "DIAGNOSTICS_RUN")
    bundle_path = _write_json(
        tmp_path / "evidence-bundle.json",
        _evidence_bundle((trial,), _reviewer_verdict()).to_dict(),
    )

    code, payload = _run_cli(
        [
            "governance",
            "build-evidence",
            "--registry-path",
            str(registry_path),
            str(bundle_path),
        ],
        capsys,
    )

    assert code == 2
    assert payload["status"] == "rejected"
    assert payload["issues"][0]["code"] == "missing_trial_ledger_path"


def test_build_evidence_with_trial_ledger_still_requires_variant_ledger_path(
    tmp_path: Path,
    capsys,
) -> None:
    registry_path = tmp_path / "governance.sqlite3"
    registry = GovernanceRegistry(registry_path)
    trial = _trial_record()
    registry.save(StudySpec.from_mapping(_load_json(STUDY_FIXTURE)), "DIAGNOSTICS_ALLOWED")
    registry.save(trial, "DIAGNOSTICS_RUN")
    bundle_path = _write_json(
        tmp_path / "evidence-bundle.json",
        _evidence_bundle((trial,), _reviewer_verdict()).to_dict(),
    )

    code, payload = _run_cli(
        [
            "governance",
            "build-evidence",
            "--registry-path",
            str(registry_path),
            "--trial-ledger-path",
            str(_trial_ledger_file(tmp_path)),
            "--family-id",
            "family-cli-rigor",
            str(bundle_path),
        ],
        capsys,
    )

    assert code == 2
    assert payload["status"] == "rejected"
    assert payload["issues"][0]["code"] == "missing_variant_ledger_path"


def test_variant_ledger_summary_is_read_only(tmp_path: Path, capsys) -> None:
    ledger_path = tmp_path / "variant-ledger.jsonl"
    ledger_path.write_text("", encoding="utf-8")
    spec = StudySpec.from_mapping(_load_json(STUDY_FIXTURE))
    record = _trial_record()
    validate_variant_and_family_budget(
        spec,
        trial_ledger_records=(record,),
        family_id="family-cli-rigor",
        variant_ledger_path=ledger_path,
        created_at=TIMESTAMP,
    )
    before = ledger_path.read_text(encoding="utf-8")

    code, payload = _run_cli(
        [
            "governance",
            "variant-ledger-summary",
            "--ledger-path",
            str(ledger_path),
            "--family-id",
            "family-cli-rigor",
            "--family-budget",
            "2",
        ],
        capsys,
    )

    assert code == 0
    assert payload["status"] == "ok"
    assert payload["record_count"] == 1
    assert payload["families"]["family-cli-rigor"]["observed_variant_count"] == 1
    assert payload["family_budget_check"]["status"] == "RESPECTED"
    assert ledger_path.read_text(encoding="utf-8") == before


def test_review_rejects_self_approval(capsys, tmp_path: Path) -> None:
    registry_path = tmp_path / "governance.sqlite3"
    verdict_path = _write_json(
        tmp_path / "self-review.json",
        _reviewer_verdict(reviewer_id=IMPLEMENTER_ID).to_dict(),
    )

    code, payload = _run_cli(
        [
            "governance",
            "review",
            "--registry-path",
            str(registry_path),
            "--implementer-id",
            IMPLEMENTER_ID,
            "--implementer-role",
            IMPLEMENTER_ROLE,
            str(verdict_path),
        ],
        capsys,
    )

    assert code == 2
    assert any(issue["code"] == "reviewer_self_approval" for issue in payload["issues"])


def test_promote_routes_complete_trial_context_to_gate_and_blocks_failed_run_omission(
    tmp_path: Path,
    capsys,
) -> None:
    registry_path = tmp_path / "governance.sqlite3"
    registry = GovernanceRegistry(registry_path)
    completed = _trial_record(run_id="diagnostics-run-cli-completed", variant_id="variant-a")
    failed = _trial_record(
        run_id="diagnostics-run-cli-failed",
        variant_id="variant-b",
        status=TrialStatus.FAILED,
        failure_reason="synthetic dependency check failed before metrics existed",
    )
    verdict = _reviewer_verdict()
    incomplete_bundle = _evidence_bundle((completed,), verdict)
    decision = create_promotion_decision(
        alpha_spec_id=ALPHA_SPEC_ID,
        evidence_bundle_id=incomplete_bundle.evidence_bundle_id,
        trial_ledger_refs=[completed.trial_id],
        previous_state=PromotionLifecycleState.REVIEWED,
        next_state=PromotionLifecycleState.CANDIDATE,
        decision=PromotionDecisionOutcome.CANDIDATE,
        rationale="Synthetic governance metadata supports this controlled state transition.",
        reviewer_verdict_id=verdict.reviewer_verdict_id,
        warnings=["This decision is not live, capital, or production approval."],
        timestamp=TIMESTAMP,
    )
    registry.save(completed, "DIAGNOSTICS_RUN")
    registry.save(failed, "DIAGNOSTICS_RUN")
    registry.save(incomplete_bundle, "EVIDENCE_READY")
    registry.save(verdict, "REVIEWED", gate_context=_reviewer_context(verdict))
    decision_path = _write_json(tmp_path / "promotion-decision.json", decision.to_dict())

    code, payload = _run_cli(
        [
            "governance",
            "promote",
            "--registry-path",
            str(registry_path),
            "--implementer-id",
            IMPLEMENTER_ID,
            "--implementer-role",
            IMPLEMENTER_ROLE,
            str(decision_path),
        ],
        capsys,
    )

    assert code == 2
    assert payload["issues"][0]["code"] == "failed_run_omission"


def test_promote_rejects_prohibited_mvp_state_before_persistence(
    tmp_path: Path,
    capsys,
) -> None:
    completed = _trial_record()
    verdict = _reviewer_verdict()
    bundle = _evidence_bundle((completed,), verdict)
    decision = create_promotion_decision(
        alpha_spec_id=ALPHA_SPEC_ID,
        evidence_bundle_id=bundle.evidence_bundle_id,
        trial_ledger_refs=[completed.trial_id],
        previous_state=PromotionLifecycleState.REVIEWED,
        next_state=PromotionLifecycleState.CANDIDATE,
        decision=PromotionDecisionOutcome.CANDIDATE,
        rationale="Synthetic governance metadata supports this controlled state transition.",
        reviewer_verdict_id=verdict.reviewer_verdict_id,
        warnings=["This decision is not live, capital, or production approval."],
        timestamp=TIMESTAMP,
    )
    payload = decision.to_dict()
    payload["next_state"] = "LIVE_APPROVED"
    decision_path = _write_json(tmp_path / "prohibited-decision.json", payload)

    code, result = _run_cli(
        [
            "governance",
            "promote",
            "--registry-path",
            str(tmp_path / "governance.sqlite3"),
            "--implementer-id",
            IMPLEMENTER_ID,
            "--implementer-role",
            IMPLEMENTER_ROLE,
            str(decision_path),
        ],
        capsys,
    )

    assert code == 2
    assert any(issue["code"] == "prohibited_mvp_state" for issue in result["issues"])


def test_validation_tool_uses_same_spec_gate(tmp_path: Path) -> None:
    alpha_path = _linked_alpha_spec(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "tools/governance/validate_objects.py",
            "--alpha-spec",
            str(alpha_path),
            "--hypothesis-card",
            str(HYPOTHESIS_FIXTURE),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["validations"][0]["validated_transition"] == "DRAFT->REGISTERED"
