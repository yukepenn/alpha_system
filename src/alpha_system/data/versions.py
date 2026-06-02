"""Data and source version helpers for canonical datasets."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from alpha_system.core.hashing import canonical_json, hash_config, sha256_hex


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _short_hash(value: str) -> str:
    return value[:12]


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceVersion:
    source_name: str
    source_dataset: str
    content_hash: str
    created_at: str
    metadata: Mapping[str, Any]

    @property
    def source_version(self) -> str:
        payload = {
            "source_dataset": self.source_dataset,
            "source_name": self.source_name,
            "content_hash": self.content_hash,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }
        return f"src:{self.source_name}:{_short_hash(hash_config(payload))}"


@dataclass(frozen=True, slots=True, kw_only=True)
class DatasetVersion:
    data_version: str
    dataset_name: str
    created_at: str
    source_uri: str
    content_hash: str
    config_hash: str
    metadata: Mapping[str, Any]
    status_message: str = ""

    def metadata_json(self) -> str:
        return canonical_json(self.metadata)


def make_source_version(
    source_name: str,
    source_dataset: str,
    *,
    content_hash: str,
    created_at: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> SourceVersion:
    return SourceVersion(
        source_name=source_name,
        source_dataset=source_dataset,
        content_hash=content_hash,
        created_at=created_at or _utc_now_iso(),
        metadata={} if metadata is None else dict(metadata),
    )


def derive_data_version(
    dataset_name: str,
    *,
    content_hash: str,
    config_hash: str,
    source_version: str,
) -> str:
    payload = {
        "config_hash": config_hash,
        "content_hash": content_hash,
        "dataset_name": dataset_name,
        "source_version": source_version,
    }
    return f"data:{dataset_name}:{_short_hash(hash_config(payload))}"


def make_dataset_version(
    dataset_name: str,
    *,
    content_hash: str,
    config_hash: str,
    source_version: str,
    source_uri: str = "",
    created_at: str | None = None,
    metadata: Mapping[str, Any] | None = None,
    status_message: str = "",
) -> DatasetVersion:
    combined_metadata = dict(metadata or {})
    combined_metadata["source_version"] = source_version
    return DatasetVersion(
        data_version=derive_data_version(
            dataset_name,
            content_hash=content_hash,
            config_hash=config_hash,
            source_version=source_version,
        ),
        dataset_name=dataset_name,
        created_at=created_at or _utc_now_iso(),
        source_uri=source_uri,
        content_hash=content_hash,
        config_hash=config_hash,
        metadata=combined_metadata,
        status_message=status_message,
    )


def content_hash_for_rows(rows: tuple[Mapping[str, Any], ...]) -> str:
    return sha256_hex(canonical_json(rows).encode("utf-8"))


def config_hash_for_mapping(config: Mapping[str, Any]) -> str:
    return hash_config(config)


def record_dataset_version(
    connection: sqlite3.Connection,
    record: DatasetVersion,
) -> None:
    """Record a dataset version in an initialized local/temp registry."""
    connection.execute(
        """
        INSERT OR REPLACE INTO dataset_versions (
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
            record.data_version,
            record.dataset_name,
            record.created_at,
            record.source_uri,
            record.content_hash,
            record.config_hash,
            record.metadata_json(),
            record.status_message,
        ),
    )


def get_dataset_version(
    connection: sqlite3.Connection,
    data_version: str,
) -> DatasetVersion | None:
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
        (data_version,),
    ).fetchone()
    if row is None:
        return None
    return DatasetVersion(
        data_version=str(row["data_version"]),
        dataset_name=str(row["dataset_name"]),
        created_at=str(row["created_at"]),
        source_uri=str(row["source_uri"]),
        content_hash=str(row["content_hash"]),
        config_hash=str(row["config_hash"]),
        metadata=json.loads(str(row["metadata_json"])),
        status_message=str(row["status_message"]),
    )
