from __future__ import annotations

import pytest

from alpha_system.core.instrument_master import (
    InstrumentMasterCatalog,
    InstrumentMasterError,
    InstrumentMasterRecord,
)


def test_instrument_master_active_dates_are_inclusive() -> None:
    record = InstrumentMasterRecord.from_mapping(
        {
            **_instrument_payload(),
            "start_date": "2026-01-02",
            "end_date": "2026-01-03",
        }
    )

    assert record.active_on("2026-01-01") is False
    assert record.active_on("2026-01-02") is True
    assert record.active_on("2026-01-03") is True
    assert record.active_on("2026-01-04") is False


def test_catalog_resolves_symbol_only_when_unambiguous() -> None:
    catalog = InstrumentMasterCatalog.from_mappings(
        (
            _instrument_payload("EQ_US_SYNTH_A", "SYN", "XNYS", "USD"),
            _instrument_payload("EQ_CA_SYNTH_A", "SYN", "XTSE", "CAD"),
        )
    )

    assert catalog.resolve_symbol("SYN", exchange="XNYS", currency="USD") == "EQ_US_SYNTH_A"

    with pytest.raises(InstrumentMasterError, match="ambiguous"):
        catalog.resolve_symbol("SYN")


def _instrument_payload(
    instrument_id: str = "EQ_US_SYNTH_A",
    symbol: str = "SYN-A",
    exchange: str = "XNYS",
    currency: str = "USD",
) -> dict[str, object]:
    return {
        "instrument_id": instrument_id,
        "symbol": symbol,
        "asset_class": "equity",
        "exchange": exchange,
        "currency": currency,
        "timezone": "America/New_York",
        "tick_size": "0.01",
        "lot_size": "1",
        "multiplier": "1",
        "start_date": "2026-01-01",
        "end_date": None,
        "corporate_action_policy": "point_in_time",
        "metadata": {},
    }
