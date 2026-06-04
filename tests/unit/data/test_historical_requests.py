from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest

from alpha_system.data.foundation.requests import (
    HistoricalRequestLifecycleState,
    HistoricalRequestManifest,
    HistoricalRequestSpec,
    authorize_historical_request_transition,
    compute_historical_request_manifest_hash,
    plan_historical_request_transition,
    provider_pull_manifest_guard,
    require_validated_manifest_for_provider_pull,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError

START_TS = datetime(2025, 1, 2, 14, 30, tzinfo=UTC)
END_TS = datetime(2025, 1, 3, 22, 0, tzinfo=UTC)
CREATED_AT = datetime(2026, 6, 3, 21, 52, 49, tzinfo=UTC)
TEMPLATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "templates"
    / "data"
    / "synthetic_historical_request_manifest.json"
)


def _request_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "request_spec_id": "hrs_synthetic_es_h5_20250102_20250103",
        "source_id": "dsrc_ibkr_historical",
        "symbol_root": "ES",
        "contract_ref": "fcr_synthetic_es_h5",
        "sec_type": "FUT",
        "exchange": "CME",
        "currency": "USD",
        "bar_size": "1 min",
        "what_to_show": "TRADES",
        "use_rth": False,
        "duration": "2 D",
        "end_datetime_policy": "explicit_end_ts_required",
        "start_ts": START_TS.isoformat(),
        "end_ts": END_TS.isoformat(),
        "chunk_policy": {
            "planned_chunks": 2,
            "max_duration": "1 D",
            "policy": "synthetic_planning_only",
        },
        "client_id": 201,
    }
    values.update(overrides)
    return values


def _manifest_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "manifest_id": "hrm_synthetic_es_h5_manifest_v1",
        "batch_id": "batch_synthetic_es_h5_planning_only",
        "request_specs": [_request_values()],
        "chunk_count": 2,
        "expected_coverage": {
            "synthetic": True,
            "coverage_status": "planned_only_not_requested",
            "symbols": ["ES"],
            "start_ts": START_TS.isoformat(),
            "end_ts": END_TS.isoformat(),
            "real_coverage_claim": False,
            "authorization_claim": False,
        },
        "pacing_policy_id": "rpp_synthetic_planning_only",
        "data_root": "~/alpha_data/alpha_system",
        "created_by": "DATA-P07 synthetic template",
        "created_at": CREATED_AT.isoformat(),
    }
    values["manifest_hash"] = compute_historical_request_manifest_hash(
        manifest_id=values["manifest_id"],
        batch_id=values["batch_id"],
        request_specs=values["request_specs"],
        chunk_count=values["chunk_count"],
        expected_coverage=values["expected_coverage"],
        pacing_policy_id=values["pacing_policy_id"],
        data_root=values["data_root"],
        created_by=values["created_by"],
    )
    values.update(overrides)
    return values


def test_historical_request_spec_validates_required_fields_and_client_id_policy() -> None:
    spec = HistoricalRequestSpec.from_mapping(_request_values())

    assert spec.request_spec_id == "hrs_synthetic_es_h5_20250102_20250103"
    assert spec.source_id == "dsrc_ibkr_historical"
    assert spec.symbol_root == "ES"
    assert spec.sec_type == "FUT"
    assert spec.exchange == "CME"
    assert spec.currency == "USD"
    assert spec.what_to_show == "TRADES"
    assert spec.client_id == 201
    assert "executed" not in spec.to_mapping()

    with pytest.raises(DataFoundationValidationError, match="hard-blocked"):
        HistoricalRequestSpec.from_mapping(_request_values(client_id=101))
    with pytest.raises(DataFoundationValidationError, match="201-209"):
        HistoricalRequestSpec.from_mapping(_request_values(client_id=210))


def test_historical_request_spec_rejects_missing_time_order_and_empty_chunk_policy() -> None:
    missing = _request_values()
    missing.pop("contract_ref")
    with pytest.raises(DataFoundationValidationError, match="missing required fields"):
        HistoricalRequestSpec.from_mapping(missing)

    with pytest.raises(DataFoundationValidationError, match="end_ts"):
        HistoricalRequestSpec.from_mapping(_request_values(end_ts="2025-01-01T00:00:00+00:00"))
    with pytest.raises(DataFoundationValidationError, match="empty mapping"):
        HistoricalRequestSpec.from_mapping(_request_values(chunk_policy={}))
    with pytest.raises(DataFoundationValidationError, match="zero or negative"):
        HistoricalRequestSpec.from_mapping(_request_values(chunk_policy={"planned_chunks": 0}))


def test_manifest_hash_is_deterministic_and_excludes_created_at() -> None:
    manifest = HistoricalRequestManifest.from_mapping(_manifest_values())
    same_content_later = HistoricalRequestManifest.from_mapping(
        _manifest_values(created_at="2026-06-04T00:00:00+00:00")
    )

    assert manifest.manifest_hash == same_content_later.manifest_hash
    assert manifest.manifest_hash == compute_historical_request_manifest_hash(
        manifest_id=manifest.manifest_id,
        batch_id=manifest.batch_id,
        request_specs=manifest.request_specs,
        chunk_count=manifest.chunk_count,
        expected_coverage=manifest.expected_coverage,
        pacing_policy_id=manifest.pacing_policy_id,
        data_root=manifest.data_root,
        created_by=manifest.created_by,
    )

    persisted = dict(manifest.to_mapping())
    assert HistoricalRequestManifest.from_mapping(persisted).manifest_hash == (
        manifest.manifest_hash
    )

    persisted["expected_coverage"] = {
        "synthetic": True,
        "coverage_status": "changed_planned_only",
    }
    with pytest.raises(DataFoundationValidationError, match="manifest_hash does not match"):
        HistoricalRequestManifest.from_mapping(persisted)


def test_manifest_rejects_missing_invalid_data_root_and_bad_chunk_count() -> None:
    missing = _manifest_values()
    missing.pop("manifest_hash")
    with pytest.raises(DataFoundationValidationError, match="missing required fields"):
        HistoricalRequestManifest.from_mapping(missing)

    invalid_root = _manifest_values(data_root="data/raw")
    invalid_root["manifest_hash"] = "0" * 64
    with pytest.raises(DataFoundationValidationError, match="outside the repository"):
        HistoricalRequestManifest.from_mapping(invalid_root)

    with pytest.raises(DataFoundationValidationError, match="positive"):
        HistoricalRequestManifest.from_mapping(_manifest_values(chunk_count=0))


def test_lifecycle_guards_fail_closed_without_external_authorization() -> None:
    request = _request_values()
    manifest = HistoricalRequestManifest.from_mapping(_manifest_values())

    assert plan_historical_request_transition(request) is (
        HistoricalRequestLifecycleState.REQUEST_PLANNED
    )
    assert authorize_historical_request_transition(manifest) is (
        HistoricalRequestLifecycleState.REQUEST_AUTHORIZED
    )
    assert provider_pull_manifest_guard(manifest) is True
    assert provider_pull_manifest_guard(None) is False
    assert (
        provider_pull_manifest_guard(
            _manifest_values(request_specs=[_request_values(client_id=102)])
        )
        is False
    )

    with pytest.raises(DataFoundationValidationError, match="blocks provider pull"):
        require_validated_manifest_for_provider_pull(None)


def test_synthetic_template_manifest_is_labeled_and_validated() -> None:
    payload = cast(
        Mapping[str, object],
        json.loads(TEMPLATE_PATH.read_text(encoding="utf-8")),
    )
    expected_coverage = payload["expected_coverage"]

    assert isinstance(expected_coverage, Mapping)
    assert expected_coverage["synthetic"] is True
    assert expected_coverage["coverage_status"] == "planned_only_not_requested"
    assert expected_coverage["real_coverage_claim"] is False
    assert expected_coverage["authorization_claim"] is False

    manifest = HistoricalRequestManifest.from_mapping(payload)

    assert manifest.manifest_hash == payload["manifest_hash"]
    assert manifest.request_specs[0].source_id == "dsrc_ibkr_historical"
    assert provider_pull_manifest_guard(payload) is True
