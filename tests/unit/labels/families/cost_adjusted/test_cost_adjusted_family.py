from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from alpha_system.data.foundation.grid import (
    NO_TRADE_QUALITY_FLAG,
    PREVIOUS_CLOSE_FILL_METHOD,
    DenseGridBarRecord,
)
from alpha_system.features.input_views import BBOInputRow, BBOInputView
from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.families.cost_adjusted import (
    CostAdjustedForwardReturnSpec,
    CostAdjustedLabelError,
    CostAdjustedLabelName,
    SpreadAdjustedForwardReturnSpec,
    build_cost_adjusted_label_definition,
    compute_cost_adjusted_label,
    compute_cost_adjusted_labels,
    supported_cost_adjusted_labels,
)
from alpha_system.labels.version import LabelContractError, LabelValueRecord


def test_cost_and_spread_adjusted_labels_are_governance_bound_and_available() -> None:
    view = _fixture_view()
    cost_spec = _governance_label_spec(
        CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
        cost_model={
            "model": "spread_plus_bps",
            "spread_adjustment": "half_spread_round_trip",
            "fixed_cost_bps": 1.0,
        },
    )
    spread_spec = _governance_label_spec(
        CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET,
        cost_model={
            "model": "spread_adjusted",
            "spread_adjustment": "half_spread_round_trip",
        },
    )
    definitions = (
        build_cost_adjusted_label_definition(
            CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
            cost_spec,
            dataset_version_ids=("dsv_synthetic_bbo",),
        ),
        build_cost_adjusted_label_definition(
            CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET,
            spread_spec,
            dataset_version_ids=("dsv_synthetic_bbo",),
        ),
    )

    results = compute_cost_adjusted_labels(definitions, view)

    assert supported_cost_adjusted_labels() == tuple(CostAdjustedLabelName)
    cost_definition, spread_definition = definitions
    assert isinstance(cost_definition.spec, CostAdjustedForwardReturnSpec)
    assert isinstance(spread_definition.spec, SpreadAdjustedForwardReturnSpec)
    assert cost_definition.spec.label_spec_id == cost_spec.label_spec_id
    assert cost_definition.spec.label_spec_id.startswith("lspec_")
    assert cost_definition.spec.cost_adjustment.cost_model.to_dict() == cost_spec.cost_model
    assert spread_definition.spec.cost_adjustment.cost_model.to_dict() == spread_spec.cost_model

    cost_records = results[CostAdjustedLabelName.COST_ADJUSTED_FWD_RET]
    spread_records = results[CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET]
    raw_return = (Decimal("104") / Decimal("100")) - Decimal("1")
    half_spread_adjustment = (Decimal("0.5") * Decimal("2") / Decimal("100")) + (
        Decimal("0.5") * Decimal("4") / Decimal("104")
    )
    expected_spread_adjusted = raw_return - half_spread_adjustment
    expected_cost_adjusted = expected_spread_adjusted - (Decimal("1.0") / Decimal("10000"))

    assert len(cost_records) == len(view.rows)
    assert cost_records[0].value == pytest.approx(float(expected_cost_adjusted))
    assert spread_records[0].value == pytest.approx(float(expected_spread_adjusted))
    assert cost_records[0].label_spec_id == cost_spec.label_spec_id
    assert cost_records[0].label_available_ts == _dt("2024-01-02T14:34:00+00:00")
    assert cost_records[0].horizon_end_ts == _dt("2024-01-02T14:33:00+00:00")
    assert all(record.label_available_ts is not None for record in cost_records)


def test_missing_lspec_binding_fails_closed() -> None:
    with pytest.raises(LabelContractError, match="lspec_ binding"):
        build_cost_adjusted_label_definition(
            CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
            None,
        )


def test_label_value_record_requires_label_available_ts_for_cost_contract() -> None:
    definition = build_cost_adjusted_label_definition(
        CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
        _governance_label_spec(
            CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
            cost_model={
                "model": "spread_plus_bps",
                "spread_adjustment": "half_spread_round_trip",
                "fixed_cost_bps": 1.0,
            },
        ),
    )
    contract = definition.spec.label_contract

    with pytest.raises(TypeError):
        LabelValueRecord(  # type: ignore[call-arg]
            label_version_id=definition.label_version_id,
            entity_id="ES_c_0",
            event_ts=_dt("2024-01-02T14:31:00+00:00"),
            horizon_end_ts=_dt("2024-01-02T14:33:00+00:00"),
            value=0.0,
            label_contract=contract,
        )
    with pytest.raises(LabelContractError, match="label_available_ts"):
        LabelValueRecord(
            label_version_id=definition.label_version_id,
            entity_id="ES_c_0",
            event_ts=_dt("2024-01-02T14:31:00+00:00"),
            horizon_end_ts=_dt("2024-01-02T14:33:00+00:00"),
            label_available_ts=None,  # type: ignore[arg-type]
            value=0.0,
            label_contract=contract,
        )


def test_invalid_cost_model_fails_closed_before_values() -> None:
    with pytest.raises(CostAdjustedLabelError, match="fixed_cost_bps"):
        build_cost_adjusted_label_definition(
            CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
            _governance_label_spec(
                CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
                cost_model={
                    "model": "spread_plus_bps",
                    "spread_adjustment": "half_spread_round_trip",
                },
            ),
        )


def test_missing_or_quarantined_bbo_are_not_used_or_forward_filled() -> None:
    start = _dt("2024-01-02T14:30:00+00:00")
    view = BBOInputView(
        (
            _bbo_row(start, bid="99", ask="101"),
            _bbo_row(
                start + timedelta(minutes=1),
                bid="105",
                ask="104",
                mid="104.5",
                spread="-1",
                quality_flags=("bbo_quarantined",),
            ),
            _bbo_row(
                start + timedelta(minutes=2),
                bid="0",
                ask="0",
                quality_flags=("missing_bbo",),
            ),
            _bbo_row(start + timedelta(minutes=3), bid="103", ask="105"),
        )
    )
    definition = build_cost_adjusted_label_definition(
        CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET,
        _governance_label_spec(
            CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET,
            cost_model={
                "model": "spread_adjusted",
                "spread_adjustment": "half_spread_round_trip",
            },
        ),
    )

    records = compute_cost_adjusted_label(definition, view)

    assert records[0].value is None
    assert "terminal_bbo_gap" in records[0].quality_flags
    assert "missing_bbo" in records[0].quality_flags
    assert records[1].value is None
    assert "entry_bbo_gap" in records[1].quality_flags
    assert "bbo_quarantined" in records[1].quality_flags


def test_synthetic_no_trade_rows_are_flagged_not_trade_anchors() -> None:
    view = _fixture_view()
    definition = build_cost_adjusted_label_definition(
        CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
        _governance_label_spec(
            CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
            cost_model={
                "model": "spread_plus_bps",
                "spread_adjustment": "half_spread_round_trip",
                "fixed_cost_bps": 1.0,
            },
        ),
    )

    records = compute_cost_adjusted_label(
        definition,
        view,
        trade_rows=(_dense_no_trade_row(view.rows[0].bar_start_ts),),
    )

    assert records[0].value is None
    assert "synthetic_no_trade" in records[0].quality_flags
    assert "no_trade" in records[0].quality_flags
    assert records[0].label_available_ts == _dt("2024-01-02T14:34:00+00:00")


def _fixture_view() -> BBOInputView:
    start = _dt("2024-01-02T14:30:00+00:00")
    return BBOInputView(
        (
            _bbo_row(start, bid="99", ask="101"),
            _bbo_row(start + timedelta(minutes=1), bid="100", ask="102"),
            _bbo_row(start + timedelta(minutes=2), bid="102", ask="106"),
            _bbo_row(start + timedelta(minutes=3), bid="103", ask="105"),
        )
    )


def _bbo_row(
    bar_start_ts: datetime,
    *,
    bid: str,
    ask: str,
    mid: str | None = None,
    spread: str | None = None,
    quality_flags: tuple[str, ...] = (),
) -> BBOInputRow:
    bid_decimal = Decimal(bid)
    ask_decimal = Decimal(ask)
    mid_decimal = Decimal(mid) if mid is not None else (bid_decimal + ask_decimal) / Decimal("2")
    spread_decimal = Decimal(spread) if spread is not None else ask_decimal - bid_decimal
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
        mid=mid_decimal,
        spread=spread_decimal,
        data_version="dsv_synthetic_bbo",
        quality_flags=quality_flags,
        session_label="RTH",
    )


def _dense_no_trade_row(bar_start_ts: datetime) -> DenseGridBarRecord:
    return DenseGridBarRecord(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES_c_0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=bar_start_ts + timedelta(minutes=1, seconds=1),
        ingested_at=bar_start_ts + timedelta(minutes=1, seconds=2),
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        volume=Decimal("0"),
        source="dsrc_synthetic",
        source_request_id="req_synthetic",
        data_version="dsv_synthetic_dense",
        quality_flags=(NO_TRADE_QUALITY_FLAG,),
        session_label="RTH",
        has_trade=False,
        synthetic=True,
        fill_method=PREVIOUS_CLOSE_FILL_METHOD,
        provider_bar_ref=None,
    )


def _governance_label_spec(
    label_name: CostAdjustedLabelName,
    *,
    cost_model: dict[str, object],
) -> LabelSpec:
    return create_label_spec(
        horizon="2m",
        path_rules={
            "path": "bbo_mid_forward_return",
            "terminal_rule": "exact event_ts match with valid BBO only",
            "horizon_steps": 2,
        },
        cost_model=cost_model,
        target_stop_rules={
            "target_rule": "disabled_for_cost_adjusted_fixture",
            "stop_rule": "disabled_for_cost_adjusted_fixture",
        },
        availability_time="2024-01-02T14:34:00+00:00",
        forbidden_feature_overlap={
            "label_ids": [label_name.value],
            "aliases": [f"{label_name.value}_fixture"],
            "transforms": [f"label({label_name.value})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
