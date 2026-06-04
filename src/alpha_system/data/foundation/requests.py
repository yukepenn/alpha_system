"""Historical request specs, manifests, and pull preflight guards.

DATA-P07 owns request planning only. This module performs no provider calls,
opens no sockets, imports no IBKR client library, writes no market data, and
does not authorize a pull. Later DATA-P08+ phases own pacing execution, chunks,
ledgers, provider errors, raw storage, and ingestion runs.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
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

HISTORICAL_REQUEST_MANIFEST_HASH_SCHEMA = "alpha_system.historical_request_manifest.v1"

ALLOWED_HISTORICAL_SEC_TYPES: frozenset[str] = frozenset({"FUT", "CONTFUT"})
_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class HistoricalRequestLifecycleState(StrEnum):
    """DATA-P07 request lifecycle states encoded before any provider call."""

    NOT_REQUESTED = "NOT_REQUESTED"
    REQUEST_PLANNED = "REQUEST_PLANNED"
    REQUEST_AUTHORIZED = "REQUEST_AUTHORIZED"


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


class HistoricalChunkRecord:
    """DATA-P08 placeholder for one chunk request lifecycle record."""


class HistoricalPullLedger:
    """DATA-P08 placeholder for pull audit and resume state."""


class ProviderErrorRecord:
    """DATA-P08 placeholder for provider error metadata."""


class RequestPacingPolicy:
    """DATA-P08 placeholder for historical request pacing rules."""


class DataIngestionRunRecord:
    """DATA-P10 placeholder for a historical ingestion run record."""


__all__ = [
    "ALLOWED_HISTORICAL_SEC_TYPES",
    "DataIngestionRunRecord",
    "HISTORICAL_REQUEST_MANIFEST_HASH_SCHEMA",
    "HistoricalChunkRecord",
    "HistoricalPullLedger",
    "HistoricalRequestLifecycleState",
    "HistoricalRequestManifest",
    "HistoricalRequestSpec",
    "ProviderErrorRecord",
    "REQUIRED_HISTORICAL_REQUEST_MANIFEST_FIELDS",
    "REQUIRED_HISTORICAL_REQUEST_SPEC_FIELDS",
    "RequestPacingPolicy",
    "authorize_historical_request_transition",
    "compute_historical_request_manifest_hash",
    "plan_historical_request_transition",
    "provider_pull_manifest_guard",
    "require_validated_manifest_for_provider_pull",
]
