from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from alpha_system.features.contracts import WindowCausality
from alpha_system.features.input_views import (
    BBOInputRow,
    BBOInputView,
    CanonicalInputViews,
    OHLCVInputRow,
    OHLCVInputView,
)
from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelError,
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
    build_fixed_horizon_label_definitions,
    compute_fixed_horizon_label,
    compute_fixed_horizon_labels,
    supported_fixed_horizon_labels,
)
from alpha_system.labels.version import LabelContractError

RESEARCH_ROOT = (
    Path(__file__).resolve().parents[5] / "research/futures_core_alpha_pilot_v1"
)


def test_all_fixed_horizon_labels_are_governed_versioned_and_label_only() -> None:
    trade_view = _trade_view(length=35)
    bbo_view = _bbo_view(length=35)
    definitions = build_fixed_horizon_label_definitions(
        {name: _label_spec(name) for name in supported_fixed_horizon_labels()},
        dataset_version_ids=("dsv_synthetic_fixed_horizon",),
    )

    results = compute_fixed_horizon_labels(definitions, CanonicalInputViews(trade_view, bbo_view))

    assert {definition.name for definition in definitions} == set(FixedHorizonLabelName)
    for definition in definitions:
        assert definition.label_spec_id.startswith("lspec_")
        assert definition.version == definition.contract.derive_label_version()
        assert definition.contract.path.window is not None
        assert definition.contract.path.window.causality is WindowCausality.FUTURE
        assert definition.contract.path.window.offline_only is True
        assert definition.contract.availability_policy.future_data_legal_only_for_labels is True
        assert definition.name in results
        horizon = _horizon_minutes(definition.name)
        records = results[definition.name]
        # A forward-horizon label is undefined for the final `horizon` bars, so a
        # horizon >= the fixture length yields zero records (floor at 0 rather than
        # going negative for the extended 60m/120m/240m horizons).
        assert len(records) == max(0, 35 - horizon)
        assert all(record.label_version_id == definition.label_version_id for record in records)
        assert all(record.label_spec_id == definition.label_spec_id for record in records)

        with pytest.raises(LabelContractError, match="live feature"):
            definition.validate_not_live_feature(
                [
                    {
                        "feature_id": definition.label_id,
                        "available_at": "2024-01-02T14:30:00+00:00",
                    }
                ]
            )

    fwd_1m = results[FixedHorizonLabelName.FWD_RET_1M][0]
    mid_1m = results[FixedHorizonLabelName.MID_FWD_RET_1M][0]

    assert fwd_1m.value == pytest.approx(101 / 100 - 1)
    assert fwd_1m.horizon_end_ts == trade_view.rows[1].event_ts
    assert fwd_1m.label_available_ts == trade_view.rows[1].available_ts
    assert mid_1m.value == pytest.approx(100.5 / 100 - 1)
    assert mid_1m.horizon_end_ts == bbo_view.rows[1].event_ts
    assert mid_1m.label_available_ts == bbo_view.rows[1].available_ts


def test_trade_price_labels_do_not_treat_no_trade_rows_as_trade_bars() -> None:
    view = _trade_view(length=5, no_trade_indices={1, 2})
    definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_1M,
        _label_spec(FixedHorizonLabelName.FWD_RET_1M),
    )

    records = compute_fixed_horizon_label(definition, view)

    assert records[0].value is None
    assert "horizon_not_trade" in records[0].quality_flags
    assert "no_trade" in records[0].quality_flags
    assert records[1].value is None
    assert "source_not_trade" in records[1].quality_flags
    assert "no_trade" in records[1].quality_flags
    assert records[3].value == pytest.approx(104 / 103 - 1)


def test_fwd_ret_15m_uses_exact_terminal_row_without_same_bar_optimism() -> None:
    view = _trade_view(length=17)
    definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_15M,
        _label_spec(FixedHorizonLabelName.FWD_RET_15M),
    )

    records = compute_fixed_horizon_label(definition, view)

    assert len(records) == 2
    first = records[0]
    source = view.rows[0]
    same_bar = view.rows[0]
    one_minute = view.rows[1]
    terminal = view.rows[15]
    assert first.horizon_end_ts == terminal.event_ts
    assert first.value == pytest.approx(115 / 100 - 1)
    assert first.value != pytest.approx(float(same_bar.close / source.close - 1))
    assert first.value != pytest.approx(float(one_minute.close / source.close - 1))
    assert first.label_available_ts == terminal.available_ts
    assert all(record.label_available_ts >= record.horizon_end_ts for record in records)


def test_fwd_ret_15m_waits_for_governed_availability_without_session_final_inputs() -> None:
    view = _trade_view(length=16)
    governed_available = view.rows[15].available_ts + timedelta(minutes=5)
    definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_15M,
        _label_spec(
            FixedHorizonLabelName.FWD_RET_15M,
            availability_time=governed_available.isoformat(),
        ),
    )

    records = compute_fixed_horizon_label(definition, view)

    assert len(records) == 1
    assert records[0].label_available_ts == governed_available
    assert records[0].label_available_ts > records[0].horizon_end_ts
    input_fields = definition.contract.inputs.fields
    assert "session_close" not in input_fields
    assert "final_session_aggregate" not in input_fields


def test_futcore_p15_fwd_ret_15m_label_spec_file_is_governed_and_labels_only() -> None:
    spec = LabelSpec.from_mapping(
        json.loads((RESEARCH_ROOT / "label_specs/fwd_ret_15m.json").read_text())
    )
    view = _trade_view(length=16)
    definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_15M,
        spec,
    )

    records = compute_fixed_horizon_label(definition, view)

    assert spec.label_spec_id == "lspec_8ea5c33463a47d467963d216"
    assert spec.path_rules["gap_id"] == "P15-G1"
    assert records[0].label_spec_id == spec.label_spec_id
    assert records[0].horizon_end_ts == view.rows[15].event_ts
    assert records[0].label_available_ts == view.rows[15].available_ts


def test_midprice_labels_flag_missing_and_quarantined_bbo_without_fill() -> None:
    view = _bbo_view(length=5, missing_indices={1}, quarantined_indices={2})
    definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.MID_FWD_RET_1M,
        _label_spec(FixedHorizonLabelName.MID_FWD_RET_1M),
    )

    records = compute_fixed_horizon_label(definition, view)

    assert records[0].value is None
    assert "horizon_bbo_gap" in records[0].quality_flags
    assert "missing_bbo" in records[0].quality_flags
    assert records[1].value is None
    assert "source_bbo_gap" in records[1].quality_flags
    assert "missing_bbo" in records[1].quality_flags
    assert "bbo_quarantined" in records[1].quality_flags
    assert records[2].value is None
    assert "source_bbo_gap" in records[2].quality_flags
    assert "bbo_quarantined" in records[2].quality_flags
    assert records[3].value == pytest.approx(102 / 101.5 - 1)


def test_missing_horizon_end_available_ts_fails_closed() -> None:
    view = _trade_view(length=3)
    object.__setattr__(view.rows[1], "available_ts", None)
    definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_1M,
        _label_spec(FixedHorizonLabelName.FWD_RET_1M),
    )

    with pytest.raises(FixedHorizonLabelError, match="available_ts"):
        compute_fixed_horizon_label(definition, view)


def test_absent_or_invalid_lspec_binding_fails_closed() -> None:
    name = FixedHorizonLabelName.FWD_RET_3M

    with pytest.raises(FixedHorizonLabelError, match="lspec_ binding"):
        build_fixed_horizon_label_definition(name, None)

    unapproved_payload = _label_spec(name).to_dict()
    unapproved_payload["label_spec_id"] = _mutated_id(unapproved_payload["label_spec_id"])
    with pytest.raises(FixedHorizonLabelError, match="lspec_ binding is invalid"):
        build_fixed_horizon_label_definition(name, unapproved_payload)

    with pytest.raises(FixedHorizonLabelError, match="LabelSpec.horizon"):
        build_fixed_horizon_label_definition(
            name,
            _label_spec(FixedHorizonLabelName.FWD_RET_1M),
        )


def test_incomplete_forward_horizon_is_excluded_not_peeked() -> None:
    view = _trade_view(length=2)
    definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_3M,
        _label_spec(FixedHorizonLabelName.FWD_RET_3M),
    )

    records = compute_fixed_horizon_label(definition, view)

    assert records == ()


def test_wrong_input_view_for_label_kind_fails_closed() -> None:
    mid_definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.MID_FWD_RET_1M,
        _label_spec(FixedHorizonLabelName.MID_FWD_RET_1M),
    )
    trade_definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_1M,
        _label_spec(FixedHorizonLabelName.FWD_RET_1M),
    )

    with pytest.raises(FixedHorizonLabelError, match="BBOInputView"):
        compute_fixed_horizon_label(mid_definition, _trade_view(length=3))
    with pytest.raises(FixedHorizonLabelError, match="OHLCVInputView"):
        compute_fixed_horizon_label(trade_definition, _bbo_view(length=3))


def _label_spec(
    name: FixedHorizonLabelName,
    *,
    availability_time: str = "2024-01-02T14:00:00+00:00",
) -> LabelSpec:
    horizon = _horizon_minutes(name)
    path = (
        "midprice_forward_return"
        if name.value.startswith("mid_")
        else "trade_price_forward_return"
    )
    return create_label_spec(
        horizon=f"{horizon}m",
        path_rules={
            "path": path,
            "horizon_minutes": horizon,
            "terminal_rule": "exact event_ts row at fixed forward horizon",
        },
        cost_model={
            "model": "gross_unadjusted_forward_return",
            "adjustment_scope": "not_applied_in_fixed_horizon_family",
        },
        target_stop_rules={
            "target_rule": "not_used_for_fixed_horizon_return",
            "stop_rule": "not_used_for_fixed_horizon_return",
        },
        availability_time=availability_time,
        forbidden_feature_overlap={
            "label_ids": [name.value],
            "aliases": [name.value.replace("_ret_", "_return_")],
            "transforms": [f"label({name.value})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _trade_view(
    *,
    length: int,
    no_trade_indices: set[int] | None = None,
) -> OHLCVInputView:
    no_trade_indices = no_trade_indices or set()
    start = _dt("2024-01-02T14:30:00+00:00")
    return OHLCVInputView(
        tuple(
            _trade_row(
                start + timedelta(minutes=index),
                close=Decimal("100") + Decimal(index),
                no_trade=index in no_trade_indices,
            )
            for index in range(length)
        )
    )


def _trade_row(
    bar_start_ts: datetime,
    *,
    close: Decimal,
    no_trade: bool = False,
) -> OHLCVInputRow:
    return OHLCVInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES.c.0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=bar_start_ts + timedelta(minutes=1, seconds=1),
        ingested_at=bar_start_ts + timedelta(minutes=1, seconds=2),
        open=close,
        high=close if no_trade else close + Decimal("1"),
        low=close if no_trade else close - Decimal("1"),
        close=close,
        volume=Decimal("0") if no_trade else Decimal("100"),
        data_version="dsv_synthetic_ohlcv",
        quality_flags=("no_trade",) if no_trade else (),
        session_label="RTH",
    )


def _bbo_view(
    *,
    length: int,
    missing_indices: set[int] | None = None,
    quarantined_indices: set[int] | None = None,
) -> BBOInputView:
    missing_indices = missing_indices or set()
    quarantined_indices = quarantined_indices or set()
    start = _dt("2024-01-02T14:30:00+00:00")
    return BBOInputView(
        tuple(
            _bbo_row(
                start + timedelta(minutes=index),
                mid=Decimal("100") + Decimal(index) * Decimal("0.5"),
                missing=index in missing_indices,
                quarantined=index in quarantined_indices,
            )
            for index in range(length)
        )
    )


def _bbo_row(
    bar_start_ts: datetime,
    *,
    mid: Decimal,
    missing: bool = False,
    quarantined: bool = False,
) -> BBOInputRow:
    if missing:
        bid = ask = spread = Decimal("0")
        bid_size = ask_size = Decimal("0")
        mid_value = Decimal("0")
        quality_flags = ("missing_bbo",)
    elif quarantined:
        bid = mid + Decimal("1")
        ask = mid - Decimal("1")
        spread = ask - bid
        bid_size = ask_size = Decimal("10")
        mid_value = mid
        quality_flags = ("bbo_quarantined",)
    else:
        bid = mid - Decimal("0.5")
        ask = mid + Decimal("0.5")
        spread = ask - bid
        bid_size = ask_size = Decimal("10")
        mid_value = mid
        quality_flags = ()
    return BBOInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES.c.0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=bar_start_ts + timedelta(minutes=1, seconds=1),
        ingested_at=bar_start_ts + timedelta(minutes=1, seconds=2),
        bid=bid,
        ask=ask,
        bid_size=bid_size,
        ask_size=ask_size,
        mid=mid_value,
        spread=spread,
        data_version="dsv_synthetic_bbo",
        quality_flags=quality_flags,
        session_label="RTH",
    )


def _horizon_minutes(name: FixedHorizonLabelName) -> int:
    return int(name.value.rsplit("_", maxsplit=1)[1].removesuffix("m"))


def _mutated_id(value: str) -> str:
    suffix = "0" if value[-1] != "0" else "1"
    return f"{value[:-1]}{suffix}"


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
