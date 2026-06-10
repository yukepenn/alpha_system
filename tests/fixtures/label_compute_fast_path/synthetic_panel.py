"""Tiny synthetic fixtures for the LCFP shared label panel contract.

Rows in this module are generated test data only. They are not real market
data, not label values, and not alpha evidence.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.families.fixed_horizon import FixedHorizonLabelName

DATASET_ID = "dsv_lcfp_p02_synthetic_panel"


def minute_ohlcv_rows(
    start: datetime,
    *,
    count: int,
    contract_id: str = "ESH4",
    series_id: str = "ES_CONTINUOUS",
    session_label: str = "RTH",
    missing_indices: frozenset[int] = frozenset(),
    no_trade_indices: frozenset[int] = frozenset(),
) -> tuple[dict[str, object], ...]:
    """Return deterministic synthetic OHLCV rows at one-minute spacing."""

    rows: list[dict[str, object]] = []
    for index in range(count):
        if index in missing_indices:
            continue
        event_ts = start + timedelta(minutes=index)
        close = Decimal("100") + Decimal(index) / Decimal("10")
        flags: list[str] = []
        volume = Decimal("10")
        if index in no_trade_indices:
            flags.append("no_trade")
            volume = Decimal("0")
        rows.append(
            {
                "instrument_id": "ES",
                "contract_id": contract_id,
                "series_id": series_id,
                "bar_start_ts": (event_ts - timedelta(minutes=1)).isoformat(),
                "bar_end_ts": event_ts.isoformat(),
                "event_ts": event_ts.isoformat(),
                "available_ts": (event_ts + timedelta(seconds=1)).isoformat(),
                "ingested_at": (event_ts + timedelta(seconds=2)).isoformat(),
                "open": str(close - Decimal("0.05")),
                "high": str(close + Decimal("0.25")),
                "low": str(close - Decimal("0.25")),
                "close": str(close),
                "volume": str(volume),
                "data_version": DATASET_ID,
                "quality_flags": flags,
                "session_label": session_label,
            }
        )
    return tuple(rows)


def bbo_rows_for_ohlcv(
    ohlcv_rows: tuple[dict[str, object], ...],
    *,
    missing_bbo_indices: frozenset[int] = frozenset(),
    quarantined_indices: frozenset[int] = frozenset(),
) -> tuple[dict[str, object], ...]:
    """Return synthetic BBO rows aligned to synthetic OHLCV rows."""

    rows: list[dict[str, object]] = []
    for index, ohlcv in enumerate(ohlcv_rows):
        if index in missing_bbo_indices:
            continue
        close = Decimal(str(ohlcv["close"]))
        bid = close - Decimal("0.125")
        ask = close + Decimal("0.125")
        flags: list[str] = []
        if index in quarantined_indices:
            flags.append("bbo_quarantined")
        rows.append(
            {
                "instrument_id": ohlcv["instrument_id"],
                "contract_id": ohlcv["contract_id"],
                "series_id": ohlcv["series_id"],
                "bar_start_ts": ohlcv["bar_start_ts"],
                "bar_end_ts": ohlcv["bar_end_ts"],
                "event_ts": ohlcv["event_ts"],
                "available_ts": ohlcv["available_ts"],
                "ingested_at": ohlcv["ingested_at"],
                "bid": str(bid),
                "ask": str(ask),
                "bid_size": "12",
                "ask_size": "10",
                "mid": str((bid + ask) / Decimal("2")),
                "spread": str(ask - bid),
                "microprice": None,
                "data_version": DATASET_ID,
                "quality_flags": flags,
                "session_label": ohlcv["session_label"],
            }
        )
    return tuple(rows)


def fixed_horizon_label_spec(
    name: FixedHorizonLabelName = FixedHorizonLabelName.FWD_RET_30M,
    *,
    availability_time: str = "2024-01-01T00:00:00+00:00",
) -> LabelSpec:
    """Return a governed synthetic fixed-horizon LabelSpec."""

    horizon_minutes = int(name.value.removeprefix("fwd_ret_").removesuffix("m"))
    return create_label_spec(
        horizon=f"{horizon_minutes}m",
        path_rules={
            "path": "trade_price_forward_return",
            "horizon_minutes": horizon_minutes,
            "terminal_rule": "synthetic LCFP-P02 terminal",
        },
        cost_model={
            "model": "gross_unadjusted_forward_return",
            "adjustment_scope": "not_applied_in_lcfp_p02_contract_fixture",
        },
        target_stop_rules={
            "target_rule": "not_used_in_lcfp_p02_contract_fixture",
            "stop_rule": "not_used_in_lcfp_p02_contract_fixture",
        },
        availability_time=availability_time,
        forbidden_feature_overlap={
            "label_ids": [name.value],
            "aliases": [f"synthetic_{name.value}"],
            "transforms": [f"label({name.value})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


__all__ = [
    "DATASET_ID",
    "bbo_rows_for_ohlcv",
    "fixed_horizon_label_spec",
    "minute_ohlcv_rows",
]
