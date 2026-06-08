"""Synthetic Session / Calendar / Roll pack fixture for fast-path parity tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from alpha_system.data.foundation.grid import (
    NO_TRADE_QUALITY_FLAG,
    PREVIOUS_CLOSE_FILL_METHOD,
    DenseGridBarRecord,
)

DATASET_ID = "dsv_fast_path_session_calendar_roll_pack_v1"
PARTITION_ID = "development_partition"
SYNTHETIC_NO_TRADE_INDEX = 3


def session_calendar_roll_pack_records() -> tuple[DenseGridBarRecord, ...]:
    """Return dense-grid rows that exercise the governed session family edges."""

    bar_starts = (
        ("2024-01-02T13:59:00+00:00", "ETH", "ESM4"),
        ("2024-01-02T14:29:00+00:00", "RTH", "ESM4"),
        ("2024-01-02T14:30:00+00:00", "RTH", "ESM4"),
        ("2024-01-02T14:31:00+00:00", "RTH", "ESM4"),
        ("2024-01-02T14:32:00+00:00", "RTH", "ESU4"),
        ("2024-01-02T20:59:00+00:00", "RTH", "ESU4"),
        ("2024-01-02T21:00:00+00:00", "ETH", "ESU4"),
        ("2024-01-02T21:01:00+00:00", "RTH", "ESU4"),
    )
    return tuple(
        _dense_row(
            index,
            _dt(bar_start),
            session_label,
            contract_id=contract_id,
            has_trade=index != SYNTHETIC_NO_TRADE_INDEX,
        )
        for index, (bar_start, session_label, contract_id) in enumerate(bar_starts)
    )


def session_calendar_roll_pack_rows() -> tuple[dict[str, Any], ...]:
    """Return the same fixture rows as frame-ready canonical mappings."""

    return tuple(dict(record.to_mapping()) for record in session_calendar_roll_pack_records())


def _dense_row(
    index: int,
    bar_start_ts: datetime,
    session_label: str,
    *,
    contract_id: str,
    has_trade: bool,
) -> DenseGridBarRecord:
    price = Decimal("100")
    return DenseGridBarRecord(
        instrument_id="ES",
        contract_id=contract_id,
        series_id="ES_c_0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=bar_start_ts + timedelta(minutes=1, seconds=1),
        ingested_at=bar_start_ts + timedelta(minutes=1, seconds=2),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=Decimal("10") if has_trade else Decimal("0"),
        source="dsrc_synthetic",
        source_request_id=f"req_synthetic_session_{index}",
        data_version=DATASET_ID,
        quality_flags=() if has_trade else (NO_TRADE_QUALITY_FLAG,),
        session_label=session_label,
        has_trade=has_trade,
        synthetic=not has_trade,
        fill_method=None if has_trade else PREVIOUS_CLOSE_FILL_METHOD,
        provider_bar_ref=f"provider_bar_{index}" if has_trade else None,
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


__all__ = [
    "DATASET_ID",
    "PARTITION_ID",
    "SYNTHETIC_NO_TRADE_INDEX",
    "session_calendar_roll_pack_records",
    "session_calendar_roll_pack_rows",
]
