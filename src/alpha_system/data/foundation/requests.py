"""Historical request specs, manifests, pacing, and resume ledgers.

DATA-P07 owns request planning. DATA-P08 owns pacing, chunk lifecycle,
provider-error, and pull-resume ledger records. This module performs no provider
calls, opens no sockets, imports no IBKR client library, writes no market data,
and does not authorize a pull. Later DATA-P09+ phases own raw storage,
ingestion runs, parsing, canonicalization, and quality/version gates.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from math import isfinite
from types import MappingProxyType

from alpha_system.data.foundation.ibkr import IBKRClientIdPolicy
from alpha_system.data.foundation.instruments import load_futures_instrument_master_by_root
from alpha_system.data.foundation.sources import (
    DEFAULT_ALLOWED_SUBDIRS,
    DEFAULT_FORBIDDEN_REPO_PATHS,
    DEFAULT_MAX_FILE_POLICY,
    DataFoundationValidationError,
    LocalDataRootPolicy,
)

REQUIRED_HISTORICAL_REQUEST_SPEC_FIELDS: tuple[str, ...] = (
    "request_spec_id",
    "source_id",
    "symbol_root",
    "contract_ref",
    "sec_type",
    "exchange",
    "currency",
    "bar_size",
    "what_to_show",
    "use_rth",
    "duration",
    "end_datetime_policy",
    "start_ts",
    "end_ts",
    "chunk_policy",
    "client_id",
)

REQUIRED_HISTORICAL_REQUEST_MANIFEST_FIELDS: tuple[str, ...] = (
    "manifest_id",
    "batch_id",
    "request_specs",
    "chunk_count",
    "expected_coverage",
    "pacing_policy_id",
    "data_root",
    "created_by",
    "created_at",
    "manifest_hash",
)

REQUIRED_REQUEST_PACING_POLICY_FIELDS: tuple[str, ...] = (
    "pacing_policy_id",
    "min_seconds_between_identical_requests",
    "max_requests_per_window",
    "window_seconds",
    "bid_ask_counts_double",
    "backoff_policy",
    "source",
)

REQUIRED_HISTORICAL_CHUNK_RECORD_FIELDS: tuple[str, ...] = (
    "chunk_id",
    "request_spec_id",
    "symbol_root",
    "contract_ref",
    "start_ts",
    "end_ts",
    "status",
    "attempt_count",
    "provider_request_id",
    "raw_object_ref",
    "row_count",
    "error_ref",
    "retrieved_at",
)

REQUIRED_HISTORICAL_PULL_LEDGER_FIELDS: tuple[str, ...] = (
    "pull_id",
    "manifest_id",
    "chunk_records",
    "started_at",
    "finished_at",
    "status",
    "resume_token",
    "coverage_summary",
    "error_summary",
)

REQUIRED_PROVIDER_ERROR_RECORD_FIELDS: tuple[str, ...] = (
    "error_id",
    "provider",
    "request_id",
    "chunk_id",
    "error_code",
    "error_message",
    "retryable",
    "attempt",
    "timestamp",
    "resolution",
)

HISTORICAL_REQUEST_MANIFEST_HASH_SCHEMA = "alpha_system.historical_request_manifest.v1"
HISTORICAL_PULL_RESUME_TOKEN_SCHEMA = "alpha_system.historical_pull_resume_token.v1"

ALLOWED_HISTORICAL_SEC_TYPES: frozenset[str] = frozenset({"FUT", "CONTFUT"})
_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_RAW_OBJECT_REF_PATTERN = re.compile(r"^(sha256:|raw://sha256/)[0-9a-f]{64}$")
_TO_BE_VERIFIED_STATUS = "to_be_verified"
_FORBIDDEN_QUALITY_CLAIM_TOKENS: frozenset[str] = frozenset(
    {
        "quality_passed",
        "ready",
        "ready_for_research",
        "versioned",
        "quality_checked",
        "accepted",
    }
)


class HistoricalRequestLifecycleState(StrEnum):
    """DATA-P07 request lifecycle states encoded before any provider call."""

    NOT_REQUESTED = "NOT_REQUESTED"
    REQUEST_PLANNED = "REQUEST_PLANNED"
    REQUEST_AUTHORIZED = "REQUEST_AUTHORIZED"


class HistoricalChunkStatus(StrEnum):
    """Lifecycle states for one planned historical chunk."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"


class HistoricalPullLedgerStatus(StrEnum):
    """Ledger lifecycle states derived from reconciled chunk statuses."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"


class ProviderErrorResolution(StrEnum):
    """Allowed provider-error dispositions without unclassified fatal claims."""

    RETRY_BACKOFF_SCHEDULED = "RETRY_BACKOFF_SCHEDULED"
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED"
    INCOMPLETE_RESPONSE_RECORDED = "INCOMPLETE_RESPONSE_RECORDED"
    QUARANTINED_NON_RETRYABLE = "QUARANTINED_NON_RETRYABLE"


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    normalized = value.strip()
    if not normalized:
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    return normalized


def _normalize_id(value: object, field_name: str) -> str:
    token = _require_text(value, field_name)
    if not token.replace("_", "").replace("-", "").isalnum():
        msg = f"{field_name} must be an alphanumeric identifier"
        raise DataFoundationValidationError(msg)
    return token


def _require_reference(value: object, field_name: str) -> str:
    reference = _require_text(value, field_name)
    if "\n" in reference or "\r" in reference:
        msg = f"{field_name} must be a single-line reference"
        raise DataFoundationValidationError(msg)
    if reference[0] in {"{", "["}:
        msg = f"{field_name} must be a reference, not an embedded payload"
        raise DataFoundationValidationError(msg)
    return reference


def _parse_aware_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = _require_text(value, field_name)
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be an ISO-8601 timezone-aware datetime"
            raise DataFoundationValidationError(msg) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = f"{field_name} must be timezone-aware"
        raise DataFoundationValidationError(msg)
    return parsed


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        msg = f"{field_name} must be a boolean"
        raise DataFoundationValidationError(msg)
    return value


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


def _require_optional_non_negative_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    return _require_non_negative_int(value, field_name)


def _require_positive_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float | Decimal):
        msg = f"{field_name} must be a positive finite number"
        raise DataFoundationValidationError(msg)
    if isinstance(value, Decimal) and not value.is_finite():
        msg = f"{field_name} must be a positive finite number"
        raise DataFoundationValidationError(msg)
    normalized = float(value)
    if not isfinite(normalized) or normalized <= 0:
        msg = f"{field_name} must be a positive finite number"
        raise DataFoundationValidationError(msg)
    return normalized


def _parse_optional_aware_datetime(value: object, field_name: str) -> datetime | None:
    if value is None:
        return None
    return _parse_aware_datetime(value, field_name)


def _normalize_optional_reference(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_reference(value, field_name)


def _normalize_raw_object_ref(value: object) -> str:
    ref = _require_reference(value, "raw_object_ref").lower()
    if not _RAW_OBJECT_REF_PATTERN.fullmatch(ref):
        msg = (
            "raw_object_ref must be an immutable content-addressed reference "
            "using sha256:<digest> or raw://sha256/<digest>"
        )
        raise DataFoundationValidationError(msg)
    return ref


def _normalize_optional_raw_object_ref(value: object) -> str | None:
    if value is None:
        return None
    return _normalize_raw_object_ref(value)


def _normalize_source_id(value: object) -> str:
    source_id = _normalize_id(value, "source_id")
    if not source_id.startswith("dsrc_"):
        msg = "source_id must use the dsrc_ prefix"
        raise DataFoundationValidationError(msg)
    return source_id


def _normalize_symbol_root(value: object) -> str:
    symbol_root = _require_text(value, "symbol_root").upper()
    if not symbol_root.isalnum():
        msg = "symbol_root must be alphanumeric"
        raise DataFoundationValidationError(msg)
    masters = load_futures_instrument_master_by_root()
    if symbol_root not in masters:
        msg = f"symbol_root {symbol_root!r} is not in the futures instrument master"
        raise DataFoundationValidationError(msg)
    return symbol_root


def _normalize_sec_type(value: object) -> str:
    sec_type = _require_text(value, "sec_type").upper()
    if sec_type not in ALLOWED_HISTORICAL_SEC_TYPES:
        allowed = ", ".join(sorted(ALLOWED_HISTORICAL_SEC_TYPES))
        msg = f"sec_type must be one of {allowed}"
        raise DataFoundationValidationError(msg)
    return sec_type


def _freeze_json_value(value: object, field_name: str) -> object:
    if isinstance(value, Mapping):
        if not value:
            msg = f"{field_name} must not be an empty mapping"
            raise DataFoundationValidationError(msg)
        return MappingProxyType(
            {
                _require_text(key, f"{field_name} key"): _freeze_json_value(
                    nested_value,
                    f"{field_name}.{key}",
                )
                for key, nested_value in sorted(value.items(), key=lambda item: str(item[0]))
            }
        )
    if isinstance(value, tuple | list):
        return tuple(_freeze_json_value(item, f"{field_name}[]") for item in value)
    if isinstance(value, Decimal):
        if not value.is_finite():
            msg = f"{field_name} must contain only finite decimal values"
            raise DataFoundationValidationError(msg)
        return str(value)
    if isinstance(value, float) and not isfinite(value):
        msg = f"{field_name} must contain only finite float values"
        raise DataFoundationValidationError(msg)
    if value is None or isinstance(value, bool | int | float | str):
        return value
    msg = f"{field_name} must contain only JSON-stable planning values"
    raise DataFoundationValidationError(msg)


def _contains_non_positive_number(value: object) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int | float | Decimal):
        return value <= 0
    if isinstance(value, Mapping):
        return any(_contains_non_positive_number(nested) for nested in value.values())
    if isinstance(value, tuple | list):
        return any(_contains_non_positive_number(nested) for nested in value)
    return False


def _normalize_chunk_policy(value: object) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "chunk_policy must be a non-empty mapping"
        raise DataFoundationValidationError(msg)
    if _contains_non_positive_number(value):
        msg = "chunk_policy must not contain zero or negative numeric values"
        raise DataFoundationValidationError(msg)
    frozen = _freeze_json_value(value, "chunk_policy")
    if not isinstance(frozen, Mapping):
        msg = "chunk_policy must be a non-empty mapping"
        raise DataFoundationValidationError(msg)
    return frozen


def _normalize_expected_coverage(value: object) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "expected_coverage must be a non-empty mapping"
        raise DataFoundationValidationError(msg)
    frozen = _freeze_json_value(value, "expected_coverage")
    if not isinstance(frozen, Mapping):
        msg = "expected_coverage must be a non-empty mapping"
        raise DataFoundationValidationError(msg)
    return frozen


def _canonical_json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _canonical_json_value(value[key]) for key in sorted(value)}
    if isinstance(value, tuple | list):
        return [_canonical_json_value(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, StrEnum):
        return str(value)
    if value is None or isinstance(value, bool | int | float | str):
        return value
    msg = f"value {value!r} is not JSON-stable"
    raise DataFoundationValidationError(msg)


def _stable_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _canonical_json_value(payload),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_sha256_hash(value: object) -> str | None:
    if value is None:
        return None
    raw = _require_text(value, "manifest_hash").lower()
    if not _SHA256_HEX_PATTERN.fullmatch(raw):
        msg = "manifest_hash must be a lowercase sha256 hex digest"
        raise DataFoundationValidationError(msg)
    return raw


def _normalize_resume_token(value: object) -> str | None:
    if value is None:
        return None
    raw = _require_text(value, "resume_token").lower()
    if not raw.startswith("sha256:"):
        msg = "resume_token must use sha256:<digest>"
        raise DataFoundationValidationError(msg)
    digest = raw.removeprefix("sha256:")
    if not _SHA256_HEX_PATTERN.fullmatch(digest):
        msg = "resume_token must use sha256:<digest>"
        raise DataFoundationValidationError(msg)
    return raw


def _validate_client_id(value: object) -> int:
    return IBKRClientIdPolicy.default().validate_client_id(value)


def _normalize_data_root_reference(value: object) -> str:
    if not isinstance(value, (str, os.PathLike)):
        msg = "data_root must be a string or path-like local data-root reference"
        raise DataFoundationValidationError(msg)
    raw = os.fspath(value).strip()
    if not raw:
        msg = "data_root must be a non-empty local data-root reference"
        raise DataFoundationValidationError(msg)
    LocalDataRootPolicy(
        data_root=raw,
        must_be_local=True,
        must_be_ignored=True,
        forbidden_repo_paths=DEFAULT_FORBIDDEN_REPO_PATHS,
        allowed_subdirs=DEFAULT_ALLOWED_SUBDIRS,
        max_file_policy=DEFAULT_MAX_FILE_POLICY,
    )
    return raw


@dataclass(frozen=True, slots=True)
class HistoricalRequestSpec:
    """Declarative IBKR historical-data request before any provider call."""

    request_spec_id: str
    source_id: str
    symbol_root: str
    contract_ref: str
    sec_type: str
    exchange: str
    currency: str
    bar_size: str
    what_to_show: str
    use_rth: bool
    duration: str
    end_datetime_policy: str
    start_ts: datetime
    end_ts: datetime
    chunk_policy: Mapping[str, object]
    client_id: int

    def __post_init__(self) -> None:
        request_spec_id = _normalize_id(self.request_spec_id, "request_spec_id")
        source_id = _normalize_source_id(self.source_id)
        symbol_root = _normalize_symbol_root(self.symbol_root)
        contract_ref = _require_reference(self.contract_ref, "contract_ref")
        sec_type = _normalize_sec_type(self.sec_type)
        exchange = _require_text(self.exchange, "exchange").upper()
        currency = _require_text(self.currency, "currency").upper()
        bar_size = _require_text(self.bar_size, "bar_size")
        what_to_show = _require_text(self.what_to_show, "what_to_show").upper()
        use_rth = _require_bool(self.use_rth, "use_rth")
        duration = _require_text(self.duration, "duration")
        end_datetime_policy = _require_text(
            self.end_datetime_policy,
            "end_datetime_policy",
        )
        start_ts = _parse_aware_datetime(self.start_ts, "start_ts")
        end_ts = _parse_aware_datetime(self.end_ts, "end_ts")
        chunk_policy = _normalize_chunk_policy(self.chunk_policy)
        client_id = _validate_client_id(self.client_id)

        master = load_futures_instrument_master_by_root()[symbol_root]
        if exchange != master.exchange:
            msg = f"exchange {exchange!r} does not reconcile with {symbol_root}"
            raise DataFoundationValidationError(msg)
        if currency != master.currency:
            msg = f"currency {currency!r} does not reconcile with {symbol_root}"
            raise DataFoundationValidationError(msg)
        if end_ts < start_ts:
            msg = "end_ts must be greater than or equal to start_ts"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "request_spec_id", request_spec_id)
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "symbol_root", symbol_root)
        object.__setattr__(self, "contract_ref", contract_ref)
        object.__setattr__(self, "sec_type", sec_type)
        object.__setattr__(self, "exchange", exchange)
        object.__setattr__(self, "currency", currency)
        object.__setattr__(self, "bar_size", bar_size)
        object.__setattr__(self, "what_to_show", what_to_show)
        object.__setattr__(self, "use_rth", use_rth)
        object.__setattr__(self, "duration", duration)
        object.__setattr__(self, "end_datetime_policy", end_datetime_policy)
        object.__setattr__(self, "start_ts", start_ts)
        object.__setattr__(self, "end_ts", end_ts)
        object.__setattr__(self, "chunk_policy", chunk_policy)
        object.__setattr__(self, "client_id", client_id)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> HistoricalRequestSpec:
        """Build a request spec from persisted data and fail closed."""

        missing = tuple(
            field for field in REQUIRED_HISTORICAL_REQUEST_SPEC_FIELDS if field not in values
        )
        if missing:
            msg = "HistoricalRequestSpec missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)

        return cls(
            request_spec_id=_require_text(values["request_spec_id"], "request_spec_id"),
            source_id=_require_text(values["source_id"], "source_id"),
            symbol_root=_require_text(values["symbol_root"], "symbol_root"),
            contract_ref=_require_text(values["contract_ref"], "contract_ref"),
            sec_type=_require_text(values["sec_type"], "sec_type"),
            exchange=_require_text(values["exchange"], "exchange"),
            currency=_require_text(values["currency"], "currency"),
            bar_size=_require_text(values["bar_size"], "bar_size"),
            what_to_show=_require_text(values["what_to_show"], "what_to_show"),
            use_rth=_require_bool(values["use_rth"], "use_rth"),
            duration=_require_text(values["duration"], "duration"),
            end_datetime_policy=_require_text(
                values["end_datetime_policy"],
                "end_datetime_policy",
            ),
            start_ts=_parse_aware_datetime(values["start_ts"], "start_ts"),
            end_ts=_parse_aware_datetime(values["end_ts"], "end_ts"),
            chunk_policy=_normalize_chunk_policy(values["chunk_policy"]),
            client_id=_validate_client_id(values["client_id"]),
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable planning record with no execution status."""

        return MappingProxyType(
            {
                "request_spec_id": self.request_spec_id,
                "source_id": self.source_id,
                "symbol_root": self.symbol_root,
                "contract_ref": self.contract_ref,
                "sec_type": self.sec_type,
                "exchange": self.exchange,
                "currency": self.currency,
                "bar_size": self.bar_size,
                "what_to_show": self.what_to_show,
                "use_rth": self.use_rth,
                "duration": self.duration,
                "end_datetime_policy": self.end_datetime_policy,
                "start_ts": self.start_ts.isoformat(),
                "end_ts": self.end_ts.isoformat(),
                "chunk_policy": self.chunk_policy,
                "client_id": self.client_id,
            }
        )


def _coerce_request_specs(
    values: object,
) -> tuple[HistoricalRequestSpec, ...]:
    if isinstance(values, str) or not isinstance(values, Iterable):
        msg = "request_specs must be a non-empty iterable of HistoricalRequestSpec records"
        raise DataFoundationValidationError(msg)

    request_specs: list[HistoricalRequestSpec] = []
    for item in values:
        if isinstance(item, HistoricalRequestSpec):
            request_specs.append(item)
        elif isinstance(item, Mapping):
            request_specs.append(HistoricalRequestSpec.from_mapping(item))
        else:
            msg = "request_specs entries must be HistoricalRequestSpec records or mappings"
            raise DataFoundationValidationError(msg)

    if not request_specs:
        msg = "request_specs must not be empty"
        raise DataFoundationValidationError(msg)

    request_ids = [request.request_spec_id for request in request_specs]
    duplicates = sorted(
        {request_id for request_id in request_ids if request_ids.count(request_id) > 1}
    )
    if duplicates:
        msg = "request_specs contains duplicate request_spec_id values: " + ", ".join(duplicates)
        raise DataFoundationValidationError(msg)

    return tuple(request_specs)


def compute_historical_request_manifest_hash(
    *,
    manifest_id: object,
    batch_id: object,
    request_specs: object,
    chunk_count: object,
    expected_coverage: object,
    pacing_policy_id: object,
    data_root: object,
    created_by: object,
) -> str:
    """Compute a deterministic hash over non-wall-clock manifest content.

    ``created_at`` and ``manifest_hash`` are intentionally excluded: the former is
    audit metadata and the latter is the digest being computed.
    """

    normalized_request_specs = _coerce_request_specs(request_specs)
    return _stable_hash(
        {
            "schema": HISTORICAL_REQUEST_MANIFEST_HASH_SCHEMA,
            "manifest_id": _normalize_id(manifest_id, "manifest_id"),
            "batch_id": _normalize_id(batch_id, "batch_id"),
            "request_specs": tuple(
                request_spec.to_mapping() for request_spec in normalized_request_specs
            ),
            "chunk_count": _require_positive_int(chunk_count, "chunk_count"),
            "expected_coverage": _normalize_expected_coverage(expected_coverage),
            "pacing_policy_id": _normalize_id(pacing_policy_id, "pacing_policy_id"),
            "data_root": _normalize_data_root_reference(data_root),
            "created_by": _require_text(created_by, "created_by"),
        }
    )


@dataclass(frozen=True, slots=True)
class HistoricalRequestManifest:
    """Validated planned set of historical requests before any provider pull."""

    manifest_id: str
    batch_id: str
    request_specs: tuple[HistoricalRequestSpec, ...]
    chunk_count: int
    expected_coverage: Mapping[str, object]
    pacing_policy_id: str
    data_root: str
    created_by: str
    created_at: datetime
    manifest_hash: str | None = None

    def __post_init__(self) -> None:
        manifest_id = _normalize_id(self.manifest_id, "manifest_id")
        batch_id = _normalize_id(self.batch_id, "batch_id")
        request_specs = _coerce_request_specs(self.request_specs)
        chunk_count = _require_positive_int(self.chunk_count, "chunk_count")
        expected_coverage = _normalize_expected_coverage(self.expected_coverage)
        pacing_policy_id = _normalize_id(self.pacing_policy_id, "pacing_policy_id")
        data_root = _normalize_data_root_reference(self.data_root)
        created_by = _require_text(self.created_by, "created_by")
        created_at = _parse_aware_datetime(self.created_at, "created_at")

        if chunk_count < len(request_specs):
            msg = "chunk_count must cover at least one chunk per request_spec"
            raise DataFoundationValidationError(msg)

        computed_hash = compute_historical_request_manifest_hash(
            manifest_id=manifest_id,
            batch_id=batch_id,
            request_specs=request_specs,
            chunk_count=chunk_count,
            expected_coverage=expected_coverage,
            pacing_policy_id=pacing_policy_id,
            data_root=data_root,
            created_by=created_by,
        )
        supplied_hash = _normalize_sha256_hash(self.manifest_hash)
        if supplied_hash is not None and supplied_hash != computed_hash:
            msg = "manifest_hash does not match the historical request manifest content"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "manifest_id", manifest_id)
        object.__setattr__(self, "batch_id", batch_id)
        object.__setattr__(self, "request_specs", request_specs)
        object.__setattr__(self, "chunk_count", chunk_count)
        object.__setattr__(self, "expected_coverage", expected_coverage)
        object.__setattr__(self, "pacing_policy_id", pacing_policy_id)
        object.__setattr__(self, "data_root", data_root)
        object.__setattr__(self, "created_by", created_by)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "manifest_hash", computed_hash)

    @classmethod
    def create(
        cls,
        *,
        manifest_id: str,
        batch_id: str,
        request_specs: Iterable[HistoricalRequestSpec | Mapping[str, object]],
        chunk_count: int,
        expected_coverage: Mapping[str, object],
        pacing_policy_id: str,
        data_root: str | os.PathLike[str],
        created_by: str,
        created_at: datetime,
    ) -> HistoricalRequestManifest:
        """Create a manifest and compute its deterministic manifest hash."""

        return cls(
            manifest_id=manifest_id,
            batch_id=batch_id,
            request_specs=tuple(request_specs),
            chunk_count=chunk_count,
            expected_coverage=expected_coverage,
            pacing_policy_id=pacing_policy_id,
            data_root=os.fspath(data_root),
            created_by=created_by,
            created_at=created_at,
            manifest_hash=None,
        )

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> HistoricalRequestManifest:
        """Build a manifest from persisted data and validate its hash."""

        missing = tuple(
            field for field in REQUIRED_HISTORICAL_REQUEST_MANIFEST_FIELDS if field not in values
        )
        if missing:
            msg = "HistoricalRequestManifest missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)

        return cls(
            manifest_id=_require_text(values["manifest_id"], "manifest_id"),
            batch_id=_require_text(values["batch_id"], "batch_id"),
            request_specs=_coerce_request_specs(values["request_specs"]),
            chunk_count=_require_positive_int(values["chunk_count"], "chunk_count"),
            expected_coverage=_normalize_expected_coverage(values["expected_coverage"]),
            pacing_policy_id=_require_text(values["pacing_policy_id"], "pacing_policy_id"),
            data_root=_normalize_data_root_reference(values["data_root"]),
            created_by=_require_text(values["created_by"], "created_by"),
            created_at=_parse_aware_datetime(values["created_at"], "created_at"),
            manifest_hash=_require_text(values["manifest_hash"], "manifest_hash"),
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable manifest with no pull authorization claim."""

        return MappingProxyType(
            {
                "manifest_id": self.manifest_id,
                "batch_id": self.batch_id,
                "request_specs": tuple(
                    request_spec.to_mapping() for request_spec in self.request_specs
                ),
                "chunk_count": self.chunk_count,
                "expected_coverage": self.expected_coverage,
                "pacing_policy_id": self.pacing_policy_id,
                "data_root": self.data_root,
                "created_by": self.created_by,
                "created_at": self.created_at.isoformat(),
                "manifest_hash": self.manifest_hash,
            }
        )


def plan_historical_request_transition(
    request_spec: HistoricalRequestSpec | Mapping[str, object],
) -> HistoricalRequestLifecycleState:
    """Validate ``NOT_REQUESTED -> REQUEST_PLANNED`` using a request spec."""

    if isinstance(request_spec, HistoricalRequestSpec):
        return HistoricalRequestLifecycleState.REQUEST_PLANNED
    if isinstance(request_spec, Mapping):
        HistoricalRequestSpec.from_mapping(request_spec)
        return HistoricalRequestLifecycleState.REQUEST_PLANNED
    msg = "HistoricalRequestSpec is required for NOT_REQUESTED -> REQUEST_PLANNED"
    raise DataFoundationValidationError(msg)


def require_validated_manifest_for_provider_pull(
    manifest: HistoricalRequestManifest | Mapping[str, object] | None,
) -> HistoricalRequestManifest:
    """Fail closed unless a valid manifest is present before a provider pull."""

    if manifest is None:
        msg = "missing HistoricalRequestManifest blocks provider pull"
        raise DataFoundationValidationError(msg)
    if isinstance(manifest, HistoricalRequestManifest):
        return manifest
    if isinstance(manifest, Mapping):
        return HistoricalRequestManifest.from_mapping(manifest)
    msg = "HistoricalRequestManifest is required before provider pull authorization"
    raise DataFoundationValidationError(msg)


def provider_pull_manifest_guard(
    manifest: HistoricalRequestManifest | Mapping[str, object] | None,
) -> bool:
    """Return ``True`` only when a manifest validates; invalid input blocks."""

    try:
        require_validated_manifest_for_provider_pull(manifest)
    except DataFoundationValidationError:
        return False
    return True


def authorize_historical_request_transition(
    manifest: HistoricalRequestManifest | Mapping[str, object] | None,
) -> HistoricalRequestLifecycleState:
    """Validate ``REQUEST_PLANNED -> REQUEST_AUTHORIZED`` without external calls."""

    require_validated_manifest_for_provider_pull(manifest)
    return HistoricalRequestLifecycleState.REQUEST_AUTHORIZED


def _normalize_pacing_source(value: object) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "source must be a non-empty mapping"
        raise DataFoundationValidationError(msg)
    frozen = _freeze_json_value(value, "source")
    if not isinstance(frozen, Mapping):
        msg = "source must be a non-empty mapping"
        raise DataFoundationValidationError(msg)

    if "verification_status" not in frozen:
        msg = "source.verification_status must be to_be_verified"
        raise DataFoundationValidationError(msg)
    verification_status = (
        _require_text(frozen["verification_status"], "source.verification_status")
        .lower()
        .replace("-", "_")
    )
    if verification_status != _TO_BE_VERIFIED_STATUS:
        msg = "source.verification_status must be to_be_verified"
        raise DataFoundationValidationError(msg)
    if "verification_method" not in frozen:
        msg = "source.verification_method is required"
        raise DataFoundationValidationError(msg)
    verification_method = _require_text(
        frozen["verification_method"],
        "source.verification_method",
    )

    normalized = dict(frozen)
    normalized["verification_status"] = verification_status
    normalized["verification_method"] = verification_method
    return MappingProxyType(normalized)


def _normalize_backoff_policy(value: object) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "backoff_policy must be a non-empty mapping"
        raise DataFoundationValidationError(msg)
    frozen = _freeze_json_value(value, "backoff_policy")
    if not isinstance(frozen, Mapping):
        msg = "backoff_policy must be a non-empty mapping"
        raise DataFoundationValidationError(msg)

    required = ("base_seconds", "multiplier", "max_seconds", "max_attempts")
    missing = tuple(field for field in required if field not in frozen)
    if missing:
        msg = "backoff_policy missing required fields: " + ", ".join(missing)
        raise DataFoundationValidationError(msg)

    base_seconds = _require_positive_float(
        frozen["base_seconds"],
        "backoff_policy.base_seconds",
    )
    multiplier = _require_positive_float(
        frozen["multiplier"],
        "backoff_policy.multiplier",
    )
    max_seconds = _require_positive_float(
        frozen["max_seconds"],
        "backoff_policy.max_seconds",
    )
    max_attempts = _require_positive_int(
        frozen["max_attempts"],
        "backoff_policy.max_attempts",
    )

    if multiplier < 1.0:
        msg = "backoff_policy.multiplier must be at least 1.0"
        raise DataFoundationValidationError(msg)
    if max_seconds < base_seconds:
        msg = "backoff_policy.max_seconds must be greater than or equal to base_seconds"
        raise DataFoundationValidationError(msg)

    normalized = dict(frozen)
    normalized["base_seconds"] = base_seconds
    normalized["multiplier"] = multiplier
    normalized["max_seconds"] = max_seconds
    normalized["max_attempts"] = max_attempts
    return MappingProxyType(normalized)


def _normalize_chunk_status(value: object) -> HistoricalChunkStatus:
    if isinstance(value, HistoricalChunkStatus):
        return value
    token = _require_text(value, "status").upper().replace("-", "_").replace(" ", "_")
    try:
        return HistoricalChunkStatus[token]
    except KeyError as exc:
        allowed = ", ".join(status.value for status in HistoricalChunkStatus)
        msg = f"status must be one of {allowed}"
        raise DataFoundationValidationError(msg) from exc


def _normalize_pull_ledger_status(value: object) -> HistoricalPullLedgerStatus:
    if isinstance(value, HistoricalPullLedgerStatus):
        return value
    token = _require_text(value, "status").upper().replace("-", "_").replace(" ", "_")
    try:
        return HistoricalPullLedgerStatus[token]
    except KeyError as exc:
        allowed = ", ".join(status.value for status in HistoricalPullLedgerStatus)
        msg = f"status must be one of {allowed}"
        raise DataFoundationValidationError(msg) from exc


def _normalize_error_resolution(value: object) -> ProviderErrorResolution:
    if isinstance(value, ProviderErrorResolution):
        return value
    token = _require_text(value, "resolution").upper().replace("-", "_").replace(" ", "_")
    try:
        return ProviderErrorResolution[token]
    except KeyError as exc:
        allowed = ", ".join(resolution.value for resolution in ProviderErrorResolution)
        msg = f"resolution must be one of {allowed}"
        raise DataFoundationValidationError(msg) from exc


def _normalize_error_code(value: object) -> str:
    if isinstance(value, bool):
        msg = "error_code must be a provider error code"
        raise DataFoundationValidationError(msg)
    if isinstance(value, int):
        return str(value)
    return _require_text(value, "error_code")


def _reject_quality_pass_claim(summary: Mapping[str, object], field_name: str) -> None:
    for key, value in summary.items():
        key_token = str(key).lower().replace("-", "_")
        if key_token in _FORBIDDEN_QUALITY_CLAIM_TOKENS:
            msg = f"{field_name} must not imply that quality passed"
            raise DataFoundationValidationError(msg)
        if isinstance(value, str):
            value_token = value.lower().replace("-", "_").replace(" ", "_")
            if value_token in _FORBIDDEN_QUALITY_CLAIM_TOKENS:
                msg = f"{field_name} must not imply that quality passed"
                raise DataFoundationValidationError(msg)


@dataclass(frozen=True, slots=True)
class RequestPacingPolicy:
    """Conservative configurable throttle and retry policy for future pulls."""

    pacing_policy_id: str
    min_seconds_between_identical_requests: float
    max_requests_per_window: int
    window_seconds: float
    bid_ask_counts_double: bool
    backoff_policy: Mapping[str, object]
    source: Mapping[str, object]

    def __post_init__(self) -> None:
        pacing_policy_id = _normalize_id(self.pacing_policy_id, "pacing_policy_id")
        min_seconds_between_identical_requests = _require_positive_float(
            self.min_seconds_between_identical_requests,
            "min_seconds_between_identical_requests",
        )
        max_requests_per_window = _require_positive_int(
            self.max_requests_per_window,
            "max_requests_per_window",
        )
        window_seconds = _require_positive_float(self.window_seconds, "window_seconds")
        bid_ask_counts_double = _require_bool(
            self.bid_ask_counts_double,
            "bid_ask_counts_double",
        )
        backoff_policy = _normalize_backoff_policy(self.backoff_policy)
        source = _normalize_pacing_source(self.source)

        if not bid_ask_counts_double:
            msg = "bid_ask_counts_double must be true so BID_ASK counts heavier than TRADES"
            raise DataFoundationValidationError(msg)
        if min_seconds_between_identical_requests > window_seconds:
            msg = "min_seconds_between_identical_requests must not exceed window_seconds"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "pacing_policy_id", pacing_policy_id)
        object.__setattr__(
            self,
            "min_seconds_between_identical_requests",
            min_seconds_between_identical_requests,
        )
        object.__setattr__(self, "max_requests_per_window", max_requests_per_window)
        object.__setattr__(self, "window_seconds", window_seconds)
        object.__setattr__(self, "bid_ask_counts_double", bid_ask_counts_double)
        object.__setattr__(self, "backoff_policy", backoff_policy)
        object.__setattr__(self, "source", source)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> RequestPacingPolicy:
        """Build a pacing policy from persisted/configured values."""

        missing = tuple(
            field for field in REQUIRED_REQUEST_PACING_POLICY_FIELDS if field not in values
        )
        if missing:
            msg = "RequestPacingPolicy missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        return cls(
            pacing_policy_id=_require_text(values["pacing_policy_id"], "pacing_policy_id"),
            min_seconds_between_identical_requests=_require_positive_float(
                values["min_seconds_between_identical_requests"],
                "min_seconds_between_identical_requests",
            ),
            max_requests_per_window=_require_positive_int(
                values["max_requests_per_window"],
                "max_requests_per_window",
            ),
            window_seconds=_require_positive_float(
                values["window_seconds"],
                "window_seconds",
            ),
            bid_ask_counts_double=_require_bool(
                values["bid_ask_counts_double"],
                "bid_ask_counts_double",
            ),
            backoff_policy=_normalize_backoff_policy(values["backoff_policy"]),
            source=_normalize_pacing_source(values["source"]),
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable policy record labeled to-be-verified."""

        return MappingProxyType(
            {
                "pacing_policy_id": self.pacing_policy_id,
                "min_seconds_between_identical_requests": (
                    self.min_seconds_between_identical_requests
                ),
                "max_requests_per_window": self.max_requests_per_window,
                "window_seconds": self.window_seconds,
                "bid_ask_counts_double": self.bid_ask_counts_double,
                "backoff_policy": self.backoff_policy,
                "source": self.source,
            }
        )

    def accounting_weight(self, what_to_show: object) -> int:
        """Return request-window cost; BID_ASK is heavier than TRADES."""

        token = _require_text(what_to_show, "what_to_show").upper().replace("-", "_")
        if token == "BID_ASK":
            return 2
        return 1

    def backoff_delay_seconds(self, attempt: object) -> float:
        """Compute deterministic exponential backoff for a retry attempt."""

        attempt_count = _require_positive_int(attempt, "attempt")
        max_attempts = _require_positive_int(
            self.backoff_policy["max_attempts"],
            "backoff_policy.max_attempts",
        )
        if attempt_count > max_attempts:
            msg = "attempt exceeds backoff_policy.max_attempts; retry must not continue"
            raise DataFoundationValidationError(msg)
        base_seconds = _require_positive_float(
            self.backoff_policy["base_seconds"],
            "backoff_policy.base_seconds",
        )
        multiplier = _require_positive_float(
            self.backoff_policy["multiplier"],
            "backoff_policy.multiplier",
        )
        max_seconds = _require_positive_float(
            self.backoff_policy["max_seconds"],
            "backoff_policy.max_seconds",
        )
        return min(base_seconds * (multiplier ** (attempt_count - 1)), max_seconds)

    def can_retry_attempt(self, attempt: object) -> bool:
        """Return whether the retry attempt is still inside the configured cap."""

        attempt_count = _require_positive_int(attempt, "attempt")
        max_attempts = _require_positive_int(
            self.backoff_policy["max_attempts"],
            "backoff_policy.max_attempts",
        )
        return attempt_count <= max_attempts


def require_pacing_policy_for_provider_pull(
    pacing_policy: RequestPacingPolicy | Mapping[str, object] | None,
) -> RequestPacingPolicy:
    """Fail closed unless a valid pacing policy is present before a pull."""

    if pacing_policy is None:
        msg = "missing RequestPacingPolicy blocks provider pull and forbids naive loops"
        raise DataFoundationValidationError(msg)
    if isinstance(pacing_policy, RequestPacingPolicy):
        return pacing_policy
    if isinstance(pacing_policy, Mapping):
        return RequestPacingPolicy.from_mapping(pacing_policy)
    msg = "RequestPacingPolicy is required before provider pull authorization"
    raise DataFoundationValidationError(msg)


def provider_pull_pacing_guard(
    pacing_policy: RequestPacingPolicy | Mapping[str, object] | None,
) -> bool:
    """Return ``True`` only when a pacing policy validates."""

    try:
        require_pacing_policy_for_provider_pull(pacing_policy)
    except DataFoundationValidationError:
        return False
    return True


def forbid_naive_request_loop(
    pacing_policy: RequestPacingPolicy | Mapping[str, object] | None,
) -> bool:
    """Validate that future request loops are governed by a pacing policy."""

    require_pacing_policy_for_provider_pull(pacing_policy)
    return True


@dataclass(frozen=True, slots=True)
class HistoricalChunkRecord:
    """One immutable chunk request lifecycle record."""

    chunk_id: str
    request_spec_id: str
    symbol_root: str
    contract_ref: str
    start_ts: datetime
    end_ts: datetime
    status: HistoricalChunkStatus
    attempt_count: int
    provider_request_id: str | None
    raw_object_ref: str | None
    row_count: int | None
    error_ref: str | None
    retrieved_at: datetime | None

    def __post_init__(self) -> None:
        chunk_id = _normalize_id(self.chunk_id, "chunk_id")
        request_spec_id = _normalize_id(self.request_spec_id, "request_spec_id")
        symbol_root = _normalize_symbol_root(self.symbol_root)
        contract_ref = _require_reference(self.contract_ref, "contract_ref")
        start_ts = _parse_aware_datetime(self.start_ts, "start_ts")
        end_ts = _parse_aware_datetime(self.end_ts, "end_ts")
        status = _normalize_chunk_status(self.status)
        attempt_count = _require_non_negative_int(self.attempt_count, "attempt_count")
        provider_request_id = _normalize_optional_reference(
            self.provider_request_id,
            "provider_request_id",
        )
        raw_object_ref = _normalize_optional_raw_object_ref(self.raw_object_ref)
        row_count = _require_optional_non_negative_int(self.row_count, "row_count")
        error_ref = _normalize_optional_reference(self.error_ref, "error_ref")
        retrieved_at = _parse_optional_aware_datetime(self.retrieved_at, "retrieved_at")

        if end_ts < start_ts:
            msg = "end_ts must be greater than or equal to start_ts"
            raise DataFoundationValidationError(msg)

        if status is HistoricalChunkStatus.NOT_STARTED:
            if attempt_count != 0:
                msg = "NOT_STARTED chunks must have attempt_count 0"
                raise DataFoundationValidationError(msg)
            if any(
                value is not None
                for value in (
                    provider_request_id,
                    raw_object_ref,
                    row_count,
                    error_ref,
                    retrieved_at,
                )
            ):
                msg = (
                    "NOT_STARTED chunks must not carry provider, raw, row, error, or retrieval refs"
                )
                raise DataFoundationValidationError(msg)
        else:
            if attempt_count <= 0:
                msg = f"{status.value} chunks must have a positive attempt_count"
                raise DataFoundationValidationError(msg)
            if provider_request_id is None:
                msg = f"{status.value} chunks must carry provider_request_id"
                raise DataFoundationValidationError(msg)

        if status is HistoricalChunkStatus.COMPLETE:
            if raw_object_ref is None:
                msg = "COMPLETE chunks require an immutable raw_object_ref"
                raise DataFoundationValidationError(msg)
            if row_count is None:
                msg = "COMPLETE chunks require row_count"
                raise DataFoundationValidationError(msg)
            if retrieved_at is None:
                msg = "COMPLETE chunks require retrieved_at"
                raise DataFoundationValidationError(msg)
            if error_ref is not None:
                msg = "COMPLETE chunks must not carry error_ref"
                raise DataFoundationValidationError(msg)
        if status is HistoricalChunkStatus.IN_PROGRESS and retrieved_at is not None:
            msg = "IN_PROGRESS chunks must not carry retrieved_at"
            raise DataFoundationValidationError(msg)
        if status is HistoricalChunkStatus.INCOMPLETE:
            if error_ref is None:
                msg = "INCOMPLETE chunks require error_ref"
                raise DataFoundationValidationError(msg)
            if retrieved_at is None:
                msg = "INCOMPLETE chunks require retrieved_at"
                raise DataFoundationValidationError(msg)
        if status in {HistoricalChunkStatus.FAILED, HistoricalChunkStatus.QUARANTINED}:
            if error_ref is None:
                msg = f"{status.value} chunks require error_ref"
                raise DataFoundationValidationError(msg)

        object.__setattr__(self, "chunk_id", chunk_id)
        object.__setattr__(self, "request_spec_id", request_spec_id)
        object.__setattr__(self, "symbol_root", symbol_root)
        object.__setattr__(self, "contract_ref", contract_ref)
        object.__setattr__(self, "start_ts", start_ts)
        object.__setattr__(self, "end_ts", end_ts)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "attempt_count", attempt_count)
        object.__setattr__(self, "provider_request_id", provider_request_id)
        object.__setattr__(self, "raw_object_ref", raw_object_ref)
        object.__setattr__(self, "row_count", row_count)
        object.__setattr__(self, "error_ref", error_ref)
        object.__setattr__(self, "retrieved_at", retrieved_at)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> HistoricalChunkRecord:
        """Build a chunk lifecycle record from persisted data."""

        missing = tuple(
            field for field in REQUIRED_HISTORICAL_CHUNK_RECORD_FIELDS if field not in values
        )
        if missing:
            msg = "HistoricalChunkRecord missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        return cls(
            chunk_id=_require_text(values["chunk_id"], "chunk_id"),
            request_spec_id=_require_text(values["request_spec_id"], "request_spec_id"),
            symbol_root=_require_text(values["symbol_root"], "symbol_root"),
            contract_ref=_require_text(values["contract_ref"], "contract_ref"),
            start_ts=_parse_aware_datetime(values["start_ts"], "start_ts"),
            end_ts=_parse_aware_datetime(values["end_ts"], "end_ts"),
            status=_normalize_chunk_status(values["status"]),
            attempt_count=_require_non_negative_int(values["attempt_count"], "attempt_count"),
            provider_request_id=_normalize_optional_reference(
                values["provider_request_id"],
                "provider_request_id",
            ),
            raw_object_ref=_normalize_optional_raw_object_ref(values["raw_object_ref"]),
            row_count=_require_optional_non_negative_int(values["row_count"], "row_count"),
            error_ref=_normalize_optional_reference(values["error_ref"], "error_ref"),
            retrieved_at=_parse_optional_aware_datetime(
                values["retrieved_at"],
                "retrieved_at",
            ),
        )

    @property
    def request_key(self) -> tuple[str, str, str, str, str]:
        """Stable identity for duplicate-request detection."""

        return (
            self.request_spec_id,
            self.symbol_root,
            self.contract_ref,
            self.start_ts.isoformat(),
            self.end_ts.isoformat(),
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable chunk lifecycle record."""

        return MappingProxyType(
            {
                "chunk_id": self.chunk_id,
                "request_spec_id": self.request_spec_id,
                "symbol_root": self.symbol_root,
                "contract_ref": self.contract_ref,
                "start_ts": self.start_ts.isoformat(),
                "end_ts": self.end_ts.isoformat(),
                "status": self.status.value,
                "attempt_count": self.attempt_count,
                "provider_request_id": self.provider_request_id,
                "raw_object_ref": self.raw_object_ref,
                "row_count": self.row_count,
                "error_ref": self.error_ref,
                "retrieved_at": self.retrieved_at.isoformat()
                if self.retrieved_at is not None
                else None,
            }
        )

    def with_recorded_raw_object_ref(
        self,
        raw_object_ref: object,
        *,
        row_count: object,
        retrieved_at: object,
        provider_request_id: object | None = None,
    ) -> HistoricalChunkRecord:
        """Record a raw ref once; resume must never overwrite a different ref."""

        normalized_raw_ref = _normalize_raw_object_ref(raw_object_ref)
        if self.raw_object_ref is not None and self.raw_object_ref != normalized_raw_ref:
            msg = "raw_object_ref is immutable; resume must not overwrite existing raw refs"
            raise DataFoundationValidationError(msg)

        normalized_provider_request_id = (
            _normalize_optional_reference(provider_request_id, "provider_request_id")
            if provider_request_id is not None
            else self.provider_request_id
        )
        if normalized_provider_request_id is None:
            msg = "provider_request_id is required before recording raw_object_ref"
            raise DataFoundationValidationError(msg)

        return replace(
            self,
            status=HistoricalChunkStatus.COMPLETE,
            attempt_count=max(self.attempt_count, 1),
            provider_request_id=normalized_provider_request_id,
            raw_object_ref=normalized_raw_ref,
            row_count=_require_non_negative_int(row_count, "row_count"),
            error_ref=None,
            retrieved_at=_parse_aware_datetime(retrieved_at, "retrieved_at"),
        )


@dataclass(frozen=True, slots=True)
class ProviderErrorRecord:
    """Permanent provider-error or incomplete-response ledger record."""

    error_id: str
    provider: str
    request_id: str
    chunk_id: str
    error_code: str
    error_message: str
    retryable: bool
    attempt: int
    timestamp: datetime
    resolution: ProviderErrorResolution

    def __post_init__(self) -> None:
        error_id = _normalize_id(self.error_id, "error_id")
        provider = _require_text(self.provider, "provider").upper()
        request_id = _require_reference(self.request_id, "request_id")
        chunk_id = _normalize_id(self.chunk_id, "chunk_id")
        error_code = _normalize_error_code(self.error_code)
        error_message = _require_text(self.error_message, "error_message")
        retryable = _require_bool(self.retryable, "retryable")
        attempt = _require_positive_int(self.attempt, "attempt")
        timestamp = _parse_aware_datetime(self.timestamp, "timestamp")
        resolution = _normalize_error_resolution(self.resolution)

        if retryable and resolution is ProviderErrorResolution.QUARANTINED_NON_RETRYABLE:
            msg = "retryable provider errors must not use non-retryable quarantine resolution"
            raise DataFoundationValidationError(msg)
        if not retryable and resolution is not ProviderErrorResolution.QUARANTINED_NON_RETRYABLE:
            msg = "non-retryable provider errors must quarantine the chunk"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "error_id", error_id)
        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "request_id", request_id)
        object.__setattr__(self, "chunk_id", chunk_id)
        object.__setattr__(self, "error_code", error_code)
        object.__setattr__(self, "error_message", error_message)
        object.__setattr__(self, "retryable", retryable)
        object.__setattr__(self, "attempt", attempt)
        object.__setattr__(self, "timestamp", timestamp)
        object.__setattr__(self, "resolution", resolution)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> ProviderErrorRecord:
        """Build a provider-error record from persisted data."""

        missing = tuple(
            field for field in REQUIRED_PROVIDER_ERROR_RECORD_FIELDS if field not in values
        )
        if missing:
            msg = "ProviderErrorRecord missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        return cls(
            error_id=_require_text(values["error_id"], "error_id"),
            provider=_require_text(values["provider"], "provider"),
            request_id=_require_reference(values["request_id"], "request_id"),
            chunk_id=_require_text(values["chunk_id"], "chunk_id"),
            error_code=_normalize_error_code(values["error_code"]),
            error_message=_require_text(values["error_message"], "error_message"),
            retryable=_require_bool(values["retryable"], "retryable"),
            attempt=_require_positive_int(values["attempt"], "attempt"),
            timestamp=_parse_aware_datetime(values["timestamp"], "timestamp"),
            resolution=_normalize_error_resolution(values["resolution"]),
        )

    def backoff_delay_seconds(
        self, pacing_policy: RequestPacingPolicy | Mapping[str, object]
    ) -> float:
        """Return retry backoff delay; non-retryable errors must quarantine."""

        if not self.retryable:
            msg = "non-retryable provider errors quarantine instead of backing off"
            raise DataFoundationValidationError(msg)
        policy = require_pacing_policy_for_provider_pull(pacing_policy)
        return policy.backoff_delay_seconds(self.attempt)

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable permanent provider-error record."""

        return MappingProxyType(
            {
                "error_id": self.error_id,
                "provider": self.provider,
                "request_id": self.request_id,
                "chunk_id": self.chunk_id,
                "error_code": self.error_code,
                "error_message": self.error_message,
                "retryable": self.retryable,
                "attempt": self.attempt,
                "timestamp": self.timestamp.isoformat(),
                "resolution": self.resolution.value,
            }
        )


def _coerce_chunk_records(values: object) -> tuple[HistoricalChunkRecord, ...]:
    if isinstance(values, str) or not isinstance(values, Iterable):
        msg = "chunk_records must be a non-empty iterable of HistoricalChunkRecord records"
        raise DataFoundationValidationError(msg)
    chunk_records: list[HistoricalChunkRecord] = []
    for item in values:
        if isinstance(item, HistoricalChunkRecord):
            chunk_records.append(item)
        elif isinstance(item, Mapping):
            chunk_records.append(HistoricalChunkRecord.from_mapping(item))
        else:
            msg = "chunk_records entries must be HistoricalChunkRecord records or mappings"
            raise DataFoundationValidationError(msg)
    if not chunk_records:
        msg = "chunk_records must not be empty"
        raise DataFoundationValidationError(msg)
    return tuple(chunk_records)


def _detect_chunk_duplicates(chunk_records: tuple[HistoricalChunkRecord, ...]) -> None:
    chunk_ids = [chunk.chunk_id for chunk in chunk_records]
    duplicate_chunk_ids = sorted(
        {chunk_id for chunk_id in chunk_ids if chunk_ids.count(chunk_id) > 1}
    )
    if duplicate_chunk_ids:
        msg = "duplicate chunk_id values detected: " + ", ".join(duplicate_chunk_ids)
        raise DataFoundationValidationError(msg)

    request_keys = [chunk.request_key for chunk in chunk_records]
    duplicate_request_keys = sorted(
        {
            "|".join(request_key)
            for request_key in request_keys
            if request_keys.count(request_key) > 1
        }
    )
    if duplicate_request_keys:
        msg = "duplicate chunk request detected: " + ", ".join(duplicate_request_keys)
        raise DataFoundationValidationError(msg)

    provider_request_ids = [
        chunk.provider_request_id
        for chunk in chunk_records
        if chunk.provider_request_id is not None
    ]
    duplicate_provider_request_ids = sorted(
        {
            provider_request_id
            for provider_request_id in provider_request_ids
            if provider_request_ids.count(provider_request_id) > 1
        }
    )
    if duplicate_provider_request_ids:
        msg = "duplicate provider_request_id values detected: " + ", ".join(
            duplicate_provider_request_ids
        )
        raise DataFoundationValidationError(msg)


def _normalize_expected_chunk_ids(value: object) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = "coverage_summary.expected_chunk_ids must be a non-empty iterable"
        raise DataFoundationValidationError(msg)
    expected_chunk_ids = tuple(
        _normalize_id(chunk_id, "coverage_summary.expected_chunk_ids[]") for chunk_id in value
    )
    if not expected_chunk_ids:
        msg = "coverage_summary.expected_chunk_ids must not be empty"
        raise DataFoundationValidationError(msg)
    duplicates = sorted(
        {chunk_id for chunk_id in expected_chunk_ids if expected_chunk_ids.count(chunk_id) > 1}
    )
    if duplicates:
        msg = "coverage_summary.expected_chunk_ids contains duplicates: " + ", ".join(duplicates)
        raise DataFoundationValidationError(msg)
    return expected_chunk_ids


def _derive_pull_status(
    chunk_records: tuple[HistoricalChunkRecord, ...],
) -> HistoricalPullLedgerStatus:
    statuses = {chunk.status for chunk in chunk_records}
    if HistoricalChunkStatus.QUARANTINED in statuses:
        return HistoricalPullLedgerStatus.QUARANTINED
    if HistoricalChunkStatus.FAILED in statuses:
        return HistoricalPullLedgerStatus.FAILED
    if HistoricalChunkStatus.INCOMPLETE in statuses:
        return HistoricalPullLedgerStatus.INCOMPLETE
    if statuses == {HistoricalChunkStatus.COMPLETE}:
        return HistoricalPullLedgerStatus.COMPLETE
    if statuses == {HistoricalChunkStatus.NOT_STARTED}:
        return HistoricalPullLedgerStatus.NOT_STARTED
    return HistoricalPullLedgerStatus.IN_PROGRESS


def _normalize_coverage_summary(
    value: object,
    chunk_records: tuple[HistoricalChunkRecord, ...],
) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "coverage_summary must be a non-empty mapping"
        raise DataFoundationValidationError(msg)
    frozen = _freeze_json_value(value, "coverage_summary")
    if not isinstance(frozen, Mapping):
        msg = "coverage_summary must be a non-empty mapping"
        raise DataFoundationValidationError(msg)
    if "expected_chunk_ids" not in frozen:
        msg = "coverage_summary.expected_chunk_ids is required for no-silent-gaps reconciliation"
        raise DataFoundationValidationError(msg)

    _reject_quality_pass_claim(frozen, "coverage_summary")
    expected_chunk_ids = _normalize_expected_chunk_ids(frozen["expected_chunk_ids"])
    record_ids = tuple(chunk.chunk_id for chunk in chunk_records)
    missing = tuple(sorted(set(expected_chunk_ids) - set(record_ids)))
    unexpected = tuple(sorted(set(record_ids) - set(expected_chunk_ids)))
    if missing:
        msg = "missing expected chunks fail closed: " + ", ".join(missing)
        raise DataFoundationValidationError(msg)
    if unexpected:
        msg = "unexpected chunk_records fail closed: " + ", ".join(unexpected)
        raise DataFoundationValidationError(msg)

    counts = {
        "expected_chunk_count": len(expected_chunk_ids),
        "recorded_chunk_count": len(chunk_records),
        "not_started_count": sum(
            chunk.status is HistoricalChunkStatus.NOT_STARTED for chunk in chunk_records
        ),
        "in_progress_count": sum(
            chunk.status is HistoricalChunkStatus.IN_PROGRESS for chunk in chunk_records
        ),
        "complete_count": sum(
            chunk.status is HistoricalChunkStatus.COMPLETE for chunk in chunk_records
        ),
        "incomplete_count": sum(
            chunk.status is HistoricalChunkStatus.INCOMPLETE for chunk in chunk_records
        ),
        "failed_count": sum(
            chunk.status is HistoricalChunkStatus.FAILED for chunk in chunk_records
        ),
        "quarantined_count": sum(
            chunk.status is HistoricalChunkStatus.QUARANTINED for chunk in chunk_records
        ),
    }

    normalized = dict(frozen)
    for key, expected_value in counts.items():
        if key in normalized and normalized[key] != expected_value:
            msg = f"coverage_summary.{key} does not reconcile with chunk_records"
            raise DataFoundationValidationError(msg)
        normalized[key] = expected_value
    normalized["expected_chunk_ids"] = expected_chunk_ids
    normalized["missing_chunk_ids"] = ()
    normalized["quality_status"] = "not_quality_checked"
    return MappingProxyType(normalized)


def _normalize_error_summary(
    value: object,
    chunk_records: tuple[HistoricalChunkRecord, ...],
) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "error_summary must be a non-empty mapping"
        raise DataFoundationValidationError(msg)
    frozen = _freeze_json_value(value, "error_summary")
    if not isinstance(frozen, Mapping):
        msg = "error_summary must be a non-empty mapping"
        raise DataFoundationValidationError(msg)
    if "error_refs" not in frozen:
        msg = "error_summary.error_refs is required"
        raise DataFoundationValidationError(msg)
    _reject_quality_pass_claim(frozen, "error_summary")

    if isinstance(frozen["error_refs"], str) or not isinstance(
        frozen["error_refs"],
        Iterable,
    ):
        msg = "error_summary.error_refs must be an iterable of references"
        raise DataFoundationValidationError(msg)
    supplied_error_refs = tuple(
        _require_reference(error_ref, "error_summary.error_refs[]")
        for error_ref in frozen["error_refs"]
    )
    duplicates = sorted(
        {error_ref for error_ref in supplied_error_refs if supplied_error_refs.count(error_ref) > 1}
    )
    if duplicates:
        msg = "error_summary.error_refs contains duplicates: " + ", ".join(duplicates)
        raise DataFoundationValidationError(msg)

    chunk_error_refs = tuple(
        sorted(chunk.error_ref for chunk in chunk_records if chunk.error_ref is not None)
    )
    if tuple(sorted(supplied_error_refs)) != chunk_error_refs:
        msg = "error_summary.error_refs does not reconcile with chunk_records"
        raise DataFoundationValidationError(msg)

    normalized = dict(frozen)
    if "error_count" in normalized and normalized["error_count"] != len(chunk_error_refs):
        msg = "error_summary.error_count does not reconcile with chunk_records"
        raise DataFoundationValidationError(msg)
    normalized["error_refs"] = supplied_error_refs
    normalized["error_count"] = len(chunk_error_refs)
    return MappingProxyType(normalized)


def compute_historical_pull_resume_token(
    *,
    pull_id: object,
    manifest_id: object,
    chunk_records: object,
) -> str:
    """Compute a deterministic resume token over recorded pull state."""

    normalized_chunk_records = _coerce_chunk_records(chunk_records)
    digest = _stable_hash(
        {
            "schema": HISTORICAL_PULL_RESUME_TOKEN_SCHEMA,
            "pull_id": _normalize_id(pull_id, "pull_id"),
            "manifest_id": _normalize_id(manifest_id, "manifest_id"),
            "chunk_records": tuple(chunk.to_mapping() for chunk in normalized_chunk_records),
        }
    )
    return f"sha256:{digest}"


@dataclass(frozen=True, slots=True)
class HistoricalPullLedger:
    """Audit and resume ledger for one manifest pull attempt."""

    pull_id: str
    manifest_id: str
    chunk_records: tuple[HistoricalChunkRecord, ...]
    started_at: datetime
    finished_at: datetime | None
    status: HistoricalPullLedgerStatus
    resume_token: str | None
    coverage_summary: Mapping[str, object]
    error_summary: Mapping[str, object]

    def __post_init__(self) -> None:
        pull_id = _normalize_id(self.pull_id, "pull_id")
        manifest_id = _normalize_id(self.manifest_id, "manifest_id")
        chunk_records = _coerce_chunk_records(self.chunk_records)
        _detect_chunk_duplicates(chunk_records)
        started_at = _parse_aware_datetime(self.started_at, "started_at")
        finished_at = _parse_optional_aware_datetime(self.finished_at, "finished_at")
        status = _normalize_pull_ledger_status(self.status)
        coverage_summary = _normalize_coverage_summary(self.coverage_summary, chunk_records)
        error_summary = _normalize_error_summary(self.error_summary, chunk_records)

        if finished_at is not None and finished_at < started_at:
            msg = "finished_at must be greater than or equal to started_at"
            raise DataFoundationValidationError(msg)
        derived_status = _derive_pull_status(chunk_records)
        if status is not derived_status:
            msg = "HistoricalPullLedger status does not reconcile with chunk_records"
            raise DataFoundationValidationError(msg)
        terminal_statuses = {
            HistoricalPullLedgerStatus.COMPLETE,
            HistoricalPullLedgerStatus.INCOMPLETE,
            HistoricalPullLedgerStatus.FAILED,
            HistoricalPullLedgerStatus.QUARANTINED,
        }
        if status in terminal_statuses and finished_at is None:
            msg = f"{status.value} ledgers require finished_at"
            raise DataFoundationValidationError(msg)
        if status not in terminal_statuses and finished_at is not None:
            msg = f"{status.value} ledgers must not carry finished_at"
            raise DataFoundationValidationError(msg)

        computed_resume_token = compute_historical_pull_resume_token(
            pull_id=pull_id,
            manifest_id=manifest_id,
            chunk_records=chunk_records,
        )
        supplied_resume_token = _normalize_resume_token(self.resume_token)
        if supplied_resume_token is not None and supplied_resume_token != computed_resume_token:
            msg = "resume_token does not match HistoricalPullLedger state"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "pull_id", pull_id)
        object.__setattr__(self, "manifest_id", manifest_id)
        object.__setattr__(self, "chunk_records", chunk_records)
        object.__setattr__(self, "started_at", started_at)
        object.__setattr__(self, "finished_at", finished_at)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "resume_token", computed_resume_token)
        object.__setattr__(self, "coverage_summary", coverage_summary)
        object.__setattr__(self, "error_summary", error_summary)

    @classmethod
    def create(
        cls,
        *,
        pull_id: str,
        manifest_id: str,
        chunk_records: Iterable[HistoricalChunkRecord | Mapping[str, object]],
        expected_chunk_ids: Iterable[str],
        started_at: datetime,
        finished_at: datetime | None = None,
    ) -> HistoricalPullLedger:
        """Create a ledger with computed status, summaries, and resume token."""

        chunks = _coerce_chunk_records(tuple(chunk_records))
        _detect_chunk_duplicates(chunks)
        status = _derive_pull_status(chunks)
        error_refs = tuple(
            sorted(chunk.error_ref for chunk in chunks if chunk.error_ref is not None)
        )
        return cls(
            pull_id=pull_id,
            manifest_id=manifest_id,
            chunk_records=chunks,
            started_at=started_at,
            finished_at=finished_at,
            status=status,
            resume_token=None,
            coverage_summary={
                "expected_chunk_ids": tuple(expected_chunk_ids),
                "quality_status": "not_quality_checked",
            },
            error_summary={
                "error_refs": error_refs,
            },
        )

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> HistoricalPullLedger:
        """Build a pull ledger from persisted data and validate its token."""

        missing = tuple(
            field for field in REQUIRED_HISTORICAL_PULL_LEDGER_FIELDS if field not in values
        )
        if missing:
            msg = "HistoricalPullLedger missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        return cls(
            pull_id=_require_text(values["pull_id"], "pull_id"),
            manifest_id=_require_text(values["manifest_id"], "manifest_id"),
            chunk_records=_coerce_chunk_records(values["chunk_records"]),
            started_at=_parse_aware_datetime(values["started_at"], "started_at"),
            finished_at=_parse_optional_aware_datetime(values["finished_at"], "finished_at"),
            status=_normalize_pull_ledger_status(values["status"]),
            resume_token=_normalize_resume_token(values["resume_token"]),
            coverage_summary=_normalize_coverage_summary(
                values["coverage_summary"],
                _coerce_chunk_records(values["chunk_records"]),
            ),
            error_summary=_normalize_error_summary(
                values["error_summary"],
                _coerce_chunk_records(values["chunk_records"]),
            ),
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable pull ledger with no quality-pass claim."""

        return MappingProxyType(
            {
                "pull_id": self.pull_id,
                "manifest_id": self.manifest_id,
                "chunk_records": tuple(chunk.to_mapping() for chunk in self.chunk_records),
                "started_at": self.started_at.isoformat(),
                "finished_at": self.finished_at.isoformat()
                if self.finished_at is not None
                else None,
                "status": self.status.value,
                "resume_token": self.resume_token,
                "coverage_summary": self.coverage_summary,
                "error_summary": self.error_summary,
            }
        )

    def pending_chunk_ids_for_resume(self, resume_token: object) -> tuple[str, ...]:
        """Return chunks that may be requested again for the matching token."""

        token = _normalize_resume_token(resume_token)
        if token != self.resume_token:
            msg = "resume_token does not match recorded ledger state"
            raise DataFoundationValidationError(msg)
        return tuple(
            chunk.chunk_id
            for chunk in self.chunk_records
            if chunk.status is not HistoricalChunkStatus.COMPLETE
        )

    def completed_chunk_ids(self) -> tuple[str, ...]:
        """Return chunk IDs that resume must not regenerate."""

        return tuple(
            chunk.chunk_id
            for chunk in self.chunk_records
            if chunk.status is HistoricalChunkStatus.COMPLETE
        )


class DataIngestionRunRecord:
    """DATA-P10 placeholder for a historical ingestion run record."""


__all__ = [
    "ALLOWED_HISTORICAL_SEC_TYPES",
    "DataIngestionRunRecord",
    "HISTORICAL_REQUEST_MANIFEST_HASH_SCHEMA",
    "HISTORICAL_PULL_RESUME_TOKEN_SCHEMA",
    "HistoricalChunkStatus",
    "HistoricalChunkRecord",
    "HistoricalPullLedgerStatus",
    "HistoricalPullLedger",
    "HistoricalRequestLifecycleState",
    "HistoricalRequestManifest",
    "HistoricalRequestSpec",
    "ProviderErrorResolution",
    "ProviderErrorRecord",
    "REQUIRED_HISTORICAL_CHUNK_RECORD_FIELDS",
    "REQUIRED_HISTORICAL_PULL_LEDGER_FIELDS",
    "REQUIRED_HISTORICAL_REQUEST_MANIFEST_FIELDS",
    "REQUIRED_HISTORICAL_REQUEST_SPEC_FIELDS",
    "REQUIRED_PROVIDER_ERROR_RECORD_FIELDS",
    "REQUIRED_REQUEST_PACING_POLICY_FIELDS",
    "RequestPacingPolicy",
    "authorize_historical_request_transition",
    "compute_historical_pull_resume_token",
    "compute_historical_request_manifest_hash",
    "forbid_naive_request_loop",
    "plan_historical_request_transition",
    "provider_pull_manifest_guard",
    "provider_pull_pacing_guard",
    "require_pacing_policy_for_provider_pull",
    "require_validated_manifest_for_provider_pull",
]
