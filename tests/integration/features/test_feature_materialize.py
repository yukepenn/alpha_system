from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetVersion,
    ReportStatus,
    compute_quality_report_hash,
)
from alpha_system.features import consumption
from alpha_system.features.contracts import FeatureSetSpec
from alpha_system.features.engine import (
    FeatureMaterializationInputs,
    build_feature_materialization_plan,
    materialize_features,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
)
from alpha_system.governance.duplicate_exposure import ExposureCheckResult, ExposureRegistryStatus
from alpha_system.governance.feature_request import (
    FeatureRequestApprovalStatus,
    create_feature_request,
)

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_materialize_feature_set_writes_idempotent_local_jsonl(tmp_path: Path) -> None:
    dataset_id = "dsv_synthetic_engine_integration_v1"
    accepted = _accepted_version(dataset_id)
    definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.RETURNS,
        _approved_request(),
        EmptyRegistryReader(),
        dataset_version_ids=(dataset_id,),
        reset_on_session=False,
    )
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_engine_integration_fixture",
        feature_set_version="v1",
        features=(definition.spec,),
    )
    plan = build_feature_materialization_plan(
        feature_set,
        accepted,
        partition_id="development_partition",
        alpha_data_root=tmp_path,
    )
    inputs = FeatureMaterializationInputs(
        accepted_version=accepted,
        bar_rows=_bar_rows(dataset_id),
    )

    first = materialize_features(plan, inputs, (definition,))
    first_payload = plan.output_path.read_text(encoding="utf-8")
    second = materialize_features(plan, inputs, (definition,))

    assert first.dry_run is False
    assert first.wrote_output is True
    assert second.wrote_output is False
    assert first.records == second.records
    assert first.record_count == 3
    assert plan.output_path.is_relative_to(tmp_path)
    assert plan.output_path.read_text(encoding="utf-8") == first_payload

    lines = [json.loads(line) for line in first_payload.splitlines()]
    assert lines[0]["record_type"] == "feature_materialization_plan"
    assert lines[0]["plan"]["dataset_version_id"] == dataset_id
    value_lines = lines[1:]
    assert len(value_lines) == first.record_count
    assert all(line["record_type"] == "feature_value" for line in value_lines)
    assert all(line["value"]["available_ts"] for line in value_lines)
    assert all(
        line["value"]["feature_version_id"] == definition.feature_version_id for line in value_lines
    )


def _approved_request():
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=["engine_returns"],
        formula_sketch={
            "exposure_family": "engine_returns",
            "inputs": ["canonical_ohlcv"],
            "operation": "returns",
            "window": 1,
        },
        availability_assumptions={
            "timing": "synthetic OHLCV fixture rows expose available_ts after bar end"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["close", "available_ts"],
            "source": "tiny synthetic canonical OHLCV fixture only",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _accepted_version(dataset_id: str) -> consumption.AcceptedDatasetVersion:
    quality_report = _quality_report(dataset_id)
    return consumption.AcceptedDatasetVersion(
        registry_path="synthetic_registry.sqlite",
        dataset_version=_dataset_version(dataset_id, quality_report=quality_report),
        lifecycle_state="VERSIONED",
        quality_report=quality_report,
        coverage_report=_coverage_report(dataset_id),
    )


def _dataset_version(dataset_id: str, *, quality_report: DataQualityReport) -> DatasetVersion:
    return DatasetVersion(
        dataset_version_id=dataset_id,
        source="dsrc_synthetic_fixture",
        symbol_universe=("ES",),
        bar_size="1 min",
        what_to_show="TRADES",
        start_ts=_dt("2024-01-02T14:30:00+00:00"),
        end_ts=_dt("2024-01-02T14:33:00+00:00"),
        contract_universe=("ESM4",),
        roll_policy_id="roll_policy_fixture",
        manifest_hash=HASH_0,
        code_hash=HASH_1,
        config_hash=HASH_2,
        quality_report_hash=compute_quality_report_hash(quality_report),
        created_at=_dt("2024-01-02T15:00:00+00:00"),
    )


def _quality_report(dataset_id: str) -> DataQualityReport:
    return DataQualityReport(
        quality_report_id=f"qr_{dataset_id}",
        dataset_version_id=dataset_id,
        gap_summary=_passing_summary(),
        duplicate_summary=_passing_summary(),
        non_monotonic_summary=_passing_summary(),
        ohlc_errors=_passing_summary(),
        zero_negative_price_errors=_passing_summary(),
        zero_volume_anomalies=_passing_summary(),
        dst_anomalies=_passing_summary(),
        session_coverage=_passing_summary(),
        roll_discontinuities=_passing_summary(),
        provider_error_summary=_passing_summary(),
        bbo_missing_metric=_passing_summary(),
        abnormal_spread_summary=_passing_summary(),
        status=ReportStatus.PASSING,
    )


def _coverage_report(dataset_id: str) -> CoverageReport:
    return CoverageReport(
        coverage_report_id=f"cr_{dataset_id}",
        dataset_version_id=dataset_id,
        symbol_coverage=_coverage_summary(),
        contract_coverage=_coverage_summary(),
        session_coverage=_coverage_summary(),
        partition_coverage=_coverage_summary(include_partition_counts=True),
        missing_intervals=(),
        incomplete_chunks=(),
    )


def _passing_summary() -> dict[str, object]:
    return {"count": 0, "status": ReportStatus.PASSING.value, "blocking": False}


def _coverage_summary(*, include_partition_counts: bool = False) -> dict[str, object]:
    summary: dict[str, object] = {
        "status": ReportStatus.PASSING.value,
        "blocking": False,
        "expected_count": 1,
        "observed_count": 1,
        "missing_count": 0,
    }
    if include_partition_counts:
        summary["missing_interval_count"] = 0
        summary["incomplete_chunk_count"] = 0
    return summary


def _bar_rows(dataset_id: str) -> tuple[dict[str, object], ...]:
    start = _dt("2024-01-02T14:30:00+00:00")
    return tuple(
        _bar_row(dataset_id, start + timedelta(minutes=index), close=close)
        for index, close in enumerate(("100.00", "101.00", "102.00"))
    )


def _bar_row(dataset_id: str, start: datetime, *, close: str) -> dict[str, object]:
    end = start + timedelta(minutes=1)
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_CONTINUOUS",
        "bar_start_ts": start.isoformat(),
        "bar_end_ts": end.isoformat(),
        "event_ts": end.isoformat(),
        "available_ts": (end + timedelta(seconds=1)).isoformat(),
        "ingested_at": (end + timedelta(seconds=2)).isoformat(),
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": "10",
        "source": "dsrc_synthetic_fixture",
        "source_request_id": "req_fixture_1",
        "data_version": dataset_id,
        "quality_flags": (),
        "session_label": "RTH",
    }


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
