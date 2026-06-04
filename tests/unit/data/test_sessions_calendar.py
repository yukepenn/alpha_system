from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import date, timedelta
from pathlib import Path

import pytest

from alpha_system.data.foundation.instruments import load_futures_instrument_master_records
from alpha_system.data.foundation.sessions import (
    DEFAULT_SESSION_CALENDAR_CONFIG,
    REQUIRED_SESSION_TEMPLATE_FIELDS,
    REQUIRED_TRADING_CALENDAR_FIELDS,
    SESSION_TYPE_EARLY_CLOSE,
    SESSION_TYPE_ETH,
    SESSION_TYPE_HOLIDAY,
    SessionTemplate,
    TradingCalendarRecord,
    load_session_templates,
    load_trading_calendar_records,
    resolve_session_templates_for_instrument_master,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

FIXTURE_PATH = Path("tests/fixtures/data/synthetic_session_calendar.json")


def _payload() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _template_values(**overrides: object) -> dict[str, object]:
    payload = _payload()
    templates = payload["session_templates"]
    assert isinstance(templates, list)
    values = dict(templates[0])
    values.update(overrides)
    return values


def _record_values(calendar_id: str, **overrides: object) -> dict[str, object]:
    payload = _payload()
    records = payload["calendar_records"]
    assert isinstance(records, list)
    for record in records:
        assert isinstance(record, dict)
        if record["calendar_id"] == calendar_id:
            values = dict(record)
            values.update(overrides)
            return values
    raise AssertionError(f"missing fixture record {calendar_id}")


def test_session_template_loads_required_fields_and_is_immutable() -> None:
    template = load_session_templates(FIXTURE_PATH)[0]
    mapping = template.to_mapping()

    for field_name in REQUIRED_SESSION_TEMPLATE_FIELDS:
        assert field_name in mapping

    assert template.template_id == "session_cme_index_futures_eth"
    assert template.timezone == "America/Chicago"
    assert template.zone.key == "America/Chicago"
    assert template.rth_start.isoformat(timespec="minutes") == "08:30"
    assert template.rth_end.isoformat(timespec="minutes") == "15:00"
    assert template.eth_start.isoformat(timespec="minutes") == "17:00"
    assert template.eth_end.isoformat(timespec="minutes") == "16:00"
    assert template.maintenance_breaks[0].start.isoformat(timespec="minutes") == "16:00"
    assert template.maintenance_breaks[0].end.isoformat(timespec="minutes") == "17:00"

    with pytest.raises(FrozenInstanceError):
        template.timezone = "UTC"  # type: ignore[misc]


def test_session_template_resolves_instrument_master_session_template_ids() -> None:
    resolved_by_root = resolve_session_templates_for_instrument_master(
        session_calendar_path=DEFAULT_SESSION_CALENDAR_CONFIG
    )
    instrument_records = load_futures_instrument_master_records()

    assert set(resolved_by_root) == {record.root_symbol for record in instrument_records}
    for record in instrument_records:
        template = resolved_by_root[record.root_symbol]
        assert template.template_id == record.session_template_id
        assert template.timezone == record.timezone


@pytest.mark.parametrize("bad_timezone", ["", "local", "CST", "America/Not_A_Zone"])
def test_session_template_requires_explicit_valid_iana_timezone(
    bad_timezone: str,
) -> None:
    with pytest.raises(DataFoundationValidationError, match="timezone"):
        SessionTemplate.from_mapping(_template_values(timezone=bad_timezone))


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"rth_start": "15:00", "rth_end": "08:30"}, "rth_start"),
        ({"rth_start": "16:30", "rth_end": "17:00"}, "RTH window"),
        ({"eth_start": "17:00", "eth_end": "17:00"}, "eth_start"),
        (
            {"maintenance_breaks": [{"start": "17:00", "end": "16:00"}]},
            "maintenance_breaks",
        ),
        ({"source": "official_final_exchange_calendar"}, "exchange-final"),
    ],
)
def test_session_template_rejects_malformed_windows_and_finality_claims(
    overrides: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(DataFoundationValidationError, match=match):
        SessionTemplate.from_mapping(_template_values(**overrides))


def test_trading_calendar_fixture_covers_normal_dst_early_close_and_holiday() -> None:
    records = {
        record.calendar_id: record for record in load_trading_calendar_records(FIXTURE_PATH)
    }

    normal = records["synthetic_cme_index_eth"]
    assert normal.session_type == SESSION_TYPE_ETH
    assert normal.is_open_session is True
    assert normal.date == date(2026, 6, 1)
    assert normal.open_ts is not None
    assert normal.close_ts is not None
    assert normal.open_ts.tzinfo is not None
    assert normal.close_ts.tzinfo is not None
    assert normal.duration == timedelta(hours=23)
    assert normal.has_offset_transition is False

    dst = records["synthetic_cme_index_dst"]
    assert dst.has_offset_transition is True
    assert dst.open_ts is not None
    assert dst.close_ts is not None
    assert dst.open_ts.utcoffset() == timedelta(hours=-6)
    assert dst.close_ts.utcoffset() == timedelta(hours=-5)
    assert dst.duration == timedelta(hours=2)

    early_close = records["synthetic_cme_index_early_close"]
    assert early_close.session_type == SESSION_TYPE_EARLY_CLOSE
    assert early_close.is_early_close is True
    assert early_close.duration < normal.duration
    assert early_close.close_ts is not None
    assert early_close.close_ts.isoformat().endswith("-06:00")

    holiday = records["synthetic_cme_index_holiday"]
    assert holiday.session_type == SESSION_TYPE_HOLIDAY
    assert holiday.is_holiday is True
    assert holiday.is_open_session is False
    assert holiday.open_ts is None
    assert holiday.close_ts is None
    assert holiday.duration == timedelta(0)


def test_trading_calendar_record_exposes_required_fields() -> None:
    record = TradingCalendarRecord.from_mapping(
        _record_values("synthetic_cme_index_eth")
    )
    mapping = record.to_mapping()

    for field_name in REQUIRED_TRADING_CALENDAR_FIELDS:
        assert field_name in mapping


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"open_ts": "2026-06-01T17:00:00"}, "timezone-aware"),
        ({"close_ts": None}, "require open_ts and close_ts"),
        ({"close_ts": "2026-06-01T17:00:00-05:00"}, "close_ts"),
        (
            {
                "breaks": [
                    {
                        "start": "2026-06-02T12:10:00-05:00",
                        "end": "2026-06-02T12:00:00-05:00",
                    }
                ]
            },
            "breaks",
        ),
        (
            {
                "breaks": [
                    {
                        "start": "2026-06-02T16:30:00-05:00",
                        "end": "2026-06-02T16:45:00-05:00",
                    }
                ]
            },
            "within the open session",
        ),
        ({"instrument_root": "YM"}, "instrument master"),
        ({"is_early_close": True}, "EARLY_CLOSE"),
        ({"session_type": "HOLIDAY"}, "is_holiday true"),
    ],
)
def test_trading_calendar_record_rejects_malformed_open_sessions(
    overrides: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(DataFoundationValidationError, match=match):
        TradingCalendarRecord.from_mapping(
            _record_values("synthetic_cme_index_eth", **overrides)
        )


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"open_ts": "2026-12-25T00:00:00"}, "timezone-aware"),
        ({"open_ts": "2026-12-25T00:00:00-06:00"}, "provide both"),
        (
            {
                "open_ts": "2026-12-25T00:00:00-06:00",
                "close_ts": "2026-12-25T01:00:00-06:00",
            },
            "explicitly closed",
        ),
        (
            {
                "breaks": [
                    {
                        "start": "2026-12-25T00:00:00-06:00",
                        "end": "2026-12-25T00:01:00-06:00",
                    }
                ]
            },
            "holiday records must not include",
        ),
        ({"is_holiday": False}, "session_type HOLIDAY"),
    ],
)
def test_trading_calendar_record_rejects_malformed_holidays(
    overrides: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(DataFoundationValidationError, match=match):
        TradingCalendarRecord.from_mapping(
            _record_values("synthetic_cme_index_holiday", **overrides)
        )
