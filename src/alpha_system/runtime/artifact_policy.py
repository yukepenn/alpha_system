"""Pure local artifact classification for research runtime outputs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

CURATED_SUMMARY_COMMIT_SIZE_LIMIT_BYTES = 64 * 1024

CURATED_COMMIT_KINDS: frozenset[str] = frozenset(
    {
        "diagnostic_summary",
        "evidence_summary",
        "manifest",
        "markdown_summary",
        "reference_summary",
        "runtime_summary",
        "summary",
        "text_summary",
    }
)

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

LOCAL_DB_OR_LOG_SUFFIXES: tuple[str, ...] = (
    ".log",
    ".sqlite-journal",
    ".db-journal",
)

NEVER_COMMIT_PATH_PREFIXES: tuple[str, ...] = (
    "$alpha_data_root/",
    "artifacts/",
    "cache/",
    "data/cache/",
    "data/canonical/",
    "data/factors/",
    "data/labels/",
    "data/raw/",
    "logs/",
    "metadata/",
    "runs/",
)

VALUE_BEARING_KIND_TOKENS: tuple[str, ...] = (
    "arrow",
    "canonical_values",
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
    "runtime_values",
    "sqlite",
    "value_table",
    "values",
    "zst",
)

FORBIDDEN_OUTPUT_KIND_TOKENS: tuple[str, ...] = (
    "cache",
    "canonical",
    "db",
    "log",
    "provider_payload",
    "provider_response",
    "raw",
    "sqlite",
)


class RuntimeArtifactPolicyError(ValueError):
    """Raised when an artifact descriptor is malformed for policy classification."""


class RuntimeArtifactDisposition(StrEnum):
    """Commit disposition for a runtime output descriptor."""

    COMMIT_ALLOWED = "commit_allowed"
    LOCAL_ONLY = "local_only"


@dataclass(frozen=True, slots=True)
class RuntimeArtifactDescriptor:
    """Value-free descriptor of one runtime output candidate."""

    kind: str
    location: str
    size_bytes: int
    curated: bool = False
    row_free: bool = False
    row_count: int | None = None
    contains_runtime_values: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _required_string(self.kind, field="kind"))
        object.__setattr__(
            self,
            "location",
            _required_string(self.location, field="location"),
        )
        object.__setattr__(self, "size_bytes", _coerce_size(self.size_bytes))
        object.__setattr__(self, "curated", _coerce_bool(self.curated, field="curated"))
        object.__setattr__(self, "row_free", _coerce_bool(self.row_free, field="row_free"))
        object.__setattr__(
            self,
            "contains_runtime_values",
            _coerce_bool(self.contains_runtime_values, field="contains_runtime_values"),
        )
        if self.row_count is not None:
            row_count = self.row_count
            if isinstance(row_count, bool) or not isinstance(row_count, int) or row_count < 0:
                raise RuntimeArtifactPolicyError("row_count must be a non-negative integer")

    @property
    def is_row_free(self) -> bool:
        """Return whether the descriptor explicitly carries no rows."""

        return self.row_free or self.row_count == 0


@dataclass(frozen=True, slots=True)
class RuntimeArtifactPolicyDecision:
    """Pure classification result for one runtime artifact descriptor."""

    disposition: RuntimeArtifactDisposition
    commit_allowed: bool
    local_only: bool
    reasons: tuple[str, ...]
    forbidden_classes: tuple[str, ...]

    def to_manifest_flags(self) -> dict[str, bool]:
        """Return the flags consumed by artifact-manifest entries."""

        return {
            "commit_allowed": self.commit_allowed,
            "local_only": self.local_only,
        }


def classify_runtime_artifact(
    descriptor: RuntimeArtifactDescriptor | Mapping[str, Any],
) -> RuntimeArtifactPolicyDecision:
    """Classify a runtime output as commit-eligible or local-only."""

    artifact = coerce_runtime_artifact_descriptor(descriptor)
    reasons: list[str] = []
    forbidden_classes: list[str] = []

    path_classes = forbidden_path_classes(artifact.location)
    if path_classes:
        forbidden_classes.extend(path_classes)
        reasons.append("forbidden_output_location")

    kind_classes = forbidden_kind_classes(artifact.kind)
    if kind_classes:
        forbidden_classes.extend(kind_classes)
        reasons.append("forbidden_output_kind")

    if artifact.contains_runtime_values:
        forbidden_classes.append("runtime_values")
        reasons.append("contains_runtime_values")

    if _has_invalid_commit_location_shape(artifact.location):
        reasons.append("invalid_commit_location")

    if artifact.kind.lower() not in CURATED_COMMIT_KINDS:
        reasons.append("not_curated_summary_kind")

    if not artifact.curated:
        reasons.append("not_marked_curated")

    if not artifact.is_row_free:
        reasons.append("not_row_free")

    if artifact.size_bytes > CURATED_SUMMARY_COMMIT_SIZE_LIMIT_BYTES:
        reasons.append("exceeds_curated_summary_size_limit")

    commit_allowed = not reasons
    disposition = (
        RuntimeArtifactDisposition.COMMIT_ALLOWED
        if commit_allowed
        else RuntimeArtifactDisposition.LOCAL_ONLY
    )

    return RuntimeArtifactPolicyDecision(
        disposition=disposition,
        commit_allowed=commit_allowed,
        local_only=not commit_allowed,
        reasons=tuple(dict.fromkeys(reasons)),
        forbidden_classes=tuple(dict.fromkeys(forbidden_classes)),
    )


def coerce_runtime_artifact_descriptor(
    value: RuntimeArtifactDescriptor | Mapping[str, Any],
) -> RuntimeArtifactDescriptor:
    """Coerce a descriptor mapping into the immutable descriptor shape."""

    if isinstance(value, RuntimeArtifactDescriptor):
        return value
    if not isinstance(value, Mapping):
        raise RuntimeArtifactPolicyError(
            f"artifact descriptor must be a mapping, got {type(value).__name__}"
        )

    location = value.get("location", value.get("path"))
    size_bytes = value.get("size_bytes", value.get("bytes"))
    curated = _mapping_bool(
        value,
        keys=("curated", "summary_curated", "curated_summary"),
        default=False,
    )
    row_free_value = value.get("row_free")
    contains_rows = value.get("contains_rows")
    if row_free_value is not None and not isinstance(row_free_value, bool):
        raise RuntimeArtifactPolicyError("row_free must be a boolean")
    if contains_rows is not None and not isinstance(contains_rows, bool):
        raise RuntimeArtifactPolicyError("contains_rows must be a boolean")
    row_free = row_free_value is True or contains_rows is False
    contains_values = _mapping_bool(
        value,
        keys=("contains_runtime_values", "value_bearing", "contains_values"),
        default=False,
    )

    return RuntimeArtifactDescriptor(
        kind=value.get("kind"),
        location=location,
        size_bytes=size_bytes,
        curated=curated,
        row_free=row_free,
        row_count=value.get("row_count"),
        contains_runtime_values=contains_values,
    )


def runtime_artifact_commit_allowed(
    descriptor: RuntimeArtifactDescriptor | Mapping[str, Any],
) -> bool:
    """Return whether a descriptor is eligible for commit."""

    return classify_runtime_artifact(descriptor).commit_allowed


def runtime_artifact_manifest_flags(
    descriptor: RuntimeArtifactDescriptor | Mapping[str, Any],
) -> dict[str, bool]:
    """Return ``commit_allowed`` and ``local_only`` flags for manifest entries."""

    return classify_runtime_artifact(descriptor).to_manifest_flags()


def forbidden_path_classes(location: str) -> tuple[str, ...]:
    """Return forbidden output classes implied by an output location."""

    normalized = _normalize_location_for_policy(location)
    classes: list[str] = []

    for prefix in NEVER_COMMIT_PATH_PREFIXES:
        if normalized.startswith(prefix):
            classes.append(_class_name_from_prefix(prefix))

    if normalized.endswith(HEAVY_ARTIFACT_SUFFIXES):
        classes.append("heavy_artifact")
    if normalized.endswith(LOCAL_DB_OR_LOG_SUFFIXES):
        classes.append("local_db_or_log")
    if normalized.startswith("/") or normalized.startswith("~"):
        classes.append("local_absolute_path")
    if "\\" in location:
        classes.append("non_posix_path")
    if any(part in {"", ".", ".."} for part in normalized.split("/")):
        classes.append("invalid_path_segment")

    return tuple(dict.fromkeys(classes))


def forbidden_kind_classes(kind: str) -> tuple[str, ...]:
    """Return forbidden output classes implied by an artifact kind."""

    normalized = _normalize_kind(kind)
    classes: list[str] = []

    if _contains_kind_token(normalized, VALUE_BEARING_KIND_TOKENS):
        classes.append("value_bearing")
    if _contains_kind_token(normalized, FORBIDDEN_OUTPUT_KIND_TOKENS):
        classes.append("forbidden_output")

    return tuple(dict.fromkeys(classes))


def validate_commit_allowed(descriptor: RuntimeArtifactDescriptor | Mapping[str, Any]) -> None:
    """Raise if a descriptor is not eligible for commit."""

    decision = classify_runtime_artifact(descriptor)
    if decision.commit_allowed:
        return
    raise RuntimeArtifactPolicyError(
        "runtime artifact is local-only: " + ", ".join(decision.reasons)
    )


def _has_invalid_commit_location_shape(location: str) -> bool:
    normalized = _normalize_location_for_policy(location)
    return (
        normalized.startswith(("/", "~"))
        or "\\" in location
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
    )


def _normalize_location_for_policy(location: str) -> str:
    return _required_string(location, field="location").replace("\\", "/").lower()


def _normalize_kind(kind: str) -> str:
    return _required_string(kind, field="kind").replace("-", "_").lower()


def _contains_kind_token(normalized_kind: str, tokens: tuple[str, ...]) -> bool:
    parts = set(normalized_kind.replace(".", "_").replace("/", "_").split("_"))
    for token in tokens:
        if "_" in token:
            if token in normalized_kind:
                return True
        elif token in parts:
            return True
    return False


def _class_name_from_prefix(prefix: str) -> str:
    normalized = prefix.strip("/").replace("$", "").replace("/", "_")
    return f"{normalized}_path"


def _mapping_bool(value: Mapping[str, Any], *, keys: tuple[str, ...], default: bool) -> bool:
    for key in keys:
        if key not in value:
            continue
        candidate = value[key]
        if not isinstance(candidate, bool):
            raise RuntimeArtifactPolicyError(f"{key} must be a boolean")
        return candidate
    return default


def _required_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeArtifactPolicyError(f"{field} is required")
    return value.strip()


def _coerce_size(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeArtifactPolicyError("size_bytes must be a non-negative integer")
    return value


def _coerce_bool(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise RuntimeArtifactPolicyError(f"{field} must be a boolean")
    return value


__all__ = [
    "CURATED_COMMIT_KINDS",
    "CURATED_SUMMARY_COMMIT_SIZE_LIMIT_BYTES",
    "FORBIDDEN_OUTPUT_KIND_TOKENS",
    "HEAVY_ARTIFACT_SUFFIXES",
    "NEVER_COMMIT_PATH_PREFIXES",
    "RuntimeArtifactDescriptor",
    "RuntimeArtifactDisposition",
    "RuntimeArtifactPolicyDecision",
    "RuntimeArtifactPolicyError",
    "VALUE_BEARING_KIND_TOKENS",
    "classify_runtime_artifact",
    "coerce_runtime_artifact_descriptor",
    "forbidden_kind_classes",
    "forbidden_path_classes",
    "runtime_artifact_commit_allowed",
    "runtime_artifact_manifest_flags",
    "validate_commit_allowed",
]
