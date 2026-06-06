from __future__ import annotations

from datetime import UTC, datetime, timedelta

from alpha_system.runtime.contracts.run_record import StudyRunResultState
from alpha_system.runtime.diagnostics.contracts import (
    DiagnosticsFamily,
    DiagnosticsRunSpec,
    RuntimePlanRef,
)
from alpha_system.runtime.diagnostics.label.runtime import (
    LabelDiagnosticsReport,
    build_label_diagnostics_report,
)
from alpha_system.runtime.input_resolver import LabelPackHandle, RuntimeInputPack

ALPHA_SPEC_REF = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_REF = "sspec_438ceffd40855205de5497f0"
LABEL_SPEC_REF = "lspec_8663589ca7a9f1e5859289c7"
LABEL_VERSION_ID = "lver_" + "b" * 64
DATASET_VERSION_ID = "dsv_synthetic_label_diagnostics_fixture_v1"
BASE_TS = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)


def test_builds_descriptive_label_diagnostics_report() -> None:
    report = _report()

    assert isinstance(report, LabelDiagnosticsReport)
    assert report.status is StudyRunResultState.DIAGNOSTICS_COMPLETE
    assert report.diagnostics_report.diagnostics_family is DiagnosticsFamily.LABEL
    assert report.diagnostics_run_record.report_ref == report.diagnostics_report.to_ref()
    assert report.rejection_reasons == ()

    payload = report.to_dict()
    assert payload["descriptive_only"] is True
    assert payload["non_promotional"] is True
    assert payload["raw_or_heavy_data_embedded"] is False
    assert payload["diagnostic_pass_is_alpha_validation"] is False
    assert payload["label_distribution_summary"]["observed_outcome_count"] == 4
    assert payload["label_class_balance"]["class_count"] == 2
    assert payload["label_horizon_coverage"]["horizon_count"] == 1
    assert payload["label_mfe_mae_summary"]["mfe_sample_count"] == 4
    assert payload["label_mfe_mae_summary"]["mae_sample_count"] == 4
    assert payload["label_path_ambiguity_summary"]["ambiguous_path_count"] == 1
    assert payload["label_available_ts_validity"]["label_available_ts_valid"] is True
    assert payload["label_cost_adjustment_sanity"]["cost_model_declared_count"] >= 1
    assert payload["diagnostics_run_record"]["status"] == "DIAGNOSTICS_COMPLETE"

    rendered = str(payload).lower()
    assert "label_value" not in rendered
    for prohibited in (
        "alpha validated",
        "validated alpha",
        "factor promoted",
        "tradable",
        "profitable",
        "production ready",
    ):
        assert prohibited not in rendered


def test_label_available_ts_failure_is_visible_rejection() -> None:
    observations = list(_label_observations())
    observations[0] = {
        **observations[0],
        "label_available_ts": (BASE_TS + timedelta(seconds=30)).isoformat(),
    }

    report = _report(label_observations=observations)

    assert report.status is StudyRunResultState.REJECTED
    assert _reason_codes(report) == {"leakage_risk"}
    assert report.diagnostics_run_record.to_dict()["status"] == "REJECTED"
    assert report.to_dict()["rejection_reason_records"][0]["code"] == "leakage_risk"


def test_label_as_live_feature_reference_is_hard_failure() -> None:
    report = _report(live_feature_references={"features": [LABEL_VERSION_ID]})

    assert report.status is StudyRunResultState.REJECTED
    assert "leakage_risk" in _reason_codes(report)
    assert report.label_available_ts_validity["label_as_feature_reference_detected"] is True


def test_low_sample_remains_visible_as_inconclusive() -> None:
    report = _report(label_observations=(), label_profiles=_label_profiles())

    assert report.status is StudyRunResultState.INCONCLUSIVE
    assert {"low_sample", "inconclusive"}.issubset(_reason_codes(report))
    assert report.diagnostics_run_record.to_dict()["status"] == "INCONCLUSIVE"
    assert report.to_dict()["label_distribution_summary"]["sample_count"] == 0


def test_missing_cost_metadata_fails_closed_without_claims() -> None:
    observations = [
        {
            key: value
            for key, value in row.items()
            if key not in {"cost_model_ref", "cost_adjusted"}
        }
        for row in _label_observations()
    ]

    report = _report(label_observations=observations, label_profiles=())

    assert report.status is StudyRunResultState.DIAGNOSTICS_FAILED
    assert "weak_diagnostics" in _reason_codes(report)
    assert report.cost_adjustment_sanity["cost_adjustment_sanity"] == "missing"


def _report(**overrides: object) -> LabelDiagnosticsReport:
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
        spec_metadata={"requested_by": "rt_p08_label_diagnostics_test"},
    )


def _runtime_input_pack() -> RuntimeInputPack:
    return RuntimeInputPack(
        alpha_spec_ref=ALPHA_SPEC_REF,
        study_spec_ref=STUDY_SPEC_REF,
        study_input_pack={
            "alpha_spec_id": ALPHA_SPEC_REF,
            "feature_request_ids": ["freq_eb180e1226ce34c048c7e6eb"],
            "label_spec_ids": [LABEL_SPEC_REF],
            "dataset_scope": {"fixture": "tiny synthetic diagnostics metadata"},
        },
        dataset_version_id=DATASET_VERSION_ID,
        dataset_lifecycle_state="VERSIONED",
        dataset_source="databento",
        dataset_reproducibility_hashes={"manifest_hash": "0" * 64},
        canonical_input_views=(),
        feature_packs=(),
        label_packs=[
            LabelPackHandle(
                label_version_id=LABEL_VERSION_ID,
                label_spec_id=LABEL_SPEC_REF,
                label_id="fixed_horizon_forward_return_1m",
                dataset_version_id=DATASET_VERSION_ID,
                partition_id="development_partition",
                materialization_plan_id="label_plan_synthetic",
                first_event_ts=BASE_TS.isoformat(),
                last_event_ts=(BASE_TS + timedelta(minutes=3)).isoformat(),
                first_label_available_ts=(BASE_TS + timedelta(minutes=1, seconds=1)).isoformat(),
                last_label_available_ts=(BASE_TS + timedelta(minutes=4, seconds=1)).isoformat(),
                lifecycle_state="READY_FOR_STUDY",
            )
        ],
        dataset_scope={"fixture": "tiny synthetic diagnostics metadata"},
        partition_scope={"partition_id": "development_partition"},
        session_scope={"session": "RTH"},
        governance_metadata={"contamination_review_id": "synthetic_review_001"},
    )


def _label_observations() -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    outcomes = (0.02, -0.01, 0.03, -0.02)
    for index, outcome in enumerate(outcomes):
        event_ts = BASE_TS + timedelta(minutes=index)
        horizon_end_ts = event_ts + timedelta(minutes=1)
        rows.append(
            {
                "label_outcome": outcome,
                "event_ts": event_ts.isoformat(),
                "horizon_end_ts": horizon_end_ts.isoformat(),
                "label_available_ts": (horizon_end_ts + timedelta(seconds=1)).isoformat(),
                "horizon_seconds": 60,
                "event_trigger": True,
                "mfe": abs(outcome) + 0.01,
                "mae": -abs(outcome),
                "target_before_stop": index % 2 == 0,
                "path_ambiguity": index == 3,
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
            "record_count": 4,
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
        "symbol_coverage": [{"key": "ES", "count": 4}],
        "session_coverage": [{"key": "RTH", "count": 4}],
        "partition_coverage": [{"key": "development_partition", "count": 4}],
        "blocking": [],
        "non_blocking": [],
    }


def _label_audit_report() -> dict[str, object]:
    return {
        "report_type": "LabelLeakageAuditReport",
        "label_version_id": LABEL_VERSION_ID,
        "label_id": "fixed_horizon_forward_return_1m",
        "label_spec_id": LABEL_SPEC_REF,
        "dataset_version_id": DATASET_VERSION_ID,
        "partition_id": "development_partition",
        "lifecycle_state": "READY_FOR_STUDY",
        "availability_time": BASE_TS.isoformat(),
        "status": "CLEAN",
        "blocked": False,
        "clean": True,
        "value_records_checked": 4,
        "blocking_finding_count": 0,
        "non_blocking_finding_count": 0,
        "findings": [],
        "coverage": {
            "symbol_coverage": [{"key": "ES", "count": 4}],
            "session_coverage": [{"key": "RTH", "count": 4}],
            "partition_coverage": [{"key": "development_partition", "count": 4}],
        },
    }


def _reason_codes(report: LabelDiagnosticsReport) -> set[str]:
    return {reason.code for reason in report.rejection_reasons}
