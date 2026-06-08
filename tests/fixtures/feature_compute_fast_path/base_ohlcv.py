"""Synthetic Base OHLCV pack fixture for fast-path parity tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

DATASET_ID = "dsv_fast_path_base_ohlcv_pack_v1"
PARTITION_ID = "development_partition"
ROW_COUNT = 32
NO_TRADE_INDEX = 5


def base_ohlcv_pack_rows() -> tuple[dict[str, Any], ...]:
    """Return a tiny deterministic canonical OHLCV frame for the six-feature pack."""

    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    rows: list[dict[str, Any]] = []
    for index in range(ROW_COUNT):
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
                "open": "100",
                "high": "102",
                "low": "98",
                "close": "100",
                "volume": "0" if no_trade else str(100 + ((index * 7) % 17)),
                "source": "dsrc_synthetic_fixture",
                "source_request_id": "synthetic_feature_compute_fast_path_base_ohlcv",
                "data_version": DATASET_ID,
                "quality_flags": ["no_trade"] if no_trade else [],
                "session_label": "RTH",
            }
        )
    return tuple(rows)


__all__ = [
    "DATASET_ID",
    "NO_TRADE_INDEX",
    "PARTITION_ID",
    "ROW_COUNT",
    "base_ohlcv_pack_rows",
]
