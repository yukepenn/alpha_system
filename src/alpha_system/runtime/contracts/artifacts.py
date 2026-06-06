"""Immutable artifact ledger contracts for research runtime outputs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.serialization import content_hash as governance_content_hash

RUNTIME_ARTIFACT_MANIFEST_SCHEMA = "alpha_system.runtime.artifact_manifest.v1"
RUNTIME_ARTIFACT_MANIFEST_ID_PREFIX = "rart"
CURATED_SUMMARY_COMMIT_SIZE_LIMIT_BYTES = 64 * 1024

HEAVY_ARTIFACT_SUFFIXES: tuple[str, ...] = (
    ".parquet",
    ".arrow",
    ".feather",
    ".dbn",
    ".zst",
    ".sqlite",
    ".db",
    ".wal",
    ".npy",
    ".npz",
)
VALUE_BEARING_KIND_TOKENS: tuple[str, ...] = (
    "arrow",
    "dbn",
    "feather",
    "feature_table",
    "feature_values",
    "label_table",
    "label_values",
    "market_values",
    "npy",
    "npz",
    "parquet",
    "raw_values",
    "sqlite",
    "value_table",
    "value-table",
    "values",
    "zst",
)
CURATED_COMMIT_KINDS: frozenset[str] = frozenset(
    {
        "diagnostic_summary",
        "evidence_summary",
        "manifest",
        "markdown_summary",
        "reference_summary",
        "summary",
        "text_summary",
    }
)
FORBIDDEN_COMMIT_PREFIXES: tuple[str, ...] = (
    "artifacts/",
    "data/cache/",
    "data/canonical/",
    "data/factors/",
    "data/labels/",
    "data/raw/",
    "metadata/",
    "runs/",
)


class RuntimeArtifactContractError(ValueError):
    """Raised when a runtime artifact ledger entry violates artifact policy."""


@dataclass(frozen=True, slots=True)
class RuntimeArtifactEntry:
    """Reference-only metadata for one produced artifact."""

    artifact_id: str
    kind: str
    location: str
    content_hash: str
    size_bytes: int
    local_only: bool = True
    commit_allowed: bool = False

    def __post_init__(self) -> None:
        artifact_id = _required_string(self.artifact_id, field="artifact_id")
        kind = _required_string(self.kind, field="kind")
        location = _normalize_location(self.location)
        digest = _required_string(self.content_hash, field="content_hash")
        size_bytes = _coerce_size(self.size_bytes)
        local_only = _coerce_bool(self.local_only, field="local_only")
        commit_allowed = _coerce_bool(self.commit_allowed, field="commit_allowed")

        if commit_allowed:
            _validate_commit_allowed(
                kind=kind,
                location=location,
                size_bytes=size_bytes,
            )
        if not local_only and _is_never_commit_location(location):
            raise RuntimeArtifactContractError(
                "non-local artifact references cannot point under never-commit locations"
            )

        object.__setattr__(self, "artifact_id", artifact_id)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "location", location)
        object.__setattr__(self, "content_hash", digest)
        object.__setattr__(self, "size_bytes", size_bytes)
        object.__setattr__(self, "local_only", local_only)
        object.__setattr__(self, "commit_allowed", commit_allowed)

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible artifact reference."""

        return {
            "artifact_id": self.artifact_id,
            "kind": self.kind,
            "location": self.location,
            "content_hash": self.content_hash,
            "size_bytes": self.size_bytes,
            "local_only": self.local_only,
            "commit_allowed": self.commit_allowed,
        }


@dataclass(frozen=True, slots=True, init=False)
class RuntimeArtifactManifest:
    """Ordered artifact ledger for one runtime run."""

    manifest_id: str
    run_id: str
    entries: tuple[RuntimeArtifactEntry, ...]
    manifest_hash: str

    def __init__(
        self,
        *,
        run_id: str,
        entries: Sequence[RuntimeArtifactEntry | Mapping[str, Any]] = (),
    ) -> None:
        normalized_run_id = _required_string(run_id, field="run_id")
        normalized_entries = tuple(_coerce_entry(entry) for entry in entries)
        _require_unique_artifact_ids(normalized_entries)

        payload = _manifest_hash_payload(
            run_id=normalized_run_id,
            entries=normalized_entries,
        )
        digest = governance_content_hash(cast(JsonValue, payload))

        object.__setattr__(
            self,
            "manifest_id",
            f"{RUNTIME_ARTIFACT_MANIFEST_ID_PREFIX}_{digest[:24]}",
        )
        object.__setattr__(self, "run_id", normalized_run_id)
        object.__setattr__(self, "entries", normalized_entries)
        object.__setattr__(self, "manifest_hash", digest)

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible artifact manifest."""

        return {
            "schema": RUNTIME_ARTIFACT_MANIFEST_SCHEMA,
            "manifest_id": self.manifest_id,
            "run_id": self.run_id,
            "entries": [entry.to_dict() for entry in self.entries],
            "manifest_hash": self.manifest_hash,
            "value_free": True,
        }


def _coerce_entry(value: RuntimeArtifactEntry | Mapping[str, Any]) -> RuntimeArtifactEntry:
    if isinstance(value, RuntimeArtifactEntry):
        return value
    if not isinstance(value, Mapping):
        raise RuntimeArtifactContractError(
            f"artifact entry must be RuntimeArtifactEntry or mapping, got {type(value).__name__}"
        )
    allowed = {
        "artifact_id",
        "kind",
        "location",
        "content_hash",
        "size_bytes",
        "local_only",
        "commit_allowed",
    }
    extra = set(value) - allowed
    if extra:
        raise RuntimeArtifactContractError(
            f"artifact entry contains non-reference fields: {', '.join(sorted(extra))}"
        )
    return RuntimeArtifactEntry(
        artifact_id=value.get("artifact_id"),
        kind=value.get("kind"),
        location=value.get("location"),
        content_hash=value.get("content_hash"),
        size_bytes=value.get("size_bytes"),
        local_only=value.get("local_only", True),
        commit_allowed=value.get("commit_allowed", False),
    )


def _manifest_hash_payload(
    *,
    run_id: str,
    entries: tuple[RuntimeArtifactEntry, ...],
) -> dict[str, object]:
    return {
        "schema": RUNTIME_ARTIFACT_MANIFEST_SCHEMA,
        "run_id": run_id,
        "entries": [entry.to_dict() for entry in entries],
    }


def _require_unique_artifact_ids(entries: tuple[RuntimeArtifactEntry, ...]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for entry in entries:
        if entry.artifact_id in seen:
            duplicates.add(entry.artifact_id)
        seen.add(entry.artifact_id)
    if duplicates:
        raise RuntimeArtifactContractError(
            f"artifact ids must be unique: {', '.join(sorted(duplicates))}"
        )


def _validate_commit_allowed(*, kind: str, location: str, size_bytes: int) -> None:
    if _is_heavy_or_value_bearing(kind=kind, location=location):
        raise RuntimeArtifactContractError(
            "heavy or value-bearing artifacts cannot be marked commit_allowed"
        )
    if _is_never_commit_location(location):
        raise RuntimeArtifactContractError(
            "artifacts under never-commit locations cannot be marked commit_allowed"
        )
    if kind.lower() not in CURATED_COMMIT_KINDS:
        raise RuntimeArtifactContractError(
            "commit_allowed artifacts must use a curated row-free summary kind"
        )
    if size_bytes > CURATED_SUMMARY_COMMIT_SIZE_LIMIT_BYTES:
        raise RuntimeArtifactContractError(
            "commit_allowed artifacts exceed the curated summary size threshold"
        )


def _is_heavy_or_value_bearing(*, kind: str, location: str) -> bool:
    kind_lower = kind.lower()
    return any(
        token in kind_lower for token in VALUE_BEARING_KIND_TOKENS
    ) or location.lower().endswith(HEAVY_ARTIFACT_SUFFIXES)


def _is_never_commit_location(location: str) -> bool:
    location_lower = location.lower()
    return location_lower.startswith(FORBIDDEN_COMMIT_PREFIXES) or location_lower.endswith(
        HEAVY_ARTIFACT_SUFFIXES
    )


def _required_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeArtifactContractError(f"{field} is required")
    return value.strip()


def _normalize_location(value: object) -> str:
    location = _required_string(value, field="location")
    if location.startswith(("/", "~")) or "\\" in location:
        raise RuntimeArtifactContractError("artifact location must be a relative reference")
    parts = location.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise RuntimeArtifactContractError(
            "artifact location must not contain empty or parent segments"
        )
    return location


def _coerce_size(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeArtifactContractError("size_bytes must be a non-negative integer")
    return value


def _coerce_bool(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise RuntimeArtifactContractError(f"{field} must be a boolean")
    return value


__all__ = [
    "CURATED_SUMMARY_COMMIT_SIZE_LIMIT_BYTES",
    "RuntimeArtifactContractError",
    "RuntimeArtifactEntry",
    "RuntimeArtifactManifest",
]
