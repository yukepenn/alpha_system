"""Local-only label store and registry version helpers."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from alpha_system.core.git_info import capture_git_info
from alpha_system.core.hashing import canonical_json, hash_config
from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.labels.spec import (
    LabelSpec,
    compute_label_config_hash,
)
from alpha_system.labels.validation import validate_label_record


class LabelStoreError(ValueError):
    """Raised when label store or registry policy is violated."""


LOCAL_SYNC_MARKERS: tuple[str, ...] = (
    "onedrive",
    "dropbox",
    "google drive",
    "googledrive",
)


@dataclass(frozen=True, slots=True)
class LabelVersionRecord:
    label_id: str
    label_version: str
    label_type: str
    created_at: str
    git_commit: str | None
    git_dirty: int | None
    code_hash: str
    config_hash: str
    data_version: str
    parameters: Mapping[str, Any]
    artifact_paths: Mapping[str, Any]
    decision_status: str
    status_message: str


class LocalLabelStore:
    """Small JSONL label store rooted outside committed repository paths."""

    def __init__(self, root: str | Path | None = None, *, repo_root: str | Path | None = None):
        active_root = (
            Path(tempfile.mkdtemp(prefix="alpha_system_labels_"))
            if root is None
            else Path(root)
        )
        self.repo_root = Path(repo_root or Path.cwd()).resolve(strict=False)
        self.root = active_root.expanduser().resolve(strict=False)
        if not is_local_only_label_store_path(self.root, repo_root=self.repo_root):
            msg = f"label store path is not local-only: {self.root}"
            raise LabelStoreError(msg)
        self.root.mkdir(parents=True, exist_ok=True)

    def write_labels(
        self,
        name: str,
        labels: Iterable[LabelSpec | Mapping[str, Any]],
    ) -> Path:
        """Write validated labels to a local-only JSONL file."""
        safe_name = _safe_name(name)
        path = self.root / f"{safe_name}.jsonl"
        normalized = tuple(validate_label_record(label) for label in labels)
        with path.open("w", encoding="utf-8") as handle:
            for label in normalized:
                handle.write(json.dumps(label.to_dict(), sort_keys=True))
                handle.write("\n")
        return path

    def read_labels(self, name_or_path: str | Path) -> tuple[LabelSpec, ...]:
        """Read labels written by this store."""
        candidate = Path(name_or_path)
        path = candidate if candidate.suffix else self.root / f"{_safe_name(str(name_or_path))}.jsonl"
        resolved = path.expanduser().resolve(strict=False)
        if self.root not in (resolved, *resolved.parents):
            msg = "label store reads are restricted to the configured local root"
            raise LabelStoreError(msg)
        labels: list[LabelSpec] = []
        with resolved.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    labels.append(LabelSpec.from_mapping(json.loads(line)))
        return tuple(labels)


def is_local_only_label_store_path(path: str | Path, *, repo_root: str | Path | None = None) -> bool:
    """Return whether a label output root avoids committed/synced paths."""
    resolved = Path(path).expanduser().resolve(strict=False)
    repo = Path(repo_root or Path.cwd()).expanduser().resolve(strict=False)
    normalized = resolved.as_posix()
    lowered = normalized.lower()
    if normalized.startswith(("/mnt/c/", "/mnt/d/", "/mnt/e/")):
        return False
    if any(marker in lowered for marker in LOCAL_SYNC_MARKERS):
        return False
    if resolved == repo or repo in resolved.parents:
        return False
    return True


def register_label_version(
    registry_path: str | Path,
    spec: LabelSpec,
    *,
    label_version: str,
    parameters: Mapping[str, Any] | None = None,
    artifact_paths: Mapping[str, Any] | None = None,
    decision_status: str = "draft",
    status_message: str = "label version registration",
    code_hash: str | None = None,
    config_hash: str | None = None,
    repo_root: str | Path | None = None,
) -> None:
    """Record a label version in the ASV1-P05 label_versions table."""
    registry = _init_valid_temp_registry(registry_path, repo_root=repo_root)
    active_parameters = dict(parameters or {})
    active_artifact_paths = dict(artifact_paths or {})
    active_code_hash = code_hash or hash_config(
        {
            "label_id": spec.label_id,
            "label_type": spec.label_type.value,
            "module": "alpha_system.labels",
        }
    )
    active_config_hash = config_hash or compute_label_config_hash(
        {
            "label_id": spec.label_id,
            "label_type": spec.label_type.value,
            "horizon": int(spec.horizon.total_seconds()),
            "data_version": spec.data_version,
            "parameters": active_parameters,
        }
    )
    git_info = capture_git_info(Path.cwd())
    with connect_registry(registry) as connection:
        if label_version_exists(connection, spec.label_id, label_version):
            msg = f"label version already exists: {spec.label_id} {label_version}"
            raise LabelStoreError(msg)
        connection.execute(
            """
            INSERT INTO label_versions (
                label_id,
                label_version,
                label_type,
                created_at,
                git_commit,
                git_dirty,
                code_hash,
                config_hash,
                data_version,
                parameters_json,
                artifact_paths_json,
                decision_status,
                status_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                spec.label_id,
                label_version,
                spec.label_type.value,
                _utc_now(),
                git_info.commit,
                _git_dirty_value(git_info.dirty),
                active_code_hash,
                active_config_hash,
                spec.data_version,
                canonical_json(active_parameters),
                canonical_json(active_artifact_paths),
                decision_status,
                status_message,
            ),
        )


def label_version_exists(
    connection: sqlite3.Connection,
    label_id: str,
    label_version: str,
) -> bool:
    """Return whether a label version already exists."""
    row = connection.execute(
        """
        SELECT 1
        FROM label_versions
        WHERE label_id = ? AND label_version = ?
        """,
        (label_id, label_version),
    ).fetchone()
    return row is not None


def get_label_version(
    registry_path: str | Path,
    label_id: str,
    label_version: str,
) -> LabelVersionRecord | None:
    """Read a label version record from a temp/local registry database."""
    with connect_registry(registry_path, read_only=True) as connection:
        row = connection.execute(
            """
            SELECT
                label_id,
                label_version,
                label_type,
                created_at,
                git_commit,
                git_dirty,
                code_hash,
                config_hash,
                data_version,
                parameters_json,
                artifact_paths_json,
                decision_status,
                status_message
            FROM label_versions
            WHERE label_id = ? AND label_version = ?
            """,
            (label_id, label_version),
        ).fetchone()
    if row is None:
        return None
    return LabelVersionRecord(
        label_id=str(row["label_id"]),
        label_version=str(row["label_version"]),
        label_type=str(row["label_type"]),
        created_at=str(row["created_at"]),
        git_commit=row["git_commit"],
        git_dirty=row["git_dirty"],
        code_hash=str(row["code_hash"]),
        config_hash=str(row["config_hash"]),
        data_version=str(row["data_version"]),
        parameters=_loads(row["parameters_json"]),
        artifact_paths=_loads(row["artifact_paths_json"]),
        decision_status=str(row["decision_status"]),
        status_message=str(row["status_message"]),
    )


def _init_valid_temp_registry(
    registry_path: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> Path:
    registry = Path(registry_path).expanduser().resolve(strict=False)
    repo = Path(repo_root or Path.cwd()).resolve(strict=False)
    if registry == repo or repo in registry.parents:
        msg = "label registry writes must use a temp/local path outside the repository"
        raise LabelStoreError(msg)
    status = init_registry(registry)
    if not status.valid:
        msg = f"registry is not valid: {status.status_message}"
        raise LabelStoreError(msg)
    return registry


def _safe_name(name: str) -> str:
    normalized = "".join(char if char.isalnum() or char in "-_" else "_" for char in name)
    normalized = normalized.strip("._-")
    if not normalized:
        msg = "label store name must contain at least one safe character"
        raise LabelStoreError(msg)
    return normalized


def _loads(value: str) -> dict[str, Any]:
    payload = json.loads(value or "{}")
    if isinstance(payload, dict):
        return payload
    return {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _git_dirty_value(value: bool | None) -> int | None:
    if value is None:
        return None
    return 1 if value else 0
