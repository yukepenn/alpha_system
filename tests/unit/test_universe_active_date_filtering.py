from __future__ import annotations

from datetime import datetime, timezone

from alpha_system.data.universe import UniverseSpec


def test_universe_filters_members_by_active_date_range() -> None:
    universe = UniverseSpec.from_mapping(_payload())

    assert universe.active_instrument_ids("2026-01-02") == ("EQ_US_SYNTH_A",)
    assert universe.active_instrument_ids("2026-01-03") == ("EQ_US_SYNTH_A", "EQ_US_SYNTH_B")
    assert universe.active_instrument_ids("2026-01-04") == ("EQ_US_SYNTH_B",)


def test_universe_active_at_uses_member_local_timezone() -> None:
    universe = UniverseSpec.from_mapping(_payload())

    assert tuple(
        member.instrument_id
        for member in universe.active_members_at(datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc))
    ) == ("EQ_US_SYNTH_A",)
    assert tuple(
        member.instrument_id
        for member in universe.active_members_at(datetime(2026, 1, 2, 16, 30, tzinfo=timezone.utc))
    ) == ("EQ_US_SYNTH_A", "EQ_US_SYNTH_B")


def _payload() -> dict[str, object]:
    return {
        "universe_id": "active_dates",
        "name": "Active Dates",
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
                "end_date": "2026-01-03",
                "data_version": "synthetic:bars:v1",
            },
            {
                "instrument_id": "EQ_US_SYNTH_B",
                "symbol": "SYN-B",
                "asset_class": "equity",
                "exchange": "XTKS",
                "currency": "JPY",
                "timezone": "Asia/Tokyo",
                "start_date": "2026-01-03",
                "end_date": None,
                "data_version": "synthetic:bars:v1",
            },
        ],
    }
