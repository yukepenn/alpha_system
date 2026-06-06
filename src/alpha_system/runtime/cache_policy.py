"""Lineage-keyed local cache policy for derived runtime summaries."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.serialization import content_hash as governance_content_hash
from alpha_system.runtime.artifact_policy import (
    CURATED_COMMIT_KINDS,
    forbidden_kind_classes,
)

RUNTIME_CACHE_POLICY_SCHEMA = "alpha_system.runtime.cache_policy.v1"
RUNTIME_CACHE_METADATA_SCHEMA = "alpha_system.runtime.cache_metadata.v1"
RUNTIME_CACHE_KEY_PREFIX = "rcache"
DEFAULT_CACHE_NAMESPACE = "derived_summaries"


class RuntimeCachePolicyError(ValueError):
    """Raised when cache policy inputs would violate local artifact rules."""


class RuntimeCacheLookupState(StrEnum):
    """Deterministic lookup state for local runtime cache metadata."""

    HIT = "hit"
    MISS = "miss"
    STALE = "stale"


class RuntimeCacheStorageKind(StrEnum):
    """Local-only storage root kind for runtime cache metadata and summaries."""

    ALPHA_DATA_ROOT = "alpha_data_root"
    RUN_ARTIFACTS = "run_artifacts"


@dataclass(frozen=True, slots=True)
class RuntimeCacheVersionRef:
    """Reference-only version token included in cache lineage."""

    name: str
    version: str
    content_hash: str
    lineage_ref: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _required_string(self.name, field="name"))
        object.__setattr__(self, "version", _required_string(self.version, field="version"))
        object.__setattr__(
            self,
            "content_hash",
            _required_string(self.content_hash, field="content_hash"),
        )
        if self.lineage_ref is not None:
            object.__setattr__(
                self,
                "lineage_ref",
                _required_string(self.lineage_ref, field="lineage_ref"),
            )

    def to_dict(self) -> dict[str, str | None]:
        """Return a stable JSON-compatible version reference."""

        return {
            "name": self.name,
            "version": self.version,
            "content_hash": self.content_hash,
            "lineage_ref": self.lineage_ref,
        }


@dataclass(frozen=True, slots=True, init=False)
class RuntimeCacheLineage:
    """Reproducibility lineage that invalidates derived-summary cache entries."""

    dataset_version_id: str
    dataset_version_hash: str
    feature_pack_versions: tuple[RuntimeCacheVersionRef, ...]
    label_pack_versions: tuple[RuntimeCacheVersionRef, ...]
    code_version: str
    code_content_hash: str
    config_version: str
    config_hash: str
    run_scope: Mapping[str, JsonValue]
    cost_model_version: str | None
    cost_model_hash: str | None

    def __init__(
        self,
        *,
        dataset_version_id: str,
        dataset_version_hash: str,
        feature_pack_versions: Sequence[RuntimeCacheVersionRef | Mapping[str, Any]],
        label_pack_versions: Sequence[RuntimeCacheVersionRef | Mapping[str, Any]],
        code_version: str,
        code_content_hash: str,
        config_version: str,
        config_hash: str,
        run_scope: Mapping[str, JsonValue] | None = None,
        cost_model_version: str | None = None,
        cost_model_hash: str | None = None,
    ) -> None:
        feature_refs = _coerce_version_refs(feature_pack_versions, field="feature_pack_versions")
        label_refs = _coerce_version_refs(label_pack_versions, field="label_pack_versions")
        if not feature_refs:
            raise RuntimeCachePolicyError("feature_pack_versions must not be empty")
        if not label_refs:
            raise RuntimeCachePolicyError("label_pack_versions must not be empty")

        normalized_cost_version = _optional_string(cost_model_version, field="cost_model_version")
        normalized_cost_hash = _optional_string(cost_model_hash, field="cost_model_hash")
        if (normalized_cost_version is None) != (normalized_cost_hash is None):
            raise RuntimeCachePolicyError(
                "cost_model_version and cost_model_hash must be supplied together"
            )

        scope = dict(run_scope or {})
        governance_content_hash(cast(JsonValue, scope))

        object.__setattr__(
            self,
            "dataset_version_id",
            _required_string(dataset_version_id, field="dataset_version_id"),
        )
        object.__setattr__(
            self,
            "dataset_version_hash",
            _required_string(dataset_version_hash, field="dataset_version_hash"),
        )
        object.__setattr__(self, "feature_pack_versions", feature_refs)
        object.__setattr__(self, "label_pack_versions", label_refs)
        object.__setattr__(
            self, "code_version", _required_string(code_version, field="code_version")
        )
        object.__setattr__(
            self,
            "code_content_hash",
            _required_string(code_content_hash, field="code_content_hash"),
        )
        object.__setattr__(
            self,
            "config_version",
            _required_string(config_version, field="config_version"),
        )
        object.__setattr__(
            self,
            "config_hash",
            _required_string(config_hash, field="config_hash"),
        )
        object.__setattr__(self, "run_scope", MappingProxyType(scope))
        object.__setattr__(self, "cost_model_version", normalized_cost_version)
        object.__setattr__(self, "cost_model_hash", normalized_cost_hash)

    @classmethod
    def from_study_run_manifest(
        cls,
        manifest: object,
        *,
        run_scope: Mapping[str, JsonValue] | None = None,
    ) -> RuntimeCacheLineage:
        """Build cache lineage from a StudyRunManifest-like object."""

        return cls(
            dataset_version_id=getattr(manifest, "dataset_version_id"),
            dataset_version_hash=getattr(manifest, "dataset_version_hash"),
            feature_pack_versions=[
                {
                    "name": getattr(ref, "pack_id"),
                    "version": getattr(ref, "pack_id"),
                    "content_hash": getattr(ref, "content_hash"),
                    "lineage_ref": getattr(ref, "lineage_ref"),
                }
                for ref in getattr(manifest, "feature_pack_versions")
            ],
            label_pack_versions=[
                {
                    "name": getattr(ref, "pack_id"),
                    "version": getattr(ref, "pack_id"),
                    "content_hash": getattr(ref, "content_hash"),
                    "lineage_ref": getattr(ref, "lineage_ref"),
                }
                for ref in getattr(manifest, "label_pack_versions")
            ],
            code_version=getattr(manifest, "code_version"),
            code_content_hash=getattr(manifest, "code_content_hash"),
            config_version=getattr(manifest, "config_version"),
            config_hash=getattr(manifest, "config_hash"),
            run_scope=run_scope,
            cost_model_version=getattr(manifest, "cost_model_version", None),
            cost_model_hash=getattr(manifest, "cost_model_hash", None),
        )

    @property
    def lineage_hash(self) -> str:
        """Return the stable hash of the cache lineage."""

        return governance_content_hash(cast(JsonValue, self.to_dict()))

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a stable JSON-compatible lineage payload."""

        return {
            "schema": RUNTIME_CACHE_POLICY_SCHEMA,
            "dataset_version_id": self.dataset_version_id,
            "dataset_version_hash": self.dataset_version_hash,
            "feature_pack_versions": [
                cast(JsonValue, ref.to_dict()) for ref in self.feature_pack_versions
            ],
            "label_pack_versions": [
                cast(JsonValue, ref.to_dict()) for ref in self.label_pack_versions
            ],
            "code_version": self.code_version,
            "code_content_hash": self.code_content_hash,
            "config_version": self.config_version,
            "config_hash": self.config_hash,
            "run_scope": cast(JsonValue, dict(self.run_scope)),
            "cost_model_version": self.cost_model_version,
            "cost_model_hash": self.cost_model_hash,
        }


@dataclass(frozen=True, slots=True)
class RuntimeCacheKey:
    """Stable cache-key result for one derived summary."""

    summary_kind: str
    key: str
    lineage_hash: str
    payload_hash: str

    def to_metadata(self) -> dict[str, str]:
        """Return value-free cache metadata for later lookup decisions."""

        return {
            "schema": RUNTIME_CACHE_METADATA_SCHEMA,
            "summary_kind": self.summary_kind,
            "cache_key": self.key,
            "lineage_hash": self.lineage_hash,
            "payload_hash": self.payload_hash,
        }


@dataclass(frozen=True, slots=True)
class RuntimeCacheMetadata:
    """Value-free local metadata read by the cache lookup decision surface."""

    schema: str
    summary_kind: str
    cache_key: str
    lineage_hash: str
    payload_hash: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> RuntimeCacheMetadata:
        """Coerce value-free cache metadata from a mapping."""

        return cls(
            schema=_required_string(value.get("schema"), field="schema"),
            summary_kind=_required_string(value.get("summary_kind"), field="summary_kind"),
            cache_key=_required_string(value.get("cache_key"), field="cache_key"),
            lineage_hash=_required_string(value.get("lineage_hash"), field="lineage_hash"),
            payload_hash=_required_string(value.get("payload_hash"), field="payload_hash"),
        )


@dataclass(frozen=True, slots=True)
class RuntimeCacheLookupDecision:
    """Deterministic cache lookup result without touching cache contents."""

    state: RuntimeCacheLookupState
    expected_key: str
    observed_key: str | None
    reasons: tuple[str, ...]

    @property
    def hit(self) -> bool:
        """Return whether metadata is a valid cache hit."""

        return self.state is RuntimeCacheLookupState.HIT

    @property
    def miss(self) -> bool:
        """Return whether metadata is absent."""

        return self.state is RuntimeCacheLookupState.MISS

    @property
    def stale(self) -> bool:
        """Return whether metadata exists but is invalid for the current lineage."""

        return self.state is RuntimeCacheLookupState.STALE


@dataclass(frozen=True, slots=True)
class RuntimeCacheRoot:
    """Resolved local-only cache storage root."""

    path: Path
    storage_kind: RuntimeCacheStorageKind
    local_only: bool = True
    commit_allowed: bool = False


@dataclass(frozen=True, slots=True)
class RuntimeCachePolicy:
    """Metadata-only cache policy for derived runtime summaries."""

    namespace: str = DEFAULT_CACHE_NAMESPACE
    storage_root: str | os.PathLike[str] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "namespace", _normalize_namespace(self.namespace))

    def derive_cache_key(
        self,
        *,
        lineage: RuntimeCacheLineage,
        summary_kind: str,
    ) -> RuntimeCacheKey:
        """Derive a cache key from summary kind and complete reproducibility lineage."""

        if not isinstance(lineage, RuntimeCacheLineage):
            raise RuntimeCachePolicyError("lineage must be a RuntimeCacheLineage")
        normalized_summary_kind = _require_cacheable_summary_kind(summary_kind)
        lineage_hash = lineage.lineage_hash
        payload = {
            "schema": RUNTIME_CACHE_POLICY_SCHEMA,
            "namespace": self.namespace,
            "summary_kind": normalized_summary_kind,
            "lineage_hash": lineage_hash,
            "lineage": lineage.to_dict(),
        }
        payload_hash = governance_content_hash(cast(JsonValue, payload))

        return RuntimeCacheKey(
            summary_kind=normalized_summary_kind,
            key=f"{RUNTIME_CACHE_KEY_PREFIX}_{payload_hash[:32]}",
            lineage_hash=lineage_hash,
            payload_hash=payload_hash,
        )

    def metadata_for(
        self,
        *,
        lineage: RuntimeCacheLineage,
        summary_kind: str,
    ) -> RuntimeCacheMetadata:
        """Return value-free metadata for a derived summary cache entry."""

        return RuntimeCacheMetadata.from_mapping(
            self.derive_cache_key(lineage=lineage, summary_kind=summary_kind).to_metadata()
        )

    def lookup(
        self,
        *,
        lineage: RuntimeCacheLineage,
        summary_kind: str,
        existing_metadata: RuntimeCacheMetadata | Mapping[str, Any] | None,
    ) -> RuntimeCacheLookupDecision:
        """Classify existing cache metadata as hit, miss, or stale."""

        expected = self.derive_cache_key(lineage=lineage, summary_kind=summary_kind)
        if existing_metadata is None:
            return RuntimeCacheLookupDecision(
                state=RuntimeCacheLookupState.MISS,
                expected_key=expected.key,
                observed_key=None,
                reasons=("cache_metadata_absent",),
            )

        metadata = (
            existing_metadata
            if isinstance(existing_metadata, RuntimeCacheMetadata)
            else RuntimeCacheMetadata.from_mapping(existing_metadata)
        )
        reasons: list[str] = []
        if metadata.schema != RUNTIME_CACHE_METADATA_SCHEMA:
            reasons.append("cache_metadata_schema_changed")
        if metadata.summary_kind != expected.summary_kind:
            reasons.append("summary_kind_changed")
        if metadata.lineage_hash != expected.lineage_hash:
            reasons.append("lineage_changed")
        if metadata.cache_key != expected.key or metadata.payload_hash != expected.payload_hash:
            reasons.append("cache_key_changed")

        if reasons:
            return RuntimeCacheLookupDecision(
                state=RuntimeCacheLookupState.STALE,
                expected_key=expected.key,
                observed_key=metadata.cache_key,
                reasons=tuple(dict.fromkeys(reasons)),
            )

        return RuntimeCacheLookupDecision(
            state=RuntimeCacheLookupState.HIT,
            expected_key=expected.key,
            observed_key=metadata.cache_key,
            reasons=("cache_metadata_matches_lineage",),
        )

    def resolve_storage_root(
        self,
        *,
        alpha_data_root: str | os.PathLike[str] | None = None,
        run_root: str | os.PathLike[str] | None = None,
        repo_root: str | os.PathLike[str] | None = None,
    ) -> RuntimeCacheRoot:
        """Resolve the local-only cache root without creating directories."""

        repo_path = _resolved_path(repo_root) if repo_root is not None else None

        if self.storage_root is not None:
            root = _resolved_path(self.storage_root, base=repo_path)
            storage_kind = (
                RuntimeCacheStorageKind.RUN_ARTIFACTS
                if _has_path_segment(root, "runs")
                else RuntimeCacheStorageKind.ALPHA_DATA_ROOT
            )
        else:
            alpha_root = alpha_data_root or os.environ.get("ALPHA_DATA_ROOT")
            if alpha_root:
                root = _resolved_path(alpha_root) / "runtime" / "cache" / self.namespace
                storage_kind = RuntimeCacheStorageKind.ALPHA_DATA_ROOT
            elif run_root is not None:
                root = _resolved_path(run_root, base=repo_path) / "cache" / self.namespace
                storage_kind = RuntimeCacheStorageKind.RUN_ARTIFACTS
            else:
                raise RuntimeCachePolicyError("ALPHA_DATA_ROOT or run_root is required")

        if storage_kind is RuntimeCacheStorageKind.RUN_ARTIFACTS:
            if not _has_path_segment(root, "runs"):
                raise RuntimeCachePolicyError("run-local cache roots must be under runs/**")
        elif repo_path is not None and _is_relative_to(root, repo_path):
            raise RuntimeCachePolicyError(
                "runtime cache roots must not resolve inside the repo tree"
            )

        return RuntimeCacheRoot(path=root, storage_kind=storage_kind)


def _coerce_version_refs(
    values: Sequence[RuntimeCacheVersionRef | Mapping[str, Any]],
    *,
    field: str,
) -> tuple[RuntimeCacheVersionRef, ...]:
    refs: list[RuntimeCacheVersionRef] = []
    for value in values:
        if isinstance(value, RuntimeCacheVersionRef):
            refs.append(value)
            continue
        if not isinstance(value, Mapping):
            raise RuntimeCachePolicyError(f"{field} must contain version-reference mappings")
        name = value.get("name", value.get("pack_id"))
        version = value.get("version", value.get("pack_id", name))
        refs.append(
            RuntimeCacheVersionRef(
                name=name,
                version=version,
                content_hash=value.get("content_hash"),
                lineage_ref=value.get("lineage_ref"),
            )
        )
    return tuple(sorted(refs, key=lambda ref: (ref.name, ref.version, ref.content_hash)))


def _require_cacheable_summary_kind(value: object) -> str:
    summary_kind = _required_string(value, field="summary_kind").lower()
    if summary_kind not in CURATED_COMMIT_KINDS:
        raise RuntimeCachePolicyError("runtime cache may only cache derived summary kinds")
    forbidden = forbidden_kind_classes(summary_kind)
    if forbidden:
        raise RuntimeCachePolicyError(
            "runtime cache may not cache raw, heavy, or value-bearing outputs"
        )
    return summary_kind


def _normalize_namespace(value: str) -> str:
    namespace = _required_string(value, field="namespace").strip("/")
    parts = namespace.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise RuntimeCachePolicyError("cache namespace must be relative path segments")
    return namespace


def _required_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeCachePolicyError(f"{field} is required")
    return value.strip()


def _optional_string(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    return _required_string(value, field=field)


def _resolved_path(
    value: str | os.PathLike[str],
    *,
    base: Path | None = None,
) -> Path:
    path = Path(os.path.expandvars(os.fspath(value))).expanduser()
    if not path.is_absolute() and base is not None:
        path = base / path
    return path.resolve(strict=False)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _has_path_segment(path: Path, segment: str) -> bool:
    return segment in path.parts


__all__ = [
    "DEFAULT_CACHE_NAMESPACE",
    "RUNTIME_CACHE_KEY_PREFIX",
    "RUNTIME_CACHE_METADATA_SCHEMA",
    "RUNTIME_CACHE_POLICY_SCHEMA",
    "RuntimeCacheKey",
    "RuntimeCacheLineage",
    "RuntimeCacheLookupDecision",
    "RuntimeCacheLookupState",
    "RuntimeCacheMetadata",
    "RuntimeCachePolicy",
    "RuntimeCachePolicyError",
    "RuntimeCacheRoot",
    "RuntimeCacheStorageKind",
    "RuntimeCacheVersionRef",
]
