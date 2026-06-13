from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from alpha_system.runtime.contracts.run_record import StudyRunResultState
from alpha_system.runtime.diagnostics.contracts import (
    DiagnosticsFamily,
    DiagnosticsHalfLifeProtocol,
    DiagnosticsRunSpec,
    RuntimePlanRef,
)
from alpha_system.runtime.diagnostics.label.runtime import build_label_diagnostics_report
from alpha_system.runtime.diagnostics.splits import (
    ROWS_NOT_INDEPENDENT_MARKER,
    NEffSampleReportingError,
    WalkForwardSplitConfig,
    attach_n_eff_to_walk_forward_metadata,
    build_n_eff_sample_report,
    build_session_day_aggregation,
    build_walk_forward_split_plan,
    estimate_n_eff,
)
from alpha_system.runtime.input_resolver import LabelPackHandle, RuntimeInputPack

ALPHA_SPEC_REF = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_REF = "sspec_438ceffd40855205de5497f0"
LABEL_SPEC_REF = "lspec_8663589ca7a9f1e5859289c7"
LABEL_VERSION_ID = "lver_" + "b" * 64
DATASET_VERSION_ID = "dsv_synthetic_n_eff_fixture_v1"
BASE_TS = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)


def test_n_eff_equals_rows_for_non_overlapping_and_discounts_overlap() -> None:
    non_overlapping = estimate_n_eff(
        120,
        {
            "horizon_minutes": 5,
            "sampling_cadence_minutes": 5,
            "discount_factor": 1,
            "metadata_source": "synthetic_non_overlap",
        },
    )
    overlapping = estimate_n_eff(
        120,
        {
            "horizon_minutes": 5,
            "sampling_cadence_minutes": 1,
            "discount_factor": 5,
            "metadata_source": "synthetic_overlap",
        },
    )

    assert non_overlapping.n_eff == non_overlapping.rows == 120
    assert non_overlapping.rows_after_purge_embargo == 120
    assert non_overlapping.purge_embargo_removed_rows == 0
    assert overlapping.n_eff == 24
    assert overlapping.n_eff < overlapping.rows


def test_purge_embargo_lowers_n_eff_before_overlap_discount() -> None:
    metadata = {
        "horizon_bars": 2,
        "sampling_cadence_bars": 1,
        "discount_factor": 2,
        "metadata_source": "synthetic_overlap",
    }

    base = estimate_n_eff(20, metadata)
    adjusted = estimate_n_eff(20, metadata, purge_gap=3, embargo_gap=2)

    assert base.n_eff == 10
    assert adjusted.rows == 20
    assert adjusted.rows_after_purge_embargo == 15
    assert adjusted.purge_embargo_removed_rows == 5
    assert adjusted.n_eff == 7
    assert adjusted.n_eff < base.n_eff
    assert adjusted.n_eff <= adjusted.rows


def test_extended_horizon_discount_is_stronger_than_primary_horizon() -> None:
    rows = 2400
    primary = estimate_n_eff(
        rows,
        {
            "horizon_minutes": 30,
            "sampling_cadence_minutes": 1,
            "discount_factor": 30,
        },
    )
    extended = estimate_n_eff(
        rows,
        {
            "horizon_minutes": 240,
            "sampling_cadence_minutes": 1,
            "discount_factor": 240,
        },
    )

    assert extended.n_eff < primary.n_eff
    assert extended.overlap_metadata.discount_factor > primary.overlap_metadata.discount_factor


def test_n_eff_never_exceeds_rows() -> None:
    for rows in (0, 1, 2, 17, 240):
        for factor in (1, 3, 60, 240):
            estimate = estimate_n_eff(
                rows,
                {
                    "horizon_bars": factor,
                    "sampling_cadence_bars": 1,
                    "discount_factor": factor,
                },
            )
            assert 0 <= estimate.n_eff <= estimate.rows


def test_missing_or_inconsistent_overlap_metadata_fails_closed() -> None:
    with pytest.raises(NEffSampleReportingError, match="required"):
        estimate_n_eff(10, None)

    with pytest.raises(NEffSampleReportingError, match="understates"):
        estimate_n_eff(
            10,
            {
                "horizon_minutes": 10,
                "sampling_cadence_minutes": 1,
                "discount_factor": 2,
            },
        )


def test_session_day_aggregation_hooks_count_units() -> None:
    aggregation = build_session_day_aggregation(_label_observations())

    assert aggregation.to_dict() == {
        "session_fields": "session_label,session,session_segment",
        "trade_date_fields": "trade_date,trade_date_id",
        "observation_count": 8,
        "session_unit_count": 2,
        "trade_date_unit_count": 2,
        "session_trade_date_unit_count": 4,
        "missing_session_count": 0,
        "missing_trade_date_count": 0,
    }


def test_per_fold_n_eff_attaches_to_p24_fold_metadata() -> None:
    plan = _walk_forward_plan()
    records = attach_n_eff_to_walk_forward_metadata(plan.to_dict(), _overlap_metadata(2))

    assert len(records) == 3
    assert records[0]["split_id"] == "walk_forward_0"
    assert records[0]["half_life_protocol"] == "FAST"
    assert records[0]["purge_gap"] == 1
    assert records[0]["embargo_gap"] == 1
    assert records[0]["train"]["rows"] == 4
    assert records[0]["train"]["rows_after_purge_embargo"] == 2
    assert records[0]["train"]["n_eff"] == 1
    assert records[0]["validation"]["rows"] == 2
    assert records[0]["validation"]["rows_after_purge_embargo"] == 0
    assert records[0]["validation"]["n_eff"] == 0


def test_label_report_carries_opt_in_n_eff_block_and_marker() -> None:
    report = _label_report(
        n_eff_overlap_metadata=_overlap_metadata(4),
        walk_forward_metadata=_walk_forward_plan().to_dict(),
    )

    assert report.status is StudyRunResultState.DIAGNOSTICS_COMPLETE
    payload = report.to_dict()
    block = payload["label_n_eff_report"]
    assert block["rows"] == 8
    assert block["n_eff"] == 2
    assert block["rows_after_purge_embargo"] == 8
    assert block["rows_are_not_independent_samples"] is ROWS_NOT_INDEPENDENT_MARKER
    assert block["overlap_metadata"]["discount_factor"] == 4
    assert block["session_day_aggregation"]["session_trade_date_unit_count"] == 4
    assert block["walk_forward_fold_n_eff"][0]["split_id"] == "walk_forward_0"
    assert payload["report_metadata"]["n_eff_reporting"] == "reported"


def test_label_report_fails_closed_when_n_eff_requested_without_metadata() -> None:
    report = _label_report(walk_forward_metadata=_walk_forward_plan().to_dict())

    assert report.status is StudyRunResultState.DIAGNOSTICS_FAILED
    assert "n_eff_overlap_metadata_unavailable" in {
        reason["code"] for reason in report.to_dict()["rejection_reason_records"]
    }
    assert "label_n_eff_report" not in report.to_dict()


def test_label_report_without_n_eff_request_is_unchanged() -> None:
    first = _label_report().to_dict()
    second = _label_report(n_eff_overlap_metadata=None, walk_forward_metadata=None).to_dict()

    assert first == second
    assert "label_n_eff_report" not in first
    assert "n_eff_reporting" not in first["report_metadata"]


def test_n_eff_report_is_deterministic() -> None:
    kwargs = {
        "rows": 8,
        "horizon_overlap_metadata": _overlap_metadata(4),
        "observations": _label_observations(),
        "walk_forward_metadata": _walk_forward_plan().to_dict(),
    }

    assert build_n_eff_sample_report(**kwargs) == build_n_eff_sample_report(**kwargs)


def _overlap_metadata(discount_factor: int) -> dict[str, object]:
    return {
        "horizon_bars": discount_factor,
        "sampling_cadence_bars": 1,
        "discount_factor": discount_factor,
        "metadata_source": "synthetic_fixture",
    }


def _walk_forward_plan():
    return build_walk_forward_split_plan(
        12,
        config=WalkForwardSplitConfig(
            half_life_protocol=DiagnosticsHalfLifeProtocol.FAST,
            train_window=5,
            validation_window=2,
            step_size=2,
            purge_gap=1,
            embargo_gap=1,
            min_fold_count=2,
        ),
    )


def _label_report(**overrides: object):
    values: dict[str, object] = {
        "diagnostics_run_spec": _diagnostics_spec(),
        "runtime_input_pack": _runtime_input_pack(),
        "feature_quality_reports": [_feature_quality_report()],
        "feature_coverage_reports": [_feature_coverage_report()],
        "label_audit_reports": [_label_audit_report()],
        "label_observations": _label_observations(),
        "label_profiles": _label_profiles(),
    }
    values.update(overrides)
    return build_label_diagnostics_report(**values)  # type: ignore[arg-type]


def _diagnostics_spec() -> DiagnosticsRunSpec:
    return DiagnosticsRunSpec(
        diagnostics_family=DiagnosticsFamily.LABEL,
        study_run_spec={
            "study_run_spec_id": "srun_" + "1" * 24,
            "content_hash": "2" * 64,
        },
        runtime_plan=RuntimePlanRef(plan_id="rplan_" + "3" * 24, content_hash="4" * 64),
        spec_metadata={"requested_by": "futsub_p25_n_eff_reporting_test"},
    )


def _runtime_input_pack() -> RuntimeInputPack:
    return RuntimeInputPack(
        alpha_spec_ref=ALPHA_SPEC_REF,
        study_spec_ref=STUDY_SPEC_REF,
        study_input_pack={
            "alpha_spec_id": ALPHA_SPEC_REF,
            "feature_request_ids": ["freq_eb180e1226ce34c048c7e6eb"],
            "label_spec_ids": [LABEL_SPEC_REF],
            "dataset_scope": {"fixture": "tiny synthetic n_eff diagnostics metadata"},
        },
        dataset_version_id=DATASET_VERSION_ID,
        dataset_lifecycle_state="VERSIONED",
        dataset_source="synthetic",
        dataset_reproducibility_hashes={"manifest_hash": "0" * 64},
        canonical_input_views=(),
        feature_packs=(),
        label_packs=[
            LabelPackHandle(
                label_version_id=LABEL_VERSION_ID,
                label_spec_id=LABEL_SPEC_REF,
                label_id="fixed_horizon_forward_return_4m",
                dataset_version_id=DATASET_VERSION_ID,
                partition_id="development_partition",
                materialization_plan_id="label_plan_synthetic_n_eff",
                first_event_ts=BASE_TS.isoformat(),
                last_event_ts=(BASE_TS + timedelta(minutes=7)).isoformat(),
                first_label_available_ts=(BASE_TS + timedelta(minutes=4, seconds=1)).isoformat(),
                last_label_available_ts=(BASE_TS + timedelta(minutes=11, seconds=1)).isoformat(),
                lifecycle_state="READY_FOR_STUDY",
            )
        ],
        dataset_scope={"fixture": "tiny synthetic n_eff diagnostics metadata"},
        partition_scope={"partition_id": "development_partition"},
        session_scope={"session": "RTH"},
        governance_metadata={"contamination_review_id": "synthetic_review_001"},
    )


def _label_observations() -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    outcomes = (0.02, -0.01, 0.03, -0.02, 0.01, -0.03, 0.04, -0.04)
    for index, outcome in enumerate(outcomes):
        event_ts = BASE_TS + timedelta(minutes=index)
        horizon_end_ts = event_ts + timedelta(minutes=4)
        rows.append(
            {
                "label_outcome": outcome,
                "event_ts": event_ts.isoformat(),
                "horizon_end_ts": horizon_end_ts.isoformat(),
                "label_available_ts": (horizon_end_ts + timedelta(seconds=1)).isoformat(),
                "horizon_seconds": 240,
                "session_label": "RTH" if index % 2 == 0 else "ETH",
                "trade_date": "2026-01-02" if index < 4 else "2026-01-05",
                "event_trigger": True,
                "mfe": abs(outcome) + 0.01,
                "mae": -abs(outcome),
                "target_before_stop": index % 2 == 0,
                "path_ambiguity": index == 7,
                "cost_model_ref": "spread_plus_bps_fixture",
                "cost_adjusted": True,
            }
        )
    return tuple(rows)


def _label_profiles() -> tuple[dict[str, object], ...]:
    return (
        {
            "label_version_id": LABEL_VERSION_ID,
            "cost_model_ref": "spread_plus_bps_fixture",
            "cost_adjustment_ref": "fixture_cost_adjustment_v1",
            "cost_adjusted": True,
        },
    )


def _feature_quality_report() -> dict[str, object]:
    return {
        "report_type": "FeatureQualityReport",
        "feature_id": "fixture_close_state",
        "feature_version_id": "fver_fixture_close_state",
        "dataset_version_id": DATASET_VERSION_ID,
        "partition_id": "development_partition",
        "metrics": {
            "record_count": 8,
            "missing_bbo_count": 1,
            "bbo_quarantined_count": 0,
            "available_ts_missing_count": 0,
            "available_ts_invalid_count": 0,
            "available_ts_before_event_count": 0,
            "synthetic_no_trade_count": 1,
        },
        "blocking": [],
        "non_blocking": [],
    }


def _feature_coverage_report() -> dict[str, object]:
    return {
        "report_type": "FeatureCoverageReport",
        "feature_id": "fixture_close_state",
        "feature_version_id": "fver_fixture_close_state",
        "dataset_version_id": DATASET_VERSION_ID,
        "partition_id": "development_partition",
        "symbol_coverage": [{"key": "ES", "count": 8}],
        "session_coverage": [{"key": "RTH", "count": 4}, {"key": "ETH", "count": 4}],
        "partition_coverage": [{"key": "development_partition", "count": 8}],
        "blocking": [],
        "non_blocking": [],
    }


def _label_audit_report() -> dict[str, object]:
    return {
        "report_type": "LabelLeakageAuditReport",
        "label_version_id": LABEL_VERSION_ID,
        "label_id": "fixed_horizon_forward_return_4m",
        "label_spec_id": LABEL_SPEC_REF,
        "dataset_version_id": DATASET_VERSION_ID,
        "partition_id": "development_partition",
        "lifecycle_state": "READY_FOR_STUDY",
        "availability_time": BASE_TS.isoformat(),
        "status": "CLEAN",
        "blocked": False,
        "clean": True,
        "value_records_checked": 8,
        "blocking_finding_count": 0,
        "non_blocking_finding_count": 0,
        "findings": [],
        "coverage": {
            "symbol_coverage": [{"key": "ES", "count": 8}],
            "session_coverage": [{"key": "RTH", "count": 4}, {"key": "ETH", "count": 4}],
            "partition_coverage": [{"key": "development_partition", "count": 8}],
        },
    }
