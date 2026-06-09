"""Worker-side contracts for V1 fast feature materialization.

The objects in this module describe completed compute outputs only. They do not
write to the feature registry and do not create feature identity.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alpha_system.core.hashing import hash_config
from alpha_system.features.engine import FeatureMaterializationResult
from alpha_system.governance.serialization import JsonValue, canonical_serialize

FAST_WORKER_MANIFEST_SCHEMA = "alpha_system.features.fast.worker_manifest.v1"
CANONICAL_FEATURE_RECORD_ORDER = (
    "feature_version_id",
    "entity_id",
    "event_ts",
    "available_ts",
)


@dataclass(frozen=True, slots=True)
class FastWorkerManifest:
    """Deterministic, value-free manifest for one worker-computed feature unit."""

    unit_key: Mapping[str, Any]
    parquet_path: str
    content_hash: str
    row_count: int
    feature_version_ids: tuple[str, ...]
    producer_engine_id: str
    value_schema_version: str
    manifest_path: str

    def to_dict(self) -> dict[str, JsonValue]:
        payload: dict[str, Any] = {
            "schema": FAST_WORKER_MANIFEST_SCHEMA,
            "unit_key": dict(self.unit_key),
            "parquet_path": self.parquet_path,
            "content_hash": self.content_hash,
            "row_count": self.row_count,
            "feature_version_ids": list(self.feature_version_ids),
            "producer_engine_id": self.producer_engine_id,
            "value_schema_version": self.value_schema_version,
            "canonical_record_order": list(CANONICAL_FEATURE_RECORD_ORDER),
            "manifest_path": self.manifest_path,
        }
        payload["manifest_hash"] = "sha256:" + hash_config(payload)
        return payload


@dataclass(frozen=True, slots=True)
class FastWorkerUnitOutput:
    """Worker output queued for the single serial registry writer."""

    materialization_result: FeatureMaterializationResult
    feature_set: Any
    feature_request_payloads: Mapping[str, Mapping[str, Any]]
    registry_metadata: Mapping[str, Any]
    manifest: FastWorkerManifest


def worker_manifest_path(
    alpha_data_root: str | Path,
    *,
    checkpoint_root: str | Path,
    unit_id: str,
) -> Path:
    """Return the local-only manifest path for one worker-computed unit."""

    return Path(alpha_data_root) / Path(checkpoint_root) / "worker_manifests" / f"{unit_id}.json"


def write_worker_manifest(path: str | Path, manifest: FastWorkerManifest) -> None:
    """Write one deterministic worker manifest atomically enough for local resume."""

    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        canonical_serialize(manifest.to_dict()) + "\n",
        encoding="utf-8",
    )


def feature_request_payloads(
    requests: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    """Return JSON-compatible checked FeatureRequest payloads by feature id."""

    payloads: dict[str, Mapping[str, Any]] = {}
    for feature_id, request in requests.items():
        if hasattr(request, "to_dict"):
            payload = request.to_dict()
        elif isinstance(request, Mapping):
            payload = dict(request)
        else:
            raise TypeError(f"feature request for {feature_id} is not serializable")
        payloads[str(feature_id)] = payload
    return payloads


def worker_manifest_from_result(
    *,
    unit_key: Mapping[str, Any],
    result: FeatureMaterializationResult,
    feature_version_ids: Sequence[str],
    producer_engine_id: str,
    value_schema_version: str,
    manifest_path: str | Path,
) -> FastWorkerManifest:
    """Build the deterministic manifest for a finished worker result."""

    handle = result.value_store_handle
    if handle is None or not handle.parquet_path or not handle.content_hash:
        raise ValueError("worker result requires a Parquet value-store handle")
    return FastWorkerManifest(
        unit_key=dict(unit_key),
        parquet_path=str(handle.parquet_path),
        content_hash=str(handle.content_hash),
        row_count=int(handle.value_count),
        feature_version_ids=tuple(str(value) for value in feature_version_ids),
        producer_engine_id=producer_engine_id,
        value_schema_version=value_schema_version,
        manifest_path=str(manifest_path),
    )


__all__ = [
    "CANONICAL_FEATURE_RECORD_ORDER",
    "FAST_WORKER_MANIFEST_SCHEMA",
    "FastWorkerManifest",
    "FastWorkerUnitOutput",
    "feature_request_payloads",
    "worker_manifest_from_result",
    "worker_manifest_path",
    "write_worker_manifest",
]
