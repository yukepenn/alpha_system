from __future__ import annotations

import json
from pathlib import Path

from alpha_system.research.feature_label_diagnostics import (
    DiagnosticStatus,
    build_feature_label_diagnostics,
)


def test_diagnostics_unify_alignment_overlap_and_missingness_descriptively() -> None:
    report = build_feature_label_diagnostics(
        feature_quality_reports=[
            _feature_quality_report(
                missing_bbo_count=2,
                bbo_quarantined_count=1,
                synthetic_no_trade_count=3,
            )
        ],
        feature_coverage_reports=[_feature_coverage_report()],
        label_audit_reports=[_label_audit_report()],
    )

    assert report.status is DiagnosticStatus.CLEAR
    assert report.availability_alignment.shared_dataset_versions == ("dsv_fixture_v1",)
    assert report.availability_alignment.shared_partitions == ("development_partition",)
    assert report.coverage_overlap.dimension("symbol").shared_values == ("ES",)
    assert report.coverage_overlap.dimension("session").shared_values == ("RTH",)
    assert report.coverage_overlap.dimension("partition").shared_values == (
        "development_partition",
    )
    assert report.missingness_exposure.missing_bbo_count == 2
    assert report.missingness_exposure.bbo_quarantined_count == 1
    assert report.missingness_exposure.synthetic_no_trade_count == 3
    assert report.blocking == ()
    assert {
        "BBO_MISSINGNESS_EXPOSURE_RECORDED",
        "SYNTHETIC_NO_TRADE_EXPOSURE_RECORDED",
    }.issubset(_codes(report.non_blocking))

    rendered = json.dumps(report.to_dict(), sort_keys=True).lower()
    for prohibited in (
        "alpha",
        "predictive",
        "profitability",
        "tradability",
        "tradable",
        "production",
    ):
        assert prohibited not in rendered


def test_label_as_feature_audit_blocks_without_rechecking_governance() -> None:
    report = build_feature_label_diagnostics(
        feature_quality_reports=[_feature_quality_report()],
        feature_coverage_reports=[_feature_coverage_report()],
        label_audit_reports=[
            _label_audit_report(
                blocked=True,
                findings=[
                    {
                        "check": "label_identity_as_feature",
                        "severity": "BLOCKING",
                        "message": "fixture label identity appeared in feature references",
                    }
                ],
            )
        ],
    )

    assert report.blocked is True
    assert "LABEL_REACHABLE_AS_FEATURE_INPUT_REPORTED" in _codes(report.blocking)
    assert report.availability_alignment.label_as_feature_finding_count == 1


def test_missing_label_symbol_and_session_coverage_is_reported_not_derived() -> None:
    label_audit = _label_audit_report()
    label_audit.pop("coverage")

    report = build_feature_label_diagnostics(
        feature_quality_reports=[_feature_quality_report()],
        feature_coverage_reports=[_feature_coverage_report()],
        label_audit_reports=[label_audit],
    )

    assert report.blocked is True
    assert {
        "LABEL_SYMBOL_COVERAGE_UNREPORTED",
        "LABEL_SESSION_COVERAGE_UNREPORTED",
    }.issubset(_codes(report.coverage_overlap.blocking))
    assert report.coverage_overlap.dimension("partition").shared_values == (
        "development_partition",
    )


def test_module_is_additive_and_does_not_touch_shared_diagnostics_or_governance() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    module_source = (
        repo_root / "src/alpha_system/research/feature_label_diagnostics.py"
    ).read_text(encoding="utf-8")
    shared_diagnostics_source = (
        repo_root / "src/alpha_system/research/diagnostics.py"
    ).read_text(encoding="utf-8")

    assert "feature_label_diagnostics" not in shared_diagnostics_source
    assert "alpha_system.research.diagnostics" not in module_source
    assert "alpha_system.governance" not in module_source
    assert "check_label_leakage" not in module_source
    for forbidden_suffix in (".dbn", ".zst", ".parquet", ".arrow", ".feather"):
        assert forbidden_suffix not in module_source


def _feature_quality_report(
    *,
    missing_bbo_count: int = 0,
    bbo_quarantined_count: int = 0,
    synthetic_no_trade_count: int = 0,
) -> dict[str, object]:
    return {
        "report_type": "FeatureQualityReport",
        "feature_id": "fixture_close_state",
        "feature_version_id": "fver_fixture_close_state",
        "feature_request_id": "freq_fixture_close_state",
        "dataset_version_id": "dsv_fixture_v1",
        "partition_id": "development_partition",
        "materialization_output_path": "/tmp/local-only-values.jsonl",
        "metrics": {
            "record_count": 4,
            "valid_value_record_count": 4,
            "nan_record_count": 0,
            "nan_rate": 0.0,
            "constant_feature": False,
            "distinct_observed_values": 4,
            "missing_bbo_count": missing_bbo_count,
            "bbo_quarantined_count": bbo_quarantined_count,
            "available_ts_missing_count": 0,
            "available_ts_invalid_count": 0,
            "available_ts_before_event_count": 0,
            "synthetic_no_trade_count": synthetic_no_trade_count,
        },
        "blocking": [],
        "non_blocking": [],
    }


def _feature_coverage_report() -> dict[str, object]:
    return {
        "report_type": "FeatureCoverageReport",
        "feature_id": "fixture_close_state",
        "feature_version_id": "fver_fixture_close_state",
        "feature_request_id": "freq_fixture_close_state",
        "dataset_version_id": "dsv_fixture_v1",
        "partition_id": "development_partition",
        "partition_role": "development",
        "materialization_output_path": "/tmp/local-only-values.jsonl",
        "record_count": 4,
        "symbol_coverage": [{"key": "ES", "count": 2}, {"key": "NQ", "count": 2}],
        "session_coverage": [{"key": "RTH", "count": 4}],
        "partition_coverage": [{"key": "development_partition", "count": 4}],
        "blocking": [],
        "non_blocking": [],
    }


def _label_audit_report(
    *,
    blocked: bool = False,
    findings: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    active_findings = findings or []
    return {
        "report_type": "LabelLeakageAuditReport",
        "label_version_id": "lver_fixture_forward_return",
        "label_id": "fixture_forward_return",
        "label_spec_id": "lspec_fixture_forward_return",
        "dataset_version_id": "dsv_fixture_v1",
        "partition_id": "development_partition",
        "lifecycle_state": "REGISTERED",
        "availability_time": "2024-01-02T14:32:00+00:00",
        "status": "BLOCKED" if blocked else "CLEAN",
        "blocked": blocked,
        "clean": not blocked,
        "value_records_checked": 4,
        "blocking_finding_count": len(active_findings) if blocked else 0,
        "non_blocking_finding_count": 0,
        "findings": active_findings,
        "coverage": {
            "symbol_coverage": [{"key": "ES", "count": 4}],
            "session_coverage": [{"key": "RTH", "count": 4}],
            "partition_coverage": [{"key": "development_partition", "count": 4}],
        },
    }


def _codes(findings: object) -> set[str]:
    return {finding.code for finding in findings}
