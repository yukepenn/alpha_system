"""Synthetic regime / volatility / compression pack fixture."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

DATASET_ID = "dsv_fast_path_regime_vol_compression_v1"
PARTITION_ID = "development_partition"
ROW_COUNT = 12
WINDOW_LENGTH = 3
FIRST_SESSION_ZERO_MOVEMENT_INDEX = 2
NO_TRADE_INDEX = 4
SESSION_RESET_INDEX = 6
RANGE_CONTRACTION_VALID_INDEX = 9
SECOND_SESSION_ZERO_MOVEMENT_INDEX = 11


def regime_vol_compression_rows() -> tuple[dict[str, Any], ...]:
    """Return a tiny canonical OHLCV frame for the governed regime pack."""

    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    specs = (
        ("RTH", 100.0, 101.0, 99.0, 100.0, 110),
        ("RTH", 100.0, 101.0, 99.0, 100.0, 111),
        ("RTH", 100.0, 101.0, 99.0, 100.0, 112),
        ("RTH", 103.0, 104.0, 101.0, 103.0, 113),
        ("RTH", 103.0, 103.0, 103.0, 103.0, 0),
        ("RTH", 105.0, 106.0, 104.0, 105.0, 115),
        ("ETH", 110.0, 111.0, 109.0, 110.0, 116),
        ("ETH", 111.0, 112.0, 110.0, 111.0, 117),
        ("ETH", 112.0, 113.0, 111.0, 112.0, 118),
        ("ETH", 114.0, 115.0, 113.0, 114.0, 119),
        ("ETH", 114.0, 115.0, 113.0, 114.0, 120),
        ("ETH", 114.0, 115.0, 113.0, 114.0, 121),
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
                "source_request_id": (
                    "synthetic_feature_compute_fast_path_regime_vol_compression"
                ),
                "data_version": DATASET_ID,
                "quality_flags": ["no_trade"] if no_trade else [],
                "session_label": session,
            }
        )
    return tuple(rows)


__all__ = [
    "DATASET_ID",
    "FIRST_SESSION_ZERO_MOVEMENT_INDEX",
    "NO_TRADE_INDEX",
    "PARTITION_ID",
    "RANGE_CONTRACTION_VALID_INDEX",
    "ROW_COUNT",
    "SECOND_SESSION_ZERO_MOVEMENT_INDEX",
    "SESSION_RESET_INDEX",
    "WINDOW_LENGTH",
    "regime_vol_compression_rows",
]
