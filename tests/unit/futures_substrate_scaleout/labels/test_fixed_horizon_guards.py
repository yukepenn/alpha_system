from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from alpha_system.features.input_views import OHLCVInputRow, OHLCVInputView
from alpha_system.governance.label_spec import create_label_spec
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
    compute_fixed_horizon_label,
)


DATASET_ID = "dsv_futsub_p16_synthetic"


def test_roll_crossing_fixed_horizon_window_is_dropped() -> None:
    definition = _definition(FixedHorizonLabelName.FWD_RET_30M)
    source_ts = _dt("2024-03-07T23:45:00+00:00")
    terminal_ts = source_ts + timedelta(minutes=30)

    records = compute_fixed_horizon_label(
        definition,
        OHLCVInputView(
            (
                _row(source_ts, contract_id="ESM4", close=Decimal("100")),
                _row(terminal_ts, contract_id="ESM4", close=Decimal("101")),
            )
        ),
    )

    assert records == ()


def test_contract_scoped_terminal_key_prevents_splice() -> None:
    definition = _definition(FixedHorizonLabelName.FWD_RET_30M)
    source_ts = _dt("2024-01-02T14:30:00+00:00")
    terminal_ts = source_ts + timedelta(minutes=30)

    records = compute_fixed_horizon_label(
        definition,
        OHLCVInputView(
            (
                _row(source_ts, contract_id="ESM4", close=Decimal("100")),
                _row(terminal_ts, contract_id="ESU4", close=Decimal("101")),
            )
        ),
    )

    assert records == ()


def test_maintenance_crossing_fixed_horizon_window_is_dropped() -> None:
    definition = _definition(FixedHorizonLabelName.FWD_RET_30M)
    source_ts = _dt("2024-01-02T21:45:00+00:00")
    terminal_ts = source_ts + timedelta(minutes=30)

    records = compute_fixed_horizon_label(
        definition,
        OHLCVInputView(
            (
                _row(source_ts, contract_id="ESH4", close=Decimal("100")),
                _row(terminal_ts, contract_id="ESH4", close=Decimal("101")),
            )
        ),
    )

    assert records == ()


def test_non_crossing_window_keeps_label_available_ts() -> None:
    definition = _definition(FixedHorizonLabelName.FWD_RET_30M)
    source_ts = _dt("2024-01-02T14:30:00+00:00")
    terminal_ts = source_ts + timedelta(minutes=30)
    terminal_available_ts = terminal_ts + timedelta(seconds=2)

    records = compute_fixed_horizon_label(
        definition,
        OHLCVInputView(
            (
                _row(source_ts, contract_id="ESH4", close=Decimal("100")),
                _row(
                    terminal_ts,
                    contract_id="ESH4",
                    close=Decimal("101"),
                    available_ts=terminal_available_ts,
                ),
            )
        ),
    )

    assert len(records) == 1
    assert records[0].value == pytest.approx(0.01)
    assert records[0].label_available_ts == terminal_available_ts


def _definition(name: FixedHorizonLabelName):
    horizon_minutes = int(name.value.removeprefix("fwd_ret_").removesuffix("m"))
    return build_fixed_horizon_label_definition(
        name,
        create_label_spec(
            horizon=f"{horizon_minutes}m",
            path_rules={
                "path": "trade_price_forward_return",
                "horizon_minutes": horizon_minutes,
                "terminal_rule": "synthetic fixed-horizon test terminal",
            },
            cost_model={
                "model": "gross_unadjusted_forward_return",
                "adjustment_scope": "not_applied_in_guard_test",
            },
            target_stop_rules={
                "target_rule": "not_used_for_fixed_horizon_guard_test",
                "stop_rule": "not_used_for_fixed_horizon_guard_test",
            },
            availability_time="2024-01-01T00:00:00+00:00",
            forbidden_feature_overlap={
                "label_ids": [name.value],
                "aliases": [f"synthetic_{name.value}"],
                "transforms": [f"label({name.value})"],
            },
            leakage_checks=["label_as_feature", "availability_time"],
        ),
        dataset_version_ids=(DATASET_ID,),
    )


def _row(
    event_ts: datetime,
    *,
    contract_id: str,
    close: Decimal,
    available_ts: datetime | None = None,
) -> OHLCVInputRow:
    bar_start = event_ts - timedelta(minutes=1)
    available = available_ts or event_ts + timedelta(seconds=1)
    return OHLCVInputRow(
        instrument_id="ES",
        contract_id=contract_id,
        series_id="ES_CONTINUOUS",
        bar_start_ts=bar_start,
        bar_end_ts=event_ts,
        event_ts=event_ts,
        available_ts=available,
        ingested_at=available + timedelta(seconds=1),
        open=close,
        high=close + Decimal("0.25"),
        low=close - Decimal("0.25"),
        close=close,
        volume=Decimal("10"),
        data_version=DATASET_ID,
        quality_flags=(),
        session_label="ETH",
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
