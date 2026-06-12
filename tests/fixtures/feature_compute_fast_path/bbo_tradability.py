"""Synthetic BBO tradability pack fixture."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

DATASET_ID = "dsv_fast_path_bbo_tradability_v1"
PARTITION_ID = "development_partition"
WINDOW_LENGTH = 3
ROW_COUNT = 10
FIRST_ZSCORE_VALID_INDEX = 2
MISSING_BBO_INDEX = 3
QUARANTINED_BBO_INDEX = 4
WIDE_LOW_DEPTH_INDEX = 5
SESSION_RESET_INDEX = 6
SECOND_SESSION_VALID_INDEX = 8
MISSING_SPREAD_TICKS_INDEX = 9

_MID = Decimal("128")


def bbo_tradability_rows() -> tuple[dict[str, Any], ...]:
    """Return a tiny synthetic canonical BBO frame for the governed BBO pack."""

    # P235500 provenance: SESSION_RESET_INDEX is the real 15:00
    # America/Chicago RTH close under the shared timestamp-derived truth.
    start = datetime(2024, 1, 2, 20, 54, tzinfo=UTC)
    row_specs = (
        {"session": "RTH", "spread": "0.25", "bid_size": "8", "ask_size": "24"},
        {"session": "RTH", "spread": "0.50", "bid_size": "8", "ask_size": "24"},
        {"session": "RTH", "spread": "0.75", "bid_size": "8", "ask_size": "24"},
        {
            "session": "RTH",
            "spread": "0",
            "bid_size": "0",
            "ask_size": "0",
            "quality_flags": ["missing_bbo"],
            "missing": True,
        },
        {
            "session": "RTH",
            "spread": "1.00",
            "bid_size": "8",
            "ask_size": "24",
            "quality_flags": ["bbo_quarantined"],
        },
        {"session": "RTH", "spread": "2.00", "bid_size": "0.25", "ask_size": "0.25"},
        {"session": "ETH", "spread": "0.25", "bid_size": "8", "ask_size": "24"},
        {"session": "ETH", "spread": "0.50", "bid_size": "8", "ask_size": "24"},
        {"session": "ETH", "spread": "1.00", "bid_size": "8", "ask_size": "24"},
        {
            "session": "ETH",
            "spread": "1.50",
            "bid_size": "8",
            "ask_size": "24",
            "spread_ticks": None,
        },
    )
    return tuple(_row(index, start, spec) for index, spec in enumerate(row_specs))


def _row(index: int, start: datetime, spec: dict[str, Any]) -> dict[str, Any]:
    bar_start = start + timedelta(minutes=index)
    bar_end = bar_start + timedelta(minutes=1)
    spread = Decimal(str(spec["spread"]))
    bid_size = Decimal(str(spec["bid_size"]))
    ask_size = Decimal(str(spec["ask_size"]))
    missing = bool(spec.get("missing", False))
    if missing:
        bid = ask = mid = Decimal("0")
        microprice = None
    else:
        mid = _MID
        bid = mid - spread / Decimal("2")
        ask = mid + spread / Decimal("2")
        microprice = (ask * bid_size + bid * ask_size) / (bid_size + ask_size)
    spread_ticks = spec.get("spread_ticks", spread / Decimal("0.25") if not missing else None)
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
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
        "source_request_id": "synthetic_feature_compute_fast_path_bbo_tradability",
        "data_version": DATASET_ID,
        "quality_flags": list(spec.get("quality_flags", [])),
        "session_label": str(spec["session"]),
        "spread_ticks": str(spread_ticks) if spread_ticks is not None else None,
        "microprice": str(microprice) if microprice is not None else None,
    }


__all__ = [
    "DATASET_ID",
    "FIRST_ZSCORE_VALID_INDEX",
    "MISSING_BBO_INDEX",
    "MISSING_SPREAD_TICKS_INDEX",
    "PARTITION_ID",
    "QUARANTINED_BBO_INDEX",
    "ROW_COUNT",
    "SECOND_SESSION_VALID_INDEX",
    "SESSION_RESET_INDEX",
    "WIDE_LOW_DEPTH_INDEX",
    "WINDOW_LENGTH",
    "bbo_tradability_rows",
]
