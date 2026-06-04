"""Dataset-version adapter for the local SQLite metadata registry.

DATA-P17 reuses the existing ``dataset_versions`` table. The table's
``data_version`` key stores ``DatasetVersion.dataset_version_id`` and
``metadata_json`` stores the complete DATA-P17 object for lossless round trips.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from pathlib import Path

from alpha_system.core.hashing import canonical_json
from alpha_system.core.registry import (
    connect_registry,
    init_registry,
    is_local_only_registry_path,
    resolve_registry_path,
)
from alpha_system.data.foundation.datasets import CoverageReport, DataQualityReport, DatasetVersion
from alpha_system.data.foundation.sources import DataFoundationValidationError

DATASET_VERSION_REGISTRY_METADATA_SCHEMA = (
    "alpha_system.data_foundation.dataset_version.v1"
)


def _require_dataset_version(record: object) -> DatasetVersion:
    if not isinstance(record, DatasetVersion):
        msg = "dataset version registry writes require a DatasetVersion"
        raise DataFoundationValidationError(msg)
    return record


def _normalize_dataset_version_id(value: object) -> str:
    if not isinstance(value, str):
        msg = "dataset_version_id must be a non-empty string"
        raise DataFoundationValidationError(msg)
    dataset_version_id = value.strip()
    if not dataset_version_id:
        msg = "dataset_version_id must be a non-empty string"
        raise DataFoundationValidationError(msg)
    if "\n" in dataset_version_id or "\r" in dataset_version_id:
        msg = "dataset_version_id must be a single-line string"
        raise DataFoundationValidationError(msg)
    if not dataset_version_id.replace("_", "").replace("-", "").isalnum():
        msg = "dataset_version_id must be an alphanumeric identifier"
        raise DataFoundationValidationError(msg)
    return dataset_version_id


def _registry_dataset_name(record: DatasetVersion) -> str:
    symbols = ",".join(record.symbol_universe)
    return f"{record.source}:{symbols}:{record.bar_size}:{record.what_to_show}"


def _registry_metadata_json(record: DatasetVersion) -> str:
    return canonical_json(
        {
            "schema": DATASET_VERSION_REGISTRY_METADATA_SCHEMA,
            "dataset_version": record.to_mapping(),
        }
    )


def _ensure_registry_ready(registry_path: str | Path) -> Path:
    resolved = resolve_registry_path(registry_path)
    if not is_local_only_registry_path(resolved):
        msg = "dataset version registry path is not local-only"
        raise DataFoundationValidationError(msg)

    status = init_registry(resolved)
    if not status.valid:
        msg = "dataset version registry is not ready: " + status.status_message
        raise DataFoundationValidationError(msg)
    return resolved


def persist_dataset_version(
    registry_path: str | Path,
    record: DatasetVersion,
    *,
    quality_report: DataQualityReport | None,
    coverage_report: CoverageReport | None,
    source_manifest: object,
    code_hash: object,
    config_hash: object,
) -> None:
    """Persist one VERSIONED-eligible DatasetVersion and reject duplicates."""

    dataset_version = _require_dataset_version(record)
    dataset_version.require_versioned_prerequisites(
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest=source_manifest,
        code_hash=code_hash,
        config_hash=config_hash,
    )
    resolved = _ensure_registry_ready(registry_path)

    with connect_registry(resolved) as connection:
        existing = connection.execute(
            """
            SELECT 1
            FROM dataset_versions
            WHERE data_version = ?
            """,
            (dataset_version.dataset_version_id,),
        ).fetchone()
        if existing is not None:
            msg = (
                "dataset_version_id already exists in registry: "
                f"{dataset_version.dataset_version_id}"
            )
            raise DataFoundationValidationError(msg)

        try:
            connection.execute(
                """
                INSERT INTO dataset_versions (
                    data_version,
                    dataset_name,
                    created_at,
                    source_uri,
                    content_hash,
                    config_hash,
                    metadata_json,
                    status_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dataset_version.dataset_version_id,
                    _registry_dataset_name(dataset_version),
                    dataset_version.created_at.isoformat(),
                    dataset_version.source,
                    dataset_version.manifest_hash,
                    dataset_version.config_hash,
                    _registry_metadata_json(dataset_version),
                    "DATA-P17 dataset version registry record",
                ),
            )
        except sqlite3.IntegrityError as exc:
            msg = (
                "dataset_version_id already exists in registry: "
                f"{dataset_version.dataset_version_id}"
            )
            raise DataFoundationValidationError(msg) from exc


def resolve_dataset_version(
    registry_path: str | Path,
    dataset_version_id: object,
) -> DatasetVersion | None:
    """Resolve a DatasetVersion by ID from the initialized metadata registry."""

    dataset_id = _normalize_dataset_version_id(dataset_version_id)
    resolved = _ensure_registry_ready(registry_path)

    with connect_registry(resolved, read_only=True) as connection:
        row = connection.execute(
            """
            SELECT
                data_version,
                dataset_name,
                created_at,
                source_uri,
                content_hash,
                config_hash,
                metadata_json,
                status_message
            FROM dataset_versions
            WHERE data_version = ?
            """,
            (dataset_id,),
        ).fetchone()

    if row is None:
        return None
    return _dataset_version_from_registry_row(row)


def _dataset_version_from_registry_row(row: Mapping[str, object]) -> DatasetVersion:
    try:
        payload = json.loads(str(row["metadata_json"]))
    except (KeyError, json.JSONDecodeError) as exc:
        msg = "dataset version registry metadata_json is not valid JSON"
        raise DataFoundationValidationError(msg) from exc

    if not isinstance(payload, Mapping):
        msg = "dataset version registry metadata_json must be a mapping"
        raise DataFoundationValidationError(msg)
    if payload.get("schema") != DATASET_VERSION_REGISTRY_METADATA_SCHEMA:
        msg = "dataset version registry metadata schema is unsupported"
        raise DataFoundationValidationError(msg)

    values = payload.get("dataset_version")
    if not isinstance(values, Mapping):
        msg = "dataset version registry metadata is missing dataset_version"
        raise DataFoundationValidationError(msg)
    record = DatasetVersion.from_mapping(values)

    expected = {
        "data_version": record.dataset_version_id,
        "dataset_name": _registry_dataset_name(record),
        "created_at": record.created_at.isoformat(),
        "source_uri": record.source,
        "content_hash": record.manifest_hash,
        "config_hash": record.config_hash,
    }
    for column_name, expected_value in expected.items():
        actual = str(row[column_name])
        if actual != expected_value:
            msg = (
                "dataset version registry row is mis-bound: "
                f"{column_name} does not match metadata_json"
            )
            raise DataFoundationValidationError(msg)
    return record


__all__ = [
    "DATASET_VERSION_REGISTRY_METADATA_SCHEMA",
    "persist_dataset_version",
    "resolve_dataset_version",
]
