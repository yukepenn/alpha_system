from __future__ import annotations

from datetime import datetime, timedelta, timezone

from alpha_system.core.enums import Direction
from alpha_system.signals.spec import SignalType
from alpha_system.strategies.templates import (
    build_single_factor_threshold_spec,
    evaluate_single_factor_threshold,
)


def test_template_strategy_output_is_deterministic_on_tiny_fixture() -> None:
    spec = build_single_factor_threshold_spec(
        strategy_id="threshold_strategy",
        version="v1",
        owner="research",
        factor_id="fixture_close_delta",
        factor_version="v1",
        entry_threshold=0.5,
        exit_threshold=-0.1,
        direction=Direction.LONG,
        confidence_score=0.6,
        desired_exposure=0.25,
    )
    factor_inputs = {"fixture_close_delta": _factor_value()}

    first = evaluate_single_factor_threshold(spec, factor_inputs)
    second = evaluate_single_factor_threshold(spec, factor_inputs)

    assert first.to_dict() == second.to_dict()
    assert first.signal_type is SignalType.ENTRY
    assert first.direction is Direction.LONG
    assert first.factor_versions == {"fixture_close_delta": "v1"}
    assert first.desired_exposure == 0.25


def _factor_value() -> dict[str, object]:
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
    }
