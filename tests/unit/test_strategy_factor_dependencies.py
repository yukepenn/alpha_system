from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from alpha_system.core.enums import Direction
from alpha_system.strategies.spec import StrategyFactorDependency, StrategySpec
from alpha_system.strategies.validation import (
    StrategyValidationError,
    validate_strategy_inputs,
)


def test_strategy_reads_only_declared_factor_dependencies() -> None:
    spec = _strategy_spec()
    factor = _factor_value("fixture_close_delta", "v1")

    normalized = validate_strategy_inputs(spec, {"fixture_close_delta": factor})

    assert normalized["fixture_close_delta"]["factor_version"] == "v1"


def test_strategy_rejects_missing_undeclared_and_wrong_version_inputs() -> None:
    spec = _strategy_spec()

    with pytest.raises(StrategyValidationError, match="missing declared"):
        validate_strategy_inputs(spec, {})

    with pytest.raises(StrategyValidationError, match="undeclared"):
        validate_strategy_inputs(
            spec,
            {
                "fixture_close_delta": _factor_value("fixture_close_delta", "v1"),
                "raw_close": _factor_value("raw_close", "v1"),
            },
        )

    with pytest.raises(StrategyValidationError, match="version mismatch"):
        validate_strategy_inputs(
            spec,
            {"fixture_close_delta": _factor_value("fixture_close_delta", "v2")},
        )


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
    )


def _factor_value(factor_id: str, factor_version: str) -> dict[str, object]:
    event_ts = datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc)
    return {
        "factor_id": factor_id,
        "factor_version": factor_version,
        "instrument_id": "SYNTH",
        "event_ts": event_ts.isoformat().replace("+00:00", "Z"),
        "available_ts": (event_ts + timedelta(seconds=5)).isoformat().replace("+00:00", "Z"),
        "session_id": "XNYS:2026-01-02:regular",
        "bar_index": 1,
        "value": 0.8,
        "normalized_value": 0.8,
        "quality_flags": ["synthetic"],
        "data_version": "data:v1",
        "compute_version": "test",
    }
