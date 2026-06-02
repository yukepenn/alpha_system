"""Shared type aliases for schema-only domain contracts."""

from __future__ import annotations

from typing import Any, Mapping, TypeAlias

ArtifactPaths: TypeAlias = Mapping[str, str]
ConfigParameters: TypeAlias = Mapping[str, Any]
ContractMetadata: TypeAlias = Mapping[str, Any]
QualityFlags: TypeAlias = tuple[str, ...]
VersionMap: TypeAlias = Mapping[str, str]
