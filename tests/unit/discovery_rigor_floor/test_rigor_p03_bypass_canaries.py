from __future__ import annotations

import json
from pathlib import Path

import pytest

from alpha_system.governance.canaries import (
    REQUIRED_NEGATIVE_CONTROL_TYPES,
    NegativeControlPassFail,
    create_negative_control_result,
    expected_failure_for_canary_type,
)
from alpha_system.governance.evidence_bundle import create_evidence_bundle
from alpha_system.governance.promotion_gate import (
    PromotionGateContext,
    validate_governance_transition,
)
from alpha_system.governance.sealed_holdout import (
    HoldoutAccessType,
    SealedHoldoutRegistry,
    SealedHoldoutStatus,
    create_sealed_holdout_window,
    emit_holdout_access_if_intersects,
    transition_sealed_holdout_status,
)
from alpha_system.governance.study_spec import (
    StudySpec,
    generate_study_spec_id,
    validate_study_spec,
)
from alpha_system.governance.trial_ledger import TrialLedgerRecord, create_trial_ledger_record
from alpha_system.governance.validation import GovernanceValidationError

FIXTURE_PATH = Path("tests/fixtures/governance/study_spec_valid.json")
CODE_HASH = "a" * 64
CONFIG_HASH = "b" * 64
MANIFEST_HASH = "c" * 64
DECLARED_AT = "2026-06-11T22:36:43Z"
ACCESS_AT = "2026-06-11T23:00:00Z"
FAMILY_ID = "family-rigor-p03-canary"


def study_spec() -> StudySpec:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["study_spec_id"] = generate_study_spec_id(payload)
    return validate_study_spec(payload)


def trial_record(spec: StudySpec, *, contaminated: bool = False) -> TrialLedgerRecord:
    return create_trial_ledger_record(
        alpha_spec_id=spec.alpha_spec_id,
        study_spec_id=spec.study_spec_id,
        run_id="diagnostics-run-rigor-p03-canary",
        variant_id="variant-rigor-p03-canary",
        status="COMPLETED",
        parameters={"threshold": 0.25, "window": 20},
        metrics_summary={"coverage": 0.75},
        failure_reason=None,
        oos_touched_flag=False,
        locked_test_contamination_flag=contaminated,
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
    )


def evidence_bundle(record: TrialLedgerRecord) -> dict[str, object]:
    return create_evidence_bundle(
        alpha_spec_id=record.alpha_spec_id,
        study_spec_id=record.study_spec_id,
        trial_ids=[record.trial_id],
        data_version="synthetic-data-v1",
        factor_version="synthetic-factor-v1",
        label_version="synthetic-label-v1",
        code_hash=CODE_HASH,
        config_hash=CONFIG_HASH,
        diagnostics_summary={
            "diagnostics_run_ref": "diagnostics-run-rigor-p03-canary",
            "metric_set": "synthetic governance smoke metrics",
        },
        negative_control_results=negative_control_results(record.study_spec_id),
        limitations=["synthetic metadata fixture only"],
        artifact_manifest=[
            {
                "logical_name": "diagnostics summary",
                "role": "diagnostics_summary",
                "reference": "local/evidence/diagnostics-summary.json",
                "content_hash": MANIFEST_HASH,
            }
        ],
        reviewer_verdict_reference="rver_0123456789abcdef01234567",
    ).to_dict()


def negative_control_results(study_spec_id: str) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for control_type in REQUIRED_NEGATIVE_CONTROL_TYPES:
        expected_failure = expected_failure_for_canary_type(control_type)
        results.append(
            create_negative_control_result(
                canary_type=control_type,
                expected_failure=expected_failure,
                observed_result=expected_failure,
                pass_fail=NegativeControlPassFail.PASS,
                related_study_or_evidence=study_spec_id,
                notes=f"Synthetic {control_type} control result for P03 canaries.",
            ).to_dict()
        )
    return results


def trial_ledger_file(tmp_path: Path) -> Path:
    path = tmp_path / "trial-ledger.json"
    path.write_text(
        json.dumps({"schema": "synthetic-trial-ledger-v1", "records": []}),
        encoding="utf-8",
    )
    return path


def sealed_window(
    *,
    status: SealedHoldoutStatus = SealedHoldoutStatus.SEALED,
    symbol: str = "ES",
):
    return create_sealed_holdout_window(
        partition_spec={
            "dataset_family": "futures_core_alpha_pilot_v1",
            "symbols": [symbol],
            "split_role": "locked_test",
        },
        start_date="2025-01-01",
        end_date="2026-06-11",
        status=status,
        declared_at=DECLARED_AT,
        sealed_by="research-governance-owner",
        provenance={"compass_ref": "docs/OPERATING_COMPASS_V4.md Stage B"},
    )


def test_access_log_canary_blocks_unwritable_log(tmp_path: Path) -> None:
    registry_path = tmp_path / "sealed-holdout.json"
    registry_path.write_text(json.dumps(sealed_window().to_dict()), encoding="utf-8")
    log_path = tmp_path / "holdout-access.jsonl"
    log_path.write_text("", encoding="utf-8")
    log_path.chmod(0o444)

    try:
        with pytest.raises(GovernanceValidationError) as exc_info:
            emit_holdout_access_if_intersects(
                sealed_holdout_registry_path=registry_path,
                holdout_access_log_path=log_path,
                study_spec_id=study_spec().study_spec_id,
                actor="codex:rigor-p03-canary",
                access_type=HoldoutAccessType.TRAINING,
                rationale="Canary requires unwritable holdout log to block.",
                timestamp=ACCESS_AT,
            )
        assert exc_info.value.issues[0].code == "unwritable_holdout_access_log"
    finally:
        log_path.chmod(0o644)


def test_unbreach_canary_blocks_terminal_status_flip() -> None:
    with pytest.raises(GovernanceValidationError) as exc_info:
        transition_sealed_holdout_status(
            sealed_window(status=SealedHoldoutStatus.BREACHED),
            next_status=SealedHoldoutStatus.SEALED,
            actor="retroactive-editor",
            timestamp=ACCESS_AT,
            rationale="Canary proves BREACHED cannot be flipped back.",
        )

    assert exc_info.value.issues[0].code == "sealed_holdout_breach_is_terminal"


def test_contamination_canary_blocks_evidence_ready_even_with_metadata(tmp_path: Path) -> None:
    spec = study_spec()
    record = trial_record(spec, contaminated=True)

    with pytest.raises(GovernanceValidationError) as exc_info:
        validate_governance_transition(
            "DIAGNOSTICS_RUN",
            "EVIDENCE_READY",
            PromotionGateContext(
                evidence_bundle=evidence_bundle(record),
                study_spec=spec,
                trial_ledger_records=(record,),
                trial_ledger_path=trial_ledger_file(tmp_path),
                locked_test_contamination_metadata={
                    "recorded_trial_id": record.trial_id,
                    "summary": "Metadata is not a waiver.",
                },
                family_id=FAMILY_ID,
            ),
        )

    assert exc_info.value.issues[0].code == "locked_test_contamination_blocks_evidence_ready"


def test_second_active_window_canary_blocks_declaration(tmp_path: Path) -> None:
    registry_path = tmp_path / "sealed-holdout.json"
    registry_path.write_text(
        json.dumps(
            {
                "windows": [
                    sealed_window(symbol="ES").to_dict(),
                    sealed_window(symbol="NQ").to_dict(),
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(GovernanceValidationError) as exc_info:
        SealedHoldoutRegistry(registry_path).active_window()

    assert exc_info.value.issues[0].code == "multiple_active_sealed_holdout_windows"
