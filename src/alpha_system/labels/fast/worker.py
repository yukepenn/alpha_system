"""Worker-side contracts for V1 fast label materialization.

The objects in this module describe completed compute outputs only. They do not
write to the label registry and do not create label identity.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alpha_system.core.hashing import hash_config
from alpha_system.governance.serialization import JsonValue, canonical_serialize
from alpha_system.labels.engine import LabelMaterializationResult

FAST_LABEL_WORKER_MANIFEST_SCHEMA = "alpha_system.labels.fast.worker_manifest.v1"
CANONICAL_LABEL_RECORD_ORDER = (
    "label_version_id",
    "entity_id",
    "event_ts",
    "horizon_end_ts",
    "label_available_ts",
)


@dataclass(frozen=True, slots=True)
class FastLabelWorkerManifest:
    """Deterministic, value-free manifest for one worker-computed label unit."""

    unit_key: Mapping[str, Any]
    parquet_path: str
    content_hash: str
    row_count: int
    label_version_ids: tuple[str, ...]
    producer_engine_id: str
    value_schema_version: str
    manifest_path: str

    def to_dict(self) -> dict[str, JsonValue]:
        payload: dict[str, Any] = {
            "schema": FAST_LABEL_WORKER_MANIFEST_SCHEMA,
            "unit_key": dict(self.unit_key),
            "parquet_path": self.parquet_path,
            "content_hash": self.content_hash,
            "row_count": self.row_count,
            "label_version_ids": list(self.label_version_ids),
            "producer_engine_id": self.producer_engine_id,
            "value_schema_version": self.value_schema_version,
            "canonical_record_order": list(CANONICAL_LABEL_RECORD_ORDER),
            "manifest_path": self.manifest_path,
        }
        payload["manifest_hash"] = "sha256:" + hash_config(payload)
        return payload


@dataclass(frozen=True, slots=True)
class FastLabelWorkerUnitOutput:
    """Worker output queued for the single serial label-registry writer."""

    materialization_result: LabelMaterializationResult
    pack: Any
    registry_metadata: Mapping[str, Any]
    manifest: FastLabelWorkerManifest


def label_worker_manifest_path(
    alpha_data_root: str | Path,
    *,
    checkpoint_root: str | Path,
    unit_id: str,
) -> Path:
    """Return the local-only manifest path for one worker-computed label unit."""

    return Path(alpha_data_root) / Path(checkpoint_root) / "worker_manifests" / f"{unit_id}.json"


def write_label_worker_manifest(
    path: str | Path,
    manifest: FastLabelWorkerManifest,
) -> None:
    """Write one deterministic label worker manifest for local resume."""

    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        canonical_serialize(manifest.to_dict()) + "\n",
        encoding="utf-8",
    )


def label_worker_manifest_from_result(
    *,
    unit_key: Mapping[str, Any],
    result: LabelMaterializationResult,
    label_version_ids: Sequence[str],
    producer_engine_id: str,
    value_schema_version: str,
    manifest_path: str | Path,
) -> FastLabelWorkerManifest:
    """Build the deterministic manifest for a finished label worker result."""

    handle = result.value_store_handle
    if handle is None or not handle.parquet_path or not handle.content_hash:
        raise ValueError("label worker result requires a Parquet value-store handle")
    return FastLabelWorkerManifest(
        unit_key=dict(unit_key),
        parquet_path=str(handle.parquet_path),
        content_hash=str(handle.content_hash),
        row_count=int(handle.value_count),
        label_version_ids=tuple(str(value) for value in label_version_ids),
        producer_engine_id=producer_engine_id,
        value_schema_version=value_schema_version,
        manifest_path=str(manifest_path),
    )


__all__ = [
    "CANONICAL_LABEL_RECORD_ORDER",
    "FAST_LABEL_WORKER_MANIFEST_SCHEMA",
    "FastLabelWorkerManifest",
    "FastLabelWorkerUnitOutput",
    "label_worker_manifest_from_result",
    "label_worker_manifest_path",
    "write_label_worker_manifest",
]
