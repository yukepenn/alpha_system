from __future__ import annotations

from datetime import UTC, datetime

import pytest

import alpha_system.features.primitives as primitives
from alpha_system.features.contracts import (
    FeatureContractError,
    FeatureFamily,
    FeatureInputSpec,
    FeatureSpec,
    NormalizationSpec,
    TransformSpec,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.primitives import (
    PrimitivePoint,
    PrimitiveSpecError,
    build_live_primitive,
    rolling_mean,
)
from alpha_system.features.primitives.offline import offline_future_mean


def test_rolling_outputs_use_available_ts_not_event_ts() -> None:
    points = (
        _point("2024-01-02T14:40:00+00:00", 1000.0, event_ts="2024-01-02T14:30:00+00:00"),
        _point("2024-01-02T14:31:00+00:00", 1.0),
        _point("2024-01-02T14:32:00+00:00", 2.0),
    )

    result = rolling_mean(points, 2)

    assert result[1].available_ts == _dt("2024-01-02T14:32:00+00:00")
    assert result[1].value == pytest.approx(1.5)
    assert result[1].source_available_ts == (
        _dt("2024-01-02T14:31:00+00:00"),
        _dt("2024-01-02T14:32:00+00:00"),
    )
    assert all(
        source_available_ts <= item.available_ts
        for item in result
        for source_available_ts in item.source_available_ts
    )


def test_late_available_future_value_cannot_change_prior_outputs() -> None:
    base = (
        _point("2024-01-02T14:31:00+00:00", 1.0),
        _point("2024-01-02T14:32:00+00:00", 2.0),
        _point("2024-01-02T14:40:00+00:00", 1000.0, event_ts="2024-01-02T14:30:00+00:00"),
    )
    changed_late_value = (
        _point("2024-01-02T14:31:00+00:00", 1.0),
        _point("2024-01-02T14:32:00+00:00", 2.0),
        _point("2024-01-02T14:40:00+00:00", -1000.0, event_ts="2024-01-02T14:30:00+00:00"),
    )

    base_result = rolling_mean(base, 2)
    changed_result = rolling_mean(changed_late_value, 2)

    assert base_result[1].available_ts == changed_result[1].available_ts
    assert base_result[1].value == changed_result[1].value == pytest.approx(1.5)


def test_future_windows_are_not_reachable_from_live_primitive_or_feature_spec() -> None:
    future = WindowSpec(
        kind=WindowKind.FUTURE,
        length=2,
        causality=WindowCausality.FUTURE,
        offline_only=True,
    )

    with pytest.raises(PrimitiveSpecError, match="live primitives"):
        build_live_primitive(
            TransformSpec(transform_id="rolling_mean"),
            future,
            NormalizationSpec(normalization_id="identity"),
        )

    with pytest.raises(FeatureContractError, match="live FeatureSpec"):
        FeatureSpec(
            feature_id="base_ohlcv_close_return_1m",
            family=FeatureFamily.BASE_OHLCV,
            feature_request_id="freq_111111111111111111111111",
            inputs=FeatureInputSpec(input_views=("canonical_ohlcv",), fields=("close",)),
            transform=TransformSpec(transform_id="rolling_mean"),
            window=future,
            normalization=NormalizationSpec(normalization_id="identity"),
            availability_assumptions={"source": "synthetic available_ts fixture"},
            available_ts_derivation_rule="feature.available_ts = max(input.available_ts)",
            live=True,
        )

    assert not hasattr(primitives, "offline_future_mean")
    offline = offline_future_mean(
        (
            _point("2024-01-02T14:31:00+00:00", 1.0),
            _point("2024-01-02T14:32:00+00:00", 2.0),
            _point("2024-01-02T14:33:00+00:00", 3.0),
        ),
        future,
    )
    assert offline[0].value == pytest.approx(2.5)
    assert any(source_ts > offline[0].available_ts for source_ts in offline[0].source_available_ts)


def _point(
    available_ts: str,
    value: float,
    *,
    event_ts: str | None = None,
) -> PrimitivePoint:
    return PrimitivePoint(
        available_ts=_dt(available_ts),
        event_ts=_dt(event_ts) if event_ts is not None else _dt(available_ts),
        value=value,
        session_label="ETH",
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
