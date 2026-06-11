from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from alpha_system.core.value_store import ValueStoreFormat, ValueStoreHandle
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetVersion,
    ReportStatus,
    compute_quality_report_hash,
)
from alpha_system.features import consumption
from alpha_system.features.contracts import (
    FeatureFamily,
    FeatureInputSpec,
    FeatureLineageRecord,
    FeatureSetSpec,
    FeatureSpec,
    FeatureValueRecord,
    NormalizationSpec,
    TransformSpec,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.engine import (
    FeatureMaterializationResult,
    build_feature_materialization_plan,
)
from alpha_system.features.registry import (
    PROHIBITED_FEATURE_REGISTRY_STATES,
    FeatureRegistry,
    FeatureRegistryError,
    FeatureRegistryLifecycleState,
)
from alpha_system.features.store import FeatureStore, FeatureStoreError
from alpha_system.governance.duplicate_exposure import (
    ExposureCheckResult,
    ExposureRegistryStatus,
    apply_duplicate_exposure_notes,
    check_duplicate_exposure,
)
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)
from alpha_system.governance.serialization import canonical_serialize

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


class StaticRegistryReader:
    def __init__(self, entries: list[dict[str, object]]) -> None:
        self.entries = entries

    def read_factor_versions(self) -> list[dict[str, object]]:
        return list(self.entries)


def test_registration_fails_closed_without_valid_spec_request_or_lineage(tmp_path: Path) -> None:
    store = FeatureStore(FeatureRegistry(tmp_path / "features.sqlite"))
    request = _feature_request("synthetic_close_return_1m")
    spec, checked_request = _implementation_spec(
        feature_id="base_ohlcv_close_return_1m",
        request=request,
        registry_reader=EmptyRegistryReader(),
    )
    result = _materialization_result(tmp_path, spec)
    version = spec.derive_feature_version()

    unvalidated_spec = _feature_spec(
        feature_id="base_ohlcv_unvalidated_return_1m",
        feature_request_id=spec.feature_request_id,
        implementation_eligible=False,
    )
    with pytest.raises(FeatureStoreError, match="implementation eligible"):
        store.register_materialized_feature(
            result,
            feature_spec=unvalidated_spec,
            feature_version=version,
            feature_request=checked_request,
        )

    with pytest.raises(FeatureStoreError, match="FeatureRequest gate rejected"):
        store.register_materialized_feature(
            result,
            feature_spec=spec,
            feature_version=version,
            feature_request=None,
        )

    for status in (
        FeatureRequestApprovalStatus.PENDING,
        FeatureRequestApprovalStatus.NEEDS_REVIEW,
    ):
        with pytest.raises(FeatureStoreError, match="FeatureRequest gate rejected"):
            store.register_materialized_feature(
                result,
                feature_spec=spec,
                feature_version=version,
                feature_request=_feature_request(
                    f"synthetic_close_return_{status.value.lower()}",
                    approval_status=status,
                ),
            )

    with pytest.raises(FeatureStoreError, match="FeatureRequest gate rejected"):
        store.register_materialized_feature(
            result,
            feature_spec=spec,
            feature_version=version,
            feature_request=_blocked_duplicate_request(),
        )

    with pytest.raises(FeatureStoreError, match="FeatureLineageRecord"):
        store.register_materialized_feature(
            result,
            feature_spec=spec,
            feature_version=version,
            feature_request=checked_request,
            lineage=object(),  # type: ignore[arg-type]
        )

    assert store.registry.count_feature_records() == 0


def test_successful_registration_resolves_by_version_and_feature_set(
    tmp_path: Path,
) -> None:
    store = FeatureStore(FeatureRegistry(tmp_path / "features.sqlite"))
    request = _feature_request("synthetic_close_return_1m")
    spec, checked_request = _implementation_spec(
        feature_id="base_ohlcv_close_return_1m",
        request=request,
        registry_reader=EmptyRegistryReader(),
    )
    result = _materialization_result(tmp_path, spec)
    version = spec.derive_feature_version()
    lineage = FeatureLineageRecord(
        feature_version=version,
        feature_spec=spec,
        feature_request_id=spec.feature_request_id,
        contract_provenance={"phase": "FLF-P14"},
    )

    record = store.register_materialized_feature(
        result,
        feature_spec=spec,
        feature_version=version,
        feature_request=checked_request,
        lineage=lineage,
    )

    assert record.feature_version == version
    assert record.lineage == lineage
    assert record.value_record_count == 2
    assert record.first_available_ts == _dt("2024-01-02T14:31:05+00:00")
    assert record.last_available_ts == _dt("2024-01-02T14:32:05+00:00")
    assert record.duplicate_exposure_report.has_findings is False
    assert hash(record)

    resolved = store.resolve_feature(version.feature_version_id)
    assert resolved is not None
    assert resolved.feature_version == version
    assert resolved.lineage.feature_request_id == spec.feature_request_id

    feature_set_records = store.resolve_feature_set(result.plan.feature_set)
    assert tuple(item.feature_version for item in feature_set_records) == (version,)

    duplicate = store.register_materialized_feature(
        result,
        feature_spec=spec,
        feature_version=version,
        feature_request=checked_request,
        lineage=lineage,
    )
    assert duplicate.feature_version_id == record.feature_version_id
    assert store.registry.count_feature_records() == 1


def test_existing_registration_refreshes_materialization_metadata_via_store(
    tmp_path: Path,
) -> None:
    store = FeatureStore(FeatureRegistry(tmp_path / "features.sqlite"))
    request = _feature_request("synthetic_close_return_refresh")
    spec, checked_request = _implementation_spec(
        feature_id="base_ohlcv_close_return_refresh",
        request=request,
        registry_reader=EmptyRegistryReader(),
    )
    result = _materialization_result(tmp_path, spec)
    version = spec.derive_feature_version()

    record = store.register_materialized_feature(
        result,
        feature_spec=spec,
        feature_version=version,
        feature_request=checked_request,
        registry_metadata={"phase": "old"},
    )
    refreshed_path = tmp_path / "features" / "refreshed.parquet"
    refreshed_handle = ValueStoreHandle(
        format=ValueStoreFormat.PARQUET,
        jsonl_path=None,
        parquet_path=refreshed_path.as_posix(),
        value_count=result.record_count,
        content_hash="sha256:" + HASH_2,
        schema_version="schema.refresh.v1",
        dataset_version_id=result.plan.dataset_version_id,
        set_id=result.plan.feature_set.feature_set_id,
        partition_id=result.plan.partition_id,
        min_event_ts="2024-01-02T14:31:00+00:00",
        max_event_ts="2024-01-02T14:32:00+00:00",
        min_available_ts="2024-01-02T14:31:05+00:00",
        max_available_ts="2024-01-02T14:32:05+00:00",
    )

    refreshed = store.register_materialized_feature(
        replace(
            result,
            output_path=refreshed_path,
            value_store_handle=refreshed_handle,
        ),
        feature_spec=spec,
        feature_version=version,
        feature_request=checked_request,
        registry_metadata={
            "phase": "new",
            "session_metadata_role": "SESSION_METADATA_POINT_IN_TIME",
        },
    )

    assert refreshed.feature_version_id == record.feature_version_id
    assert refreshed.registered_at == record.registered_at
    assert store.registry.count_feature_records() == 1
    resolved = store.resolve_feature(version.feature_version_id)
    assert resolved is not None
    assert resolved.parquet_path == refreshed_path.as_posix()
    assert resolved.value_content_hash == refreshed_handle.content_hash
    assert resolved.value_schema_version == "schema.refresh.v1"
    assert resolved.registry_metadata.to_dict()["phase"] == "new"
    assert (
        resolved.registry_metadata.to_dict()["session_metadata_role"]
        == "SESSION_METADATA_POINT_IN_TIME"
    )


def test_registry_backfills_old_rows_and_persists_parquet_metadata(tmp_path: Path) -> None:
    request = _feature_request("synthetic_close_return_old_row")
    old_spec, old_checked_request = _implementation_spec(
        feature_id="base_ohlcv_close_return_old_row",
        request=request,
        registry_reader=EmptyRegistryReader(),
    )
    old_store = FeatureStore(FeatureRegistry(tmp_path / "source.sqlite"))
    old_record = old_store.register_materialized_feature(
        _materialization_result(tmp_path, old_spec),
        feature_spec=old_spec,
        feature_version=old_spec.derive_feature_version(),
        feature_request=old_checked_request,
    )
    old_payload = old_record.to_dict()
    for key in (
        "value_store_format",
        "parquet_path",
        "value_content_hash",
        "value_schema_version",
    ):
        old_payload["materialization"].pop(key, None)

    registry_path = tmp_path / "old_features.sqlite"
    with sqlite3.connect(registry_path) as connection:
        connection.execute(
            """
            CREATE TABLE feature_registry_records (
                feature_version_id TEXT PRIMARY KEY,
                feature_id TEXT NOT NULL,
                feature_request_id TEXT NOT NULL,
                lifecycle_state TEXT NOT NULL,
                materialization_plan_id TEXT NOT NULL,
                dataset_version_id TEXT NOT NULL,
                partition_id TEXT NOT NULL,
                materialization_output_path TEXT NOT NULL,
                value_record_count INTEGER NOT NULL,
                first_event_ts TEXT NOT NULL,
                last_event_ts TEXT NOT NULL,
                first_available_ts TEXT NOT NULL,
                last_available_ts TEXT NOT NULL,
                duplicate_exposure_status TEXT NOT NULL,
                registered_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO feature_registry_records (
                feature_version_id,
                feature_id,
                feature_request_id,
                lifecycle_state,
                materialization_plan_id,
                dataset_version_id,
                partition_id,
                materialization_output_path,
                value_record_count,
                first_event_ts,
                last_event_ts,
                first_available_ts,
                last_available_ts,
                duplicate_exposure_status,
                registered_at,
                metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                old_record.feature_version_id,
                old_record.feature_spec.feature_id,
                old_record.feature_request_id,
                old_record.lifecycle_state.value,
                old_record.materialization_plan_id,
                old_record.dataset_version_id,
                old_record.partition_id,
                old_record.materialization_output_path,
                old_record.value_record_count,
                old_record.first_event_ts.isoformat(),
                old_record.last_event_ts.isoformat(),
                old_record.first_available_ts.isoformat(),
                old_record.last_available_ts.isoformat(),
                old_record.duplicate_exposure_status,
                old_record.registered_at.isoformat(),
                canonical_serialize(old_payload),
            ),
        )

    registry = FeatureRegistry(registry_path)
    loaded_old = registry.resolve_feature(old_record.feature_version_id)
    assert loaded_old is not None
    assert loaded_old.value_store_format == "jsonl"
    assert loaded_old.parquet_path is None

    new_request = _feature_request("synthetic_close_return_parquet_row")
    new_spec, new_checked_request = _implementation_spec(
        feature_id="base_ohlcv_close_return_parquet_row",
        request=new_request,
        registry_reader=registry,
    )
    new_result = _materialization_result(tmp_path, new_spec)
    parquet_path = tmp_path / "features" / "values.parquet"
    handle = ValueStoreHandle(
        format=ValueStoreFormat.PARQUET,
        jsonl_path=None,
        parquet_path=parquet_path.as_posix(),
        value_count=new_result.record_count,
        content_hash="sha256:" + "1" * 64,
        schema_version="schema.v1",
        dataset_version_id=new_result.plan.dataset_version_id,
        set_id=new_result.plan.feature_set.feature_set_id,
        partition_id=new_result.plan.partition_id,
        min_event_ts="2024-01-02T14:31:00+00:00",
        max_event_ts="2024-01-02T14:32:00+00:00",
        min_available_ts="2024-01-02T14:31:05+00:00",
        max_available_ts="2024-01-02T14:32:05+00:00",
    )
    new_record = FeatureStore(registry).register_materialized_feature(
        replace(new_result, output_path=parquet_path, value_store_handle=handle),
        feature_spec=new_spec,
        feature_version=new_spec.derive_feature_version(),
        feature_request=new_checked_request,
    )

    loaded_new = registry.resolve_feature(new_record.feature_version_id)
    assert loaded_new is not None
    assert loaded_new.value_store_format == "parquet"
    assert loaded_new.parquet_path == parquet_path.as_posix()
    assert loaded_new.value_content_hash == handle.content_hash
    assert loaded_new.value_schema_version == "schema.v1"


def test_duplicate_or_equivalent_exposure_is_not_silently_admitted(
    tmp_path: Path,
) -> None:
    store = FeatureStore(FeatureRegistry(tmp_path / "features.sqlite"))
    first_request = _feature_request("synthetic_close_return_1m")
    first_spec, first_checked_request = _implementation_spec(
        feature_id="base_ohlcv_close_return_1m",
        request=first_request,
        registry_reader=EmptyRegistryReader(),
    )
    first_result = _materialization_result(tmp_path, first_spec)
    first_version = first_spec.derive_feature_version()
    store.register_materialized_feature(
        first_result,
        feature_spec=first_spec,
        feature_version=first_version,
        feature_request=first_checked_request,
    )

    duplicate_request = _feature_request(
        first_spec.feature_id,
        requested_inputs=[first_spec.feature_id],
        exposure_family=first_spec.feature_id,
    )
    with pytest.raises(FeatureStoreError, match="duplicate-exposure guard"):
        store.register_materialized_feature(
            first_result,
            feature_spec=first_spec,
            feature_version=first_version,
            feature_request=duplicate_request,
        )
    assert store.registry.count_feature_records() == 1

    equivalent_request = _feature_request(
        "synthetic_close_return_equivalent_1m",
        exposure_family="synthetic_close_return_equivalent_1m",
        operation="pct_change",
        inputs=["synthetic_close"],
        window=1,
    )
    equivalent_spec, equivalent_checked_request = _implementation_spec(
        feature_id="base_ohlcv_close_return_equivalent_1m",
        request=equivalent_request,
        registry_reader=store.registry,
    )
    equivalent_result = _materialization_result(tmp_path, equivalent_spec)
    equivalent_version = equivalent_spec.derive_feature_version()

    record = store.register_materialized_feature(
        equivalent_result,
        feature_spec=equivalent_spec,
        feature_version=equivalent_version,
        feature_request=equivalent_checked_request,
    )

    assert record.duplicate_exposure_status == "EQUIVALENCE_RECORDED"
    assert record.duplicate_exposure_report.has_findings is True
    assert len(record.duplicate_exposure_report.equivalent_feature_groups) == 1
    assert (
        record.duplicate_exposure_report.equivalent_feature_groups[0]
        .matched_registry_reference["factor_id"]
        == first_spec.feature_id
    )
    assert store.registry.count_feature_records() == 2


def test_deprecation_preserves_lineage_and_excludes_prohibited_states(
    tmp_path: Path,
) -> None:
    store = FeatureStore(FeatureRegistry(tmp_path / "features.sqlite"))
    request = _feature_request("synthetic_close_return_1m")
    spec, checked_request = _implementation_spec(
        feature_id="base_ohlcv_close_return_1m",
        request=request,
        registry_reader=EmptyRegistryReader(),
    )
    result = _materialization_result(tmp_path, spec)
    version = spec.derive_feature_version()
    record = store.register_materialized_feature(
        result,
        feature_spec=spec,
        feature_version=version,
        feature_request=checked_request,
    )

    deprecation = store.deprecate_feature(
        version.feature_version_id,
        reason="synthetic fixture retirement",
        deprecated_by="FLF-P14 unit test",
        deprecated_at=_dt("2024-01-03T00:00:00+00:00"),
    )

    assert deprecation.feature_version_id == version.feature_version_id
    resolved = store.resolve_feature(version.feature_version_id)
    assert resolved is not None
    assert resolved.lifecycle_state is FeatureRegistryLifecycleState.DEPRECATED
    assert resolved.lineage == record.lineage
    assert store.resolve_active_feature(version.feature_version_id) is None
    assert store.registry.resolve_registered_feature(version.feature_version_id) is None
    assert store.registry.resolve_deprecation(version.feature_version_id) == deprecation

    assert PROHIBITED_FEATURE_REGISTRY_STATES.isdisjoint(
        {state.value for state in FeatureRegistryLifecycleState}
    )
    with pytest.raises(FeatureRegistryError, match="prohibited"):
        replace(record, lifecycle_state="TRADABLE")


def _implementation_spec(
    *,
    feature_id: str,
    request: FeatureRequest,
    registry_reader: object,
    dataset_version_id: str = "dsv_synthetic_feature_store_v1",
) -> tuple[FeatureSpec, FeatureRequest]:
    decision = _require_allowed_request(request, registry_reader)
    spec = _feature_spec(
        feature_id=feature_id,
        feature_request_id=decision.feature_request_id,
        dataset_version_id=dataset_version_id,
        implementation_eligible=True,
        request_gate_decision=decision,
    )
    assert decision.checked_feature_request is not None
    return spec, decision.checked_feature_request


def _require_allowed_request(request: FeatureRequest, registry_reader: object):
    from alpha_system.features.request_gate import evaluate_feature_request_gate

    decision = evaluate_feature_request_gate(request, registry_reader)
    assert decision.implementation_allowed is True
    return decision


def _feature_spec(
    *,
    feature_id: str,
    feature_request_id: str,
    dataset_version_id: str = "dsv_synthetic_feature_store_v1",
    implementation_eligible: bool,
    request_gate_decision: object | None = None,
) -> FeatureSpec:
    kwargs = {
        "feature_id": feature_id,
        "family": FeatureFamily.BASE_OHLCV,
        "feature_request_id": feature_request_id,
        "inputs": FeatureInputSpec(
            input_views=("canonical_ohlcv",),
            fields=("synthetic_close", "available_ts"),
            dataset_version_ids=(dataset_version_id,),
        ),
        "transform": TransformSpec(
            transform_id="pct_change",
            parameters={"operation": "pct_change", "inputs": ["synthetic_close"], "window": 1},
        ),
        "window": WindowSpec(
            kind=WindowKind.ROLLING,
            length=1,
            causality=WindowCausality.CAUSAL,
            offline_only=False,
        ),
        "normalization": NormalizationSpec(normalization_id="identity"),
        "availability_assumptions": {
            "timing": "synthetic fixture available_ts follows event_ts"
        },
        "available_ts_derivation_rule": "feature.available_ts = input available_ts",
        "live": True,
        "implementation_eligible": implementation_eligible,
    }
    if implementation_eligible:
        return FeatureSpec(**kwargs, request_gate_decision=request_gate_decision)
    return FeatureSpec(**kwargs)


def _feature_request(
    name: str,
    *,
    requested_inputs: list[str] | None = None,
    exposure_family: str | None = None,
    operation: str = "pct_change",
    inputs: list[str] | None = None,
    window: int = 1,
    approval_status: FeatureRequestApprovalStatus = FeatureRequestApprovalStatus.APPROVED,
) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    request_inputs = requested_inputs or [name]
    formula_inputs = inputs or ["synthetic_close"]
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=request_inputs,
        formula_sketch={
            "exposure_family": exposure_family or name,
            "inputs": formula_inputs,
            "operation": operation,
            "window": window,
        },
        availability_assumptions={
            "timing": "synthetic feature inputs are available after fixture bars close"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": formula_inputs,
            "source": "tiny synthetic fixture fields only",
        },
        approval_status=approval_status,
    )


def _blocked_duplicate_request() -> FeatureRequest:
    request = _feature_request("synthetic_blocked_duplicate")
    registry = StaticRegistryReader(
        [
            {
                "factor_id": "synthetic_blocked_duplicate",
                "factor_version": "v1",
                "name": "synthetic_blocked_duplicate",
                "metadata": {
                    "exposure_family": "synthetic_blocked_duplicate",
                    "operation": "pct_change",
                    "inputs": ["synthetic_close"],
                    "window": 1,
                },
                "parameters": {
                    "operation": "pct_change",
                    "inputs": ["synthetic_close"],
                    "window": 1,
                },
            }
        ]
    )
    return apply_duplicate_exposure_notes(request, check_duplicate_exposure(request, registry))


def _materialization_result(
    tmp_path: Path,
    spec: FeatureSpec,
) -> FeatureMaterializationResult:
    dataset_version_id = spec.inputs.dataset_version_ids[0]
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_store_fixture",
        feature_set_version=f"v1_{spec.feature_id}",
        features=(spec,),
    )
    plan = build_feature_materialization_plan(
        feature_set,
        _accepted_version(dataset_version_id),
        partition_id="development_partition",
        alpha_data_root=tmp_path,
    )
    version = spec.derive_feature_version()
    return FeatureMaterializationResult(
        plan=plan,
        records=(
            FeatureValueRecord(
                feature_version_id=version.feature_version_id,
                entity_id="ES",
                event_ts=_dt("2024-01-02T14:31:00+00:00"),
                available_ts=_dt("2024-01-02T14:31:05+00:00"),
                value=1.0,
            ),
            FeatureValueRecord(
                feature_version_id=version.feature_version_id,
                entity_id="ES",
                event_ts=_dt("2024-01-02T14:32:00+00:00"),
                available_ts=_dt("2024-01-02T14:32:05+00:00"),
                value=1.5,
            ),
        ),
        dry_run=False,
        wrote_output=False,
        output_path=plan.output_path,
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
    return {"status": ReportStatus.PASSING.value, "count": 0, "blocking": False, "notes": []}


def _coverage_summary(*, include_partition_counts: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": ReportStatus.PASSING.value,
        "blocking": False,
        "expected_count": 2,
        "observed_count": 2,
        "missing_count": 0,
        "coverage_ratio": 1.0,
    }
    if include_partition_counts:
        payload["partition_counts"] = {"development_partition": 2}
        payload["missing_interval_count"] = 0
        payload["incomplete_chunk_count"] = 0
    return payload


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
