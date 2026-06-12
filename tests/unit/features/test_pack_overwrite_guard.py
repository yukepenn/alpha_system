from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from alpha_system.core.value_store import (
    ValueStoreFormat,
    compute_value_content_hash,
    write_parquet_values,
)
from alpha_system.features.contracts import FeatureLineageRecord, FeatureSetSpec
from alpha_system.features.fast import (
    FAST_PRODUCER_ENGINE_ID,
    FAST_VALUE_SCHEMA_VERSION,
    PackMaterializer,
    build_fast_feature_pack,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
)
from alpha_system.features.pack_integrity import (
    PACK_AUDIT_BENIGN_EXTRA,
    PACK_AUDIT_CLEAN,
    PACK_AUDIT_STALE_REGISTRY,
    PackIntegrityError,
    audit_registered_feature_packs,
)
from alpha_system.features.registry import FeatureRegistry, FeatureRegistryRecord
from tests.fixtures.feature_compute_fast_path.base_ohlcv import (
    DATASET_ID,
    PARTITION_ID,
    base_ohlcv_pack_rows,
)
from tests.fixtures.feature_label.synthetic import (
    EmptyRegistryReader,
    accepted_version,
    approved_feature_request,
)


def test_registered_pack_subset_rewrite_is_refused_and_superset_allowed(
    tmp_path: Path,
) -> None:
    pytest.importorskip("polars")
    materializer = PackMaterializer()
    rows = base_ohlcv_pack_rows()
    definitions, full_pack, _ = _pack_contracts(
        (
            OHLCVFeatureName.RETURNS,
            OHLCVFeatureName.LOG_RETURNS,
        )
    )
    full_result = materializer.materialize_pack(
        full_pack,
        accepted_version(DATASET_ID),
        partition_id=PARTITION_ID,
        canonical_frame=materializer.frame_from_rows(rows),
        alpha_data_root=tmp_path,
        value_store_format=ValueStoreFormat.PARQUET,
    )
    registry = FeatureRegistry.from_alpha_data_root(tmp_path)
    _persist_pack_records(registry, full_result, definitions)

    _, subset_pack, _ = _pack_contracts((OHLCVFeatureName.RETURNS,))
    missing = definitions[1].feature_version_id
    with pytest.raises(
        PackIntegrityError,
        match="deprecate first or run full-scope config",
    ) as excinfo:
        materializer.materialize_pack(
            subset_pack,
            accepted_version(DATASET_ID),
            partition_id=PARTITION_ID,
            canonical_frame=materializer.frame_from_rows(rows),
            alpha_data_root=tmp_path,
            value_store_format=ValueStoreFormat.PARQUET,
        )

    _, superset_pack, _ = _pack_contracts(
        (
            OHLCVFeatureName.RETURNS,
            OHLCVFeatureName.LOG_RETURNS,
            OHLCVFeatureName.ROLLING_VOLATILITY,
        )
    )
    superset_result = materializer.materialize_pack(
        superset_pack,
        accepted_version(DATASET_ID),
        partition_id=PARTITION_ID,
        canonical_frame=materializer.frame_from_rows(rows),
        alpha_data_root=tmp_path,
        value_store_format=ValueStoreFormat.PARQUET,
    )

    assert missing in str(excinfo.value)
    assert superset_result.value_store_handle is not None
    assert Path(superset_result.value_store_handle.parquet_path or "").exists()


def test_register_pack_reconciliation_catches_tampered_file(tmp_path: Path) -> None:
    pytest.importorskip("polars")
    materializer = PackMaterializer()
    definitions, pack, feature_requests = _pack_contracts((OHLCVFeatureName.RETURNS,))
    result = materializer.materialize_pack(
        pack,
        accepted_version(DATASET_ID),
        partition_id=PARTITION_ID,
        canonical_frame=materializer.frame_from_rows(base_ohlcv_pack_rows()),
        alpha_data_root=tmp_path,
        value_store_format=ValueStoreFormat.PARQUET,
    )
    materializer.register_pack(result, pack, feature_requests=feature_requests)
    handle = result.value_store_handle
    assert handle is not None and handle.parquet_path

    tampered_rows = [record.to_dict() for record in result.records[:-1]]
    tampered_hash = compute_value_content_hash(tampered_rows)
    write_parquet_values(
        tampered_rows,
        handle.parquet_path,
        plan_dict=result.plan.to_dict(),
        content_hash=tampered_hash,
        schema_version=FAST_VALUE_SCHEMA_VERSION,
        value_count=len(tampered_rows),
    )

    with pytest.raises(
        PackIntegrityError,
        match="hash_mismatch_feature_version_ids",
    ) as excinfo:
        materializer.register_pack(result, pack, feature_requests=feature_requests)

    assert definitions[0].feature_version_id in str(excinfo.value)


def test_pack_audit_reports_stale_registry_benign_extra_and_clean(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    pytest.importorskip("polars")
    materializer = PackMaterializer()
    definitions, pack, _ = _pack_contracts(
        (
            OHLCVFeatureName.RETURNS,
            OHLCVFeatureName.LOG_RETURNS,
            OHLCVFeatureName.ROLLING_VOLATILITY,
            OHLCVFeatureName.ROLLING_RANGE,
            OHLCVFeatureName.RANGE_POSITION,
        )
    )
    result = materializer.materialize_pack(
        pack,
        accepted_version(DATASET_ID),
        partition_id=PARTITION_ID,
        canonical_frame=materializer.frame_from_rows(base_ohlcv_pack_rows()),
        alpha_data_root=tmp_path,
        value_store_format=ValueStoreFormat.PARQUET,
    )
    by_id = _record_dicts_by_feature_version(result)
    registry = FeatureRegistry.from_alpha_data_root(tmp_path)

    clean_path = tmp_path / "audit" / "clean.parquet"
    clean_rows = by_id[definitions[0].feature_version_id]
    clean_hash = _write_rows(result, clean_path, clean_rows)
    _persist_pack_records(
        registry,
        result,
        definitions[:1],
        parquet_path=clean_path,
        content_hash=clean_hash,
    )

    extra_path = tmp_path / "audit" / "extra.parquet"
    extra_rows = (
        by_id[definitions[1].feature_version_id]
        + by_id[definitions[2].feature_version_id]
    )
    extra_hash = _write_rows(result, extra_path, extra_rows)
    _persist_pack_records(
        registry,
        result,
        definitions[1:2],
        parquet_path=extra_path,
        content_hash=extra_hash,
    )

    stale_path = tmp_path / "audit" / "stale.parquet"
    stale_rows = by_id[definitions[3].feature_version_id]
    stale_hash = _write_rows(
        result,
        stale_path,
        stale_rows + by_id[definitions[4].feature_version_id],
    )
    _write_rows(result, stale_path, stale_rows)
    _persist_pack_records(
        registry,
        result,
        definitions[3:5],
        parquet_path=stale_path,
        content_hash=stale_hash,
    )

    summary = audit_registered_feature_packs(alpha_data_root=tmp_path)
    by_status = {entry.status: entry for entry in summary.entries}

    assert summary.clean_count == 1
    assert summary.benign_extra_count == 1
    assert summary.stale_registry_count == 1
    assert by_status[PACK_AUDIT_CLEAN].parquet_path == clean_path.resolve().as_posix()
    assert by_status[PACK_AUDIT_BENIGN_EXTRA].extra_disk_feature_version_ids == (
        definitions[2].feature_version_id,
    )
    assert by_status[PACK_AUDIT_STALE_REGISTRY].missing_registered_feature_version_ids == (
        definitions[4].feature_version_id,
    )

    from alpha_system.cli.scaleout import run_pack_audit

    exit_code = run_pack_audit(argparse.Namespace(alpha_data_root=tmp_path, json=True))
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["stale_registry_count"] == 1
    assert payload["benign_extra_count"] == 1


def _pack_contracts(
    names: tuple[OHLCVFeatureName, ...],
) -> tuple[tuple[Any, ...], Any, dict[str, Any]]:
    requests = {
        name: approved_feature_request(f"pack_overwrite_guard_{name.value}")
        for name in names
    }
    definitions = tuple(
        build_ohlcv_feature_definition(
            name,
            requests[name],
            EmptyRegistryReader(),
            dataset_version_ids=(DATASET_ID,),
            window_length=20,
            horizon=1,
            reset_on_session=False,
            ddof=0,
        )
        for name in names
    )
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_pack_overwrite_guard",
        feature_set_version="v1",
        features=tuple(definition.spec for definition in definitions),
        description="Synthetic pack overwrite guard fixture.",
    )
    feature_requests = {
        definition.spec.feature_id: (
            definition.request_gate_decision.checked_feature_request or requests[name]
        )
        for definition, name in zip(definitions, names, strict=True)
    }
    return definitions, build_fast_feature_pack(feature_set), feature_requests


def _persist_pack_records(
    registry: FeatureRegistry,
    result: Any,
    definitions: tuple[Any, ...],
    *,
    parquet_path: str | Path | None = None,
    content_hash: str | None = None,
) -> None:
    handle = result.value_store_handle
    assert handle is not None and handle.parquet_path and handle.content_hash
    path = Path(parquet_path or handle.parquet_path).resolve().as_posix()
    pack_hash = content_hash or handle.content_hash
    values_by_id = _values_by_feature_version(result)
    for ordinal, definition in enumerate(definitions):
        decision = definition.request_gate_decision
        checked_request = decision.checked_feature_request
        duplicate_report = decision.duplicate_exposure_report
        assert checked_request is not None
        assert duplicate_report is not None
        version = definition.version
        values = values_by_id[version.feature_version_id]
        registry.persist_feature(
            FeatureRegistryRecord(
                feature_version=version,
                feature_spec=definition.spec,
                lineage=FeatureLineageRecord(
                    feature_version=version,
                    feature_spec=definition.spec,
                    feature_request_id=definition.spec.feature_request_id,
                    contract_provenance={
                        "producer_engine_id": FAST_PRODUCER_ENGINE_ID,
                        "value_schema_version": FAST_VALUE_SCHEMA_VERSION,
                    },
                ),
                feature_request_payload=checked_request.to_dict(),
                duplicate_exposure_report=duplicate_report,
                feature_set_id=result.plan.feature_set.feature_set_id,
                feature_set_version=result.plan.feature_set.feature_set_version,
                feature_set_ordinal=ordinal,
                materialization_plan_id=result.plan.plan_id,
                dataset_version_id=result.plan.dataset_version_id,
                partition_id=result.plan.partition_id,
                materialization_output_path=str(result.output_path or result.plan.output_path),
                value_store_format=handle.format.value,
                parquet_path=path,
                value_content_hash=pack_hash,
                producer_engine_id=FAST_PRODUCER_ENGINE_ID,
                value_schema_version=FAST_VALUE_SCHEMA_VERSION,
                value_record_count=len(values),
                first_event_ts=min(record.event_ts for record in values),
                last_event_ts=max(record.event_ts for record in values),
                first_available_ts=min(record.available_ts for record in values),
                last_available_ts=max(record.available_ts for record in values),
                registered_at=datetime(2026, 6, 12, tzinfo=UTC),
                registry_metadata={
                    "producer_engine_id": FAST_PRODUCER_ENGINE_ID,
                    "value_schema_version": FAST_VALUE_SCHEMA_VERSION,
                },
            )
        )


def _values_by_feature_version(result: Any) -> dict[str, tuple[Any, ...]]:
    grouped: dict[str, list[Any]] = defaultdict(list)
    for record in result.records:
        grouped[record.feature_version_id].append(record)
    return {feature_version_id: tuple(records) for feature_version_id, records in grouped.items()}


def _record_dicts_by_feature_version(result: Any) -> dict[str, list[dict[str, Any]]]:
    return {
        feature_version_id: [record.to_dict() for record in records]
        for feature_version_id, records in _values_by_feature_version(result).items()
    }


def _write_rows(result: Any, path: Path, rows: list[dict[str, Any]]) -> str:
    content_hash = compute_value_content_hash(rows)
    write_parquet_values(
        rows,
        path,
        plan_dict=result.plan.to_dict(),
        content_hash=content_hash,
        schema_version=FAST_VALUE_SCHEMA_VERSION,
        value_count=len(rows),
    )
    return content_hash
