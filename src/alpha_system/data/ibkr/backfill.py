"""DATA-P23 guarded local backfill resume-drill entry point.

The drill composes the existing data-foundation contracts. It performs no
provider call in dry-run or synthetic mode, and the authorized-pull mode fails
closed through ``DataAccessMode`` before any historical handler can run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import deque
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
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
from alpha_system.data.ibkr._json_utils import json_ready_base as _json_ready
from alpha_system.data.ibkr.pull import (
    RawPayloadWriteResult,
    SmokePullDoctorReport,
    load_default_pacing_policy,
    probe_ibkr_host_port,
)

DEFAULT_BACKFILL_BATCH_ID = "mini_main_resume_drill"
DEFAULT_MAX_DRILL_CHUNKS = 2
DEFAULT_SYNTHETIC_FIXTURE_RELATIVE_PATH = Path(
    "tests/fixtures/data/synthetic_backfill_resume_drill.json"
)
_IBKR_ONE_MIN_MAX_REQUEST_SPAN = timedelta(days=1)
IBKR_MAX_REQUEST_SPAN_BY_BAR_SIZE: Mapping[str, timedelta] = MappingProxyType(
    {
        "1 min": _IBKR_ONE_MIN_MAX_REQUEST_SPAN,
    }
)
_HISTORICAL_METHOD_NAME = "reqHistoricalData"
_STOP_FILE_ENV_NAMES = ("ALPHA_FRONTIER_STOP_FILE", "FRONTIER_STOP_FILE")


@dataclass(frozen=True, slots=True)
class BackfillPlannedChunk:
    """Internal one-request/one-chunk drill plan derived from a manifest."""

    chunk_id: str
    request_spec: HistoricalRequestSpec


class BackfillArtifactStore(Protocol):
    """Local-only artifact sink for the resume drill."""

    def write_raw_payload(
        self,
        *,
        request_spec: HistoricalRequestSpec,
        chunk_id: str,
        payload: bytes,
        retrieved_at: datetime,
    ) -> RawPayloadWriteResult:
        """Write immutable raw payload bytes or an in-memory synthetic equivalent."""

    def write_ledger(self, ledger: HistoricalPullLedger) -> None:
        """Write a pull ledger record."""

    def write_provider_error(self, error: ProviderErrorRecord) -> None:
        """Write a provider-error or interruption ledger record."""


@dataclass(frozen=True, slots=True)
class LocalBackfillArtifactStore:
    """Local-only store for authorized drill raw bytes, ledgers, and errors."""

    layout_policy: RawDataLakeLayoutPolicy

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> LocalBackfillArtifactStore:
        """Build the local store from ``ALPHA_DATA_ROOT``."""

        return cls(layout_policy=RawDataLakeLayoutPolicy.from_env(env))

    @property
    def _metadata_root(self) -> Path:
        return (
            self.layout_policy.local_data_root_policy.data_root
            / "metadata"
            / ("ibkr_backfill_resume_drill")
        )

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
            raw_object_id=f"raw_ibkr_backfill_{chunk_id}",
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
        """Persist one drill ledger without overwriting an existing ledger."""

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


@dataclass(slots=True)
class InMemoryBackfillArtifactStore:
    """Synthetic artifact sink used by tests and ``--mode synthetic``."""

    raw_by_slot: dict[tuple[str, str, str], tuple[str, bytes]] = field(default_factory=dict)
    ledgers: list[HistoricalPullLedger] = field(default_factory=list)
    provider_errors: list[ProviderErrorRecord] = field(default_factory=list)

    def write_raw_payload(
        self,
        *,
        request_spec: HistoricalRequestSpec,
        chunk_id: str,
        payload: bytes,
        retrieved_at: datetime,
    ) -> RawPayloadWriteResult:
        """Record a synthetic content-addressed raw object and reject overwrite."""

        del retrieved_at
        digest = hashlib.sha256(payload).hexdigest()
        slot = (request_spec.source_id, request_spec.request_spec_id, chunk_id)
        existing = self.raw_by_slot.get(slot)
        if existing is not None and existing[0] != digest:
            msg = "raw object slot already has a different content hash; refusing overwrite"
            raise DataFoundationValidationError(msg)
        self.raw_by_slot.setdefault(slot, (digest, payload))
        return RawPayloadWriteResult(
            raw_object_ref="raw://sha256/" + digest,
            row_count=_count_payload_rows(payload),
            raw_object_id=f"raw_synthetic_backfill_{chunk_id}",
        )

    def write_ledger(self, ledger: HistoricalPullLedger) -> None:
        self.ledgers.append(ledger)

    def write_provider_error(self, error: ProviderErrorRecord) -> None:
        self.provider_errors.append(error)


@dataclass(frozen=True, slots=True)
class BackfillResumeDrillFixture:
    """Synthetic fixture payload for the local resume drill."""

    manifest: HistoricalRequestManifest
    payloads_by_chunk_id: Mapping[str, bytes]


@dataclass(frozen=True, slots=True)
class BackfillResumeDrillSummary:
    """Curated resume-drill summary with no provider payload or account data."""

    status: str
    batch_id: str
    access_mode: str
    external_call_attempted: bool
    interruption_simulated: bool
    chunks_planned: int
    chunks_completed_before_resume: int
    chunks_requested_initial: int
    chunks_requested_on_resume: int
    chunks_complete: int
    chunks_incomplete: int
    chunks_failed: int
    chunks_quarantined: int
    raw_objects_written: int
    provider_errors_logged: int
    manifest_id: str | None
    pacing_policy_id: str | None
    interrupted_ledger_status: str | None
    resumed_ledger_status: str | None
    initial_resume_token: str | None
    final_resume_token: str | None
    completed_chunk_ids_before_resume: tuple[str, ...]
    resumed_chunk_ids: tuple[str, ...]
    skipped_completed_chunk_ids: tuple[str, ...]
    coverage_status: str
    doctor: Mapping[str, object]

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable, redacted summary mapping."""

        return MappingProxyType(
            {
                "status": self.status,
                "batch_id": self.batch_id,
                "access_mode": self.access_mode,
                "external_call_attempted": self.external_call_attempted,
                "interruption_simulated": self.interruption_simulated,
                "chunks_planned": self.chunks_planned,
                "chunks_completed_before_resume": self.chunks_completed_before_resume,
                "chunks_requested_initial": self.chunks_requested_initial,
                "chunks_requested_on_resume": self.chunks_requested_on_resume,
                "chunks_complete": self.chunks_complete,
                "chunks_incomplete": self.chunks_incomplete,
                "chunks_failed": self.chunks_failed,
                "chunks_quarantined": self.chunks_quarantined,
                "raw_objects_written": self.raw_objects_written,
                "provider_errors_logged": self.provider_errors_logged,
                "manifest_id": self.manifest_id,
                "pacing_policy_id": self.pacing_policy_id,
                "interrupted_ledger_status": self.interrupted_ledger_status,
                "resumed_ledger_status": self.resumed_ledger_status,
                "initial_resume_token": self.initial_resume_token,
                "final_resume_token": self.final_resume_token,
                "completed_chunk_ids_before_resume": self.completed_chunk_ids_before_resume,
                "resumed_chunk_ids": self.resumed_chunk_ids,
                "skipped_completed_chunk_ids": self.skipped_completed_chunk_ids,
                "coverage_status": self.coverage_status,
                "doctor": self.doctor,
            }
        )


ReachabilityProbe = Callable[[IBKRConnectionProfile], SmokePullDoctorReport]
Clock = Callable[[], datetime]
PacingClock = Callable[[], float]
Sleeper = Callable[[float], None]


@dataclass(frozen=True, slots=True)
class _ChunkRequestOutcome:
    payload: bytes | None
    external_call_attempted: bool
    attempt_count: int
    error: ProviderErrorRecord | None


@dataclass(slots=True)
class _ProviderRequestRateLimiter:
    pacing_policy: RequestPacingPolicy
    clock: PacingClock
    sleep: Sleeper
    recent_requests: deque[tuple[float, int]] = field(default_factory=deque)
    last_request_at_by_key: dict[tuple[str, str, str, str, str], float] = field(
        default_factory=dict
    )

    def wait(self, request_spec: HistoricalRequestSpec) -> None:
        """Block until both duplicate-request and sliding-window limits allow a call."""

        request_key = _request_key_for_spec(request_spec)
        request_weight = self.pacing_policy.accounting_weight(request_spec.what_to_show)
        if request_weight > self.pacing_policy.max_requests_per_window:
            msg = "request accounting weight exceeds max_requests_per_window"
            raise DataFoundationValidationError(msg)

        now = self.clock()
        last_request_at = self.last_request_at_by_key.get(request_key)
        if last_request_at is not None:
            identical_delay = (
                self.pacing_policy.min_seconds_between_identical_requests
                - (now - last_request_at)
            )
            if identical_delay > 0:
                self.sleep(identical_delay)
                now = self.clock()

        self._sleep_until_window_allows(now=now, request_weight=request_weight)
        request_timestamp = self.clock()
        self._drop_expired_requests(request_timestamp)
        self.recent_requests.append((request_timestamp, request_weight))
        self.last_request_at_by_key[request_key] = request_timestamp

    def _sleep_until_window_allows(self, *, now: float, request_weight: int) -> None:
        current = now
        self._drop_expired_requests(current)
        while self._window_weight() + request_weight > self.pacing_policy.max_requests_per_window:
            oldest_timestamp = self.recent_requests[0][0]
            window_delay = self.pacing_policy.window_seconds - (current - oldest_timestamp)
            if window_delay <= 0:
                self._drop_expired_requests(current)
                continue
            self.sleep(window_delay)
            current = self.clock()
            self._drop_expired_requests(current)

    def _drop_expired_requests(self, now: float) -> None:
        while (
            self.recent_requests
            and now - self.recent_requests[0][0] >= self.pacing_policy.window_seconds
        ):
            self.recent_requests.popleft()

    def _window_weight(self) -> int:
        return sum(weight for _, weight in self.recent_requests)


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _repo_root() -> Path:
    return Path(__file__).resolve(strict=False).parents[4]


def _default_synthetic_fixture_path() -> Path:
    return _repo_root() / DEFAULT_SYNTHETIC_FIXTURE_RELATIVE_PATH


def _timestamp_id(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _normalize_id(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a non-empty identifier"
        raise DataFoundationValidationError(msg)
    token = value.strip()
    if not token or not token.replace("_", "").replace("-", "").isalnum():
        msg = f"{field_name} must be an alphanumeric identifier"
        raise DataFoundationValidationError(msg)
    return token


def _require_positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be a positive integer"
        raise DataFoundationValidationError(msg)
    if value <= 0:
        msg = f"{field_name} must be positive"
        raise DataFoundationValidationError(msg)
    return value


def _require_non_negative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be a non-negative integer"
        raise DataFoundationValidationError(msg)
    if value < 0:
        msg = f"{field_name} must be non-negative"
        raise DataFoundationValidationError(msg)
    return value


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


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = f"{field_name} must be a JSON object"
        raise DataFoundationValidationError(msg)
    return value


def _load_json_mapping(path: Path) -> Mapping[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return _require_mapping(payload, path.as_posix())


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


def _assert_no_stop_file(env: Mapping[str, str]) -> None:
    for env_name in _STOP_FILE_ENV_NAMES:
        configured = env.get(env_name)
        if configured and Path(configured).expanduser().exists():
            msg = f"active STOP file blocks DATA-P23 resume drill: {configured}"
            raise DataFoundationValidationError(msg)


def _coerce_access_mode(access_mode: DataAccessMode | str | None) -> DataAccessMode:
    if access_mode is None:
        return DataAccessMode.dry_run()
    if isinstance(access_mode, DataAccessMode):
        return access_mode
    return DataAccessMode.for_mode(access_mode)


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


def _chunk_id_for_request(request_spec: HistoricalRequestSpec) -> str:
    configured = request_spec.chunk_policy.get("chunk_id")
    if configured is not None:
        return _normalize_id(str(configured), "chunk_policy.chunk_id")
    derived = "hchunk_" + request_spec.request_spec_id.removeprefix("hrs_")
    return _normalize_id(derived, "derived chunk_id")


def _request_key_for_spec(
    request_spec: HistoricalRequestSpec,
) -> tuple[str, str, str, str, str]:
    return (
        request_spec.request_spec_id,
        request_spec.symbol_root,
        request_spec.contract_ref,
        request_spec.start_ts.isoformat(),
        request_spec.end_ts.isoformat(),
    )


def _normalize_bar_size(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _validated_max_request_spans(
    value: Mapping[str, timedelta] | None,
) -> Mapping[str, timedelta]:
    source = IBKR_MAX_REQUEST_SPAN_BY_BAR_SIZE if value is None else value
    normalized: dict[str, timedelta] = {}
    for bar_size, span in source.items():
        if not isinstance(span, timedelta) or span.total_seconds() <= 0:
            msg = "max_request_span_by_bar_size values must be positive timedeltas"
            raise DataFoundationValidationError(msg)
        normalized_bar_size = _normalize_bar_size(str(bar_size))
        if (
            normalized_bar_size == "1 min"
            and span > _IBKR_ONE_MIN_MAX_REQUEST_SPAN
        ):
            msg = (
                "max_request_span_by_bar_size['1 min'] must be <= 1 day; "
                "IBKR caps 1-minute historical requests at about one day per request"
            )
            raise DataFoundationValidationError(msg)
        normalized[normalized_bar_size] = span
    return MappingProxyType(normalized)


def _duration_for_window(start_ts: datetime, end_ts: datetime) -> str:
    seconds_float = (end_ts - start_ts).total_seconds()
    if seconds_float <= 0 or not seconds_float.is_integer():
        msg = "sub-window duration must be a positive whole number of seconds"
        raise DataFoundationValidationError(msg)
    seconds = int(seconds_float)
    # Dated-future probes showed IBKR can return only about 60 one-minute
    # bars for "1 D", while "86400 S" returns the full 1440-bar day.
    return f"{seconds} S"


def _subchunk_suffix(start_ts: datetime, end_ts: datetime) -> str:
    start_utc = start_ts.astimezone(UTC)
    end_utc = end_ts.astimezone(UTC)
    if (
        start_utc.hour == 0
        and start_utc.minute == 0
        and start_utc.second == 0
        and start_utc.microsecond == 0
        and end_utc - start_utc == timedelta(days=1)
    ):
        return start_utc.strftime("%Y%m%d")
    return (
        start_utc.strftime("%Y%m%dT%H%M%SZ")
        + "_"
        + end_utc.strftime("%Y%m%dT%H%M%SZ")
    )


def _subchunk_request_spec(
    *,
    plan: BackfillPlannedChunk,
    start_ts: datetime,
    end_ts: datetime,
    subchunk_index: int,
    suffix: str,
) -> HistoricalRequestSpec:
    request_spec = plan.request_spec
    chunk_id = _normalize_id(f"{plan.chunk_id}_{suffix}", "subchunk chunk_id")
    request_spec_id = _normalize_id(
        f"{request_spec.request_spec_id}_{suffix}",
        "subchunk request_spec_id",
    )
    chunk_policy = dict(request_spec.chunk_policy)
    chunk_policy.update(
        {
            "chunk_id": chunk_id,
            "parent_chunk_id": plan.chunk_id,
            "parent_request_spec_id": request_spec.request_spec_id,
            "subchunk_index": subchunk_index,
            "subchunk_start_ts": start_ts.isoformat(),
            "subchunk_end_ts": end_ts.isoformat(),
            "policy": "ibkr_1_min_dated_fut_subchunk",
        }
    )
    return replace(
        request_spec,
        request_spec_id=request_spec_id,
        duration=_duration_for_window(start_ts, end_ts),
        end_datetime_policy="explicit_dated_fut_sub_window_end_ts",
        start_ts=start_ts,
        end_ts=end_ts,
        chunk_policy=chunk_policy,
    )


def _expand_planned_chunk(
    plan: BackfillPlannedChunk,
    *,
    max_request_span_by_bar_size: Mapping[str, timedelta],
) -> tuple[BackfillPlannedChunk, ...]:
    request_spec = plan.request_spec
    max_span = max_request_span_by_bar_size.get(_normalize_bar_size(request_spec.bar_size))
    if max_span is None or request_spec.sec_type == "CONTFUT":
        return (plan,)

    subchunks: list[BackfillPlannedChunk] = []
    window_start = request_spec.start_ts
    index = 1
    while window_start < request_spec.end_ts:
        window_end = min(window_start + max_span, request_spec.end_ts)
        suffix = _subchunk_suffix(window_start, window_end)
        subchunk_spec = _subchunk_request_spec(
            plan=plan,
            start_ts=window_start,
            end_ts=window_end,
            subchunk_index=index,
            suffix=suffix,
        )
        subchunks.append(
            BackfillPlannedChunk(
                chunk_id=_chunk_id_for_request(subchunk_spec),
                request_spec=subchunk_spec,
            )
        )
        window_start = window_end
        index += 1

    if not subchunks:
        msg = "1 min dated FUT request must span at least one positive sub-window"
        raise DataFoundationValidationError(msg)
    return tuple(subchunks)


def _expand_planned_chunks(
    planned: Sequence[BackfillPlannedChunk],
    *,
    max_request_span_by_bar_size: Mapping[str, timedelta] | None,
) -> tuple[BackfillPlannedChunk, ...]:
    spans = _validated_max_request_spans(max_request_span_by_bar_size)
    expanded = tuple(
        subchunk
        for plan in planned
        for subchunk in _expand_planned_chunk(
            plan,
            max_request_span_by_bar_size=spans,
        )
    )
    chunk_ids = tuple(chunk.chunk_id for chunk in expanded)
    duplicate_chunk_ids = sorted(
        {chunk_id for chunk_id in chunk_ids if chunk_ids.count(chunk_id) > 1}
    )
    if duplicate_chunk_ids:
        msg = "expanded backfill plan contains duplicate chunk_id values: "
        raise DataFoundationValidationError(msg + ", ".join(duplicate_chunk_ids))
    request_spec_ids = tuple(chunk.request_spec.request_spec_id for chunk in expanded)
    duplicate_request_spec_ids = sorted(
        {
            request_spec_id
            for request_spec_id in request_spec_ids
            if request_spec_ids.count(request_spec_id) > 1
        }
    )
    if duplicate_request_spec_ids:
        msg = "expanded backfill plan contains duplicate request_spec_id values: "
        raise DataFoundationValidationError(msg + ", ".join(duplicate_request_spec_ids))
    return expanded


def _enforce_planned_chunk_limit(
    *,
    planned_count: int,
    max_chunks: int | None,
    enforce_expanded_max_chunks: bool,
) -> None:
    if max_chunks is None:
        return
    chunk_limit = _require_positive_int(max_chunks, "max_chunks")
    if enforce_expanded_max_chunks and planned_count > chunk_limit:
        msg = (
            "expanded backfill planned chunk_count exceeds max_chunks; "
            f"expanded={planned_count} max_chunks={chunk_limit}"
        )
        raise DataFoundationValidationError(msg)


def _planned_chunks_from_manifest(
    manifest: HistoricalRequestManifest,
) -> tuple[BackfillPlannedChunk, ...]:
    if manifest.chunk_count != len(manifest.request_specs):
        msg = "backfill drill requires one request_spec per planned chunk to avoid hidden gaps"
        raise DataFoundationValidationError(msg)

    planned = tuple(
        BackfillPlannedChunk(chunk_id=_chunk_id_for_request(request), request_spec=request)
        for request in manifest.request_specs
    )
    chunk_ids = tuple(chunk.chunk_id for chunk in planned)
    duplicates = sorted({chunk_id for chunk_id in chunk_ids if chunk_ids.count(chunk_id) > 1})
    if duplicates:
        msg = "backfill drill manifest contains duplicate chunk_id values: " + ", ".join(duplicates)
        raise DataFoundationValidationError(msg)
    return planned


def _validate_interrupt_after(value: int, *, planned_count: int) -> int:
    interrupt_after = _require_non_negative_int(value, "interrupt_after_chunks")
    if interrupt_after >= planned_count:
        return interrupt_after
    if planned_count < 2:
        msg = "resume drill requires at least two planned chunks when interruption is simulated"
        raise DataFoundationValidationError(msg)
    return interrupt_after


def _validated_execution_inputs(
    *,
    manifest: HistoricalRequestManifest | Mapping[str, object] | None,
    pacing_policy: RequestPacingPolicy | Mapping[str, object] | None,
    max_chunks: int | None,
    max_request_span_by_bar_size: Mapping[str, timedelta] | None,
    enforce_expanded_max_chunks: bool,
) -> tuple[HistoricalRequestManifest, RequestPacingPolicy, tuple[BackfillPlannedChunk, ...]]:
    manifest_record = require_validated_manifest_for_provider_pull(manifest)
    pacing_record = (
        load_default_pacing_policy()
        if pacing_policy is None
        else require_pacing_policy_for_provider_pull(pacing_policy)
    )
    forbid_naive_request_loop(pacing_record)
    if manifest_record.pacing_policy_id != pacing_record.pacing_policy_id:
        msg = "manifest pacing_policy_id must match the armed RequestPacingPolicy"
        raise DataFoundationValidationError(msg)
    if max_chunks is not None and manifest_record.chunk_count > _require_positive_int(
        max_chunks,
        "max_chunks",
    ):
        msg = "backfill manifest chunk_count exceeds max_chunks"
        raise DataFoundationValidationError(msg)
    manifest_planned = _planned_chunks_from_manifest(manifest_record)
    planned = _expand_planned_chunks(
        manifest_planned,
        max_request_span_by_bar_size=max_request_span_by_bar_size,
    )
    _enforce_planned_chunk_limit(
        planned_count=len(planned),
        max_chunks=max_chunks,
        enforce_expanded_max_chunks=enforce_expanded_max_chunks,
    )
    return manifest_record, pacing_record, planned


def _provider_request_id(*, stage: str, chunk_id: str, timestamp: datetime) -> str:
    return f"ibkr_backfill_{stage}_{chunk_id}_{_timestamp_id(timestamp)}"


def _interruption_error_record(
    *,
    chunk_id: str,
    request_id: str,
    timestamp: datetime,
) -> ProviderErrorRecord:
    return ProviderErrorRecord(
        error_id=f"perr_backfill_interrupted_{chunk_id}",
        provider="IBKR",
        request_id=request_id,
        chunk_id=chunk_id,
        error_code="LOCAL_INTERRUPTION_DRILL",
        error_message="local interruption drill marker; no provider payload captured",
        retryable=True,
        attempt=1,
        timestamp=timestamp,
        resolution=ProviderErrorResolution.INCOMPLETE_RESPONSE_RECORDED,
    )


def _provider_error_record(
    *,
    exc: BaseException,
    request_id: str,
    chunk_id: str,
    timestamp: datetime,
    stage: str,
    attempt: int,
    retryable: bool,
    resolution: ProviderErrorResolution,
) -> ProviderErrorRecord:
    return ProviderErrorRecord(
        error_id=f"perr_backfill_{stage}_{chunk_id}",
        provider="IBKR",
        request_id=request_id,
        chunk_id=chunk_id,
        error_code=type(exc).__name__,
        error_message=_redacted_error_message(exc),
        retryable=retryable,
        attempt=attempt,
        timestamp=timestamp,
        resolution=resolution,
    )


def _interrupted_chunk_record(
    *,
    plan: BackfillPlannedChunk,
    request_id: str,
    error_ref: str,
    timestamp: datetime,
) -> HistoricalChunkRecord:
    return HistoricalChunkRecord(
        chunk_id=plan.chunk_id,
        request_spec_id=plan.request_spec.request_spec_id,
        symbol_root=plan.request_spec.symbol_root,
        contract_ref=plan.request_spec.contract_ref,
        start_ts=plan.request_spec.start_ts,
        end_ts=plan.request_spec.end_ts,
        status=HistoricalChunkStatus.INCOMPLETE,
        attempt_count=1,
        provider_request_id=request_id,
        raw_object_ref=None,
        row_count=0,
        error_ref=error_ref,
        retrieved_at=timestamp,
    )


def _complete_chunk_record(
    *,
    plan: BackfillPlannedChunk,
    request_id: str,
    raw_write: RawPayloadWriteResult,
    retrieved_at: datetime,
    attempt_count: int,
) -> HistoricalChunkRecord:
    return HistoricalChunkRecord(
        chunk_id=plan.chunk_id,
        request_spec_id=plan.request_spec.request_spec_id,
        symbol_root=plan.request_spec.symbol_root,
        contract_ref=plan.request_spec.contract_ref,
        start_ts=plan.request_spec.start_ts,
        end_ts=plan.request_spec.end_ts,
        status=HistoricalChunkStatus.COMPLETE,
        attempt_count=attempt_count,
        provider_request_id=request_id,
        raw_object_ref=raw_write.raw_object_ref,
        row_count=raw_write.row_count,
        error_ref=None,
        retrieved_at=retrieved_at,
    )


def _quarantined_chunk_record(
    *,
    plan: BackfillPlannedChunk,
    request_id: str,
    error_ref: str,
    timestamp: datetime,
    attempt_count: int,
) -> HistoricalChunkRecord:
    return HistoricalChunkRecord(
        chunk_id=plan.chunk_id,
        request_spec_id=plan.request_spec.request_spec_id,
        symbol_root=plan.request_spec.symbol_root,
        contract_ref=plan.request_spec.contract_ref,
        start_ts=plan.request_spec.start_ts,
        end_ts=plan.request_spec.end_ts,
        status=HistoricalChunkStatus.QUARANTINED,
        attempt_count=attempt_count,
        provider_request_id=request_id,
        raw_object_ref=None,
        row_count=None,
        error_ref=error_ref,
        retrieved_at=None,
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


def _fixture_manifest_from_seed(seed: Mapping[str, object]) -> HistoricalRequestManifest:
    request_specs = tuple(
        HistoricalRequestSpec.from_mapping(_require_mapping(item, "request_specs[]"))
        for item in seed.get("request_specs", ())
    )
    return HistoricalRequestManifest.create(
        manifest_id=str(seed["manifest_id"]),
        batch_id=str(seed["batch_id"]),
        request_specs=request_specs,
        chunk_count=_require_positive_int(seed["chunk_count"], "chunk_count"),
        expected_coverage=_require_mapping(seed["expected_coverage"], "expected_coverage"),
        pacing_policy_id=str(seed["pacing_policy_id"]),
        data_root=str(seed["data_root"]),
        created_by=str(seed["created_by"]),
        created_at=_parse_aware_datetime(seed["created_at"], "created_at"),
    )


def load_synthetic_backfill_resume_fixture(
    path: Path | None = None,
) -> BackfillResumeDrillFixture:
    """Load the tiny synthetic DATA-P23 resume-drill fixture."""

    fixture_path = path or _default_synthetic_fixture_path()
    values = _load_json_mapping(fixture_path)
    manifest_seed = _require_mapping(values["manifest_seed"], "manifest_seed")
    raw_payloads = _require_mapping(values["payloads_by_chunk_id"], "payloads_by_chunk_id")
    payloads_by_chunk_id = {
        _normalize_id(chunk_id, "payloads_by_chunk_id key"): _payload_to_bytes(payload)
        for chunk_id, payload in raw_payloads.items()
    }
    return BackfillResumeDrillFixture(
        manifest=_fixture_manifest_from_seed(manifest_seed),
        payloads_by_chunk_id=MappingProxyType(payloads_by_chunk_id),
    )


def _payload_for_synthetic_chunk(
    *,
    payloads_by_chunk_id: Mapping[str, bytes],
    chunk_id: str,
) -> bytes:
    payload = payloads_by_chunk_id.get(chunk_id)
    if payload is None:
        msg = f"synthetic payload missing for planned chunk {chunk_id}"
        raise DataFoundationValidationError(msg)
    return payload


def _request_chunk_payload(
    *,
    plan: BackfillPlannedChunk,
    access_mode: DataAccessMode,
    boundary: IBKRReadOnlyApiBoundary | None,
    env: Mapping[str, str],
    ci: bool | None,
    synthetic_payloads: Mapping[str, bytes] | None,
    rate_limiter: _ProviderRequestRateLimiter | None,
) -> tuple[bytes, bool]:
    if access_mode.mode == "synthetic":
        if synthetic_payloads is None:
            msg = "synthetic mode requires payloads_by_chunk_id"
            raise DataFoundationValidationError(msg)
        return (
            _payload_for_synthetic_chunk(
                payloads_by_chunk_id=synthetic_payloads,
                chunk_id=plan.chunk_id,
            ),
            False,
        )

    if boundary is None or _HISTORICAL_METHOD_NAME not in boundary.read_only_methods:
        msg = "missing registered read-only historical data handler blocks resume drill"
        raise DataFoundationValidationError(msg)
    if rate_limiter is not None:
        rate_limiter.wait(plan.request_spec)
    response = boundary.request_historical_data(plan.request_spec, env=env, ci=ci)
    return _payload_to_bytes(response), True


def _request_chunk_payload_with_retry(
    *,
    plan: BackfillPlannedChunk,
    request_id: str,
    access_mode: DataAccessMode,
    boundary: IBKRReadOnlyApiBoundary | None,
    env: Mapping[str, str],
    ci: bool | None,
    synthetic_payloads: Mapping[str, bytes] | None,
    pacing_policy: RequestPacingPolicy,
    rate_limiter: _ProviderRequestRateLimiter | None,
    sleep: Sleeper,
    timestamp: datetime,
    stage: str,
) -> _ChunkRequestOutcome:
    attempt = 1
    external_call_attempted = False
    retry_provider_exceptions = access_mode.mode == "authorized_pull"
    while True:
        try:
            if retry_provider_exceptions:
                external_call_attempted = True
            payload, external_called = _request_chunk_payload(
                plan=plan,
                access_mode=access_mode,
                boundary=boundary,
                env=env,
                ci=ci,
                synthetic_payloads=synthetic_payloads,
                rate_limiter=rate_limiter,
            )
            return _ChunkRequestOutcome(
                payload=payload,
                external_call_attempted=external_call_attempted or external_called,
                attempt_count=attempt,
                error=None,
            )
        except DataFoundationValidationError as exc:
            if retry_provider_exceptions:
                # Guard/config failures are deterministic and should abort the run;
                # provider/runtime failures can still retry and quarantine by chunk.
                raise
            caught_exc = exc
        except Exception as exc:
            caught_exc = exc

        next_attempt = attempt + 1
        if retry_provider_exceptions and pacing_policy.can_retry_attempt(next_attempt):
            sleep(pacing_policy.backoff_delay_seconds(attempt))
            attempt = next_attempt
            continue

        retryable = retry_provider_exceptions
        resolution = (
            ProviderErrorResolution.RETRY_EXHAUSTED
            if retryable
            else ProviderErrorResolution.QUARANTINED_NON_RETRYABLE
        )
        return _ChunkRequestOutcome(
            payload=None,
            external_call_attempted=external_call_attempted,
            attempt_count=attempt,
            error=_provider_error_record(
                exc=caught_exc,
                request_id=request_id,
                chunk_id=plan.chunk_id,
                timestamp=timestamp,
                stage=stage,
                attempt=attempt,
                retryable=retryable,
                resolution=resolution,
            ),
        )


def _empty_summary(
    *,
    status: str,
    batch_id: str,
    access_mode: DataAccessMode,
    doctor: SmokePullDoctorReport,
    manifest_id: str | None = None,
    pacing_policy_id: str | None = None,
    chunks_planned: int = 0,
) -> BackfillResumeDrillSummary:
    return BackfillResumeDrillSummary(
        status=status,
        batch_id=batch_id,
        access_mode=access_mode.mode,
        external_call_attempted=False,
        interruption_simulated=False,
        chunks_planned=chunks_planned,
        chunks_completed_before_resume=0,
        chunks_requested_initial=0,
        chunks_requested_on_resume=0,
        chunks_complete=0,
        chunks_incomplete=0,
        chunks_failed=0,
        chunks_quarantined=0,
        raw_objects_written=0,
        provider_errors_logged=0,
        manifest_id=manifest_id,
        pacing_policy_id=pacing_policy_id,
        interrupted_ledger_status=None,
        resumed_ledger_status=None,
        initial_resume_token=None,
        final_resume_token=None,
        completed_chunk_ids_before_resume=(),
        resumed_chunk_ids=(),
        skipped_completed_chunk_ids=(),
        coverage_status="not_quality_checked",
        doctor=doctor.to_mapping(),
    )


def _summary_status_for_final_ledger(
    *,
    access_mode: DataAccessMode,
    final_status: HistoricalPullLedgerStatus,
) -> str:
    if access_mode.mode == "synthetic" and final_status is HistoricalPullLedgerStatus.COMPLETE:
        return "SYNTHETIC_COMPLETE"
    if final_status is HistoricalPullLedgerStatus.COMPLETE:
        return final_status.value
    return HistoricalPullLedgerStatus.INCOMPLETE.value


def run_local_backfill_resume_drill(
    *,
    manifest: HistoricalRequestManifest | Mapping[str, object] | None = None,
    pacing_policy: RequestPacingPolicy | Mapping[str, object] | None = None,
    boundary: IBKRReadOnlyApiBoundary | None = None,
    access_mode: DataAccessMode | str | None = None,
    env: Mapping[str, str] | None = None,
    ci: bool | None = None,
    max_chunks: int | None = DEFAULT_MAX_DRILL_CHUNKS,
    enforce_expanded_max_chunks: bool = True,
    max_request_span_by_bar_size: Mapping[str, timedelta] | None = None,
    interrupt_after_chunks: int = 1,
    batch: str = DEFAULT_BACKFILL_BATCH_ID,
    artifact_store: BackfillArtifactStore | None = None,
    reachability_probe: ReachabilityProbe | None = None,
    synthetic_payloads_by_chunk_id: Mapping[str, bytes] | None = None,
    now: Clock = _now_utc,
    clock: PacingClock = time.monotonic,
    sleep: Sleeper = time.sleep,
    execute: bool = False,
) -> BackfillResumeDrillSummary:
    """Run dry-run preflight, synthetic drill, or authorized local resume drill."""

    source = os.environ if env is None else env
    access = _coerce_access_mode(access_mode)
    timestamp = now()
    profile = IBKRConnectionProfile.from_env(source)
    IBKRClientIdPolicy.default().validate_client_id(profile.client_id)
    dry_doctor = _doctor_not_probed(profile)

    if not execute or access.mode == "dry_run":
        manifest_id = None
        pacing_policy_id = None
        planned_count = 0
        if manifest is not None:
            manifest_record, pacing_record, planned = _validated_execution_inputs(
                manifest=manifest,
                pacing_policy=pacing_policy,
                max_chunks=max_chunks,
                max_request_span_by_bar_size=max_request_span_by_bar_size,
                enforce_expanded_max_chunks=enforce_expanded_max_chunks,
            )
            manifest_id = manifest_record.manifest_id
            pacing_policy_id = pacing_record.pacing_policy_id
            planned_count = len(planned)
        return _empty_summary(
            status="DRY_RUN",
            batch_id=batch,
            access_mode=access,
            doctor=dry_doctor,
            manifest_id=manifest_id,
            pacing_policy_id=pacing_policy_id,
            chunks_planned=planned_count,
        )

    access.validate_runtime_env(source, ci=ci)
    if access.mode not in {"synthetic", "authorized_pull"}:
        msg = f"DataAccessMode {access.mode!r} is not supported by the resume drill"
        raise DataFoundationValidationError(msg)

    manifest_record, pacing_record, planned = _validated_execution_inputs(
        manifest=manifest,
        pacing_policy=pacing_policy,
        max_chunks=max_chunks,
        max_request_span_by_bar_size=max_request_span_by_bar_size,
        enforce_expanded_max_chunks=enforce_expanded_max_chunks,
    )
    interrupt_after = _validate_interrupt_after(
        interrupt_after_chunks,
        planned_count=len(planned),
    )

    if access.mode == "authorized_pull":
        if not access.allows_external_api:
            msg = f"DataAccessMode {access.mode!r} forbids external API calls"
            raise DataFoundationValidationError(msg)
        if not access.allows_raw_write:
            msg = f"DataAccessMode {access.mode!r} forbids raw local writes"
            raise DataFoundationValidationError(msg)
        _assert_no_stop_file(source)
        if not source.get("ALPHA_DATA_ROOT"):
            msg = "ALPHA_DATA_ROOT is required for authorized resume-drill local outputs"
            raise DataFoundationValidationError(msg)
        probe = reachability_probe or probe_ibkr_host_port
        doctor = probe(profile)
        if not doctor.reachable:
            msg = "connection doctor failed; refusing resume drill before provider call"
            raise DataFoundationValidationError(msg)
        drill_boundary = _coerce_boundary(
            boundary=boundary,
            profile=doctor.profile,
            access_mode=access,
        )
        if _HISTORICAL_METHOD_NAME not in drill_boundary.read_only_methods:
            msg = "missing registered read-only historical data handler blocks resume drill"
            raise DataFoundationValidationError(msg)
        store = artifact_store or LocalBackfillArtifactStore.from_env(source)
    else:
        doctor = dry_doctor
        drill_boundary = None
        store = artifact_store or InMemoryBackfillArtifactStore()

    rate_limiter = (
        None
        if access.mode == "synthetic"
        else _ProviderRequestRateLimiter(
            pacing_policy=pacing_record,
            clock=clock,
            sleep=sleep,
        )
    )
    expected_chunk_ids = tuple(chunk.chunk_id for chunk in planned)
    if access.mode == "synthetic":
        if synthetic_payloads_by_chunk_id is None:
            msg = "synthetic mode requires payloads_by_chunk_id"
            raise DataFoundationValidationError(msg)
        missing_payloads = tuple(
            chunk_id
            for chunk_id in expected_chunk_ids
            if chunk_id not in synthetic_payloads_by_chunk_id
        )
        if missing_payloads:
            msg = "synthetic payloads missing planned chunks: " + ", ".join(missing_payloads)
            raise DataFoundationValidationError(msg)
    timestamp_token = _timestamp_id(timestamp)
    interrupted_pull_id = f"hpl_ibkr_backfill_{batch}_{timestamp_token}_interrupted"
    resumed_pull_id = f"hpl_ibkr_backfill_{batch}_{timestamp_token}_resumed"

    interrupted_records: list[HistoricalChunkRecord] = []
    raw_objects_written = 0
    provider_errors_logged = 0
    external_call_attempted = False
    initial_requested_chunk_ids: list[str] = []

    for index, plan in enumerate(planned):
        request_id = _provider_request_id(
            stage="initial",
            chunk_id=plan.chunk_id,
            timestamp=timestamp,
        )
        if index >= interrupt_after:
            error = _interruption_error_record(
                chunk_id=plan.chunk_id,
                request_id=request_id,
                timestamp=timestamp,
            )
            store.write_provider_error(error)
            provider_errors_logged += 1
            interrupted_records.append(
                _interrupted_chunk_record(
                    plan=plan,
                    request_id=request_id,
                    error_ref=error.error_id,
                    timestamp=timestamp,
                )
            )
            continue

        initial_requested_chunk_ids.append(plan.chunk_id)
        outcome = _request_chunk_payload_with_retry(
            plan=plan,
            request_id=request_id,
            access_mode=access,
            boundary=drill_boundary,
            env=source,
            ci=ci,
            synthetic_payloads=synthetic_payloads_by_chunk_id,
            pacing_policy=pacing_record,
            rate_limiter=rate_limiter,
            sleep=sleep,
            timestamp=timestamp,
            stage="initial",
        )
        external_call_attempted = (
            external_call_attempted or outcome.external_call_attempted
        )
        if outcome.error is not None:
            store.write_provider_error(outcome.error)
            provider_errors_logged += 1
            interrupted_records.append(
                _quarantined_chunk_record(
                    plan=plan,
                    request_id=request_id,
                    error_ref=outcome.error.error_id,
                    timestamp=timestamp,
                    attempt_count=outcome.attempt_count,
                )
            )
            continue

        if outcome.payload is None:
            msg = "chunk request completed without payload or provider error"
            raise DataFoundationValidationError(msg)
        raw_write = store.write_raw_payload(
            request_spec=plan.request_spec,
            chunk_id=plan.chunk_id,
            payload=outcome.payload,
            retrieved_at=timestamp,
        )
        raw_objects_written += 1
        interrupted_records.append(
            _complete_chunk_record(
                plan=plan,
                request_id=request_id,
                raw_write=raw_write,
                retrieved_at=timestamp,
                attempt_count=outcome.attempt_count,
            )
        )

    interrupted_ledger = _ledger_for_chunks(
        pull_id=interrupted_pull_id,
        manifest_id=manifest_record.manifest_id,
        chunks=interrupted_records,
        expected_chunk_ids=expected_chunk_ids,
        started_at=timestamp,
        finished_at=timestamp,
    )
    store.write_ledger(interrupted_ledger)
    resume_token = interrupted_ledger.resume_token
    interrupted_ledger.pending_chunk_ids_for_resume(resume_token)
    completed_before_resume = interrupted_ledger.completed_chunk_ids()

    records_by_chunk_id = {record.chunk_id: record for record in interrupted_records}
    plan_by_chunk_id = {plan.chunk_id: plan for plan in planned}
    resumed_records: list[HistoricalChunkRecord] = []
    resumed_chunk_ids: list[str] = []

    for chunk_id in expected_chunk_ids:
        prior = records_by_chunk_id[chunk_id]
        if prior.status is HistoricalChunkStatus.COMPLETE:
            resumed_records.append(prior)
            continue
        if prior.status in {HistoricalChunkStatus.FAILED, HistoricalChunkStatus.QUARANTINED}:
            resumed_records.append(prior)
            continue

        plan = plan_by_chunk_id[chunk_id]
        request_id = _provider_request_id(
            stage="resume",
            chunk_id=plan.chunk_id,
            timestamp=timestamp,
        )
        resumed_chunk_ids.append(chunk_id)
        outcome = _request_chunk_payload_with_retry(
            plan=plan,
            request_id=request_id,
            access_mode=access,
            boundary=drill_boundary,
            env=source,
            ci=ci,
            synthetic_payloads=synthetic_payloads_by_chunk_id,
            pacing_policy=pacing_record,
            rate_limiter=rate_limiter,
            sleep=sleep,
            timestamp=timestamp,
            stage="resume",
        )
        external_call_attempted = (
            external_call_attempted or outcome.external_call_attempted
        )
        if outcome.error is not None:
            store.write_provider_error(outcome.error)
            provider_errors_logged += 1
            resumed_records.append(
                _quarantined_chunk_record(
                    plan=plan,
                    request_id=request_id,
                    error_ref=outcome.error.error_id,
                    timestamp=timestamp,
                    attempt_count=prior.attempt_count + outcome.attempt_count,
                )
            )
            continue
        if outcome.payload is None:
            msg = "resumed chunk request completed without payload or provider error"
            raise DataFoundationValidationError(msg)
        raw_write = store.write_raw_payload(
            request_spec=plan.request_spec,
            chunk_id=plan.chunk_id,
            payload=outcome.payload,
            retrieved_at=timestamp,
        )
        raw_objects_written += 1
        resumed_records.append(
            _complete_chunk_record(
                plan=plan,
                request_id=request_id,
                raw_write=raw_write,
                retrieved_at=timestamp,
                attempt_count=prior.attempt_count + outcome.attempt_count,
            )
        )

    final_ledger = _ledger_for_chunks(
        pull_id=resumed_pull_id,
        manifest_id=manifest_record.manifest_id,
        chunks=resumed_records,
        expected_chunk_ids=expected_chunk_ids,
        started_at=timestamp,
        finished_at=timestamp,
    )
    store.write_ledger(final_ledger)
    coverage = final_ledger.coverage_summary
    status = _summary_status_for_final_ledger(
        access_mode=access,
        final_status=final_ledger.status,
    )

    return BackfillResumeDrillSummary(
        status=status,
        batch_id=batch,
        access_mode=access.mode,
        external_call_attempted=external_call_attempted,
        interruption_simulated=interrupt_after < len(planned),
        chunks_planned=len(planned),
        chunks_completed_before_resume=len(completed_before_resume),
        chunks_requested_initial=len(initial_requested_chunk_ids),
        chunks_requested_on_resume=len(resumed_chunk_ids),
        chunks_complete=int(coverage["complete_count"]),
        chunks_incomplete=int(coverage["incomplete_count"]),
        chunks_failed=int(coverage["failed_count"]),
        chunks_quarantined=int(coverage["quarantined_count"]),
        raw_objects_written=raw_objects_written,
        provider_errors_logged=provider_errors_logged,
        manifest_id=manifest_record.manifest_id,
        pacing_policy_id=pacing_record.pacing_policy_id,
        interrupted_ledger_status=interrupted_ledger.status.value,
        resumed_ledger_status=final_ledger.status.value,
        initial_resume_token=resume_token,
        final_resume_token=final_ledger.resume_token,
        completed_chunk_ids_before_resume=completed_before_resume,
        resumed_chunk_ids=tuple(resumed_chunk_ids),
        skipped_completed_chunk_ids=completed_before_resume,
        coverage_status=str(coverage["quality_status"]),
        doctor=doctor.to_mapping(),
    )


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DATA-P23 guarded local backfill resume-drill preflight",
    )
    parser.add_argument(
        "--mode",
        choices=("dry_run", "synthetic", "authorized_pull"),
        default="dry_run",
    )
    parser.add_argument("--batch", default=DEFAULT_BACKFILL_BATCH_ID)
    parser.add_argument("--max-chunks", type=int, default=DEFAULT_MAX_DRILL_CHUNKS)
    parser.add_argument("--interrupt-after-chunks", type=int, default=1)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--pacing-policy", type=Path)
    parser.add_argument("--max-request-span-days", type=float)
    parser.add_argument("--synthetic-fixture", type=Path)
    return parser.parse_args(argv)


def _max_request_span_override(days: float | None) -> Mapping[str, timedelta] | None:
    if days is None:
        return None
    if days <= 0:
        msg = "--max-request-span-days must be positive"
        raise DataFoundationValidationError(msg)
    span = timedelta(days=days)
    if span > _IBKR_ONE_MIN_MAX_REQUEST_SPAN:
        msg = (
            "--max-request-span-days for 1 min bars must be <= 1 day; "
            "IBKR caps 1-minute historical requests at about one day per request"
        )
        raise DataFoundationValidationError(msg)
    return MappingProxyType({"1 min": span})


def _summary_stdout(summary: BackfillResumeDrillSummary) -> None:
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
    """CLI for ``python -m alpha_system.data.ibkr.backfill``."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    fixture: BackfillResumeDrillFixture | None = None
    manifest: HistoricalRequestManifest | None = None
    synthetic_payloads: Mapping[str, bytes] | None = None
    if args.mode == "synthetic" and args.manifest is None:
        fixture = load_synthetic_backfill_resume_fixture(args.synthetic_fixture)
        manifest = fixture.manifest
        synthetic_payloads = fixture.payloads_by_chunk_id
    elif args.manifest is not None:
        manifest = HistoricalRequestManifest.from_mapping(_load_json_mapping(args.manifest))

    pacing_policy = (
        RequestPacingPolicy.from_mapping(_load_json_mapping(args.pacing_policy))
        if args.pacing_policy is not None
        else None
    )
    try:
        summary = run_local_backfill_resume_drill(
            manifest=manifest,
            pacing_policy=pacing_policy,
            access_mode=DataAccessMode.for_mode(args.mode),
            max_chunks=args.max_chunks,
            max_request_span_by_bar_size=_max_request_span_override(
                args.max_request_span_days
            ),
            interrupt_after_chunks=args.interrupt_after_chunks,
            batch=args.batch,
            synthetic_payloads_by_chunk_id=synthetic_payloads,
            execute=args.mode != "dry_run",
        )
    except DataFoundationValidationError as exc:
        _blocked_stdout(exc)
        return 2
    _summary_stdout(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
