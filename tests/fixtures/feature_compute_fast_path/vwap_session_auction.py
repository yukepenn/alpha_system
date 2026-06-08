"""Synthetic VWAP / session-auction pack fixture for fast-path parity tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from alpha_system.features.input_views import OHLCVInputRow

DATASET_ID = "dsv_fast_path_vwap_session_auction_pack_v1"
PARTITION_ID = "development_partition"
LEADING_NO_TRADE_INDEX = 0
FIRST_RTH_NO_TRADE_INDEX = 4
RTH_ZERO_VOLUME_INDEX = 6
NEXT_RTH_OPEN_INDEX = 10
ZERO_VWAP_INDEX = 11


def vwap_session_auction_input_rows() -> tuple[OHLCVInputRow, ...]:
    """Return tiny deterministic rows that exercise VWAP/session-auction gaps."""

    return (
        _row(
            0,
            "2024-01-02T13:57:00+00:00",
            "HALT",
            open_="100",
            high="100",
            low="100",
            close="100",
            volume="0",
            quality_flags=("no_trade",),
        ),
        _row(
            1,
            "2024-01-02T13:58:00+00:00",
            "ETH",
            open_="100",
            high="100",
            low="100",
            close="100",
            volume="0",
            quality_flags=("no_trade",),
        ),
        _row(
            2,
            "2024-01-02T13:59:00+00:00",
            "ETH",
            open_="100",
            high="101",
            low="99",
            close="100",
            volume="10",
        ),
        _row(
            3,
            "2024-01-02T14:00:00+00:00",
            "ETH",
            open_="100",
            high="102",
            low="98",
            close="100",
            volume="0",
        ),
        _row(
            FIRST_RTH_NO_TRADE_INDEX,
            "2024-01-02T14:30:00+00:00",
            "RTH",
            open_="101",
            high="101",
            low="101",
            close="101",
            volume="0",
            quality_flags=("no_trade",),
        ),
        _row(
            5,
            "2024-01-02T14:31:00+00:00",
            "RTH",
            open_="101",
            high="103",
            low="100",
            close="102",
            volume="100",
        ),
        _row(
            RTH_ZERO_VOLUME_INDEX,
            "2024-01-02T14:32:00+00:00",
            "RTH",
            open_="101",
            high="104",
            low="99",
            close="101",
            volume="0",
        ),
        _row(
            7,
            "2024-01-02T14:33:00+00:00",
            "RTH",
            open_="104",
            high="105",
            low="101",
            close="104",
            volume="200",
        ),
        _row(
            8,
            "2024-01-02T15:00:00+00:00",
            "ETH",
            open_="104",
            high="104",
            low="104",
            close="104",
            volume="0",
            quality_flags=("no_trade",),
        ),
        _row(
            9,
            "2024-01-02T15:01:00+00:00",
            "ETH",
            open_="105",
            high="106",
            low="103",
            close="105",
            volume="50",
        ),
        _row(
            NEXT_RTH_OPEN_INDEX,
            "2024-01-03T14:30:00+00:00",
            "RTH",
            open_="106",
            high="108",
            low="104",
            close="106",
            volume="150",
        ),
        _row(
            ZERO_VWAP_INDEX,
            "2024-01-03T16:00:00+00:00",
            "RTH",
            open_="0",
            high="0",
            low="0",
            close="0",
            volume="10",
            series_id="ZERO_VWAP_SERIES",
        ),
    )


def vwap_session_auction_frame_rows() -> tuple[dict[str, Any], ...]:
    """Return the same rows as frame-ready canonical-style mappings."""

    return tuple(
        _mapping(row, index) for index, row in enumerate(vwap_session_auction_input_rows())
    )


def _row(
    index: int,
    bar_start_ts: str,
    session_label: str,
    *,
    open_: str,
    high: str,
    low: str,
    close: str,
    volume: str,
    quality_flags: tuple[str, ...] = (),
    series_id: str = "ES_CONTINUOUS",
) -> OHLCVInputRow:
    start = datetime.fromisoformat(bar_start_ts).astimezone(UTC)
    return OHLCVInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id=series_id,
        bar_start_ts=start,
        bar_end_ts=start + timedelta(minutes=1),
        event_ts=start + timedelta(minutes=1),
        available_ts=start + timedelta(minutes=1, seconds=1),
        ingested_at=start + timedelta(minutes=1, seconds=2),
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal(volume),
        data_version=DATASET_ID,
        quality_flags=quality_flags,
        session_label=session_label,
    )


def _mapping(row: OHLCVInputRow, index: int) -> dict[str, Any]:
    return {
        "instrument_id": row.instrument_id,
        "contract_id": row.contract_id,
        "series_id": row.series_id,
        "bar_start_ts": row.bar_start_ts.isoformat(),
        "bar_end_ts": row.bar_end_ts.isoformat(),
        "event_ts": row.event_ts.isoformat(),
        "available_ts": row.available_ts.isoformat(),
        "ingested_at": row.ingested_at.isoformat(),
        "open": str(row.open),
        "high": str(row.high),
        "low": str(row.low),
        "close": str(row.close),
        "volume": str(row.volume),
        "source": "dsrc_synthetic_fixture",
        "source_request_id": f"synthetic_feature_compute_fast_path_vwap_session_{index}",
        "data_version": row.data_version,
        "quality_flags": list(row.quality_flags),
        "session_label": row.session_label,
    }


__all__ = [
    "DATASET_ID",
    "FIRST_RTH_NO_TRADE_INDEX",
    "LEADING_NO_TRADE_INDEX",
    "NEXT_RTH_OPEN_INDEX",
    "PARTITION_ID",
    "RTH_ZERO_VOLUME_INDEX",
    "ZERO_VWAP_INDEX",
    "vwap_session_auction_frame_rows",
    "vwap_session_auction_input_rows",
]
