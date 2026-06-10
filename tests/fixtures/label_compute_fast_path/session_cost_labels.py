"""Synthetic P04 session, maintenance, and cost label fixtures.

Rows in this module are generated test data only. They are not real market
data, not materialized label values, and not alpha evidence.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.families.cost_adjusted import CostAdjustedLabelName
from alpha_system.labels.families.fixed_horizon import FixedHorizonLabelName

DATASET_ID = "dsv_lcfp_p04_synthetic_session_cost"
PARTITION_ID = "development_partition"
SESSION_NORMAL_SOURCE_TS = datetime(2024, 1, 2, 20, 58, tzinfo=UTC)
SESSION_GAP_SOURCE_TS = datetime(2024, 1, 2, 21, 30, tzinfo=UTC)
MAINTENANCE_NORMAL_SOURCE_TS = datetime(2024, 1, 2, 21, 30, tzinfo=UTC)
ROLL_SOURCE_TS = datetime(2024, 3, 6, 23, 45, tzinfo=UTC)
COST_NORMAL_SOURCE_TS = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
COST_TERMINAL_GAP_SOURCE_TS = datetime(2024, 1, 2, 14, 31, tzinfo=UTC)
COST_MISSING_SOURCE_TS = datetime(2024, 1, 2, 14, 33, tzinfo=UTC)


def session_maintenance_ohlcv_rows() -> tuple[dict[str, Any], ...]:
    """Return synthetic close-out rows with session-gap and roll-drop cases."""

    return (
        _ohlcv_row(SESSION_NORMAL_SOURCE_TS, close=Decimal("100"), contract_id="ESM4"),
        _ohlcv_row(datetime(2024, 1, 2, 20, 59, tzinfo=UTC), close=Decimal("101"), contract_id="ESM4"),
        _ohlcv_row(datetime(2024, 1, 2, 21, 0, tzinfo=UTC), close=Decimal("102"), contract_id="ESM4"),
        _ohlcv_row(SESSION_GAP_SOURCE_TS, close=Decimal("103"), contract_id="ESM4"),
        _ohlcv_row(datetime(2024, 1, 2, 22, 0, tzinfo=UTC), close=Decimal("104"), contract_id="ESM4"),
        _ohlcv_row(ROLL_SOURCE_TS, close=Decimal("200"), contract_id="ESH4"),
        _ohlcv_row(datetime(2024, 3, 7, 21, 0, tzinfo=UTC), close=Decimal("202"), contract_id="ESH4"),
        _ohlcv_row(datetime(2024, 3, 7, 22, 0, tzinfo=UTC), close=Decimal("203"), contract_id="ESH4"),
    )


def cost_adjusted_ohlcv_rows() -> tuple[dict[str, Any], ...]:
    """Return OHLCV rows aligned to the synthetic BBO cost fixture."""

    return tuple(
        _ohlcv_row(
            datetime(2024, 1, 2, 14, 30, tzinfo=UTC) + timedelta(minutes=index),
            close=Decimal("100") + Decimal(index),
            contract_id="ESM4",
            series_id="ES_COST",
        )
        for index in range(5)
    )


def cost_adjusted_bbo_rows() -> tuple[dict[str, Any], ...]:
    """Return BBO rows covering normal, terminal-gap, and missing-BBO cases."""

    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    rows = []
    for index in range(5):
        event_ts = start + timedelta(minutes=index)
        bid = Decimal("99") + Decimal(index)
        ask = bid + Decimal("2")
        flags: list[str] = []
        if event_ts == COST_MISSING_SOURCE_TS:
            bid = ask = Decimal("0")
            flags.append("missing_bbo")
        rows.append(
            _bbo_row(
                event_ts,
                bid=bid,
                ask=ask,
                contract_id="ESM4",
                series_id="ES_COST",
                quality_flags=tuple(flags),
            )
        )
    return tuple(rows)


def session_maintenance_label_specs() -> dict[FixedHorizonLabelName, LabelSpec]:
    """Return governed synthetic LabelSpecs for P04 close-out labels."""

    return {
        FixedHorizonLabelName.SESSION_CLOSE: _close_out_label_spec(
            FixedHorizonLabelName.SESSION_CLOSE
        ),
        FixedHorizonLabelName.MAINTENANCE_FLAT: _close_out_label_spec(
            FixedHorizonLabelName.MAINTENANCE_FLAT
        ),
    }


def cost_adjusted_label_specs() -> dict[CostAdjustedLabelName, LabelSpec]:
    """Return governed synthetic LabelSpecs for P04 cost-adjusted labels."""

    return {
        CostAdjustedLabelName.COST_ADJUSTED_FWD_RET: _cost_label_spec(
            CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
            cost_model={
                "model": "spread_plus_bps",
                "spread_adjustment": "half_spread_round_trip",
                "fixed_cost_bps": 1.0,
            },
        ),
        CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET: _cost_label_spec(
            CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET,
            cost_model={
                "model": "spread_adjusted",
                "spread_adjustment": "half_spread_round_trip",
            },
        ),
    }


def _ohlcv_row(
    event_ts: datetime,
    *,
    close: Decimal,
    contract_id: str,
    series_id: str = "ES_CONTINUOUS",
) -> dict[str, Any]:
    return {
        "instrument_id": "ES",
        "contract_id": contract_id,
        "series_id": series_id,
        "bar_start_ts": (event_ts - timedelta(minutes=1)).isoformat(),
        "bar_end_ts": event_ts.isoformat(),
        "event_ts": event_ts.isoformat(),
        "available_ts": (event_ts + timedelta(seconds=1)).isoformat(),
        "ingested_at": (event_ts + timedelta(seconds=2)).isoformat(),
        "open": str(close - Decimal("0.25")),
        "high": str(close + Decimal("0.25")),
        "low": str(close - Decimal("0.25")),
        "close": str(close),
        "volume": "10",
        "source": "dsrc_synthetic_fixture",
        "source_request_id": "synthetic_lcfp_p04_ohlcv",
        "data_version": DATASET_ID,
        "quality_flags": [],
        "session_label": "RTH",
    }


def _bbo_row(
    event_ts: datetime,
    *,
    bid: Decimal,
    ask: Decimal,
    contract_id: str,
    series_id: str,
    quality_flags: tuple[str, ...] = (),
) -> dict[str, Any]:
    mid = (bid + ask) / Decimal("2")
    spread = ask - bid
    size = "0" if "missing_bbo" in quality_flags else "10"
    return {
        "instrument_id": "ES",
        "contract_id": contract_id,
        "series_id": series_id,
        "bar_start_ts": (event_ts - timedelta(minutes=1)).isoformat(),
        "bar_end_ts": event_ts.isoformat(),
        "event_ts": event_ts.isoformat(),
        "available_ts": (event_ts + timedelta(seconds=1)).isoformat(),
        "ingested_at": (event_ts + timedelta(seconds=2)).isoformat(),
        "bid": str(bid),
        "ask": str(ask),
        "bid_size": size,
        "ask_size": size,
        "mid": str(mid),
        "spread": str(spread),
        "source": "dsrc_synthetic_fixture",
        "source_request_id": "synthetic_lcfp_p04_bbo",
        "data_version": DATASET_ID,
        "quality_flags": list(quality_flags),
        "session_label": "RTH",
        "spread_ticks": None,
        "microprice": None,
        "bid_order_count": None,
        "ask_order_count": None,
    }


def _close_out_label_spec(label_name: FixedHorizonLabelName) -> LabelSpec:
    return create_label_spec(
        horizon=label_name.value,
        path_rules={
            "path": "trade_price_close_out_return",
            "close_out_terminal": label_name.value,
            "terminal_rule": "synthetic P04 close-out terminal",
        },
        cost_model={
            "model": "gross_unadjusted_forward_return",
            "adjustment_scope": "not_applied_in_lcfp_p04_close_out_fixture",
        },
        target_stop_rules={
            "target_rule": "not_used_for_lcfp_p04_close_out_fixture",
            "stop_rule": "not_used_for_lcfp_p04_close_out_fixture",
        },
        availability_time="2024-01-02T14:00:00+00:00",
        forbidden_feature_overlap={
            "label_ids": [label_name.value],
            "aliases": [f"synthetic_{label_name.value}"],
            "transforms": [f"label({label_name.value})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _cost_label_spec(
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
            "target_rule": "disabled_for_lcfp_p04_cost_fixture",
            "stop_rule": "disabled_for_lcfp_p04_cost_fixture",
        },
        availability_time="2024-01-02T14:34:00+00:00",
        forbidden_feature_overlap={
            "label_ids": [label_name.value],
            "aliases": [f"synthetic_{label_name.value}"],
            "transforms": [f"label({label_name.value})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


__all__ = [
    "COST_MISSING_SOURCE_TS",
    "COST_NORMAL_SOURCE_TS",
    "COST_TERMINAL_GAP_SOURCE_TS",
    "DATASET_ID",
    "MAINTENANCE_NORMAL_SOURCE_TS",
    "PARTITION_ID",
    "ROLL_SOURCE_TS",
    "SESSION_GAP_SOURCE_TS",
    "SESSION_NORMAL_SOURCE_TS",
    "cost_adjusted_bbo_rows",
    "cost_adjusted_label_specs",
    "cost_adjusted_ohlcv_rows",
    "session_maintenance_label_specs",
    "session_maintenance_ohlcv_rows",
]
