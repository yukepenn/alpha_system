"""Synthetic fixed-horizon label pack fixture for fast-path parity tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelName,
    supported_fixed_horizon_labels,
)

DATASET_ID = "dsv_fast_path_fixed_horizon_label_pack_v1"
PARTITION_ID = "development_partition"
ROW_COUNT = 720
ROLL_SOURCE_INDEX = 5
NO_TRADE_TERMINAL_INDEX = 32
MAINTENANCE_SOURCE_INDEX = 440
MAINTENANCE_TERMINAL_INDEX = 470
BBO_MISSING_SOURCE_INDEX = 4
BBO_QUARANTINED_TERMINAL_INDEX = 300


def fixed_horizon_ohlcv_rows() -> tuple[dict[str, Any], ...]:
    """Return tiny synthetic OHLCV rows covering all governed fixed horizons."""

    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    rows: list[dict[str, Any]] = []
    for index in range(ROW_COUNT):
        bar_start = start + timedelta(minutes=index)
        bar_end = bar_start + timedelta(minutes=1)
        flags: list[str] = []
        volume = Decimal("10")
        if index == ROLL_SOURCE_INDEX:
            flags = ["no_trade", "roll_splice_boundary"]
            volume = Decimal("0")
        if index == NO_TRADE_TERMINAL_INDEX:
            flags = ["no_trade"]
            volume = Decimal("0")
        if index == MAINTENANCE_TERMINAL_INDEX:
            flags = ["no_trade", "maintenance_crossing"]
            volume = Decimal("0")
        close = Decimal("100") + Decimal(index) / Decimal("10")
        rows.append(
            {
                "instrument_id": "ES",
                "contract_id": "ESM4" if index < 18 else "ESU4",
                "series_id": "ES_CONTINUOUS",
                "bar_start_ts": bar_start.isoformat(),
                "bar_end_ts": bar_end.isoformat(),
                "event_ts": bar_end.isoformat(),
                "available_ts": (bar_end + timedelta(seconds=1)).isoformat(),
                "ingested_at": (bar_end + timedelta(seconds=2)).isoformat(),
                "open": str(close - Decimal("0.05")),
                "high": str(close + Decimal("0.10")),
                "low": str(close - Decimal("0.10")),
                "close": str(close),
                "volume": str(volume),
                "source": "dsrc_synthetic_fixture",
                "source_request_id": "synthetic_fixed_horizon_ohlcv",
                "data_version": DATASET_ID,
                "quality_flags": flags,
                "session_label": "RTH",
            }
        )
    return tuple(rows)


def fixed_horizon_bbo_rows() -> tuple[dict[str, Any], ...]:
    """Return tiny synthetic BBO rows covering missing and quarantined gaps."""

    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    rows: list[dict[str, Any]] = []
    for index in range(ROW_COUNT):
        bar_start = start + timedelta(minutes=index)
        bar_end = bar_start + timedelta(minutes=1)
        flags: list[str] = []
        bid = Decimal("99") + Decimal(index) / Decimal("10")
        ask = bid + Decimal("0.25")
        bid_size = Decimal("12")
        ask_size = Decimal("10")
        if index == BBO_MISSING_SOURCE_INDEX:
            flags = ["missing_bbo"]
            bid = ask = bid_size = ask_size = Decimal("0")
        if index == BBO_QUARANTINED_TERMINAL_INDEX:
            flags = ["bbo_quarantined"]
        mid = (bid + ask) / Decimal("2")
        spread = ask - bid
        rows.append(
            {
                "instrument_id": "ES",
                "contract_id": "ESM4" if index < 18 else "ESU4",
                "series_id": "ES_CONTINUOUS",
                "bar_start_ts": bar_start.isoformat(),
                "bar_end_ts": bar_end.isoformat(),
                "event_ts": bar_end.isoformat(),
                "available_ts": (bar_end + timedelta(seconds=1)).isoformat(),
                "ingested_at": (bar_end + timedelta(seconds=2)).isoformat(),
                "bid": str(bid),
                "ask": str(ask),
                "bid_size": str(bid_size),
                "ask_size": str(ask_size),
                "mid": str(mid),
                "spread": str(spread),
                "source": "dsrc_synthetic_fixture",
                "source_request_id": "synthetic_fixed_horizon_bbo",
                "data_version": DATASET_ID,
                "quality_flags": flags,
                "session_label": "RTH",
                "spread_ticks": None,
                "microprice": None,
                "bid_order_count": None,
                "ask_order_count": None,
            }
        )
    return tuple(rows)


def governed_fixed_horizon_label_specs() -> dict[FixedHorizonLabelName, LabelSpec]:
    """Return one governed synthetic LabelSpec per current fixed-horizon label."""

    return {
        label_name: _label_spec(label_name)
        for label_name in supported_fixed_horizon_labels()
    }


def _label_spec(label_name: FixedHorizonLabelName) -> LabelSpec:
    horizon_minutes = _horizon_minutes_or_none(label_name)
    if horizon_minutes is None:
        return _close_out_label_spec(label_name)
    is_mid = label_name.value.startswith("mid_")
    path = "midprice_forward_return" if is_mid else "trade_price_forward_return"
    return create_label_spec(
        horizon=f"{horizon_minutes}m",
        path_rules={
            "path": path,
            "horizon_minutes": horizon_minutes,
            "terminal_rule": "exact event_ts row at fixed forward horizon",
        },
        cost_model={
            "model": "gross_unadjusted_forward_return",
            "adjustment_scope": "not_applied_in_fixed_horizon_fast_path_fixture",
        },
        target_stop_rules={
            "target_rule": "not_used_for_fixed_horizon_fast_path_fixture",
            "stop_rule": "not_used_for_fixed_horizon_fast_path_fixture",
        },
        availability_time="2024-01-02T14:00:00+00:00",
        forbidden_feature_overlap={
            "label_ids": [label_name.value],
            "aliases": [f"synthetic_{label_name.value}"],
            "transforms": [f"label({label_name.value})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _close_out_label_spec(label_name: FixedHorizonLabelName) -> LabelSpec:
    if label_name not in {
        FixedHorizonLabelName.SESSION_CLOSE,
        FixedHorizonLabelName.MAINTENANCE_FLAT,
    }:
        raise ValueError(f"unsupported close-out fixture label: {label_name.value}")
    return create_label_spec(
        horizon=label_name.value,
        path_rules={
            "path": "trade_price_close_out_return",
            "close_out_terminal": label_name.value,
            "terminal_rule": "synthetic close-out terminal routed to LCFP-P04",
        },
        cost_model={
            "model": "gross_unadjusted_forward_return",
            "adjustment_scope": "not_applied_in_fixed_horizon_fast_path_fixture",
        },
        target_stop_rules={
            "target_rule": "not_used_for_fixed_horizon_fast_path_fixture",
            "stop_rule": "not_used_for_fixed_horizon_fast_path_fixture",
        },
        availability_time="2024-01-02T14:00:00+00:00",
        forbidden_feature_overlap={
            "label_ids": [label_name.value],
            "aliases": [f"synthetic_{label_name.value}"],
            "transforms": [f"label({label_name.value})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _horizon_minutes(label_name: FixedHorizonLabelName) -> int:
    horizon_minutes = _horizon_minutes_or_none(label_name)
    if horizon_minutes is None:
        raise ValueError(f"{label_name.value} is not a fixed-minute horizon")
    return horizon_minutes


def _horizon_minutes_or_none(label_name: FixedHorizonLabelName) -> int | None:
    token = label_name.value.removeprefix("mid_fwd_ret_").removeprefix("fwd_ret_")
    if not token.endswith("m"):
        return None
    minutes = token.removesuffix("m")
    if not minutes.isdigit():
        return None
    return int(minutes)


__all__ = [
    "BBO_MISSING_SOURCE_INDEX",
    "BBO_QUARANTINED_TERMINAL_INDEX",
    "DATASET_ID",
    "MAINTENANCE_TERMINAL_INDEX",
    "MAINTENANCE_SOURCE_INDEX",
    "NO_TRADE_TERMINAL_INDEX",
    "PARTITION_ID",
    "ROLL_SOURCE_INDEX",
    "ROW_COUNT",
    "fixed_horizon_bbo_rows",
    "fixed_horizon_ohlcv_rows",
    "governed_fixed_horizon_label_specs",
]
