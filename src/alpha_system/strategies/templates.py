"""Deterministic template strategies over declared factor dependencies."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from alpha_system.core.enums import Direction
from alpha_system.core.hashing import hash_config
from alpha_system.signals.spec import SignalRecord, SignalType
from alpha_system.signals.validation import validate_signal_available_ts
from alpha_system.strategies.spec import (
    StrategyFactorDependency,
    StrategySpec,
)
from alpha_system.strategies.validation import validate_strategy_inputs


class TemplateStrategyError(ValueError):
    """Raised when a template strategy cannot produce a deterministic signal."""


SINGLE_FACTOR_THRESHOLD_TEMPLATE = "single_factor_threshold"


def build_single_factor_threshold_spec(
    *,
    strategy_id: str,
    version: str,
    owner: str,
    factor_id: str,
    factor_version: str,
    entry_threshold: float,
    exit_threshold: float,
    direction: Direction = Direction.LONG,
    confidence_score: float | None = None,
    desired_exposure: float | None = None,
) -> StrategySpec:
    """Build the scoped deterministic threshold StrategySpec template."""
    return StrategySpec(
        strategy_id=strategy_id,
        name="Single factor threshold template",
        version=version,
        owner=owner,
        description=(
            "Deterministic research template that converts one declared factor "
            "value into entry, exit, or hold signal intent."
        ),
        entry_signal=f"{factor_id}.normalized_value >= {entry_threshold}",
        exit_signal=f"{factor_id}.normalized_value <= {exit_threshold}",
        direction=direction,
        required_factor_dependencies=(
            StrategyFactorDependency(
                factor_id=factor_id,
                factor_version=factor_version,
                input_name="primary_factor",
            ),
        ),
        parameters={
            "template": SINGLE_FACTOR_THRESHOLD_TEMPLATE,
            "source_factor_id": factor_id,
            "value_field": "normalized_value",
            "entry_threshold": entry_threshold,
            "exit_threshold": exit_threshold,
        },
        metadata={"template_scope": "research_signal_intent_only"},
        confidence_score=confidence_score,
        desired_exposure=desired_exposure,
    )


def evaluate_single_factor_threshold(
    spec: StrategySpec,
    factor_values: Mapping[str, Mapping[str, Any] | Any],
    *,
    signal_id: str | None = None,
) -> SignalRecord:
    """Evaluate one StrategySpec on declared factor values and return signal intent."""
    _require_threshold_template(spec)
    normalized_inputs = validate_strategy_inputs(spec, factor_values)
    source_factor_id = str(
        spec.parameters.get("source_factor_id") or spec.required_factor_ids[0]
    )
    if source_factor_id not in normalized_inputs:
        msg = f"source_factor_id {source_factor_id!r} is not a declared factor input"
        raise TemplateStrategyError(msg)
    factor = normalized_inputs[source_factor_id]
    value_field = str(spec.parameters.get("value_field", "normalized_value"))
    if value_field not in {"value", "normalized_value"}:
        msg = "template value_field must be value or normalized_value"
        raise TemplateStrategyError(msg)

    metric = factor.get(value_field)
    if metric is None and value_field == "normalized_value":
        metric = factor.get("value")
    numeric_metric = _numeric(metric, value_field)
    entry_threshold = _numeric(spec.parameters.get("entry_threshold"), "entry_threshold")
    exit_threshold = _numeric(spec.parameters.get("exit_threshold"), "exit_threshold")

    if numeric_metric >= entry_threshold:
        signal_type = SignalType.ENTRY
        direction = spec.direction
        confidence = spec.confidence_score
        desired_exposure = spec.desired_exposure
    elif numeric_metric <= exit_threshold:
        signal_type = SignalType.EXIT
        direction = Direction.FLAT
        confidence = spec.confidence_score
        desired_exposure = 0.0
    else:
        signal_type = SignalType.HOLD
        direction = Direction.FLAT
        confidence = spec.confidence_score
        desired_exposure = 0.0

    record = SignalRecord.from_mapping(
        {
            "signal_id": signal_id or _signal_id(spec, factor, signal_type),
            "instrument_id": factor["instrument_id"],
            "event_ts": factor["event_ts"],
            "available_ts": factor["available_ts"],
            "session_id": factor["session_id"],
            "bar_index": factor["bar_index"],
            "signal_type": signal_type.value,
            "direction": direction.value,
            "score": numeric_metric,
            "confidence": confidence,
            "desired_exposure": desired_exposure,
            "strategy_id": spec.strategy_id,
            "strategy_version": spec.version,
            "factor_versions": spec.factor_versions,
            "quality_flags": factor["quality_flags"],
            "data_version": factor["data_version"],
        }
    )
    return validate_signal_available_ts(record, normalized_inputs.values())


def _require_threshold_template(spec: StrategySpec) -> None:
    template = str(spec.parameters.get("template", ""))
    if template != SINGLE_FACTOR_THRESHOLD_TEMPLATE:
        msg = (
            "unsupported strategy template: "
            f"{template!r}; expected {SINGLE_FACTOR_THRESHOLD_TEMPLATE!r}"
        )
        raise TemplateStrategyError(msg)
    if len(spec.required_factor_dependencies) != 1:
        msg = "single-factor threshold template requires exactly one factor dependency"
        raise TemplateStrategyError(msg)


def _numeric(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or value is None:
        msg = f"{field_name} must be numeric"
        raise TemplateStrategyError(msg)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    msg = f"{field_name} must be numeric"
    raise TemplateStrategyError(msg)


def _signal_id(
    spec: StrategySpec,
    factor: Mapping[str, Any],
    signal_type: SignalType,
) -> str:
    digest = hash_config(
        {
            "bar_index": factor["bar_index"],
            "event_ts": str(factor["event_ts"]),
            "factor_id": factor["factor_id"],
            "factor_version": factor["factor_version"],
            "instrument_id": factor["instrument_id"],
            "signal_type": signal_type.value,
            "strategy_id": spec.strategy_id,
            "strategy_version": spec.version,
        }
    )
    return f"signal:{spec.strategy_id}:{spec.version}:{digest[:16]}"
