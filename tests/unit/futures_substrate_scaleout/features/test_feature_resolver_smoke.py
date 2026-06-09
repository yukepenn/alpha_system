from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from alpha_system.core.value_store import (
    compute_value_content_hash,
    parquet_is_current,
    write_parquet_values,
)
from alpha_system.runtime.input_resolver import (
    FeatureLabelPackResolver,
    RuntimeInputResolverError,
)

DATASET_VERSION_ID = "dsv_databento_ohlcv_dense_2024_v1"
FEATURE_REQUEST_ID = "freq_eb180e1226ce34c048c7e6eb"
FEATURE_VERSION_ID = "fver_" + "a" * 64
PARTITION_ID = "ES_2024_full_year"
BASE_TS = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)


def test_feature_resolver_smoke_resolves_exact_lock_to_current_parquet(
    tmp_path: Path,
) -> None:
    pytest.importorskip("polars")
    records = (
        {
            "feature_version_id": FEATURE_VERSION_ID,
            "event_ts": BASE_TS.isoformat(),
            "available_ts": (BASE_TS + timedelta(seconds=5)).isoformat(),
            "value": {"kind": "value-free-smoke-fixture", "ordinal": 1},
            "quality_flags": [],
        },
    )
    content_hash = compute_value_content_hash(records)
    parquet_path = write_parquet_values(
        records,
        tmp_path / "features.parquet",
        plan_dict={"plan_id": "fmat_feature_resolver_smoke_fixture"},
        content_hash=content_hash,
        schema_version="alpha_system.features.fast.values.v1",
        value_count=len(records),
    )
    record = _FeatureRecord(
        parquet_path=parquet_path.as_posix(),
        value_content_hash=content_hash,
    )
    resolver = FeatureLabelPackResolver(
        feature_store=_FeatureStore({FEATURE_VERSION_ID: record})
    )

    handles = resolver.resolve_feature_packs(
        (FEATURE_VERSION_ID,),
        expected_dataset_version_id=DATASET_VERSION_ID,
        expected_feature_request_ids=(FEATURE_REQUEST_ID,),
        partition_id=PARTITION_ID,
    )

    assert len(handles) == 1
    assert handles[0].feature_version_id == FEATURE_VERSION_ID
    assert handles[0].dataset_version_id == DATASET_VERSION_ID
    assert handles[0].feature_request_id == FEATURE_REQUEST_ID
    assert handles[0].partition_id == PARTITION_ID
    assert handles[0].available_ts == (
        (BASE_TS + timedelta(seconds=5)).isoformat(),
        (BASE_TS + timedelta(minutes=1, seconds=5)).isoformat(),
    )
    assert parquet_is_current(parquet_path, content_hash) is True


def test_feature_resolver_smoke_fails_closed_for_absent_lock() -> None:
    resolver = FeatureLabelPackResolver(feature_store=_FeatureStore({}))

    with pytest.raises(RuntimeInputResolverError) as exc_info:
        resolver.resolve_feature_packs(
            (FEATURE_VERSION_ID,),
            expected_dataset_version_id=DATASET_VERSION_ID,
            expected_feature_request_ids=(),
            partition_id=PARTITION_ID,
        )

    assert exc_info.value.reason.code == "feature_pack_not_found"


def test_session_label_with_registry_session_metadata_role_is_metadata() -> None:
    resolver = FeatureLabelPackResolver(
        feature_store=_FeatureStore({FEATURE_VERSION_ID: _FeatureRecord()})
    )

    handles = resolver.resolve_feature_packs(
        (FEATURE_VERSION_ID,),
        expected_dataset_version_id=DATASET_VERSION_ID,
        expected_feature_request_ids=(FEATURE_REQUEST_ID,),
        partition_id=PARTITION_ID,
    )

    assert handles[0].feature_version_id == FEATURE_VERSION_ID


def test_session_label_without_registry_session_metadata_role_fails_closed() -> None:
    record = _FeatureRecord(
        registry_metadata={
            "family": "session_calendar_maintenance",
            "producer_engine_id": "alpha_system.features.fast.pack_materializer.v1",
        }
    )
    resolver = FeatureLabelPackResolver(feature_store=_FeatureStore({FEATURE_VERSION_ID: record}))

    with pytest.raises(RuntimeInputResolverError) as exc_info:
        resolver.resolve_feature_packs(
            (FEATURE_VERSION_ID,),
            expected_dataset_version_id=DATASET_VERSION_ID,
            expected_feature_request_ids=(FEATURE_REQUEST_ID,),
            partition_id=PARTITION_ID,
        )

    assert exc_info.value.reason.code == "label_as_feature_input"


@dataclass(frozen=True, slots=True)
class _Inputs:
    fields: tuple[str, ...] = ("close", "session_label", "available_ts")
    input_views: tuple[str, ...] = ("canonical_ohlcv",)
    input_metadata: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class _FeatureSpec:
    feature_request_id: str = FEATURE_REQUEST_ID
    live: bool = True
    inputs: _Inputs = _Inputs()


@dataclass(frozen=True, slots=True)
class _FeatureRecord:
    feature_version_id: str = FEATURE_VERSION_ID
    feature_request_id: str = FEATURE_REQUEST_ID
    feature_set_id: str = "feature_set_futures_scaleout_session_calendar_maintenance"
    feature_set_version: str = "v1_es_2024"
    dataset_version_id: str = DATASET_VERSION_ID
    partition_id: str = PARTITION_ID
    materialization_plan_id: str = "fmat_feature_resolver_smoke_fixture"
    first_event_ts: datetime = BASE_TS
    last_event_ts: datetime = BASE_TS + timedelta(minutes=1)
    first_available_ts: datetime = BASE_TS + timedelta(seconds=5)
    last_available_ts: datetime = BASE_TS + timedelta(minutes=1, seconds=5)
    lifecycle_state: str = "REGISTERED"
    feature_spec: _FeatureSpec = _FeatureSpec()
    parquet_path: str = ""
    value_content_hash: str = ""
    registry_metadata: dict[str, object] | None = None

    def __post_init__(self) -> None:
        if self.registry_metadata is None:
            object.__setattr__(
                self,
                "registry_metadata",
                {
                    "family": "session_calendar_maintenance",
                    "producer_engine_id": "alpha_system.features.fast.pack_materializer.v1",
                    "session_metadata_role": "SESSION_METADATA_POINT_IN_TIME",
                },
            )


class _FeatureStore:
    def __init__(self, records: dict[str, _FeatureRecord]) -> None:
        self.records = records

    def resolve_feature_by_version(self, feature_version_id: str) -> _FeatureRecord | None:
        return self.records.get(feature_version_id)
