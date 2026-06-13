"""Deterministic template strategies over declared factor dependencies."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
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


CONTEXT_TRIGGER_CONDITIONAL_TEMPLATE = "context_trigger_conditional"
PREDICATE_OPERATORS = frozenset({">", ">=", "<", "<=", "==", "!="})


def build_context_trigger_conditional_spec(
    *,
    strategy_id: str,
    version: str,
    owner: str,
    context_factor_id: str,
    context_factor_version: str,
    context_threshold: float,
    trigger_factor_id: str,
    trigger_factor_version: str,
    trigger_threshold: float,
    context_operator: str = ">=",
    trigger_operator: str = ">=",
    context_value_field: str = "normalized_value",
    trigger_value_field: str = "normalized_value",
    direction: Direction = Direction.LONG,
    confidence_score: float | None = None,
    desired_exposure: float | None = None,
) -> StrategySpec:
    """Build the additive context-factor plus trigger-factor template."""

    _require_separate_factors(context_factor_id, trigger_factor_id)
    active_context_operator = _predicate_operator(context_operator, "context_operator")
    active_trigger_operator = _predicate_operator(trigger_operator, "trigger_operator")
    active_context_value_field = _value_field(context_value_field, "context_value_field")
    active_trigger_value_field = _value_field(trigger_value_field, "trigger_value_field")
    active_context_threshold = _numeric(context_threshold, "context_threshold")
    active_trigger_threshold = _numeric(trigger_threshold, "trigger_threshold")
    context_expression = _predicate_expression(
        context_factor_id,
        active_context_value_field,
        active_context_operator,
        active_context_threshold,
    )
    trigger_expression = _predicate_expression(
        trigger_factor_id,
        active_trigger_value_field,
        active_trigger_operator,
        active_trigger_threshold,
    )
    return StrategySpec(
        strategy_id=strategy_id,
        name="Context trigger conditional template",
        version=version,
        owner=owner,
        description=(
            "Deterministic research template that emits entry intent only when "
            "a context-factor predicate and a separate trigger-factor predicate "
            "are both satisfied at the same decision point."
        ),
        entry_signal=f"{context_expression} AND {trigger_expression}",
        exit_signal=f"NOT ({context_expression} AND {trigger_expression})",
        direction=direction,
        required_factor_dependencies=(
            StrategyFactorDependency(
                factor_id=context_factor_id,
                factor_version=context_factor_version,
                input_name="entry_context_factor",
            ),
            StrategyFactorDependency(
                factor_id=trigger_factor_id,
                factor_version=trigger_factor_version,
                input_name="event_trigger_factor",
            ),
        ),
        parameters={
            "template": CONTEXT_TRIGGER_CONDITIONAL_TEMPLATE,
            "context_factor_id": context_factor_id,
            "context_value_field": active_context_value_field,
            "context_operator": active_context_operator,
            "context_threshold": active_context_threshold,
            "trigger_factor_id": trigger_factor_id,
            "trigger_value_field": active_trigger_value_field,
            "trigger_operator": active_trigger_operator,
            "trigger_threshold": active_trigger_threshold,
        },
        metadata={
            "template_scope": "research_signal_intent_only",
            "context_trigger_separate": True,
        },
        confidence_score=confidence_score,
        desired_exposure=desired_exposure,
    )


def evaluate_context_trigger_conditional(
    spec: StrategySpec,
    factor_values: Mapping[str, Mapping[str, Any] | Any],
    *,
    signal_id: str | None = None,
) -> SignalRecord:
    """Evaluate separate context and trigger predicates into signal intent."""

    _require_context_trigger_template(spec)
    normalized_inputs = validate_strategy_inputs(spec, factor_values)
    context_factor_id = str(spec.parameters["context_factor_id"])
    trigger_factor_id = str(spec.parameters["trigger_factor_id"])
    _require_separate_factors(context_factor_id, trigger_factor_id)
    if context_factor_id not in normalized_inputs:
        msg = f"context_factor_id {context_factor_id!r} is not a declared factor input"
        raise TemplateStrategyError(msg)
    if trigger_factor_id not in normalized_inputs:
        msg = f"trigger_factor_id {trigger_factor_id!r} is not a declared factor input"
        raise TemplateStrategyError(msg)

    context_factor = normalized_inputs[context_factor_id]
    trigger_factor = normalized_inputs[trigger_factor_id]
    _require_same_decision_point(context_factor, trigger_factor)
    context_metric = _predicate_metric(
        context_factor,
        str(spec.parameters["context_value_field"]),
        "context_value_field",
    )
    trigger_metric = _predicate_metric(
        trigger_factor,
        str(spec.parameters["trigger_value_field"]),
        "trigger_value_field",
    )
    context_passed = _compare(
        context_metric,
        str(spec.parameters["context_operator"]),
        _numeric(spec.parameters["context_threshold"], "context_threshold"),
    )
    trigger_passed = _compare(
        trigger_metric,
        str(spec.parameters["trigger_operator"]),
        _numeric(spec.parameters["trigger_threshold"], "trigger_threshold"),
    )

    if context_passed and trigger_passed:
        signal_type = SignalType.ENTRY
        direction = spec.direction
        desired_exposure = spec.desired_exposure
    else:
        signal_type = SignalType.HOLD
        direction = Direction.FLAT
        desired_exposure = 0.0

    record = SignalRecord.from_mapping(
        {
            "signal_id": signal_id
            or _conditional_signal_id(
                spec,
                context_factor,
                trigger_factor,
                signal_type,
            ),
            "instrument_id": trigger_factor["instrument_id"],
            "event_ts": trigger_factor["event_ts"],
            "available_ts": _latest_available_ts(context_factor, trigger_factor),
            "session_id": trigger_factor["session_id"],
            "bar_index": trigger_factor["bar_index"],
            "signal_type": signal_type.value,
            "direction": direction.value,
            "score": trigger_metric,
            "confidence": spec.confidence_score,
            "desired_exposure": desired_exposure,
            "strategy_id": spec.strategy_id,
            "strategy_version": spec.version,
            "factor_versions": spec.factor_versions,
            "quality_flags": _merged_quality_flags(context_factor, trigger_factor),
            "data_version": trigger_factor["data_version"],
        }
    )
    return validate_signal_available_ts(record, normalized_inputs.values())


def _require_context_trigger_template(spec: StrategySpec) -> None:
    template = str(spec.parameters.get("template", ""))
    if template != CONTEXT_TRIGGER_CONDITIONAL_TEMPLATE:
        msg = (
            "unsupported strategy template: "
            f"{template!r}; expected {CONTEXT_TRIGGER_CONDITIONAL_TEMPLATE!r}"
        )
        raise TemplateStrategyError(msg)
    if len(spec.required_factor_dependencies) != 2:
        msg = "context-trigger conditional template requires exactly two factor dependencies"
        raise TemplateStrategyError(msg)


def _require_separate_factors(context_factor_id: str, trigger_factor_id: str) -> None:
    if not str(context_factor_id).strip() or not str(trigger_factor_id).strip():
        msg = "context and trigger factor IDs must be non-empty"
        raise TemplateStrategyError(msg)
    if context_factor_id == trigger_factor_id:
        msg = "context and trigger factors must be separate"
        raise TemplateStrategyError(msg)


def _value_field(value: str, field_name: str) -> str:
    if value not in {"value", "normalized_value"}:
        msg = f"{field_name} must be value or normalized_value"
        raise TemplateStrategyError(msg)
    return value


def _predicate_operator(value: str, field_name: str) -> str:
    if value not in PREDICATE_OPERATORS:
        msg = f"{field_name} must be one of: {', '.join(sorted(PREDICATE_OPERATORS))}"
        raise TemplateStrategyError(msg)
    return value


def _predicate_expression(
    factor_id: str,
    value_field: str,
    operator: str,
    threshold: float,
) -> str:
    return f"{factor_id}.{value_field} {operator} {threshold}"


def _predicate_metric(
    factor: Mapping[str, Any],
    value_field: str,
    field_name: str,
) -> float:
    active_field = _value_field(value_field, field_name)
    metric = factor.get(active_field)
    if metric is None and active_field == "normalized_value":
        metric = factor.get("value")
    return _numeric(metric, field_name)


def _compare(left: float, operator: str, right: float) -> bool:
    active_operator = _predicate_operator(operator, "operator")
    if active_operator == ">":
        return left > right
    if active_operator == ">=":
        return left >= right
    if active_operator == "<":
        return left < right
    if active_operator == "<=":
        return left <= right
    if active_operator == "==":
        return left == right
    if active_operator == "!=":
        return left != right
    msg = f"unsupported predicate operator: {operator}"
    raise TemplateStrategyError(msg)


def _require_same_decision_point(
    context_factor: Mapping[str, Any],
    trigger_factor: Mapping[str, Any],
) -> None:
    fields = ("instrument_id", "event_ts", "session_id", "bar_index", "data_version")
    mismatched = [
        field
        for field in fields
        if str(context_factor.get(field)) != str(trigger_factor.get(field))
    ]
    if mismatched:
        msg = "context and trigger factor rows must share decision point fields: "
        raise TemplateStrategyError(msg + ", ".join(mismatched))


def _latest_available_ts(
    context_factor: Mapping[str, Any],
    trigger_factor: Mapping[str, Any],
) -> datetime:
    return max(
        _datetime_value(context_factor["available_ts"], "context.available_ts"),
        _datetime_value(trigger_factor["available_ts"], "trigger.available_ts"),
    )


def _datetime_value(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        active = value
    elif isinstance(value, str):
        try:
            active = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be ISO-8601 datetime text"
            raise TemplateStrategyError(msg) from exc
    else:
        msg = f"{field_name} must be datetime or ISO-8601 text"
        raise TemplateStrategyError(msg)
    if active.tzinfo is None:
        active = active.replace(tzinfo=UTC)
    return active.astimezone(UTC)


def _merged_quality_flags(
    context_factor: Mapping[str, Any],
    trigger_factor: Mapping[str, Any],
) -> list[str]:
    flags: list[str] = []
    for factor in (context_factor, trigger_factor):
        values = factor.get("quality_flags", ())
        if isinstance(values, str):
            values = (values,)
        for value in values:
            text = str(value)
            if text not in flags:
                flags.append(text)
    return flags


def _conditional_signal_id(
    spec: StrategySpec,
    context_factor: Mapping[str, Any],
    trigger_factor: Mapping[str, Any],
    signal_type: SignalType,
) -> str:
    digest = hash_config(
        {
            "bar_index": trigger_factor["bar_index"],
            "context_factor_id": context_factor["factor_id"],
            "context_factor_version": context_factor["factor_version"],
            "event_ts": str(trigger_factor["event_ts"]),
            "instrument_id": trigger_factor["instrument_id"],
            "signal_type": signal_type.value,
            "strategy_id": spec.strategy_id,
            "strategy_version": spec.version,
            "trigger_factor_id": trigger_factor["factor_id"],
            "trigger_factor_version": trigger_factor["factor_version"],
        }
    )
    return f"signal:{spec.strategy_id}:{spec.version}:{digest[:16]}"
