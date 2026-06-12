"""DST-aware synthetic rows for fast-path session-boundary parity tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

DATASET_ID = "dsv_fast_path_dst_session_boundary_v1"
PARTITION_ID = "development_partition"
WINDOW_LENGTH = 3
VOLUME_WINDOW_LENGTH = 20
STATIC_SESSION_LABEL = "ETH"

PRE_DST_RTH_OPEN_TS = datetime(2024, 3, 8, 14, 30, tzinfo=UTC)
POST_DST_RTH_OPEN_TS = datetime(2024, 3, 11, 13, 30, tzinfo=UTC)
SUMMER_RTH_OPEN_TS = datetime(2024, 7, 2, 13, 30, tzinfo=UTC)
RTH_OPEN_BAR_STARTS = (
    PRE_DST_RTH_OPEN_TS,
    POST_DST_RTH_OPEN_TS,
    SUMMER_RTH_OPEN_TS,
)

_MARKETS = ("ES", "NQ", "RTY")


def dst_ohlcv_rows() -> tuple[dict[str, Any], ...]:
    """Return static-label OHLCV rows spanning CST, CDT, and summer boundaries."""

    return tuple(
        _ohlcv_mapping("ES", bar_start, ordinal)
        for ordinal, bar_start in enumerate(_bar_starts())
    )


def dst_bbo_rows() -> tuple[dict[str, Any], ...]:
    """Return static-label BBO rows over the same boundary timestamps."""

    return tuple(
        _bbo_mapping("ES", bar_start, ordinal)
        for ordinal, bar_start in enumerate(_bar_starts())
    )


def dst_cross_market_ohlcv_rows() -> tuple[dict[str, Any], ...]:
    """Return static-label ES/NQ/RTY OHLCV rows for strict-intersection parity."""

    rows: list[dict[str, Any]] = []
    for ordinal, bar_start in enumerate(_bar_starts()):
        for market_index, market in enumerate(_MARKETS):
            rows.append(_ohlcv_mapping(market, bar_start, ordinal, market_index=market_index))
    return tuple(rows)


def dst_rth_open_event_timestamps() -> tuple[datetime, ...]:
    """Return event timestamps for the RTH-open bars represented in this fixture."""

    return tuple(bar_start + timedelta(minutes=1) for bar_start in RTH_OPEN_BAR_STARTS)


def _bar_starts() -> tuple[datetime, ...]:
    # Static fixture timestamps only: session labels below are intentionally not
    # derived here. The test's reference and fast paths must derive session truth.
    starts: list[datetime] = []
    for rth_open in RTH_OPEN_BAR_STARTS:
        starts.extend(rth_open + timedelta(minutes=offset) for offset in range(-2, 23))
    return tuple(starts)


def _ohlcv_mapping(
    market: str,
    bar_start_ts: datetime,
    ordinal: int,
    *,
    market_index: int = 0,
) -> dict[str, Any]:
    bar_end = bar_start_ts + timedelta(minutes=1)
    base = Decimal("100") + Decimal(market_index * 50) + Decimal(ordinal) / Decimal("10")
    high = base + Decimal("1.25")
    low = base - Decimal("1.00")
    close = base + (Decimal(ordinal % 5) - Decimal("2")) / Decimal("20")
    return {
        "instrument_id": market,
        "contract_id": f"{market}M4",
        "series_id": f"{market}_CONTINUOUS",
        "bar_start_ts": bar_start_ts.isoformat(),
        "bar_end_ts": bar_end.isoformat(),
        "event_ts": bar_end.isoformat(),
        "available_ts": (bar_end + timedelta(seconds=1 + market_index)).isoformat(),
        "ingested_at": (bar_end + timedelta(seconds=5 + market_index)).isoformat(),
        "open": str(base),
        "high": str(high),
        "low": str(low),
        "close": str(close),
        "volume": str(100 + ordinal + market_index),
        "source": "dsrc_synthetic_fixture",
        "source_request_id": "synthetic_feature_compute_fast_path_dst_boundary",
        "data_version": DATASET_ID,
        "quality_flags": [],
        "session_label": STATIC_SESSION_LABEL,
    }


def _bbo_mapping(market: str, bar_start_ts: datetime, ordinal: int) -> dict[str, Any]:
    bar_end = bar_start_ts + timedelta(minutes=1)
    mid = Decimal("128") + Decimal(ordinal % 7) / Decimal("10")
    spread = Decimal("0.25") + Decimal(ordinal % 4) / Decimal("20")
    bid = mid - spread / Decimal("2")
    ask = mid + spread / Decimal("2")
    bid_size = Decimal("10") + Decimal(ordinal % 3)
    ask_size = Decimal("12") + Decimal(ordinal % 5)
    microprice = (ask * bid_size + bid * ask_size) / (bid_size + ask_size)
    return {
        "instrument_id": market,
        "contract_id": f"{market}M4",
        "series_id": f"{market}_CONTINUOUS",
        "bar_start_ts": bar_start_ts.isoformat(),
        "bar_end_ts": bar_end.isoformat(),
        "event_ts": (bar_end - timedelta(milliseconds=200)).isoformat(),
        "available_ts": (bar_end + timedelta(seconds=1)).isoformat(),
        "ingested_at": (bar_end + timedelta(seconds=5)).isoformat(),
        "bid": str(bid),
        "ask": str(ask),
        "bid_size": str(bid_size),
        "ask_size": str(ask_size),
        "mid": str(mid),
        "spread": str(spread),
        "source": "dsrc_synthetic_fixture",
        "source_request_id": "synthetic_feature_compute_fast_path_dst_boundary_bbo",
        "data_version": DATASET_ID,
        "quality_flags": [],
        "session_label": STATIC_SESSION_LABEL,
        "spread_ticks": str(spread / Decimal("0.25")),
        "microprice": str(microprice),
    }


__all__ = [
    "DATASET_ID",
    "PARTITION_ID",
    "POST_DST_RTH_OPEN_TS",
    "PRE_DST_RTH_OPEN_TS",
    "RTH_OPEN_BAR_STARTS",
    "STATIC_SESSION_LABEL",
    "SUMMER_RTH_OPEN_TS",
    "VOLUME_WINDOW_LENGTH",
    "WINDOW_LENGTH",
    "dst_bbo_rows",
    "dst_cross_market_ohlcv_rows",
    "dst_ohlcv_rows",
    "dst_rth_open_event_timestamps",
]
