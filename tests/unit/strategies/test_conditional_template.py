from __future__ import annotations

import ast
import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from alpha_system.core.enums import Direction
from alpha_system.signals.spec import SignalType
from alpha_system.strategies.templates import (
    CONTEXT_TRIGGER_CONDITIONAL_TEMPLATE,
    TemplateStrategyError,
    build_context_trigger_conditional_spec,
    evaluate_context_trigger_conditional,
)

SINGLE_FACTOR_TEMPLATE_SOURCE_HASH = (
    "82803fb0b7f48e40fc8e5923b90241cd7d8c39f7953f5e80b893b39bcc344131"
)


def test_single_factor_template_source_is_unchanged() -> None:
    text = Path("src/alpha_system/strategies/templates.py").read_text(encoding="utf-8")
    module = ast.parse(text)
    parts: list[str] = []
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "SINGLE_FACTOR_THRESHOLD_TEMPLATE"
                ):
                    parts.append(ast.get_source_segment(text, node) or "")
        if isinstance(node, ast.FunctionDef) and node.name in {
            "build_single_factor_threshold_spec",
            "evaluate_single_factor_threshold",
            "_require_threshold_template",
        }:
            parts.append(ast.get_source_segment(text, node) or "")

    digest = hashlib.sha256("\n\n".join(parts).encode("utf-8")).hexdigest()

    assert digest == SINGLE_FACTOR_TEMPLATE_SOURCE_HASH


def test_context_trigger_template_compiles_and_evaluates_separate_factors() -> None:
    spec = build_context_trigger_conditional_spec(
        strategy_id="conditional_strategy",
        version="v1",
        owner="research",
        context_factor_id="range_context",
        context_factor_version="ctx:v1",
        context_threshold=0.5,
        trigger_factor_id="sweep_trigger",
        trigger_factor_version="trg:v1",
        trigger_threshold=0.0,
        direction=Direction.LONG,
        desired_exposure=0.25,
    )

    signal = evaluate_context_trigger_conditional(
        spec,
        {
            "range_context": _factor_value("range_context", "ctx:v1", 0.8),
            "sweep_trigger": _factor_value("sweep_trigger", "trg:v1", 1.2),
        },
    )

    assert spec.parameters["template"] == CONTEXT_TRIGGER_CONDITIONAL_TEMPLATE
    assert spec.required_factor_ids == ("range_context", "sweep_trigger")
    assert signal.signal_type is SignalType.ENTRY
    assert signal.direction is Direction.LONG
    assert signal.desired_exposure == 0.25
    assert signal.factor_versions == {
        "range_context": "ctx:v1",
        "sweep_trigger": "trg:v1",
    }


def test_context_trigger_template_holds_when_context_fails() -> None:
    spec = build_context_trigger_conditional_spec(
        strategy_id="conditional_strategy",
        version="v1",
        owner="research",
        context_factor_id="range_context",
        context_factor_version="ctx:v1",
        context_threshold=0.5,
        trigger_factor_id="sweep_trigger",
        trigger_factor_version="trg:v1",
        trigger_threshold=0.0,
    )

    signal = evaluate_context_trigger_conditional(
        spec,
        {
            "range_context": _factor_value("range_context", "ctx:v1", 0.2),
            "sweep_trigger": _factor_value("sweep_trigger", "trg:v1", 1.2),
        },
    )

    assert signal.signal_type is SignalType.HOLD
    assert signal.direction is Direction.FLAT
    assert signal.desired_exposure == 0.0


def test_context_trigger_template_rejects_context_equal_trigger() -> None:
    with pytest.raises(TemplateStrategyError, match="separate"):
        build_context_trigger_conditional_spec(
            strategy_id="bad_conditional_strategy",
            version="v1",
            owner="research",
            context_factor_id="same_factor",
            context_factor_version="v1",
            context_threshold=0.0,
            trigger_factor_id="same_factor",
            trigger_factor_version="v1",
            trigger_threshold=0.0,
        )


def _factor_value(factor_id: str, factor_version: str, value: float) -> dict[str, object]:
    event_ts = datetime(2026, 1, 2, 14, 31, tzinfo=UTC)
    return {
        "factor_id": factor_id,
        "factor_version": factor_version,
        "instrument_id": "SYNTH",
        "event_ts": event_ts.isoformat().replace("+00:00", "Z"),
        "available_ts": (event_ts + timedelta(seconds=5)).isoformat().replace(
            "+00:00",
            "Z",
        ),
        "session_id": "XNYS:2026-01-02:regular",
        "bar_index": 1,
        "value": value,
        "normalized_value": value,
        "quality_flags": ["synthetic"],
        "data_version": "data:v1",
        "compute_version": "test",
    }
