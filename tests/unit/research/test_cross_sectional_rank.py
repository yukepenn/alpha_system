from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from alpha_system.data.universe import (
    MISALIGNED_TIMESTAMP_FLAG,
    UNAVAILABLE_DATA_FLAG,
    UniverseSpec,
)
from alpha_system.research.cross_sectional import point_in_time_cross_sectional_rank


def test_cross_sectional_rank_uses_point_in_time_active_membership() -> None:
    decision_ts = datetime(2026, 1, 2, 15, 0, tzinfo=timezone.utc)
    universe = UniverseSpec.from_mapping(_payload())
    result = point_in_time_cross_sectional_rank(
        (
            _row("EQ_US_SYNTH_A", decision_ts, Decimal("0.2")),
            _row("EQ_US_SYNTH_B", decision_ts, Decimal("0.1")),
            _row("EQ_US_FUTURE_MEMBER", decision_ts, Decimal("9.9")),
        ),
        universe,
        decision_ts=decision_ts,
    )

    assert result.ranked_instrument_ids == ("EQ_US_SYNTH_A", "EQ_US_SYNTH_B")
    assert [rank.rank for rank in result.ranks] == [1, 2]
    assert "EQ_US_FUTURE_MEMBER" in result.missing_data_flags


def test_cross_sectional_rank_flags_unavailable_and_misaligned_rows() -> None:
    decision_ts = datetime(2026, 1, 2, 15, 0, tzinfo=timezone.utc)
    universe = UniverseSpec.from_mapping(_payload())
    result = point_in_time_cross_sectional_rank(
        (
            _row("EQ_US_SYNTH_A", decision_ts, Decimal("0.2"), available_ts=decision_ts + timedelta(seconds=1)),
            _row("EQ_US_SYNTH_B", decision_ts - timedelta(minutes=1), Decimal("0.1")),
        ),
        universe,
        decision_ts=decision_ts,
    )

    assert result.ranks == ()
    assert result.missing_data_flags["EQ_US_SYNTH_A"] == (UNAVAILABLE_DATA_FLAG,)
    assert result.missing_data_flags["EQ_US_SYNTH_B"] == (MISALIGNED_TIMESTAMP_FLAG,)


def _row(
    instrument_id: str,
    event_ts: datetime,
    value: Decimal,
    *,
    available_ts: datetime | None = None,
) -> dict[str, object]:
    return {
        "instrument_id": instrument_id,
        "event_ts": event_ts,
        "available_ts": available_ts or event_ts,
        "value": value,
    }


def _payload() -> dict[str, object]:
    return {
        "universe_id": "cross_sectional",
        "name": "Cross Sectional",
        "data_version": "synthetic:universe:v1",
        "instruments": [
            {
                "instrument_id": "EQ_US_SYNTH_A",
                "symbol": "SYN-A",
                "asset_class": "equity",
                "exchange": "XNYS",
                "currency": "USD",
                "timezone": "America/New_York",
                "start_date": "2026-01-01",
                "end_date": None,
                "data_version": "synthetic:bars:v1",
            },
            {
                "instrument_id": "EQ_US_SYNTH_B",
                "symbol": "SYN-B",
                "asset_class": "equity",
                "exchange": "XNYS",
                "currency": "USD",
                "timezone": "America/New_York",
                "start_date": "2026-01-01",
                "end_date": None,
                "data_version": "synthetic:bars:v1",
            },
            {
                "instrument_id": "EQ_US_FUTURE_MEMBER",
                "symbol": "SYN-F",
                "asset_class": "equity",
                "exchange": "XNYS",
                "currency": "USD",
                "timezone": "America/New_York",
                "start_date": "2026-01-03",
                "end_date": None,
                "data_version": "synthetic:bars:v1",
            },
        ],
    }
