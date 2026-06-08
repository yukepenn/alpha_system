"""Synthetic Cross-Market pack fixture for fast-path parity tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from alpha_system.features.families.cross_market import CrossMarketInputBundle
from alpha_system.features.input_views import (
    BBOInputRow,
    BBOInputView,
    OHLCVInputRow,
    OHLCVInputView,
)

DATASET_ID = "dsv_fast_path_cross_market_panel_v1"
PARTITION_ID = "development_partition"
WINDOW_LENGTH = 3
DELAYED_NQ_EVENT_INDEX = 1
NO_TRADE_INDEX = 4
SESSION_RESET_INDEX = 6
MISSING_RTY_EVENT_INDEX = 10


def cross_market_combined_rows() -> tuple[dict[str, Any], ...]:
    """Return OHLCV rows plus optional exact-time BBO rows for the fast pack."""

    rows = list(cross_market_ohlcv_rows())
    rows.extend(cross_market_bbo_rows())
    return tuple(rows)


def cross_market_ohlcv_rows() -> tuple[dict[str, Any], ...]:
    """Return a deterministic ES/NQ/RTY OHLCV fixture with one missing RTY event."""

    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    specs = {
        "ES": (
            ("RTH", "100", ()),
            ("RTH", "102", ()),
            ("RTH", "104.04", ()),
            ("RTH", "106.1208", ()),
            ("RTH", "106.1208", ("no_trade",)),
            ("RTH", "108", ()),
            ("ETH", "100", ()),
            ("ETH", "101", ()),
            ("ETH", "103.02", ()),
            ("ETH", "106.1106", ()),
            ("ETH", "107", ()),
        ),
        "NQ": (
            ("RTH", "200", ()),
            ("RTH", "204", ()),
            ("RTH", "210.12", ()),
            ("RTH", "214.3224", ()),
            ("RTH", "218", ()),
            ("RTH", "222", ()),
            ("ETH", "100", ()),
            ("ETH", "102", ()),
            ("ETH", "104.04", ()),
            ("ETH", "106.1208", ()),
            ("ETH", "109", ()),
        ),
        "RTY": (
            ("RTH", "50", ()),
            ("RTH", "51", ()),
            ("RTH", "52.02", ()),
            ("RTH", "53.0604", ()),
            ("RTH", "54", ()),
            ("RTH", "55", ()),
            ("ETH", "200", ()),
            ("ETH", "204", ()),
            ("ETH", "208.08", ()),
            ("ETH", "212.2416", ()),
        ),
    }
    rows: list[dict[str, Any]] = []
    for market, market_specs in specs.items():
        for index, (session, close, quality_flags) in enumerate(market_specs):
            bar_start = start + timedelta(minutes=index)
            available_ts = _available_ts(index, market, bar_start)
            rows.append(
                _ohlcv_mapping(
                    market,
                    bar_start,
                    close=close,
                    available_ts=available_ts,
                    session_label=session,
                    quality_flags=quality_flags,
                )
            )
    return tuple(rows)


def cross_market_bbo_rows() -> tuple[dict[str, Any], ...]:
    """Return one exact-time NQ missing-BBO row at the delayed output timestamp."""

    event_ts = _event_ts(DELAYED_NQ_EVENT_INDEX)
    available_ts = event_ts + timedelta(seconds=20)
    return (
        _bbo_mapping("NQ", event_ts, available_ts, quality_flags=("missing_bbo",)),
    )


def cross_market_input_bundle() -> CrossMarketInputBundle:
    """Return the reference-engine input bundle for the fixture."""

    ohlcv_rows: dict[str, list[OHLCVInputRow]] = {market: [] for market in ("ES", "NQ", "RTY")}
    for row in cross_market_ohlcv_rows():
        market = str(row["instrument_id"])
        ohlcv_rows[market].append(_ohlcv_input_row(row))
    bbo_rows: dict[str, list[BBOInputRow]] = {market: [] for market in ("ES", "NQ", "RTY")}
    for row in cross_market_bbo_rows():
        market = str(row["instrument_id"])
        bbo_rows[market].append(_bbo_input_row(row))
    return CrossMarketInputBundle(
        {market: OHLCVInputView(tuple(rows)) for market, rows in ohlcv_rows.items()},
        {
            market: BBOInputView(tuple(rows))
            for market, rows in bbo_rows.items()
            if rows
        },
    )


def delayed_nq_available_ts() -> datetime:
    """Return the expected strict-intersection max availability timestamp."""

    return _event_ts(DELAYED_NQ_EVENT_INDEX) + timedelta(seconds=20)


def missing_rty_event_ts() -> datetime:
    """Return the event timestamp intentionally omitted from RTY."""

    return _event_ts(MISSING_RTY_EVENT_INDEX)


def no_trade_event_ts() -> datetime:
    """Return the event timestamp carrying the ES no-trade gap."""

    return _event_ts(NO_TRADE_INDEX)


def session_reset_event_ts() -> datetime:
    """Return the first ETH event timestamp."""

    return _event_ts(SESSION_RESET_INDEX)


def _ohlcv_mapping(
    market: str,
    bar_start_ts: datetime,
    *,
    close: str,
    available_ts: datetime,
    session_label: str,
    quality_flags: tuple[str, ...],
) -> dict[str, Any]:
    bar_end = bar_start_ts + timedelta(minutes=1)
    return {
        "instrument_id": market,
        "contract_id": f"{market}M4",
        "series_id": f"{market}.c.0",
        "bar_start_ts": bar_start_ts.isoformat(),
        "bar_end_ts": bar_end.isoformat(),
        "event_ts": bar_end.isoformat(),
        "available_ts": available_ts.isoformat(),
        "ingested_at": (available_ts + timedelta(seconds=1)).isoformat(),
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": "0" if "no_trade" in quality_flags else "10",
        "source": "dsrc_synthetic_fixture",
        "source_request_id": "synthetic_feature_compute_fast_path_cross_market",
        "data_version": DATASET_ID,
        "quality_flags": list(quality_flags),
        "session_label": session_label,
        "bid": None,
        "ask": None,
        "bid_size": None,
        "ask_size": None,
        "mid": None,
        "spread": None,
    }


def _bbo_mapping(
    market: str,
    event_ts: datetime,
    available_ts: datetime,
    *,
    quality_flags: tuple[str, ...],
) -> dict[str, Any]:
    bid = Decimal("0") if quality_flags else Decimal("99")
    ask = Decimal("0") if quality_flags else Decimal("101")
    mid = (bid + ask) / Decimal("2")
    spread = ask - bid
    bar_start = event_ts - timedelta(minutes=1)
    return {
        "instrument_id": market,
        "contract_id": f"{market}M4",
        "series_id": f"{market}.c.0",
        "bar_start_ts": bar_start.isoformat(),
        "bar_end_ts": event_ts.isoformat(),
        "event_ts": event_ts.isoformat(),
        "available_ts": available_ts.isoformat(),
        "ingested_at": (available_ts + timedelta(seconds=1)).isoformat(),
        "open": None,
        "high": None,
        "low": None,
        "close": None,
        "volume": None,
        "source": "dsrc_synthetic_fixture",
        "source_request_id": "synthetic_feature_compute_fast_path_cross_market_bbo",
        "data_version": DATASET_ID,
        "quality_flags": list(quality_flags),
        "session_label": "RTH",
        "bid": str(bid),
        "ask": str(ask),
        "bid_size": "0" if quality_flags else "10",
        "ask_size": "0" if quality_flags else "10",
        "mid": str(mid),
        "spread": str(spread),
    }


def _ohlcv_input_row(row: dict[str, Any]) -> OHLCVInputRow:
    return OHLCVInputRow(
        instrument_id=str(row["instrument_id"]),
        contract_id=str(row["contract_id"]),
        series_id=str(row["series_id"]),
        bar_start_ts=_dt(str(row["bar_start_ts"])),
        bar_end_ts=_dt(str(row["bar_end_ts"])),
        event_ts=_dt(str(row["event_ts"])),
        available_ts=_dt(str(row["available_ts"])),
        ingested_at=_dt(str(row["ingested_at"])),
        open=Decimal(str(row["open"])),
        high=Decimal(str(row["high"])),
        low=Decimal(str(row["low"])),
        close=Decimal(str(row["close"])),
        volume=Decimal(str(row["volume"])),
        data_version=str(row["data_version"]),
        quality_flags=tuple(str(flag) for flag in row["quality_flags"]),
        session_label=str(row["session_label"]),
    )


def _bbo_input_row(row: dict[str, Any]) -> BBOInputRow:
    return BBOInputRow(
        instrument_id=str(row["instrument_id"]),
        contract_id=str(row["contract_id"]),
        series_id=str(row["series_id"]),
        bar_start_ts=_dt(str(row["bar_start_ts"])),
        bar_end_ts=_dt(str(row["bar_end_ts"])),
        event_ts=_dt(str(row["event_ts"])),
        available_ts=_dt(str(row["available_ts"])),
        ingested_at=_dt(str(row["ingested_at"])),
        bid=Decimal(str(row["bid"])),
        ask=Decimal(str(row["ask"])),
        bid_size=Decimal(str(row["bid_size"])),
        ask_size=Decimal(str(row["ask_size"])),
        mid=Decimal(str(row["mid"])),
        spread=Decimal(str(row["spread"])),
        data_version=str(row["data_version"]),
        quality_flags=tuple(str(flag) for flag in row["quality_flags"]),
        session_label=str(row["session_label"]),
    )


def _available_ts(index: int, market: str, bar_start_ts: datetime) -> datetime:
    event_ts = bar_start_ts + timedelta(minutes=1)
    if index == DELAYED_NQ_EVENT_INDEX and market == "NQ":
        return event_ts + timedelta(seconds=20)
    return event_ts + timedelta(seconds=1)


def _event_ts(index: int) -> datetime:
    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    return start + timedelta(minutes=index + 1)


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


__all__ = [
    "DATASET_ID",
    "DELAYED_NQ_EVENT_INDEX",
    "MISSING_RTY_EVENT_INDEX",
    "NO_TRADE_INDEX",
    "PARTITION_ID",
    "SESSION_RESET_INDEX",
    "WINDOW_LENGTH",
    "cross_market_bbo_rows",
    "cross_market_combined_rows",
    "cross_market_input_bundle",
    "cross_market_ohlcv_rows",
    "delayed_nq_available_ts",
    "missing_rty_event_ts",
    "no_trade_event_ts",
    "session_reset_event_ts",
]
