"""Strategy dependency, boundary, and leakage validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import Any

from alpha_system.factors.base import FACTOR_VALUE_SCHEMA_FIELDS
from alpha_system.factors.dependency_spec import looks_like_label_field
from alpha_system.strategies.spec import (
    FORBIDDEN_STRATEGY_RESPONSIBILITIES,
    StrategySpec,
    StrategySpecError,
)


class StrategyValidationError(ValueError):
    """Raised when strategy inputs or boundaries are invalid."""


ALLOWED_FACTOR_VALUE_FIELDS: frozenset[str] = frozenset(FACTOR_VALUE_SCHEMA_FIELDS)
REQUIRED_FACTOR_VALUE_FIELDS: frozenset[str] = frozenset(
    (
        "factor_id",
        "factor_version",
        "instrument_id",
        "event_ts",
        "available_ts",
        "session_id",
        "bar_index",
        "value",
        "normalized_value",
        "quality_flags",
        "data_version",
        "compute_version",
    )
)


def validate_strategy_boundaries(spec_or_payload: StrategySpec | Mapping[str, Any]) -> None:
    """Reject management, portfolio, execution, and accounting responsibilities."""
    if isinstance(spec_or_payload, StrategySpec):
        field_names = set(_dataclass_field_names(spec_or_payload))
        forbidden_fields = field_names.intersection(FORBIDDEN_STRATEGY_RESPONSIBILITIES)
        if forbidden_fields:
            msg = (
                "StrategySpec contains forbidden responsibilities: "
                f"{', '.join(sorted(forbidden_fields))}"
            )
            raise StrategyValidationError(msg)
        _reject_forbidden_mapping(dict(spec_or_payload.parameters), "parameters")
        _reject_forbidden_mapping(dict(spec_or_payload.metadata), "metadata")
        return

    if not isinstance(spec_or_payload, Mapping):
        msg = "strategy boundary validation expects a StrategySpec or mapping"
        raise StrategyValidationError(msg)
    try:
        StrategySpec.from_mapping(spec_or_payload)
    except StrategySpecError as exc:
        raise StrategyValidationError(str(exc)) from exc


def validate_strategy_inputs(
    spec: StrategySpec,
    inputs: Mapping[str, Mapping[str, Any] | Any],
) -> Mapping[str, Mapping[str, Any]]:
    """Validate that a strategy reads only declared factor value records."""
    validate_strategy_boundaries(spec)
    if not isinstance(inputs, Mapping):
        msg = "strategy inputs must be a mapping keyed by factor_id"
        raise StrategyValidationError(msg)

    declared = dict(spec.factor_versions)
    normalized: dict[str, Mapping[str, Any]] = {}
    for key, value in inputs.items():
        factor_key = _required_string(key, "strategy input key")
        _reject_label_like(factor_key, "strategy input")
        if factor_key not in declared:
            msg = f"undeclared strategy inputs are not allowed: {factor_key}"
            raise StrategyValidationError(msg)
        factor_record = _factor_mapping(value)
        _validate_factor_record_keys(factor_record)
        factor_id = _required_string(factor_record.get("factor_id"), "factor_id")
        factor_version = _required_string(
            factor_record.get("factor_version"),
            "factor_version",
        )
        if factor_id != factor_key:
            msg = f"strategy input key {factor_key!r} does not match factor_id {factor_id!r}"
            raise StrategyValidationError(msg)
        if declared[factor_id] != factor_version:
            msg = (
                "strategy factor version mismatch: "
                f"{factor_id} expected {declared[factor_id]}, got {factor_version}"
            )
            raise StrategyValidationError(msg)
        normalized[factor_id] = factor_record

    missing = tuple(sorted(set(declared).difference(normalized)))
    if missing:
        msg = f"strategy missing declared factor inputs: {', '.join(missing)}"
        raise StrategyValidationError(msg)
    return normalized


def reject_labels_as_strategy_inputs(inputs: Mapping[str, Any]) -> None:
    """Raise when strategy inputs expose label-like names or fields."""
    for key, value in inputs.items():
        _reject_label_like(str(key), "strategy input")
        if isinstance(value, Mapping):
            for field_name in value:
                _reject_label_like(str(field_name), "strategy input field")


def _validate_factor_record_keys(record: Mapping[str, Any]) -> None:
    for field_name in record:
        _reject_label_like(str(field_name), "strategy input field")
    missing = tuple(sorted(REQUIRED_FACTOR_VALUE_FIELDS.difference(record)))
    if missing:
        msg = f"factor value input missing required fields: {', '.join(missing)}"
        raise StrategyValidationError(msg)
    extra = tuple(sorted(set(record).difference(ALLOWED_FACTOR_VALUE_FIELDS)))
    if extra:
        msg = f"raw ad hoc columns are not allowed as strategy inputs: {', '.join(extra)}"
        raise StrategyValidationError(msg)


def _factor_mapping(value: Mapping[str, Any] | Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return payload
    msg = "strategy inputs must be factor-value mappings"
    raise StrategyValidationError(msg)


def _reject_label_like(value: str, context: str) -> None:
    if looks_like_label_field(value):
        msg = f"labels are not allowed as live strategy inputs: {context} {value!r}"
        raise StrategyValidationError(msg)


def _reject_forbidden_mapping(payload: Mapping[str, Any], context: str) -> None:
    for key, value in payload.items():
        normalized = _normalize_key(key)
        if normalized in FORBIDDEN_STRATEGY_RESPONSIBILITIES:
            msg = f"{context} contains forbidden StrategySpec responsibility {key!r}"
            raise StrategyValidationError(msg)
        if isinstance(value, Mapping):
            _reject_forbidden_mapping(value, f"{context}.{key}")


def _dataclass_field_names(value: Any) -> tuple[str, ...]:
    if not is_dataclass(value):
        return ()
    return tuple(field.name for field in fields(value))


def _required_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise StrategyValidationError(msg)
    return value.strip()


def _normalize_key(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")
