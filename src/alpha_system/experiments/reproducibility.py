"""Reproducibility metadata assembly and completeness checks."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from alpha_system.core.git_info import capture_git_info
from alpha_system.core.hashing import hash_code_paths, hash_config
from alpha_system.experiments.version_refs import VersionReferences, VersionRefError


class ReproducibilityError(ValueError):
    """Raised when reproducibility metadata cannot be assembled or validated."""


@dataclass(frozen=True, slots=True)
class ReproducibilityMetadata:
    """Required metadata for reproducing an experiment run."""

    git_commit: str | None
    git_dirty: bool | None
    code_hash: str
    config_hash: str
    data_version: str
    factor_versions: Mapping[str, str]
    label_versions: Mapping[str, str]
    engine_version: str

    def __post_init__(self) -> None:
        try:
            refs = VersionReferences(
                data_version=self.data_version,
                factor_versions=self.factor_versions,
                label_versions=self.label_versions,
                engine_version=self.engine_version,
            )
        except VersionRefError as exc:
            raise ReproducibilityError(str(exc)) from exc
        object.__setattr__(self, "data_version", refs.data_version)
        object.__setattr__(self, "factor_versions", refs.factor_versions)
        object.__setattr__(self, "label_versions", refs.label_versions)
        object.__setattr__(self, "engine_version", refs.engine_version)
        object.__setattr__(self, "code_hash", _require_hash_text(self.code_hash, "code_hash"))
        object.__setattr__(self, "config_hash", _require_hash_text(self.config_hash, "config_hash"))
        if self.git_commit is not None and not str(self.git_commit).strip():
            raise ReproducibilityError("git_commit must be non-empty when provided")

    def missing_fields(
        self,
        *,
        require_factor_versions: bool = True,
        require_label_versions: bool = False,
        require_git_commit: bool = True,
    ) -> tuple[str, ...]:
        """Return the missing reproducibility fields for a run requirement set."""
        missing: list[str] = []
        if require_git_commit and not self.git_commit:
            missing.append("git_commit")
        if not self.code_hash:
            missing.append("code_hash")
        if not self.config_hash:
            missing.append("config_hash")
        if not self.data_version:
            missing.append("data_version")
        if require_factor_versions and not self.factor_versions:
            missing.append("factor_versions")
        if require_label_versions and not self.label_versions:
            missing.append("label_versions")
        if not self.engine_version:
            missing.append("engine_version")
        return tuple(missing)

    def is_complete(
        self,
        *,
        require_factor_versions: bool = True,
        require_label_versions: bool = False,
        require_git_commit: bool = True,
    ) -> bool:
        return not self.missing_fields(
            require_factor_versions=require_factor_versions,
            require_label_versions=require_label_versions,
            require_git_commit=require_git_commit,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _require_hash_text(value: str, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ReproducibilityError(f"{field_name} must be non-empty")
    return text


def build_reproducibility_metadata(
    *,
    config: Mapping[str, Any] | None = None,
    config_hash: str | None = None,
    code_paths: Iterable[str | Path] | None = None,
    code_hash: str | None = None,
    data_version: str,
    factor_versions: Mapping[str, str] | None = None,
    label_versions: Mapping[str, str] | None = None,
    engine_version: str,
    repo_root: str | Path = ".",
) -> ReproducibilityMetadata:
    """Assemble reproducibility metadata using existing git and hashing helpers."""
    if config_hash is None:
        if config is None:
            raise ReproducibilityError("config or config_hash is required")
        config_hash = hash_config(config)
    if code_hash is None:
        if code_paths is None:
            raise ReproducibilityError("code_paths or code_hash is required")
        code_hash = hash_code_paths(code_paths, root=repo_root)

    git_info = capture_git_info(repo_root)
    return ReproducibilityMetadata(
        git_commit=git_info.commit,
        git_dirty=git_info.dirty,
        code_hash=code_hash,
        config_hash=config_hash,
        data_version=data_version,
        factor_versions=dict(factor_versions or {}),
        label_versions=dict(label_versions or {}),
        engine_version=engine_version,
    )


def check_reproducibility_completeness(
    metadata: ReproducibilityMetadata,
    *,
    require_factor_versions: bool = True,
    require_label_versions: bool = False,
    require_git_commit: bool = True,
) -> tuple[str, ...]:
    """Return missing fields without mutating or writing registry state."""
    return metadata.missing_fields(
        require_factor_versions=require_factor_versions,
        require_label_versions=require_label_versions,
        require_git_commit=require_git_commit,
    )
