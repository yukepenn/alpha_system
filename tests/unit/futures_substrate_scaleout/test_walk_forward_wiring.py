from __future__ import annotations

import pytest

from alpha_system.runtime.contracts.run_record import StudyRunResultState
from alpha_system.runtime.diagnostics.contracts import (
    DiagnosticsHalfLifeProtocol,
    DiagnosticsRunSpecRef,
)
from alpha_system.runtime.diagnostics.factor import (
    FactorDiagnosticsThresholds,
    build_factor_diagnostics_run,
)
from alpha_system.runtime.diagnostics.splits import (
    WalkForwardSplitConfig,
    WalkForwardSplitError,
    build_walk_forward_split_plan,
)


def test_walk_forward_split_plan_exposes_canonical_split_windows() -> None:
    config = WalkForwardSplitConfig(
        half_life_protocol=DiagnosticsHalfLifeProtocol.FAST,
        train_window=5,
        validation_window=2,
        step_size=2,
        purge_gap=1,
        embargo_gap=1,
        min_fold_count=2,
    )

    plan = build_walk_forward_split_plan(12, config=config)

    assert plan.fold_count == 3
    assert plan.scalar_summary() == {
        "walk_forward_enabled": True,
        "walk_forward_fold_count": 3,
        "walk_forward_sample_count": 12,
        "walk_forward_half_life_protocol": "FAST",
        "walk_forward_train_window": 5,
        "walk_forward_validation_window": 2,
        "walk_forward_step_size": 2,
        "walk_forward_purge_gap": 1,
        "walk_forward_embargo_gap": 1,
        "walk_forward_min_fold_count": 2,
    }
    payload = plan.to_dict()
    assert payload["config"]["half_life_protocol"] == "FAST"
    assert payload["folds"][0] == {
        "split_id": "walk_forward_0",
        "train_indices": [0, 1, 2, 3],
        "validation_indices": [5, 6],
        "purge_gap": 1,
        "embargo_gap": 1,
    }
    assert payload["folds"][1]["train_indices"] == [2, 3, 4, 5]
    assert payload["folds"][1]["validation_indices"] == [7, 8]


def test_walk_forward_split_plan_fails_closed_without_unsplit_fallback() -> None:
    config = WalkForwardSplitConfig(
        half_life_protocol="FAST",
        train_window=5,
        validation_window=2,
        step_size=2,
        purge_gap=0,
        embargo_gap=0,
        min_fold_count=1,
    )

    with pytest.raises(WalkForwardSplitError, match="failed closed"):
        build_walk_forward_split_plan(6, config=config)


def test_factor_diagnostics_opt_in_walk_forward_metadata() -> None:
    result = build_factor_diagnostics_run(
        diagnostics_run_spec=_spec_ref(),
        observations=_rows(12),
        lineage_refs=_lineage_refs(),
        thresholds=FactorDiagnosticsThresholds(
            min_observations=4,
            max_outlier_rate=1.0,
            bucket_count=2,
            min_populated_buckets=2,
        ),
        walk_forward_config={
            "half_life_protocol": "FAST",
            "train_window": 5,
            "validation_window": 2,
            "step_size": 2,
            "purge_gap": 1,
            "embargo_gap": 1,
            "min_fold_count": 2,
        },
    )

    assert result.report.status is StudyRunResultState.DIAGNOSTICS_COMPLETE
    assert result.record.status is StudyRunResultState.DIAGNOSTICS_COMPLETE
    assert result.report.coverage_summary["walk_forward_fold_count"] == 3
    assert result.report.quality_summary["walk_forward_status"] == "reported"
    gate_ids = {gate.gate_id for gate in result.report.report.quality_gates}
    assert "factor_walk_forward_gate" in gate_ids

    payload = result.report.to_dict()
    assert payload["walk_forward_metadata"]["fold_count"] == 3
    assert payload["walk_forward_metadata"]["folds"][0]["validation_indices"] == [5, 6]
    assert "alpha validated" not in str(payload).lower()


def test_factor_diagnostics_requested_walk_forward_reports_inconclusive_when_too_small() -> None:
    result = build_factor_diagnostics_run(
        diagnostics_run_spec=_spec_ref(),
        observations=_rows(3),
        lineage_refs=_lineage_refs(),
        thresholds=FactorDiagnosticsThresholds(
            min_observations=1,
            min_coverage_ratio=0.0,
            max_missingness_rate=1.0,
            max_outlier_rate=1.0,
            bucket_count=2,
            min_populated_buckets=1,
        ),
        walk_forward_config={
            "half_life_protocol": "FAST",
            "train_window": 5,
            "validation_window": 2,
            "step_size": 2,
            "purge_gap": 1,
            "embargo_gap": 1,
            "min_fold_count": 1,
        },
    )

    assert result.report.status is StudyRunResultState.INCONCLUSIVE
    assert "walk_forward_split_unavailable" in {
        reason.code for reason in result.report.rejection_reasons
    }
    assert result.record.status is StudyRunResultState.INCONCLUSIVE
    assert "walk_forward_metadata" not in result.report.to_dict()


def _rows(count: int) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "factor_value": float(index + 1),
            "label_value": float(index + 1) / 100.0,
            "available_ts": "2026-01-02T14:30:05Z",
            "label_available_ts": "2026-01-02T14:31:00Z",
            "horizon_seconds": 60 if index % 2 == 0 else 120,
        }
        for index in range(count)
    )


def _spec_ref() -> DiagnosticsRunSpecRef:
    return DiagnosticsRunSpecRef(
        diagnostics_run_spec_id="dspec_" + "1" * 24,
        content_hash="2" * 64,
    )


def _lineage_refs() -> dict[str, str]:
    return {
        "study_run_spec_id": "srun_" + "3" * 24,
        "runtime_plan_id": "rplan_" + "4" * 24,
        "dataset_version_id": "dsv_synthetic_factor_fixture_v1",
        "feature_pack_ref": "feature_pack_synthetic_v1",
        "label_pack_ref": "label_pack_synthetic_v1",
    }
