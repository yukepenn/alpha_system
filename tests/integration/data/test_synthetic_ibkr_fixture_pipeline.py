from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest

from alpha_system.core.hashing import hash_config
from alpha_system.data.foundation import (
    ContractDetailsSnapshot,
    ContractDiscoveryRequest,
    CoverageReport,
    DataQualityReport,
    DatasetVersion,
    FuturesContractRecord,
    HistoricalChunkRecord,
    HistoricalPullLedger,
    HistoricalRequestManifest,
    HistoricalRequestSpec,
    RawDataLakeLayoutPolicy,
    RawDataObject,
    RequestPacingPolicy,
    compute_quality_report_hash,
    parse_raw_bar_records,
    persist_dataset_version,
    require_pacing_policy_for_provider_pull,
    require_validated_manifest_for_provider_pull,
    resolve_dataset_version,
)
from alpha_system.data.foundation.bars import CanonicalBarRecord, ParsedBarRecord
from alpha_system.data.foundation.datasets import ReportStatus
from alpha_system.data.foundation.sources import (
    DEFAULT_ALLOWED_SUBDIRS,
    DEFAULT_FORBIDDEN_REPO_PATHS,
    DEFAULT_MAX_FILE_POLICY,
    DataFoundationValidationError,
    LocalDataRootPolicy,
)

ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "data" / ("synthetic_ibkr_e2e_provider_fixture.json")
POLICY_PATH = ROOT / "configs" / "data" / "request_pacing_policy_to_be_verified.json"
CREATED_AT = datetime(2026, 6, 4, 0, 0, tzinfo=UTC)
DATASET_VERSION_ID = "dsv_synthetic_ibkr_e2e_v1"


class SyntheticIBKRFixtureTransport:
    def __init__(self, historical_bars_csv: bytes) -> None:
        self.historical_bars_csv = historical_bars_csv
        self.synthetic_call_count = 0
        self.external_call_count = 0

    def historical_bars(self) -> bytes:
        self.synthetic_call_count += 1
        return self.historical_bars_csv

    def external_ibkr_call(self) -> bytes:
        self.external_call_count += 1
        raise AssertionError("external IBKR call attempted in synthetic fixture test")


def _fixture() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))


def _pacing_policy() -> RequestPacingPolicy:
    values = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    return RequestPacingPolicy.from_mapping(cast(Mapping[str, object], values))


def _data_root() -> Path:
    return Path.home() / "alpha_data" / "alpha_system_synthetic_ibkr_e2e"


def _layout() -> RawDataLakeLayoutPolicy:
    return RawDataLakeLayoutPolicy(
        local_data_root_policy=LocalDataRootPolicy(
            data_root=_data_root(),
            must_be_local=True,
            must_be_ignored=True,
            forbidden_repo_paths=DEFAULT_FORBIDDEN_REPO_PATHS,
            allowed_subdirs=DEFAULT_ALLOWED_SUBDIRS,
            max_file_policy=DEFAULT_MAX_FILE_POLICY,
        )
    )


def _request_spec() -> HistoricalRequestSpec:
    values = cast(Mapping[str, object], _fixture()["historical_request"])
    return HistoricalRequestSpec.from_mapping(values)


def _manifest(request_spec: HistoricalRequestSpec) -> HistoricalRequestManifest:
    fixture = _fixture()
    manifest_values = cast(Mapping[str, object], fixture["manifest"])
    return HistoricalRequestManifest.create(
        manifest_id=cast(str, manifest_values["manifest_id"]),
        batch_id=cast(str, manifest_values["batch_id"]),
        request_specs=(request_spec,),
        chunk_count=cast(int, manifest_values["chunk_count"]),
        expected_coverage=cast(Mapping[str, object], manifest_values["expected_coverage"]),
        pacing_policy_id=cast(str, manifest_values["pacing_policy_id"]),
        data_root=_data_root(),
        created_by=cast(str, manifest_values["created_by"]),
        created_at=CREATED_AT,
    )


def _historical_bars_payload() -> bytes:
    return cast(str, _fixture()["historical_bars_csv"]).encode("utf-8")


def _content_hash(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _pull_synthetic_payload(
    *,
    manifest: HistoricalRequestManifest,
    pacing_policy: RequestPacingPolicy,
    transport: SyntheticIBKRFixtureTransport,
) -> bytes:
    require_validated_manifest_for_provider_pull(manifest)
    require_pacing_policy_for_provider_pull(pacing_policy)
    return transport.historical_bars()


def _contract_details() -> tuple[
    ContractDiscoveryRequest, FuturesContractRecord, ContractDetailsSnapshot
]:
    fixture = _fixture()
    details = cast(Mapping[str, object], fixture["contract_details"])
    request = ContractDiscoveryRequest.from_mapping(cast(Mapping[str, object], details["request"]))
    contract = FuturesContractRecord.from_mapping(
        cast(Mapping[str, object], details["contract_record"])
    )
    snapshot_values = cast(Mapping[str, object], details["snapshot"])
    snapshot = ContractDetailsSnapshot.create(
        snapshot_id=cast(str, snapshot_values["snapshot_id"]),
        contract_id=cast(str, snapshot_values["contract_id"]),
        raw_details_ref=cast(str, snapshot_values["raw_details_ref"]),
        normalized_fields=cast(Mapping[str, object], details["normalized_fields"]),
        retrieved_at=datetime.fromisoformat(cast(str, snapshot_values["retrieved_at"])),
        client_id=cast(int, snapshot_values["client_id"]),
        source=cast(str, snapshot_values["source"]),
    )
    return request, contract, snapshot


def _raw_object(payload: bytes, request_spec: HistoricalRequestSpec) -> RawDataObject:
    raw = cast(Mapping[str, object], _fixture()["raw_object"])
    return RawDataObject.create(
        raw_object_id=cast(str, raw["raw_object_id"]),
        source=request_spec.source_id,
        request_id=cast(str, raw["request_id"]),
        chunk_id=cast(str, raw["chunk_id"]),
        content_hash=_content_hash(payload),
        schema_hint=cast(str, raw["schema_hint"]),
        retrieved_at=datetime.fromisoformat(cast(str, raw["retrieved_at"])),
        row_count=cast(int, raw["row_count"]),
        layout_policy=_layout(),
    )


def _canonical_bars(
    parsed_bars: tuple[ParsedBarRecord, ...],
    contract: FuturesContractRecord,
) -> tuple[CanonicalBarRecord, ...]:
    fixture = _fixture()
    timestamp_rows = cast(list[Mapping[str, object]], fixture["canonicalization_expectations"])
    records: list[CanonicalBarRecord] = []
    for parsed, timestamps in zip(parsed_bars, timestamp_rows, strict=True):
        records.append(
            CanonicalBarRecord.from_mapping(
                {
                    "instrument_id": "inst_synth_es",
                    "contract_id": contract.contract_id,
                    "series_id": "series_es_front_unadjusted",
                    "bar_start_ts": cast(str, timestamps["bar_start_ts"]),
                    "bar_end_ts": cast(str, timestamps["bar_end_ts"]),
                    "event_ts": cast(str, timestamps["event_ts"]),
                    "available_ts": cast(str, timestamps["available_ts"]),
                    "ingested_at": cast(str, timestamps["ingested_at"]),
                    "open": parsed.open,
                    "high": parsed.high,
                    "low": parsed.low,
                    "close": parsed.close,
                    "volume": parsed.volume,
                    "source": parsed.source,
                    "source_request_id": parsed.request_id,
                    "data_version": DATASET_VERSION_ID,
                    "quality_flags": (),
                    "session_label": "ETH",
                }
            )
        )
    return tuple(records)


def _expected_intervals() -> tuple[Mapping[str, object], ...]:
    fixture = _fixture()
    return tuple(cast(list[Mapping[str, object]], fixture["coverage_expected_intervals"]))


def _quality_report(
    bars: tuple[CanonicalBarRecord | Mapping[str, object], ...],
) -> DataQualityReport:
    return DataQualityReport.from_canonical_bars(
        quality_report_id="dqr_synthetic_ibkr_e2e",
        dataset_version_id=DATASET_VERSION_ID,
        bars=bars,
        expected_sessions=("ETH",),
    )


def _coverage_report(
    bars: tuple[CanonicalBarRecord | Mapping[str, object], ...],
) -> CoverageReport:
    return CoverageReport.from_canonical_bars(
        coverage_report_id="covr_synthetic_ibkr_e2e",
        dataset_version_id=DATASET_VERSION_ID,
        bars=bars,
        expected_intervals=_expected_intervals(),
    )


def _dataset_version(
    *,
    manifest: HistoricalRequestManifest,
    quality_report: DataQualityReport,
    canonical_bars: tuple[CanonicalBarRecord, ...],
    contract: FuturesContractRecord,
) -> DatasetVersion:
    code_hash = hash_config({"phase": "DATA-P21", "paths": ("src/alpha_system/data/foundation",)})
    config_hash = hash_config(
        {
            "fixture_id": _fixture()["fixture_id"],
            "bar_size": "1 min",
            "what_to_show": "TRADES",
        }
    )
    return DatasetVersion.from_mapping(
        {
            "dataset_version_id": DATASET_VERSION_ID,
            "source": "dsrc_ibkr_historical",
            "symbol_universe": ("ES",),
            "bar_size": "1 min",
            "what_to_show": "TRADES",
            "start_ts": canonical_bars[0].bar_start_ts.isoformat(),
            "end_ts": canonical_bars[-1].bar_end_ts.isoformat(),
            "contract_universe": (contract.contract_id,),
            "roll_policy_id": "roll_policy_volume_open_interest",
            "manifest_hash": manifest.manifest_hash,
            "code_hash": code_hash,
            "config_hash": config_hash,
            "quality_report_hash": compute_quality_report_hash(quality_report),
            "created_at": CREATED_AT.isoformat(),
        }
    )


def _complete_chunk(
    raw_object: RawDataObject,
    request_spec: HistoricalRequestSpec,
) -> HistoricalChunkRecord:
    return HistoricalChunkRecord.from_mapping(
        {
            "chunk_id": raw_object.chunk_id,
            "request_spec_id": request_spec.request_spec_id,
            "symbol_root": request_spec.symbol_root,
            "contract_ref": request_spec.contract_ref,
            "start_ts": request_spec.start_ts.isoformat(),
            "end_ts": request_spec.end_ts.isoformat(),
            "status": "COMPLETE",
            "attempt_count": 1,
            "provider_request_id": "ibkr_req_synthetic_e2e_001",
            "raw_object_ref": raw_object.raw_object_ref,
            "row_count": raw_object.row_count,
            "error_ref": None,
            "retrieved_at": raw_object.retrieved_at.isoformat(),
        }
    )


def test_synthetic_ibkr_fixture_pipeline_versions_without_external_call(
    tmp_path: Path,
) -> None:
    discovery_request, contract, snapshot = _contract_details()
    request_spec = _request_spec()
    manifest = _manifest(request_spec)
    pacing_policy = _pacing_policy()
    transport = SyntheticIBKRFixtureTransport(_historical_bars_payload())

    assert discovery_request.client_id == request_spec.client_id == snapshot.client_id
    assert contract.contract_id == request_spec.contract_ref
    assert snapshot.contract_id == contract.contract_id

    payload = _pull_synthetic_payload(
        manifest=manifest,
        pacing_policy=pacing_policy,
        transport=transport,
    )
    assert transport.synthetic_call_count == 1
    assert transport.external_call_count == 0

    raw_object = _raw_object(payload, request_spec)
    parsed_bars = parse_raw_bar_records(
        raw_object,
        layout_policy=_layout(),
        raw_payload_loader=lambda _: payload,
    )
    canonical_bars = _canonical_bars(parsed_bars, contract)

    assert len(parsed_bars) == len(canonical_bars) == 3
    for parsed, canonical in zip(parsed_bars, canonical_bars, strict=True):
        assert canonical.source_request_id == parsed.request_id
        assert canonical.source == parsed.source
        assert canonical.available_ts >= canonical.bar_end_ts
        assert (
            len(
                {
                    canonical.bar_start_ts,
                    canonical.bar_end_ts,
                    canonical.event_ts,
                    canonical.available_ts,
                    canonical.ingested_at,
                }
            )
            == 5
        )

    complete_chunk = _complete_chunk(raw_object, request_spec)
    ledger = HistoricalPullLedger.create(
        pull_id="hpl_synthetic_ibkr_e2e_complete",
        manifest_id=manifest.manifest_id,
        chunk_records=(complete_chunk,),
        expected_chunk_ids=(complete_chunk.chunk_id,),
        started_at=CREATED_AT,
        finished_at=CREATED_AT,
    )
    assert ledger.completed_chunk_ids() == (complete_chunk.chunk_id,)

    quality = _quality_report(canonical_bars)
    coverage = _coverage_report(canonical_bars)
    version = _dataset_version(
        manifest=manifest,
        quality_report=quality,
        canonical_bars=canonical_bars,
        contract=contract,
    )

    assert quality.status is ReportStatus.PASSING
    assert coverage.coverage_status is ReportStatus.PASSING
    assert not quality.blocks_versioning
    assert not coverage.blocks_versioning
    assert version.reproducibility_hashes["manifest_hash"] == manifest.manifest_hash

    version.require_versioned_prerequisites(
        quality_report=quality,
        coverage_report=coverage,
        source_manifest=manifest,
        code_hash=version.code_hash,
        config_hash=version.config_hash,
    )
    registry_path = tmp_path / "synthetic_ibkr_e2e_registry.sqlite"
    persist_dataset_version(
        registry_path,
        version,
        quality_report=quality,
        coverage_report=coverage,
        source_manifest=manifest,
        code_hash=version.code_hash,
        config_hash=version.config_hash,
    )
    assert resolve_dataset_version(registry_path, DATASET_VERSION_ID) == version


def test_synthetic_quality_coverage_defects_are_not_silent() -> None:
    _, contract, _ = _contract_details()
    request_spec = _request_spec()
    manifest = _manifest(request_spec)
    payload = _historical_bars_payload()
    raw_object = _raw_object(payload, request_spec)
    parsed_bars = parse_raw_bar_records(
        raw_object,
        layout_policy=_layout(),
        raw_payload_loader=lambda _: payload,
    )
    canonical_bars = _canonical_bars(parsed_bars, contract)
    clean_quality = _quality_report(canonical_bars)
    clean_coverage = _coverage_report(canonical_bars)
    version = _dataset_version(
        manifest=manifest,
        quality_report=clean_quality,
        canonical_bars=canonical_bars,
        contract=contract,
    )

    gap_quality = _quality_report((canonical_bars[0], canonical_bars[2]))
    duplicate_quality = _quality_report((canonical_bars[0], canonical_bars[0]))
    non_monotonic_quality = _quality_report((canonical_bars[1], canonical_bars[0]))
    zero_volume_bar = dict(canonical_bars[0].to_mapping())
    zero_volume_bar["volume"] = "0"
    zero_volume_quality = _quality_report((zero_volume_bar,))
    ohlc_bar = dict(canonical_bars[0].to_mapping())
    ohlc_bar["high"] = "4999.00"
    ohlc_quality = _quality_report((ohlc_bar,))
    coverage_gap = _coverage_report(canonical_bars[:2])

    assert gap_quality.status is ReportStatus.BLOCKING
    assert gap_quality.gap_summary["count"] == 1
    assert duplicate_quality.status is ReportStatus.BLOCKING
    assert duplicate_quality.duplicate_summary["count"] == 1
    assert non_monotonic_quality.status is ReportStatus.BLOCKING
    assert non_monotonic_quality.non_monotonic_summary["count"] == 1
    assert zero_volume_quality.status is ReportStatus.WARNING
    assert zero_volume_quality.zero_volume_anomalies["count"] == 1
    assert ohlc_quality.status is ReportStatus.BLOCKING
    assert ohlc_quality.ohlc_errors["count"] >= 1
    assert coverage_gap.coverage_status is ReportStatus.BLOCKING

    with pytest.raises(DataFoundationValidationError, match="blocking DataQualityReport"):
        version.require_versioned_prerequisites(
            quality_report=gap_quality,
            coverage_report=clean_coverage,
            source_manifest=manifest,
            code_hash=version.code_hash,
            config_hash=version.config_hash,
        )

    with pytest.raises(DataFoundationValidationError, match="blocking coverage report"):
        version.require_versioned_prerequisites(
            quality_report=clean_quality,
            coverage_report=coverage_gap,
            source_manifest=manifest,
            code_hash=version.code_hash,
            config_hash=version.config_hash,
        )
