"""Shared value-store helpers for feature and label value records."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from alpha_system.core.hashing import hash_text
from alpha_system.data.storage import (
    DataDependencyError,
    dependency_available,
    require_dependency,
)
from alpha_system.governance.serialization import canonical_serialize


class ValueStoreFormat(StrEnum):
    """Supported low-level materialized value storage formats."""

    JSONL = "jsonl"
    PARQUET = "parquet"
    DUAL = "dual"


@dataclass(frozen=True, slots=True)
class ValueStoreHandle:
    """Metadata describing the concrete value store emitted by a materialization."""

    format: ValueStoreFormat
    jsonl_path: str | None
    parquet_path: str | None
    value_count: int
    content_hash: str
    schema_version: str
    dataset_version_id: str
    set_id: str
    partition_id: str
    min_event_ts: str
    max_event_ts: str
    min_available_ts: str
    max_available_ts: str

    def to_dict(self) -> dict[str, str | int | None]:
        """Return a plain JSON-compatible value-store handle payload."""

        return {
            "format": self.format.value,
            "jsonl_path": self.jsonl_path,
            "parquet_path": self.parquet_path,
            "value_count": self.value_count,
            "content_hash": self.content_hash,
            "schema_version": self.schema_version,
            "dataset_version_id": self.dataset_version_id,
            "set_id": self.set_id,
            "partition_id": self.partition_id,
            "min_event_ts": self.min_event_ts,
            "max_event_ts": self.max_event_ts,
            "min_available_ts": self.min_available_ts,
            "max_available_ts": self.max_available_ts,
        }


def compute_value_content_hash(record_dicts: Sequence[Mapping[str, Any]]) -> str:
    """Hash canonical value record dictionaries independent of storage format."""

    payload = [dict(record) for record in record_dicts]
    return f"sha256:{hash_text(canonical_serialize(payload))}"


def write_parquet_values(
    record_dicts: Sequence[Mapping[str, Any]],
    path: str | Path,
    *,
    plan_dict: Mapping[str, Any],
    content_hash: str,
    schema_version: str,
    value_count: int,
) -> Path:
    """Write value records as Parquet plus a sidecar manifest."""

    polars = require_dependency("polars")
    output_path = Path(path).expanduser().resolve(strict=False)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [_parquet_row(record) for record in record_dicts]

    with NamedTemporaryFile(
        "wb",
        dir=output_path.parent,
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)
    try:
        polars.DataFrame(rows).write_parquet(temp_path.as_posix())
        temp_path.replace(output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    manifest = {
        "schema": schema_version,
        "plan": dict(plan_dict),
        "content_hash": content_hash,
        "value_count": value_count,
    }
    _write_manifest_atomic(output_path, manifest)
    return output_path


def load_parquet_values(path: str | Path) -> list[dict[str, Any]]:
    """Read Parquet value rows and reconstruct original record dictionaries."""

    polars = require_dependency("polars")
    frame = polars.read_parquet(Path(path).expanduser().resolve(strict=False).as_posix())
    records: list[dict[str, Any]] = []
    for row in frame.to_dicts():
        value_json = row.pop("value_json", None)
        flags_json = row.pop("quality_flags_json", None)
        if not isinstance(value_json, str):
            raise ValueError("Parquet value row is missing value_json")
        row["value"] = json.loads(value_json)
        if flags_json is not None:
            if not isinstance(flags_json, str):
                raise ValueError("Parquet value row has invalid quality_flags_json")
            row["quality_flags"] = json.loads(flags_json)
        records.append(row)
    return records


def read_parquet_manifest(path: str | Path) -> dict[str, Any]:
    """Read the JSON sidecar manifest for a Parquet value store."""

    manifest_path = _manifest_path(path)
    with manifest_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Parquet value manifest must be a JSON object")
    return payload


def parquet_is_current(path: str | Path, content_hash: str) -> bool:
    """Return whether a Parquet value store sidecar matches the content hash."""

    try:
        return read_parquet_manifest(path).get("content_hash") == content_hash
    except (OSError, ValueError, json.JSONDecodeError):
        return False


def _parquet_row(record: Mapping[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for key, value in record.items():
        if key == "value":
            row["value_json"] = canonical_serialize(value)
            continue
        if key == "quality_flags":
            row["quality_flags_json"] = canonical_serialize(value)
            continue
        if not _is_scalar(value):
            raise ValueError(f"Parquet value record field must be scalar: {key}")
        row[str(key)] = value
    if "value_json" not in row:
        raise ValueError("value record must include a value field")
    return row


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, bool | int | float | str)


def _manifest_path(path: str | Path) -> Path:
    return Path(str(Path(path).expanduser().resolve(strict=False)) + ".manifest.json")


def _write_manifest_atomic(path: Path, manifest: Mapping[str, Any]) -> None:
    manifest_path = _manifest_path(path)
    payload = canonical_serialize(manifest) + "\n"
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=manifest_path.parent,
        prefix=f".{manifest_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)
        handle.write(payload)
    temp_path.replace(manifest_path)


__all__ = [
    "DataDependencyError",
    "ValueStoreFormat",
    "ValueStoreHandle",
    "compute_value_content_hash",
    "dependency_available",
    "parquet_is_current",
    "read_parquet_manifest",
    "load_parquet_values",
    "require_dependency",
    "write_parquet_values",
]
