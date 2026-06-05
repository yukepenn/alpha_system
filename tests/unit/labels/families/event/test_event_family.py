from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from alpha_system.features.input_views import (
    BBOInputRow,
    BBOInputView,
    CanonicalInputViews,
    OHLCVInputRow,
    OHLCVInputView,
)
from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.families.event import (
    EventLabelError,
    EventLabelName,
    build_event_label_definition,
    build_event_label_definitions,
    compute_event_label,
    compute_event_labels,
    supported_event_labels,
)
from alpha_system.labels.version import LabelContractError, LabelFamily


def test_all_event_labels_are_governance_bound_versioned_and_available() -> None:
    views = CanonicalInputViews(_trade_view(), _bbo_view())
    definitions = build_event_label_definitions(
        {name: _label_spec(name) for name in supported_event_labels()},
        dataset_version_ids=("dsv_synthetic_event",),
    )

    results = compute_event_labels(definitions, views)

    assert set(results) == set(EventLabelName)
    for definition in definitions:
        records = results[definition.name]
        assert definition.contract.family is LabelFamily.EVENT
        assert definition.label_spec_id.startswith("lspec_")
        assert definition.version == definition.contract.derive_label_version()
        assert definition.contract.path.window is not None
        assert definition.contract.path.window.offline_only is True
        assert definition.contract.availability_policy.future_data_legal_only_for_labels is True
        assert records
        assert all(record.label_spec_id == definition.label_spec_id for record in records)
        assert all(record.label_version_id == definition.label_version_id for record in records)
        assert all(record.label_available_ts >= record.horizon_end_ts for record in records)

        with pytest.raises(LabelContractError, match="live feature"):
            definition.validate_not_live_feature(
                [
                    {
                        "feature_id": definition.label_id,
                        "available_at": "2024-01-02T14:31:00+00:00",
                    }
                ]
            )

    breakout = results[EventLabelName.BREAKOUT_SUCCESS][0]
    sweep = results[EventLabelName.SWEEP_OUTCOME][0]
    liquidity = results[EventLabelName.LIQUIDITY_QUALITY_FUTURE][0]

    assert breakout.value is True
    assert breakout.horizon_end_ts == _dt("2024-01-02T14:32:00+00:00")
    assert breakout.label_available_ts == _dt("2024-01-02T14:32:01+00:00")
    assert sweep.value == "continuation"
    assert liquidity.value is True
    assert liquidity.horizon_end_ts == _dt("2024-01-02T14:33:00+00:00")
    assert liquidity.label_available_ts == _dt("2024-01-02T14:33:01+00:00")


def test_label_available_ts_respects_governed_availability_time() -> None:
    definition = build_event_label_definition(
        EventLabelName.RETURN_TO_VWAP,
        _label_spec(
            EventLabelName.RETURN_TO_VWAP,
            availability_time="2024-01-02T15:00:00+00:00",
        ),
    )

    record = compute_event_label(definition, _trade_view())[0]

    assert record.horizon_end_ts == _dt("2024-01-02T14:32:00+00:00")
    assert record.label_available_ts == _dt("2024-01-02T15:00:00+00:00")


def test_synthetic_no_trade_rows_are_excluded_from_event_and_outcome_detection() -> None:
    view = _trade_view(no_trade_indices={1})
    definition = build_event_label_definition(
        EventLabelName.BREAKOUT_SUCCESS,
        _label_spec(EventLabelName.BREAKOUT_SUCCESS, horizon_steps=2),
    )

    records = compute_event_label(definition, view)

    no_trade_event_ts = view.rows[1].event_ts
    assert no_trade_event_ts not in {record.event_ts for record in records}
    assert records[0].event_ts == view.rows[0].event_ts
    assert records[0].horizon_end_ts == view.rows[2].event_ts
    assert records[0].value is True


def test_missing_and_quarantined_bbo_are_flagged_without_fill() -> None:
    start = _dt("2024-01-02T14:30:00+00:00")
    views = CanonicalInputViews(
        _trade_view(),
        BBOInputView(
            (
                _bbo_row(start, bid="99", ask="101"),
                _bbo_row(
                    start + timedelta(minutes=1),
                    bid="0",
                    ask="0",
                    quality_flags=("missing_bbo",),
                ),
                _bbo_row(start + timedelta(minutes=2), bid="100", ask="102"),
                _bbo_row(
                    start + timedelta(minutes=3),
                    bid="103",
                    ask="105",
                    quality_flags=("bbo_quarantined",),
                ),
            )
        ),
    )
    definition = build_event_label_definition(
        EventLabelName.LIQUIDITY_QUALITY_FUTURE,
        _label_spec(EventLabelName.LIQUIDITY_QUALITY_FUTURE, horizon_steps=1),
    )

    records = compute_event_label(definition, views)

    assert records[0].value is None
    assert "future_bbo_gap" in records[0].quality_flags
    assert "missing_bbo" in records[0].quality_flags
    assert records[2].value is None
    assert "future_bbo_gap" in records[2].quality_flags
    assert "bbo_quarantined" in records[2].quality_flags


def test_absent_or_invalid_lspec_binding_fails_closed_before_values() -> None:
    with pytest.raises(EventLabelError, match="lspec_ binding"):
        build_event_label_definition(EventLabelName.BREAKOUT_SUCCESS, None)

    payload = _label_spec(EventLabelName.BREAKOUT_SUCCESS).to_dict()
    suffix = "0" if not payload["label_spec_id"].endswith("0") else "1"
    payload["label_spec_id"] = f"{payload['label_spec_id'][:-1]}{suffix}"
    with pytest.raises(EventLabelError, match="lspec_ binding is invalid"):
        build_event_label_definition(EventLabelName.BREAKOUT_SUCCESS, payload)

    with pytest.raises(EventLabelError, match="event_label"):
        build_event_label_definition(
            EventLabelName.BREAKOUT_SUCCESS,
            _label_spec(EventLabelName.RETURN_TO_VWAP),
        )


def test_wrong_input_view_for_label_kind_fails_closed() -> None:
    trade_definition = build_event_label_definition(
        EventLabelName.SWEEP_OUTCOME,
        _label_spec(EventLabelName.SWEEP_OUTCOME),
    )
    liquidity_definition = build_event_label_definition(
        EventLabelName.LIQUIDITY_QUALITY_FUTURE,
        _label_spec(EventLabelName.LIQUIDITY_QUALITY_FUTURE),
    )

    with pytest.raises(EventLabelError, match="OHLCVInputView"):
        compute_event_label(trade_definition, _bbo_view())
    with pytest.raises(EventLabelError, match="BBOInputView"):
        compute_event_label(liquidity_definition, _trade_view())


def _trade_view(no_trade_indices: set[int] | None = None) -> OHLCVInputView:
    no_trade_indices = no_trade_indices or set()
    start = _dt("2024-01-02T14:30:00+00:00")
    rows = (
        _row(start, open_="100", high="100.5", low="99.5", close="100"),
        _row(
            start + timedelta(minutes=1),
            open_="101",
            high="104",
            low="100",
            close="103",
            no_trade=1 in no_trade_indices,
        ),
        _row(start + timedelta(minutes=2), open_="103", high="105", low="99", close="101"),
        _row(start + timedelta(minutes=3), open_="101", high="102", low="98", close="99"),
        _row(start + timedelta(minutes=4), open_="99", high="103", low="97", close="102"),
    )
    return OHLCVInputView(rows)


def _row(
    bar_start_ts: datetime,
    *,
    open_: str,
    high: str,
    low: str,
    close: str,
    no_trade: bool = False,
) -> OHLCVInputRow:
    return OHLCVInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES_c_0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=bar_start_ts + timedelta(minutes=1, seconds=1),
        ingested_at=bar_start_ts + timedelta(minutes=1, seconds=2),
        open=Decimal(close) if no_trade else Decimal(open_),
        high=Decimal(close) if no_trade else Decimal(high),
        low=Decimal(close) if no_trade else Decimal(low),
        close=Decimal(close),
        volume=Decimal("0") if no_trade else Decimal("10"),
        data_version="dsv_synthetic_event_ohlcv",
        quality_flags=("no_trade",) if no_trade else (),
        session_label="RTH",
    )


def _bbo_view() -> BBOInputView:
    start = _dt("2024-01-02T14:30:00+00:00")
    return BBOInputView(
        (
            _bbo_row(start, bid="99", ask="101"),
            _bbo_row(start + timedelta(minutes=1), bid="100", ask="102"),
            _bbo_row(start + timedelta(minutes=2), bid="101", ask="103"),
            _bbo_row(start + timedelta(minutes=3), bid="102", ask="104"),
            _bbo_row(start + timedelta(minutes=4), bid="103", ask="105"),
        )
    )


def _bbo_row(
    bar_start_ts: datetime,
    *,
    bid: str,
    ask: str,
    quality_flags: tuple[str, ...] = (),
) -> BBOInputRow:
    bid_decimal = Decimal(bid)
    ask_decimal = Decimal(ask)
    return BBOInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES_c_0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=bar_start_ts + timedelta(minutes=1, seconds=1),
        ingested_at=bar_start_ts + timedelta(minutes=1, seconds=2),
        bid=bid_decimal,
        ask=ask_decimal,
        bid_size=Decimal("10"),
        ask_size=Decimal("10"),
        mid=(bid_decimal + ask_decimal) / Decimal("2"),
        spread=ask_decimal - bid_decimal,
        data_version="dsv_synthetic_event_bbo",
        quality_flags=quality_flags,
        session_label="RTH",
    )


def _label_spec(
    name: EventLabelName,
    *,
    horizon_steps: int = 2,
    availability_time: str = "2024-01-02T14:29:00+00:00",
) -> LabelSpec:
    label_ids = [label.value for label in EventLabelName]
    return create_label_spec(
        horizon=f"{horizon_steps}m",
        path_rules={
            "path": "strategy_agnostic_event_outcome",
            "event_label": name.value,
            "horizon_steps": horizon_steps,
            "horizon_minutes": horizon_steps,
            "direction": "up",
            "sweep_side": "buy_side",
            "vwap_price": 100,
            "vwap_tolerance_bps": 0,
        },
        cost_model={
            "model": "not_applied_to_event_outcome_labels",
            "reason": "strategy_agnostic_event_descriptor",
        },
        target_stop_rules={
            "success_return": 0.02,
            "failure_return": 0.02,
            "continuation_return": 0.03,
            "reversal_return": 0.02,
            "max_mean_spread_bps": 250,
        },
        availability_time=availability_time,
        forbidden_feature_overlap={
            "label_ids": label_ids,
            "aliases": [label.replace("_", "-") for label in label_ids],
            "transforms": [f"label({label_id})" for label_id in label_ids],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
