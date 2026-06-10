"""Synthetic P05 path-label fixtures.

Rows in this module are generated test data only. They are not real market
data, not materialized label values, and not alpha evidence.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.families.path import PathLabelName

DATASET_ID = "dsv_lcfp_p05_synthetic_path"
PARTITION_ID = "development_partition"
TARGET_FIRST_SOURCE_TS = datetime(2024, 1, 2, 14, 31, tzinfo=UTC)
STOP_FIRST_SOURCE_TS = datetime(2024, 1, 2, 14, 32, tzinfo=UTC)
SAME_BAR_SOURCE_TS = datetime(2024, 1, 2, 14, 35, tzinfo=UTC)
TIMEOUT_SOURCE_TS = datetime(2024, 1, 2, 14, 39, tzinfo=UTC)
SESSION_GAP_SOURCE_TS = datetime(2024, 1, 2, 14, 47, tzinfo=UTC)
ROLL_SOURCE_TS = datetime(2024, 3, 7, 23, 45, tzinfo=UTC)
MAINTENANCE_SOURCE_TS = datetime(2024, 1, 2, 21, 45, tzinfo=UTC)


def path_kernel_ohlcv_rows() -> tuple[dict[str, Any], ...]:
    """Return contiguous synthetic rows for reference-vs-fast path parity."""

    bars = (
        ("100.00", "100.20", "99.80"),
        ("101.00", "103.00", "100.00"),
        ("99.00", "101.00", "97.00"),
        ("100.00", "100.50", "99.50"),
        ("100.00", "100.50", "99.50"),
        ("100.00", "103.00", "97.00"),
        ("100.00", "100.50", "99.50"),
        ("100.00", "100.50", "99.50"),
        ("100.00", "101.00", "99.00"),
        ("100.00", "101.00", "99.00"),
        ("100.00", "101.00", "99.00"),
        ("100.00", "101.00", "99.00"),
        ("100.00", "100.50", "99.50"),
        ("100.00", "100.50", "99.50"),
        ("100.00", "100.50", "99.50"),
        ("100.00", "100.50", "99.50"),
    )
    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    return tuple(
        _ohlcv_row(
            start + timedelta(minutes=index + 1),
            close=Decimal(close),
            high=Decimal(high),
            low=Decimal(low),
        )
        for index, (close, high, low) in enumerate(bars)
    )


def session_gap_ohlcv_rows() -> tuple[dict[str, Any], ...]:
    """Return rows with a no-trade source row to exercise session-gap omission."""

    return (
        _ohlcv_row(
            SESSION_GAP_SOURCE_TS,
            close=Decimal("100"),
            high=Decimal("100.50"),
            low=Decimal("99.50"),
            quality_flags=("no_trade", "session_reset"),
            volume=Decimal("0"),
        ),
        _ohlcv_row(
            SESSION_GAP_SOURCE_TS + timedelta(minutes=1),
            close=Decimal("101"),
            high=Decimal("101.50"),
            low=Decimal("100.50"),
        ),
        _ohlcv_row(
            SESSION_GAP_SOURCE_TS + timedelta(minutes=2),
            close=Decimal("102"),
            high=Decimal("102.50"),
            low=Decimal("101.50"),
        ),
        _ohlcv_row(
            SESSION_GAP_SOURCE_TS + timedelta(minutes=3),
            close=Decimal("103"),
            high=Decimal("103.50"),
            low=Decimal("102.50"),
        ),
    )


def roll_crossing_ohlcv_rows() -> tuple[dict[str, Any], ...]:
    """Return a minimal roll-crossing window retained only as a guard case."""

    terminal_ts = ROLL_SOURCE_TS + timedelta(minutes=240)
    return (
        _ohlcv_row(
            ROLL_SOURCE_TS,
            close=Decimal("100"),
            high=Decimal("100.25"),
            low=Decimal("99.75"),
            contract_id="ESH4",
        ),
        _ohlcv_row(
            terminal_ts,
            close=Decimal("101"),
            high=Decimal("101.25"),
            low=Decimal("100.75"),
            contract_id="ESH4",
        ),
    )


def maintenance_crossing_ohlcv_rows() -> tuple[dict[str, Any], ...]:
    """Return a minimal CME maintenance-crossing window."""

    terminal_ts = MAINTENANCE_SOURCE_TS + timedelta(minutes=240)
    return (
        _ohlcv_row(
            MAINTENANCE_SOURCE_TS,
            close=Decimal("100"),
            high=Decimal("100.25"),
            low=Decimal("99.75"),
        ),
        _ohlcv_row(
            terminal_ts,
            close=Decimal("101"),
            high=Decimal("101.25"),
            low=Decimal("100.75"),
        ),
    )


def maintenance_gap_recovery_ohlcv_rows() -> tuple[dict[str, Any], ...]:
    """Rows spanning the CME maintenance break with full positional windows.

    Reproduces the LCFP-P08 mfe divergence mechanism: the reference family
    resolves ``horizon_steps`` positionally across the break/gap and emits
    records here, while a fixed-minute guarded terminal model finds no bar at
    ``entry + N minutes`` (and a maintenance crossing) and drops them.
    """

    base = datetime(2024, 1, 2, 21, 56, tzinfo=UTC)  # 15:56 America/Chicago
    pre_break = tuple(
        _ohlcv_row(
            base + timedelta(minutes=index),
            close=Decimal("100.00") + Decimal(index),
            high=Decimal("100.50") + Decimal(index),
            low=Decimal("99.50") + Decimal(index),
        )
        for index in range(4)
    )
    post_break_base = datetime(2024, 1, 2, 23, 0, tzinfo=UTC)  # 17:00 America/Chicago
    post_break = tuple(
        _ohlcv_row(
            post_break_base + timedelta(minutes=index),
            close=Decimal("104.00") + Decimal(index),
            high=Decimal("104.50") + Decimal(index),
            low=Decimal("103.50") + Decimal(index),
        )
        for index in range(3)
    )
    return pre_break + post_break


def roll_window_recovery_ohlcv_rows() -> tuple[dict[str, Any], ...]:
    """Contiguous rows inside the ES roll window (2024-03-07).

    Reproduces the LCFP-P08 mfe divergence mechanism for roll windows: the
    reference path family applies no roll guard and emits every full-window
    entry, while a roll-guarded terminal model drops every entry inside the
    analytic roll window.
    """

    base = datetime(2024, 3, 7, 23, 40, tzinfo=UTC)  # 17:40 America/Chicago
    return tuple(
        _ohlcv_row(
            base + timedelta(minutes=index),
            close=Decimal("100.00") + Decimal(index) / Decimal(4),
            high=Decimal("100.25") + Decimal(index) / Decimal(4),
            low=Decimal("99.75") + Decimal(index) / Decimal(4),
            contract_id="ESH4",
        )
        for index in range(8)
    )


def path_label_specs(
    *,
    horizon_steps: int = 3,
    same_bar_policy: str = "ambiguous",
    target_return: float = 0.02,
    stop_return: float = -0.02,
) -> dict[PathLabelName, LabelSpec]:
    """Return governed synthetic LabelSpecs for all P05 path labels."""

    spec = _path_label_spec(
        horizon_steps=horizon_steps,
        same_bar_policy=same_bar_policy,
        target_return=target_return,
        stop_return=stop_return,
    )
    return {label_name: spec for label_name in PathLabelName}


def _path_label_spec(
    *,
    horizon_steps: int,
    same_bar_policy: str,
    target_return: float,
    stop_return: float,
) -> LabelSpec:
    path_ids = [f"path_{label_name.value}" for label_name in PathLabelName]
    return create_label_spec(
        horizon=f"{horizon_steps}_trade_bars",
        path_rules={
            "path": "ohlcv_trade_truth_forward_path",
            "horizon_steps": horizon_steps,
            "price_field": "close",
            "direction": "long",
            "trade_truth_predicate": "alpha_system.features.semantics.is_real_trade_bar",
        },
        cost_model={"model": "gross_path_labels_unadjusted", "reason": "no cost adjustment"},
        target_stop_rules={
            "target_return": target_return,
            "stop_return": stop_return,
            "same_bar_policy": same_bar_policy,
        },
        availability_time="2024-01-02T14:00:00+00:00",
        forbidden_feature_overlap={
            "label_ids": path_ids,
            "aliases": ["mfe", "mae", "target_before_stop", "triple_barrier"],
            "transforms": [f"label({label_id})" for label_id in path_ids],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _ohlcv_row(
    event_ts: datetime,
    *,
    close: Decimal,
    high: Decimal,
    low: Decimal,
    contract_id: str = "ESM4",
    quality_flags: tuple[str, ...] = (),
    volume: Decimal = Decimal("10"),
) -> dict[str, Any]:
    return {
        "instrument_id": "ES",
        "contract_id": contract_id,
        "series_id": "ES_PATH",
        "bar_start_ts": (event_ts - timedelta(minutes=1)).isoformat(),
        "bar_end_ts": event_ts.isoformat(),
        "event_ts": event_ts.isoformat(),
        "available_ts": (event_ts + timedelta(seconds=1)).isoformat(),
        "ingested_at": (event_ts + timedelta(seconds=2)).isoformat(),
        "open": str(close),
        "high": str(high),
        "low": str(low),
        "close": str(close),
        "volume": str(volume),
        "source": "dsrc_synthetic_fixture",
        "source_request_id": "synthetic_lcfp_p05_path",
        "data_version": DATASET_ID,
        "quality_flags": list(quality_flags),
        "session_label": "RTH",
    }


__all__ = [
    "DATASET_ID",
    "MAINTENANCE_SOURCE_TS",
    "PARTITION_ID",
    "ROLL_SOURCE_TS",
    "SAME_BAR_SOURCE_TS",
    "SESSION_GAP_SOURCE_TS",
    "STOP_FIRST_SOURCE_TS",
    "TARGET_FIRST_SOURCE_TS",
    "TIMEOUT_SOURCE_TS",
    "maintenance_crossing_ohlcv_rows",
    "maintenance_gap_recovery_ohlcv_rows",
    "path_kernel_ohlcv_rows",
    "path_label_specs",
    "roll_crossing_ohlcv_rows",
    "roll_window_recovery_ohlcv_rows",
    "session_gap_ohlcv_rows",
]
