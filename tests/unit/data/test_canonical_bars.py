from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from alpha_system.data.foundation import (
    CANONICAL_BAR_RECORD_FIELDS,
    CANONICAL_BAR_TIMESTAMP_FIELDS,
    TIMESTAMP_SEMANTICS_POLICY_FIELDS,
    CanonicalBarRecord,
    TimestampSemanticsPolicy,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError


def _timestamps() -> dict[str, datetime]:
    start = datetime(2026, 6, 1, 14, 30, tzinfo=UTC)
    return {
        "bar_start_ts": start,
        "event_ts": start + timedelta(seconds=30),
        "bar_end_ts": start + timedelta(minutes=1),
        "available_ts": start + timedelta(minutes=1, seconds=5),
        "ingested_at": start + timedelta(minutes=2),
    }


def _bar_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "instrument_id": "inst_synth_es",
        "contract_id": "fut_es_202606",
        "series_id": "series_es_front_unadjusted",
        **_timestamps(),
        "open": "5000.25",
        "high": "5001.00",
        "low": "4999.75",
        "close": "5000.50",
        "volume": "100",
        "source": "dsrc_ibkr_historical",
        "source_request_id": "hrs_synthetic_canonical_bars",
        "data_version": "canonical-bars-v1",
        "quality_flags": (),
        "session_label": "ETH",
    }
    values.update(overrides)
    return values


def test_canonical_bar_exposes_required_fields_and_distinct_timestamp_keys() -> None:
    record = CanonicalBarRecord.from_mapping(_bar_values())
    mapping = record.to_mapping()

    assert {field.name for field in fields(CanonicalBarRecord)} == set(
        CANONICAL_BAR_RECORD_FIELDS
    )
    assert set(mapping) == set(CANONICAL_BAR_RECORD_FIELDS)
    assert all(field_name in mapping for field_name in CANONICAL_BAR_TIMESTAMP_FIELDS)
    assert len(CANONICAL_BAR_TIMESTAMP_FIELDS) == len(set(CANONICAL_BAR_TIMESTAMP_FIELDS))
    assert record.available_ts >= record.bar_end_ts
    assert record.open == Decimal("5000.25")
    assert record.quality_flags == ()
    assert record.session_label == "ETH"

    with pytest.raises(FrozenInstanceError):
        record.available_ts = record.bar_end_ts  # type: ignore[misc]


def test_canonical_bar_missing_available_ts_blocks_construction() -> None:
    values = _bar_values()
    del values["available_ts"]

    with pytest.raises(DataFoundationValidationError, match="available_ts"):
        CanonicalBarRecord.from_mapping(values)

    with pytest.raises(DataFoundationValidationError, match="available_ts"):
        CanonicalBarRecord.from_mapping(_bar_values(available_ts=None))


def test_canonical_bar_enforces_timestamp_ordering() -> None:
    times = _timestamps()

    with pytest.raises(DataFoundationValidationError, match="bar_end_ts"):
        CanonicalBarRecord.from_mapping(
            _bar_values(bar_end_ts=times["bar_start_ts"])
        )
    with pytest.raises(DataFoundationValidationError, match="available_ts"):
        CanonicalBarRecord.from_mapping(
            _bar_values(available_ts=times["bar_end_ts"] - timedelta(microseconds=1))
        )


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"open": "0"}, "open"),
        ({"high": "0"}, "high"),
        ({"low": "0"}, "low"),
        ({"close": "0"}, "close"),
        ({"open": "5002.00"}, "open"),
        ({"close": "4999.00"}, "close"),
        ({"high": "4999.00"}, "high"),
        ({"volume": "-1"}, "volume"),
    ],
)
def test_canonical_bar_enforces_ohlc_and_volume_rules(
    overrides: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(DataFoundationValidationError, match=match):
        CanonicalBarRecord.from_mapping(_bar_values(**overrides))


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"session_label": ""}, "session_label"),
        ({"session_label": "regular"}, "session model"),
        ({"quality_flags": None}, "quality_flags"),
        ({"quality_flags": "clean"}, "quality_flags"),
        ({"quality_flags": ("checked", "checked")}, "duplicate"),
    ],
)
def test_canonical_bar_requires_session_label_and_explicit_quality_flags(
    overrides: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(DataFoundationValidationError, match=match):
        CanonicalBarRecord.from_mapping(_bar_values(**overrides))


def test_canonical_bar_rejects_unsupported_provider_timestamp_field() -> None:
    with pytest.raises(DataFoundationValidationError, match="unsupported fields"):
        CanonicalBarRecord.from_mapping(
            _bar_values(provider_ts="2026-06-01 09:30:00 US/Central")
        )


def test_timestamp_semantics_policy_defines_v1_no_lookahead_rules() -> None:
    policy = TimestampSemanticsPolicy.v1_no_lookahead()
    mapping = policy.to_mapping()

    assert {field.name for field in fields(TimestampSemanticsPolicy)} == set(
        TIMESTAMP_SEMANTICS_POLICY_FIELDS
    )
    assert set(mapping) == set(TIMESTAMP_SEMANTICS_POLICY_FIELDS)
    assert "available_ts" in policy.available_ts_definition
    assert "historical API return time" in policy.available_ts_definition
    assert "separately from available_ts" in policy.ingested_at_definition
    assert any("missing" in rule and "available_ts" in rule for rule in policy.lookahead_rules)
    assert any("not research-ready" in rule for rule in policy.lookahead_rules)


def test_timestamp_semantics_policy_fails_closed_on_missing_or_bad_rules() -> None:
    values = dict(TimestampSemanticsPolicy.v1_no_lookahead().to_mapping())
    del values["lookahead_rules"]

    with pytest.raises(DataFoundationValidationError, match="lookahead_rules"):
        TimestampSemanticsPolicy.from_mapping(values)
    with pytest.raises(DataFoundationValidationError, match="lookahead_rules"):
        TimestampSemanticsPolicy.from_mapping(
            {
                **dict(TimestampSemanticsPolicy.v1_no_lookahead().to_mapping()),
                "lookahead_rules": (),
            }
        )
    with pytest.raises(DataFoundationValidationError, match="provider timestamps"):
        TimestampSemanticsPolicy.from_mapping(
            {
                **dict(TimestampSemanticsPolicy.v1_no_lookahead().to_mapping()),
                "event_ts_definition": "Provider timestamps are research-ready.",
            }
        )
