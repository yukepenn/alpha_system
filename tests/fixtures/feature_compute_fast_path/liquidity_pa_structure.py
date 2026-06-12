"""Synthetic liquidity sweep / PA-structure pack fixture."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

DATASET_ID = "dsv_fast_path_liquidity_pa_structure_v1"
PARTITION_ID = "development_partition"
ROW_COUNT = 12
WINDOW_LENGTH = 3
OPENING_RANGE_MINUTES = 2
OUTSIDE_OPENING_SESSION_INDEX = 0
HIGH_SWEEP_INDEX = 3
NO_TRADE_INDEX = 4
PRIOR_GAP_INDEX = 5
SESSION_RESET_INDEX = 6
OPENING_RANGE_FROZEN_INDEX = 8
LOW_SWEEP_INDEX = 9
ZERO_RANGE_INDEX = 10
RANGE_CONTRACTION_VALID_INDEX = 11


def liquidity_pa_structure_rows() -> tuple[dict[str, Any], ...]:
    """Return a tiny canonical OHLCV frame for the governed structure pack."""

    # P235500 provenance: SESSION_RESET_INDEX is the real 08:30
    # America/Chicago RTH open under the shared timestamp-derived truth.
    start = datetime(2024, 1, 2, 14, 24, tzinfo=UTC)
    specs = (
        ("ETH", 100.0, 101.0, 99.0, 100.0, 110),
        ("ETH", 100.0, 102.0, 100.0, 101.0, 111),
        ("ETH", 101.0, 103.0, 100.0, 102.0, 112),
        ("ETH", 103.0, 104.0, 100.0, 102.5, 113),
        ("ETH", 102.5, 102.5, 102.5, 102.5, 0),
        ("ETH", 102.0, 105.0, 101.0, 104.0, 115),
        ("RTH", 105.0, 106.0, 104.0, 105.0, 116),
        ("RTH", 105.0, 107.0, 105.0, 106.5, 117),
        ("RTH", 106.5, 108.0, 106.0, 107.5, 118),
        ("RTH", 107.0, 108.0, 103.0, 104.0, 119),
        ("RTH", 104.0, 104.0, 104.0, 104.0, 120),
        ("RTH", 104.0, 105.0, 102.0, 104.5, 121),
    )
    rows: list[dict[str, Any]] = []
    for index, (session, open_, high, low, close, volume) in enumerate(specs):
        bar_start = start + timedelta(minutes=index)
        bar_end = bar_start + timedelta(minutes=1)
        no_trade = index == NO_TRADE_INDEX
        rows.append(
            {
                "instrument_id": "ES",
                "contract_id": "ESM4",
                "series_id": "ES_CONTINUOUS",
                "bar_start_ts": bar_start.isoformat(),
                "bar_end_ts": bar_end.isoformat(),
                "event_ts": bar_end.isoformat(),
                "available_ts": (bar_end + timedelta(seconds=1)).isoformat(),
                "ingested_at": (bar_end + timedelta(seconds=2)).isoformat(),
                "open": str(open_),
                "high": str(high),
                "low": str(low),
                "close": str(close),
                "volume": str(volume),
                "source": "dsrc_synthetic_fixture",
                "source_request_id": "synthetic_feature_compute_fast_path_liquidity_pa",
                "data_version": DATASET_ID,
                "quality_flags": ["input_gap", "no_trade"] if no_trade else [],
                "session_label": session,
            }
        )
    return tuple(rows)


__all__ = [
    "DATASET_ID",
    "HIGH_SWEEP_INDEX",
    "LOW_SWEEP_INDEX",
    "NO_TRADE_INDEX",
    "OPENING_RANGE_FROZEN_INDEX",
    "OPENING_RANGE_MINUTES",
    "OUTSIDE_OPENING_SESSION_INDEX",
    "PARTITION_ID",
    "PRIOR_GAP_INDEX",
    "RANGE_CONTRACTION_VALID_INDEX",
    "ROW_COUNT",
    "SESSION_RESET_INDEX",
    "WINDOW_LENGTH",
    "ZERO_RANGE_INDEX",
    "liquidity_pa_structure_rows",
]
