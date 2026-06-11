from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from alpha_system.core.value_store import (
    compute_value_content_hash,
    load_parquet_values,
    parquet_is_current,
    read_parquet_manifest,
    write_parquet_values,
)
from alpha_system.runtime.input_resolver import (
    FeatureLabelPackResolver,
    RuntimeInputResolverError,
)

DATASET_VERSION_ID = "dsv_synthetic_label_resolver_smoke"
LABEL_SPEC_ID = "lspec_synthetic_label_resolver_smoke"
LABEL_ID = "fwd_ret_1m"
LABEL_VERSION_ID = "lver_" + "1" * 64
PARTITION_ID = "ES_2024_fwd_ret_1m"
BASE_TS = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)


def test_label_resolver_smoke_resolves_exact_lock_to_current_parquet(
    tmp_path: Path,
) -> None:
    pytest.importorskip("polars")
    records = (
        {
            "label_version_id": LABEL_VERSION_ID,
            "event_ts": BASE_TS.isoformat(),
            "label_available_ts": (BASE_TS + timedelta(minutes=1)).isoformat(),
            "value": {"kind": "synthetic-label-resolver-smoke", "ordinal": 1},
            "quality_flags": [],
        },
    )
    content_hash = compute_value_content_hash(records)
    parquet_path = write_parquet_values(
        records,
        tmp_path / "labels.parquet",
        plan_dict={"plan_id": "lmat_label_resolver_smoke_fixture"},
        content_hash=content_hash,
        schema_version="alpha_system.labels.synthetic.values.v1",
        value_count=len(records),
    )
    record = _LabelRecord(
        parquet_path=parquet_path.as_posix(),
        value_content_hash=content_hash,
    )
    resolver = FeatureLabelPackResolver(label_registry=_LabelRegistry({LABEL_VERSION_ID: record}))

    handles = resolver.resolve_label_packs(
        (LABEL_VERSION_ID,),
        expected_dataset_version_id=DATASET_VERSION_ID,
        expected_label_spec_ids=(LABEL_SPEC_ID,),
        partition_id=PARTITION_ID,
    )

    assert len(handles) == 1
    assert handles[0].label_version_id == LABEL_VERSION_ID
    assert handles[0].label_spec_id == LABEL_SPEC_ID
    assert handles[0].dataset_version_id == DATASET_VERSION_ID
    assert handles[0].partition_id == PARTITION_ID
    assert handles[0].label_available_ts == (
        (BASE_TS + timedelta(minutes=1)).isoformat(),
        (BASE_TS + timedelta(minutes=2)).isoformat(),
    )
    assert record.value_content_hash == content_hash
    assert read_parquet_manifest(parquet_path)["content_hash"] == content_hash
    assert load_parquet_values(parquet_path) == list(records)
    assert parquet_is_current(parquet_path, content_hash) is True


def test_label_resolver_smoke_fails_closed_for_absent_exact_lock() -> None:
    resolver = FeatureLabelPackResolver(label_registry=_LabelRegistry({}))

    with pytest.raises(RuntimeInputResolverError) as exc_info:
        resolver.resolve_label_packs(
            (LABEL_VERSION_ID,),
            expected_dataset_version_id=DATASET_VERSION_ID,
            expected_label_spec_ids=(),
            partition_id=PARTITION_ID,
        )

    assert exc_info.value.reason.code == "label_pack_not_found"


def test_label_resolver_smoke_fails_closed_for_mutated_exact_lock() -> None:
    resolver = FeatureLabelPackResolver(
        label_registry=_LabelRegistry({LABEL_VERSION_ID: _LabelRecord()})
    )
    mutated_label_version_id = "lver_" + "2" * 64

    with pytest.raises(RuntimeInputResolverError) as exc_info:
        resolver.resolve_label_packs(
            (mutated_label_version_id,),
            expected_dataset_version_id=DATASET_VERSION_ID,
            expected_label_spec_ids=(LABEL_SPEC_ID,),
            partition_id=PARTITION_ID,
        )

    assert exc_info.value.reason.code == "label_pack_not_found"


def test_label_resolver_smoke_fails_closed_for_fuzzy_label_name() -> None:
    resolver = FeatureLabelPackResolver(
        label_registry=_LabelRegistry({LABEL_VERSION_ID: _LabelRecord()})
    )

    with pytest.raises(RuntimeInputResolverError) as exc_info:
        resolver.resolve_label_packs(
            (LABEL_ID,),
            expected_dataset_version_id=DATASET_VERSION_ID,
            expected_label_spec_ids=(LABEL_SPEC_ID,),
            partition_id=PARTITION_ID,
        )

    assert exc_info.value.reason.code == "invalid_label_pack_ref"


def test_label_resolver_smoke_fails_closed_for_deprecated_exact_lock() -> None:
    resolver = FeatureLabelPackResolver(
        label_registry=_LabelRegistry(
            {LABEL_VERSION_ID: _LabelRecord(lifecycle_state="DEPRECATED")}
        )
    )

    with pytest.raises(RuntimeInputResolverError) as exc_info:
        resolver.resolve_label_packs(
            (LABEL_VERSION_ID,),
            expected_dataset_version_id=DATASET_VERSION_ID,
            expected_label_spec_ids=(LABEL_SPEC_ID,),
            partition_id=PARTITION_ID,
        )

    assert exc_info.value.reason.code == "label_pack_deprecated"


@dataclass(frozen=True, slots=True)
class _LabelRecord:
    label_version_id: str = LABEL_VERSION_ID
    label_spec_id: str = LABEL_SPEC_ID
    label_id: str = LABEL_ID
    dataset_version_id: str = DATASET_VERSION_ID
    partition_id: str = PARTITION_ID
    materialization_plan_id: str = "lmat_label_resolver_smoke_fixture"
    first_event_ts: datetime = BASE_TS
    last_event_ts: datetime = BASE_TS + timedelta(minutes=1)
    first_label_available_ts: datetime = BASE_TS + timedelta(minutes=1)
    last_label_available_ts: datetime = BASE_TS + timedelta(minutes=2)
    lifecycle_state: str = "REGISTERED"
    parquet_path: str = ""
    value_content_hash: str = ""


class _LabelRegistry:
    def __init__(self, records: dict[str, _LabelRecord]) -> None:
        self.records = records

    def resolve_label_by_version(self, label_version_id: str) -> _LabelRecord | None:
        return self.records.get(label_version_id)
