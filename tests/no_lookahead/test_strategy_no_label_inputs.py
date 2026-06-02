from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from alpha_system.core.enums import Direction
from alpha_system.strategies.spec import (
    StrategyFactorDependency,
    StrategySpec,
    StrategySpecError,
)
from alpha_system.strategies.validation import (
    StrategyValidationError,
    reject_labels_as_strategy_inputs,
    validate_strategy_inputs,
)


def test_labels_rejected_as_live_strategy_dependencies_and_inputs() -> None:
    with pytest.raises(StrategySpecError, match="label"):
        StrategyFactorDependency(
            factor_id="forward_return_1m",
            factor_version="labels:v1",
            input_name="forward_return_1m",
        )

    spec = _strategy_spec()

    with pytest.raises(StrategyValidationError, match="labels are not allowed"):
        validate_strategy_inputs(
            spec,
            {
                "fixture_close_delta": _factor_value_with_label_field(),
            },
        )

    with pytest.raises(StrategyValidationError, match="labels are not allowed"):
        reject_labels_as_strategy_inputs({"label_forward_return_1m": 0.01})


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


def _factor_value_with_label_field() -> dict[str, object]:
    event_ts = datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc)
    return {
        "factor_id": "fixture_close_delta",
        "factor_version": "v1",
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
        "label_forward_return_1m": 0.01,
    }
