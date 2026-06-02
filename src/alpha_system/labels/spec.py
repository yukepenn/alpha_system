"""Validated label record contract for future-looking research labels."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import MappingProxyType
from typing import Any

from alpha_system.core.enums import LabelType
from alpha_system.core.hashing import hash_config


class LabelSpecError(ValueError):
    """Raised when a label record mapping or field is invalid."""


REQUIRED_LABEL_RECORD_FIELDS: tuple[str, ...] = (
    "label_id",
    "instrument_id",
    "event_ts",
    "horizon",
    "label_type",
    "value",
    "path_metadata",
    "data_version",
    "label_available_ts",
)

STANDARD_LABEL_TYPES: tuple[LabelType, ...] = (
    LabelType.FORWARD_RETURN_1M,
    LabelType.FORWARD_RETURN_3M,
    LabelType.FORWARD_RETURN_5M,
    LabelType.FORWARD_RETURN_10M,
    LabelType.FORWARD_RETURN_30M,
    LabelType.MFE_BY_HORIZON,
    LabelType.MAE_BY_HORIZON,
    LabelType.TARGET_BEFORE_STOP,
    LabelType.STOP_BEFORE_TARGET,
    LabelType.FUTURE_REALIZED_VOLATILITY,
    LabelType.FUTURE_SPREAD_LIQUIDITY,
)

FORWARD_RETURN_LABEL_TYPES_BY_MINUTE: Mapping[int, LabelType] = MappingProxyType(
    {
        1: LabelType.FORWARD_RETURN_1M,
        3: LabelType.FORWARD_RETURN_3M,
        5: LabelType.FORWARD_RETURN_5M,
        10: LabelType.FORWARD_RETURN_10M,
        30: LabelType.FORWARD_RETURN_30M,
    }
)

_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_:-]*$")

LabelValue = Decimal | float | int | str | bool | None


@dataclass(frozen=True, slots=True, kw_only=True)
class LabelSpec:
    """One point-in-time label record with the required ASV1-P10 schema."""

    label_id: str
    instrument_id: str
    event_ts: datetime
    horizon: timedelta
    label_type: LabelType
    value: LabelValue
    path_metadata: Mapping[str, Any]
    data_version: str
    label_available_ts: datetime

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "LabelSpec":
        """Build and validate a label record from a JSON-like mapping."""
        missing = tuple(field for field in REQUIRED_LABEL_RECORD_FIELDS if field not in payload)
        if missing:
            msg = f"LabelSpec missing required fields: {', '.join(missing)}"
            raise LabelSpecError(msg)

        unexpected = tuple(field for field in payload if field not in REQUIRED_LABEL_RECORD_FIELDS)
        if unexpected:
            msg = f"LabelSpec has unexpected fields: {', '.join(unexpected)}"
            raise LabelSpecError(msg)

        spec = cls(
            label_id=_identifier(payload["label_id"], "label_id"),
            instrument_id=_required_string(payload["instrument_id"], "instrument_id"),
            event_ts=_datetime(payload["event_ts"], "event_ts"),
            horizon=_horizon(payload["horizon"]),
            label_type=_label_type(payload["label_type"]),
            value=_label_value(payload["value"]),
            path_metadata=_metadata(payload["path_metadata"]),
            data_version=_required_string(payload["data_version"], "data_version"),
            label_available_ts=_datetime(
                payload["label_available_ts"],
                "label_available_ts",
            ),
        )
        _validate_record_semantics(spec)
        return spec

    def to_dict(self) -> dict[str, Any]:
        """Serialize the label record in stable required-field order."""
        return {
            "label_id": self.label_id,
            "instrument_id": self.instrument_id,
            "event_ts": _datetime_to_text(self.event_ts),
            "horizon": int(self.horizon.total_seconds()),
            "label_type": self.label_type.value,
            "value": _serialize_value(self.value),
            "path_metadata": dict(self.path_metadata),
            "data_version": self.data_version,
            "label_available_ts": _datetime_to_text(self.label_available_ts),
        }


def label_record_field_names() -> tuple[str, ...]:
    """Return the dataclass field names for schema-order assertions."""
    return tuple(field.name for field in fields(LabelSpec))


def compute_label_config_hash(payload: Mapping[str, Any]) -> str:
    """Hash a label config while excluding its self-referential config_hash."""
    return hash_config(
        {
            str(key): _normalize_hash_value(value)
            for key, value in payload.items()
            if str(key) != "config_hash"
        }
    )


def parse_horizon_minutes(value: int | float | str | timedelta) -> int:
    """Return a positive whole-minute horizon from common serialized values."""
    horizon = _horizon(value)
    seconds = horizon.total_seconds()
    if seconds % 60 != 0:
        msg = "horizon must be an exact minute interval"
        raise LabelSpecError(msg)
    return int(seconds // 60)


def _validate_record_semantics(spec: LabelSpec) -> None:
    if spec.horizon <= timedelta(0):
        msg = "horizon must be positive"
        raise LabelSpecError(msg)
    if spec.label_type not in STANDARD_LABEL_TYPES:
        msg = f"unsupported label_type: {spec.label_type.value}"
        raise LabelSpecError(msg)
    if spec.label_available_ts < spec.event_ts:
        msg = "label_available_ts must be at or after event_ts"
        raise LabelSpecError(msg)


def _required_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise LabelSpecError(msg)
    return value.strip()


def _identifier(value: Any, field_name: str) -> str:
    text = _required_string(value, field_name)
    if not _IDENTIFIER_RE.fullmatch(text):
        msg = f"{field_name} must match {_IDENTIFIER_RE.pattern}"
        raise LabelSpecError(msg)
    return text


def _datetime(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            msg = f"{field_name} must be an ISO-8601 datetime"
            raise LabelSpecError(msg) from exc
    else:
        msg = f"{field_name} must be a datetime or ISO-8601 string"
        raise LabelSpecError(msg)

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise LabelSpecError(msg)
    return parsed.astimezone(timezone.utc)


def _datetime_to_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _horizon(value: Any) -> timedelta:
    if isinstance(value, timedelta):
        horizon = value
    elif isinstance(value, int | float) and not isinstance(value, bool):
        horizon = timedelta(seconds=float(value))
    elif isinstance(value, str):
        text = value.strip().lower()
        if text.endswith("m"):
            horizon = timedelta(minutes=float(text[:-1]))
        elif text.endswith("s"):
            horizon = timedelta(seconds=float(text[:-1]))
        elif text.endswith("h"):
            horizon = timedelta(hours=float(text[:-1]))
        else:
            horizon = timedelta(seconds=float(text))
    else:
        msg = "horizon must be a timedelta, seconds value, or duration string"
        raise LabelSpecError(msg)

    if horizon <= timedelta(0):
        msg = "horizon must be positive"
        raise LabelSpecError(msg)
    return horizon


def _label_type(value: Any) -> LabelType:
    if isinstance(value, LabelType):
        return value
    try:
        return LabelType(str(value))
    except ValueError as exc:
        msg = f"unsupported label_type: {value}"
        raise LabelSpecError(msg) from exc


def _label_value(value: Any) -> LabelValue:
    if value is None:
        return None
    if isinstance(value, bool | str | Decimal):
        return value
    if isinstance(value, int | float) and not isinstance(value, bool):
        return value
    msg = "value must be a scalar label value or None"
    raise LabelSpecError(msg)


def _metadata(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        msg = "path_metadata must be a mapping"
        raise LabelSpecError(msg)
    return dict(value)


def _serialize_value(value: LabelValue) -> bool | float | int | str | None:
    if isinstance(value, Decimal):
        return str(value)
    return value


def _normalize_hash_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return _datetime_to_text(value)
    if isinstance(value, timedelta):
        return int(value.total_seconds())
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, LabelType):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _normalize_hash_value(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_normalize_hash_value(item) for item in value]
    return value
