from __future__ import annotations

import json
from decimal import Decimal

import pytest

from alpha_system.data.foundation.instruments import (
    DEFAULT_FUTURES_INSTRUMENT_MASTER_CONFIG,
    INSTRUMENT_MASTER_ANCHOR_STATUS,
    INSTRUMENT_MASTER_CERTIFICATION_STATUS,
    INSTRUMENT_MASTER_SOURCE_ID,
    REQUIRED_INSTRUMENT_MASTER_FIELDS,
    InstrumentMasterRecord,
    load_futures_instrument_master_by_root,
    load_futures_instrument_master_records,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError


EXPECTED_ECONOMICS = {
    "ES": (Decimal("50"), Decimal("0.25"), Decimal("12.50")),
    "NQ": (Decimal("20"), Decimal("0.25"), Decimal("5.00")),
    "RTY": (Decimal("50"), Decimal("0.10"), Decimal("5.00")),
    "MES": (Decimal("5"), Decimal("0.25"), Decimal("1.25")),
    "MNQ": (Decimal("2"), Decimal("0.25"), Decimal("0.50")),
    "M2K": (Decimal("5"), Decimal("0.10"), Decimal("0.50")),
}


def _valid_record_mapping() -> dict[str, object]:
    records_by_root = load_futures_instrument_master_by_root()
    return dict(records_by_root["ES"].to_mapping())


def test_futures_instrument_master_loads_six_expected_roots() -> None:
    records = load_futures_instrument_master_records()
    records_by_root = load_futures_instrument_master_by_root()

    assert len(records) == 6
    assert set(records_by_root) == set(EXPECTED_ECONOMICS)

    for record in records:
        assert record.source == INSTRUMENT_MASTER_SOURCE_ID
        assert record.source_retrieved_at.tzinfo is not None
        assert record.timezone == "America/Chicago"
        assert record.sec_type == "FUT"
        assert not hasattr(record, "trading_class")
        assert not hasattr(record, "con_id")


@pytest.mark.parametrize("root_symbol", sorted(EXPECTED_ECONOMICS))
def test_each_root_has_exact_tick_value_consistency(root_symbol: str) -> None:
    records_by_root = load_futures_instrument_master_by_root()
    record = records_by_root[root_symbol]
    expected_point_value, expected_tick_size, expected_tick_value = EXPECTED_ECONOMICS[
        root_symbol
    ]

    assert record.point_value == expected_point_value
    assert record.tick_size == expected_tick_size
    assert record.tick_value == expected_tick_value
    assert record.computed_tick_value == expected_tick_value
    assert record.tick_value == record.tick_size * record.point_value
    assert record.multiplier == expected_point_value


def test_instrument_master_record_exposes_all_required_fields() -> None:
    record = load_futures_instrument_master_by_root()["ES"]
    mapping = record.to_mapping()

    for field_name in REQUIRED_INSTRUMENT_MASTER_FIELDS:
        assert field_name in mapping


def test_instrument_master_rejects_missing_required_fields() -> None:
    values = _valid_record_mapping()
    values.pop("tick_value")

    with pytest.raises(DataFoundationValidationError, match="missing required fields"):
        InstrumentMasterRecord.from_mapping(values)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "match"),
    [
        ("point_value", "0", "point_value must be positive"),
        ("tick_size", "-0.25", "tick_size must be positive"),
        ("tick_value", "12.49", "tick_value must equal"),
        ("timezone", "", "timezone must be a non-empty string"),
        ("timezone", "local", "explicit IANA"),
        ("timezone", "CST", "explicit IANA"),
        ("source", "campaign_goal", "dsrc_"),
        ("source_retrieved_at", "2026-06-03T00:00:00", "timezone-aware"),
    ],
)
def test_instrument_master_rejects_invalid_required_fields(
    field_name: str,
    bad_value: object,
    match: str,
) -> None:
    values = _valid_record_mapping()
    values[field_name] = bad_value

    with pytest.raises(DataFoundationValidationError, match=match):
        InstrumentMasterRecord.from_mapping(values)


def test_instrument_master_config_requires_to_be_verified_posture(tmp_path) -> None:
    payload = json.loads(
        DEFAULT_FUTURES_INSTRUMENT_MASTER_CONFIG.read_text(encoding="utf-8")
    )
    assert payload["anchor_status"] == INSTRUMENT_MASTER_ANCHOR_STATUS
    assert payload["certification_status"] == INSTRUMENT_MASTER_CERTIFICATION_STATUS

    payload["anchor_status"] = "production_certified"
    bad_config = tmp_path / "instrument_master_bad_posture.json"
    bad_config.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(DataFoundationValidationError, match="to-be-verified"):
        load_futures_instrument_master_records(bad_config)
