from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from alpha_system.data.foundation import (
    PARSED_BAR_RECORD_FIELDS,
    ParsedBarRecord,
    RawDataLakeLayoutPolicy,
    RawDataObject,
    parse_raw_bar_records,
)
from alpha_system.data.foundation.sources import (
    DEFAULT_ALLOWED_SUBDIRS,
    DEFAULT_FORBIDDEN_REPO_PATHS,
    DEFAULT_MAX_FILE_POLICY,
    DataFoundationValidationError,
    LocalDataRootPolicy,
)

RETRIEVED_AT = datetime(2026, 6, 3, 21, 52, 49, tzinfo=UTC)
FIXTURE_PATH = (
    Path(__file__).resolve().parents[2] / "fixtures" / "data" / "synthetic_ibkr_raw_bars.csv"
)


def _outside_repo_root(name: str = "alpha_system_parsed_bar_unit_root") -> Path:
    return Path.home() / "alpha_data" / name


def _local_policy(root: Path | str | None = None) -> LocalDataRootPolicy:
    return LocalDataRootPolicy(
        data_root=root or _outside_repo_root(),
        must_be_local=True,
        must_be_ignored=True,
        forbidden_repo_paths=DEFAULT_FORBIDDEN_REPO_PATHS,
        allowed_subdirs=DEFAULT_ALLOWED_SUBDIRS,
        max_file_policy=DEFAULT_MAX_FILE_POLICY,
    )


def _layout(root_name: str = "alpha_system_parsed_bar_unit_root") -> RawDataLakeLayoutPolicy:
    return RawDataLakeLayoutPolicy(
        local_data_root_policy=_local_policy(_outside_repo_root(root_name))
    )


def _content_hash(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _fixture_payload() -> bytes:
    return FIXTURE_PATH.read_bytes()


def _raw_object(
    payload: bytes,
    *,
    row_count: int = 2,
    raw_object_id: str = "raw_synth_parsed_bars_a",
) -> RawDataObject:
    return RawDataObject.create(
        raw_object_id=raw_object_id,
        source="dsrc_ibkr_historical",
        request_id="hrs_synthetic_parsed_bars",
        chunk_id="hchunk_synthetic_parsed_bars_a",
        content_hash=_content_hash(payload),
        schema_hint="ibkr_historical_bars_raw_v1",
        retrieved_at=RETRIEVED_AT,
        row_count=row_count,
        layout_policy=_layout(raw_object_id),
    )


def _record_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "source": "dsrc_ibkr_historical",
        "symbol": "SYNTHES",
        "contract_ref": "synth-contract:ESH5",
        "provider_ts": "2025-01-02 08:30:00 US/Central",
        "open": "5000.25",
        "high": "5001.00",
        "low": "4999.75",
        "close": "5000.50",
        "volume": "100",
        "request_id": "hrs_synthetic_parsed_bars",
        "raw_object_id": "raw_synth_parsed_bars_a",
    }
    values.update(overrides)
    return values


def test_parsed_bar_record_validates_required_fields_and_optional_absent() -> None:
    record = ParsedBarRecord.from_mapping(_record_values())

    assert {field.name for field in fields(ParsedBarRecord)} == set(PARSED_BAR_RECORD_FIELDS)
    assert record.provider_ts == "2025-01-02 08:30:00 US/Central"
    assert record.open == Decimal("5000.25")
    assert record.wap_if_available is None
    assert record.bar_count_if_available is None
    assert set(record.to_mapping()) == set(PARSED_BAR_RECORD_FIELDS)

    missing = _record_values()
    del missing["provider_ts"]
    with pytest.raises(DataFoundationValidationError, match="missing required fields"):
        ParsedBarRecord.from_mapping(missing)

    with pytest.raises(DataFoundationValidationError, match="bar_count_if_available"):
        ParsedBarRecord.from_mapping(_record_values(bar_count_if_available="not-an-int"))
    with pytest.raises(FrozenInstanceError):
        record.provider_ts = "canonicalized"  # type: ignore[misc]


def test_parser_produces_provider_shaped_bars_with_raw_provenance() -> None:
    payload = _fixture_payload()
    raw_object = _raw_object(payload)

    records = parse_raw_bar_records(
        raw_object,
        raw_payload_loader=lambda _: payload,
    )

    assert len(records) == 2
    first = records[0]
    assert first.source == raw_object.source
    assert first.symbol == "SYNTHES"
    assert first.contract_ref == "synth-contract:ESH5"
    assert first.provider_ts == "2025-01-02 08:30:00 US/Central"
    assert first.wap_if_available == Decimal("5000.40")
    assert first.bar_count_if_available == 3
    assert first.request_id == raw_object.request_id
    assert first.raw_object_id == raw_object.raw_object_id


def test_parser_fails_closed_on_malformed_rows_and_row_count_mismatch() -> None:
    malformed = (
        b"symbol,contract_ref,provider_ts,open,high,low,close,volume,wap,barCount\n"
        b"SYNTHES,synth-contract:ESH5,2025-01-02 08:30:00 US/Central,"
        b"not-a-decimal,5001.00,4999.75,5000.50,100,5000.40,3\n"
    )
    raw_malformed = _raw_object(
        malformed,
        row_count=1,
        raw_object_id="raw_synth_parsed_bars_malformed",
    )

    with pytest.raises(DataFoundationValidationError, match="open"):
        parse_raw_bar_records(raw_malformed, raw_payload_loader=lambda _: malformed)

    payload = _fixture_payload()
    raw_wrong_count = _raw_object(
        payload,
        row_count=3,
        raw_object_id="raw_synth_parsed_bars_wrong_count",
    )
    with pytest.raises(DataFoundationValidationError, match="row_count=3"):
        parse_raw_bar_records(raw_wrong_count, raw_payload_loader=lambda _: payload)


def test_parsed_bar_record_has_no_canonical_timestamp_or_session_fields() -> None:
    forbidden = {
        "available_ts",
        "bar_end_ts",
        "bar_start_ts",
        "event_ts",
        "ingested_at",
        "session",
        "session_id",
        "session_label",
    }
    record_fields = {field.name for field in fields(ParsedBarRecord)}
    record = ParsedBarRecord.from_mapping(_record_values())

    assert forbidden.isdisjoint(record_fields)
    assert all(not hasattr(record, field_name) for field_name in forbidden)

    with pytest.raises(DataFoundationValidationError, match="canonical timestamp"):
        ParsedBarRecord.from_mapping(_record_values(event_ts="2025-01-02T14:31:00Z"))
