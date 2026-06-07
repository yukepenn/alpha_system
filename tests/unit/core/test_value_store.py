from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.core.value_store import (
    DataDependencyError,
    ValueStoreFormat,
    ValueStoreHandle,
    compute_value_content_hash,
    load_parquet_values,
    parquet_is_current,
    read_parquet_manifest,
    require_dependency,
    write_parquet_values,
)


def test_value_store_format_values() -> None:
    assert ValueStoreFormat.JSONL.value == "jsonl"
    assert ValueStoreFormat.PARQUET.value == "parquet"
    assert ValueStoreFormat.DUAL.value == "dual"


def test_compute_value_content_hash_is_deterministic_and_format_agnostic() -> None:
    records = [
        {
            "feature_version_id": "fver_" + "0" * 64,
            "entity_id": "ES",
            "event_ts": "2024-01-02T14:31:00+00:00",
            "available_ts": "2024-01-02T14:31:01+00:00",
            "value": {"nested": [1, "2"]},
            "quality_flags": ["missing_bbo"],
        }
    ]

    first = compute_value_content_hash(records)
    second = compute_value_content_hash([dict(records[0])])

    assert first == second
    assert first.startswith("sha256:")


def test_value_store_handle_to_dict() -> None:
    handle = ValueStoreHandle(
        format=ValueStoreFormat.DUAL,
        jsonl_path="/tmp/values.jsonl",
        parquet_path="/tmp/values.parquet",
        value_count=2,
        content_hash="sha256:" + "a" * 64,
        schema_version="schema.v1",
        dataset_version_id="dsv_fixture",
        set_id="set_fixture",
        partition_id="development_partition",
        min_event_ts="2024-01-02T14:31:00+00:00",
        max_event_ts="2024-01-02T14:32:00+00:00",
        min_available_ts="2024-01-02T14:31:01+00:00",
        max_available_ts="2024-01-02T14:32:01+00:00",
    )

    assert handle.to_dict() == {
        "format": "dual",
        "jsonl_path": "/tmp/values.jsonl",
        "parquet_path": "/tmp/values.parquet",
        "value_count": 2,
        "content_hash": "sha256:" + "a" * 64,
        "schema_version": "schema.v1",
        "dataset_version_id": "dsv_fixture",
        "set_id": "set_fixture",
        "partition_id": "development_partition",
        "min_event_ts": "2024-01-02T14:31:00+00:00",
        "max_event_ts": "2024-01-02T14:32:00+00:00",
        "min_available_ts": "2024-01-02T14:31:01+00:00",
        "max_available_ts": "2024-01-02T14:32:01+00:00",
    }


def test_missing_dependency_guard_is_actionable_without_polars() -> None:
    with pytest.raises(DataDependencyError, match="definitely_missing_pkg is required"):
        require_dependency("definitely_missing_pkg")

    assert compute_value_content_hash([{"value": 1}]).startswith("sha256:")


def test_parquet_values_round_trip_and_manifest(tmp_path: Path) -> None:
    pytest.importorskip("polars")
    records = [
        {
            "feature_version_id": "fver_" + "1" * 64,
            "entity_id": "ES",
            "event_ts": "2024-01-02T14:31:00+00:00",
            "available_ts": "2024-01-02T14:31:01+00:00",
            "value": {"mixed": [1, "two", {"three": 3}]},
            "quality_flags": ["missing_bbo", "bbo_quarantined"],
        },
        {
            "feature_version_id": "fver_" + "1" * 64,
            "entity_id": "NQ",
            "event_ts": "2024-01-02T14:32:00+00:00",
            "available_ts": "2024-01-02T14:32:01+00:00",
            "value": 1.25,
            "quality_flags": [],
        },
    ]
    content_hash = compute_value_content_hash(records)
    path = tmp_path / "values.parquet"

    written = write_parquet_values(
        records,
        path,
        plan_dict={"plan_id": "plan_fixture"},
        content_hash=content_hash,
        schema_version="schema.v1",
        value_count=len(records),
    )

    assert written == path.resolve(strict=False)
    assert load_parquet_values(path) == records
    assert read_parquet_manifest(path) == {
        "schema": "schema.v1",
        "plan": {"plan_id": "plan_fixture"},
        "content_hash": content_hash,
        "value_count": 2,
    }
    assert parquet_is_current(path, content_hash) is True
    assert parquet_is_current(path, "sha256:" + "0" * 64) is False
