"""Synthetic end-to-end data-foundation dry run for DATA-P24.

The dry run composes existing data-foundation records over tiny hand-authored
fixtures only. It performs no IBKR call, opens no socket, writes no raw or
canonical data, and returns aggregate status only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType

from alpha_system.core.hashing import hash_config
from alpha_system.data.foundation.bars import (
    CanonicalBarRecord,
    RawDataLakeLayoutPolicy,
    RawDataObject,
    parse_raw_bar_records,
    require_raw_data_lake_layout_policy,
)
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetPartitionPlan,
    DatasetVersion,
    compute_quality_report_hash,
)
from alpha_system.data.foundation.ibkr import (
    IBKRClientIdPolicy,
    IBKRConnectionProfile,
    ReadOnlyBoundaryViolation,
    build_read_only_ibkr_boundary,
    run_connection_doctor,
)
from alpha_system.data.foundation.instruments import (
    ContractDetailsSnapshot,
    ContractDiscoveryRequest,
    FuturesContractRecord,
)
from alpha_system.data.foundation.requests import (
    HistoricalChunkRecord,
    HistoricalPullLedger,
    HistoricalRequestManifest,
    HistoricalRequestSpec,
    RequestPacingPolicy,
    forbid_naive_request_loop,
    require_pacing_policy_for_provider_pull,
    require_validated_manifest_for_provider_pull,
)
from alpha_system.data.foundation.sources import (
    DEFAULT_ALLOWED_SUBDIRS,
    DEFAULT_FORBIDDEN_REPO_PATHS,
    DEFAULT_MAX_FILE_POLICY,
    DataAccessMode,
    DataFoundationValidationError,
    DataSourceProfile,
    LocalDataRootPolicy,
    require_local_data_root_policy,
)
from alpha_system.data.foundation.version_registry import (
    persist_dataset_version,
    resolve_dataset_version,
)
from alpha_system.data.ibkr._json_utils import json_ready_base as _json_ready

DEFAULT_E2E_FIXTURE_RELATIVE_PATH = Path(
    "tests/fixtures/data/synthetic_ibkr_e2e_provider_fixture.json"
)
DEFAULT_PACING_POLICY_RELATIVE_PATH = Path("configs/data/request_pacing_policy_to_be_verified.json")
DATA_P24_DRY_RUN_DATASET_VERSION_ID = "dsv_data_p24_synthetic_e2e_v1"
DATA_P24_CREATED_AT = datetime(2026, 6, 4, 0, 0, tzinfo=UTC)
PROHIBITED_MVP_STATES: tuple[str, ...] = (
    "READY_FOR_TRADING",
    "LIVE_FEED_READY",
    "BROKER_ENABLED",
    "ALPHA_VALIDATED",
    "PROFITABLE",
)
_FORBIDDEN_BOUNDARY_METHODS: tuple[str, ...] = (
    "placeOrder",
    "reqPositions",
    "reqAccountUpdates",
    "reqAccountSummary",
    "reqOpenOrders",
    "reqExecutions",
)


@dataclass(frozen=True, slots=True)
class LifecycleBlockAssertion:
    """One fail-closed lifecycle assertion result."""

    block_id: str
    blocked: bool
    reason: str

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "block_id": self.block_id,
                "blocked": self.blocked,
                "reason": self.reason,
            }
        )


@dataclass(frozen=True, slots=True)
class EndToEndDryRunSummary:
    """Curated aggregate dry-run summary with no raw provider payload."""

    status: str
    fixture_id: str
    source_id: str
    access_mode: str
    allows_external_api: bool
    external_call_attempted: bool
    client_id: int
    manifest_id: str
    manifest_hash: str
    pacing_policy_id: str
    chunk_count: int
    completed_chunk_count: int
    pending_resume_chunk_count: int
    raw_object_count: int
    parsed_bar_count: int
    canonical_bar_count: int
    quality_status: str
    coverage_status: str
    dataset_version_id: str
    registry_round_trip: bool
    partition_ids: tuple[str, ...]
    lifecycle_blocks: tuple[LifecycleBlockAssertion, ...]
    read_only_boundary_confirmed: bool
    prohibited_states_unreachable: bool
    reproducibility_hashes: Mapping[str, str]

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "status": self.status,
                "fixture_id": self.fixture_id,
                "source_id": self.source_id,
                "access_mode": self.access_mode,
                "allows_external_api": self.allows_external_api,
                "external_call_attempted": self.external_call_attempted,
                "client_id": self.client_id,
                "manifest_id": self.manifest_id,
                "manifest_hash": self.manifest_hash,
                "pacing_policy_id": self.pacing_policy_id,
                "chunk_count": self.chunk_count,
                "completed_chunk_count": self.completed_chunk_count,
                "pending_resume_chunk_count": self.pending_resume_chunk_count,
                "raw_object_count": self.raw_object_count,
                "parsed_bar_count": self.parsed_bar_count,
                "canonical_bar_count": self.canonical_bar_count,
                "quality_status": self.quality_status,
                "coverage_status": self.coverage_status,
                "dataset_version_id": self.dataset_version_id,
                "registry_round_trip": self.registry_round_trip,
                "partition_ids": self.partition_ids,
                "lifecycle_blocks": tuple(
                    assertion.to_mapping() for assertion in self.lifecycle_blocks
                ),
                "read_only_boundary_confirmed": self.read_only_boundary_confirmed,
                "prohibited_states_unreachable": self.prohibited_states_unreachable,
                "reproducibility_hashes": self.reproducibility_hashes,
            }
        )


@dataclass(frozen=True, slots=True)
class _SyntheticTransport:
    historical_bars_csv: bytes
    synthetic_call_count: int = 0
    external_call_count: int = 0

    def historical_bars(self) -> tuple[bytes, _SyntheticTransport]:
        return (
            self.historical_bars_csv,
            _SyntheticTransport(
                historical_bars_csv=self.historical_bars_csv,
                synthetic_call_count=self.synthetic_call_count + 1,
                external_call_count=self.external_call_count,
            ),
        )

    def external_ibkr_call(self) -> tuple[bytes, _SyntheticTransport]:
        return (
            b"",
            _SyntheticTransport(
                historical_bars_csv=self.historical_bars_csv,
                synthetic_call_count=self.synthetic_call_count,
                external_call_count=self.external_call_count + 1,
            ),
        )


@dataclass(frozen=True, slots=True)
class _DryRunContext:
    fixture: Mapping[str, object]
    source_profile: DataSourceProfile
    connection_profile: IBKRConnectionProfile
    access_mode: DataAccessMode
    request_spec: HistoricalRequestSpec
    manifest: HistoricalRequestManifest
    pacing_policy: RequestPacingPolicy
    contract: FuturesContractRecord
    raw_object: RawDataObject
    canonical_bars: tuple[CanonicalBarRecord, ...]
    quality_report: DataQualityReport
    coverage_report: CoverageReport
    dataset_version: DatasetVersion
    ledger: HistoricalPullLedger
    partition_plan: DatasetPartitionPlan
    external_call_attempted: bool


def _repo_root() -> Path:
    return Path(__file__).resolve(strict=False).parents[4]


def _default_fixture_path() -> Path:
    return _repo_root() / DEFAULT_E2E_FIXTURE_RELATIVE_PATH


def _default_pacing_policy_path() -> Path:
    return _repo_root() / DEFAULT_PACING_POLICY_RELATIVE_PATH


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = f"{field_name} must be a JSON object"
        raise DataFoundationValidationError(msg)
    return value


def _load_json_mapping(path: Path) -> Mapping[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return _require_mapping(payload, path.as_posix())


def _parse_aware_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be an ISO-8601 timezone-aware datetime"
            raise DataFoundationValidationError(msg) from exc
    else:
        msg = f"{field_name} must be an ISO-8601 timezone-aware datetime"
        raise DataFoundationValidationError(msg)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return parsed


def _content_hash(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _synthetic_data_root() -> Path:
    return Path.home() / "alpha_data" / "alpha_system_data_p24_synthetic_e2e"


def _layout() -> RawDataLakeLayoutPolicy:
    return RawDataLakeLayoutPolicy(
        local_data_root_policy=LocalDataRootPolicy(
            data_root=_synthetic_data_root(),
            must_be_local=True,
            must_be_ignored=True,
            forbidden_repo_paths=DEFAULT_FORBIDDEN_REPO_PATHS,
            allowed_subdirs=DEFAULT_ALLOWED_SUBDIRS,
            max_file_policy=DEFAULT_MAX_FILE_POLICY,
        )
    )


def _load_pacing_policy(path: Path | None) -> RequestPacingPolicy:
    return RequestPacingPolicy.from_mapping(
        _load_json_mapping(path or _default_pacing_policy_path())
    )


def _load_access_mode(access_mode: DataAccessMode | str) -> DataAccessMode:
    mode = (
        access_mode
        if isinstance(access_mode, DataAccessMode)
        else DataAccessMode.for_mode(access_mode)
    )
    if mode.allows_external_api:
        msg = "DATA-P24 dry run requires dry_run or synthetic access mode"
        raise DataFoundationValidationError(msg)
    mode.validate_runtime_env({"CI": "true"}, ci=True)
    return mode


def _connection_profile(fixture: Mapping[str, object]) -> IBKRConnectionProfile:
    values = _require_mapping(fixture["connection_profile"], "connection_profile")
    return IBKRConnectionProfile(
        host=str(values["host"]),
        port=int(values["port"]),
        client_id=int(values["client_id"]),
        read_only_mode=bool(values["read_only_mode"]),
        environment=str(values["environment"]),
        connection_timeout=float(values["connection_timeout"]),
        validated_at=_parse_aware_datetime(values["validated_at"], "validated_at"),
    )


def _request_spec(fixture: Mapping[str, object]) -> HistoricalRequestSpec:
    return HistoricalRequestSpec.from_mapping(
        _require_mapping(fixture["historical_request"], "historical_request")
    )


def _manifest(
    fixture: Mapping[str, object],
    request_spec: HistoricalRequestSpec,
) -> HistoricalRequestManifest:
    values = _require_mapping(fixture["manifest"], "manifest")
    raw_values = _require_mapping(fixture["raw_object"], "raw_object")
    expected_coverage = dict(
        _require_mapping(values["expected_coverage"], "expected_coverage")
    )
    expected_coverage["expected_chunk_ids"] = (str(raw_values["chunk_id"]),)
    return HistoricalRequestManifest.create(
        manifest_id=str(values["manifest_id"]),
        batch_id=str(values["batch_id"]),
        request_specs=(request_spec,),
        chunk_count=1,
        expected_coverage=expected_coverage,
        pacing_policy_id=str(values["pacing_policy_id"]),
        data_root=_synthetic_data_root(),
        created_by=str(values["created_by"]),
        created_at=DATA_P24_CREATED_AT,
    )


def _contract_details(
    fixture: Mapping[str, object],
) -> tuple[ContractDiscoveryRequest, FuturesContractRecord, ContractDetailsSnapshot]:
    values = _require_mapping(fixture["contract_details"], "contract_details")
    request = ContractDiscoveryRequest.from_mapping(
        _require_mapping(values["request"], "contract_details.request")
    )
    contract = FuturesContractRecord.from_mapping(
        _require_mapping(values["contract_record"], "contract_details.contract_record")
    )
    snapshot_values = _require_mapping(values["snapshot"], "contract_details.snapshot")
    snapshot = ContractDetailsSnapshot.create(
        snapshot_id=str(snapshot_values["snapshot_id"]),
        contract_id=str(snapshot_values["contract_id"]),
        raw_details_ref=str(snapshot_values["raw_details_ref"]),
        normalized_fields=_require_mapping(
            values["normalized_fields"],
            "contract_details.normalized_fields",
        ),
        retrieved_at=_parse_aware_datetime(snapshot_values["retrieved_at"], "retrieved_at"),
        client_id=int(snapshot_values["client_id"]),
        source=str(snapshot_values["source"]),
    )
    return request, contract, snapshot


def _historical_bars_payload(fixture: Mapping[str, object]) -> bytes:
    payload = fixture["historical_bars_csv"]
    if not isinstance(payload, str):
        msg = "historical_bars_csv must be fixture text"
        raise DataFoundationValidationError(msg)
    return payload.encode("utf-8")


def _raw_object(
    fixture: Mapping[str, object],
    payload: bytes,
    request_spec: HistoricalRequestSpec,
) -> RawDataObject:
    values = _require_mapping(fixture["raw_object"], "raw_object")
    return RawDataObject.create(
        raw_object_id=str(values["raw_object_id"]),
        source=request_spec.source_id,
        request_id=str(values["request_id"]),
        chunk_id=str(values["chunk_id"]),
        content_hash=_content_hash(payload),
        schema_hint=str(values["schema_hint"]),
        retrieved_at=_parse_aware_datetime(values["retrieved_at"], "retrieved_at"),
        row_count=int(values["row_count"]),
        layout_policy=_layout(),
    )


def _canonical_bars(
    fixture: Mapping[str, object],
    raw_object: RawDataObject,
    payload: bytes,
    contract: FuturesContractRecord,
) -> tuple[CanonicalBarRecord, ...]:
    parsed_bars = parse_raw_bar_records(
        raw_object,
        layout_policy=_layout(),
        raw_payload_loader=lambda _: payload,
    )
    timestamp_rows = fixture["canonicalization_expectations"]
    if isinstance(timestamp_rows, str) or not isinstance(timestamp_rows, Sequence):
        msg = "canonicalization_expectations must be a sequence"
        raise DataFoundationValidationError(msg)

    records: list[CanonicalBarRecord] = []
    for parsed, timestamps in zip(parsed_bars, timestamp_rows, strict=True):
        timestamp_values = _require_mapping(timestamps, "canonicalization_expectations[]")
        records.append(
            CanonicalBarRecord.from_mapping(
                {
                    "instrument_id": "inst_synth_es",
                    "contract_id": contract.contract_id,
                    "series_id": "series_es_front_unadjusted",
                    "bar_start_ts": str(timestamp_values["bar_start_ts"]),
                    "bar_end_ts": str(timestamp_values["bar_end_ts"]),
                    "event_ts": str(timestamp_values["event_ts"]),
                    "available_ts": str(timestamp_values["available_ts"]),
                    "ingested_at": str(timestamp_values["ingested_at"]),
                    "open": parsed.open,
                    "high": parsed.high,
                    "low": parsed.low,
                    "close": parsed.close,
                    "volume": parsed.volume,
                    "source": parsed.source,
                    "source_request_id": parsed.request_id,
                    "data_version": DATA_P24_DRY_RUN_DATASET_VERSION_ID,
                    "quality_flags": (),
                    "session_label": "ETH",
                }
            )
        )
    return tuple(records)


def _expected_intervals(fixture: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    intervals = fixture["coverage_expected_intervals"]
    if isinstance(intervals, str) or not isinstance(intervals, Sequence):
        msg = "coverage_expected_intervals must be a sequence"
        raise DataFoundationValidationError(msg)
    return tuple(
        _require_mapping(interval, "coverage_expected_intervals[]") for interval in intervals
    )


def _quality_report(canonical_bars: tuple[CanonicalBarRecord, ...]) -> DataQualityReport:
    return DataQualityReport.from_canonical_bars(
        quality_report_id="dqr_data_p24_synthetic_e2e",
        dataset_version_id=DATA_P24_DRY_RUN_DATASET_VERSION_ID,
        bars=canonical_bars,
        expected_sessions=("ETH",),
    )


def _coverage_report(
    fixture: Mapping[str, object],
    canonical_bars: tuple[CanonicalBarRecord, ...],
) -> CoverageReport:
    return CoverageReport.from_canonical_bars(
        coverage_report_id="covr_data_p24_synthetic_e2e",
        dataset_version_id=DATA_P24_DRY_RUN_DATASET_VERSION_ID,
        bars=canonical_bars,
        expected_intervals=_expected_intervals(fixture),
    )


def _dataset_version(
    fixture: Mapping[str, object],
    manifest: HistoricalRequestManifest,
    quality_report: DataQualityReport,
    canonical_bars: tuple[CanonicalBarRecord, ...],
    contract: FuturesContractRecord,
) -> DatasetVersion:
    code_hash = hash_config(
        {
            "phase": "DATA-P24",
            "paths": (
                "src/alpha_system/data/foundation/dry_run.py",
                "src/alpha_system/data/foundation",
            ),
        }
    )
    config_hash = hash_config(
        {
            "fixture_id": fixture["fixture_id"],
            "bar_size": "1 min",
            "what_to_show": "TRADES",
            "dry_run": "synthetic",
        }
    )
    return DatasetVersion.from_mapping(
        {
            "dataset_version_id": DATA_P24_DRY_RUN_DATASET_VERSION_ID,
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
            "created_at": DATA_P24_CREATED_AT.isoformat(),
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
            "provider_request_id": "ibkr_req_data_p24_synthetic_e2e_001",
            "raw_object_ref": raw_object.raw_object_ref,
            "row_count": raw_object.row_count,
            "error_ref": None,
            "retrieved_at": raw_object.retrieved_at.isoformat(),
        }
    )


def _build_context(
    *,
    fixture_path: Path | None,
    pacing_policy_path: Path | None,
    access_mode: DataAccessMode | str,
) -> _DryRunContext:
    fixture = _load_json_mapping(fixture_path or _default_fixture_path())
    source_profile = DataSourceProfile.ibkr_historical(created_at=DATA_P24_CREATED_AT)
    mode = _load_access_mode(access_mode)
    client_policy = IBKRClientIdPolicy.default()
    connection_profile = run_connection_doctor(_connection_profile(fixture))
    client_policy.validate_client_id(connection_profile.client_id)
    boundary = build_read_only_ibkr_boundary(profile=connection_profile, access_mode=mode)

    discovery_request, contract, snapshot = _contract_details(fixture)
    request_spec = _request_spec(fixture)
    if discovery_request.client_id != request_spec.client_id:
        msg = "contract-discovery client_id must match historical request client_id"
        raise DataFoundationValidationError(msg)
    if snapshot.client_id != request_spec.client_id:
        msg = "contract snapshot client_id must match historical request client_id"
        raise DataFoundationValidationError(msg)
    if contract.contract_id != request_spec.contract_ref:
        msg = "contract record must match the historical request contract_ref"
        raise DataFoundationValidationError(msg)

    manifest = _manifest(fixture, request_spec)
    pacing_policy = _load_pacing_policy(pacing_policy_path)
    require_validated_manifest_for_provider_pull(manifest)
    require_pacing_policy_for_provider_pull(pacing_policy)
    forbid_naive_request_loop(pacing_policy)

    transport = _SyntheticTransport(_historical_bars_payload(fixture))
    payload, transport = transport.historical_bars()
    raw_object = _raw_object(fixture, payload, request_spec)
    canonical_bars = _canonical_bars(fixture, raw_object, payload, contract)
    quality_report = _quality_report(canonical_bars)
    coverage_report = _coverage_report(fixture, canonical_bars)
    version = _dataset_version(fixture, manifest, quality_report, canonical_bars, contract)
    version.require_versioned_prerequisites(
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest=manifest,
        code_hash=version.code_hash,
        config_hash=version.config_hash,
    )

    chunk = _complete_chunk(raw_object, request_spec)
    ledger = HistoricalPullLedger.create(
        pull_id="hpl_data_p24_synthetic_e2e_complete",
        manifest_id=manifest.manifest_id,
        chunk_records=(chunk,),
        expected_chunk_ids=(chunk.chunk_id,),
        started_at=DATA_P24_CREATED_AT,
        finished_at=DATA_P24_CREATED_AT,
    )
    ledger.pending_chunk_ids_for_resume(ledger.resume_token)
    partition_plan = DatasetPartitionPlan.canonical()
    for partition_id in partition_plan.partition_ids:
        partition_plan.permits_coverage_qa(partition_id)

    if boundary.access_mode.allows_external_api:
        msg = "DATA-P24 boundary unexpectedly allows external API calls"
        raise DataFoundationValidationError(msg)

    return _DryRunContext(
        fixture=fixture,
        source_profile=source_profile,
        connection_profile=connection_profile,
        access_mode=mode,
        request_spec=request_spec,
        manifest=manifest,
        pacing_policy=pacing_policy,
        contract=contract,
        raw_object=raw_object,
        canonical_bars=canonical_bars,
        quality_report=quality_report,
        coverage_report=coverage_report,
        dataset_version=version,
        ledger=ledger,
        partition_plan=partition_plan,
        external_call_attempted=transport.external_call_count > 0,
    )


def _capture_block(
    block_id: str,
    action: Callable[[], object],
) -> LifecycleBlockAssertion:
    try:
        action()
    except (DataFoundationValidationError, ReadOnlyBoundaryViolation) as exc:
        return LifecycleBlockAssertion(block_id=block_id, blocked=True, reason=str(exc))
    return LifecycleBlockAssertion(
        block_id=block_id,
        blocked=False,
        reason="missing prerequisite did not fail closed",
    )


def _capture_composite_block(
    block_id: str,
    actions: Sequence[Callable[[], object]],
) -> LifecycleBlockAssertion:
    reasons: list[str] = []
    for action in actions:
        assertion = _capture_block(block_id, action)
        if not assertion.blocked:
            return assertion
        reasons.append(assertion.reason)
    return LifecycleBlockAssertion(
        block_id=block_id,
        blocked=True,
        reason="; ".join(reasons),
    )


def _prohibited_state_action(
    state: str,
    version: DatasetVersion,
    *,
    quality_report: DataQualityReport,
    coverage_report: CoverageReport,
    source_manifest: HistoricalRequestManifest,
) -> Callable[[], object]:
    def action() -> object:
        try:
            return version.require_lifecycle_prerequisites(
                state,
                quality_report=quality_report,
                coverage_report=coverage_report,
                source_manifest=source_manifest,
                code_hash=version.code_hash,
                config_hash=version.config_hash,
            )
        except DataFoundationValidationError as exc:
            raise DataFoundationValidationError(f"{state}: {exc}") from exc

    return action


def assert_lifecycle_blocks_fail_closed(
    *,
    fixture_path: Path | None = None,
    pacing_policy_path: Path | None = None,
) -> tuple[LifecycleBlockAssertion, ...]:
    """Exercise DATA-P24 lifecycle blocks at missing-prerequisite points."""

    context = _build_context(
        fixture_path=fixture_path,
        pacing_policy_path=pacing_policy_path,
        access_mode=DataAccessMode.synthetic(),
    )
    clean_quality = context.quality_report
    clean_coverage = context.coverage_report
    version = context.dataset_version
    canonical = context.canonical_bars[0]

    missing_available_ts = dict(canonical.to_mapping())
    missing_available_ts.pop("available_ts")
    early_available_ts = dict(canonical.to_mapping())
    early_available_ts["available_ts"] = canonical.bar_start_ts.isoformat()

    quality_gap = DataQualityReport.from_canonical_bars(
        quality_report_id="dqr_data_p24_synthetic_gap",
        dataset_version_id=version.dataset_version_id,
        bars=(context.canonical_bars[0], context.canonical_bars[2]),
        expected_sessions=("ETH",),
    )
    incomplete_coverage = CoverageReport.from_canonical_bars(
        coverage_report_id="covr_data_p24_synthetic_incomplete_chunk",
        dataset_version_id=version.dataset_version_id,
        bars=context.canonical_bars,
        expected_intervals=_expected_intervals(context.fixture),
        incomplete_chunks=(
            {
                "chunk_id": "hchunk_data_p24_synthetic_missing",
                "status": "INCOMPLETE",
                "start_ts": context.request_spec.start_ts.isoformat(),
                "end_ts": context.request_spec.end_ts.isoformat(),
                "reason": "synthetic incomplete chunk assertion",
            },
        ),
    )
    boundary = build_read_only_ibkr_boundary(
        profile=context.connection_profile,
        access_mode=context.access_mode,
    )

    return (
        _capture_block(
            "missing_manifest_blocks_provider_pull",
            lambda: require_validated_manifest_for_provider_pull(None),
        ),
        _capture_composite_block(
            "reserved_client_ids_block_connection",
            (
                lambda: IBKRConnectionProfile(client_id=101),
                lambda: IBKRConnectionProfile(client_id=102),
            ),
        ),
        _capture_composite_block(
            "client_ids_outside_201_209_fail_closed",
            (
                lambda: IBKRClientIdPolicy.default().validate_client_id(200),
                lambda: IBKRClientIdPolicy.default().validate_client_id(210),
            ),
        ),
        _capture_composite_block(
            "missing_pacing_guard_blocks_pull",
            (
                lambda: require_pacing_policy_for_provider_pull(None),
                lambda: forbid_naive_request_loop(None),
            ),
        ),
        _capture_composite_block(
            "missing_local_data_root_policy_blocks_raw_writes",
            (
                lambda: require_local_data_root_policy(None),
                lambda: require_raw_data_lake_layout_policy(None),
            ),
        ),
        _capture_block(
            "missing_available_ts_blocks_canonicalization",
            lambda: CanonicalBarRecord.from_mapping(missing_available_ts),
        ),
        _capture_block(
            "available_ts_before_bar_end_blocks_canonicalization",
            lambda: CanonicalBarRecord.from_mapping(early_available_ts),
        ),
        _capture_block(
            "quality_gap_blocks_versioning",
            lambda: version.require_versioned_prerequisites(
                quality_report=quality_gap,
                coverage_report=clean_coverage,
                source_manifest=context.manifest,
                code_hash=version.code_hash,
                config_hash=version.config_hash,
            ),
        ),
        _capture_block(
            "incomplete_chunk_blocks_versioning",
            lambda: version.require_versioned_prerequisites(
                quality_report=clean_quality,
                coverage_report=incomplete_coverage,
                source_manifest=context.manifest,
                code_hash=version.code_hash,
                config_hash=version.config_hash,
            ),
        ),
        _capture_composite_block(
            "prohibited_mvp_states_unreachable",
            tuple(
                _prohibited_state_action(
                    state,
                    quality_report=clean_quality,
                    coverage_report=clean_coverage,
                    source_manifest=context.manifest,
                    version=version,
                )
                for state in PROHIBITED_MVP_STATES
            ),
        ),
        _capture_composite_block(
            "order_account_methods_unreachable_from_data_boundary",
            tuple(
                lambda method_name=method_name: boundary.call_read_only_api(method_name)
                for method_name in _FORBIDDEN_BOUNDARY_METHODS
            ),
        ),
    )


def run_synthetic_data_foundation_dry_run(
    *,
    fixture_path: Path | None = None,
    pacing_policy_path: Path | None = None,
    registry_path: Path | None = None,
    access_mode: DataAccessMode | str = "synthetic",
) -> EndToEndDryRunSummary:
    """Run the full synthetic data-foundation lifecycle in memory."""

    context = _build_context(
        fixture_path=fixture_path,
        pacing_policy_path=pacing_policy_path,
        access_mode=access_mode,
    )
    registry_round_trip = False
    if registry_path is not None:
        persist_dataset_version(
            registry_path,
            context.dataset_version,
            quality_report=context.quality_report,
            coverage_report=context.coverage_report,
            source_manifest=context.manifest,
            code_hash=context.dataset_version.code_hash,
            config_hash=context.dataset_version.config_hash,
        )
        registry_round_trip = (
            resolve_dataset_version(
                registry_path,
                context.dataset_version.dataset_version_id,
            )
            == context.dataset_version
        )

    lifecycle_blocks = assert_lifecycle_blocks_fail_closed(
        fixture_path=fixture_path,
        pacing_policy_path=pacing_policy_path,
    )
    read_only_boundary_confirmed = any(
        assertion.block_id == "order_account_methods_unreachable_from_data_boundary"
        and assertion.blocked
        for assertion in lifecycle_blocks
    )
    prohibited_states_unreachable = any(
        assertion.block_id == "prohibited_mvp_states_unreachable" and assertion.blocked
        for assertion in lifecycle_blocks
    )
    return EndToEndDryRunSummary(
        status="SYNTHETIC_COMPLETE",
        fixture_id=str(context.fixture["fixture_id"]),
        source_id=context.source_profile.source_id,
        access_mode=context.access_mode.mode,
        allows_external_api=context.access_mode.allows_external_api,
        external_call_attempted=context.external_call_attempted,
        client_id=context.connection_profile.client_id,
        manifest_id=context.manifest.manifest_id,
        manifest_hash=context.manifest.manifest_hash,
        pacing_policy_id=context.pacing_policy.pacing_policy_id,
        chunk_count=context.manifest.chunk_count,
        completed_chunk_count=len(context.ledger.completed_chunk_ids()),
        pending_resume_chunk_count=len(
            context.ledger.pending_chunk_ids_for_resume(context.ledger.resume_token)
        ),
        raw_object_count=1,
        parsed_bar_count=len(context.canonical_bars),
        canonical_bar_count=len(context.canonical_bars),
        quality_status=context.quality_report.status.value,
        coverage_status=context.coverage_report.coverage_status.value,
        dataset_version_id=context.dataset_version.dataset_version_id,
        registry_round_trip=registry_round_trip,
        partition_ids=context.partition_plan.partition_ids,
        lifecycle_blocks=lifecycle_blocks,
        read_only_boundary_confirmed=read_only_boundary_confirmed,
        prohibited_states_unreachable=prohibited_states_unreachable,
        reproducibility_hashes=context.dataset_version.reproducibility_hashes,
    )


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-path", type=Path, default=None)
    parser.add_argument("--pacing-policy-path", type=Path, default=None)
    parser.add_argument("--registry-path", type=Path, default=None)
    parser.add_argument(
        "--mode",
        choices=("dry_run", "synthetic"),
        default="synthetic",
        help="Local-only mode; both forbid external API calls.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(tuple(argv or ()))
    try:
        summary = run_synthetic_data_foundation_dry_run(
            fixture_path=args.fixture_path,
            pacing_policy_path=args.pacing_policy_path,
            registry_path=args.registry_path,
            access_mode=args.mode,
        )
    except DataFoundationValidationError as exc:
        print(
            json.dumps(
                {"status": "BLOCKED", "reason": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(_json_ready(summary.to_mapping()), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DATA_P24_DRY_RUN_DATASET_VERSION_ID",
    "EndToEndDryRunSummary",
    "LifecycleBlockAssertion",
    "PROHIBITED_MVP_STATES",
    "assert_lifecycle_blocks_fail_closed",
    "run_synthetic_data_foundation_dry_run",
]
