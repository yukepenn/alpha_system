from __future__ import annotations

from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.data.versions import (
    config_hash_for_mapping,
    content_hash_for_rows,
    get_dataset_version,
    make_dataset_version,
    make_source_version,
    record_dataset_version,
)


def test_data_and_source_versions_are_deterministic() -> None:
    rows = (
        {"instrument_id": "SYNTH-1", "bar_index": 0},
        {"instrument_id": "SYNTH-1", "bar_index": 1},
    )
    config = {"frequency": "1min", "latency_seconds": 5}
    content_hash = content_hash_for_rows(rows)
    config_hash = config_hash_for_mapping(config)
    source = make_source_version(
        "synthetic",
        "fixture",
        content_hash=content_hash,
        created_at="2026-01-02T14:31:00Z",
        metadata={"purpose": "correctness"},
    )

    first = make_dataset_version(
        "synthetic_1min",
        content_hash=content_hash,
        config_hash=config_hash,
        source_version=source.source_version,
        created_at="2026-01-02T14:31:05Z",
    )
    second = make_dataset_version(
        "synthetic_1min",
        content_hash=content_hash,
        config_hash=config_hash,
        source_version=source.source_version,
        created_at="2026-01-02T14:31:05Z",
    )

    assert first.data_version == second.data_version
    assert first.metadata["source_version"] == source.source_version
    assert first.data_version.startswith("data:synthetic_1min:")


def test_dataset_version_can_be_recorded_in_temp_registry(tmp_path) -> None:
    registry_path = tmp_path / "registry.sqlite"
    status = init_registry(registry_path)
    assert status.valid

    source = make_source_version(
        "synthetic",
        "fixture",
        content_hash="abc123",
        created_at="2026-01-02T14:31:00Z",
    )
    record = make_dataset_version(
        "synthetic_1min",
        content_hash="abc123",
        config_hash="def456",
        source_version=source.source_version,
        created_at="2026-01-02T14:31:05Z",
        metadata={"fixture": True},
        status_message="synthetic fixture only",
    )

    with connect_registry(registry_path) as connection:
        record_dataset_version(connection, record)
        loaded = get_dataset_version(connection, record.data_version)

    assert loaded == record
