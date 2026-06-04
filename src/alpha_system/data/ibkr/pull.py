"""Guarded DATA-P22 read-only IBKR smoke-pull entry point.

The module composes the existing data-foundation contracts. It does not import a
generic IBKR client, expose broker/account/order methods, or run any provider
call unless an external-enabled ``DataAccessMode`` and the required runtime env
gates validate first.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import MappingProxyType
from typing import Protocol

from alpha_system.data.foundation.bars import RawDataLakeLayoutPolicy, RawDataObject
from alpha_system.data.foundation.ibkr import (
    IBKRClientIdPolicy,
    IBKRConnectionProfile,
    IBKRReadOnlyApiBoundary,
    build_read_only_ibkr_boundary,
    run_connection_doctor,
)
from alpha_system.data.foundation.requests import (
    HistoricalChunkRecord,
    HistoricalChunkStatus,
    HistoricalPullLedger,
    HistoricalPullLedgerStatus,
    HistoricalRequestManifest,
    HistoricalRequestSpec,
    ProviderErrorRecord,
    ProviderErrorResolution,
    RequestPacingPolicy,
    forbid_naive_request_loop,
    require_pacing_policy_for_provider_pull,
    require_validated_manifest_for_provider_pull,
)
from alpha_system.data.foundation.sources import DataAccessMode, DataFoundationValidationError

DATA_P22_MAX_SMOKE_CHUNKS = 1
DEFAULT_SMOKE_BATCH_ID = "mini_main"
DEFAULT_PACING_POLICY_RELATIVE_PATH = Path("configs/data/request_pacing_policy_to_be_verified.json")
_HISTORICAL_METHOD_NAME = "reqHistoricalData"
_STOP_FILE_ENV_NAMES = ("ALPHA_FRONTIER_STOP_FILE", "FRONTIER_STOP_FILE")


@dataclass(frozen=True, slots=True)
class SmokePullDoctorReport:
    """Redacted connection-doctor result used before a smoke pull."""

    profile: IBKRConnectionProfile
    reachable: bool
    probe_performed: bool
    failure_reason: str | None = None

    def to_mapping(self) -> Mapping[str, object]:
        """Return a redacted doctor summary with no account/provider payload."""

        status = "reachable" if self.reachable else "unreachable"
        if not self.probe_performed:
            status = "not_probed"
        return MappingProxyType(
            {
                "status": status,
                "host": self.profile.host,
                "port": self.profile.port,
                "client_id": self.profile.client_id,
                "read_only_mode": self.profile.read_only_mode,
                "probe_performed": self.probe_performed,
                "retry_target": None,
                "failure_reason": self.failure_reason,
            }
        )


@dataclass(frozen=True, slots=True)
class RawPayloadWriteResult:
    """Aggregate raw write metadata returned by the local artifact store."""

    raw_object_ref: str
    row_count: int
    raw_object_id: str


class SmokePullArtifactStore(Protocol):
    """Local-only artifact sink used after a read-only historical response."""

    def write_raw_payload(
        self,
        *,
        request_spec: HistoricalRequestSpec,
        chunk_id: str,
        payload: bytes,
        retrieved_at: datetime,
    ) -> RawPayloadWriteResult:
        """Write immutable raw payload bytes under ALPHA_DATA_ROOT."""

    def write_ledger(self, ledger: HistoricalPullLedger) -> None:
        """Write the local-only pull ledger."""

    def write_provider_error(self, error: ProviderErrorRecord) -> None:
        """Write a local-only provider-error record."""


@dataclass(frozen=True, slots=True)
class LocalSmokePullArtifactStore:
    """Local-only store for raw bytes, ledgers, and provider errors."""

    layout_policy: RawDataLakeLayoutPolicy

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "LocalSmokePullArtifactStore":
        """Build the local store from ALPHA_DATA_ROOT."""

        return cls(layout_policy=RawDataLakeLayoutPolicy.from_env(env))

    @property
    def _metadata_root(self) -> Path:
        return self.layout_policy.local_data_root_policy.data_root / "metadata" / "ibkr_smoke_pull"

    def write_raw_payload(
        self,
        *,
        request_spec: HistoricalRequestSpec,
        chunk_id: str,
        payload: bytes,
        retrieved_at: datetime,
    ) -> RawPayloadWriteResult:
        """Write one immutable content-addressed raw object."""

        content_hash = "sha256:" + hashlib.sha256(payload).hexdigest()
        raw_object = RawDataObject.create(
            raw_object_id=f"raw_ibkr_smoke_{chunk_id}",
            source=request_spec.source_id,
            request_id=request_spec.request_spec_id,
            chunk_id=chunk_id,
            content_hash=content_hash,
            schema_hint="ibkr_historical_bars_raw_v1",
            retrieved_at=retrieved_at,
            row_count=_count_payload_rows(payload),
            layout_policy=self.layout_policy,
        )
        self._assert_raw_slot_not_bound_to_different_hash(raw_object)

        if raw_object.path.exists():
            existing_hash = "sha256:" + hashlib.sha256(raw_object.path.read_bytes()).hexdigest()
            if existing_hash != content_hash:
                msg = "existing raw object path content does not match content address"
                raise DataFoundationValidationError(msg)
        else:
            raw_object.path.parent.mkdir(parents=True, exist_ok=True)
            with raw_object.path.open("xb") as handle:
                handle.write(payload)

        return RawPayloadWriteResult(
            raw_object_ref=raw_object.raw_object_ref,
            row_count=raw_object.row_count,
            raw_object_id=raw_object.raw_object_id,
        )

    def write_ledger(self, ledger: HistoricalPullLedger) -> None:
        """Persist one pull ledger without overwriting an existing ledger."""

        path = self._metadata_root / "ledgers" / f"{ledger.pull_id}.json"
        self._write_json_once(path, ledger.to_mapping())

    def write_provider_error(self, error: ProviderErrorRecord) -> None:
        """Persist one provider-error record without overwriting."""

        path = self._metadata_root / "provider_errors" / f"{error.error_id}.json"
        self._write_json_once(path, error.to_mapping())

    def _assert_raw_slot_not_bound_to_different_hash(self, raw_object: RawDataObject) -> None:
        chunk_root = raw_object.path.parent.parent
        existing_paths = tuple(chunk_root.glob("sha256=*/*.raw"))
        conflicting = tuple(path for path in existing_paths if path != raw_object.path)
        if conflicting:
            msg = "raw object slot already has a different content hash; refusing overwrite"
            raise DataFoundationValidationError(msg)

    @staticmethod
    def _write_json_once(path: Path, payload: Mapping[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as handle:
            json.dump(_json_ready(payload), handle, indent=2, sort_keys=True)
            handle.write("\n")


@dataclass(frozen=True, slots=True)
class SmokePullSummary:
    """Curated smoke-pull summary with no raw bars or provider response body."""

    status: str
    batch_id: str
    access_mode: str
    external_call_attempted: bool
    chunks_requested: int
    chunks_complete: int
    chunks_failed: int
    raw_objects_written: int
    provider_errors_logged: int
    manifest_id: str | None
    pacing_policy_id: str | None
    ledger_status: str | None
    resume_token: str | None
    doctor: Mapping[str, object]

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable summary for stdout or handoff notes."""

        return MappingProxyType(
            {
                "status": self.status,
                "batch_id": self.batch_id,
                "access_mode": self.access_mode,
                "external_call_attempted": self.external_call_attempted,
                "chunks_requested": self.chunks_requested,
                "chunks_complete": self.chunks_complete,
                "chunks_failed": self.chunks_failed,
                "raw_objects_written": self.raw_objects_written,
                "provider_errors_logged": self.provider_errors_logged,
                "manifest_id": self.manifest_id,
                "pacing_policy_id": self.pacing_policy_id,
                "ledger_status": self.ledger_status,
                "resume_token": self.resume_token,
                "doctor": self.doctor,
            }
        )


ReachabilityProbe = Callable[[IBKRConnectionProfile], SmokePullDoctorReport]
Clock = Callable[[], datetime]


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _repo_root() -> Path:
    return Path(__file__).resolve(strict=False).parents[4]


def _timestamp_id(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _require_one_smoke_chunk(max_chunks: object) -> int:
    if isinstance(max_chunks, bool) or not isinstance(max_chunks, int):
        msg = "max_chunks must be the integer 1 for DATA-P22 smoke pulls"
        raise DataFoundationValidationError(msg)
    if max_chunks != DATA_P22_MAX_SMOKE_CHUNKS:
        msg = "DATA-P22 smoke pull is bounded to exactly one chunk"
        raise DataFoundationValidationError(msg)
    return max_chunks


def _require_env_present(env: Mapping[str, str], name: str) -> str:
    value = env.get(name)
    if value is None or not value.strip():
        msg = f"{name} is required for authorized smoke-pull local outputs"
        raise DataFoundationValidationError(msg)
    return value


def _assert_no_stop_file(env: Mapping[str, str]) -> None:
    for env_name in _STOP_FILE_ENV_NAMES:
        configured = env.get(env_name)
        if configured and Path(configured).expanduser().exists():
            msg = f"active STOP file blocks DATA-P22 smoke pull: {configured}"
            raise DataFoundationValidationError(msg)


def _json_ready(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(nested) for key, nested in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if hasattr(value, "value") and isinstance(value.value, str):
        return value.value
    if value is None or isinstance(value, bool | int | float | str):
        return value
    msg = f"value {value!r} is not JSON-stable"
    raise DataFoundationValidationError(msg)


def _load_json_mapping(path: Path) -> Mapping[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        msg = f"{path.as_posix()} must contain a JSON object"
        raise DataFoundationValidationError(msg)
    return payload


def _payload_to_bytes(payload: object) -> bytes:
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, str):
        return payload.encode("utf-8")
    if isinstance(payload, Mapping):
        encoded = json.dumps(
            _json_ready(payload),
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return encoded.encode("utf-8")
    msg = "read-only historical handler must return bytes, text, or a JSON mapping"
    raise DataFoundationValidationError(msg)


def _count_payload_rows(payload: bytes) -> int:
    text = payload.decode("utf-8", errors="ignore").strip()
    if not text:
        return 0
    lines = tuple(line for line in text.splitlines() if line.strip())
    if not lines:
        return 0
    first_line = lines[0]
    if "," in first_line and any(character.isalpha() for character in first_line):
        return max(0, len(lines) - 1)
    return len(lines)


def _redacted_error_message(exc: BaseException) -> str:
    return f"redacted provider error class: {type(exc).__name__}"


def _doctor_not_probed(profile: IBKRConnectionProfile) -> SmokePullDoctorReport:
    doctor_profile = run_connection_doctor(profile)
    return SmokePullDoctorReport(
        profile=doctor_profile,
        reachable=False,
        probe_performed=False,
        failure_reason="external reachability probe not requested",
    )


def probe_ibkr_host_port(profile: IBKRConnectionProfile) -> SmokePullDoctorReport:
    """Probe exactly the configured host/port once before any IBKR API call."""

    doctor_profile = run_connection_doctor(profile)
    try:
        with socket.create_connection(
            (doctor_profile.host, doctor_profile.port),
            timeout=doctor_profile.connection_timeout,
        ):
            return SmokePullDoctorReport(
                profile=doctor_profile,
                reachable=True,
                probe_performed=True,
                failure_reason=None,
            )
    except OSError as exc:
        return SmokePullDoctorReport(
            profile=doctor_profile,
            reachable=False,
            probe_performed=True,
            failure_reason=f"{type(exc).__name__}: {exc}",
        )


def load_default_pacing_policy(
    path: Path | None = None,
) -> RequestPacingPolicy:
    """Load the DATA-P08 conservative pacing policy config."""

    policy_path = path or _repo_root() / DEFAULT_PACING_POLICY_RELATIVE_PATH
    return RequestPacingPolicy.from_mapping(_load_json_mapping(policy_path))


def build_default_smoke_manifest(
    *,
    env: Mapping[str, str],
    profile: IBKRConnectionProfile,
    batch: str = DEFAULT_SMOKE_BATCH_ID,
    now: datetime | None = None,
    pacing_policy_id: str = "rpp_ibkr_historical_conservative_tobeverified_v1",
) -> HistoricalRequestManifest:
    """Build a one-chunk runtime smoke manifest for the target operator command."""

    created_at = now or _now_utc()
    end_ts = created_at.astimezone(UTC).replace(second=0, microsecond=0)
    start_ts = end_ts - timedelta(minutes=30)
    data_root = _require_env_present(env, "ALPHA_DATA_ROOT")
    request_spec = HistoricalRequestSpec(
        request_spec_id="hrs_ibkr_smoke_mini_main_es_v1",
        source_id="dsrc_ibkr_historical",
        symbol_root="ES",
        contract_ref="fcr_ibkr_smoke_es_contfut_to_be_verified",
        sec_type="CONTFUT",
        exchange="CME",
        currency="USD",
        bar_size="1 min",
        what_to_show="TRADES",
        use_rth=False,
        duration="1800 S",
        end_datetime_policy="explicit_runtime_smoke_end_ts",
        start_ts=start_ts,
        end_ts=end_ts,
        chunk_policy={
            "planned_chunks": 1,
            "max_duration": "1800 S",
            "policy": "DATA-P22 bounded smoke pull",
        },
        client_id=profile.client_id,
    )
    return HistoricalRequestManifest.create(
        manifest_id=f"hrm_ibkr_smoke_{batch}_v1",
        batch_id=f"batch_ibkr_smoke_{batch}_v1",
        request_specs=(request_spec,),
        chunk_count=1,
        expected_coverage={
            "smoke_pull": True,
            "bounded_chunk_count": 1,
            "coverage_status": "smoke_pull_not_quality_checked",
            "roots": ("ES",),
            "bar_size": "1 min",
            "what_to_show": "TRADES",
            "real_coverage_claim": False,
            "quality_claim": False,
            "production_readiness_claim": False,
        },
        pacing_policy_id=pacing_policy_id,
        data_root=data_root,
        created_by="DATA-P22 smoke-pull entry point",
        created_at=created_at,
    )


def _coerce_boundary(
    *,
    boundary: IBKRReadOnlyApiBoundary | None,
    profile: IBKRConnectionProfile,
    access_mode: DataAccessMode,
) -> IBKRReadOnlyApiBoundary:
    read_only_methods: Mapping[str, Callable[..., object]] = MappingProxyType({})
    if boundary is not None:
        read_only_methods = boundary.read_only_methods
    return build_read_only_ibkr_boundary(
        profile=profile,
        access_mode=access_mode,
        read_only_methods=read_only_methods,
    )


def _validated_execution_inputs(
    *,
    manifest: HistoricalRequestManifest | Mapping[str, object] | None,
    pacing_policy: RequestPacingPolicy | Mapping[str, object] | None,
    env: Mapping[str, str],
    profile: IBKRConnectionProfile,
    batch: str,
    max_chunks: int,
    now: datetime,
    use_default_manifest: bool,
    use_default_pacing_policy: bool,
) -> tuple[HistoricalRequestManifest, RequestPacingPolicy]:
    manifest_record = (
        build_default_smoke_manifest(env=env, profile=profile, batch=batch, now=now)
        if manifest is None and use_default_manifest
        else require_validated_manifest_for_provider_pull(manifest)
    )
    pacing_record = (
        load_default_pacing_policy()
        if pacing_policy is None and use_default_pacing_policy
        else require_pacing_policy_for_provider_pull(pacing_policy)
    )
    forbid_naive_request_loop(pacing_record)
    if manifest_record.pacing_policy_id != pacing_record.pacing_policy_id:
        msg = "manifest pacing_policy_id must match the armed RequestPacingPolicy"
        raise DataFoundationValidationError(msg)
    if manifest_record.chunk_count > max_chunks:
        msg = "smoke manifest chunk_count exceeds DATA-P22 max_chunks bound"
        raise DataFoundationValidationError(msg)
    if not manifest_record.request_specs:
        msg = "smoke manifest must contain one request spec"
        raise DataFoundationValidationError(msg)
    return manifest_record, pacing_record


def _provider_error_record(
    *,
    exc: BaseException,
    request_id: str,
    chunk_id: str,
    timestamp: datetime,
) -> ProviderErrorRecord:
    return ProviderErrorRecord(
        error_id=f"perr_ibkr_smoke_{chunk_id}",
        provider="IBKR",
        request_id=request_id,
        chunk_id=chunk_id,
        error_code=type(exc).__name__,
        error_message=_redacted_error_message(exc),
        retryable=False,
        attempt=1,
        timestamp=timestamp,
        resolution=ProviderErrorResolution.QUARANTINED_NON_RETRYABLE,
    )


def _ledger_for_chunks(
    *,
    pull_id: str,
    manifest_id: str,
    chunks: Iterable[HistoricalChunkRecord],
    expected_chunk_ids: Iterable[str],
    started_at: datetime,
    finished_at: datetime,
) -> HistoricalPullLedger:
    return HistoricalPullLedger.create(
        pull_id=pull_id,
        manifest_id=manifest_id,
        chunk_records=tuple(chunks),
        expected_chunk_ids=tuple(expected_chunk_ids),
        started_at=started_at,
        finished_at=finished_at,
    )


def run_ibkr_smoke_pull(
    *,
    manifest: HistoricalRequestManifest | Mapping[str, object] | None = None,
    pacing_policy: RequestPacingPolicy | Mapping[str, object] | None = None,
    boundary: IBKRReadOnlyApiBoundary | None = None,
    access_mode: DataAccessMode | None = None,
    env: Mapping[str, str] | None = None,
    ci: bool | None = None,
    max_chunks: int = DATA_P22_MAX_SMOKE_CHUNKS,
    batch: str = DEFAULT_SMOKE_BATCH_ID,
    artifact_store: SmokePullArtifactStore | None = None,
    reachability_probe: ReachabilityProbe | None = None,
    now: Clock = _now_utc,
    execute: bool = False,
    use_default_manifest: bool = False,
    use_default_pacing_policy: bool = False,
) -> SmokePullSummary:
    """Run a dry-run preflight or one authorized read-only smoke pull."""

    source = os.environ if env is None else env
    max_chunk_count = _require_one_smoke_chunk(max_chunks)
    timestamp = now()
    access = access_mode or DataAccessMode.authorized_pull()
    profile = IBKRConnectionProfile.from_env(source)
    IBKRClientIdPolicy.default().validate_client_id(profile.client_id)
    dry_doctor = _doctor_not_probed(profile)

    if not execute:
        return SmokePullSummary(
            status="DRY_RUN",
            batch_id=batch,
            access_mode=access.mode,
            external_call_attempted=False,
            chunks_requested=0,
            chunks_complete=0,
            chunks_failed=0,
            raw_objects_written=0,
            provider_errors_logged=0,
            manifest_id=None,
            pacing_policy_id=None,
            ledger_status=None,
            resume_token=None,
            doctor=dry_doctor.to_mapping(),
        )

    _assert_no_stop_file(source)
    access.validate_runtime_env(source, ci=ci)
    if not access.allows_external_api:
        msg = f"DataAccessMode {access.mode!r} forbids external API calls"
        raise DataFoundationValidationError(msg)
    if not access.allows_raw_write:
        msg = f"DataAccessMode {access.mode!r} forbids raw local writes"
        raise DataFoundationValidationError(msg)
    _require_env_present(source, "ALPHA_DATA_ROOT")

    probe = reachability_probe or probe_ibkr_host_port
    doctor = probe(profile)
    if not doctor.reachable:
        msg = "connection doctor failed; refusing smoke pull before provider call"
        raise DataFoundationValidationError(msg)

    manifest_record, pacing_record = _validated_execution_inputs(
        manifest=manifest,
        pacing_policy=pacing_policy,
        env=source,
        profile=doctor.profile,
        batch=batch,
        max_chunks=max_chunk_count,
        now=timestamp,
        use_default_manifest=use_default_manifest,
        use_default_pacing_policy=use_default_pacing_policy,
    )
    request_spec = manifest_record.request_specs[0]
    if request_spec.client_id != doctor.profile.client_id:
        msg = "request_spec client_id must match the validated connection profile"
        raise DataFoundationValidationError(msg)

    smoke_boundary = _coerce_boundary(boundary=boundary, profile=doctor.profile, access_mode=access)
    if _HISTORICAL_METHOD_NAME not in smoke_boundary.read_only_methods:
        msg = "missing registered read-only historical data handler blocks smoke pull"
        raise DataFoundationValidationError(msg)

    timestamp_token = _timestamp_id(timestamp)
    pull_id = f"hpl_ibkr_smoke_{batch}_{timestamp_token}"
    chunk_id = f"hchunk_ibkr_smoke_{request_spec.symbol_root.lower()}_{timestamp_token}"
    provider_request_id = f"ibkr_smoke_req_{request_spec.symbol_root.lower()}_{timestamp_token}"
    store = artifact_store or LocalSmokePullArtifactStore.from_env(source)

    try:
        response = smoke_boundary.request_historical_data(
            request_spec,
            env=source,
            ci=ci,
        )
    except Exception as exc:
        provider_error = _provider_error_record(
            exc=exc,
            request_id=provider_request_id,
            chunk_id=chunk_id,
            timestamp=timestamp,
        )
        store.write_provider_error(provider_error)
        failed_chunk = HistoricalChunkRecord(
            chunk_id=chunk_id,
            request_spec_id=request_spec.request_spec_id,
            symbol_root=request_spec.symbol_root,
            contract_ref=request_spec.contract_ref,
            start_ts=request_spec.start_ts,
            end_ts=request_spec.end_ts,
            status=HistoricalChunkStatus.QUARANTINED,
            attempt_count=1,
            provider_request_id=provider_request_id,
            raw_object_ref=None,
            row_count=None,
            error_ref=provider_error.error_id,
            retrieved_at=None,
        )
        ledger = _ledger_for_chunks(
            pull_id=pull_id,
            manifest_id=manifest_record.manifest_id,
            chunks=(failed_chunk,),
            expected_chunk_ids=(chunk_id,),
            started_at=timestamp,
            finished_at=timestamp,
        )
        store.write_ledger(ledger)
        msg = "provider error recorded locally; smoke pull chunk quarantined"
        raise DataFoundationValidationError(msg) from exc

    payload = _payload_to_bytes(response)
    raw_write = store.write_raw_payload(
        request_spec=request_spec,
        chunk_id=chunk_id,
        payload=payload,
        retrieved_at=timestamp,
    )
    complete_chunk = HistoricalChunkRecord(
        chunk_id=chunk_id,
        request_spec_id=request_spec.request_spec_id,
        symbol_root=request_spec.symbol_root,
        contract_ref=request_spec.contract_ref,
        start_ts=request_spec.start_ts,
        end_ts=request_spec.end_ts,
        status=HistoricalChunkStatus.COMPLETE,
        attempt_count=1,
        provider_request_id=provider_request_id,
        raw_object_ref=raw_write.raw_object_ref,
        row_count=raw_write.row_count,
        error_ref=None,
        retrieved_at=timestamp,
    )
    ledger = _ledger_for_chunks(
        pull_id=pull_id,
        manifest_id=manifest_record.manifest_id,
        chunks=(complete_chunk,),
        expected_chunk_ids=(chunk_id,),
        started_at=timestamp,
        finished_at=timestamp,
    )
    store.write_ledger(ledger)

    return SmokePullSummary(
        status="COMPLETE",
        batch_id=batch,
        access_mode=access.mode,
        external_call_attempted=True,
        chunks_requested=1,
        chunks_complete=1 if ledger.status is HistoricalPullLedgerStatus.COMPLETE else 0,
        chunks_failed=0,
        raw_objects_written=1,
        provider_errors_logged=0,
        manifest_id=manifest_record.manifest_id,
        pacing_policy_id=pacing_record.pacing_policy_id,
        ledger_status=ledger.status.value,
        resume_token=ledger.resume_token,
        doctor=doctor.to_mapping(),
    )


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DATA-P22 guarded read-only IBKR smoke-pull preflight",
    )
    parser.add_argument("--batch", default=DEFAULT_SMOKE_BATCH_ID)
    parser.add_argument("--smoke", action="store_true", help="attempt the authorized smoke pull")
    parser.add_argument("--dry-run", action="store_true", help="force non-pulling preflight")
    parser.add_argument("--max-chunks", type=int, default=DATA_P22_MAX_SMOKE_CHUNKS)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--pacing-policy", type=Path)
    return parser.parse_args(argv)


def _summary_stdout(summary: SmokePullSummary) -> None:
    print(json.dumps(_json_ready(summary.to_mapping()), indent=2, sort_keys=True))


def _blocked_stdout(exc: BaseException) -> None:
    payload = {
        "status": "BLOCKED",
        "error_class": type(exc).__name__,
        "message": str(exc),
        "external_call_attempted": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    """CLI for ``python -m alpha_system.data.ibkr.pull``."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    execute = bool(args.smoke and not args.dry_run)
    manifest = (
        HistoricalRequestManifest.from_mapping(_load_json_mapping(args.manifest))
        if args.manifest is not None
        else None
    )
    pacing_policy = (
        RequestPacingPolicy.from_mapping(_load_json_mapping(args.pacing_policy))
        if args.pacing_policy is not None
        else None
    )
    try:
        summary = run_ibkr_smoke_pull(
            manifest=manifest,
            pacing_policy=pacing_policy,
            max_chunks=args.max_chunks,
            batch=args.batch,
            execute=execute,
            use_default_manifest=execute and manifest is None,
            use_default_pacing_policy=execute and pacing_policy is None,
        )
    except DataFoundationValidationError as exc:
        _blocked_stdout(exc)
        return 2
    _summary_stdout(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
