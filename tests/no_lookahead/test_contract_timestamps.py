from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.core.enums import Direction, ExecutionTiming, LabelType
from alpha_system.core.time import BarAvailabilityPolicy
from alpha_system.data.contracts import OneMinuteBar
from alpha_system.factors.contracts import FactorValue
from alpha_system.labels.contracts import LabelSchema
from alpha_system.signals.contracts import SignalRecord


def test_bar_available_ts_is_distinct_and_latency_bounded() -> None:
    bar_start = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
    bar_end = bar_start + timedelta(minutes=1)
    event_ts = bar_end
    latency = timedelta(seconds=5)
    policy = BarAvailabilityPolicy(data_latency=latency)

    bar = OneMinuteBar(
        instrument_id="inst-1",
        session_id="session-1",
        bar_index=0,
        bar_start_ts=bar_start,
        bar_end_ts=bar_end,
        event_ts=event_ts,
        available_ts=bar_end + latency,
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100.5"),
        volume=Decimal("1000"),
        vwap=Decimal("100.25"),
        trade_count=42,
        bid=Decimal("100.4"),
        ask=Decimal("100.6"),
        spread=Decimal("0.2"),
        source_version="source-v1",
        data_version="data-v1",
        quality_flags=(),
    )

    assert bar.bar_start_ts < bar.bar_end_ts
    assert bar.available_ts not in {
        bar.bar_start_ts,
        bar.bar_end_ts,
        bar.event_ts,
    }
    assert bar.available_ts >= policy.earliest_available_ts(bar.bar_end_ts)


def test_next_bar_conservative_execution_is_default() -> None:
    policy = BarAvailabilityPolicy(data_latency=timedelta(seconds=0))

    assert policy.execution_timing == ExecutionTiming.NEXT_BAR_CONSERVATIVE
    assert policy.same_bar_execution_allowed is False


def test_factor_value_uses_available_ts_distinct_from_event_ts() -> None:
    event_ts = datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc)

    factor_value = FactorValue(
        factor_id="factor-1",
        factor_version="1",
        instrument_id="inst-1",
        event_ts=event_ts,
        available_ts=event_ts + timedelta(seconds=2),
        session_id="session-1",
        bar_index=1,
        value=Decimal("1.2"),
        normalized_value=Decimal("0.8"),
        quality_flags=(),
        data_version="data-v1",
        compute_version="compute-v1",
    )

    assert factor_value.available_ts > factor_value.event_ts


def test_label_available_ts_is_distinct_after_horizon_completion() -> None:
    event_ts = datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc)
    horizon = timedelta(minutes=5)

    label = LabelSchema(
        label_id="label-1",
        instrument_id="inst-1",
        event_ts=event_ts,
        horizon=horizon,
        label_type=LabelType.FORWARD_RETURN_5M,
        value=Decimal("0.01"),
        path_metadata={},
        data_version="label-data-v1",
        label_available_ts=event_ts + horizon + timedelta(seconds=1),
    )

    assert label.label_available_ts != label.event_ts
    assert label.label_available_ts > label.event_ts + label.horizon


def test_signal_record_keeps_event_and_availability_separate() -> None:
    event_ts = datetime(2026, 1, 2, 14, 31, tzinfo=timezone.utc)

    signal = SignalRecord(
        signal_id="signal-1",
        strategy_id="strategy-1",
        instrument_id="inst-1",
        event_ts=event_ts,
        available_ts=event_ts + timedelta(seconds=1),
        session_id="session-1",
        bar_index=1,
        entry_signal=True,
        exit_signal=False,
        direction=Direction.LONG,
        confidence_score=Decimal("0.7"),
        desired_exposure=Decimal("0.1"),
        factor_versions={"factor-1": "1"},
        data_version="data-v1",
        quality_flags=(),
    )

    assert signal.available_ts > signal.event_ts
