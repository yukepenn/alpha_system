from __future__ import annotations

from dataclasses import fields

import pytest

from alpha_system.strategies.spec import (
    FORBIDDEN_STRATEGY_RESPONSIBILITIES,
    StrategySpec,
    StrategySpecError,
)
from alpha_system.strategies.validation import (
    StrategyValidationError,
    validate_strategy_boundaries,
)


def test_strategy_spec_cannot_carry_forbidden_responsibility_fields() -> None:
    field_names = {field.name for field in fields(StrategySpec)}

    assert field_names.isdisjoint(FORBIDDEN_STRATEGY_RESPONSIBILITIES)


def test_strategy_spec_rejects_accounting_execution_and_portfolio_payloads() -> None:
    payload = _strategy_payload()
    payload["account_equity"] = 100_000
    with pytest.raises(StrategySpecError, match="forbidden"):
        StrategySpec.from_mapping(payload)

    payload = _strategy_payload()
    payload["parameters"] = {"commission": 0.001}
    with pytest.raises(StrategySpecError, match="forbidden"):
        StrategySpec.from_mapping(payload)

    payload = _strategy_payload()
    payload["metadata"] = {"portfolio_aggregation": "weighted"}
    with pytest.raises(StrategyValidationError, match="forbidden"):
        validate_strategy_boundaries(payload)


def _strategy_payload() -> dict[str, object]:
    return {
        "strategy_id": "threshold_strategy",
        "name": "Threshold strategy",
        "version": "v1",
        "owner": "research",
        "description": "Fixture-only signal intent strategy.",
        "entry_signal": "fixture_close_delta.normalized_value >= 0.5",
        "exit_signal": "fixture_close_delta.normalized_value <= -0.1",
        "direction": "long",
        "required_factor_dependencies": [
            {
                "factor_id": "fixture_close_delta",
                "factor_version": "v1",
                "input_name": "primary_factor",
            }
        ],
        "parameters": {"template": "single_factor_threshold"},
        "metadata": {"purpose": "deterministic synthetic fixture"},
        "confidence_score": 0.6,
        "desired_exposure": 0.25,
    }
