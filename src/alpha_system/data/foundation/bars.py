"""Raw, parsed, and canonical bar-layer records.

DATA-P09 owns the immutable raw provider-response record and local-only raw
data-lake layout policy. DATA-P14 and DATA-P15 own parser, canonicalization,
timestamp, and quality behavior.
"""

from __future__ import annotations

import csv
import hashlib
import io
import os
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import InitVar, dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType

from alpha_system.data.foundation.sources import (
    DataFoundationValidationError,
    LocalDataRootPolicy,
    require_local_data_root_policy,
)

REQUIRED_RAW_DATA_OBJECT_FIELDS: tuple[str, ...] = (
    "raw_object_id",
    "source",
    "request_id",
    "chunk_id",
    "path",
    "content_hash",
    "schema_hint",
    "retrieved_at",
    "row_count",
)

PARSED_BAR_RECORD_FIELDS: tuple[str, ...] = (
    "source",
    "symbol",
    "contract_ref",
    "provider_ts",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "wap_if_available",
    "bar_count_if_available",
    "request_id",
    "raw_object_id",
)

REQUIRED_PARSED_BAR_RECORD_FIELDS: tuple[str, ...] = (
    "source",
    "symbol",
    "contract_ref",
    "provider_ts",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "request_id",
    "raw_object_id",
)

RAW_DATA_LAKE_SUBDIR = "raw"
RAW_DATA_OBJECT_SUFFIX = ".raw"
REPO_DATA_PLACEHOLDER_FILENAMES: frozenset[str] = frozenset({"README.md", ".gitkeep"})

RawPayloadLoader = Callable[["RawDataObject"], bytes | str]

_SHA256_CONTENT_HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
_SAFE_PATH_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_FORBIDDEN_SCHEMA_HINT_TOKENS: frozenset[str] = frozenset(
    {
        "canonical",
        "canonical_truth",
        "quality_passed",
        "research_ready",
        "versioned_truth",
    }
)
_FORBIDDEN_PARSED_BAR_FIELDS: frozenset[str] = frozenset(
    {
        "available_ts",
        "bar_end_ts",
        "bar_start_ts",
        "event_ts",
        "ingested_at",
        "session",
        "session_id",
        "session_label",
    }
)
_CSV_PROVIDER_BAR_ALIASES: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "symbol": ("symbol", "provider_symbol"),
        "contract_ref": ("contract_ref", "provider_contract_ref", "contract", "local_symbol"),
        "provider_ts": ("provider_ts", "date", "time"),
        "open": ("open",),
        "high": ("high",),
        "low": ("low",),
        "close": ("close",),
        "volume": ("volume",),
        "wap_if_available": ("wap_if_available", "wap", "vwap"),
        "bar_count_if_available": ("bar_count_if_available", "bar_count", "barCount"),
    }
)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    normalized = value.strip()
    if not normalized:
        msg = f"{field_name} must be a non-empty string"
        raise DataFoundationValidationError(msg)
    if "\n" in normalized or "\r" in normalized:
        msg = f"{field_name} must be a single-line string"
        raise DataFoundationValidationError(msg)
    return normalized


def _normalize_id(value: object, field_name: str) -> str:
    token = _require_text(value, field_name)
    if not _SAFE_PATH_TOKEN_PATTERN.fullmatch(token):
        msg = f"{field_name} must be an alphanumeric identifier"
        raise DataFoundationValidationError(msg)
    return token


def _normalize_source(value: object) -> str:
    source = _normalize_id(value, "source")
    if not source.startswith("dsrc_"):
        msg = "source must link to a DataSourceProfile source_id with dsrc_ prefix"
        raise DataFoundationValidationError(msg)
    return source


def _normalize_content_hash(value: object) -> str:
    content_hash = _require_text(value, "content_hash").lower()
    if not _SHA256_CONTENT_HASH_PATTERN.fullmatch(content_hash):
        msg = "content_hash must use sha256:<64 hex digest>"
        raise DataFoundationValidationError(msg)
    return content_hash


def _content_digest(content_hash: object) -> str:
    return _normalize_content_hash(content_hash).removeprefix("sha256:")


def _normalize_path(value: object) -> Path:
    if not isinstance(value, (str, os.PathLike)):
        msg = "path must be a string or path-like local raw object path"
        raise DataFoundationValidationError(msg)
    raw = os.fspath(value).strip()
    if not raw:
        msg = "path must be a non-empty local raw object path"
        raise DataFoundationValidationError(msg)
    if raw.startswith(("//", "\\\\")):
        msg = "path must not use a network path"
        raise DataFoundationValidationError(msg)
    return Path(raw).expanduser().resolve(strict=False)


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


def _require_non_negative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be a non-negative integer"
        raise DataFoundationValidationError(msg)
    if value < 0:
        msg = f"{field_name} must be non-negative"
        raise DataFoundationValidationError(msg)
    return value


def _parse_non_negative_int(value: object, field_name: str) -> int:
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            msg = f"{field_name} must be a non-negative integer"
            raise DataFoundationValidationError(msg)
        try:
            parsed = int(raw, 10)
        except ValueError as exc:
            msg = f"{field_name} must be a non-negative integer"
            raise DataFoundationValidationError(msg) from exc
        return _require_non_negative_int(parsed, field_name)
    return _require_non_negative_int(value, field_name)


def _require_finite_decimal(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        msg = f"{field_name} must be an exact finite decimal value"
        raise DataFoundationValidationError(msg)
    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, int):
        parsed = Decimal(value)
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            msg = f"{field_name} must be an exact finite decimal value"
            raise DataFoundationValidationError(msg)
        try:
            parsed = Decimal(raw)
        except InvalidOperation as exc:
            msg = f"{field_name} must be an exact finite decimal value"
            raise DataFoundationValidationError(msg) from exc
    else:
        msg = f"{field_name} must be an exact finite decimal value"
        raise DataFoundationValidationError(msg)

    if not parsed.is_finite():
        msg = f"{field_name} must be finite"
        raise DataFoundationValidationError(msg)
    return parsed


def _require_non_negative_decimal(value: object, field_name: str) -> Decimal:
    parsed = _require_finite_decimal(value, field_name)
    if parsed < 0:
        msg = f"{field_name} must be non-negative"
        raise DataFoundationValidationError(msg)
    return parsed


def _optional_non_negative_decimal(value: object, field_name: str) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return _require_non_negative_decimal(value, field_name)


def _optional_non_negative_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return _parse_non_negative_int(value, field_name)


def _normalize_schema_hint(value: object) -> str:
    schema_hint = _require_text(value, "schema_hint")
    token = schema_hint.lower().replace("-", "_").replace(" ", "_")
    if token in _FORBIDDEN_SCHEMA_HINT_TOKENS:
        msg = "schema_hint must be a provider-shape hint and must not imply canonical truth"
        raise DataFoundationValidationError(msg)
    return schema_hint


def _raw_layout_token(value: object, field_name: str) -> str:
    return _normalize_id(value, field_name)


def raw_object_ref_for_content_hash(content_hash: object) -> str:
    """Return the DATA-P08-compatible raw object ref for a content hash."""

    return "raw://sha256/" + _content_digest(content_hash)


@dataclass(frozen=True, slots=True)
class RawDataLakeLayoutPolicy:
    """Pure local path policy for immutable raw provider responses."""

    local_data_root_policy: LocalDataRootPolicy
    raw_subdir: str = RAW_DATA_LAKE_SUBDIR
    object_suffix: str = RAW_DATA_OBJECT_SUFFIX

    def __post_init__(self) -> None:
        local_policy = require_local_data_root_policy(self.local_data_root_policy)
        raw_subdir = _raw_layout_token(self.raw_subdir, "raw_subdir")
        object_suffix = _require_text(self.object_suffix, "object_suffix")

        if raw_subdir not in local_policy.allowed_subdirs:
            msg = f"raw_subdir {raw_subdir!r} is not allowed by LocalDataRootPolicy"
            raise DataFoundationValidationError(msg)
        if not object_suffix.startswith(".") or "/" in object_suffix or "\\" in object_suffix:
            msg = "object_suffix must be a simple file suffix"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "local_data_root_policy", local_policy)
        object.__setattr__(self, "raw_subdir", raw_subdir)
        object.__setattr__(self, "object_suffix", object_suffix)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> RawDataLakeLayoutPolicy:
        """Build the raw layout policy from ``ALPHA_DATA_ROOT``."""

        return cls(local_data_root_policy=LocalDataRootPolicy.from_env(env))

    def resolve_path(
        self,
        *,
        source: object,
        request_id: object,
        chunk_id: object,
        content_hash: object,
    ) -> Path:
        """Resolve the content-addressed raw object path under ``ALPHA_DATA_ROOT``."""

        normalized_source = _normalize_source(source)
        normalized_request_id = _raw_layout_token(request_id, "request_id")
        normalized_chunk_id = _raw_layout_token(chunk_id, "chunk_id")
        digest = _content_digest(content_hash)
        return (
            self.local_data_root_policy.data_root
            / self.raw_subdir
            / f"source={normalized_source}"
            / f"request={normalized_request_id}"
            / f"chunk={normalized_chunk_id}"
            / f"sha256={digest[:2]}"
            / f"{digest}{self.object_suffix}"
        ).resolve(strict=False)

    def validate_path(
        self,
        path: object,
        *,
        source: object,
        request_id: object,
        chunk_id: object,
        content_hash: object,
    ) -> Path:
        """Validate a raw object path is local-only, linked, and content-addressed."""

        normalized_path = _normalize_path(path)
        data_root = self.local_data_root_policy.data_root
        if not _is_relative_to(normalized_path, data_root):
            msg = f"path must resolve under ALPHA_DATA_ROOT: {data_root.as_posix()}"
            raise DataFoundationValidationError(msg)

        relative = normalized_path.relative_to(data_root)
        if not relative.parts or relative.parts[0] != self.raw_subdir:
            msg = f"path must live under the {self.raw_subdir!r} local data-root subdir"
            raise DataFoundationValidationError(msg)

        digest = _content_digest(content_hash)
        required_parts = {
            f"source={_normalize_source(source)}",
            f"request={_raw_layout_token(request_id, 'request_id')}",
            f"chunk={_raw_layout_token(chunk_id, 'chunk_id')}",
        }
        if not required_parts.issubset(set(relative.parts)):
            msg = "path must be source/request/chunk linked"
            raise DataFoundationValidationError(msg)
        if digest not in relative.as_posix():
            msg = "path must include the content_hash digest"
            raise DataFoundationValidationError(msg)

        return normalized_path


def require_raw_data_lake_layout_policy(
    policy: RawDataLakeLayoutPolicy | None,
) -> RawDataLakeLayoutPolicy:
    """Fail closed unless a validated raw lake layout policy is present."""

    if not isinstance(policy, RawDataLakeLayoutPolicy):
        msg = "missing RawDataLakeLayoutPolicy blocks raw object path resolution"
        raise DataFoundationValidationError(msg)
    return policy


def resolve_raw_object_storage_path(
    *,
    layout_policy: RawDataLakeLayoutPolicy,
    source: object,
    request_id: object,
    chunk_id: object,
    content_hash: object,
) -> Path:
    """Resolve a raw object path with an explicit layout policy."""

    return require_raw_data_lake_layout_policy(layout_policy).resolve_path(
        source=source,
        request_id=request_id,
        chunk_id=chunk_id,
        content_hash=content_hash,
    )


@dataclass(frozen=True, slots=True)
class RawDataObject:
    """Immutable local provider response metadata.

    The content address is ``content_hash``. This record is provenance metadata
    for raw bytes only and does not imply canonical truth or quality acceptance.
    """

    raw_object_id: str
    source: str
    request_id: str
    chunk_id: str
    path: Path
    content_hash: str
    schema_hint: str
    retrieved_at: datetime
    row_count: int
    validation_policy: InitVar[RawDataLakeLayoutPolicy | None] = None

    def __post_init__(self, validation_policy: RawDataLakeLayoutPolicy | None) -> None:
        raw_object_id = _normalize_id(self.raw_object_id, "raw_object_id")
        source = _normalize_source(self.source)
        request_id = _raw_layout_token(self.request_id, "request_id")
        chunk_id = _raw_layout_token(self.chunk_id, "chunk_id")
        content_hash = _normalize_content_hash(self.content_hash)
        schema_hint = _normalize_schema_hint(self.schema_hint)
        retrieved_at = _parse_aware_datetime(self.retrieved_at, "retrieved_at")
        row_count = _require_non_negative_int(self.row_count, "row_count")
        layout_policy = (
            require_raw_data_lake_layout_policy(validation_policy)
            if validation_policy is not None
            else RawDataLakeLayoutPolicy.from_env()
        )
        path = layout_policy.validate_path(
            self.path,
            source=source,
            request_id=request_id,
            chunk_id=chunk_id,
            content_hash=content_hash,
        )

        object.__setattr__(self, "raw_object_id", raw_object_id)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "request_id", request_id)
        object.__setattr__(self, "chunk_id", chunk_id)
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "content_hash", content_hash)
        object.__setattr__(self, "schema_hint", schema_hint)
        object.__setattr__(self, "retrieved_at", retrieved_at)
        object.__setattr__(self, "row_count", row_count)

    @classmethod
    def create(
        cls,
        *,
        raw_object_id: str,
        source: str,
        request_id: str,
        chunk_id: str,
        content_hash: str,
        schema_hint: str,
        retrieved_at: datetime,
        row_count: int,
        layout_policy: RawDataLakeLayoutPolicy,
    ) -> RawDataObject:
        """Create a raw object record by resolving the path from an explicit policy."""

        policy = require_raw_data_lake_layout_policy(layout_policy)
        path = policy.resolve_path(
            source=source,
            request_id=request_id,
            chunk_id=chunk_id,
            content_hash=content_hash,
        )
        return cls(
            raw_object_id=raw_object_id,
            source=source,
            request_id=request_id,
            chunk_id=chunk_id,
            path=path,
            content_hash=content_hash,
            schema_hint=schema_hint,
            retrieved_at=retrieved_at,
            row_count=row_count,
            validation_policy=policy,
        )

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, object],
        *,
        layout_policy: RawDataLakeLayoutPolicy | None = None,
    ) -> RawDataObject:
        """Build a raw object from persisted metadata and fail closed."""

        missing = tuple(field for field in REQUIRED_RAW_DATA_OBJECT_FIELDS if field not in values)
        if missing:
            msg = "RawDataObject missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        return cls(
            raw_object_id=_require_text(values["raw_object_id"], "raw_object_id"),
            source=_require_text(values["source"], "source"),
            request_id=_require_text(values["request_id"], "request_id"),
            chunk_id=_require_text(values["chunk_id"], "chunk_id"),
            path=_normalize_path(values["path"]),
            content_hash=_require_text(values["content_hash"], "content_hash"),
            schema_hint=_require_text(values["schema_hint"], "schema_hint"),
            retrieved_at=_parse_aware_datetime(values["retrieved_at"], "retrieved_at"),
            row_count=_require_non_negative_int(values["row_count"], "row_count"),
            validation_policy=layout_policy,
        )

    @property
    def raw_object_ref(self) -> str:
        """Return a DATA-P08-compatible immutable raw ref."""

        return raw_object_ref_for_content_hash(self.content_hash)

    @property
    def logical_slot(self) -> tuple[str, str, str]:
        """Return the source/request/chunk slot protected by no-overwrite checks."""

        return (self.source, self.request_id, self.chunk_id)

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable raw object metadata record."""

        return MappingProxyType(
            {
                "raw_object_id": self.raw_object_id,
                "source": self.source,
                "request_id": self.request_id,
                "chunk_id": self.chunk_id,
                "path": self.path.as_posix(),
                "content_hash": self.content_hash,
                "schema_hint": self.schema_hint,
                "retrieved_at": self.retrieved_at.isoformat(),
                "row_count": self.row_count,
            }
        )


def assert_raw_slot_immutable(
    existing: RawDataObject | Mapping[str, object] | None,
    candidate: RawDataObject | Mapping[str, object],
) -> RawDataObject:
    """Reject binding a different content hash to an existing logical raw slot."""

    candidate_object = (
        candidate if isinstance(candidate, RawDataObject) else RawDataObject.from_mapping(candidate)
    )
    if existing is None:
        return candidate_object
    existing_object = (
        existing if isinstance(existing, RawDataObject) else RawDataObject.from_mapping(existing)
    )
    if existing_object.logical_slot != candidate_object.logical_slot:
        return candidate_object
    if existing_object.content_hash != candidate_object.content_hash:
        msg = "raw object slot is immutable; a different content_hash would overwrite raw data"
        raise DataFoundationValidationError(msg)
    return existing_object


@dataclass(frozen=True, slots=True, kw_only=True)
class ParsedBarRecord:
    """Provider-shaped parsed bar with raw-object provenance.

    This is a bronze parsed record. ``provider_ts`` is kept as provider-supplied
    text and does not carry canonical timestamp semantics.
    """

    source: str
    symbol: str
    contract_ref: str
    provider_ts: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    wap_if_available: Decimal | None = None
    bar_count_if_available: int | None = None
    request_id: str
    raw_object_id: str

    def __post_init__(self) -> None:
        source = _normalize_source(self.source)
        symbol = _require_text(self.symbol, "symbol")
        contract_ref = _require_text(self.contract_ref, "contract_ref")
        provider_ts = _require_text(self.provider_ts, "provider_ts")
        open_price = _require_finite_decimal(self.open, "open")
        high_price = _require_finite_decimal(self.high, "high")
        low_price = _require_finite_decimal(self.low, "low")
        close_price = _require_finite_decimal(self.close, "close")
        volume = _require_non_negative_decimal(self.volume, "volume")
        wap_if_available = _optional_non_negative_decimal(
            self.wap_if_available,
            "wap_if_available",
        )
        bar_count_if_available = _optional_non_negative_int(
            self.bar_count_if_available,
            "bar_count_if_available",
        )
        request_id = _raw_layout_token(self.request_id, "request_id")
        raw_object_id = _normalize_id(self.raw_object_id, "raw_object_id")

        object.__setattr__(self, "source", source)
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "contract_ref", contract_ref)
        object.__setattr__(self, "provider_ts", provider_ts)
        object.__setattr__(self, "open", open_price)
        object.__setattr__(self, "high", high_price)
        object.__setattr__(self, "low", low_price)
        object.__setattr__(self, "close", close_price)
        object.__setattr__(self, "volume", volume)
        object.__setattr__(self, "wap_if_available", wap_if_available)
        object.__setattr__(self, "bar_count_if_available", bar_count_if_available)
        object.__setattr__(self, "request_id", request_id)
        object.__setattr__(self, "raw_object_id", raw_object_id)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> ParsedBarRecord:
        """Build a parsed bar from a mapping and reject canonical-layer fields."""

        extra = tuple(field for field in values if field not in PARSED_BAR_RECORD_FIELDS)
        canonical_extra = tuple(
            field for field in extra if field.lower() in _FORBIDDEN_PARSED_BAR_FIELDS
        )
        if canonical_extra:
            msg = "ParsedBarRecord must not include canonical timestamp/session fields: "
            raise DataFoundationValidationError(msg + ", ".join(canonical_extra))
        if extra:
            msg = "ParsedBarRecord includes unsupported fields: "
            raise DataFoundationValidationError(msg + ", ".join(extra))

        missing = tuple(field for field in REQUIRED_PARSED_BAR_RECORD_FIELDS if field not in values)
        if missing:
            msg = "ParsedBarRecord missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)

        return cls(
            source=_require_text(values["source"], "source"),
            symbol=_require_text(values["symbol"], "symbol"),
            contract_ref=_require_text(values["contract_ref"], "contract_ref"),
            provider_ts=_require_text(values["provider_ts"], "provider_ts"),
            open=_require_finite_decimal(values["open"], "open"),
            high=_require_finite_decimal(values["high"], "high"),
            low=_require_finite_decimal(values["low"], "low"),
            close=_require_finite_decimal(values["close"], "close"),
            volume=_require_non_negative_decimal(values["volume"], "volume"),
            wap_if_available=_optional_non_negative_decimal(
                values.get("wap_if_available"),
                "wap_if_available",
            ),
            bar_count_if_available=_optional_non_negative_int(
                values.get("bar_count_if_available"),
                "bar_count_if_available",
            ),
            request_id=_require_text(values["request_id"], "request_id"),
            raw_object_id=_require_text(values["raw_object_id"], "raw_object_id"),
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable provider-shaped parsed bar mapping."""

        return MappingProxyType(
            {
                "source": self.source,
                "symbol": self.symbol,
                "contract_ref": self.contract_ref,
                "provider_ts": self.provider_ts,
                "open": str(self.open),
                "high": str(self.high),
                "low": str(self.low),
                "close": str(self.close),
                "volume": str(self.volume),
                "wap_if_available": (
                    None if self.wap_if_available is None else str(self.wap_if_available)
                ),
                "bar_count_if_available": self.bar_count_if_available,
                "request_id": self.request_id,
                "raw_object_id": self.raw_object_id,
            }
        )


def _normalize_csv_header_name(value: object) -> str:
    return _require_text(value, "CSV header").lower().replace(" ", "_")


def _csv_field_map(fieldnames: list[str] | None) -> Mapping[str, str]:
    if fieldnames is None:
        msg = "raw bar CSV payload must include a header row"
        raise DataFoundationValidationError(msg)

    normalized: dict[str, str] = {}
    for fieldname in fieldnames:
        token = _normalize_csv_header_name(fieldname)
        if token in normalized:
            msg = f"raw bar CSV payload has duplicate column after normalization: {fieldname}"
            raise DataFoundationValidationError(msg)
        normalized[token] = fieldname
    return MappingProxyType(normalized)


def _csv_row_value(
    row: Mapping[str, str | None],
    field_map: Mapping[str, str],
    field_name: str,
    *,
    row_number: int,
    required: bool,
) -> str | None:
    for alias in _CSV_PROVIDER_BAR_ALIASES[field_name]:
        source_field = field_map.get(_normalize_csv_header_name(alias))
        if source_field is None:
            continue
        value = row.get(source_field)
        if value is None:
            msg = f"raw bar CSV row {row_number} missing value for {source_field}"
            raise DataFoundationValidationError(msg)
        normalized = value.strip()
        if not normalized:
            if required:
                msg = f"raw bar CSV row {row_number} has empty {source_field}"
                raise DataFoundationValidationError(msg)
            return None
        return normalized

    if required:
        aliases = ", ".join(_CSV_PROVIDER_BAR_ALIASES[field_name])
        msg = f"raw bar CSV payload missing required provider column for {field_name}: {aliases}"
        raise DataFoundationValidationError(msg)
    return None


def _payload_as_bytes(payload: bytes | str, *, encoding: str) -> bytes:
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, str):
        return payload.encode(encoding)
    msg = "raw payload loader must return bytes or text"
    raise DataFoundationValidationError(msg)


def _load_raw_payload(raw_object: RawDataObject) -> bytes:
    try:
        return raw_object.path.read_bytes()
    except OSError as exc:
        msg = f"raw object path is not readable for {raw_object.raw_object_id}"
        raise DataFoundationValidationError(msg) from exc


def _validate_payload_hash(raw_object: RawDataObject, payload: bytes) -> None:
    actual = hashlib.sha256(payload).hexdigest()
    expected = _content_digest(raw_object.content_hash)
    if actual != expected:
        msg = f"raw payload hash mismatch for {raw_object.raw_object_id}"
        raise DataFoundationValidationError(msg)


def _parse_csv_bar_payload(
    *,
    raw_object: RawDataObject,
    payload: bytes,
    encoding: str,
) -> tuple[ParsedBarRecord, ...]:
    try:
        text = payload.decode(encoding)
    except UnicodeDecodeError as exc:
        msg = f"raw bar payload for {raw_object.raw_object_id} is not valid {encoding}"
        raise DataFoundationValidationError(msg) from exc

    if not text.strip():
        if raw_object.row_count == 0:
            return ()
        msg = f"raw bar payload for {raw_object.raw_object_id} is empty"
        raise DataFoundationValidationError(msg)

    reader = csv.DictReader(io.StringIO(text))
    field_map = _csv_field_map(reader.fieldnames)

    records: list[ParsedBarRecord] = []
    for row_number, row in enumerate(reader, start=2):
        if None in row:
            msg = f"raw bar CSV row {row_number} has more columns than the header"
            raise DataFoundationValidationError(msg)
        record = ParsedBarRecord.from_mapping(
            {
                "source": raw_object.source,
                "symbol": _csv_row_value(
                    row,
                    field_map,
                    "symbol",
                    row_number=row_number,
                    required=True,
                ),
                "contract_ref": _csv_row_value(
                    row,
                    field_map,
                    "contract_ref",
                    row_number=row_number,
                    required=True,
                ),
                "provider_ts": _csv_row_value(
                    row,
                    field_map,
                    "provider_ts",
                    row_number=row_number,
                    required=True,
                ),
                "open": _csv_row_value(
                    row,
                    field_map,
                    "open",
                    row_number=row_number,
                    required=True,
                ),
                "high": _csv_row_value(
                    row,
                    field_map,
                    "high",
                    row_number=row_number,
                    required=True,
                ),
                "low": _csv_row_value(
                    row,
                    field_map,
                    "low",
                    row_number=row_number,
                    required=True,
                ),
                "close": _csv_row_value(
                    row,
                    field_map,
                    "close",
                    row_number=row_number,
                    required=True,
                ),
                "volume": _csv_row_value(
                    row,
                    field_map,
                    "volume",
                    row_number=row_number,
                    required=True,
                ),
                "wap_if_available": _csv_row_value(
                    row,
                    field_map,
                    "wap_if_available",
                    row_number=row_number,
                    required=False,
                ),
                "bar_count_if_available": _csv_row_value(
                    row,
                    field_map,
                    "bar_count_if_available",
                    row_number=row_number,
                    required=False,
                ),
                "request_id": raw_object.request_id,
                "raw_object_id": raw_object.raw_object_id,
            }
        )
        records.append(record)

    if len(records) != raw_object.row_count:
        msg = (
            f"raw object {raw_object.raw_object_id} row_count={raw_object.row_count} "
            f"but parser produced {len(records)} rows"
        )
        raise DataFoundationValidationError(msg)
    return tuple(records)


@dataclass(frozen=True, slots=True)
class ParsedBarParser:
    """Deterministic parser from immutable raw objects to provider-shaped bars."""

    layout_policy: RawDataLakeLayoutPolicy | None = None
    raw_payload_loader: RawPayloadLoader | None = None
    encoding: str = "utf-8"

    def __post_init__(self) -> None:
        if self.layout_policy is not None:
            object.__setattr__(
                self,
                "layout_policy",
                require_raw_data_lake_layout_policy(self.layout_policy),
            )
        if self.raw_payload_loader is not None and not callable(self.raw_payload_loader):
            msg = "raw_payload_loader must be callable"
            raise DataFoundationValidationError(msg)
        object.__setattr__(self, "encoding", _require_text(self.encoding, "encoding"))

    def _coerce_raw_object(self, value: RawDataObject | Mapping[str, object]) -> RawDataObject:
        if isinstance(value, RawDataObject):
            raw_object = value
        elif isinstance(value, Mapping):
            raw_object = RawDataObject.from_mapping(value, layout_policy=self.layout_policy)
        else:
            msg = "raw_objects must contain RawDataObject records or mappings"
            raise DataFoundationValidationError(msg)

        if self.layout_policy is not None:
            self.layout_policy.validate_path(
                raw_object.path,
                source=raw_object.source,
                request_id=raw_object.request_id,
                chunk_id=raw_object.chunk_id,
                content_hash=raw_object.content_hash,
            )
        return raw_object

    def parse(
        self,
        raw_objects: RawDataObject
        | Mapping[str, object]
        | Iterable[RawDataObject | Mapping[str, object]],
    ) -> tuple[ParsedBarRecord, ...]:
        """Parse one or more immutable raw object refs into parsed bars."""

        if isinstance(raw_objects, (RawDataObject, Mapping)):
            candidates = (raw_objects,)
        else:
            candidates = tuple(raw_objects)
        if not candidates:
            msg = "raw_objects must not be empty"
            raise DataFoundationValidationError(msg)

        records: list[ParsedBarRecord] = []
        loader = self.raw_payload_loader or _load_raw_payload
        for candidate in candidates:
            raw_object = self._coerce_raw_object(candidate)
            payload = _payload_as_bytes(loader(raw_object), encoding=self.encoding)
            _validate_payload_hash(raw_object, payload)
            records.extend(
                _parse_csv_bar_payload(
                    raw_object=raw_object,
                    payload=payload,
                    encoding=self.encoding,
                )
            )
        return tuple(records)


def parse_raw_bar_records(
    raw_objects: RawDataObject
    | Mapping[str, object]
    | Iterable[RawDataObject | Mapping[str, object]],
    *,
    layout_policy: RawDataLakeLayoutPolicy | None = None,
    raw_payload_loader: RawPayloadLoader | None = None,
    encoding: str = "utf-8",
) -> tuple[ParsedBarRecord, ...]:
    """Parse immutable raw bar refs into provider-shaped parsed bar records."""

    parser = ParsedBarParser(
        layout_policy=layout_policy,
        raw_payload_loader=raw_payload_loader,
        encoding=encoding,
    )
    return parser.parse(raw_objects)


class CanonicalBarRecord:
    """DATA-P15 placeholder for a research-ready canonical bar record."""


class TimestampSemanticsPolicy:
    """DATA-P15 placeholder for canonical timestamp semantics."""


__all__ = [
    "CanonicalBarRecord",
    "PARSED_BAR_RECORD_FIELDS",
    "ParsedBarRecord",
    "ParsedBarParser",
    "RAW_DATA_LAKE_SUBDIR",
    "RAW_DATA_OBJECT_SUFFIX",
    "REPO_DATA_PLACEHOLDER_FILENAMES",
    "REQUIRED_PARSED_BAR_RECORD_FIELDS",
    "REQUIRED_RAW_DATA_OBJECT_FIELDS",
    "RawDataLakeLayoutPolicy",
    "RawDataObject",
    "RawPayloadLoader",
    "TimestampSemanticsPolicy",
    "assert_raw_slot_immutable",
    "parse_raw_bar_records",
    "raw_object_ref_for_content_hash",
    "require_raw_data_lake_layout_policy",
    "resolve_raw_object_storage_path",
]
