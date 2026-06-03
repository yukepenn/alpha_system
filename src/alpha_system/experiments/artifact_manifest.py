"""Artifact manifest models and path-policy classification."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from alpha_system.core.hashing import canonical_json, hash_config, hash_file


LOCAL_ONLY_ROOTS: tuple[str, ...] = (
    "artifacts",
    "runs",
    "metadata",
    "data/raw",
    "data/canonical",
    "data/factors",
    "data/labels",
    "data/cache",
)
COMMIT_ELIGIBLE_ROOTS: tuple[str, ...] = (
    "src",
    "tests",
    "docs",
    "handoffs",
    "reviews",
    "configs",
    "campaigns",
    "specs",
    "decisions",
    "evals",
)
FORBIDDEN_SUFFIXES: tuple[str, ...] = (
    ".sqlite",
    ".sqlite3",
    ".db",
    ".db-journal",
    ".wal",
    ".parquet",
    ".arrow",
    ".feather",
    ".log",
)
FORBIDDEN_SEGMENTS: tuple[str, ...] = (
    "full_grid_outputs",
    "full_trade_logs",
)
SYNC_MARKERS: tuple[str, ...] = (
    "onedrive",
    "dropbox",
    "google drive",
    "googledrive",
)


class ArtifactManifestError(ValueError):
    """Raised when artifact manifest metadata is malformed."""


@dataclass(frozen=True, slots=True)
class ArtifactPathPolicy:
    """Path-policy classification for a manifest artifact path."""

    path: str
    is_relative: bool
    local_only: bool
    commit_eligible: bool
    commit_safe: bool
    forbidden: bool
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_text(value: datetime | str | None) -> str:
    if value is None:
        value = datetime.now(timezone.utc)
    if isinstance(value, str):
        return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_path_text(path: str | Path) -> str:
    return Path(path).as_posix() if isinstance(path, Path) else str(path).replace("\\", "/")


def _is_under(path: PurePosixPath, roots: Sequence[str]) -> bool:
    parts = path.parts
    for root in roots:
        root_parts = PurePosixPath(root).parts
        if parts[: len(root_parts)] == root_parts:
            return True
    return False


def classify_artifact_path(path: str | Path) -> ArtifactPathPolicy:
    """Classify an artifact path for local-only and commit-safety behavior."""
    text = _normalize_path_text(path).strip()
    warnings: list[str] = []
    forbidden = False
    if not text:
        return ArtifactPathPolicy(
            path=text,
            is_relative=False,
            local_only=True,
            commit_eligible=False,
            commit_safe=False,
            forbidden=True,
            warnings=("artifact path is empty",),
        )

    lowered = text.lower()
    pure = PurePosixPath(text)
    is_windows_absolute = len(text) >= 3 and text[1] == ":" and text[2] == "/"
    is_relative = not pure.is_absolute() and not is_windows_absolute

    if not is_relative:
        forbidden = True
        warnings.append("artifact path must be relative to be commit-safe")
    if ".." in pure.parts:
        forbidden = True
        warnings.append("artifact path must not contain parent-directory traversal")
    if text.startswith(("/mnt/c/", "/mnt/d/", "/mnt/e/")):
        forbidden = True
        warnings.append("artifact path points at a forbidden synced Windows mount")
    if any(marker in lowered for marker in SYNC_MARKERS):
        forbidden = True
        warnings.append("artifact path points at a known synced/nonlocal location")
    if any(part in FORBIDDEN_SEGMENTS for part in pure.parts):
        forbidden = True
        warnings.append("artifact path points at a forbidden generated-output directory")

    suffix_forbidden = any(lowered.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES)
    if suffix_forbidden:
        forbidden = True
        warnings.append("artifact path has a local-only or forbidden generated-file suffix")

    local_only = _is_under(pure, LOCAL_ONLY_ROOTS) or suffix_forbidden or not is_relative
    commit_eligible = is_relative and _is_under(pure, COMMIT_ELIGIBLE_ROOTS) and not forbidden
    commit_safe = is_relative and commit_eligible and not local_only and not forbidden
    if not commit_safe and "artifact path is not commit-safe" not in warnings:
        warnings.append("artifact path is not commit-safe")

    return ArtifactPathPolicy(
        path=text,
        is_relative=is_relative,
        local_only=local_only,
        commit_eligible=commit_eligible,
        commit_safe=commit_safe,
        forbidden=forbidden,
        warnings=tuple(dict.fromkeys(warnings)),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactManifestEntry:
    """A schema-validated artifact manifest entry."""

    artifact_id: str
    run_id: str
    artifact_type: str
    relative_path: str
    content_hash: str = ""
    size_bytes: int | None = None
    created_at: datetime | str | None = None
    local_only: bool | None = None
    commit_eligible: bool | None = None
    warnings: Sequence[str] = ()

    def __post_init__(self) -> None:
        artifact_id = _require_text(self.artifact_id, "artifact_id")
        run_id = _require_text(self.run_id, "run_id")
        artifact_type = _require_text(self.artifact_type, "artifact_type")
        policy = classify_artifact_path(self.relative_path)
        if not policy.is_relative:
            raise ArtifactManifestError("relative_path must be relative")
        if ".." in PurePosixPath(policy.path).parts:
            raise ArtifactManifestError("relative_path must not contain parent-directory traversal")
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ArtifactManifestError("size_bytes must be non-negative when provided")

        object.__setattr__(self, "artifact_id", artifact_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "artifact_type", artifact_type)
        object.__setattr__(self, "relative_path", policy.path)
        object.__setattr__(self, "created_at", _utc_text(self.created_at))
        object.__setattr__(
            self,
            "local_only",
            policy.local_only if self.local_only is None else bool(self.local_only),
        )
        object.__setattr__(
            self,
            "commit_eligible",
            policy.commit_eligible
            if self.commit_eligible is None
            else bool(self.commit_eligible),
        )
        all_warnings = tuple(dict.fromkeys((*self.warnings, *policy.warnings)))
        object.__setattr__(self, "warnings", all_warnings)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["created_at"] = str(self.created_at)
        payload["warnings"] = list(self.warnings)
        return payload

    def to_registry_values(
        self,
        *,
        run_table: str,
        artifact_key: str | None = None,
    ) -> tuple[str, str, str, str, str, str, str, str, str, str]:
        policy = classify_artifact_path(self.relative_path)
        metadata = {
            "artifact_type": self.artifact_type,
            "size_bytes": self.size_bytes,
            "local_only": self.local_only,
            "commit_eligible": self.commit_eligible,
            "commit_safe": policy.commit_safe,
            "forbidden": policy.forbidden,
            "warnings": list(self.warnings),
        }
        status_message = "; ".join(self.warnings)
        return (
            self.artifact_id,
            self.run_id,
            run_table,
            artifact_key or self.artifact_type,
            self.relative_path,
            self.content_hash,
            self.artifact_type,
            str(self.created_at),
            canonical_json(metadata),
            status_message,
        )


def _require_text(value: str, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ArtifactManifestError(f"{field_name} must be non-empty")
    return text


def artifact_entry_from_file(
    *,
    run_id: str,
    artifact_type: str,
    path: str | Path,
    root: str | Path | None = None,
    artifact_id: str | None = None,
    created_at: datetime | str | None = None,
) -> ArtifactManifestEntry:
    """Capture hash and size for an available file without writing registry state."""
    file_path = Path(path)
    relative_path = (
        file_path.resolve().relative_to(Path(root).resolve()).as_posix()
        if root is not None
        else file_path.as_posix()
    )
    content_hash = hash_file(file_path) if file_path.exists() else ""
    size_bytes = file_path.stat().st_size if file_path.exists() else None
    active_id = artifact_id or hash_config(
        {
            "run_id": run_id,
            "artifact_type": artifact_type,
            "relative_path": relative_path,
            "content_hash": content_hash,
        }
    )[:24]
    warnings: tuple[str, ...] = ()
    if not file_path.exists():
        warnings = ("artifact file unavailable for hash/size capture",)
    return ArtifactManifestEntry(
        artifact_id=active_id,
        run_id=run_id,
        artifact_type=artifact_type,
        relative_path=relative_path,
        content_hash=content_hash,
        size_bytes=size_bytes,
        created_at=created_at,
        warnings=warnings,
    )


def insert_artifact_manifest(
    connection: sqlite3.Connection,
    entry: ArtifactManifestEntry,
    *,
    run_table: str,
    artifact_key: str | None = None,
) -> None:
    """Insert one artifact manifest entry into the existing registry table."""
    connection.execute(
        """
        INSERT INTO artifact_manifest (
            artifact_id,
            run_id,
            run_table,
            artifact_key,
            artifact_path,
            content_hash,
            artifact_role,
            created_at,
            metadata_json,
            status_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        entry.to_registry_values(run_table=run_table, artifact_key=artifact_key),
    )


def read_artifact_manifest(
    connection: sqlite3.Connection,
    *,
    run_id: str | None = None,
) -> tuple[dict[str, Any], ...]:
    """Read artifact manifest rows as dictionaries for audit/reporting."""
    if run_id is None:
        rows = connection.execute(
            """
            SELECT artifact_id, run_id, run_table, artifact_key, artifact_path,
                   content_hash, artifact_role, created_at, metadata_json,
                   status_message
            FROM artifact_manifest
            ORDER BY run_id, artifact_key, artifact_path
            """
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT artifact_id, run_id, run_table, artifact_key, artifact_path,
                   content_hash, artifact_role, created_at, metadata_json,
                   status_message
            FROM artifact_manifest
            WHERE run_id = ?
            ORDER BY artifact_key, artifact_path
            """,
            (run_id,),
        ).fetchall()
    return tuple(_row_to_dict(row) for row in rows)


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    try:
        payload["metadata"] = json.loads(str(payload.get("metadata_json") or "{}"))
    except json.JSONDecodeError:
        payload["metadata"] = {}
    return payload
