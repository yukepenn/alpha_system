"""Study configuration model for intraday factor diagnostics."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DIAGNOSTIC_TYPES: tuple[str, ...] = (
    "directional",
    "buckets",
    "events",
    "regimes",
    "execution_filters",
    "management_features",
)
DEFAULT_MIN_TOTAL = 30
DEFAULT_MIN_BUCKET = 5
DEFAULT_MIN_EVENT = 5
DEFAULT_MAX_MISSING_LABEL_RATE = 0.1
DEFAULT_MAX_MISSING_FACTOR_RATE = 0.2


class StudyConfigError(ValueError):
    """Raised when a study configuration is incomplete or invalid."""


@dataclass(frozen=True, slots=True)
class SampleSizeThresholds:
    min_total: int = DEFAULT_MIN_TOTAL
    min_bucket: int = DEFAULT_MIN_BUCKET
    min_event: int = DEFAULT_MIN_EVENT
    max_missing_label_rate: float = DEFAULT_MAX_MISSING_LABEL_RATE
    max_missing_factor_rate: float = DEFAULT_MAX_MISSING_FACTOR_RATE

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> "SampleSizeThresholds":
        if payload is None:
            return cls()
        return cls(
            min_total=_non_negative_int(payload.get("min_total", DEFAULT_MIN_TOTAL), "min_total"),
            min_bucket=_non_negative_int(payload.get("min_bucket", DEFAULT_MIN_BUCKET), "min_bucket"),
            min_event=_non_negative_int(payload.get("min_event", DEFAULT_MIN_EVENT), "min_event"),
            max_missing_label_rate=_rate(
                payload.get("max_missing_label_rate", DEFAULT_MAX_MISSING_LABEL_RATE),
                "max_missing_label_rate",
            ),
            max_missing_factor_rate=_rate(
                payload.get("max_missing_factor_rate", DEFAULT_MAX_MISSING_FACTOR_RATE),
                "max_missing_factor_rate",
            ),
        )


@dataclass(frozen=True, slots=True)
class StudyConfig:
    study_id: str
    factor_id: str
    factor_version: str
    label_id: str
    label_version: str
    data_version: str
    factor_values_path: str
    labels_path: str
    horizon_seconds: int | None = None
    start_ts: datetime | None = None
    end_ts: datetime | None = None
    instruments: tuple[str, ...] = ()
    sessions: tuple[str, ...] = ()
    sample_size_thresholds: SampleSizeThresholds = field(default_factory=SampleSizeThresholds)
    output_dir: str | None = None
    registry_path: str | None = None
    manifest_path: str | None = None
    diagnostic_types: tuple[str, ...] = DEFAULT_DIAGNOSTIC_TYPES
    bucket_count: int = 5
    engine_version: str = "intraday_factor_diagnostics_v1"

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "StudyConfig":
        """Build and validate a study config from JSON-like data."""
        required = (
            "study_id",
            "factor_id",
            "factor_version",
            "label_id",
            "label_version",
            "data_version",
            "factor_values_path",
            "labels_path",
        )
        missing = tuple(field for field in required if not str(payload.get(field, "")).strip())
        if missing:
            msg = f"study config missing required fields: {', '.join(missing)}"
            raise StudyConfigError(msg)

        bucket_count = _positive_int(payload.get("bucket_count", 5), "bucket_count")
        if bucket_count < 2:
            msg = "bucket_count must be at least 2"
            raise StudyConfigError(msg)

        return cls(
            study_id=_text(payload["study_id"], "study_id"),
            factor_id=_text(payload["factor_id"], "factor_id"),
            factor_version=_text(payload["factor_version"], "factor_version"),
            label_id=_text(payload["label_id"], "label_id"),
            label_version=_text(payload["label_version"], "label_version"),
            data_version=_text(payload["data_version"], "data_version"),
            factor_values_path=_text(payload["factor_values_path"], "factor_values_path"),
            labels_path=_text(payload["labels_path"], "labels_path"),
            horizon_seconds=_optional_positive_int(payload.get("horizon_seconds"), "horizon_seconds"),
            start_ts=_optional_datetime(payload.get("start_ts"), "start_ts"),
            end_ts=_optional_datetime(payload.get("end_ts"), "end_ts"),
            instruments=_text_tuple(payload.get("instruments", ()), "instruments"),
            sessions=_text_tuple(payload.get("sessions", ()), "sessions"),
            sample_size_thresholds=SampleSizeThresholds.from_mapping(
                payload.get("sample_size_thresholds")
            ),
            output_dir=_optional_text(payload.get("output_dir"), "output_dir"),
            registry_path=_optional_text(payload.get("registry_path"), "registry_path"),
            manifest_path=_optional_text(payload.get("manifest_path"), "manifest_path"),
            diagnostic_types=_diagnostic_types(payload.get("diagnostic_types")),
            bucket_count=bucket_count,
            engine_version=_optional_text(payload.get("engine_version"), "engine_version")
            or "intraday_factor_diagnostics_v1",
        )

    def with_overrides(self, **overrides: Any) -> "StudyConfig":
        """Return a config with non-None CLI overrides applied."""
        updates = {key: value for key, value in overrides.items() if value is not None}
        if "start_ts" in updates:
            updates["start_ts"] = _optional_datetime(updates["start_ts"], "start_ts")
        if "end_ts" in updates:
            updates["end_ts"] = _optional_datetime(updates["end_ts"], "end_ts")
        if "horizon_seconds" in updates:
            updates["horizon_seconds"] = _optional_positive_int(
                updates["horizon_seconds"],
                "horizon_seconds",
            )
        if "instruments" in updates:
            updates["instruments"] = _text_tuple(updates["instruments"], "instruments")
        if "sessions" in updates:
            updates["sessions"] = _text_tuple(updates["sessions"], "sessions")
        if "min_total" in updates:
            thresholds = replace(
                self.sample_size_thresholds,
                min_total=_non_negative_int(updates.pop("min_total"), "min_total"),
            )
            updates["sample_size_thresholds"] = thresholds
        return replace(self, **updates)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["start_ts"] = _datetime_to_text(self.start_ts)
        payload["end_ts"] = _datetime_to_text(self.end_ts)
        payload["sample_size_thresholds"] = asdict(self.sample_size_thresholds)
        payload["instruments"] = list(self.instruments)
        payload["sessions"] = list(self.sessions)
        payload["diagnostic_types"] = list(self.diagnostic_types)
        return payload


def load_study_config(path: str | Path) -> StudyConfig:
    """Load a JSON study config from disk."""
    config_path = Path(path).expanduser().resolve(strict=False)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        msg = "study config root must be a JSON object"
        raise StudyConfigError(msg)
    return StudyConfig.from_mapping(payload)


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise StudyConfigError(msg)
    return value.strip()


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    return _text(value, field_name)


def _text_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (_text(value, field_name),)
    if not isinstance(value, Sequence):
        msg = f"{field_name} must be a string or sequence of strings"
        raise StudyConfigError(msg)
    return tuple(_text(item, field_name) for item in value)


def _diagnostic_types(value: Any) -> tuple[str, ...]:
    if value is None:
        return DEFAULT_DIAGNOSTIC_TYPES
    diagnostics = _text_tuple(value, "diagnostic_types")
    return tuple(item.strip().lower() for item in diagnostics)


def _optional_datetime(value: Any, field_name: str) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        active = value
    elif isinstance(value, str):
        try:
            active = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be ISO-8601 datetime text"
            raise StudyConfigError(msg) from exc
    else:
        msg = f"{field_name} must be datetime or ISO-8601 text"
        raise StudyConfigError(msg)
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc)


def _datetime_to_text(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        msg = f"{field_name} must be a positive integer"
        raise StudyConfigError(msg)
    try:
        active = int(value)
    except (TypeError, ValueError) as exc:
        msg = f"{field_name} must be a positive integer"
        raise StudyConfigError(msg) from exc
    if active <= 0:
        msg = f"{field_name} must be positive"
        raise StudyConfigError(msg)
    return active


def _optional_positive_int(value: Any, field_name: str) -> int | None:
    if value in (None, ""):
        return None
    return _positive_int(value, field_name)


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        msg = f"{field_name} must be a non-negative integer"
        raise StudyConfigError(msg)
    try:
        active = int(value)
    except (TypeError, ValueError) as exc:
        msg = f"{field_name} must be a non-negative integer"
        raise StudyConfigError(msg) from exc
    if active < 0:
        msg = f"{field_name} must be non-negative"
        raise StudyConfigError(msg)
    return active


def _rate(value: Any, field_name: str) -> float:
    if isinstance(value, bool):
        msg = f"{field_name} must be a rate between 0 and 1"
        raise StudyConfigError(msg)
    try:
        active = float(value)
    except (TypeError, ValueError) as exc:
        msg = f"{field_name} must be a rate between 0 and 1"
        raise StudyConfigError(msg) from exc
    if active < 0 or active > 1:
        msg = f"{field_name} must be between 0 and 1"
        raise StudyConfigError(msg)
    return active
