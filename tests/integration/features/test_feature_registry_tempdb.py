from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from alpha_system.features.contracts import (
    FeatureFamily,
    FeatureInputSpec,
    FeatureLineageRecord,
    FeatureSetSpec,
    FeatureSpec,
    NormalizationSpec,
    TransformSpec,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.registry import (
    DEFAULT_FEATURE_REGISTRY_RELATIVE_PATH,
    FeatureRegistry,
    FeatureRegistryLifecycleState,
    FeatureRegistryRecord,
)
from alpha_system.features.request_gate import evaluate_feature_request_gate
from alpha_system.governance.duplicate_exposure import ExposureCheckResult, ExposureRegistryStatus
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"


def test_feature_registry_tempdb_persist_resolve_deprecate_round_trip(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "features.sqlite"
    registry = FeatureRegistry(registry_path)
    record, feature_set = _registry_record(tmp_path, registry)

    persisted = registry.persist_feature(record)
    resolved = FeatureRegistry(registry_path).resolve_feature(record.feature_version_id)

    assert registry_path.exists()
    assert registry_path.is_relative_to(tmp_path)
    assert persisted.feature_version == record.feature_version
    assert resolved is not None
    assert resolved.feature_version == record.feature_version
    assert resolved.lineage.feature_request_id == record.feature_request_id
    assert resolved.first_available_ts == _dt("2024-01-02T14:31:05+00:00")
    assert tuple(registry.resolve_feature_set(feature_set)) == (resolved,)

    deprecation = registry.deprecate_feature(
        record.feature_version_id,
        reason="synthetic tempdb retirement",
        deprecated_by="FLF-P14 integration test",
        deprecated_at=_dt("2024-01-04T00:00:00+00:00"),
    )
    deprecated = registry.resolve_feature(record.feature_version_id)

    assert deprecation.feature_version_id == record.feature_version_id
    assert deprecated is not None
    assert deprecated.lifecycle_state is FeatureRegistryLifecycleState.DEPRECATED
    assert deprecated.lineage.feature_version == record.lineage.feature_version

    with sqlite3.connect(registry_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            )
        }
        feature_rows = connection.execute(
            "SELECT count(*) FROM feature_registry_records"
        ).fetchone()[0]
        lineage_rows = connection.execute(
            "SELECT count(*) FROM feature_lineage_records"
        ).fetchone()[0]
        deprecation_rows = connection.execute(
            "SELECT count(*) FROM feature_deprecation_records"
        ).fetchone()[0]

    assert "feature_values" not in tables
    assert feature_rows == 1
    assert lineage_rows == 1
    assert deprecation_rows == 1


def test_default_feature_registry_path_uses_alpha_data_root(tmp_path: Path) -> None:
    alpha_data_root = tmp_path / "alpha_data"
    registry = FeatureRegistry.from_alpha_data_root(alpha_data_root)

    assert registry.registry_path == alpha_data_root / DEFAULT_FEATURE_REGISTRY_RELATIVE_PATH
    assert registry.registry_path.exists()


def _registry_record(
    tmp_path: Path,
    registry: FeatureRegistry,
) -> tuple[FeatureRegistryRecord, FeatureSetSpec]:
    request = _feature_request()
    decision = evaluate_feature_request_gate(request, registry)
    assert decision.implementation_allowed is True
    assert decision.checked_feature_request is not None
    assert decision.duplicate_exposure_report is not None
    spec = _feature_spec(decision.feature_request_id, decision)
    version = spec.derive_feature_version()
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_registry_tempdb_fixture",
        feature_set_version="v1",
        features=(spec,),
    )
    lineage = FeatureLineageRecord(
        feature_version=version,
        feature_spec=spec,
        feature_request_id=spec.feature_request_id,
        contract_provenance={"phase": "FLF-P14", "fixture": "tempdb"},
    )
    return (
        FeatureRegistryRecord(
            feature_version=version,
            feature_spec=spec,
            lineage=lineage,
            feature_request_payload=decision.checked_feature_request.to_dict(),
            duplicate_exposure_report=decision.duplicate_exposure_report,
            feature_set_id=feature_set.feature_set_id,
            feature_set_version=feature_set.feature_set_version,
            feature_set_ordinal=0,
            materialization_plan_id="fmat_synthetic_tempdb",
            dataset_version_id="dsv_synthetic_registry_tempdb_v1",
            partition_id="development_partition",
            materialization_output_path=(tmp_path / "features" / "values.jsonl").as_posix(),
            value_record_count=1,
            first_event_ts=_dt("2024-01-02T14:31:00+00:00"),
            last_event_ts=_dt("2024-01-02T14:31:00+00:00"),
            first_available_ts=_dt("2024-01-02T14:31:05+00:00"),
            last_available_ts=_dt("2024-01-02T14:31:05+00:00"),
            registered_at=_dt("2024-01-02T15:00:00+00:00"),
            registry_metadata={"fixture": "synthetic tempdb"},
        ),
        feature_set,
    )


def _feature_spec(feature_request_id: str, decision: object) -> FeatureSpec:
    return FeatureSpec(
        feature_id="base_ohlcv_registry_tempdb_return_1m",
        family=FeatureFamily.BASE_OHLCV,
        feature_request_id=feature_request_id,
        inputs=FeatureInputSpec(
            input_views=("canonical_ohlcv",),
            fields=("synthetic_close", "available_ts"),
            dataset_version_ids=("dsv_synthetic_registry_tempdb_v1",),
        ),
        transform=TransformSpec(
            transform_id="pct_change",
            parameters={"operation": "pct_change", "inputs": ["synthetic_close"], "window": 1},
        ),
        window=WindowSpec(
            kind=WindowKind.ROLLING,
            length=1,
            causality=WindowCausality.CAUSAL,
            offline_only=False,
        ),
        normalization=NormalizationSpec(normalization_id="identity"),
        availability_assumptions={
            "timing": "synthetic fixture available_ts follows event_ts"
        },
        available_ts_derivation_rule="feature.available_ts = input available_ts",
        live=True,
        implementation_eligible=True,
        request_gate_decision=decision,
    )


def _feature_request() -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=["synthetic_registry_tempdb_return_1m"],
        formula_sketch={
            "exposure_family": "synthetic_registry_tempdb_return_1m",
            "inputs": ["synthetic_close"],
            "operation": "pct_change",
            "window": 1,
        },
        availability_assumptions={
            "timing": "synthetic feature inputs are available after fixture bars close"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["synthetic_close"],
            "source": "tiny synthetic fixture fields only",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
