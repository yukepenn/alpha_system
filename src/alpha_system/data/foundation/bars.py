"""Raw, parsed, and canonical bar-layer records.

DATA-P09 owns the immutable raw provider-response record and local-only raw
data-lake layout policy. DATA-P14 and DATA-P15 own parser, canonicalization,
timestamp, and quality behavior.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import InitVar, dataclass
from datetime import datetime
from pathlib import Path
from types import MappingProxyType

from alpha_system.data.foundation.sources import (
    DataFoundationValidationError,
    LocalDataRootPolicy,
    require_local_data_root_policy,
)

REQUIRED_RAW_DATA_OBJECT_FIELDS: tuple[str, ...] = (
    "raw_object_id",
    "source",
    "request_id",
    "chunk_id",
    "path",
    "content_hash",
    "schema_hint",
    "retrieved_at",
    "row_count",
)

RAW_DATA_LAKE_SUBDIR = "raw"
RAW_DATA_OBJECT_SUFFIX = ".raw"
REPO_DATA_PLACEHOLDER_FILENAMES: frozenset[str] = frozenset({"README.md", ".gitkeep"})

_SHA256_CONTENT_HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
_SAFE_PATH_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_FORBIDDEN_SCHEMA_HINT_TOKENS: frozenset[str] = frozenset(
    {
        "canonical",
        "canonical_truth",
        "quality_passed",
        "research_ready",
        "versioned_truth",
    }
)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    normalized = value.strip()
    if not normalized:
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    if "\n" in normalized or "\r" in normalized:
        msg = f"{field_name} must be a single-line string"
        raise DataFoundationValidationError(msg)
    return normalized


def _normalize_id(value: object, field_name: str) -> str:
    token = _require_text(value, field_name)
    if not _SAFE_PATH_TOKEN_PATTERN.fullmatch(token):
        msg = f"{field_name} must be an alphanumeric identifier"
        raise DataFoundationValidationError(msg)
    return token


def _normalize_source(value: object) -> str:
    source = _normalize_id(value, "source")
    if not source.startswith("dsrc_"):
        msg = "source must link to a DataSourceProfile source_id with dsrc_ prefix"
        raise DataFoundationValidationError(msg)
    return source


def _normalize_content_hash(value: object) -> str:
    content_hash = _require_text(value, "content_hash").lower()
    if not _SHA256_CONTENT_HASH_PATTERN.fullmatch(content_hash):
        msg = "content_hash must use sha256:<64 hex digest>"
        raise DataFoundationValidationError(msg)
    return content_hash


def _content_digest(content_hash: object) -> str:
    return _normalize_content_hash(content_hash).removeprefix("sha256:")


def _normalize_path(value: object) -> Path:
    if not isinstance(value, (str, os.PathLike)):
        msg = "path must be a string or path-like local raw object path"
        raise DataFoundationValidationError(msg)
    raw = os.fspath(value).strip()
    if not raw:
        msg = "path must be a non-empty local raw object path"
        raise DataFoundationValidationError(msg)
    if raw.startswith(("//", "\\\\")):
        msg = "path must not use a network path"
        raise DataFoundationValidationError(msg)
    return Path(raw).expanduser().resolve(strict=False)


def _parse_aware_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = _require_text(value, field_name)
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be an ISO-8601 timezone-aware datetime"
            raise DataFoundationValidationError(msg) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return parsed


def _require_non_negative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be a non-negative integer"
        raise DataFoundationValidationError(msg)
    if value < 0:
        msg = f"{field_name} must be non-negative"
        raise DataFoundationValidationError(msg)
    return value


def _normalize_schema_hint(value: object) -> str:
    schema_hint = _require_text(value, "schema_hint")
    token = schema_hint.lower().replace("-", "_").replace(" ", "_")
    if token in _FORBIDDEN_SCHEMA_HINT_TOKENS:
        msg = "schema_hint must be a provider-shape hint and must not imply canonical truth"
        raise DataFoundationValidationError(msg)
    return schema_hint


def _raw_layout_token(value: object, field_name: str) -> str:
    return _normalize_id(value, field_name)


def raw_object_ref_for_content_hash(content_hash: object) -> str:
    """Return the DATA-P08-compatible raw object ref for a content hash."""

    return "raw://sha256/" + _content_digest(content_hash)


@dataclass(frozen=True, slots=True)
class RawDataLakeLayoutPolicy:
    """Pure local path policy for immutable raw provider responses."""

    local_data_root_policy: LocalDataRootPolicy
    raw_subdir: str = RAW_DATA_LAKE_SUBDIR
    object_suffix: str = RAW_DATA_OBJECT_SUFFIX

    def __post_init__(self) -> None:
        local_policy = require_local_data_root_policy(self.local_data_root_policy)
        raw_subdir = _raw_layout_token(self.raw_subdir, "raw_subdir")
        object_suffix = _require_text(self.object_suffix, "object_suffix")

        if raw_subdir not in local_policy.allowed_subdirs:
            msg = f"raw_subdir {raw_subdir!r} is not allowed by LocalDataRootPolicy"
            raise DataFoundationValidationError(msg)
        if not object_suffix.startswith(".") or "/" in object_suffix or "\\" in object_suffix:
            msg = "object_suffix must be a simple file suffix"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "local_data_root_policy", local_policy)
        object.__setattr__(self, "raw_subdir", raw_subdir)
        object.__setattr__(self, "object_suffix", object_suffix)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> RawDataLakeLayoutPolicy:
        """Build the raw layout policy from ``ALPHA_DATA_ROOT``."""

        return cls(local_data_root_policy=LocalDataRootPolicy.from_env(env))

    def resolve_path(
        self,
        *,
        source: object,
        request_id: object,
        chunk_id: object,
        content_hash: object,
    ) -> Path:
        """Resolve the content-addressed raw object path under ``ALPHA_DATA_ROOT``."""

        normalized_source = _normalize_source(source)
        normalized_request_id = _raw_layout_token(request_id, "request_id")
        normalized_chunk_id = _raw_layout_token(chunk_id, "chunk_id")
        digest = _content_digest(content_hash)
        return (
            self.local_data_root_policy.data_root
            / self.raw_subdir
            / f"source={normalized_source}"
            / f"request={normalized_request_id}"
            / f"chunk={normalized_chunk_id}"
            / f"sha256={digest[:2]}"
            / f"{digest}{self.object_suffix}"
        ).resolve(strict=False)

    def validate_path(
        self,
        path: object,
        *,
        source: object,
        request_id: object,
        chunk_id: object,
        content_hash: object,
    ) -> Path:
        """Validate a raw object path is local-only, linked, and content-addressed."""

        normalized_path = _normalize_path(path)
        data_root = self.local_data_root_policy.data_root
        if not _is_relative_to(normalized_path, data_root):
            msg = f"path must resolve under ALPHA_DATA_ROOT: {data_root.as_posix()}"
            raise DataFoundationValidationError(msg)

        relative = normalized_path.relative_to(data_root)
        if not relative.parts or relative.parts[0] != self.raw_subdir:
            msg = f"path must live under the {self.raw_subdir!r} local data-root subdir"
            raise DataFoundationValidationError(msg)

        digest = _content_digest(content_hash)
        required_parts = {
            f"source={_normalize_source(source)}",
            f"request={_raw_layout_token(request_id, 'request_id')}",
            f"chunk={_raw_layout_token(chunk_id, 'chunk_id')}",
        }
        if not required_parts.issubset(set(relative.parts)):
            msg = "path must be source/request/chunk linked"
            raise DataFoundationValidationError(msg)
        if digest not in relative.as_posix():
            msg = "path must include the content_hash digest"
            raise DataFoundationValidationError(msg)

        return normalized_path


def require_raw_data_lake_layout_policy(
    policy: RawDataLakeLayoutPolicy | None,
) -> RawDataLakeLayoutPolicy:
    """Fail closed unless a validated raw lake layout policy is present."""

    if not isinstance(policy, RawDataLakeLayoutPolicy):
        msg = "missing RawDataLakeLayoutPolicy blocks raw object path resolution"
        raise DataFoundationValidationError(msg)
    return policy


def resolve_raw_object_storage_path(
    *,
    layout_policy: RawDataLakeLayoutPolicy,
    source: object,
    request_id: object,
    chunk_id: object,
    content_hash: object,
) -> Path:
    """Resolve a raw object path with an explicit layout policy."""

    return require_raw_data_lake_layout_policy(layout_policy).resolve_path(
        source=source,
        request_id=request_id,
        chunk_id=chunk_id,
        content_hash=content_hash,
    )


@dataclass(frozen=True, slots=True)
class RawDataObject:
    """Immutable local provider response metadata.

    The content address is ``content_hash``. This record is provenance metadata
    for raw bytes only and does not imply canonical truth or quality acceptance.
    """

    raw_object_id: str
    source: str
    request_id: str
    chunk_id: str
    path: Path
    content_hash: str
    schema_hint: str
    retrieved_at: datetime
    row_count: int
    validation_policy: InitVar[RawDataLakeLayoutPolicy | None] = None

    def __post_init__(self, validation_policy: RawDataLakeLayoutPolicy | None) -> None:
        raw_object_id = _normalize_id(self.raw_object_id, "raw_object_id")
        source = _normalize_source(self.source)
        request_id = _raw_layout_token(self.request_id, "request_id")
        chunk_id = _raw_layout_token(self.chunk_id, "chunk_id")
        content_hash = _normalize_content_hash(self.content_hash)
        schema_hint = _normalize_schema_hint(self.schema_hint)
        retrieved_at = _parse_aware_datetime(self.retrieved_at, "retrieved_at")
        row_count = _require_non_negative_int(self.row_count, "row_count")
        layout_policy = (
            require_raw_data_lake_layout_policy(validation_policy)
            if validation_policy is not None
            else RawDataLakeLayoutPolicy.from_env()
        )
        path = layout_policy.validate_path(
            self.path,
            source=source,
            request_id=request_id,
            chunk_id=chunk_id,
            content_hash=content_hash,
        )

        object.__setattr__(self, "raw_object_id", raw_object_id)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "request_id", request_id)
        object.__setattr__(self, "chunk_id", chunk_id)
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "content_hash", content_hash)
        object.__setattr__(self, "schema_hint", schema_hint)
        object.__setattr__(self, "retrieved_at", retrieved_at)
        object.__setattr__(self, "row_count", row_count)

    @classmethod
    def create(
        cls,
        *,
        raw_object_id: str,
        source: str,
        request_id: str,
        chunk_id: str,
        content_hash: str,
        schema_hint: str,
        retrieved_at: datetime,
        row_count: int,
        layout_policy: RawDataLakeLayoutPolicy,
    ) -> RawDataObject:
        """Create a raw object record by resolving the path from an explicit policy."""

        policy = require_raw_data_lake_layout_policy(layout_policy)
        path = policy.resolve_path(
            source=source,
            request_id=request_id,
            chunk_id=chunk_id,
            content_hash=content_hash,
        )
        return cls(
            raw_object_id=raw_object_id,
            source=source,
            request_id=request_id,
            chunk_id=chunk_id,
            path=path,
            content_hash=content_hash,
            schema_hint=schema_hint,
            retrieved_at=retrieved_at,
            row_count=row_count,
            validation_policy=policy,
        )

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, object],
        *,
        layout_policy: RawDataLakeLayoutPolicy | None = None,
    ) -> RawDataObject:
        """Build a raw object from persisted metadata and fail closed."""

        missing = tuple(field for field in REQUIRED_RAW_DATA_OBJECT_FIELDS if field not in values)
        if missing:
            msg = "RawDataObject missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        return cls(
            raw_object_id=_require_text(values["raw_object_id"], "raw_object_id"),
            source=_require_text(values["source"], "source"),
            request_id=_require_text(values["request_id"], "request_id"),
            chunk_id=_require_text(values["chunk_id"], "chunk_id"),
            path=_normalize_path(values["path"]),
            content_hash=_require_text(values["content_hash"], "content_hash"),
            schema_hint=_require_text(values["schema_hint"], "schema_hint"),
            retrieved_at=_parse_aware_datetime(values["retrieved_at"], "retrieved_at"),
            row_count=_require_non_negative_int(values["row_count"], "row_count"),
            validation_policy=layout_policy,
        )

    @property
    def raw_object_ref(self) -> str:
        """Return a DATA-P08-compatible immutable raw ref."""

        return raw_object_ref_for_content_hash(self.content_hash)

    @property
    def logical_slot(self) -> tuple[str, str, str]:
        """Return the source/request/chunk slot protected by no-overwrite checks."""

        return (self.source, self.request_id, self.chunk_id)

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable raw object metadata record."""

        return MappingProxyType(
            {
                "raw_object_id": self.raw_object_id,
                "source": self.source,
                "request_id": self.request_id,
                "chunk_id": self.chunk_id,
                "path": self.path.as_posix(),
                "content_hash": self.content_hash,
                "schema_hint": self.schema_hint,
                "retrieved_at": self.retrieved_at.isoformat(),
                "row_count": self.row_count,
            }
        )


def assert_raw_slot_immutable(
    existing: RawDataObject | Mapping[str, object] | None,
    candidate: RawDataObject | Mapping[str, object],
) -> RawDataObject:
    """Reject binding a different content hash to an existing logical raw slot."""

    candidate_object = (
        candidate if isinstance(candidate, RawDataObject) else RawDataObject.from_mapping(candidate)
    )
    if existing is None:
        return candidate_object
    existing_object = (
        existing if isinstance(existing, RawDataObject) else RawDataObject.from_mapping(existing)
    )
    if existing_object.logical_slot != candidate_object.logical_slot:
        return candidate_object
    if existing_object.content_hash != candidate_object.content_hash:
        msg = "raw object slot is immutable; a different content_hash would overwrite raw data"
        raise DataFoundationValidationError(msg)
    return existing_object


class ParsedBarRecord:
    """DATA-P14 placeholder for a provider-shaped parsed bar record."""


class CanonicalBarRecord:
    """DATA-P15 placeholder for a research-ready canonical bar record."""


class TimestampSemanticsPolicy:
    """DATA-P15 placeholder for canonical timestamp semantics."""


__all__ = [
    "CanonicalBarRecord",
    "ParsedBarRecord",
    "RAW_DATA_LAKE_SUBDIR",
    "RAW_DATA_OBJECT_SUFFIX",
    "REPO_DATA_PLACEHOLDER_FILENAMES",
    "REQUIRED_RAW_DATA_OBJECT_FIELDS",
    "RawDataLakeLayoutPolicy",
    "RawDataObject",
    "TimestampSemanticsPolicy",
    "assert_raw_slot_immutable",
    "raw_object_ref_for_content_hash",
    "require_raw_data_lake_layout_policy",
    "resolve_raw_object_storage_path",
]
