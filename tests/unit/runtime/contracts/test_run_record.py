from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from alpha_system.runtime.contracts.artifacts import RuntimeArtifactEntry, RuntimeArtifactManifest
from alpha_system.runtime.contracts.manifest import StudyRunManifest
from alpha_system.runtime.contracts.run_record import (
    RunRejectionReason,
    StudyRunRecord,
    StudyRunRecordContractError,
    StudyRunResultState,
)
from alpha_system.runtime.contracts.run_spec import RuntimeLifecycleState


def test_study_run_record_is_immutable_hashable_and_reference_only() -> None:
    record = _record()
    same_record = _record()

    assert record.result_state is StudyRunResultState.REFERENCE_HANDOFF_READY
    assert record.record_hash == same_record.record_hash
    assert hash(record)
    payload = record.to_dict()
    assert payload["value_free"] is True
    assert "runtime_plan" not in payload["study_run_spec_ref"]
    assert "values" not in str(payload)
    assert "rows" not in str(payload)
    with pytest.raises(FrozenInstanceError):
        record.run_id = "changed"  # type: ignore[misc]


def test_runtime_lifecycle_state_inputs_can_be_carried_without_redefinition() -> None:
    record = _record(result_state=RuntimeLifecycleState.PLAN_VALIDATED)

    assert record.result_state is StudyRunResultState.PLAN_VALIDATED


@pytest.mark.parametrize(
    "prohibited_state",
    [
        "ALPHA_VALIDATED",
        "FACTOR_PROMOTED",
        "STRATEGY_READY",
        "PORTFOLIO_READY",
        "LIVE_READY",
        "PAPER_READY",
        "PROFITABLE",
        "TRADABLE",
        "PRODUCTION_READY",
    ],
)
def test_prohibited_mvp_states_cannot_be_constructed(prohibited_state: str) -> None:
    with pytest.raises(ValueError):
        StudyRunResultState(prohibited_state)

    with pytest.raises(ValueError):
        _record(result_state=prohibited_state)


@pytest.mark.parametrize(
    "terminal_state",
    [
        StudyRunResultState.REJECTED,
        StudyRunResultState.INCONCLUSIVE,
        StudyRunResultState.BLOCKED,
    ],
)
def test_terminal_failure_record_without_rejection_reason_is_rejected(
    terminal_state: StudyRunResultState,
) -> None:
    with pytest.raises(StudyRunRecordContractError):
        _record(result_state=terminal_state, rejection_reasons=())


def test_terminal_failure_record_keeps_rejection_reasons_visible() -> None:
    record = _record(
        result_state=StudyRunResultState.BLOCKED,
        rejection_reasons=[
            RunRejectionReason(
                code="dataset_lineage_missing",
                message="Dataset lineage reference was unavailable.",
            )
        ],
    )

    assert record.rejection_reasons[0].code == "dataset_lineage_missing"
    assert record.to_dict()["rejection_reasons"] == [
        {
            "code": "dataset_lineage_missing",
            "message": "Dataset lineage reference was unavailable.",
        }
    ]


def test_record_rejects_inline_values_in_reference_mappings() -> None:
    with pytest.raises(StudyRunRecordContractError):
        _record(
            artifact_refs=[
                {
                    "artifact_id": "bad_artifact_ref",
                    "location": "summaries/bad.json",
                    "content_hash": "a" * 64,
                    "rows": [{"not": "allowed"}],
                }
            ]
        )

    with pytest.raises(StudyRunRecordContractError):
        _record(
            manifest_ref={
                "manifest_id": "smanifest_fixture",
                "manifest_hash": "b" * 64,
                "data": [1, 2, 3],
            }
        )


def _record(**overrides: object) -> StudyRunRecord:
    artifacts = RuntimeArtifactManifest(
        run_id="run_rt_p05_fixture",
        entries=[
            RuntimeArtifactEntry(
                artifact_id="diagnostic_summary",
                kind="diagnostic_summary",
                location="summaries/diagnostic-summary.json",
                content_hash="6" * 64,
                size_bytes=512,
            )
        ],
    )
    values: dict[str, object] = {
        "run_id": "run_rt_p05_fixture",
        "study_run_spec_ref": {
            "study_run_spec_id": "srun_" + "1" * 24,
            "content_hash": "2" * 64,
        },
        "result_state": StudyRunResultState.REFERENCE_HANDOFF_READY,
        "manifest_ref": _manifest(),
        "rejection_reasons": (),
        "artifact_refs": [artifacts],
    }
    values.update(overrides)
    return StudyRunRecord(**values)  # type: ignore[arg-type]


def _manifest() -> StudyRunManifest:
    return StudyRunManifest(
        run_id="run_rt_p05_fixture",
        dataset_version_id="dsv_synthetic_runtime_fixture_v1",
        dataset_version_hash="0" * 64,
        dataset_lineage_ref="dataset_lineage_fixture_v1",
        dataset_admissibility_state="VERSIONED",
        feature_pack_versions=[
            {
                "pack_id": "feature_pack_v1",
                "content_hash": "1" * 64,
                "lineage_ref": "feature_lineage_v1",
                "available_ts_ref": "features.available_ts",
            }
        ],
        label_pack_versions=[
            {
                "pack_id": "label_pack_v1",
                "content_hash": "2" * 64,
                "lineage_ref": "label_lineage_v1",
                "label_available_ts_ref": "labels.label_available_ts",
            }
        ],
        code_version="git:abcdef1234567890",
        code_content_hash="3" * 64,
        config_version="config_runtime_fixture_v1",
        config_hash="4" * 64,
    )
