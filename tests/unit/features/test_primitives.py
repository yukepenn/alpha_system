from __future__ import annotations

import math
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from alpha_system.features.contracts import (
    NormalizationSpec,
    TransformSpec,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.input_views import BBOInputRow, OHLCVInputRow
from alpha_system.features.primitives import (
    OHLCVPrimitiveBar,
    PrimitivePoint,
    PrimitiveSpecError,
    apply_live_primitive,
    average_true_range,
    bars_from_trade_rows,
    build_live_primitive,
    causal_minmax_scale,
    causal_zscore,
    log_returns,
    points_from_bbo_rows,
    points_from_trade_rows,
    rolling_mean,
    rolling_range,
    rolling_std,
    session_reset_groups,
    simple_returns,
    true_range,
)
from alpha_system.features.primitives.offline import offline_centered_mean


def test_causal_rolling_windows_order_by_available_ts() -> None:
    points = (
        _point("2024-01-02T14:40:00+00:00", 100.0, event_ts="2024-01-02T14:30:00+00:00"),
        _point("2024-01-02T14:31:00+00:00", 1.0),
        _point("2024-01-02T14:32:00+00:00", 3.0),
        _point("2024-01-02T14:33:00+00:00", 5.0),
    )

    result = rolling_mean(points, 2)

    assert [item.available_ts for item in result] == [
        _dt("2024-01-02T14:31:00+00:00"),
        _dt("2024-01-02T14:32:00+00:00"),
        _dt("2024-01-02T14:33:00+00:00"),
        _dt("2024-01-02T14:40:00+00:00"),
    ]
    assert result[0].value is None
    assert result[1].value == pytest.approx(2.0)
    assert result[2].value == pytest.approx(4.0)
    assert result[3].value == pytest.approx(52.5)
    for item in result:
        assert all(source_ts <= item.available_ts for source_ts in item.source_available_ts)


def test_return_and_log_return_primitives_are_trailing_only() -> None:
    points = (
        _point("2024-01-02T14:31:00+00:00", 100.0),
        _point("2024-01-02T14:32:00+00:00", 110.0),
        _point("2024-01-02T14:33:00+00:00", 121.0),
    )

    simple = simple_returns(points, 1)
    logged = log_returns(points, 1)

    assert simple[0].value is None
    assert simple[1].value == pytest.approx(0.10)
    assert simple[2].value == pytest.approx(0.10)
    assert logged[1].value == pytest.approx(math.log(1.1))
    assert logged[2].value == pytest.approx(math.log(1.1))


def test_range_std_and_normalization_primitives_are_causal() -> None:
    points = (
        _point("2024-01-02T14:31:00+00:00", 1.0),
        _point("2024-01-02T14:32:00+00:00", 2.0),
        _point("2024-01-02T14:33:00+00:00", 3.0),
    )

    ranges = rolling_range(points, 3)
    std = rolling_std(points, 3)
    zscore = causal_zscore(points, 3)
    minmax = causal_minmax_scale(points, 3)

    assert ranges[2].value == pytest.approx(2.0)
    assert std[2].value == pytest.approx(math.sqrt(2.0 / 3.0))
    assert zscore[2].value == pytest.approx((3.0 - 2.0) / math.sqrt(2.0 / 3.0))
    assert minmax[2].value == pytest.approx(1.0)


def test_session_reset_helpers_prevent_cross_session_windows() -> None:
    points = (
        _point("2024-01-02T14:31:00+00:00", 1.0, session_label="ETH"),
        _point("2024-01-02T14:32:00+00:00", 2.0, session_label="ETH"),
        _point("2024-01-02T14:33:00+00:00", 100.0, session_label="RTH"),
    )

    no_reset = rolling_mean(points, 2)
    reset = rolling_mean(points, 2, reset_on_session=True)
    groups = session_reset_groups(points)

    assert no_reset[2].value == pytest.approx(51.0)
    assert reset[2].value is None
    assert "insufficient_window" in reset[2].quality_flags
    assert [[point.value for point in group] for group in groups] == [[1.0, 2.0], [100.0]]


def test_true_range_and_atr_are_causal_and_session_aware() -> None:
    bars = (
        OHLCVPrimitiveBar(
            available_ts=_dt("2024-01-02T14:31:00+00:00"),
            high=110,
            low=100,
            close=105,
            session_label="ETH",
        ),
        OHLCVPrimitiveBar(
            available_ts=_dt("2024-01-02T14:32:00+00:00"),
            high=112,
            low=104,
            close=110,
            session_label="ETH",
        ),
        OHLCVPrimitiveBar(
            available_ts=_dt("2024-01-02T14:33:00+00:00"),
            high=207,
            low=200,
            close=205,
            session_label="RTH",
        ),
    )

    tr = true_range(bars)
    reset_tr = true_range(bars, reset_on_session=True)
    atr = average_true_range(bars[:2], 2)

    assert [item.value for item in tr] == [pytest.approx(10), pytest.approx(8), pytest.approx(97)]
    assert reset_tr[2].value == pytest.approx(7)
    assert atr[0].value is None
    assert atr[1].value == pytest.approx(9)


def test_trade_and_bbo_row_adapters_surface_gaps_without_imputation() -> None:
    trade_rows = (_ohlcv_row(close="100"), _ohlcv_row_no_trade())
    trade_points = points_from_trade_rows(trade_rows, "close")
    trade_bars = bars_from_trade_rows(trade_rows)
    bbo_points = points_from_bbo_rows((_bbo_row(mid="100"), _bbo_row_missing()), "mid")

    assert trade_points[0].value == pytest.approx(100.0)
    assert trade_points[1].value is None
    assert "no_trade" in trade_points[1].quality_flags
    assert trade_bars[0].is_gap is False
    assert trade_bars[1].is_gap is True
    assert rolling_mean(trade_points, 2)[1].value is None
    assert "input_gap" in rolling_mean(trade_points, 2)[1].quality_flags

    assert bbo_points[0].value == pytest.approx(100.0)
    assert bbo_points[1].value is None
    assert "missing_bbo" in bbo_points[1].quality_flags
    assert rolling_mean(bbo_points, 2)[1].value is None


def test_spec_bound_live_pipeline_consumes_flf_p06_contracts() -> None:
    transform = TransformSpec(transform_id="rolling_mean")
    window = _live_window(2)
    normalization = NormalizationSpec(normalization_id="identity")
    points = (
        _point("2024-01-02T14:31:00+00:00", 1.0),
        _point("2024-01-02T14:32:00+00:00", 3.0),
    )

    pipeline = build_live_primitive(transform, window, normalization)
    result = apply_live_primitive(points, transform, window, normalization)

    assert pipeline.describe()["window"] == window.to_dict()
    assert result[1].value == pytest.approx(2.0)


def test_centered_windows_are_offline_only_and_not_live_bindable() -> None:
    centered = WindowSpec(
        kind=WindowKind.CENTERED,
        length=3,
        causality=WindowCausality.CENTERED,
        offline_only=True,
    )
    points = (
        _point("2024-01-02T14:31:00+00:00", 1.0),
        _point("2024-01-02T14:32:00+00:00", 3.0),
        _point("2024-01-02T14:33:00+00:00", 5.0),
    )

    with pytest.raises(PrimitiveSpecError, match="live primitives"):
        build_live_primitive(
            TransformSpec(transform_id="rolling_mean"),
            centered,
            NormalizationSpec(normalization_id="identity"),
        )

    offline = offline_centered_mean(points, centered)
    assert offline[1].value == pytest.approx(3.0)
    assert any(source_ts > offline[0].available_ts for source_ts in offline[0].source_available_ts)


def _live_window(length: int) -> WindowSpec:
    return WindowSpec(
        kind=WindowKind.ROLLING,
        length=length,
        causality=WindowCausality.CAUSAL,
        offline_only=False,
    )


def _point(
    available_ts: str,
    value: float,
    *,
    event_ts: str | None = None,
    session_label: str = "ETH",
) -> PrimitivePoint:
    return PrimitivePoint(
        available_ts=_dt(available_ts),
        event_ts=_dt(event_ts) if event_ts is not None else _dt(available_ts),
        value=value,
        session_label=session_label,
    )


def _ohlcv_row(*, close: str) -> OHLCVInputRow:
    return OHLCVInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES_CONTINUOUS",
        bar_start_ts=_dt("2024-01-02T14:30:00+00:00"),
        bar_end_ts=_dt("2024-01-02T14:31:00+00:00"),
        event_ts=_dt("2024-01-02T14:31:00+00:00"),
        available_ts=_dt("2024-01-02T14:31:05+00:00"),
        ingested_at=_dt("2024-01-02T14:31:06+00:00"),
        open=Decimal("99"),
        high=Decimal("101"),
        low=Decimal("98"),
        close=Decimal(close),
        volume=Decimal("10"),
        data_version="dsv_fixture",
        quality_flags=(),
        session_label="ETH",
    )


def _ohlcv_row_no_trade() -> OHLCVInputRow:
    return replace(
        _ohlcv_row(close="100"),
        bar_start_ts=_dt("2024-01-02T14:31:00+00:00"),
        bar_end_ts=_dt("2024-01-02T14:32:00+00:00"),
        event_ts=_dt("2024-01-02T14:32:00+00:00"),
        available_ts=_dt("2024-01-02T14:32:05+00:00"),
        quality_flags=("no_trade",),
    )


def _bbo_row(*, mid: str) -> BBOInputRow:
    return BBOInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES_CONTINUOUS",
        bar_start_ts=_dt("2024-01-02T14:30:00+00:00"),
        bar_end_ts=_dt("2024-01-02T14:31:00+00:00"),
        event_ts=_dt("2024-01-02T14:31:00+00:00"),
        available_ts=_dt("2024-01-02T14:31:05+00:00"),
        ingested_at=_dt("2024-01-02T14:31:06+00:00"),
        bid=Decimal("99"),
        ask=Decimal("101"),
        bid_size=Decimal("4"),
        ask_size=Decimal("6"),
        mid=Decimal(mid),
        spread=Decimal("2"),
        data_version="dsv_fixture",
        quality_flags=(),
        session_label="ETH",
        microprice=Decimal("100"),
    )


def _bbo_row_missing() -> BBOInputRow:
    return replace(
        _bbo_row(mid="100"),
        bar_start_ts=_dt("2024-01-02T14:31:00+00:00"),
        bar_end_ts=_dt("2024-01-02T14:32:00+00:00"),
        event_ts=_dt("2024-01-02T14:32:00+00:00"),
        available_ts=_dt("2024-01-02T14:32:05+00:00"),
        bid=Decimal("0"),
        ask=Decimal("0"),
        bid_size=Decimal("0"),
        ask_size=Decimal("0"),
        mid=Decimal("0"),
        spread=Decimal("0"),
        quality_flags=("missing_bbo",),
        microprice=Decimal("0"),
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
