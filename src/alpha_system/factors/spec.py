"""Validated factor specification contract."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from alpha_system.core.enums import (
    FactorEvaluationType,
    FactorFrequency,
    FactorStatus,
    FactorType,
)
from alpha_system.core.hashing import hash_config
from alpha_system.factors.dependency_spec import (
    FactorDependencyError,
    FactorInputField,
    normalize_input_fields,
    validate_declared_dependencies,
)
from alpha_system.factors.lifecycle import (
    FactorLifecycleError,
    parse_factor_status,
    requires_validation_artifact,
)


class FactorSpecError(ValueError):
    """Raised when a FactorSpec mapping or field is invalid."""


REQUIRED_FACTOR_SPEC_FIELDS: tuple[str, ...] = (
    "factor_id",
    "name",
    "version",
    "owner",
    "description",
    "input_fields",
    "parameters",
    "frequency",
    "warmup_bars",
    "session_reset",
    "availability_lag",
    "factor_type",
    "evaluation_type",
    "code_hash",
    "config_hash",
    "status",
    "created_at",
    "validation_artifact_path",
)

FORBIDDEN_ARTIFACT_SUFFIXES: tuple[str, ...] = (
    ".parquet",
    ".arrow",
    ".feather",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".db-journal",
    ".wal",
    ".log",
)

FORBIDDEN_ARTIFACT_PREFIXES: tuple[str, ...] = (
    "data/raw/",
    "data/canonical/",
    "data/factors/",
    "data/labels/",
    "data/cache/",
    "metadata/",
)

_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_VERSION_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True, kw_only=True)
class FactorSpec:
    """A versioned factor specification with validated governance fields."""

    factor_id: str
    name: str
    version: str
    owner: str
    description: str
    input_fields: tuple[FactorInputField, ...]
    parameters: Mapping[str, Any]
    frequency: FactorFrequency
    warmup_bars: int
    session_reset: bool
    availability_lag: timedelta
    factor_type: FactorType
    evaluation_type: FactorEvaluationType
    code_hash: str
    config_hash: str
    status: FactorStatus
    created_at: datetime
    validation_artifact_path: str | None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FactorSpec":
        """Build and validate a FactorSpec from a JSON-like mapping."""
        missing = tuple(field for field in REQUIRED_FACTOR_SPEC_FIELDS if field not in payload)
        if missing:
            msg = f"FactorSpec missing required fields: {', '.join(missing)}"
            raise FactorSpecError(msg)

        try:
            input_fields = normalize_input_fields(payload["input_fields"])
            status = parse_factor_status(payload["status"])
        except (FactorDependencyError, FactorLifecycleError) as exc:
            raise FactorSpecError(str(exc)) from exc

        validation_artifact_path = _optional_artifact_path(
            payload["validation_artifact_path"]
        )
        spec = cls(
            factor_id=_identifier(payload["factor_id"], "factor_id"),
            name=_required_string(payload["name"], "name"),
            version=_version(payload["version"]),
            owner=_required_string(payload["owner"], "owner"),
            description=_required_string(payload["description"], "description"),
            input_fields=input_fields,
            parameters=_mapping(payload["parameters"], "parameters"),
            frequency=_parse_enum(FactorFrequency, payload["frequency"], "frequency"),
            warmup_bars=_non_negative_int(payload["warmup_bars"], "warmup_bars"),
            session_reset=_bool(payload["session_reset"], "session_reset"),
            availability_lag=_availability_lag(payload["availability_lag"]),
            factor_type=_parse_enum(FactorType, payload["factor_type"], "factor_type"),
            evaluation_type=_parse_enum(
                FactorEvaluationType,
                payload["evaluation_type"],
                "evaluation_type",
            ),
            code_hash=_sha256(payload["code_hash"], "code_hash"),
            config_hash=_sha256(payload["config_hash"], "config_hash"),
            status=status,
            created_at=_datetime(payload["created_at"], "created_at"),
            validation_artifact_path=validation_artifact_path,
        )
        _validate_status_fields(spec)
        try:
            validate_declared_dependencies(spec.input_fields)
        except FactorDependencyError as exc:
            raise FactorSpecError(str(exc)) from exc
        return spec

    def to_dict(self) -> dict[str, Any]:
        """Serialize the spec to stable JSON-compatible values."""
        return {
            "availability_lag": _seconds_value(self.availability_lag),
            "code_hash": self.code_hash,
            "config_hash": self.config_hash,
            "created_at": _datetime_to_text(self.created_at),
            "description": self.description,
            "evaluation_type": self.evaluation_type.value,
            "factor_id": self.factor_id,
            "factor_type": self.factor_type.value,
            "frequency": self.frequency.value,
            "input_fields": [field.to_dict() for field in self.input_fields],
            "name": self.name,
            "owner": self.owner,
            "parameters": dict(self.parameters),
            "session_reset": self.session_reset,
            "status": self.status.value,
            "validation_artifact_path": self.validation_artifact_path,
            "version": self.version,
            "warmup_bars": self.warmup_bars,
        }


def compute_factor_config_hash(payload: Mapping[str, Any]) -> str:
    """Hash a FactorSpec config while excluding its self-referential config_hash."""
    return hash_config(
        {
            str(key): _normalize_hash_value(value)
            for key, value in payload.items()
            if str(key) != "config_hash"
        }
    )


def validate_factor_config_hash(payload: Mapping[str, Any], spec: FactorSpec) -> None:
    """Raise when a config mapping's deterministic hash differs from the spec."""
    actual = compute_factor_config_hash(payload)
    if actual != spec.config_hash:
        msg = (
            "config_hash mismatch: "
            f"expected {spec.config_hash}, computed {actual}"
        )
        raise FactorSpecError(msg)


def _validate_status_fields(spec: FactorSpec) -> None:
    if requires_validation_artifact(spec.status) and not spec.validation_artifact_path:
        msg = f"{spec.status.value} factors require validation_artifact_path"
        raise FactorSpecError(msg)
    if spec.validation_artifact_path is not None:
        _validate_artifact_reference(spec.validation_artifact_path)


def _validate_artifact_reference(value: str) -> None:
    normalized = value.strip().lower().replace("\\", "/")
    if normalized.startswith(("/mnt/c/", "/mnt/d/", "/mnt/e/")):
        msg = "validation_artifact_path must not point to a Windows-mounted path"
        raise FactorSpecError(msg)
    if any(marker in normalized for marker in ("onedrive", "dropbox", "google drive")):
        msg = "validation_artifact_path must not point to a synced folder"
        raise FactorSpecError(msg)
    if normalized.endswith(FORBIDDEN_ARTIFACT_SUFFIXES):
        msg = "validation_artifact_path must not reference DB, log, or factor data files"
        raise FactorSpecError(msg)
    if any(normalized.startswith(prefix) for prefix in FORBIDDEN_ARTIFACT_PREFIXES):
        msg = "validation_artifact_path must not reference forbidden repo artifact paths"
        raise FactorSpecError(msg)


def _required_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise FactorSpecError(msg)
    return value.strip()


def _identifier(value: Any, field_name: str) -> str:
    text = _required_string(value, field_name)
    if not _IDENTIFIER_RE.fullmatch(text):
        msg = f"{field_name} must match {_IDENTIFIER_RE.pattern}"
        raise FactorSpecError(msg)
    return text


def _version(value: Any) -> str:
    text = _required_string(value, "version")
    if not _VERSION_RE.fullmatch(text):
        msg = "version may contain only letters, numbers, underscores, dots, and dashes"
        raise FactorSpecError(msg)
    return text


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        msg = f"{field_name} must be a mapping"
        raise FactorSpecError(msg)
    return dict(value)


def _parse_enum(enum_type: Any, value: Any, field_name: str) -> Any:
    if isinstance(value, enum_type):
        return value
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise FactorSpecError(msg)
    try:
        return enum_type(value.strip())
    except ValueError as exc:
        allowed = ", ".join(item.value for item in enum_type)
        msg = f"{field_name} must be one of: {allowed}"
        raise FactorSpecError(msg) from exc


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be a non-negative integer"
        raise FactorSpecError(msg)
    if value < 0:
        msg = f"{field_name} must be non-negative"
        raise FactorSpecError(msg)
    return value


def _bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        msg = f"{field_name} must be a boolean"
        raise FactorSpecError(msg)
    return value


def _availability_lag(value: Any) -> timedelta:
    if isinstance(value, bool) or not isinstance(value, int | float):
        msg = "availability_lag must be a non-negative number of seconds"
        raise FactorSpecError(msg)
    if value < 0:
        msg = "availability_lag must be non-negative"
        raise FactorSpecError(msg)
    return timedelta(seconds=float(value))


def _sha256(value: Any, field_name: str) -> str:
    text = _required_string(value, field_name)
    if not _SHA256_RE.fullmatch(text):
        msg = f"{field_name} must be a lowercase SHA-256 hex digest"
        raise FactorSpecError(msg)
    return text


def _datetime(value: Any, field_name: str) -> datetime:
    text = _required_string(value, field_name)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        msg = f"{field_name} must be an ISO-8601 datetime"
        raise FactorSpecError(msg) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _optional_artifact_path(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        msg = "validation_artifact_path must be a string or null"
        raise FactorSpecError(msg)
    stripped = value.strip()
    return stripped or None


def _datetime_to_text(value: datetime) -> str:
    active = value
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _seconds_value(value: timedelta) -> int | float:
    seconds = value.total_seconds()
    if seconds.is_integer():
        return int(seconds)
    return seconds


def _normalize_hash_value(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, datetime):
        return _datetime_to_text(value)
    if isinstance(value, timedelta):
        return _seconds_value(value)
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_hash_value(item)
            for key, item in sorted(value.items(), key=lambda entry: str(entry[0]))
        }
    if isinstance(value, tuple | list):
        return [_normalize_hash_value(item) for item in value]
    return value
