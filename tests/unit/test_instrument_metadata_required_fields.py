from __future__ import annotations

from decimal import Decimal

from alpha_system.core.instrument_master import (
    REQUIRED_INSTRUMENT_MASTER_FIELDS,
    InstrumentMasterRecord,
    instrument_master_field_coverage,
)


def test_instrument_master_record_preserves_required_metadata_fields() -> None:
    record = InstrumentMasterRecord.from_mapping(_instrument_payload())
    contract = record.to_contract()

    assert tuple(record.to_dict()) == REQUIRED_INSTRUMENT_MASTER_FIELDS
    assert contract.instrument_id == "EQ_US_SYNTH_A"
    assert contract.symbol == "SYN-A"
    assert contract.currency == "USD"
    assert contract.timezone == "America/New_York"
    assert contract.tick_size == Decimal("0.01")
    assert contract.lot_size == Decimal("1")
    assert contract.multiplier == Decimal("1")
    assert contract.corporate_action_policy.value == "point_in_time"
    assert instrument_master_field_coverage(record) == {
        field: True for field in REQUIRED_INSTRUMENT_MASTER_FIELDS
    }


def _instrument_payload() -> dict[str, object]:
    return {
        "instrument_id": "EQ_US_SYNTH_A",
        "symbol": "SYN-A",
        "asset_class": "equity",
        "exchange": "XNYS",
        "currency": "usd",
        "timezone": "America/New_York",
        "tick_size": "0.01",
        "lot_size": "1",
        "multiplier": "1",
        "start_date": "2026-01-01",
        "end_date": None,
        "corporate_action_policy": "point_in_time",
        "metadata": {"calendar_id": "XNYS_SYNTH"},
    }
