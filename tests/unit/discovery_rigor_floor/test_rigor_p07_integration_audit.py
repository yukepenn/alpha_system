from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.governance.canaries import (
    REQUIRED_NEGATIVE_CONTROL_TYPES,
    NegativeControlPassFail,
    NegativeControlType,
    create_negative_control_result,
    expected_failure_for_canary_type,
    run_planted_fake_alpha_canary,
)
from alpha_system.governance.evidence_bundle import (
    EvidenceBundle,
    create_evidence_bundle,
    validate_evidence_ready_gate,
)
from alpha_system.governance.promotion import create_promotion_decision
from alpha_system.governance.promotion_gate import (
    PromotionGateContext,
    validate_governance_transition,
)
from alpha_system.governance.reviewer_verdict import create_reviewer_verdict
from alpha_system.governance.sealed_holdout import (
    HoldoutAccessLog,
    HoldoutAccessType,
    SealedHoldoutStatus,
    create_sealed_holdout_window,
)
from alpha_system.governance.study_spec import (
    StudySpec,
    generate_study_spec_id,
    validate_study_spec,
)
from alpha_system.governance.trial_ledger import TrialLedgerRecord, create_trial_ledger_record
from alpha_system.governance.validation import GovernanceValidationError
from alpha_system.governance.variant_ledger import (
    VariantLedger,
    validate_variant_and_family_budget,
)
from alpha_system.governance.verdict_reason_code import VerdictReasonCode

FIXTURE_PATH = Path("tests/fixtures/governance/study_spec_valid.json")
CODE_HASH = "a" * 64
CONFIG_HASH = "b" * 64
MANIFEST_HASH = "c" * 64
CREATED_AT = "2026-06-12T00:00:00Z"
ACCESS_AT = "2026-06-12T00:01:00Z"
REVIEW_AT = "2026-06-12T00:02:00Z"
PROMOTED_AT = "2026-06-12T00:03:00Z"
FAMILY_ID = "family-rigor-p07-integration-audit"
FOCUSED_AUDIT_COMMAND = (
    "python -m pytest "
    "tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py -q"
)


def test_full_gated_path_engages_every_rigor_floor_gate_and_blocks_bypasses(
    tmp_path: Path,
) -> None:
    spec = _study_spec(variant_budget=2, family_budget=2)
    trial = _trial_record(spec, run_id="diagnostics-run-rigor-p07", variant_id="variant-a")
    paths = _tmp_gate_paths(tmp_path, trial)

    entry_result = validate_variant_and_family_budget(
        spec,
        trial_ledger_records=(trial,),
        family_id=FAMILY_ID,
        variant_ledger_path=paths["variant_ledger"],
        created_at=CREATED_AT,
        sealed_holdout_registry_path=paths["sealed_holdout"],
        holdout_access_log_path=paths["holdout_access_log"],
        holdout_access_actor="codex:rigor-p07-integration-audit",
        holdout_access_type=HoldoutAccessType.TRAINING,
        holdout_access_rationale="Synthetic audit records the study entry access.",
        holdout_access_start_date="2026-01-02",
        holdout_access_end_date="2026-01-03",
        holdout_access_partition_spec=_holdout_partition_spec(),
    )
    assert entry_result.study_budget_check.respected is True
    assert entry_result.family_budget_check is not None
    assert entry_result.family_budget_check.respected is True
    assert len(entry_result.variant_records) == 1
    assert VariantLedger(paths["variant_ledger"]).load_records()[0].trial_ids == (
        trial.trial_id,
    )
    access_records = HoldoutAccessLog(paths["holdout_access_log"]).load_records()
    assert len(access_records) == 1
    assert access_records[0].study_spec_id == spec.study_spec_id

    validate_governance_transition(
        "DIAGNOSTICS_ALLOWED",
        "DIAGNOSTICS_RUN",
        PromotionGateContext(
            study_spec=spec,
            trial_ledger_records=(trial,),
            family_id=FAMILY_ID,
            variant_ledger_path=paths["variant_ledger"],
        ),
    )
    recorded_trial = json.loads(paths["trial_ledger"].read_text())["records"][0]
    assert recorded_trial["trial_id"] == trial.trial_id

    planted = run_planted_fake_alpha_canary(workspace=tmp_path / "planted-fake-alpha")
    assert planted.rejected is True
    assert planted.blocked_issue_code == "locked_test_contamination_blocks_evidence_ready"
    assert planted.negative_control_result.pass_fail is NegativeControlPassFail.PASS

    reviewer_verdict = _reviewer_verdict()
    bundle = _evidence_bundle(
        trial,
        reviewer_verdict_id=reviewer_verdict.reviewer_verdict_id,
        planted_future_shift_result=planted.negative_control_result.to_dict(),
    )
    assert validate_evidence_ready_gate(bundle).evidence_bundle_id == bundle.evidence_bundle_id

    evidence_ready = validate_governance_transition(
        "DIAGNOSTICS_RUN",
        "EVIDENCE_READY",
        PromotionGateContext(
            evidence_bundle=bundle,
            study_spec=spec,
            trial_ledger_records=(trial,),
            trial_ledger_path=paths["trial_ledger"],
            family_id=FAMILY_ID,
            variant_ledger_path=paths["variant_ledger"],
            sealed_holdout_registry_path=paths["sealed_holdout"],
            require_sealed_holdout=True,
        ),
    )
    assert evidence_ready.evidence_bundle == bundle

    promotion_decision = create_promotion_decision(
        alpha_spec_id=spec.alpha_spec_id,
        evidence_bundle_id=bundle.evidence_bundle_id,
        trial_ledger_refs=[trial.trial_id],
        previous_state="REVIEWED",
        next_state="CANDIDATE",
        decision="CANDIDATE",
        rationale="Synthetic integration audit reached candidate gate after all guards agreed.",
        reviewer_verdict_id=reviewer_verdict.reviewer_verdict_id,
        warnings=["Synthetic audit metadata only; no market evidence."],
        timestamp=PROMOTED_AT,
    )
    promoted = validate_governance_transition(
        "REVIEWED",
        "CANDIDATE",
        PromotionGateContext(
            evidence_bundle=bundle,
            reviewer_verdict=reviewer_verdict,
            implementer_id="codex-executor",
            implementer_role="executor",
            promotion_decision=promotion_decision,
            trial_ledger_records=(trial,),
        ),
    )
    assert promoted.promotion_decision == promotion_decision

    over_budget_records = (
        _trial_record(spec, run_id="diagnostics-run-rigor-p07-overrun-a", variant_id="variant-a"),
        _trial_record(spec, run_id="diagnostics-run-rigor-p07-overrun-b", variant_id="variant-b"),
        _trial_record(spec, run_id="diagnostics-run-rigor-p07-overrun-c", variant_id="variant-c"),
    )
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_variant_and_family_budget(
            spec,
            trial_ledger_records=over_budget_records,
            family_id=FAMILY_ID,
            variant_ledger_path=_empty_variant_ledger(tmp_path / "budget-block.jsonl"),
            created_at=CREATED_AT,
        )
    _assert_issue(exc_info.value, "variant_budget_overrun")

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "DIAGNOSTICS_RUN",
            "EVIDENCE_READY",
            PromotionGateContext(
                evidence_bundle=bundle,
                study_spec=spec,
                trial_ledger_records=(trial,),
                trial_ledger_path=tmp_path / "missing-trial-ledger.json",
                family_id=FAMILY_ID,
                variant_ledger_path=paths["variant_ledger"],
            ),
        )
    _assert_issue(exc_info.value, "missing_trial_ledger")

    unwritable_trial_ledger = _trial_ledger_file(
        tmp_path / "unwritable-trial-ledger.json",
        (trial,),
    )
    unwritable_trial_ledger.chmod(0o444)
    try:
        with pytest.raises(GovernanceValidationError) as exc_info:
            validate_governance_transition(
                "DIAGNOSTICS_RUN",
                "EVIDENCE_READY",
                PromotionGateContext(
                    evidence_bundle=bundle,
                    study_spec=spec,
                    trial_ledger_records=(trial,),
                    trial_ledger_path=unwritable_trial_ledger,
                    family_id=FAMILY_ID,
                    variant_ledger_path=paths["variant_ledger"],
                ),
            )
        _assert_issue(exc_info.value, "unwritable_trial_ledger")
    finally:
        unwritable_trial_ledger.chmod(0o644)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_variant_and_family_budget(
            spec,
            trial_ledger_records=(trial,),
            family_id=FAMILY_ID,
            variant_ledger_path=_empty_variant_ledger(tmp_path / "contamination-entry.jsonl"),
            created_at=CREATED_AT,
            sealed_holdout_registry_path=paths["sealed_holdout"],
            holdout_access_log_path=_empty_access_log(tmp_path / "contamination-access.jsonl"),
            holdout_access_actor="codex:rigor-p07-integration-audit",
            holdout_access_type=HoldoutAccessType.LOCKED_TEST,
            holdout_access_rationale="Synthetic audit intentionally pokes locked test.",
            holdout_access_start_date="2026-01-02",
            holdout_access_end_date="2026-01-03",
            holdout_access_partition_spec=_holdout_partition_spec(),
        )
    _assert_issue(exc_info.value, "unauthorized_locked_test_holdout_access")

    missing_control_bundle = _evidence_bundle(
        trial,
        reviewer_verdict_id=reviewer_verdict.reviewer_verdict_id,
        planted_future_shift_result=planted.negative_control_result.to_dict(),
        omit_control=NegativeControlType.OPTIMISTIC_FILL.value,
    )
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_evidence_ready_gate(missing_control_bundle)
    _assert_issue(exc_info.value, "missing_required_negative_control_result")

    contaminated_trial = _trial_record(
        spec,
        run_id="diagnostics-run-rigor-p07-contaminated",
        variant_id="variant-a",
        contaminated=True,
    )
    contaminated_bundle = _evidence_bundle(
        contaminated_trial,
        reviewer_verdict_id=reviewer_verdict.reviewer_verdict_id,
        planted_future_shift_result=planted.negative_control_result.to_dict(),
    )
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "DIAGNOSTICS_RUN",
            "EVIDENCE_READY",
            PromotionGateContext(
                evidence_bundle=contaminated_bundle,
                study_spec=spec,
                trial_ledger_records=(contaminated_trial,),
                trial_ledger_path=paths["trial_ledger"],
                family_id=FAMILY_ID,
                variant_ledger_path=paths["variant_ledger"],
                sealed_holdout_registry_path=paths["sealed_holdout"],
                require_sealed_holdout=True,
            ),
        )
    _assert_issue(exc_info.value, "locked_test_contamination_blocks_evidence_ready")

    with pytest.raises(GovernanceValidationError) as exc_info:
        create_reviewer_verdict(
            reviewer_id="reviewer-rigor-p07",
            role="semantic-reviewer",
            independence_statement="Fresh reviewer identity differs from executor.",
            verdict="INCONCLUSIVE",
            blocking_issues=[],
            warnings=["Synthetic audit verdict branch only."],
            checked_artifacts=["tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py"],
            checked_commands=[FOCUSED_AUDIT_COMMAND],
            timestamp=REVIEW_AT,
        )
        _assert_issue(exc_info.value, "missing_reason_code_for_inconclusive")

    inconclusive_verdict = create_reviewer_verdict(
        reviewer_id="reviewer-rigor-p07",
        role="semantic-reviewer",
        independence_statement="Fresh reviewer identity differs from executor.",
        verdict="INCONCLUSIVE",
        reason_code=VerdictReasonCode.UNDERPOWERED,
        blocking_issues=[],
        warnings=["Synthetic audit verdict branch only."],
        checked_artifacts=["tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py"],
        checked_commands=[FOCUSED_AUDIT_COMMAND],
        timestamp=REVIEW_AT,
    )
    assert inconclusive_verdict.reason_code is VerdictReasonCode.UNDERPOWERED

    empty_promotion_ledger = _empty_variant_ledger(tmp_path / "promotion-block.jsonl")
    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "DIAGNOSTICS_RUN",
            "EVIDENCE_READY",
            PromotionGateContext(
                evidence_bundle=bundle,
                study_spec=spec,
                trial_ledger_records=(trial,),
                trial_ledger_path=paths["trial_ledger"],
                family_id=FAMILY_ID,
                variant_ledger_path=empty_promotion_ledger,
                sealed_holdout_registry_path=paths["sealed_holdout"],
                require_sealed_holdout=True,
            ),
        )
    _assert_issue(exc_info.value, "variant_ledger_missing_records")


def _study_spec(*, variant_budget: int, family_budget: int) -> StudySpec:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["variant_budget"] = variant_budget
    payload["family_budget"] = family_budget
    payload["negative_controls"] = list(REQUIRED_NEGATIVE_CONTROL_TYPES)
    payload["study_spec_id"] = generate_study_spec_id(payload)
    return validate_study_spec(payload)


def _trial_record(
    spec: StudySpec,
    *,
    run_id: str,
    variant_id: str,
    contaminated: bool = False,
) -> TrialLedgerRecord:
    return create_trial_ledger_record(
        alpha_spec_id=spec.alpha_spec_id,
        study_spec_id=spec.study_spec_id,
        run_id=run_id,
        variant_id=variant_id,
        status="COMPLETED",
        parameters={"audit_station": "full-gated-path"},
        metrics_summary={
            "diagnostics_status": "PASS",
            "value_free": True,
            "synthetic_audit": "RIGOR-P07",
        },
        failure_reason=None,
        oos_touched_flag=False,
        locked_test_contamination_flag=contaminated,
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
    )


def _evidence_bundle(
    trial: TrialLedgerRecord,
    *,
    reviewer_verdict_id: str,
    planted_future_shift_result: dict[str, object],
    omit_control: str | None = None,
) -> EvidenceBundle:
    return create_evidence_bundle(
        alpha_spec_id=trial.alpha_spec_id,
        study_spec_id=trial.study_spec_id,
        trial_ids=[trial.trial_id],
        data_version="synthetic-rigor-p07-data-v1",
        factor_version="synthetic-rigor-p07-factor-v1",
        label_version="synthetic-rigor-p07-label-v1",
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
        diagnostics_summary={
            "diagnostics_run_ref": trial.run_id,
            "diagnostics_status": "PASS",
            "value_free": True,
        },
        negative_control_results=_negative_control_results(
            trial.study_spec_id,
            planted_future_shift_result=planted_future_shift_result,
            omit_control=omit_control,
        ),
        limitations=["Synthetic integration-audit metadata only."],
        artifact_manifest=[
            {
                "logical_name": "synthetic integration audit",
                "role": "diagnostics_summary",
                "reference": "pytest tmp namespace",
                "content_hash": MANIFEST_HASH,
            }
        ],
        reviewer_verdict_reference=reviewer_verdict_id,
    )


def _negative_control_results(
    study_spec_id: str,
    *,
    planted_future_shift_result: dict[str, object],
    omit_control: str | None,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for control_type in REQUIRED_NEGATIVE_CONTROL_TYPES:
        if control_type == omit_control:
            continue
        if control_type == NegativeControlType.FUTURE_SHIFT.value:
            results.append(
                create_negative_control_result(
                    canary_type=control_type,
                    expected_failure=str(planted_future_shift_result["expected_failure"]),
                    observed_result=str(planted_future_shift_result["observed_result"]),
                    pass_fail=str(planted_future_shift_result["pass_fail"]),
                    related_study_or_evidence=study_spec_id,
                    notes=(
                        "RIGOR-P07 evidence gate carries the planted-fake-alpha "
                        "future-shift canary outcome for this synthetic study."
                    ),
                ).to_dict()
            )
            continue
        expected_failure = expected_failure_for_canary_type(control_type)
        results.append(
            create_negative_control_result(
                canary_type=control_type,
                expected_failure=expected_failure,
                observed_result=expected_failure,
                pass_fail=NegativeControlPassFail.PASS,
                related_study_or_evidence=study_spec_id,
                notes=f"RIGOR-P07 synthetic {control_type} negative-control PASS.",
            ).to_dict()
        )
    return results


def _reviewer_verdict():
    return create_reviewer_verdict(
        reviewer_id="reviewer-rigor-p07",
        role="semantic-reviewer",
        independence_statement="Fresh reviewer identity differs from executor.",
        verdict="PASS",
        blocking_issues=[],
        warnings=["Synthetic integration audit only; no market claim."],
        checked_artifacts=["tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py"],
        checked_commands=[FOCUSED_AUDIT_COMMAND],
        timestamp=REVIEW_AT,
    )


def _tmp_gate_paths(
    tmp_path: Path,
    trial: TrialLedgerRecord,
) -> dict[str, Path]:
    sealed_holdout = tmp_path / "sealed-holdout.json"
    sealed_holdout.write_text(json.dumps(_sealed_window().to_dict()), encoding="utf-8")
    return {
        "trial_ledger": _trial_ledger_file(tmp_path / "trial-ledger.json", (trial,)),
        "variant_ledger": _empty_variant_ledger(tmp_path / "variant-ledger.jsonl"),
        "sealed_holdout": sealed_holdout,
        "holdout_access_log": _empty_access_log(tmp_path / "holdout-access.jsonl"),
    }


def _trial_ledger_file(path: Path, records: tuple[TrialLedgerRecord, ...]) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema": "synthetic-trial-ledger-v1",
                "records": [record.to_dict() for record in records],
            },
            sort_keys=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _empty_variant_ledger(path: Path) -> Path:
    path.write_text("", encoding="utf-8")
    return path


def _empty_access_log(path: Path) -> Path:
    path.write_text("", encoding="utf-8")
    return path


def _sealed_window():
    return create_sealed_holdout_window(
        partition_spec=_holdout_partition_spec(),
        start_date="2025-01-01",
        end_date=None,
        rolling=True,
        status=SealedHoldoutStatus.SEALED,
        declared_at=CREATED_AT,
        sealed_by="research-governance-owner",
        provenance={"compass_ref": "docs/OPERATING_COMPASS_V4.md Stage B"},
    )


def _holdout_partition_spec() -> dict[str, object]:
    return {
        "source": "tiny synthetic governance fixture metadata, not real market data",
        "instrument_universe": "SYNTH_US_EQUITY_LARGE_CAP fixture universe only",
        "split_role": "locked_test",
    }


def _assert_issue(error: GovernanceValidationError, expected_code: str) -> None:
    assert expected_code in {issue.code for issue in error.issues}
