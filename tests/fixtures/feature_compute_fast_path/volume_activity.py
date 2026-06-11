"""Synthetic volume / activity pack fixture."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

DATASET_ID = "dsv_fast_path_volume_activity_v1"
PARTITION_ID = "development_partition"
WINDOW_LENGTH = 20
STRUCTURE_WINDOW_LENGTH = 3
ROW_COUNT = 47
FIRST_VALID_INDEX = 19
INPUT_GAP_INDEX = 20
SESSION_RESET_INDEX = 25
SECOND_SESSION_VALID_INDEX = 44
ZERO_RANGE_INDEX = 46


def volume_activity_rows() -> tuple[dict[str, Any], ...]:
    """Return a tiny canonical OHLCV frame for the governed volume/activity pack."""

    # P194500 repair provenance: the synthetic session transition at
    # SESSION_RESET_INDEX is pinned to 15:00 America/Chicago, matching the
    # shared timestamp-derived RTH/ETH truth.
    start = datetime(2024, 1, 2, 20, 35, tzinfo=UTC)
    rows: list[dict[str, Any]] = []
    for index in range(ROW_COUNT):
        session = "RTH" if index < SESSION_RESET_INDEX else "ETH"
        bar_start = start + timedelta(minutes=index)
        bar_end = bar_start + timedelta(minutes=1)
        base = 100.0 + index * 0.75 + (10.0 if session == "ETH" else 0.0)
        open_ = base + (0.1 if index % 2 else 0.0)
        high = base + 1.4 + (0.05 * (index % 3))
        low = base - 1.2 - (0.05 * (index % 2))
        close = base + ((index % 5) - 2) * 0.12
        volume = 100 + index * 4 + (index % 4) * 7
        quality_flags: list[str] = []
        if index == INPUT_GAP_INDEX:
            volume = 0
            quality_flags = ["input_gap", "no_trade"]
        if index == ZERO_RANGE_INDEX:
            open_ = high = low = close = base
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
                "open": f"{open_:.6f}",
                "high": f"{high:.6f}",
                "low": f"{low:.6f}",
                "close": f"{close:.6f}",
                "volume": str(volume),
                "source": "dsrc_synthetic_fixture",
                "source_request_id": "synthetic_feature_compute_fast_path_volume_activity",
                "data_version": DATASET_ID,
                "quality_flags": quality_flags,
                "session_label": session,
            }
        )
    return tuple(rows)


__all__ = [
    "DATASET_ID",
    "FIRST_VALID_INDEX",
    "INPUT_GAP_INDEX",
    "PARTITION_ID",
    "ROW_COUNT",
    "SECOND_SESSION_VALID_INDEX",
    "SESSION_RESET_INDEX",
    "STRUCTURE_WINDOW_LENGTH",
    "WINDOW_LENGTH",
    "ZERO_RANGE_INDEX",
    "volume_activity_rows",
]
