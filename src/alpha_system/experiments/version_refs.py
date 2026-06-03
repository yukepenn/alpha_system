"""Structured version reference validation for experiment metadata."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any


_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/+~-]{0,127}$")


class VersionRefError(ValueError):
    """Raised when a version reference is missing or malformed."""


def _require_text(value: str, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        msg = f"{field_name} must be non-empty"
        raise VersionRefError(msg)
    if any(ord(char) < 32 for char in text):
        msg = f"{field_name} must not contain control characters"
        raise VersionRefError(msg)
    if not _TOKEN_PATTERN.match(text):
        msg = f"{field_name} has invalid version-reference syntax: {text!r}"
        raise VersionRefError(msg)
    return text


def validate_version_map(
    values: Mapping[str, str],
    field_name: str,
    *,
    allow_empty: bool = False,
) -> dict[str, str]:
    """Validate and normalize an id-to-version mapping."""
    if not isinstance(values, Mapping):
        msg = f"{field_name} must be a mapping"
        raise VersionRefError(msg)
    if not values and not allow_empty:
        msg = f"{field_name} must contain at least one version reference"
        raise VersionRefError(msg)

    normalized: dict[str, str] = {}
    for key, value in values.items():
        normalized[_require_text(str(key), f"{field_name} key")] = _require_text(
            str(value),
            f"{field_name}[{key!r}]",
        )
    return dict(sorted(normalized.items()))


@dataclass(frozen=True, slots=True)
class DataVersionRef:
    """A required dataset version reference."""

    data_version: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "data_version",
            _require_text(self.data_version, "data_version"),
        )


@dataclass(frozen=True, slots=True)
class FactorVersionRef:
    """A required factor id/version pair."""

    factor_id: str
    factor_version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "factor_id", _require_text(self.factor_id, "factor_id"))
        object.__setattr__(
            self,
            "factor_version",
            _require_text(self.factor_version, "factor_version"),
        )


@dataclass(frozen=True, slots=True)
class LabelVersionRef:
    """A required label id/version pair."""

    label_id: str
    label_version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "label_id", _require_text(self.label_id, "label_id"))
        object.__setattr__(
            self,
            "label_version",
            _require_text(self.label_version, "label_version"),
        )


@dataclass(frozen=True, slots=True)
class EngineVersionRef:
    """A required experiment engine version reference."""

    engine_version: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "engine_version",
            _require_text(self.engine_version, "engine_version"),
        )


@dataclass(frozen=True, slots=True)
class VersionReferences:
    """The full version-reference block required for reproducible runs."""

    data_version: str
    factor_versions: Mapping[str, str]
    label_versions: Mapping[str, str]
    engine_version: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "data_version",
            DataVersionRef(self.data_version).data_version,
        )
        object.__setattr__(
            self,
            "factor_versions",
            validate_version_map(
                self.factor_versions,
                "factor_versions",
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "label_versions",
            validate_version_map(
                self.label_versions,
                "label_versions",
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "engine_version",
            EngineVersionRef(self.engine_version).engine_version,
        )

    def validate_requirements(
        self,
        *,
        require_factor_versions: bool,
        require_label_versions: bool,
    ) -> None:
        """Enforce run-category-specific factor and label requirements."""
        if require_factor_versions and not self.factor_versions:
            raise VersionRefError("factor_versions must contain at least one version reference")
        if require_label_versions and not self.label_versions:
            raise VersionRefError("label_versions must contain at least one version reference")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
