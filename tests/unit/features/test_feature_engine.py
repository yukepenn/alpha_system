from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetPartitionPlan,
    DatasetVersion,
    ReportStatus,
    compute_quality_report_hash,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.features import consumption
from alpha_system.features.contracts import (
    FeatureFamily,
    FeatureInputSpec,
    FeatureSetSpec,
    FeatureSpec,
    NormalizationSpec,
    TransformSpec,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.engine import (
    FeatureMaterializationError,
    FeatureMaterializationInputs,
    build_feature_materialization_plan,
    materialize_features,
    resolve_feature_materialization_dataset,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
)
from alpha_system.governance.duplicate_exposure import ExposureCheckResult, ExposureRegistryStatus
from alpha_system.governance.feature_request import (
    FeatureRequest,
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


def test_dry_run_validates_plan_without_writing(tmp_path: Path) -> None:
    accepted = _accepted_version("dsv_synthetic_engine_ohlcv_v1")
    definition = _returns_definition(accepted.dataset_version_id)
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_engine_fixture",
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
        bar_rows=_bar_rows(accepted.dataset_version_id),
    )

    result = materialize_features(plan, inputs, (definition,), dry_run=True)

    assert result.dry_run is True
    assert result.record_count == 0
    assert result.output_path is None
    assert not plan.output_path.exists()
    assert plan.output_path.is_relative_to(tmp_path)
    assert plan.plan_id == f"fmat_{plan.idempotency_key}"


def test_plan_refuses_feature_spec_without_approved_request_gate(tmp_path: Path) -> None:
    accepted = _accepted_version("dsv_synthetic_engine_ohlcv_v1")
    unapproved_spec = FeatureSpec(
        feature_id="feat_unapproved_returns",
        family=FeatureFamily.BASE_OHLCV,
        feature_request_id=_approved_request(OHLCVFeatureName.RETURNS).feature_request_id,
        inputs=FeatureInputSpec(
            input_views=("canonical_ohlcv",),
            fields=("close",),
            dataset_version_ids=(accepted.dataset_version_id,),
        ),
        transform=TransformSpec(
            transform_id="return",
            parameters={"horizon": 1, "reset_on_session": False},
        ),
        window=WindowSpec(
            kind=WindowKind.POINT_IN_TIME,
            length=1,
            causality=WindowCausality.CAUSAL,
            offline_only=False,
        ),
        normalization=NormalizationSpec(normalization_id="identity"),
        availability_assumptions={"timing": "synthetic available_ts"},
        available_ts_derivation_rule="feature.available_ts = input available_ts",
        implementation_eligible=False,
    )
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_unapproved_fixture",
        feature_set_version="v1",
        features=(unapproved_spec,),
    )

    with pytest.raises(FeatureMaterializationError, match="not implementation eligible"):
        build_feature_materialization_plan(
            feature_set,
            accepted,
            partition_id="development_partition",
            alpha_data_root=tmp_path,
        )


def test_locked_partition_requires_governance_metadata(tmp_path: Path) -> None:
    accepted = _accepted_version("dsv_synthetic_engine_ohlcv_v1")
    definition = _returns_definition(accepted.dataset_version_id)
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_locked_fixture",
        feature_set_version="v1",
        features=(definition.spec,),
    )
    partition_plan = DatasetPartitionPlan.canonical()

    with pytest.raises(DataFoundationValidationError, match="Governance contamination"):
        build_feature_materialization_plan(
            feature_set,
            accepted,
            partition_id="locked_test_candidate",
            alpha_data_root=tmp_path,
            partition_plan=partition_plan,
        )

    plan = build_feature_materialization_plan(
        feature_set,
        accepted,
        partition_id="locked_test_candidate",
        alpha_data_root=tmp_path,
        governance_metadata=_locked_partition_metadata(),
        partition_plan=partition_plan,
    )

    assert plan.partition_id == "locked_test_candidate"


def test_output_root_must_stay_outside_repo_tree() -> None:
    accepted = _accepted_version("dsv_synthetic_engine_ohlcv_v1")
    definition = _returns_definition(accepted.dataset_version_id)
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_repo_root_fixture",
        feature_set_version="v1",
        features=(definition.spec,),
    )

    with pytest.raises(FeatureMaterializationError, match="outside the repository"):
        build_feature_materialization_plan(
            feature_set,
            accepted,
            partition_id="development_partition",
            alpha_data_root=Path.cwd() / "data",
        )


def test_dataset_resolution_uses_consumption_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    dataset_id = "dsv_synthetic_engine_ohlcv_v1"
    quality_report = _quality_report(dataset_id)
    coverage_report = _coverage_report(dataset_id)
    version = _dataset_version(dataset_id, quality_report=quality_report)
    calls: list[tuple[object, object]] = []

    def fake_resolve(registry_path: object, requested_id: object) -> DatasetVersion:
        calls.append((registry_path, requested_id))
        return version

    monkeypatch.setattr(consumption, "resolve_dataset_version", fake_resolve)

    accepted = resolve_feature_materialization_dataset(
        "synthetic_registry.sqlite",
        dataset_id,
        lifecycle_state="VERSIONED",
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest={"manifest_hash": version.manifest_hash},
        code_hash=version.code_hash,
        config_hash=version.config_hash,
    )

    assert calls == [("synthetic_registry.sqlite", dataset_id)]
    assert accepted.dataset_version_id == dataset_id


def _returns_definition(dataset_version_id: str):
    return build_ohlcv_feature_definition(
        OHLCVFeatureName.RETURNS,
        _approved_request(OHLCVFeatureName.RETURNS),
        EmptyRegistryReader(),
        dataset_version_ids=(dataset_version_id,),
        reset_on_session=False,
    )


def _approved_request(feature: OHLCVFeatureName) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"engine_{feature.value}"],
        formula_sketch={
            "exposure_family": f"engine_{feature.value}",
            "inputs": ["canonical_ohlcv"],
            "operation": feature.value,
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
    return (
        _bar_row(dataset_id, "2024-01-02T14:30:00+00:00", close="100.00"),
        _bar_row(dataset_id, "2024-01-02T14:31:00+00:00", close="101.00"),
    )


def _bar_row(dataset_id: str, bar_start_ts: str, *, close: str) -> dict[str, object]:
    start = _dt(bar_start_ts)
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_CONTINUOUS",
        "bar_start_ts": start.isoformat(),
        "bar_end_ts": (start.replace(minute=start.minute + 1)).isoformat(),
        "event_ts": (start.replace(minute=start.minute + 1)).isoformat(),
        "available_ts": (start.replace(minute=start.minute + 1, second=1)).isoformat(),
        "ingested_at": (start.replace(minute=start.minute + 1, second=2)).isoformat(),
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


def _locked_partition_metadata() -> dict[str, object]:
    return {
        "study_id": "study_fixture",
        "contamination_record_id": "locked_test_contamination_fixture",
        "reason": "synthetic engine test records locked-partition access",
    }


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
