from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from alpha_system.data.foundation import (
    RawDataLakeLayoutPolicy,
    RawDataObject,
    assert_raw_slot_immutable,
    raw_object_ref_for_content_hash,
    require_raw_data_lake_layout_policy,
    resolve_raw_object_storage_path,
)
from alpha_system.data.foundation.sources import (
    DEFAULT_ALLOWED_SUBDIRS,
    DEFAULT_FORBIDDEN_REPO_PATHS,
    DEFAULT_MAX_FILE_POLICY,
    DataFoundationValidationError,
    LocalDataRootPolicy,
)

RETRIEVED_AT = datetime(2026, 6, 3, 21, 52, 49, tzinfo=UTC)
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64


def _outside_repo_root(name: str = "alpha_system_raw_unit_root") -> Path:
    return Path.home() / "alpha_data" / name


def _local_policy(root: Path | str | None = None, **overrides: object) -> LocalDataRootPolicy:
    fields: dict[str, object] = {
        "data_root": root or _outside_repo_root(),
        "must_be_local": True,
        "must_be_ignored": True,
        "forbidden_repo_paths": DEFAULT_FORBIDDEN_REPO_PATHS,
        "allowed_subdirs": DEFAULT_ALLOWED_SUBDIRS,
        "max_file_policy": DEFAULT_MAX_FILE_POLICY,
    }
    fields.update(overrides)
    return LocalDataRootPolicy(**fields)


def _layout(root_name: str = "alpha_system_raw_unit_root") -> RawDataLakeLayoutPolicy:
    return RawDataLakeLayoutPolicy(
        local_data_root_policy=_local_policy(_outside_repo_root(root_name))
    )


def _raw_values(
    layout: RawDataLakeLayoutPolicy,
    *,
    content_hash: str = HASH_A,
    **overrides: object,
) -> dict[str, object]:
    values: dict[str, object] = {
        "raw_object_id": "raw_synth_es_20250102_a",
        "source": "dsrc_ibkr_historical",
        "request_id": "hrs_synthetic_es_h5_20250102_20250103",
        "chunk_id": "hchunk_synth_es_20250102_a",
        "path": layout.resolve_path(
            source="dsrc_ibkr_historical",
            request_id="hrs_synthetic_es_h5_20250102_20250103",
            chunk_id="hchunk_synth_es_20250102_a",
            content_hash=content_hash,
        ).as_posix(),
        "content_hash": content_hash,
        "schema_hint": "ibkr_historical_bars_raw_v1",
        "retrieved_at": RETRIEVED_AT.isoformat(),
        "row_count": 10,
    }
    values.update(overrides)
    return values


def test_raw_layout_resolves_content_addressed_path_under_alpha_data_root() -> None:
    layout = _layout("alpha_system_raw_layout")

    path = resolve_raw_object_storage_path(
        layout_policy=layout,
        source="dsrc_ibkr_historical",
        request_id="hrs_synthetic_es_h5_20250102_20250103",
        chunk_id="hchunk_synth_es_20250102_a",
        content_hash=HASH_A,
    )

    assert path.is_relative_to(layout.local_data_root_policy.data_root)
    assert path.parts[-6:] == (
        "raw",
        "source=dsrc_ibkr_historical",
        "request=hrs_synthetic_es_h5_20250102_20250103",
        "chunk=hchunk_synth_es_20250102_a",
        "sha256=aa",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.raw",
    )
    assert raw_object_ref_for_content_hash(HASH_A) == "raw://sha256/" + "a" * 64
    assert require_raw_data_lake_layout_policy(layout) is layout
    with pytest.raises(DataFoundationValidationError, match="missing RawDataLakeLayoutPolicy"):
        require_raw_data_lake_layout_policy(None)


def test_raw_data_object_validates_required_fields_and_mapping_round_trip() -> None:
    layout = _layout("alpha_system_raw_round_trip")
    raw_object = RawDataObject.from_mapping(_raw_values(layout), layout_policy=layout)

    persisted = raw_object.to_mapping()

    assert raw_object.content_hash == HASH_A
    assert raw_object.raw_object_ref == "raw://sha256/" + "a" * 64
    assert raw_object.logical_slot == (
        "dsrc_ibkr_historical",
        "hrs_synthetic_es_h5_20250102_20250103",
        "hchunk_synth_es_20250102_a",
    )
    assert persisted["path"] == raw_object.path.as_posix()
    assert RawDataObject.from_mapping(persisted, layout_policy=layout) == raw_object

    missing = dict(persisted)
    del missing["chunk_id"]
    with pytest.raises(DataFoundationValidationError, match="missing required fields"):
        RawDataObject.from_mapping(missing, layout_policy=layout)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "match"),
    [
        ("raw_object_id", "", "non-empty"),
        ("source", "ibkr", "dsrc_"),
        ("request_id", "hrs/synthetic", "identifier"),
        ("chunk_id", "", "non-empty"),
        ("content_hash", "raw://sha256/" + "a" * 64, "content_hash"),
        ("content_hash", "sha256:" + "g" * 64, "content_hash"),
        ("schema_hint", "canonical_truth", "canonical truth"),
        ("retrieved_at", "2026-06-03T21:52:49", "timezone"),
        ("row_count", -1, "non-negative"),
        ("row_count", True, "non-negative"),
    ],
)
def test_raw_data_object_rejects_invalid_fields(
    field_name: str,
    bad_value: object,
    match: str,
) -> None:
    layout = _layout(f"alpha_system_raw_bad_{field_name}")

    with pytest.raises(DataFoundationValidationError, match=match):
        RawDataObject.from_mapping(
            _raw_values(layout, **{field_name: bad_value}),
            layout_policy=layout,
        )


def test_raw_data_object_rejects_repo_synced_and_wrong_local_paths() -> None:
    layout = _layout("alpha_system_raw_path_enforcement")
    repo_root = Path(__file__).resolve().parents[3]

    with pytest.raises(DataFoundationValidationError, match="outside the repository"):
        _local_policy(repo_root / "data" / "raw")
    with pytest.raises(DataFoundationValidationError, match="forbidden synced"):
        _local_policy(Path.home() / "OneDrive" / "alpha_data")

    wrong_root = _outside_repo_root("alpha_system_raw_other_root")
    wrong_path = (
        wrong_root
        / "raw"
        / "source=dsrc_ibkr_historical"
        / "request=hrs_synthetic_es_h5_20250102_20250103"
        / "chunk=hchunk_synth_es_20250102_a"
        / "sha256=aa"
        / ("a" * 64 + ".raw")
    )
    with pytest.raises(DataFoundationValidationError, match="ALPHA_DATA_ROOT"):
        RawDataObject.from_mapping(
            _raw_values(layout, path=wrong_path.as_posix()),
            layout_policy=layout,
        )

    missing_link = (
        layout.local_data_root_policy.data_root
        / "raw"
        / "source=dsrc_ibkr_historical"
        / "request=hrs_synthetic_es_h5_20250102_20250103"
        / "sha256=aa"
        / ("a" * 64 + ".raw")
    )
    with pytest.raises(DataFoundationValidationError, match="source/request/chunk"):
        RawDataObject.from_mapping(
            _raw_values(layout, path=missing_link.as_posix()),
            layout_policy=layout,
        )


def test_raw_object_create_requires_request_chunk_links_and_policy() -> None:
    layout = _layout("alpha_system_raw_create")

    raw_object = RawDataObject.create(
        raw_object_id="raw_synth_es_20250102_a",
        source="dsrc_ibkr_historical",
        request_id="hrs_synthetic_es_h5_20250102_20250103",
        chunk_id="hchunk_synth_es_20250102_a",
        content_hash=HASH_A,
        schema_hint="ibkr_historical_bars_raw_v1",
        retrieved_at=RETRIEVED_AT,
        row_count=10,
        layout_policy=layout,
    )

    assert raw_object.path == layout.resolve_path(
        source=raw_object.source,
        request_id=raw_object.request_id,
        chunk_id=raw_object.chunk_id,
        content_hash=raw_object.content_hash,
    )
    with pytest.raises(DataFoundationValidationError, match="non-empty"):
        RawDataObject.create(
            raw_object_id="raw_synth_es_20250102_b",
            source="dsrc_ibkr_historical",
            request_id="",
            chunk_id="hchunk_synth_es_20250102_b",
            content_hash=HASH_A,
            schema_hint="ibkr_historical_bars_raw_v1",
            retrieved_at=RETRIEVED_AT,
            row_count=10,
            layout_policy=layout,
        )
    with pytest.raises(DataFoundationValidationError, match="missing RawDataLakeLayoutPolicy"):
        RawDataObject.create(
            raw_object_id="raw_synth_es_20250102_c",
            source="dsrc_ibkr_historical",
            request_id="hrs_synthetic_es_h5_20250102_20250103",
            chunk_id="hchunk_synth_es_20250102_c",
            content_hash=HASH_A,
            schema_hint="ibkr_historical_bars_raw_v1",
            retrieved_at=RETRIEVED_AT,
            row_count=10,
            layout_policy=None,  # type: ignore[arg-type]
        )


def test_raw_slot_immutability_guard_rejects_different_hash_for_same_slot() -> None:
    layout = _layout("alpha_system_raw_immutable")
    existing = RawDataObject.from_mapping(_raw_values(layout), layout_policy=layout)
    same_content = RawDataObject.from_mapping(_raw_values(layout), layout_policy=layout)
    different_hash_same_slot = RawDataObject.from_mapping(
        _raw_values(layout, content_hash=HASH_B),
        layout_policy=layout,
    )
    different_slot = RawDataObject.from_mapping(
        _raw_values(
            layout,
            content_hash=HASH_B,
            chunk_id="hchunk_synth_es_20250103_b",
            path=layout.resolve_path(
                source="dsrc_ibkr_historical",
                request_id="hrs_synthetic_es_h5_20250102_20250103",
                chunk_id="hchunk_synth_es_20250103_b",
                content_hash=HASH_B,
            ).as_posix(),
        ),
        layout_policy=layout,
    )

    assert assert_raw_slot_immutable(None, existing) == existing
    assert assert_raw_slot_immutable(existing, same_content) == existing
    assert assert_raw_slot_immutable(existing, different_slot) == different_slot
    with pytest.raises(DataFoundationValidationError, match="immutable"):
        assert_raw_slot_immutable(existing, different_hash_same_slot)
