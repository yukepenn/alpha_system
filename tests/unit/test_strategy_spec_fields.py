from __future__ import annotations

from dataclasses import fields

from alpha_system.core.enums import Direction
from alpha_system.strategies.spec import (
    ALLOWED_STRATEGY_OUTPUT_FIELDS,
    StrategyFactorDependency,
    StrategySpec,
)
from alpha_system.strategies.validation import validate_strategy_boundaries


def test_strategy_spec_exposes_allowed_outputs_and_factor_dependencies() -> None:
    spec = _strategy_spec()

    field_names = {field.name for field in fields(StrategySpec)}
    assert set(ALLOWED_STRATEGY_OUTPUT_FIELDS).issubset(field_names)
    assert spec.entry_signal == "fixture_close_delta.normalized_value >= 0.5"
    assert spec.exit_signal == "fixture_close_delta.normalized_value <= -0.1"
    assert spec.direction is Direction.LONG
    assert spec.confidence_score == 0.6
    assert spec.desired_exposure == 0.25
    assert spec.required_factor_ids == ("fixture_close_delta",)
    assert spec.factor_versions == {"fixture_close_delta": "v1"}
    validate_strategy_boundaries(spec)


def _strategy_spec() -> StrategySpec:
    return StrategySpec(
        strategy_id="threshold_strategy",
        name="Threshold strategy",
        version="v1",
        owner="research",
        description="Fixture-only signal intent strategy.",
        entry_signal="fixture_close_delta.normalized_value >= 0.5",
        exit_signal="fixture_close_delta.normalized_value <= -0.1",
        direction=Direction.LONG,
        required_factor_dependencies=(
            StrategyFactorDependency(
                factor_id="fixture_close_delta",
                factor_version="v1",
                input_name="primary_factor",
            ),
        ),
        parameters={"template": "single_factor_threshold"},
        metadata={"purpose": "deterministic synthetic fixture"},
        confidence_score=0.6,
        desired_exposure=0.25,
    )
