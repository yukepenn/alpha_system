from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest

from alpha_system.data.foundation.instruments import (
    ContractDetailsSnapshot,
    ContractDiscoveryRequest,
    FuturesContractRecord,
    IncludeExpiredSupportStatus,
    compute_contract_details_snapshot_hash,
    record_contract_discovery,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "data"
    / "synthetic_contract_details_es_h5.json"
)
RETRIEVED_AT = datetime(2026, 6, 3, tzinfo=UTC)


def _fixture_payload() -> dict[str, object]:
    return cast(dict[str, object], json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    assert isinstance(value, Mapping), f"{field_name} fixture section must be a mapping"
    return cast(Mapping[str, object], value)


def _contract_payload(**overrides: object) -> dict[str, object]:
    values = dict(_mapping(_fixture_payload()["contract_record"], "contract_record"))
    values.update(overrides)
    return values


def _snapshot_payload(**overrides: object) -> dict[str, object]:
    fixture = _fixture_payload()
    values = dict(_mapping(fixture["snapshot"], "snapshot"))
    values["normalized_fields"] = fixture["normalized_fields"]
    values.update(overrides)
    return values


def _snapshot() -> ContractDetailsSnapshot:
    values = _snapshot_payload()
    return ContractDetailsSnapshot.create(
        snapshot_id=cast(str, values["snapshot_id"]),
        contract_id=cast(str, values["contract_id"]),
        raw_details_ref=cast(str, values["raw_details_ref"]),
        normalized_fields=_mapping(values["normalized_fields"], "normalized_fields"),
        retrieved_at=RETRIEVED_AT,
        client_id=cast(int, values["client_id"]),
        source=cast(str, values["source"]),
    )


def test_futures_contract_record_reconciles_with_instrument_master() -> None:
    record = FuturesContractRecord.from_mapping(_contract_payload())

    assert record.contract_id == "fcr_es_2025_03"
    assert record.root_symbol == "ES"
    assert record.ib_symbol == "ES"
    assert record.trading_class == "ES"
    assert record.con_id == 123456789
    assert record.expiration == date(2025, 3, 21)
    assert record.multiplier == Decimal("50")
    assert record.exchange == "CME"
    assert record.currency == "USD"
    assert record.include_expired_support_status is IncludeExpiredSupportStatus.NOT_CHECKED


def test_futures_contract_record_defaults_include_expired_to_not_checked() -> None:
    values = _contract_payload()
    values.pop("include_expired_support_status")

    with pytest.raises(DataFoundationValidationError, match="missing required fields"):
        FuturesContractRecord.from_mapping(values)

    record = FuturesContractRecord(
        contract_id="fcr_es_h5",
        root_symbol="ES",
        contract_month="H5",
        ib_symbol="ES",
        trading_class="ES",
        con_id=None,
        last_trade_date_or_contract_month="202503",
        expiration=date(2025, 3, 21),
        multiplier=Decimal("50"),
        exchange="CME",
        currency="USD",
    )
    assert record.include_expired_support_status is IncludeExpiredSupportStatus.NOT_CHECKED


@pytest.mark.parametrize(
    ("field_name", "bad_value", "match"),
    [
        ("root_symbol", "YM", "instrument master"),
        ("multiplier", "51", "multiplier"),
        ("exchange", "CBOT", "exchange"),
        ("currency", "EUR", "currency"),
        ("con_id", 0, "con_id must be positive"),
        ("con_id", True, "con_id must be a positive integer"),
        (
            "include_expired_support_status",
            "assumed_supported",
            "include_expired_support_status",
        ),
    ],
)
def test_futures_contract_record_rejects_invalid_fields(
    field_name: str,
    bad_value: object,
    match: str,
) -> None:
    values = _contract_payload(**{field_name: bad_value})

    with pytest.raises(DataFoundationValidationError, match=match):
        FuturesContractRecord.from_mapping(values)


def test_contract_details_snapshot_hash_is_stable_and_content_addressed() -> None:
    first = _snapshot()
    second = ContractDetailsSnapshot.create(
        snapshot_id="cds_same_content_different_id",
        contract_id=first.contract_id,
        raw_details_ref=first.raw_details_ref,
        normalized_fields=first.normalized_fields,
        retrieved_at=first.retrieved_at,
        client_id=first.client_id,
        source=first.source,
    )

    assert first.hash == second.hash
    assert len(first.hash or "") == 64
    assert first.hash == compute_contract_details_snapshot_hash(
        contract_id=first.contract_id,
        raw_details_ref=first.raw_details_ref,
        normalized_fields=first.normalized_fields,
        retrieved_at=first.retrieved_at,
        client_id=first.client_id,
        source=first.source,
    )


def test_contract_details_snapshot_validates_persisted_hash() -> None:
    snapshot = _snapshot()
    persisted = dict(snapshot.to_mapping())

    assert ContractDetailsSnapshot.from_mapping(persisted).hash == snapshot.hash

    persisted["hash"] = "0" * 64
    with pytest.raises(DataFoundationValidationError, match="hash does not match"):
        ContractDetailsSnapshot.from_mapping(persisted)


def test_contract_details_snapshot_is_immutable_and_reference_only() -> None:
    snapshot = _snapshot()

    with pytest.raises(FrozenInstanceError):
        setattr(snapshot, "source", "dsrc_changed")
    with pytest.raises(TypeError):
        cast(dict[str, object], snapshot.normalized_fields)["conId"] = 1
    with pytest.raises(DataFoundationValidationError, match="client_id 101 is forbidden"):
        ContractDetailsSnapshot.create(
            snapshot_id="cds_bad_client",
            contract_id=snapshot.contract_id,
            raw_details_ref=snapshot.raw_details_ref,
            normalized_fields=snapshot.normalized_fields,
            retrieved_at=snapshot.retrieved_at,
            client_id=101,
            source=snapshot.source,
        )
    with pytest.raises(DataFoundationValidationError, match="must reference"):
        ContractDetailsSnapshot.create(
            snapshot_id="cds_embedded_payload",
            contract_id=snapshot.contract_id,
            raw_details_ref='{"conId": 123456789}',
            normalized_fields=snapshot.normalized_fields,
            retrieved_at=snapshot.retrieved_at,
            client_id=snapshot.client_id,
            source=snapshot.source,
        )


def test_contract_discovery_logs_include_expired_as_unknown_until_discovered() -> None:
    result = record_contract_discovery(
        {"root_symbol": "ES", "sec_type": "FUT", "include_expired": True},
        discovered_at=RETRIEVED_AT,
    )
    log_mapping = result.availability_log_entry.to_mapping()

    assert result.availability_log_entry.include_expired_support_status is (
        IncludeExpiredSupportStatus.UNKNOWN
    )
    assert log_mapping["include_expired_requested"] is True
    assert log_mapping["include_expired_support_status"] == "unknown"
    assert "history_depth" not in log_mapping
    assert "full_history" not in log_mapping


def test_contract_discovery_records_supported_only_with_evidence() -> None:
    request = ContractDiscoveryRequest(
        root_symbol="ES",
        sec_type="FUT",
        include_expired=True,
        client_id=201,
        source="dsrc_synthetic_contract_discovery",
    )
    contract_record = FuturesContractRecord.from_mapping(_contract_payload())
    snapshot = _snapshot()

    with pytest.raises(DataFoundationValidationError, match="requires evidence_ref"):
        record_contract_discovery(
            request,
            include_expired_support_status="supported",
            discovered_at=RETRIEVED_AT,
        )

    result = record_contract_discovery(
        request,
        include_expired_support_status="supported",
        discovered_at=RETRIEVED_AT,
        evidence_ref="fixture:tests/fixtures/data/synthetic_contract_details_es_h5.json",
        contract_record=contract_record,
        snapshot=snapshot,
    )

    assert result.contract_record is not None
    assert result.snapshot is snapshot
    assert result.contract_record.include_expired_support_status is (
        IncludeExpiredSupportStatus.SUPPORTED
    )
    assert result.availability_log_entry.evidence_ref is not None


@pytest.mark.parametrize(
    ("request_values", "kwargs", "match"),
    [
        ({"root_symbol": "ES", "sec_type": "CONTFUT"}, {}, "sec_type FUT"),
        ({"root_symbol": "YM", "sec_type": "FUT"}, {}, "instrument master"),
        ({"root_symbol": "ES", "sec_type": "FUT", "client_id": 102}, {}, "forbidden"),
        (
            {"root_symbol": "ES", "sec_type": "FUT", "include_expired": False},
            {"include_expired_support_status": "supported"},
            "requires include_expired=True",
        ),
    ],
)
def test_contract_discovery_rejects_invalid_or_assumed_availability(
    request_values: Mapping[str, object],
    kwargs: Mapping[str, object],
    match: str,
) -> None:
    with pytest.raises(DataFoundationValidationError, match=match):
        record_contract_discovery(request_values, discovered_at=RETRIEVED_AT, **kwargs)
