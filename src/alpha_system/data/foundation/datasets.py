"""Dataset version, quality, coverage, and partition contracts.

DATA-P16 owns the fail-closed quality and coverage reports. DATA-P17 and
DATA-P18 own dataset versioning and partition planning behavior.
"""

from __future__ import annotations

import json
import re
import sqlite3
from bisect import bisect_left
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from math import isfinite
from pathlib import Path
from types import MappingProxyType

from alpha_system.core.hashing import canonical_json, hash_config
from alpha_system.core.registry import (
    connect_registry,
    init_registry,
    is_local_only_registry_path,
    resolve_registry_path,
)
from alpha_system.data.foundation.bars import (
    CANONICAL_BAR_RECORD_FIELDS,
    CanonicalBarRecord,
)
from alpha_system.data.foundation.quotes import (
    BBO_QUARANTINE_QUALITY_FLAG,
    CANONICAL_BBO_RECORD_FIELDS,
    CANONICAL_BBO_REQUIRED_FIELDS,
    MISSING_BBO_QUALITY_FLAG,
    CanonicalBBORecord,
)
from alpha_system.data.foundation.requests import ProviderErrorRecord
from alpha_system.data.foundation.sessions import SUPPORTED_SESSION_TYPES
from alpha_system.data.foundation.sources import DataFoundationValidationError

DATA_QUALITY_REPORT_FIELDS: tuple[str, ...] = (
    "quality_report_id",
    "dataset_version_id",
    "gap_summary",
    "duplicate_summary",
    "non_monotonic_summary",
    "ohlc_errors",
    "zero_negative_price_errors",
    "zero_volume_anomalies",
    "dst_anomalies",
    "session_coverage",
    "roll_discontinuities",
    "provider_error_summary",
    "bbo_missing_metric",
    "abnormal_spread_summary",
    "status",
)

DATA_QUALITY_REPORT_OPTIONAL_FIELDS: frozenset[str] = frozenset(
    {"bbo_missing_metric", "abnormal_spread_summary"}
)
DATA_QUALITY_REPORT_REQUIRED_FIELDS: tuple[str, ...] = tuple(
    field
    for field in DATA_QUALITY_REPORT_FIELDS
    if field not in DATA_QUALITY_REPORT_OPTIONAL_FIELDS
)

COVERAGE_REPORT_FIELDS: tuple[str, ...] = (
    "coverage_report_id",
    "dataset_version_id",
    "symbol_coverage",
    "contract_coverage",
    "session_coverage",
    "partition_coverage",
    "missing_intervals",
    "incomplete_chunks",
)

DATASET_VERSION_FIELDS: tuple[str, ...] = (
    "dataset_version_id",
    "source",
    "symbol_universe",
    "bar_size",
    "what_to_show",
    "start_ts",
    "end_ts",
    "contract_universe",
    "roll_policy_id",
    "manifest_hash",
    "code_hash",
    "config_hash",
    "quality_report_hash",
    "created_at",
)

REQUIRED_DATASET_PARTITION_PLAN_FIELDS: tuple[str, ...] = (
    "plan_id",
    "development_partition",
    "validation_partition",
    "locked_test_candidate",
    "latest_shadow_candidate",
    "contamination_metadata_rules",
)

PARTITION_BOUND_FIELDS: tuple[str, ...] = (
    "partition_id",
    "start_date",
    "end_date",
    "role",
)

LATEST_SHADOW_PARTITION_FIELDS: tuple[str, ...] = (
    "partition_id",
    "start_date",
    "end_date",
    "role",
    "rolling",
    "optional",
)

CONTAMINATION_METADATA_RULE_FIELDS: tuple[str, ...] = (
    "data_qa_coverage_inspection_allowed",
    "locked_partition_ids",
    "locked_partition_use_requires_governance_metadata",
    "locked_partition_use_requires_contamination_metadata",
    "alpha_research_without_governance_metadata",
    "implies_research_approval",
)

CANONICAL_DEVELOPMENT_START = date(2018, 1, 1)
CANONICAL_DEVELOPMENT_END = date(2022, 12, 31)
CANONICAL_VALIDATION_START = date(2023, 1, 1)
CANONICAL_VALIDATION_END = date(2024, 12, 31)
CANONICAL_LOCKED_TEST_START = date(2025, 1, 1)
CANONICAL_LOCKED_TEST_END = "as_of_run"

DATASET_VERSION_ADMISSIBLE_STATES: frozenset[str] = frozenset(
    {"VERSIONED", "READY_FOR_RESEARCH"}
)

DATASET_ACCEPTANCE_STATES: frozenset[str] = frozenset(
    {"ACCEPTED", "ACCEPTED_WITH_WARNINGS", "BLOCKED"}
)

DATASET_ACCEPTANCE_LOCK_METADATA_SCHEMA = (
    "alpha_system.data_foundation.dataset_acceptance_lock.v1"
)

DATASET_ACCEPTANCE_DEFAULT_POLICY_ID = "dataset_acceptance_futsub_p02_v1"

DATASET_ACCEPTANCE_REQUIRED_FIELD_GROUPS: tuple[str, ...] = (
    "canonical_timestamps",
    "available_ts",
    "exchange_trade_date",
    "session_segment",
    "continuous_provenance",
    "roll_boundary_metadata",
    "quality_flags",
    "missingness_flags",
)

DATASET_ACCEPTANCE_COVERAGE_DIMENSIONS: tuple[str, ...] = (
    "schema",
    "symbol",
    "year_date_range",
    "row_count_sanity",
    "gap_coverage",
    "required_field_presence",
    "missingness_quality_flags",
    "continuous_provenance",
    "roll_metadata",
    "registry_resolution",
)

DATASET_ACCEPTANCE_DEFAULT_POLICY: Mapping[str, object] = MappingProxyType(
    {
        "policy_id": DATASET_ACCEPTANCE_DEFAULT_POLICY_ID,
        "expected_source": "dsrc_databento_historical",
        "expected_symbols": ("ES", "NQ", "RTY"),
        "expected_years": tuple(range(2018, 2027)),
        "expected_schemas": MappingProxyType(
            {
                "ohlcv_1m": MappingProxyType(
                    {"bar_size": "1 min", "what_to_show": "TRADES"}
                ),
                "ohlcv_dense_research_grid": MappingProxyType(
                    {
                        "bar_size": "1 min",
                        "what_to_show": "TRADES_DENSE_RESEARCH_GRID",
                    }
                ),
                "bbo_1m": MappingProxyType({"bar_size": "1 min", "what_to_show": "BBO"}),
            }
        ),
        "partial_year_end_ts": MappingProxyType(
            {"2026": "2026-06-01T00:00:00+00:00"}
        ),
        "required_field_groups": DATASET_ACCEPTANCE_REQUIRED_FIELD_GROUPS,
        "required_registry_metadata_keys": (
            "continuous_provenance",
            "partition_contamination_metadata",
        ),
        "row_count_evidence_required": True,
        "gap_evidence_required": True,
        "required_field_evidence_required": True,
        "missingness_quality_evidence_required": True,
        "continuous_provenance_required": True,
        "roll_metadata_required": True,
        "missing_evidence_policy": "BLOCKED",
    }
)

DATASET_PARTITION_QA_PURPOSES: frozenset[str] = frozenset(
    {
        "coverage_qa",
        "coverage_inspection",
        "data_qa_coverage",
        "data_qa_coverage_inspection",
    }
)

DEFAULT_LOCKED_PARTITION_IDS: tuple[str, ...] = (
    "locked_test_candidate",
    "latest_shadow_candidate",
)

DEFAULT_CONTAMINATION_METADATA_RULES: Mapping[str, object] = MappingProxyType(
    {
        "data_qa_coverage_inspection_allowed": True,
        "locked_partition_ids": DEFAULT_LOCKED_PARTITION_IDS,
        "locked_partition_use_requires_governance_metadata": True,
        "locked_partition_use_requires_contamination_metadata": True,
        "alpha_research_without_governance_metadata": "REJECT",
        "implies_research_approval": False,
    }
)

QUALITY_BLOCKING_SUMMARY_FIELDS: frozenset[str] = frozenset(
    {
        "gap_summary",
        "duplicate_summary",
        "non_monotonic_summary",
        "ohlc_errors",
        "zero_negative_price_errors",
        "dst_anomalies",
        "session_coverage",
        "roll_discontinuities",
        "provider_error_summary",
    }
)
QUALITY_WARNING_SUMMARY_FIELDS: frozenset[str] = frozenset(
    {"zero_volume_anomalies", "abnormal_spread_summary"}
)
QUALITY_METRIC_SUMMARY_FIELDS: frozenset[str] = frozenset({"bbo_missing_metric"})

MAX_SUMMARY_ITEMS = 25
BAR_SIZE_SECONDS_1M = 60

_RAW_BAR_DUMP_KEYS: frozenset[str] = frozenset(
    {
        "bar_start_ts",
        "bar_end_ts",
        "event_ts",
        "available_ts",
        "ingested_at",
        "open",
        "high",
        "low",
        "close",
        "volume",
    }
)

_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ReportStatus(StrEnum):
    """Quality and coverage gate status values."""

    PASSING = "PASSING"
    WARNING = "WARNING"
    BLOCKING = "BLOCKING"


class DatasetAcceptanceState(StrEnum):
    """Persisted DatasetVersion acceptance-lock states."""

    ACCEPTED = "ACCEPTED"
    ACCEPTED_WITH_WARNINGS = "ACCEPTED_WITH_WARNINGS"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class _CanonicalBarView:
    instrument_id: str
    contract_id: str
    series_id: str
    bar_start_ts: datetime
    bar_end_ts: datetime
    event_ts: datetime
    available_ts: datetime
    ingested_at: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    source: str
    source_request_id: str
    data_version: str
    quality_flags: tuple[str, ...]
    session_label: str


@dataclass(frozen=True, slots=True)
class _CanonicalBBOView:
    instrument_id: str
    contract_id: str
    series_id: str
    bar_start_ts: datetime
    bar_end_ts: datetime
    event_ts: datetime
    available_ts: datetime
    ingested_at: datetime
    bid: Decimal
    ask: Decimal
    bid_size: Decimal
    ask_size: Decimal
    mid: Decimal
    spread: Decimal
    source: str
    source_request_id: str
    data_version: str
    quality_flags: tuple[str, ...]
    session_label: str


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
    if not token.replace("_", "").replace("-", "").isalnum():
        msg = f"{field_name} must be an alphanumeric identifier"
        raise DataFoundationValidationError(msg)
    return token


def _normalize_sha256_hash(value: object, field_name: str) -> str:
    digest = _require_text(value, field_name).lower()
    if not _SHA256_HEX_PATTERN.fullmatch(digest):
        msg = f"{field_name} must be a lowercase sha256 hex digest"
        raise DataFoundationValidationError(msg)
    return digest


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        msg = f"{field_name} must be a boolean"
        raise DataFoundationValidationError(msg)
    return value


def _require_non_negative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field_name} must be a non-negative integer"
        raise DataFoundationValidationError(msg)
    if value < 0:
        msg = f"{field_name} must be a non-negative integer"
        raise DataFoundationValidationError(msg)
    return value


def _require_positive_int(value: object, field_name: str) -> int:
    parsed = _require_non_negative_int(value, field_name)
    if parsed <= 0:
        msg = f"{field_name} must be a positive integer"
        raise DataFoundationValidationError(msg)
    return parsed


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


def _parse_partition_date(value: object, field_name: str) -> date:
    if isinstance(value, datetime):
        msg = f"{field_name} must be an ISO-8601 date, not a datetime"
        raise DataFoundationValidationError(msg)
    if isinstance(value, date):
        return value
    raw = _require_text(value, field_name)
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        msg = f"{field_name} must be an ISO-8601 date"
        raise DataFoundationValidationError(msg) from exc


def _parse_decimal(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        msg = f"{field_name} must be a finite decimal"
        raise DataFoundationValidationError(msg)
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        msg = f"{field_name} must be a finite decimal"
        raise DataFoundationValidationError(msg) from exc
    if not parsed.is_finite():
        msg = f"{field_name} must be finite"
        raise DataFoundationValidationError(msg)
    return parsed


def _normalize_text_collection(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = f"{field_name} must be an explicit collection of strings"
        raise DataFoundationValidationError(msg)
    items = tuple(_require_text(item, field_name) for item in value)
    duplicate_items = tuple(sorted({item for item in items if items.count(item) > 1}))
    if duplicate_items:
        msg = f"{field_name} must not contain duplicate values: "
        raise DataFoundationValidationError(msg + ", ".join(duplicate_items))
    return items


def _normalize_symbol_universe(value: object) -> tuple[str, ...]:
    symbols = tuple(
        symbol.upper() for symbol in _normalize_text_collection(value, "symbol_universe")
    )
    if not symbols:
        msg = "symbol_universe must contain at least one symbol"
        raise DataFoundationValidationError(msg)
    invalid = tuple(symbol for symbol in symbols if not symbol.isalnum())
    if invalid:
        msg = "symbol_universe symbols must be alphanumeric: " + ", ".join(invalid)
        raise DataFoundationValidationError(msg)
    duplicates = tuple(sorted({symbol for symbol in symbols if symbols.count(symbol) > 1}))
    if duplicates:
        msg = "symbol_universe must not contain duplicate values: " + ", ".join(duplicates)
        raise DataFoundationValidationError(msg)
    return symbols


def _normalize_contract_universe(value: object) -> tuple[str, ...]:
    contracts = tuple(
        _normalize_id(contract_id, "contract_universe")
        for contract_id in _normalize_text_collection(value, "contract_universe")
    )
    if not contracts:
        msg = "contract_universe must contain at least one contract"
        raise DataFoundationValidationError(msg)
    duplicates = tuple(
        sorted({contract for contract in contracts if contracts.count(contract) > 1})
    )
    if duplicates:
        msg = "contract_universe must not contain duplicate values: " + ", ".join(duplicates)
        raise DataFoundationValidationError(msg)
    return contracts


def _normalize_status(value: object, field_name: str) -> ReportStatus:
    if isinstance(value, ReportStatus):
        return value
    token = _require_text(value, field_name).upper()
    try:
        return ReportStatus[token]
    except KeyError as exc:
        allowed = ", ".join(status.value for status in ReportStatus)
        msg = f"{field_name} must be one of {allowed}"
        raise DataFoundationValidationError(msg) from exc


def _json_scalar(value: object, field_name: str) -> object:
    if value is None or isinstance(value, str | bool | int):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            msg = f"{field_name} must be finite"
            raise DataFoundationValidationError(msg)
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    msg = f"{field_name} must contain JSON-stable aggregate values"
    raise DataFoundationValidationError(msg)


def _looks_like_raw_bar_dump(value: Mapping[object, object]) -> bool:
    keys = {str(key) for key in value}
    return _RAW_BAR_DUMP_KEYS.issubset(keys)


def _freeze_json_value(value: object, field_name: str, *, depth: int = 0) -> object:
    if depth > 8:
        msg = f"{field_name} is nested too deeply for an aggregate summary"
        raise DataFoundationValidationError(msg)
    if isinstance(value, Mapping):
        if _looks_like_raw_bar_dump(value):
            msg = f"{field_name} must not embed raw or full canonical bar rows"
            raise DataFoundationValidationError(msg)
        frozen: dict[str, object] = {}
        for raw_key, raw_value in value.items():
            key = _require_text(raw_key, f"{field_name}.key")
            frozen[key] = _freeze_json_value(
                raw_value,
                f"{field_name}.{key}",
                depth=depth + 1,
            )
        return MappingProxyType(frozen)
    if isinstance(value, tuple | list):
        if len(value) > MAX_SUMMARY_ITEMS:
            msg = f"{field_name} must be capped at {MAX_SUMMARY_ITEMS} aggregate entries"
            raise DataFoundationValidationError(msg)
        return tuple(
            _freeze_json_value(item, f"{field_name}[]", depth=depth + 1) for item in value
        )
    return _json_scalar(value, field_name)


def _require_summary_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = f"{field_name} must be an aggregate summary mapping"
        raise DataFoundationValidationError(msg)
    frozen = _freeze_json_value(value, field_name)
    if not isinstance(frozen, Mapping):
        msg = f"{field_name} must be an aggregate summary mapping"
        raise DataFoundationValidationError(msg)
    return frozen


def _require_exact_mapping_fields(
    value: Mapping[object, object],
    *,
    required_fields: tuple[str, ...],
    object_name: str,
) -> None:
    missing = tuple(field for field in required_fields if field not in value)
    if missing:
        msg = f"{object_name} missing required fields: " + ", ".join(missing)
        raise DataFoundationValidationError(msg)
    extra = tuple(str(field) for field in value if field not in required_fields)
    if extra:
        msg = f"{object_name} includes unsupported fields: " + ", ".join(extra)
        raise DataFoundationValidationError(msg)


def _normalize_fixed_partition(
    value: object,
    *,
    field_name: str,
    expected_partition_id: str,
    expected_start: date,
    expected_end: date | str,
) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = f"{field_name} must be a partition-bound mapping"
        raise DataFoundationValidationError(msg)
    _require_exact_mapping_fields(
        value,
        required_fields=PARTITION_BOUND_FIELDS,
        object_name=field_name,
    )
    partition_id = _normalize_id(value["partition_id"], f"{field_name}.partition_id")
    if partition_id != expected_partition_id:
        msg = f"{field_name}.partition_id must be {expected_partition_id}"
        raise DataFoundationValidationError(msg)
    role = _normalize_id(value["role"], f"{field_name}.role")
    if role != expected_partition_id:
        msg = f"{field_name}.role must be {expected_partition_id}"
        raise DataFoundationValidationError(msg)

    start_date = _parse_partition_date(value["start_date"], f"{field_name}.start_date")
    if expected_end == CANONICAL_LOCKED_TEST_END:
        end_date: date | str = _require_text(value["end_date"], f"{field_name}.end_date")
        if end_date != CANONICAL_LOCKED_TEST_END:
            msg = f"{field_name}.end_date must be {CANONICAL_LOCKED_TEST_END}"
            raise DataFoundationValidationError(msg)
    else:
        end_date = _parse_partition_date(value["end_date"], f"{field_name}.end_date")
        if end_date < start_date:
            msg = f"{field_name}.end_date must not be earlier than start_date"
            raise DataFoundationValidationError(msg)

    if start_date != expected_start:
        msg = f"{field_name}.start_date must be {expected_start.isoformat()}"
        raise DataFoundationValidationError(msg)
    if isinstance(expected_end, date) and end_date != expected_end:
        msg = f"{field_name}.end_date must be {expected_end.isoformat()}"
        raise DataFoundationValidationError(msg)

    return MappingProxyType(
        {
            "partition_id": partition_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date if isinstance(end_date, str) else end_date.isoformat(),
            "role": role,
        }
    )


def _normalize_latest_shadow_partition(value: object) -> Mapping[str, object] | None:
    if value is None:
        return None
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "latest_shadow_candidate must be null or a partition-bound mapping"
        raise DataFoundationValidationError(msg)
    _require_exact_mapping_fields(
        value,
        required_fields=LATEST_SHADOW_PARTITION_FIELDS,
        object_name="latest_shadow_candidate",
    )
    partition_id = _normalize_id(
        value["partition_id"],
        "latest_shadow_candidate.partition_id",
    )
    if partition_id != "latest_shadow_candidate":
        msg = "latest_shadow_candidate.partition_id must be latest_shadow_candidate"
        raise DataFoundationValidationError(msg)
    role = _normalize_id(value["role"], "latest_shadow_candidate.role")
    if role != "latest_shadow_candidate":
        msg = "latest_shadow_candidate.role must be latest_shadow_candidate"
        raise DataFoundationValidationError(msg)
    rolling = _require_bool(value["rolling"], "latest_shadow_candidate.rolling")
    optional = _require_bool(value["optional"], "latest_shadow_candidate.optional")
    if not rolling or not optional:
        msg = "latest_shadow_candidate must be explicitly rolling and optional"
        raise DataFoundationValidationError(msg)

    raw_start = value["start_date"]
    if isinstance(raw_start, str) and raw_start.strip() == "rolling_recent":
        start_date: date | str = raw_start
    else:
        start_date = _parse_partition_date(
            raw_start,
            "latest_shadow_candidate.start_date",
        )
    raw_end = value["end_date"]
    if isinstance(raw_end, str) and raw_end.strip() == CANONICAL_LOCKED_TEST_END:
        end_date: date | str = raw_end
    else:
        end_date = _parse_partition_date(raw_end, "latest_shadow_candidate.end_date")

    if isinstance(start_date, date) and isinstance(end_date, date) and end_date < start_date:
        msg = "latest_shadow_candidate.end_date must not be earlier than start_date"
        raise DataFoundationValidationError(msg)

    return MappingProxyType(
        {
            "partition_id": partition_id,
            "start_date": start_date if isinstance(start_date, str) else start_date.isoformat(),
            "end_date": end_date if isinstance(end_date, str) else end_date.isoformat(),
            "role": role,
            "rolling": rolling,
            "optional": optional,
        }
    )


def _normalize_contamination_metadata_rules(
    value: object,
) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "contamination_metadata_rules must be a structured rule mapping"
        raise DataFoundationValidationError(msg)
    _require_exact_mapping_fields(
        value,
        required_fields=CONTAMINATION_METADATA_RULE_FIELDS,
        object_name="contamination_metadata_rules",
    )

    qa_allowed = _require_bool(
        value["data_qa_coverage_inspection_allowed"],
        "contamination_metadata_rules.data_qa_coverage_inspection_allowed",
    )
    if not qa_allowed:
        msg = "contamination_metadata_rules must allow data QA coverage inspection"
        raise DataFoundationValidationError(msg)

    locked_partition_ids = tuple(
        _normalize_id(item, "contamination_metadata_rules.locked_partition_ids")
        for item in _normalize_text_collection(
            value["locked_partition_ids"],
            "contamination_metadata_rules.locked_partition_ids",
        )
    )
    if set(locked_partition_ids) != set(DEFAULT_LOCKED_PARTITION_IDS):
        msg = "contamination_metadata_rules.locked_partition_ids must identify held-out partitions"
        raise DataFoundationValidationError(msg)

    requires_governance = _require_bool(
        value["locked_partition_use_requires_governance_metadata"],
        "contamination_metadata_rules.locked_partition_use_requires_governance_metadata",
    )
    requires_contamination = _require_bool(
        value["locked_partition_use_requires_contamination_metadata"],
        "contamination_metadata_rules.locked_partition_use_requires_contamination_metadata",
    )
    if not requires_governance or not requires_contamination:
        msg = "locked partition use must require Governance contamination metadata"
        raise DataFoundationValidationError(msg)

    alpha_without_metadata = _require_text(
        value["alpha_research_without_governance_metadata"],
        "contamination_metadata_rules.alpha_research_without_governance_metadata",
    ).upper()
    if alpha_without_metadata != "REJECT":
        msg = "alpha research without Governance metadata must be rejected"
        raise DataFoundationValidationError(msg)

    implies_approval = _require_bool(
        value["implies_research_approval"],
        "contamination_metadata_rules.implies_research_approval",
    )
    if implies_approval:
        msg = "DatasetPartitionPlan must not imply research approval"
        raise DataFoundationValidationError(msg)

    return MappingProxyType(
        {
            "data_qa_coverage_inspection_allowed": qa_allowed,
            "locked_partition_ids": locked_partition_ids,
            "locked_partition_use_requires_governance_metadata": requires_governance,
            "locked_partition_use_requires_contamination_metadata": requires_contamination,
            "alpha_research_without_governance_metadata": alpha_without_metadata,
            "implies_research_approval": implies_approval,
        }
    )


def _require_substantive_governance_metadata(value: object) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping) or not value:
        msg = "locked partition use requires explicit Governance contamination metadata"
        raise DataFoundationValidationError(msg)
    normalized: dict[str, object] = {}
    vague_text = {"n/a", "na", "none", "todo", "tbd", "unknown"}
    for raw_key, raw_value in value.items():
        key = _require_text(raw_key, "governance_metadata.key")
        if key.lower() in vague_text:
            msg = "governance metadata keys must be substantive"
            raise DataFoundationValidationError(msg)
        if raw_value is None:
            msg = f"governance_metadata.{key} must not be null"
            raise DataFoundationValidationError(msg)
        if isinstance(raw_value, str) and raw_value.strip().lower() in vague_text | {""}:
            msg = f"governance_metadata.{key} must be substantive"
            raise DataFoundationValidationError(msg)
        normalized[key] = _freeze_json_value(raw_value, f"governance_metadata.{key}")
    return MappingProxyType(normalized)


def _partition_start_date(partition: Mapping[str, object], field_name: str) -> date:
    return _parse_partition_date(partition["start_date"], f"{field_name}.start_date")


def _partition_end_date(partition: Mapping[str, object], field_name: str) -> date:
    return _parse_partition_date(partition["end_date"], f"{field_name}.end_date")


def _validate_canonical_partition_order(
    development_partition: Mapping[str, object],
    validation_partition: Mapping[str, object],
    locked_test_candidate: Mapping[str, object],
) -> None:
    development_end = _partition_end_date(development_partition, "development_partition")
    validation_start = _partition_start_date(validation_partition, "validation_partition")
    validation_end = _partition_end_date(validation_partition, "validation_partition")
    locked_start = _partition_start_date(locked_test_candidate, "locked_test_candidate")
    if development_end >= validation_start:
        msg = "development_partition must end before validation_partition starts"
        raise DataFoundationValidationError(msg)
    if validation_end >= locked_start:
        msg = "validation_partition must end before locked_test_candidate starts"
        raise DataFoundationValidationError(msg)


def _normalize_quality_summary(value: object, field_name: str) -> Mapping[str, object]:
    summary = dict(_require_summary_mapping(value, field_name))
    for required_key in ("count", "status", "blocking"):
        if required_key not in summary:
            msg = f"{field_name}.{required_key} is required"
            raise DataFoundationValidationError(msg)

    count = _require_non_negative_int(summary["count"], f"{field_name}.count")
    status = _normalize_status(summary["status"], f"{field_name}.status")
    blocking = _require_bool(summary["blocking"], f"{field_name}.blocking")

    if field_name in QUALITY_BLOCKING_SUMMARY_FIELDS and count > 0:
        if status is not ReportStatus.BLOCKING or not blocking:
            msg = f"{field_name} with findings must be BLOCKING"
            raise DataFoundationValidationError(msg)
    if field_name in QUALITY_WARNING_SUMMARY_FIELDS and count > 0:
        if status is ReportStatus.PASSING:
            msg = f"{field_name} with findings must not be PASSING"
            raise DataFoundationValidationError(msg)
    if field_name in QUALITY_METRIC_SUMMARY_FIELDS:
        if status is ReportStatus.BLOCKING or blocking:
            msg = f"{field_name} must be a non-blocking metric summary"
            raise DataFoundationValidationError(msg)
        if count > 0 and status is ReportStatus.PASSING:
            msg = f"{field_name} with findings must not be PASSING"
            raise DataFoundationValidationError(msg)
    if status is ReportStatus.BLOCKING and not blocking:
        msg = f"{field_name}.blocking must be true for BLOCKING summaries"
        raise DataFoundationValidationError(msg)
    if status is not ReportStatus.BLOCKING and blocking:
        msg = f"{field_name}.blocking must be false unless status is BLOCKING"
        raise DataFoundationValidationError(msg)
    if status is ReportStatus.PASSING and count != 0:
        msg = f"{field_name} with findings must not be PASSING"
        raise DataFoundationValidationError(msg)

    summary["count"] = count
    summary["status"] = status.value
    summary["blocking"] = blocking
    return MappingProxyType(summary)


def _derive_quality_status(summaries: Iterable[Mapping[str, object]]) -> ReportStatus:
    saw_warning = False
    for summary in summaries:
        status = _normalize_status(summary["status"], "summary.status")
        if status is ReportStatus.BLOCKING:
            return ReportStatus.BLOCKING
        if status is ReportStatus.WARNING:
            saw_warning = True
    if saw_warning:
        return ReportStatus.WARNING
    return ReportStatus.PASSING


def _capped_samples(items: Iterable[Mapping[str, object]]) -> tuple[Mapping[str, object], ...]:
    capped = []
    for item in items:
        if len(capped) >= MAX_SUMMARY_ITEMS:
            break
        frozen = _freeze_json_value(item, "summary.sample")
        if not isinstance(frozen, Mapping):
            msg = "summary samples must be aggregate mappings"
            raise DataFoundationValidationError(msg)
        capped.append(frozen)
    return tuple(capped)


def _finding_summary(
    *,
    count: int,
    status: ReportStatus,
    sample_key: str,
    samples: Iterable[Mapping[str, object]] = (),
    extra: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    summary: dict[str, object] = {
        "count": _require_non_negative_int(count, "count"),
        "status": status.value,
        "blocking": status is ReportStatus.BLOCKING,
        sample_key: _capped_samples(samples),
        "truncated": count > MAX_SUMMARY_ITEMS,
    }
    if extra is not None:
        for key, value in extra.items():
            summary[_require_text(key, "summary.extra.key")] = _freeze_json_value(
                value,
                f"summary.extra.{key}",
            )
    return MappingProxyType(summary)


def _passing_summary(
    sample_key: str,
    extra: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    return _finding_summary(
        count=0,
        status=ReportStatus.PASSING,
        sample_key=sample_key,
        extra=extra,
    )


def _empty_bbo_missing_metric() -> Mapping[str, object]:
    return _passing_summary("sample_missing_bbo")


def _empty_abnormal_spread_summary() -> Mapping[str, object]:
    return _passing_summary("sample_spreads")


def _bbo_missing_metric_summary(
    findings: tuple[Mapping[str, object], ...],
) -> Mapping[str, object]:
    return _finding_summary(
        count=len(findings),
        status=_status_for_warning_count(len(findings)),
        sample_key="sample_missing_bbo",
        samples=findings,
        extra={
            "by_finding": dict(
                sorted(Counter(str(finding["finding"]) for finding in findings).items())
            )
        },
    )


def _abnormal_spread_summary(
    findings: tuple[Mapping[str, object], ...],
) -> Mapping[str, object]:
    return _finding_summary(
        count=len(findings),
        status=_status_for_warning_count(len(findings)),
        sample_key="sample_spreads",
        samples=findings,
    )


def _canonical_bar_view(bar: CanonicalBarRecord | Mapping[str, object]) -> _CanonicalBarView:
    if isinstance(bar, CanonicalBarRecord):
        values = bar.to_mapping()
    elif isinstance(bar, Mapping):
        values = bar
    else:
        msg = "canonical bars must be CanonicalBarRecord instances or canonical mappings"
        raise DataFoundationValidationError(msg)

    missing = tuple(field for field in CANONICAL_BAR_RECORD_FIELDS if field not in values)
    if missing:
        msg = "canonical bar audit input missing required fields: " + ", ".join(missing)
        raise DataFoundationValidationError(msg)
    extra = tuple(field for field in values if field not in CANONICAL_BAR_RECORD_FIELDS)
    if extra:
        msg = "canonical bar audit input includes unsupported fields: " + ", ".join(extra)
        raise DataFoundationValidationError(msg)

    start = _parse_aware_datetime(values["bar_start_ts"], "bar_start_ts")
    end = _parse_aware_datetime(values["bar_end_ts"], "bar_end_ts")
    if end <= start:
        msg = "bar_end_ts must be greater than bar_start_ts before quality audit"
        raise DataFoundationValidationError(msg)

    return _CanonicalBarView(
        instrument_id=_normalize_id(values["instrument_id"], "instrument_id"),
        contract_id=_normalize_id(values["contract_id"], "contract_id"),
        series_id=_normalize_id(values["series_id"], "series_id"),
        bar_start_ts=start,
        bar_end_ts=end,
        event_ts=_parse_aware_datetime(values["event_ts"], "event_ts"),
        available_ts=_parse_aware_datetime(values["available_ts"], "available_ts"),
        ingested_at=_parse_aware_datetime(values["ingested_at"], "ingested_at"),
        open=_parse_decimal(values["open"], "open"),
        high=_parse_decimal(values["high"], "high"),
        low=_parse_decimal(values["low"], "low"),
        close=_parse_decimal(values["close"], "close"),
        volume=_parse_decimal(values["volume"], "volume"),
        source=_require_text(values["source"], "source"),
        source_request_id=_normalize_id(values["source_request_id"], "source_request_id"),
        data_version=_require_text(values["data_version"], "data_version"),
        quality_flags=_normalize_text_collection(values["quality_flags"], "quality_flags"),
        session_label=_require_text(values["session_label"], "session_label").upper(),
    )


def _canonical_bbo_view(bbo: CanonicalBBORecord | Mapping[str, object]) -> _CanonicalBBOView:
    if isinstance(bbo, CanonicalBBORecord):
        values = bbo.to_mapping()
    elif isinstance(bbo, Mapping):
        values = bbo
    else:
        msg = "canonical BBOs must be CanonicalBBORecord instances or canonical mappings"
        raise DataFoundationValidationError(msg)

    missing = tuple(field for field in CANONICAL_BBO_REQUIRED_FIELDS if field not in values)
    if missing:
        msg = "canonical BBO audit input missing required fields: " + ", ".join(missing)
        raise DataFoundationValidationError(msg)
    extra = tuple(field for field in values if field not in CANONICAL_BBO_RECORD_FIELDS)
    if extra:
        msg = "canonical BBO audit input includes unsupported fields: " + ", ".join(extra)
        raise DataFoundationValidationError(msg)

    start = _parse_aware_datetime(values["bar_start_ts"], "bar_start_ts")
    end = _parse_aware_datetime(values["bar_end_ts"], "bar_end_ts")
    if end <= start:
        msg = "bar_end_ts must be greater than bar_start_ts before BBO quality audit"
        raise DataFoundationValidationError(msg)

    return _CanonicalBBOView(
        instrument_id=_normalize_id(values["instrument_id"], "instrument_id"),
        contract_id=_normalize_id(values["contract_id"], "contract_id"),
        series_id=_normalize_id(values["series_id"], "series_id"),
        bar_start_ts=start,
        bar_end_ts=end,
        event_ts=_parse_aware_datetime(values["event_ts"], "event_ts"),
        available_ts=_parse_aware_datetime(values["available_ts"], "available_ts"),
        ingested_at=_parse_aware_datetime(values["ingested_at"], "ingested_at"),
        bid=_parse_decimal(values["bid"], "bid"),
        ask=_parse_decimal(values["ask"], "ask"),
        bid_size=_parse_decimal(values["bid_size"], "bid_size"),
        ask_size=_parse_decimal(values["ask_size"], "ask_size"),
        mid=_parse_decimal(values["mid"], "mid"),
        spread=_parse_decimal(values["spread"], "spread"),
        source=_require_text(values["source"], "source"),
        source_request_id=_normalize_id(values["source_request_id"], "source_request_id"),
        data_version=_require_text(values["data_version"], "data_version"),
        quality_flags=_normalize_text_collection(values["quality_flags"], "quality_flags"),
        session_label=_require_text(values["session_label"], "session_label").upper(),
    )


def _expected_interval_seconds(value: object) -> int:
    interval_seconds = _require_positive_int(value, "expected_interval_seconds")
    if interval_seconds != BAR_SIZE_SECONDS_1M:
        msg = "DATA-P16 quality and coverage reports are scoped to canonical 1-minute bars"
        raise DataFoundationValidationError(msg)
    return interval_seconds


def _bar_group_key(bar: _CanonicalBarView) -> tuple[str, str, str]:
    return (bar.instrument_id, bar.contract_id, bar.series_id)


@dataclass(frozen=True, slots=True)
class _QualityGapInterval:
    instrument_id: str
    contract_id: str
    session_label: str
    start_ts: datetime
    end_ts: datetime


def _normalize_quality_gap_intervals(
    value: Iterable[Mapping[str, object]] | None,
) -> tuple[_QualityGapInterval, ...] | None:
    if value is None:
        return None
    intervals = []
    for item in value:
        if isinstance(item, str) or not isinstance(item, Mapping):
            msg = "quality gap intervals must contain aggregate interval mappings"
            raise DataFoundationValidationError(msg)
        required = ("instrument_id", "contract_id", "session_label", "start_ts", "end_ts")
        missing = tuple(field for field in required if field not in item)
        if missing:
            msg = "quality gap interval missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        start_ts = _parse_aware_datetime(item["start_ts"], "quality_gap_interval.start_ts")
        end_ts = _parse_aware_datetime(item["end_ts"], "quality_gap_interval.end_ts")
        if end_ts <= start_ts:
            msg = "quality gap interval end_ts must be greater than start_ts"
            raise DataFoundationValidationError(msg)
        intervals.append(
            _QualityGapInterval(
                instrument_id=_normalize_id(item["instrument_id"], "instrument_id"),
                contract_id=_normalize_id(item["contract_id"], "contract_id"),
                session_label=_require_text(
                    item["session_label"],
                    "quality_gap_interval.session_label",
                ).upper(),
                start_ts=start_ts,
                end_ts=end_ts,
            )
        )
    return tuple(intervals)


def _quality_gap_interval_index(
    bar: _CanonicalBarView,
    intervals: tuple[_QualityGapInterval, ...],
) -> int | None:
    for index, interval in enumerate(intervals):
        if (
            bar.instrument_id == interval.instrument_id
            and bar.contract_id == interval.contract_id
            and bar.session_label == interval.session_label
            and interval.start_ts <= bar.bar_start_ts
            and bar.bar_end_ts <= interval.end_ts
        ):
            return index
    return None


def _bar_roll_key(bar: _CanonicalBarView) -> tuple[str, str]:
    return (bar.instrument_id, bar.series_id)


def _iso_interval(start: datetime, end: datetime) -> Mapping[str, object]:
    return MappingProxyType({"start_ts": start.isoformat(), "end_ts": end.isoformat()})


def _status_for_blocking_count(count: int) -> ReportStatus:
    return ReportStatus.BLOCKING if count else ReportStatus.PASSING


def _status_for_warning_count(count: int) -> ReportStatus:
    return ReportStatus.WARNING if count else ReportStatus.PASSING


def _quality_session_summary(
    bars: tuple[_CanonicalBarView, ...],
    expected_sessions: Iterable[str] | None,
) -> Mapping[str, object]:
    counts = Counter(bar.session_label for bar in bars)
    invalid_sessions = tuple(
        sorted(session for session in counts if session not in SUPPORTED_SESSION_TYPES)
    )
    expected = (
        tuple(
            sorted(
                {
                    _require_text(session, "expected_sessions").upper()
                    for session in expected_sessions
                }
            )
        )
        if expected_sessions is not None
        else ()
    )
    missing_sessions = tuple(session for session in expected if session not in counts)
    count = len(invalid_sessions) + len(missing_sessions)
    return _finding_summary(
        count=count,
        status=_status_for_blocking_count(count),
        sample_key="sample_findings",
        samples=(
            {"session_label": session, "finding": "unsupported_session_label"}
            for session in invalid_sessions
        ),
        extra={
            "observed_session_count": len(counts),
            "observed_sessions": tuple(sorted(counts)),
            "missing_expected_sessions": missing_sessions,
            "missing_expected_session_count": len(missing_sessions),
        },
    )


def _normalize_roll_transition(value: object) -> tuple[str, str, str | None]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "roll_transitions must contain aggregate transition mappings"
        raise DataFoundationValidationError(msg)
    for field_name in ("from_contract", "to_contract"):
        if field_name not in value:
            msg = f"roll_transitions.{field_name} is required"
            raise DataFoundationValidationError(msg)
    effective_ts = None
    if value.get("effective_ts") is not None:
        effective_ts = _parse_aware_datetime(value["effective_ts"], "effective_ts").isoformat()
    return (
        _normalize_id(value["from_contract"], "from_contract"),
        _normalize_id(value["to_contract"], "to_contract"),
        effective_ts,
    )


def _roll_discontinuity_summary(
    bars: tuple[_CanonicalBarView, ...],
    roll_transitions: Iterable[Mapping[str, object]] | None,
) -> Mapping[str, object]:
    allowed = {
        _normalize_roll_transition(transition) for transition in (roll_transitions or ())
    }
    grouped: dict[tuple[str, str], list[_CanonicalBarView]] = defaultdict(list)
    for bar in bars:
        grouped[_bar_roll_key(bar)].append(bar)

    documented_roll_count = 0
    discontinuities: list[Mapping[str, object]] = []
    for group_key, group_bars in grouped.items():
        ordered = sorted(group_bars, key=lambda item: item.bar_start_ts)
        previous = ordered[0]
        for current in ordered[1:]:
            if current.contract_id == previous.contract_id:
                previous = current
                continue
            pair = (previous.contract_id, current.contract_id, None)
            exact = (
                previous.contract_id,
                current.contract_id,
                current.bar_start_ts.isoformat(),
            )
            if pair in allowed or exact in allowed:
                documented_roll_count += 1
            else:
                discontinuities.append(
                    {
                        "instrument_id": group_key[0],
                        "series_id": group_key[1],
                        "from_contract": previous.contract_id,
                        "to_contract": current.contract_id,
                        "transition_ts": current.bar_start_ts.isoformat(),
                    }
                )
            previous = current

    count = len(discontinuities)
    return _finding_summary(
        count=count,
        status=_status_for_blocking_count(count),
        sample_key="sample_transitions",
        samples=discontinuities,
        extra={"documented_roll_count": documented_roll_count},
    )


def _provider_error_summary(
    provider_errors: Iterable[ProviderErrorRecord | Mapping[str, object]],
) -> Mapping[str, object]:
    errors = tuple(provider_errors)
    by_code: Counter[str] = Counter()
    by_resolution: Counter[str] = Counter()
    retryable_count = 0
    samples: list[Mapping[str, object]] = []
    for error in errors:
        if isinstance(error, ProviderErrorRecord):
            code = error.error_code
            resolution = error.resolution.value
            retryable = error.retryable
            chunk_id = error.chunk_id
        elif isinstance(error, Mapping):
            code = _require_text(error.get("error_code"), "provider_error.error_code")
            resolution = _require_text(error.get("resolution"), "provider_error.resolution")
            retryable = _require_bool(error.get("retryable"), "provider_error.retryable")
            chunk_id = _require_text(error.get("chunk_id"), "provider_error.chunk_id")
        else:
            msg = "provider_errors must contain ProviderErrorRecord instances or mappings"
            raise DataFoundationValidationError(msg)
        by_code[code] += 1
        by_resolution[resolution] += 1
        retryable_count += int(retryable)
        samples.append({"chunk_id": chunk_id, "error_code": code, "resolution": resolution})

    count = len(errors)
    return _finding_summary(
        count=count,
        status=_status_for_blocking_count(count),
        sample_key="sample_errors",
        samples=samples,
        extra={
            "retryable_count": retryable_count,
            "non_retryable_count": count - retryable_count,
            "by_code": dict(sorted(by_code.items())),
            "by_resolution": dict(sorted(by_resolution.items())),
        },
    )


def _compute_quality_summaries(
    bars: tuple[_CanonicalBarView, ...],
    *,
    expected_interval_seconds: int,
    expected_sessions: Iterable[str] | None,
    expected_gap_intervals: Iterable[Mapping[str, object]] | None,
    roll_transitions: Iterable[Mapping[str, object]] | None,
    provider_errors: Iterable[ProviderErrorRecord | Mapping[str, object]],
) -> Mapping[str, Mapping[str, object]]:
    grouped: dict[tuple[str, str, str], list[_CanonicalBarView]] = defaultdict(list)
    for bar in bars:
        grouped[_bar_group_key(bar)].append(bar)

    duplicate_counts = Counter(
        (
            bar.instrument_id,
            bar.contract_id,
            bar.series_id,
            bar.bar_start_ts.isoformat(),
        )
        for bar in bars
    )
    duplicates = [
        {
            "instrument_id": key[0],
            "contract_id": key[1],
            "series_id": key[2],
            "bar_start_ts": key[3],
            "duplicate_count": count,
        }
        for key, count in sorted(duplicate_counts.items())
        if count > 1
    ]

    non_monotonic: list[Mapping[str, object]] = []
    original_previous: dict[tuple[str, str, str], _CanonicalBarView] = {}
    for bar in bars:
        key = _bar_group_key(bar)
        previous = original_previous.get(key)
        if previous is not None and bar.bar_start_ts < previous.bar_start_ts:
            non_monotonic.append(
                {
                    "instrument_id": key[0],
                    "contract_id": key[1],
                    "series_id": key[2],
                    "previous_bar_start_ts": previous.bar_start_ts.isoformat(),
                    "current_bar_start_ts": bar.bar_start_ts.isoformat(),
                }
            )
        original_previous[key] = bar

    gap_intervals = _normalize_quality_gap_intervals(expected_gap_intervals)
    gaps: list[Mapping[str, object]] = []
    for key, group_bars in grouped.items():
        ordered = sorted(group_bars, key=lambda item: item.bar_start_ts)
        for previous, current in zip(ordered, ordered[1:], strict=False):
            if gap_intervals is not None:
                previous_interval = _quality_gap_interval_index(previous, gap_intervals)
                current_interval = _quality_gap_interval_index(current, gap_intervals)
                if (
                    previous_interval is not None
                    and current_interval is not None
                    and previous_interval != current_interval
                ):
                    continue
            if current.bar_start_ts > previous.bar_end_ts:
                gap_seconds = int(
                    (current.bar_start_ts - previous.bar_end_ts).total_seconds()
                )
                gaps.append(
                    {
                        "instrument_id": key[0],
                        "contract_id": key[1],
                        "series_id": key[2],
                        "start_ts": previous.bar_end_ts.isoformat(),
                        "end_ts": current.bar_start_ts.isoformat(),
                        "missing_bar_count": max(
                            1,
                            gap_seconds // expected_interval_seconds,
                        ),
                    }
                )

    ohlc_errors: list[Mapping[str, object]] = []
    zero_negative_price_errors: list[Mapping[str, object]] = []
    zero_volume_anomalies: list[Mapping[str, object]] = []
    dst_anomalies: list[Mapping[str, object]] = []
    for bar in bars:
        prices = {
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
        }
        for field_name, price in prices.items():
            if price <= 0:
                zero_negative_price_errors.append(
                    {
                        "instrument_id": bar.instrument_id,
                        "contract_id": bar.contract_id,
                        "bar_start_ts": bar.bar_start_ts.isoformat(),
                        "field": field_name,
                    }
                )
        if bar.high < bar.low:
            ohlc_errors.append(
                {
                    "instrument_id": bar.instrument_id,
                    "contract_id": bar.contract_id,
                    "bar_start_ts": bar.bar_start_ts.isoformat(),
                    "rule": "high_greater_than_or_equal_low",
                }
            )
        if not (bar.low <= bar.open <= bar.high):
            ohlc_errors.append(
                {
                    "instrument_id": bar.instrument_id,
                    "contract_id": bar.contract_id,
                    "bar_start_ts": bar.bar_start_ts.isoformat(),
                    "rule": "low_less_equal_open_less_equal_high",
                }
            )
        if not (bar.low <= bar.close <= bar.high):
            ohlc_errors.append(
                {
                    "instrument_id": bar.instrument_id,
                    "contract_id": bar.contract_id,
                    "bar_start_ts": bar.bar_start_ts.isoformat(),
                    "rule": "low_less_equal_close_less_equal_high",
                }
            )
        if bar.volume == 0:
            zero_volume_anomalies.append(
                {
                    "instrument_id": bar.instrument_id,
                    "contract_id": bar.contract_id,
                    "bar_start_ts": bar.bar_start_ts.isoformat(),
                }
            )
        if bar.volume < 0:
            zero_volume_anomalies.append(
                {
                    "instrument_id": bar.instrument_id,
                    "contract_id": bar.contract_id,
                    "bar_start_ts": bar.bar_start_ts.isoformat(),
                    "finding": "negative_volume",
                }
            )

        duration_seconds = int((bar.bar_end_ts - bar.bar_start_ts).total_seconds())
        offset_changed = bar.bar_start_ts.utcoffset() != bar.bar_end_ts.utcoffset()
        if duration_seconds != expected_interval_seconds or offset_changed:
            dst_anomalies.append(
                {
                    "instrument_id": bar.instrument_id,
                    "contract_id": bar.contract_id,
                    "bar_start_ts": bar.bar_start_ts.isoformat(),
                    "bar_end_ts": bar.bar_end_ts.isoformat(),
                    "duration_seconds": duration_seconds,
                    "offset_changed": offset_changed,
                }
            )

    negative_volume_count = sum(
        1 for anomaly in zero_volume_anomalies if anomaly.get("finding") == "negative_volume"
    )
    zero_volume_status = (
        ReportStatus.BLOCKING
        if negative_volume_count
        else _status_for_warning_count(len(zero_volume_anomalies))
    )

    return MappingProxyType(
        {
            "gap_summary": _finding_summary(
                count=len(gaps),
                status=_status_for_blocking_count(len(gaps)),
                sample_key="sample_intervals",
                samples=gaps,
            ),
            "duplicate_summary": _finding_summary(
                count=len(duplicates),
                status=_status_for_blocking_count(len(duplicates)),
                sample_key="sample_duplicates",
                samples=duplicates,
            ),
            "non_monotonic_summary": _finding_summary(
                count=len(non_monotonic),
                status=_status_for_blocking_count(len(non_monotonic)),
                sample_key="sample_pairs",
                samples=non_monotonic,
            ),
            "ohlc_errors": _finding_summary(
                count=len(ohlc_errors),
                status=_status_for_blocking_count(len(ohlc_errors)),
                sample_key="sample_errors",
                samples=ohlc_errors,
            ),
            "zero_negative_price_errors": _finding_summary(
                count=len(zero_negative_price_errors),
                status=_status_for_blocking_count(len(zero_negative_price_errors)),
                sample_key="sample_errors",
                samples=zero_negative_price_errors,
            ),
            "zero_volume_anomalies": _finding_summary(
                count=len(zero_volume_anomalies),
                status=zero_volume_status,
                sample_key="sample_anomalies",
                samples=zero_volume_anomalies,
            ),
            "dst_anomalies": _finding_summary(
                count=len(dst_anomalies),
                status=_status_for_blocking_count(len(dst_anomalies)),
                sample_key="sample_anomalies",
                samples=dst_anomalies,
            ),
            "session_coverage": _quality_session_summary(bars, expected_sessions),
            "roll_discontinuities": _roll_discontinuity_summary(bars, roll_transitions),
            "provider_error_summary": _provider_error_summary(provider_errors),
            "bbo_missing_metric": _empty_bbo_missing_metric(),
            "abnormal_spread_summary": _empty_abnormal_spread_summary(),
        }
    )


def _bbo_group_key(bbo: _CanonicalBBOView) -> tuple[str, str, str]:
    return (bbo.instrument_id, bbo.contract_id, bbo.series_id)


def _bbo_minute_key(bbo: _CanonicalBBOView) -> tuple[str, str, str, datetime]:
    return (bbo.instrument_id, bbo.contract_id, bbo.series_id, bbo.bar_start_ts)


def _bar_minute_key(bar: _CanonicalBarView) -> tuple[str, str, str, datetime]:
    return (bar.instrument_id, bar.contract_id, bar.series_id, bar.bar_start_ts)


def _normalize_optional_decimal(value: object, field_name: str) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    parsed = _parse_decimal(value, field_name)
    if parsed < 0:
        msg = f"{field_name} must be non-negative"
        raise DataFoundationValidationError(msg)
    return parsed


def _bbo_expected_missing_findings(
    *,
    bbos: tuple[_CanonicalBBOView, ...],
    expected_ohlcv_bars: Iterable[CanonicalBarRecord | Mapping[str, object]] | None,
) -> tuple[Mapping[str, object], ...]:
    missing_flag = MISSING_BBO_QUALITY_FLAG.lower()
    findings: list[Mapping[str, object]] = [
        {
            "instrument_id": bbo.instrument_id,
            "contract_id": bbo.contract_id,
            "series_id": bbo.series_id,
            "bar_start_ts": bbo.bar_start_ts.isoformat(),
            "finding": "missing_bbo_flagged",
        }
        for bbo in bbos
        if missing_flag in {flag.lower() for flag in bbo.quality_flags}
    ]
    if expected_ohlcv_bars is None:
        return tuple(findings)

    expected_keys = {
        _bar_minute_key(_canonical_bar_view(bar)) for bar in expected_ohlcv_bars
    }
    observed_keys = {_bbo_minute_key(bbo) for bbo in bbos}
    for instrument_id, contract_id, series_id, bar_start_ts in sorted(
        expected_keys.difference(observed_keys),
        key=lambda item: (item[0], item[1], item[2], item[3]),
    ):
        findings.append(
            {
                "instrument_id": instrument_id,
                "contract_id": contract_id,
                "series_id": series_id,
                "bar_start_ts": bar_start_ts.isoformat(),
                "finding": "missing_bbo_record_for_ohlcv_minute",
            }
        )
    return tuple(findings)


def _bbo_alignment_findings(
    *,
    bbos: tuple[_CanonicalBBOView, ...],
    expected_ohlcv_bars: Iterable[CanonicalBarRecord | Mapping[str, object]] | None,
    expected_interval_seconds: int,
) -> tuple[Mapping[str, object], ...]:
    findings: list[Mapping[str, object]] = []
    expected_keys = (
        {_bar_minute_key(_canonical_bar_view(bar)) for bar in expected_ohlcv_bars}
        if expected_ohlcv_bars is not None
        else None
    )
    for bbo in bbos:
        duration_seconds = int((bbo.bar_end_ts - bbo.bar_start_ts).total_seconds())
        if duration_seconds != expected_interval_seconds:
            findings.append(
                {
                    "instrument_id": bbo.instrument_id,
                    "contract_id": bbo.contract_id,
                    "bar_start_ts": bbo.bar_start_ts.isoformat(),
                    "bar_end_ts": bbo.bar_end_ts.isoformat(),
                    "finding": "bbo_bar_duration_not_1m",
                    "duration_seconds": duration_seconds,
                }
            )
        if bbo.event_ts < bbo.bar_start_ts or bbo.event_ts > bbo.bar_end_ts:
            findings.append(
                {
                    "instrument_id": bbo.instrument_id,
                    "contract_id": bbo.contract_id,
                    "bar_start_ts": bbo.bar_start_ts.isoformat(),
                    "bar_end_ts": bbo.bar_end_ts.isoformat(),
                    "event_ts": bbo.event_ts.isoformat(),
                    "finding": "bbo_event_outside_bar_interval",
                }
            )
        if bbo.available_ts < bbo.bar_end_ts:
            findings.append(
                {
                    "instrument_id": bbo.instrument_id,
                    "contract_id": bbo.contract_id,
                    "bar_start_ts": bbo.bar_start_ts.isoformat(),
                    "bar_end_ts": bbo.bar_end_ts.isoformat(),
                    "available_ts": bbo.available_ts.isoformat(),
                    "finding": "bbo_available_before_bar_end",
                }
            )
        if expected_keys is not None and _bbo_minute_key(bbo) not in expected_keys:
            findings.append(
                {
                    "instrument_id": bbo.instrument_id,
                    "contract_id": bbo.contract_id,
                    "series_id": bbo.series_id,
                    "bar_start_ts": bbo.bar_start_ts.isoformat(),
                    "finding": "bbo_minute_without_ohlcv",
                }
            )
    return tuple(findings)


def _compute_bbo_quality_summaries(
    bbos: tuple[_CanonicalBBOView, ...],
    *,
    expected_interval_seconds: int,
    expected_sessions: Iterable[str] | None,
    expected_ohlcv_bars: Iterable[CanonicalBarRecord | Mapping[str, object]] | None,
    abnormal_spread_threshold: Decimal | None,
    provider_errors: Iterable[ProviderErrorRecord | Mapping[str, object]],
) -> Mapping[str, Mapping[str, object]]:
    grouped: dict[tuple[str, str, str], list[_CanonicalBBOView]] = defaultdict(list)
    for bbo in bbos:
        grouped[_bbo_group_key(bbo)].append(bbo)

    duplicate_counts = Counter(
        (
            bbo.instrument_id,
            bbo.contract_id,
            bbo.series_id,
            bbo.bar_start_ts.isoformat(),
        )
        for bbo in bbos
    )
    duplicates = [
        {
            "instrument_id": key[0],
            "contract_id": key[1],
            "series_id": key[2],
            "bar_start_ts": key[3],
            "duplicate_count": count,
        }
        for key, count in sorted(duplicate_counts.items())
        if count > 1
    ]

    non_monotonic: list[Mapping[str, object]] = []
    previous_by_group: dict[tuple[str, str, str], _CanonicalBBOView] = {}
    for bbo in bbos:
        key = _bbo_group_key(bbo)
        previous = previous_by_group.get(key)
        if previous is not None and bbo.bar_start_ts < previous.bar_start_ts:
            non_monotonic.append(
                {
                    "instrument_id": key[0],
                    "contract_id": key[1],
                    "series_id": key[2],
                    "previous_bar_start_ts": previous.bar_start_ts.isoformat(),
                    "current_bar_start_ts": bbo.bar_start_ts.isoformat(),
                }
            )
        previous_by_group[key] = bbo

    missing_findings = _bbo_expected_missing_findings(
        bbos=bbos,
        expected_ohlcv_bars=expected_ohlcv_bars,
    )
    alignment_findings = _bbo_alignment_findings(
        bbos=bbos,
        expected_ohlcv_bars=expected_ohlcv_bars,
        expected_interval_seconds=expected_interval_seconds,
    )
    quote_errors: list[Mapping[str, object]] = []
    abnormal_spread_findings: list[Mapping[str, object]] = []
    zero_size_anomalies: list[Mapping[str, object]] = []
    missing_flag = MISSING_BBO_QUALITY_FLAG.lower()
    for bbo in bbos:
        flags = {flag.lower() for flag in bbo.quality_flags}
        is_missing = missing_flag in flags
        values = {
            "bid": bbo.bid,
            "ask": bbo.ask,
            "bid_size": bbo.bid_size,
            "ask_size": bbo.ask_size,
            "spread": bbo.spread,
        }
        for field_name, value in values.items():
            if value < 0:
                quote_errors.append(
                    {
                        "instrument_id": bbo.instrument_id,
                        "contract_id": bbo.contract_id,
                        "bar_start_ts": bbo.bar_start_ts.isoformat(),
                        "field": field_name,
                        "finding": "negative_bbo_value",
                    }
                )
        if is_missing and BBO_QUARANTINE_QUALITY_FLAG in flags:
            quote_errors.append(
                {
                    "instrument_id": bbo.instrument_id,
                    "contract_id": bbo.contract_id,
                    "bar_start_ts": bbo.bar_start_ts.isoformat(),
                    "finding": "bbo_quarantine_flagged",
                    "quality_flags": tuple(sorted(bbo.quality_flags)),
                }
            )
        if bbo.ask < bbo.bid:
            quote_errors.append(
                {
                    "instrument_id": bbo.instrument_id,
                    "contract_id": bbo.contract_id,
                    "bar_start_ts": bbo.bar_start_ts.isoformat(),
                    "finding": "bid_above_ask",
                }
            )
        if bbo.mid != (bbo.bid + bbo.ask) / Decimal("2"):
            quote_errors.append(
                {
                    "instrument_id": bbo.instrument_id,
                    "contract_id": bbo.contract_id,
                    "bar_start_ts": bbo.bar_start_ts.isoformat(),
                    "finding": "mid_mismatch",
                }
            )
        if bbo.spread != bbo.ask - bbo.bid:
            quote_errors.append(
                {
                    "instrument_id": bbo.instrument_id,
                    "contract_id": bbo.contract_id,
                    "bar_start_ts": bbo.bar_start_ts.isoformat(),
                    "finding": "spread_mismatch",
                }
            )
        if (
            abnormal_spread_threshold is not None
            and not is_missing
            and bbo.spread > abnormal_spread_threshold
        ):
            abnormal_spread_findings.append(
                {
                    "instrument_id": bbo.instrument_id,
                    "contract_id": bbo.contract_id,
                    "bar_start_ts": bbo.bar_start_ts.isoformat(),
                    "finding": "abnormal_spread_outlier",
                    "spread": str(bbo.spread),
                    "threshold": str(abnormal_spread_threshold),
                }
            )
        if not is_missing and (bbo.bid_size == 0 or bbo.ask_size == 0):
            zero_size_anomalies.append(
                {
                    "instrument_id": bbo.instrument_id,
                    "contract_id": bbo.contract_id,
                    "bar_start_ts": bbo.bar_start_ts.isoformat(),
                    "finding": "zero_displayed_bbo_size",
                }
            )

    session_proxy_bars = tuple(
        _CanonicalBarView(
            instrument_id=bbo.instrument_id,
            contract_id=bbo.contract_id,
            series_id=bbo.series_id,
            bar_start_ts=bbo.bar_start_ts,
            bar_end_ts=bbo.bar_end_ts,
            event_ts=bbo.event_ts,
            available_ts=bbo.available_ts,
            ingested_at=bbo.ingested_at,
            open=bbo.bid,
            high=max(bbo.bid, bbo.ask),
            low=min(bbo.bid, bbo.ask),
            close=bbo.ask,
            volume=bbo.bid_size + bbo.ask_size,
            source=bbo.source,
            source_request_id=bbo.source_request_id,
            data_version=bbo.data_version,
            quality_flags=bbo.quality_flags,
            session_label=bbo.session_label,
        )
        for bbo in bbos
    )

    return MappingProxyType(
        {
            "gap_summary": _finding_summary(
                count=0,
                status=ReportStatus.PASSING,
                sample_key="sample_intervals",
            ),
            "duplicate_summary": _finding_summary(
                count=len(duplicates),
                status=_status_for_blocking_count(len(duplicates)),
                sample_key="sample_duplicates",
                samples=duplicates,
            ),
            "non_monotonic_summary": _finding_summary(
                count=len(non_monotonic),
                status=_status_for_blocking_count(len(non_monotonic)),
                sample_key="sample_pairs",
                samples=non_monotonic,
            ),
            "ohlc_errors": _finding_summary(
                count=len(alignment_findings),
                status=_status_for_blocking_count(len(alignment_findings)),
                sample_key="sample_errors",
                samples=alignment_findings,
            ),
            "zero_negative_price_errors": _finding_summary(
                count=len(quote_errors),
                status=_status_for_blocking_count(len(quote_errors)),
                sample_key="sample_errors",
                samples=quote_errors,
            ),
            "zero_volume_anomalies": _finding_summary(
                count=len(zero_size_anomalies),
                status=_status_for_warning_count(len(zero_size_anomalies)),
                sample_key="sample_anomalies",
                samples=zero_size_anomalies,
            ),
            "dst_anomalies": _passing_summary("sample_anomalies"),
            "session_coverage": _quality_session_summary(
                session_proxy_bars,
                expected_sessions,
            ),
            "roll_discontinuities": _roll_discontinuity_summary(
                session_proxy_bars,
                None,
            ),
            "provider_error_summary": _provider_error_summary(provider_errors),
            "bbo_missing_metric": _bbo_missing_metric_summary(missing_findings),
            "abnormal_spread_summary": _abnormal_spread_summary(
                tuple(abnormal_spread_findings)
            ),
        }
    )


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    """Fail-closed aggregate quality audit for canonical 1-minute bars.

    The report classifies data defects only. It does not imply alpha readiness,
    research approval, tradability, or production readiness.
    """

    quality_report_id: str
    dataset_version_id: str
    gap_summary: Mapping[str, object]
    duplicate_summary: Mapping[str, object]
    non_monotonic_summary: Mapping[str, object]
    ohlc_errors: Mapping[str, object]
    zero_negative_price_errors: Mapping[str, object]
    zero_volume_anomalies: Mapping[str, object]
    dst_anomalies: Mapping[str, object]
    session_coverage: Mapping[str, object]
    roll_discontinuities: Mapping[str, object]
    provider_error_summary: Mapping[str, object]
    bbo_missing_metric: Mapping[str, object]
    abnormal_spread_summary: Mapping[str, object]
    status: ReportStatus

    def __post_init__(self) -> None:
        quality_report_id = _normalize_id(self.quality_report_id, "quality_report_id")
        dataset_version_id = _normalize_id(self.dataset_version_id, "dataset_version_id")
        summaries = {
            "gap_summary": _normalize_quality_summary(
                self.gap_summary,
                "gap_summary",
            ),
            "duplicate_summary": _normalize_quality_summary(
                self.duplicate_summary,
                "duplicate_summary",
            ),
            "non_monotonic_summary": _normalize_quality_summary(
                self.non_monotonic_summary,
                "non_monotonic_summary",
            ),
            "ohlc_errors": _normalize_quality_summary(self.ohlc_errors, "ohlc_errors"),
            "zero_negative_price_errors": _normalize_quality_summary(
                self.zero_negative_price_errors,
                "zero_negative_price_errors",
            ),
            "zero_volume_anomalies": _normalize_quality_summary(
                self.zero_volume_anomalies,
                "zero_volume_anomalies",
            ),
            "dst_anomalies": _normalize_quality_summary(
                self.dst_anomalies,
                "dst_anomalies",
            ),
            "session_coverage": _normalize_quality_summary(
                self.session_coverage,
                "session_coverage",
            ),
            "roll_discontinuities": _normalize_quality_summary(
                self.roll_discontinuities,
                "roll_discontinuities",
            ),
            "provider_error_summary": _normalize_quality_summary(
                self.provider_error_summary,
                "provider_error_summary",
            ),
            "bbo_missing_metric": _normalize_quality_summary(
                self.bbo_missing_metric,
                "bbo_missing_metric",
            ),
            "abnormal_spread_summary": _normalize_quality_summary(
                self.abnormal_spread_summary,
                "abnormal_spread_summary",
            ),
        }
        status = _normalize_status(self.status, "status")
        derived_status = _derive_quality_status(summaries.values())
        if status is not derived_status:
            msg = f"status must be {derived_status.value} for the recorded findings"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "quality_report_id", quality_report_id)
        object.__setattr__(self, "dataset_version_id", dataset_version_id)
        for field_name, summary in summaries.items():
            object.__setattr__(self, field_name, summary)
        object.__setattr__(self, "status", status)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> DataQualityReport:
        """Build a report from aggregate persisted data and reject loose fields."""

        missing = tuple(
            field for field in DATA_QUALITY_REPORT_REQUIRED_FIELDS if field not in values
        )
        if missing:
            msg = "DataQualityReport missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        extra = tuple(field for field in values if field not in DATA_QUALITY_REPORT_FIELDS)
        if extra:
            msg = "DataQualityReport includes unsupported fields: " + ", ".join(extra)
            raise DataFoundationValidationError(msg)
        return cls(
            quality_report_id=_require_text(values["quality_report_id"], "quality_report_id"),
            dataset_version_id=_require_text(values["dataset_version_id"], "dataset_version_id"),
            gap_summary=_require_summary_mapping(values["gap_summary"], "gap_summary"),
            duplicate_summary=_require_summary_mapping(
                values["duplicate_summary"],
                "duplicate_summary",
            ),
            non_monotonic_summary=_require_summary_mapping(
                values["non_monotonic_summary"],
                "non_monotonic_summary",
            ),
            ohlc_errors=_require_summary_mapping(values["ohlc_errors"], "ohlc_errors"),
            zero_negative_price_errors=_require_summary_mapping(
                values["zero_negative_price_errors"],
                "zero_negative_price_errors",
            ),
            zero_volume_anomalies=_require_summary_mapping(
                values["zero_volume_anomalies"],
                "zero_volume_anomalies",
            ),
            dst_anomalies=_require_summary_mapping(values["dst_anomalies"], "dst_anomalies"),
            session_coverage=_require_summary_mapping(
                values["session_coverage"],
                "session_coverage",
            ),
            roll_discontinuities=_require_summary_mapping(
                values["roll_discontinuities"],
                "roll_discontinuities",
            ),
            provider_error_summary=_require_summary_mapping(
                values["provider_error_summary"],
                "provider_error_summary",
            ),
            bbo_missing_metric=_require_summary_mapping(
                values.get("bbo_missing_metric", _empty_bbo_missing_metric()),
                "bbo_missing_metric",
            ),
            abnormal_spread_summary=_require_summary_mapping(
                values.get("abnormal_spread_summary", _empty_abnormal_spread_summary()),
                "abnormal_spread_summary",
            ),
            status=_normalize_status(values["status"], "status"),
        )

    @classmethod
    def from_canonical_bars(
        cls,
        *,
        quality_report_id: object,
        dataset_version_id: object,
        bars: Iterable[CanonicalBarRecord | Mapping[str, object]],
        provider_errors: Iterable[ProviderErrorRecord | Mapping[str, object]] = (),
        expected_interval_seconds: object = BAR_SIZE_SECONDS_1M,
        expected_sessions: Iterable[str] | None = None,
        expected_gap_intervals: Iterable[Mapping[str, object]] | None = None,
        roll_transitions: Iterable[Mapping[str, object]] | None = None,
    ) -> DataQualityReport:
        """Compute aggregate quality findings from canonical 1-minute bar fields."""

        interval_seconds = _expected_interval_seconds(expected_interval_seconds)
        bar_views = tuple(_canonical_bar_view(bar) for bar in bars)
        if not bar_views:
            msg = "DataQualityReport requires at least one canonical bar"
            raise DataFoundationValidationError(msg)
        summaries = _compute_quality_summaries(
            bar_views,
            expected_interval_seconds=interval_seconds,
            expected_sessions=expected_sessions,
            expected_gap_intervals=expected_gap_intervals,
            roll_transitions=roll_transitions,
            provider_errors=provider_errors,
        )
        status = _derive_quality_status(summaries.values())
        return cls(
            quality_report_id=_require_text(quality_report_id, "quality_report_id"),
            dataset_version_id=_require_text(dataset_version_id, "dataset_version_id"),
            gap_summary=summaries["gap_summary"],
            duplicate_summary=summaries["duplicate_summary"],
            non_monotonic_summary=summaries["non_monotonic_summary"],
            ohlc_errors=summaries["ohlc_errors"],
            zero_negative_price_errors=summaries["zero_negative_price_errors"],
            zero_volume_anomalies=summaries["zero_volume_anomalies"],
            dst_anomalies=summaries["dst_anomalies"],
            session_coverage=summaries["session_coverage"],
            roll_discontinuities=summaries["roll_discontinuities"],
            provider_error_summary=summaries["provider_error_summary"],
            bbo_missing_metric=summaries["bbo_missing_metric"],
            abnormal_spread_summary=summaries["abnormal_spread_summary"],
            status=status,
        )

    @classmethod
    def from_canonical_bbos(
        cls,
        *,
        quality_report_id: object,
        dataset_version_id: object,
        bbos: Iterable[CanonicalBBORecord | Mapping[str, object]],
        expected_ohlcv_bars: Iterable[CanonicalBarRecord | Mapping[str, object]] | None = None,
        provider_errors: Iterable[ProviderErrorRecord | Mapping[str, object]] = (),
        expected_interval_seconds: object = BAR_SIZE_SECONDS_1M,
        expected_sessions: Iterable[str] | None = None,
        abnormal_spread_threshold: object | None = None,
    ) -> DataQualityReport:
        """Compute aggregate quality findings from canonical 1-minute BBO fields."""

        interval_seconds = _expected_interval_seconds(expected_interval_seconds)
        bbo_views = tuple(_canonical_bbo_view(bbo) for bbo in bbos)
        if not bbo_views:
            msg = "DataQualityReport requires at least one canonical BBO"
            raise DataFoundationValidationError(msg)
        threshold = _normalize_optional_decimal(
            abnormal_spread_threshold,
            "abnormal_spread_threshold",
        )
        summaries = _compute_bbo_quality_summaries(
            bbo_views,
            expected_interval_seconds=interval_seconds,
            expected_sessions=expected_sessions,
            expected_ohlcv_bars=expected_ohlcv_bars,
            abnormal_spread_threshold=threshold,
            provider_errors=provider_errors,
        )
        status = _derive_quality_status(summaries.values())
        return cls(
            quality_report_id=_require_text(quality_report_id, "quality_report_id"),
            dataset_version_id=_require_text(dataset_version_id, "dataset_version_id"),
            gap_summary=summaries["gap_summary"],
            duplicate_summary=summaries["duplicate_summary"],
            non_monotonic_summary=summaries["non_monotonic_summary"],
            ohlc_errors=summaries["ohlc_errors"],
            zero_negative_price_errors=summaries["zero_negative_price_errors"],
            zero_volume_anomalies=summaries["zero_volume_anomalies"],
            dst_anomalies=summaries["dst_anomalies"],
            session_coverage=summaries["session_coverage"],
            roll_discontinuities=summaries["roll_discontinuities"],
            provider_error_summary=summaries["provider_error_summary"],
            bbo_missing_metric=summaries["bbo_missing_metric"],
            abnormal_spread_summary=summaries["abnormal_spread_summary"],
            status=status,
        )

    @property
    def blocks_versioning(self) -> bool:
        """Return true when quality findings must block dataset versioning."""

        return self.status is ReportStatus.BLOCKING

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable aggregate report mapping."""

        return MappingProxyType(
            {
                "quality_report_id": self.quality_report_id,
                "dataset_version_id": self.dataset_version_id,
                "gap_summary": self.gap_summary,
                "duplicate_summary": self.duplicate_summary,
                "non_monotonic_summary": self.non_monotonic_summary,
                "ohlc_errors": self.ohlc_errors,
                "zero_negative_price_errors": self.zero_negative_price_errors,
                "zero_volume_anomalies": self.zero_volume_anomalies,
                "dst_anomalies": self.dst_anomalies,
                "session_coverage": self.session_coverage,
                "roll_discontinuities": self.roll_discontinuities,
                "provider_error_summary": self.provider_error_summary,
                "bbo_missing_metric": self.bbo_missing_metric,
                "abnormal_spread_summary": self.abnormal_spread_summary,
                "status": self.status.value,
            }
        )


def compute_quality_report_hash(report: DataQualityReport) -> str:
    """Return the deterministic hash a DatasetVersion must bind to."""

    if not isinstance(report, DataQualityReport):
        msg = "quality_report_hash binding requires a DataQualityReport"
        raise DataFoundationValidationError(msg)
    return hash_config(report.to_mapping())


def _normalize_expected_interval(value: object) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "expected_intervals must contain aggregate interval mappings"
        raise DataFoundationValidationError(msg)
    required = (
        "symbol",
        "instrument_id",
        "contract_id",
        "session_label",
        "start_ts",
        "end_ts",
        "partition_id",
    )
    missing = tuple(field for field in required if field not in value)
    if missing:
        msg = "coverage expected interval missing required fields: " + ", ".join(missing)
        raise DataFoundationValidationError(msg)
    start = _parse_aware_datetime(value["start_ts"], "expected_interval.start_ts")
    end = _parse_aware_datetime(value["end_ts"], "expected_interval.end_ts")
    if end <= start:
        msg = "coverage expected interval end_ts must be greater than start_ts"
        raise DataFoundationValidationError(msg)
    return MappingProxyType(
        {
            "symbol": _require_text(value["symbol"], "expected_interval.symbol").upper(),
            "instrument_id": _normalize_id(value["instrument_id"], "instrument_id"),
            "contract_id": _normalize_id(value["contract_id"], "contract_id"),
            "session_label": _require_text(
                value["session_label"],
                "expected_interval.session_label",
            ).upper(),
            "start_ts": start,
            "end_ts": end,
            "partition_id": _normalize_id(value["partition_id"], "partition_id"),
        }
    )


def _expected_bar_count(start: datetime, end: datetime, interval_seconds: int) -> int:
    seconds = int((end - start).total_seconds())
    if seconds <= 0 or seconds % interval_seconds != 0:
        msg = "coverage expected intervals must align to complete 1-minute bars"
        raise DataFoundationValidationError(msg)
    return seconds // interval_seconds


def _observed_count_for_interval(
    bars: tuple[_CanonicalBarView, ...],
    interval: Mapping[str, object],
) -> int:
    start = interval["start_ts"]
    end = interval["end_ts"]
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        msg = "normalized coverage interval carries invalid timestamps"
        raise DataFoundationValidationError(msg)
    return sum(
        1
        for bar in bars
        if bar.instrument_id == interval["instrument_id"]
        and bar.contract_id == interval["contract_id"]
        and bar.session_label == interval["session_label"]
        and start <= bar.bar_start_ts
        and bar.bar_end_ts <= end
    )


def _observed_bbo_count_for_interval(
    bbos: tuple[_CanonicalBBOView, ...],
    interval: Mapping[str, object],
) -> int:
    start = interval["start_ts"]
    end = interval["end_ts"]
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        msg = "normalized coverage interval carries invalid timestamps"
        raise DataFoundationValidationError(msg)
    return sum(
        1
        for bbo in bbos
        if bbo.instrument_id == interval["instrument_id"]
        and bbo.contract_id == interval["contract_id"]
        and bbo.session_label == interval["session_label"]
        and start <= bbo.bar_start_ts
        and bbo.bar_end_ts <= end
    )


def _build_bbo_count_index(
    bbos: tuple[_CanonicalBBOView, ...],
) -> Mapping[tuple[str, str, str], tuple[list[datetime], list[datetime]]]:
    """Group BBO views by (instrument, contract, session) with start-sorted arrays.

    Returns key -> (sorted bar_start_ts list, parallel bar_end_ts list) so an
    interval's observed count is a bisect + short forward scan rather than a full
    rescan of every BBO view.
    """

    grouped: dict[tuple[str, str, str], list[tuple[datetime, datetime]]] = defaultdict(list)
    for bbo in bbos:
        grouped[(bbo.instrument_id, bbo.contract_id, bbo.session_label)].append(
            (bbo.bar_start_ts, bbo.bar_end_ts)
        )
    index: dict[tuple[str, str, str], tuple[list[datetime], list[datetime]]] = {}
    for key, pairs in grouped.items():
        pairs.sort(key=lambda pair: pair[0])
        index[key] = ([pair[0] for pair in pairs], [pair[1] for pair in pairs])
    return index


def _observed_bbo_count_indexed(
    index: Mapping[tuple[str, str, str], tuple[list[datetime], list[datetime]]],
    interval: Mapping[str, object],
) -> int:
    start = interval["start_ts"]
    end = interval["end_ts"]
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        msg = "normalized coverage interval carries invalid timestamps"
        raise DataFoundationValidationError(msg)
    entry = index.get(
        (
            str(interval["instrument_id"]),
            str(interval["contract_id"]),
            str(interval["session_label"]),
        )
    )
    if entry is None:
        return 0
    starts, ends = entry
    count = 0
    position = bisect_left(starts, start)
    total = len(starts)
    # Equivalent to: count views with start <= bar_start_ts and bar_end_ts <= end.
    while position < total and starts[position] <= end:
        if ends[position] <= end:
            count += 1
        position += 1
    return count


def _coverage_bucket_summary(
    *,
    bucket_name: str,
    entries: Mapping[str, Mapping[str, int]],
    missing_interval_count: int | None = None,
    incomplete_chunk_count: int | None = None,
) -> Mapping[str, object]:
    samples = []
    expected_total = 0
    observed_total = 0
    missing_total = 0
    for key, counts in sorted(entries.items()):
        expected = _require_non_negative_int(counts["expected"], f"{bucket_name}.expected")
        observed = _require_non_negative_int(counts["observed"], f"{bucket_name}.observed")
        missing = _require_non_negative_int(counts["missing"], f"{bucket_name}.missing")
        expected_total += expected
        observed_total += observed
        missing_total += missing
        samples.append(
            {
                bucket_name: key,
                "expected_bar_count": expected,
                "observed_bar_count": observed,
                "missing_bar_count": missing,
            }
        )

    status = ReportStatus.BLOCKING if missing_total else ReportStatus.PASSING
    summary: dict[str, object] = {
        "status": status.value,
        "blocking": status is ReportStatus.BLOCKING,
        "expected_count": expected_total,
        "observed_count": observed_total,
        "missing_count": missing_total,
        "sample_buckets": _capped_samples(samples),
        "truncated": len(samples) > MAX_SUMMARY_ITEMS,
    }
    if missing_interval_count is not None:
        summary["missing_interval_count"] = missing_interval_count
    if incomplete_chunk_count is not None:
        summary["incomplete_chunk_count"] = incomplete_chunk_count
        if incomplete_chunk_count:
            summary["status"] = ReportStatus.BLOCKING.value
            summary["blocking"] = True
    return MappingProxyType(summary)


def _normalize_coverage_summary(value: object, field_name: str) -> Mapping[str, object]:
    summary = dict(_require_summary_mapping(value, field_name))
    for key in ("status", "blocking", "expected_count", "observed_count", "missing_count"):
        if key not in summary:
            msg = f"{field_name}.{key} is required"
            raise DataFoundationValidationError(msg)
    status = _normalize_status(summary["status"], f"{field_name}.status")
    blocking = _require_bool(summary["blocking"], f"{field_name}.blocking")
    expected = _require_non_negative_int(
        summary["expected_count"],
        f"{field_name}.expected_count",
    )
    observed = _require_non_negative_int(
        summary["observed_count"],
        f"{field_name}.observed_count",
    )
    missing = _require_non_negative_int(
        summary["missing_count"],
        f"{field_name}.missing_count",
    )
    if observed > expected:
        msg = f"{field_name}.observed_count must not exceed expected_count"
        raise DataFoundationValidationError(msg)
    if expected - observed != missing:
        msg = f"{field_name}.missing_count must reconcile expected_count and observed_count"
        raise DataFoundationValidationError(msg)
    if missing and status is not ReportStatus.BLOCKING:
        msg = f"{field_name} with missing coverage must be BLOCKING"
        raise DataFoundationValidationError(msg)
    if status is ReportStatus.BLOCKING and not blocking:
        msg = f"{field_name}.blocking must be true for BLOCKING coverage"
        raise DataFoundationValidationError(msg)
    if status is not ReportStatus.BLOCKING and blocking:
        msg = f"{field_name}.blocking must be false unless coverage is BLOCKING"
        raise DataFoundationValidationError(msg)

    summary["status"] = status.value
    summary["blocking"] = blocking
    summary["expected_count"] = expected
    summary["observed_count"] = observed
    summary["missing_count"] = missing
    return MappingProxyType(summary)


def _normalize_interval_summaries(
    value: object,
    field_name: str,
) -> tuple[Mapping[str, object], ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = f"{field_name} must be an explicit collection of aggregate intervals"
        raise DataFoundationValidationError(msg)
    intervals = []
    for item in value:
        frozen = _freeze_json_value(item, f"{field_name}[]")
        if not isinstance(frozen, Mapping):
            msg = f"{field_name} entries must be aggregate mappings"
            raise DataFoundationValidationError(msg)
        for required in ("start_ts", "end_ts", "status"):
            if required not in frozen:
                msg = f"{field_name}.{required} is required"
                raise DataFoundationValidationError(msg)
        start = _parse_aware_datetime(frozen["start_ts"], f"{field_name}.start_ts")
        end = _parse_aware_datetime(frozen["end_ts"], f"{field_name}.end_ts")
        if end <= start:
            msg = f"{field_name} intervals must have end_ts greater than start_ts"
            raise DataFoundationValidationError(msg)
        status = _normalize_status(frozen["status"], f"{field_name}.status")
        if status is not ReportStatus.BLOCKING:
            msg = f"{field_name} entries document blocking missing coverage"
            raise DataFoundationValidationError(msg)
        normalized = dict(frozen)
        normalized["start_ts"] = start.isoformat()
        normalized["end_ts"] = end.isoformat()
        normalized["status"] = status.value
        intervals.append(MappingProxyType(normalized))
    if len(intervals) > MAX_SUMMARY_ITEMS:
        msg = f"{field_name} must be capped at {MAX_SUMMARY_ITEMS} aggregate entries"
        raise DataFoundationValidationError(msg)
    return tuple(intervals)


def _normalize_incomplete_chunks(value: object) -> tuple[Mapping[str, object], ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = "incomplete_chunks must be an explicit collection of aggregate chunk summaries"
        raise DataFoundationValidationError(msg)
    chunks = []
    for item in value:
        frozen = _freeze_json_value(item, "incomplete_chunks[]")
        if not isinstance(frozen, Mapping):
            msg = "incomplete_chunks entries must be aggregate mappings"
            raise DataFoundationValidationError(msg)
        for required in ("chunk_id", "status", "start_ts", "end_ts"):
            if required not in frozen:
                msg = f"incomplete_chunks.{required} is required"
                raise DataFoundationValidationError(msg)
        status = _require_text(frozen["status"], "incomplete_chunks.status").upper()
        if status == "COMPLETE":
            msg = "incomplete_chunks must not include COMPLETE chunks"
            raise DataFoundationValidationError(msg)
        start = _parse_aware_datetime(frozen["start_ts"], "incomplete_chunks.start_ts")
        end = _parse_aware_datetime(frozen["end_ts"], "incomplete_chunks.end_ts")
        if end <= start:
            msg = "incomplete_chunks intervals must have end_ts greater than start_ts"
            raise DataFoundationValidationError(msg)
        normalized = dict(frozen)
        normalized["chunk_id"] = _normalize_id(normalized["chunk_id"], "chunk_id")
        normalized["status"] = status
        normalized["start_ts"] = start.isoformat()
        normalized["end_ts"] = end.isoformat()
        chunks.append(MappingProxyType(normalized))
    if len(chunks) > MAX_SUMMARY_ITEMS:
        msg = "incomplete_chunks must be capped at 25 aggregate entries"
        raise DataFoundationValidationError(msg)
    return tuple(chunks)


def _normalize_input_incomplete_chunk(value: object) -> Mapping[str, object]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "incomplete chunk inputs must be aggregate mappings"
        raise DataFoundationValidationError(msg)
    required = ("chunk_id", "status", "start_ts", "end_ts")
    missing = tuple(field for field in required if field not in value)
    if missing:
        msg = "incomplete chunk input missing required fields: " + ", ".join(missing)
        raise DataFoundationValidationError(msg)
    status = _require_text(value["status"], "incomplete_chunk.status").upper()
    if status == "COMPLETE":
        msg = "incomplete chunk inputs must not include COMPLETE chunks"
        raise DataFoundationValidationError(msg)
    return MappingProxyType(
        {
            "chunk_id": _normalize_id(value["chunk_id"], "chunk_id"),
            "status": status,
            "start_ts": _parse_aware_datetime(
                value["start_ts"],
                "incomplete_chunk.start_ts",
            ).isoformat(),
            "end_ts": _parse_aware_datetime(
                value["end_ts"],
                "incomplete_chunk.end_ts",
            ).isoformat(),
            "reason": _require_text(value.get("reason", "incomplete_chunk"), "reason"),
        }
    )


def _coverage_status(
    summaries: Iterable[Mapping[str, object]],
    missing_intervals: tuple[Mapping[str, object], ...],
    incomplete_chunks: tuple[Mapping[str, object], ...],
) -> ReportStatus:
    if missing_intervals or incomplete_chunks:
        return ReportStatus.BLOCKING
    for summary in summaries:
        if _normalize_status(summary["status"], "coverage.status") is ReportStatus.BLOCKING:
            return ReportStatus.BLOCKING
    return ReportStatus.PASSING


@dataclass(frozen=True, slots=True)
class CoverageReport:
    """Aggregate coverage report that does not imply quality by itself."""

    coverage_report_id: str
    dataset_version_id: str
    symbol_coverage: Mapping[str, object]
    contract_coverage: Mapping[str, object]
    session_coverage: Mapping[str, object]
    partition_coverage: Mapping[str, object]
    missing_intervals: tuple[Mapping[str, object], ...]
    incomplete_chunks: tuple[Mapping[str, object], ...]

    def __post_init__(self) -> None:
        coverage_report_id = _normalize_id(self.coverage_report_id, "coverage_report_id")
        dataset_version_id = _normalize_id(self.dataset_version_id, "dataset_version_id")
        symbol_coverage = _normalize_coverage_summary(
            self.symbol_coverage,
            "symbol_coverage",
        )
        contract_coverage = _normalize_coverage_summary(
            self.contract_coverage,
            "contract_coverage",
        )
        session_coverage = _normalize_coverage_summary(
            self.session_coverage,
            "session_coverage",
        )
        partition_coverage = _normalize_coverage_summary(
            self.partition_coverage,
            "partition_coverage",
        )
        missing_intervals = _normalize_interval_summaries(
            self.missing_intervals,
            "missing_intervals",
        )
        incomplete_chunks = _normalize_incomplete_chunks(self.incomplete_chunks)

        for required_key in ("missing_interval_count", "incomplete_chunk_count"):
            if required_key not in partition_coverage:
                msg = f"partition_coverage.{required_key} is required"
                raise DataFoundationValidationError(msg)
        missing_interval_count = _require_non_negative_int(
            partition_coverage["missing_interval_count"],
            "partition_coverage.missing_interval_count",
        )
        incomplete_chunk_count = _require_non_negative_int(
            partition_coverage["incomplete_chunk_count"],
            "partition_coverage.incomplete_chunk_count",
        )
        if missing_interval_count != len(missing_intervals):
            msg = "partition_coverage.missing_interval_count must document missing_intervals"
            raise DataFoundationValidationError(msg)
        if incomplete_chunk_count != len(incomplete_chunks):
            msg = "partition_coverage.incomplete_chunk_count must document incomplete_chunks"
            raise DataFoundationValidationError(msg)
        if any(
            summary["missing_count"] and not missing_intervals
            for summary in (
                symbol_coverage,
                contract_coverage,
                session_coverage,
                partition_coverage,
            )
        ):
            msg = "undocumented missing coverage must fail closed"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "coverage_report_id", coverage_report_id)
        object.__setattr__(self, "dataset_version_id", dataset_version_id)
        object.__setattr__(self, "symbol_coverage", symbol_coverage)
        object.__setattr__(self, "contract_coverage", contract_coverage)
        object.__setattr__(self, "session_coverage", session_coverage)
        object.__setattr__(self, "partition_coverage", partition_coverage)
        object.__setattr__(self, "missing_intervals", missing_intervals)
        object.__setattr__(self, "incomplete_chunks", incomplete_chunks)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> CoverageReport:
        """Build a coverage report from aggregate data and reject loose fields."""

        missing = tuple(field for field in COVERAGE_REPORT_FIELDS if field not in values)
        if missing:
            msg = "CoverageReport missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        extra = tuple(field for field in values if field not in COVERAGE_REPORT_FIELDS)
        if extra:
            msg = "CoverageReport includes unsupported fields: " + ", ".join(extra)
            raise DataFoundationValidationError(msg)
        return cls(
            coverage_report_id=_require_text(values["coverage_report_id"], "coverage_report_id"),
            dataset_version_id=_require_text(values["dataset_version_id"], "dataset_version_id"),
            symbol_coverage=_require_summary_mapping(
                values["symbol_coverage"],
                "symbol_coverage",
            ),
            contract_coverage=_require_summary_mapping(
                values["contract_coverage"],
                "contract_coverage",
            ),
            session_coverage=_require_summary_mapping(
                values["session_coverage"],
                "session_coverage",
            ),
            partition_coverage=_require_summary_mapping(
                values["partition_coverage"],
                "partition_coverage",
            ),
            missing_intervals=_normalize_interval_summaries(
                values["missing_intervals"],
                "missing_intervals",
            ),
            incomplete_chunks=_normalize_incomplete_chunks(values["incomplete_chunks"]),
        )

    @classmethod
    def from_canonical_bars(
        cls,
        *,
        coverage_report_id: object,
        dataset_version_id: object,
        bars: Iterable[CanonicalBarRecord | Mapping[str, object]],
        expected_intervals: Iterable[Mapping[str, object]],
        incomplete_chunks: Iterable[Mapping[str, object]] = (),
        expected_interval_seconds: object = BAR_SIZE_SECONDS_1M,
    ) -> CoverageReport:
        """Compute symbol, contract, session, and partition coverage summaries."""

        interval_seconds = _expected_interval_seconds(expected_interval_seconds)
        bar_views = tuple(_canonical_bar_view(bar) for bar in bars)
        intervals = tuple(_normalize_expected_interval(interval) for interval in expected_intervals)
        if not intervals:
            msg = "CoverageReport requires explicit expected_intervals"
            raise DataFoundationValidationError(msg)

        symbol_entries: dict[str, dict[str, int]] = defaultdict(
            lambda: {"expected": 0, "observed": 0, "missing": 0}
        )
        contract_entries: dict[str, dict[str, int]] = defaultdict(
            lambda: {"expected": 0, "observed": 0, "missing": 0}
        )
        session_entries: dict[str, dict[str, int]] = defaultdict(
            lambda: {"expected": 0, "observed": 0, "missing": 0}
        )
        partition_entries: dict[str, dict[str, int]] = defaultdict(
            lambda: {"expected": 0, "observed": 0, "missing": 0}
        )
        missing_interval_summaries = []

        for interval in intervals:
            start = interval["start_ts"]
            end = interval["end_ts"]
            if not isinstance(start, datetime) or not isinstance(end, datetime):
                msg = "normalized coverage interval carries invalid timestamps"
                raise DataFoundationValidationError(msg)
            expected_count = _expected_bar_count(start, end, interval_seconds)
            observed_count = _observed_count_for_interval(bar_views, interval)
            missing_count = max(0, expected_count - observed_count)
            keys = {
                "symbol": str(interval["symbol"]),
                "contract": str(interval["contract_id"]),
                "session": str(interval["session_label"]),
                "partition": str(interval["partition_id"]),
            }
            for entries, key_name in (
                (symbol_entries, "symbol"),
                (contract_entries, "contract"),
                (session_entries, "session"),
                (partition_entries, "partition"),
            ):
                entries[keys[key_name]]["expected"] += expected_count
                entries[keys[key_name]]["observed"] += observed_count
                entries[keys[key_name]]["missing"] += missing_count
            if missing_count:
                missing_interval_summaries.append(
                    {
                        "symbol": interval["symbol"],
                        "instrument_id": interval["instrument_id"],
                        "contract_id": interval["contract_id"],
                        "session_label": interval["session_label"],
                        "partition_id": interval["partition_id"],
                        "start_ts": start.isoformat(),
                        "end_ts": end.isoformat(),
                        "expected_bar_count": expected_count,
                        "observed_bar_count": observed_count,
                        "missing_bar_count": missing_count,
                        "status": ReportStatus.BLOCKING.value,
                    }
                )

        chunk_summaries = tuple(
            _normalize_input_incomplete_chunk(chunk) for chunk in incomplete_chunks
        )
        missing_interval_count = len(missing_interval_summaries)
        incomplete_chunk_count = len(chunk_summaries)
        return cls(
            coverage_report_id=_require_text(coverage_report_id, "coverage_report_id"),
            dataset_version_id=_require_text(dataset_version_id, "dataset_version_id"),
            symbol_coverage=_coverage_bucket_summary(
                bucket_name="symbol",
                entries=symbol_entries,
            ),
            contract_coverage=_coverage_bucket_summary(
                bucket_name="contract",
                entries=contract_entries,
            ),
            session_coverage=_coverage_bucket_summary(
                bucket_name="session",
                entries=session_entries,
            ),
            partition_coverage=_coverage_bucket_summary(
                bucket_name="partition",
                entries=partition_entries,
                missing_interval_count=missing_interval_count,
                incomplete_chunk_count=incomplete_chunk_count,
            ),
            missing_intervals=tuple(missing_interval_summaries),
            incomplete_chunks=chunk_summaries,
        )

    @classmethod
    def from_canonical_bbos(
        cls,
        *,
        coverage_report_id: object,
        dataset_version_id: object,
        bbos: Iterable[CanonicalBBORecord | Mapping[str, object]],
        expected_intervals: Iterable[Mapping[str, object]],
        incomplete_chunks: Iterable[Mapping[str, object]] = (),
        expected_interval_seconds: object = BAR_SIZE_SECONDS_1M,
    ) -> CoverageReport:
        """Compute BBO symbol, contract, session, and partition coverage summaries."""

        interval_seconds = _expected_interval_seconds(expected_interval_seconds)
        bbo_views = tuple(_canonical_bbo_view(bbo) for bbo in bbos)
        intervals = tuple(_normalize_expected_interval(interval) for interval in expected_intervals)
        if not intervals:
            msg = "CoverageReport requires explicit expected_intervals"
            raise DataFoundationValidationError(msg)

        symbol_entries: dict[str, dict[str, int]] = defaultdict(
            lambda: {"expected": 0, "observed": 0, "missing": 0}
        )
        contract_entries: dict[str, dict[str, int]] = defaultdict(
            lambda: {"expected": 0, "observed": 0, "missing": 0}
        )
        session_entries: dict[str, dict[str, int]] = defaultdict(
            lambda: {"expected": 0, "observed": 0, "missing": 0}
        )
        partition_entries: dict[str, dict[str, int]] = defaultdict(
            lambda: {"expected": 0, "observed": 0, "missing": 0}
        )
        missing_interval_summaries = []

        # Index BBO views by (instrument, contract, session) with sorted starts so
        # each interval is counted via bisect instead of rescanning every view
        # (avoids O(intervals * bbos) on large dense panels).
        bbo_count_index = _build_bbo_count_index(bbo_views)

        for interval in intervals:
            start = interval["start_ts"]
            end = interval["end_ts"]
            if not isinstance(start, datetime) or not isinstance(end, datetime):
                msg = "normalized coverage interval carries invalid timestamps"
                raise DataFoundationValidationError(msg)
            expected_count = _expected_bar_count(start, end, interval_seconds)
            observed_count = _observed_bbo_count_indexed(bbo_count_index, interval)
            missing_count = max(0, expected_count - observed_count)
            keys = {
                "symbol": str(interval["symbol"]),
                "contract": str(interval["contract_id"]),
                "session": str(interval["session_label"]),
                "partition": str(interval["partition_id"]),
            }
            for entries, key_name in (
                (symbol_entries, "symbol"),
                (contract_entries, "contract"),
                (session_entries, "session"),
                (partition_entries, "partition"),
            ):
                entries[keys[key_name]]["expected"] += expected_count
                entries[keys[key_name]]["observed"] += observed_count
                entries[keys[key_name]]["missing"] += missing_count
            if missing_count:
                missing_interval_summaries.append(
                    {
                        "symbol": interval["symbol"],
                        "instrument_id": interval["instrument_id"],
                        "contract_id": interval["contract_id"],
                        "session_label": interval["session_label"],
                        "partition_id": interval["partition_id"],
                        "start_ts": start.isoformat(),
                        "end_ts": end.isoformat(),
                        "expected_bar_count": expected_count,
                        "observed_bar_count": observed_count,
                        "missing_bar_count": missing_count,
                        "status": ReportStatus.BLOCKING.value,
                    }
                )

        chunk_summaries = tuple(
            _normalize_input_incomplete_chunk(chunk) for chunk in incomplete_chunks
        )
        missing_interval_count = len(missing_interval_summaries)
        incomplete_chunk_count = len(chunk_summaries)
        return cls(
            coverage_report_id=_require_text(coverage_report_id, "coverage_report_id"),
            dataset_version_id=_require_text(dataset_version_id, "dataset_version_id"),
            symbol_coverage=_coverage_bucket_summary(
                bucket_name="symbol",
                entries=symbol_entries,
            ),
            contract_coverage=_coverage_bucket_summary(
                bucket_name="contract",
                entries=contract_entries,
            ),
            session_coverage=_coverage_bucket_summary(
                bucket_name="session",
                entries=session_entries,
            ),
            partition_coverage=_coverage_bucket_summary(
                bucket_name="partition",
                entries=partition_entries,
                missing_interval_count=missing_interval_count,
                incomplete_chunk_count=incomplete_chunk_count,
            ),
            missing_intervals=tuple(missing_interval_summaries),
            incomplete_chunks=chunk_summaries,
        )

    @property
    def coverage_status(self) -> ReportStatus:
        """Return the coverage-only gate status."""

        return _coverage_status(
            (
                self.symbol_coverage,
                self.contract_coverage,
                self.session_coverage,
                self.partition_coverage,
            ),
            self.missing_intervals,
            self.incomplete_chunks,
        )

    @property
    def blocks_versioning(self) -> bool:
        """Return true when missing coverage or incomplete chunks block versioning."""

        return self.coverage_status is ReportStatus.BLOCKING

    def require_linked_quality_report(
        self,
        quality_report: DataQualityReport | None,
    ) -> DataQualityReport:
        """Require an explicit non-blocking quality report for this dataset version."""

        if quality_report is None:
            msg = "coverage alone is not quality; linked DataQualityReport is required"
            raise DataFoundationValidationError(msg)
        if quality_report.dataset_version_id != self.dataset_version_id:
            msg = "CoverageReport and DataQualityReport dataset_version_id must match"
            raise DataFoundationValidationError(msg)
        if self.blocks_versioning:
            msg = "blocking coverage report cannot be treated as quality passed"
            raise DataFoundationValidationError(msg)
        if quality_report.blocks_versioning:
            msg = "blocking DataQualityReport prevents coverage-quality linkage"
            raise DataFoundationValidationError(msg)
        return quality_report


    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable aggregate coverage mapping."""

        return MappingProxyType(
            {
                "coverage_report_id": self.coverage_report_id,
                "dataset_version_id": self.dataset_version_id,
                "symbol_coverage": self.symbol_coverage,
                "contract_coverage": self.contract_coverage,
                "session_coverage": self.session_coverage,
                "partition_coverage": self.partition_coverage,
                "missing_intervals": self.missing_intervals,
                "incomplete_chunks": self.incomplete_chunks,
            }
        )


def _extract_manifest_hash(source_manifest: object) -> str:
    if source_manifest is None:
        msg = "source manifest is required before dataset versioning"
        raise DataFoundationValidationError(msg)
    if isinstance(source_manifest, Mapping):
        if "manifest_hash" not in source_manifest:
            msg = "source manifest must expose manifest_hash"
            raise DataFoundationValidationError(msg)
        return _normalize_sha256_hash(
            source_manifest["manifest_hash"],
            "source_manifest.manifest_hash",
        )
    manifest_hash = getattr(source_manifest, "manifest_hash", None)
    if manifest_hash is None:
        msg = "source manifest must expose manifest_hash"
        raise DataFoundationValidationError(msg)
    return _normalize_sha256_hash(manifest_hash, "source_manifest.manifest_hash")


@dataclass(frozen=True, slots=True)
class DatasetVersion:
    """Reproducible canonical dataset version bound to quality and manifest hashes.

    The object is a data-admissibility record only. It does not imply research
    approval, tradability, alpha value, or production readiness.
    """

    dataset_version_id: str
    source: str
    symbol_universe: tuple[str, ...]
    bar_size: str
    what_to_show: str
    start_ts: datetime
    end_ts: datetime
    contract_universe: tuple[str, ...]
    roll_policy_id: str
    manifest_hash: str
    code_hash: str
    config_hash: str
    quality_report_hash: str
    created_at: datetime

    def __post_init__(self) -> None:
        dataset_version_id = _normalize_id(self.dataset_version_id, "dataset_version_id")
        source = _normalize_id(self.source, "source")
        symbol_universe = _normalize_symbol_universe(self.symbol_universe)
        bar_size = _require_text(self.bar_size, "bar_size")
        what_to_show = _require_text(self.what_to_show, "what_to_show").upper()
        start_ts = _parse_aware_datetime(self.start_ts, "start_ts")
        end_ts = _parse_aware_datetime(self.end_ts, "end_ts")
        if end_ts < start_ts:
            msg = "end_ts must not be earlier than start_ts"
            raise DataFoundationValidationError(msg)
        contract_universe = _normalize_contract_universe(self.contract_universe)
        roll_policy_id = _normalize_id(self.roll_policy_id, "roll_policy_id")
        manifest_hash = _normalize_sha256_hash(self.manifest_hash, "manifest_hash")
        code_hash = _normalize_sha256_hash(self.code_hash, "code_hash")
        config_hash = _normalize_sha256_hash(self.config_hash, "config_hash")
        quality_report_hash = _normalize_sha256_hash(
            self.quality_report_hash,
            "quality_report_hash",
        )
        created_at = _parse_aware_datetime(self.created_at, "created_at")

        object.__setattr__(self, "dataset_version_id", dataset_version_id)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "symbol_universe", symbol_universe)
        object.__setattr__(self, "bar_size", bar_size)
        object.__setattr__(self, "what_to_show", what_to_show)
        object.__setattr__(self, "start_ts", start_ts)
        object.__setattr__(self, "end_ts", end_ts)
        object.__setattr__(self, "contract_universe", contract_universe)
        object.__setattr__(self, "roll_policy_id", roll_policy_id)
        object.__setattr__(self, "manifest_hash", manifest_hash)
        object.__setattr__(self, "code_hash", code_hash)
        object.__setattr__(self, "config_hash", config_hash)
        object.__setattr__(self, "quality_report_hash", quality_report_hash)
        object.__setattr__(self, "created_at", created_at)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> DatasetVersion:
        """Build a dataset version from persisted data and reject loose fields."""

        missing = tuple(field for field in DATASET_VERSION_FIELDS if field not in values)
        if missing:
            msg = "DatasetVersion missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        extra = tuple(field for field in values if field not in DATASET_VERSION_FIELDS)
        if extra:
            msg = "DatasetVersion includes unsupported fields: " + ", ".join(extra)
            raise DataFoundationValidationError(msg)
        return cls(
            dataset_version_id=_require_text(
                values["dataset_version_id"],
                "dataset_version_id",
            ),
            source=_require_text(values["source"], "source"),
            symbol_universe=_normalize_symbol_universe(values["symbol_universe"]),
            bar_size=_require_text(values["bar_size"], "bar_size"),
            what_to_show=_require_text(values["what_to_show"], "what_to_show"),
            start_ts=_parse_aware_datetime(values["start_ts"], "start_ts"),
            end_ts=_parse_aware_datetime(values["end_ts"], "end_ts"),
            contract_universe=_normalize_contract_universe(values["contract_universe"]),
            roll_policy_id=_require_text(values["roll_policy_id"], "roll_policy_id"),
            manifest_hash=_require_text(values["manifest_hash"], "manifest_hash"),
            code_hash=_require_text(values["code_hash"], "code_hash"),
            config_hash=_require_text(values["config_hash"], "config_hash"),
            quality_report_hash=_require_text(
                values["quality_report_hash"],
                "quality_report_hash",
            ),
            created_at=_parse_aware_datetime(values["created_at"], "created_at"),
        )

    @property
    def reproducibility_hashes(self) -> Mapping[str, str]:
        """Return the complete hash set that defines reproducibility."""

        return MappingProxyType(
            {
                "manifest_hash": self.manifest_hash,
                "code_hash": self.code_hash,
                "config_hash": self.config_hash,
                "quality_report_hash": self.quality_report_hash,
            }
        )

    def require_versioned_prerequisites(
        self,
        *,
        quality_report: DataQualityReport | None,
        coverage_report: CoverageReport | None,
        source_manifest: object,
        code_hash: object,
        config_hash: object,
    ) -> DatasetVersion:
        """Require all inputs needed for the QUALITY_CHECKED -> VERSIONED gate."""

        if quality_report is None:
            msg = "linked DataQualityReport is required before dataset versioning"
            raise DataFoundationValidationError(msg)
        if not isinstance(quality_report, DataQualityReport):
            msg = "linked quality_report must be a DataQualityReport"
            raise DataFoundationValidationError(msg)
        if quality_report.dataset_version_id != self.dataset_version_id:
            msg = "DatasetVersion and DataQualityReport dataset_version_id must match"
            raise DataFoundationValidationError(msg)
        if quality_report.blocks_versioning:
            msg = "blocking DataQualityReport prevents dataset versioning"
            raise DataFoundationValidationError(msg)
        if compute_quality_report_hash(quality_report) != self.quality_report_hash:
            msg = "quality_report_hash does not match linked DataQualityReport"
            raise DataFoundationValidationError(msg)

        if coverage_report is None:
            msg = "linked CoverageReport is required before dataset versioning"
            raise DataFoundationValidationError(msg)
        if not isinstance(coverage_report, CoverageReport):
            msg = "linked coverage_report must be a CoverageReport"
            raise DataFoundationValidationError(msg)
        if coverage_report.dataset_version_id != self.dataset_version_id:
            msg = "DatasetVersion and CoverageReport dataset_version_id must match"
            raise DataFoundationValidationError(msg)
        coverage_report.require_linked_quality_report(quality_report)

        if _extract_manifest_hash(source_manifest) != self.manifest_hash:
            msg = "manifest_hash does not match linked source manifest"
            raise DataFoundationValidationError(msg)
        if _normalize_sha256_hash(code_hash, "code_hash") != self.code_hash:
            msg = "code_hash does not match linked code hash"
            raise DataFoundationValidationError(msg)
        if _normalize_sha256_hash(config_hash, "config_hash") != self.config_hash:
            msg = "config_hash does not match linked config hash"
            raise DataFoundationValidationError(msg)
        return self

    def require_lifecycle_prerequisites(
        self,
        lifecycle_state: object,
        *,
        quality_report: DataQualityReport | None,
        coverage_report: CoverageReport | None,
        source_manifest: object,
        code_hash: object,
        config_hash: object,
    ) -> DatasetVersion:
        """Require bound inputs for VERSIONED or READY_FOR_RESEARCH admissibility."""

        state = _require_text(lifecycle_state, "lifecycle_state").upper()
        if state not in DATASET_VERSION_ADMISSIBLE_STATES:
            allowed = ", ".join(sorted(DATASET_VERSION_ADMISSIBLE_STATES))
            msg = f"lifecycle_state must be one of {allowed}"
            raise DataFoundationValidationError(msg)
        return self.require_versioned_prerequisites(
            quality_report=quality_report,
            coverage_report=coverage_report,
            source_manifest=source_manifest,
            code_hash=code_hash,
            config_hash=config_hash,
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable dataset-version mapping."""

        return MappingProxyType(
            {
                "dataset_version_id": self.dataset_version_id,
                "source": self.source,
                "symbol_universe": self.symbol_universe,
                "bar_size": self.bar_size,
                "what_to_show": self.what_to_show,
                "start_ts": self.start_ts.isoformat(),
                "end_ts": self.end_ts.isoformat(),
                "contract_universe": self.contract_universe,
                "roll_policy_id": self.roll_policy_id,
                "manifest_hash": self.manifest_hash,
                "code_hash": self.code_hash,
                "config_hash": self.config_hash,
                "quality_report_hash": self.quality_report_hash,
                "created_at": self.created_at.isoformat(),
            }
        )


DATASET_ACCEPTANCE_LOCK_FIELDS: tuple[str, ...] = (
    "schema",
    "dataset_version_id",
    "state",
    "policy_id",
    "policy_hash",
    "locked_at",
    "coverage_report",
    "blocking_reasons",
    "warning_reasons",
)


@dataclass(frozen=True, slots=True)
class DatasetAcceptanceLock:
    """Persisted DatasetVersion acceptance verdict with value-free coverage evidence.

    The lock is a data-substrate gate only. It does not imply research approval,
    tradability, profitability, live readiness, or production readiness.
    """

    dataset_version_id: str
    state: DatasetAcceptanceState
    policy_id: str
    policy_hash: str
    locked_at: datetime
    coverage_report: Mapping[str, object]
    blocking_reasons: tuple[str, ...]
    warning_reasons: tuple[str, ...]
    schema: str = DATASET_ACCEPTANCE_LOCK_METADATA_SCHEMA

    def __post_init__(self) -> None:
        schema = _require_text(self.schema, "schema")
        if schema != DATASET_ACCEPTANCE_LOCK_METADATA_SCHEMA:
            msg = "DatasetAcceptanceLock schema is unsupported"
            raise DataFoundationValidationError(msg)
        dataset_version_id = _normalize_id(self.dataset_version_id, "dataset_version_id")
        state = _normalize_dataset_acceptance_state(self.state, "state")
        policy_id = _normalize_id(self.policy_id, "policy_id")
        policy_hash = _normalize_sha256_hash(self.policy_hash, "policy_hash")
        locked_at = _parse_aware_datetime(self.locked_at, "locked_at")
        coverage_report = _require_summary_mapping(
            self.coverage_report,
            "coverage_report",
        )
        blocking_reasons = _normalize_reason_tuple(
            self.blocking_reasons,
            "blocking_reasons",
        )
        warning_reasons = _normalize_reason_tuple(
            self.warning_reasons,
            "warning_reasons",
        )

        derived_state = _dataset_acceptance_state_from_reasons(
            blocking_reasons,
            warning_reasons,
        )
        if state is not derived_state:
            msg = f"state must be {derived_state.value} for recorded coverage reasons"
            raise DataFoundationValidationError(msg)

        object.__setattr__(self, "schema", schema)
        object.__setattr__(self, "dataset_version_id", dataset_version_id)
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "policy_id", policy_id)
        object.__setattr__(self, "policy_hash", policy_hash)
        object.__setattr__(self, "locked_at", locked_at)
        object.__setattr__(self, "coverage_report", coverage_report)
        object.__setattr__(self, "blocking_reasons", blocking_reasons)
        object.__setattr__(self, "warning_reasons", warning_reasons)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> DatasetAcceptanceLock:
        """Build an acceptance-lock from persisted registry metadata."""

        _require_exact_mapping_fields(
            values,
            required_fields=DATASET_ACCEPTANCE_LOCK_FIELDS,
            object_name="DatasetAcceptanceLock",
        )
        return cls(
            schema=_require_text(values["schema"], "schema"),
            dataset_version_id=_require_text(
                values["dataset_version_id"],
                "dataset_version_id",
            ),
            state=_normalize_dataset_acceptance_state(values["state"], "state"),
            policy_id=_require_text(values["policy_id"], "policy_id"),
            policy_hash=_require_text(values["policy_hash"], "policy_hash"),
            locked_at=_parse_aware_datetime(values["locked_at"], "locked_at"),
            coverage_report=_require_summary_mapping(
                values["coverage_report"],
                "coverage_report",
            ),
            blocking_reasons=_normalize_reason_tuple(
                values["blocking_reasons"],
                "blocking_reasons",
            ),
            warning_reasons=_normalize_reason_tuple(
                values["warning_reasons"],
                "warning_reasons",
            ),
        )

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable acceptance-lock mapping."""

        return MappingProxyType(
            {
                "schema": self.schema,
                "dataset_version_id": self.dataset_version_id,
                "state": self.state.value,
                "policy_id": self.policy_id,
                "policy_hash": self.policy_hash,
                "locked_at": self.locked_at.isoformat(),
                "coverage_report": self.coverage_report,
                "blocking_reasons": self.blocking_reasons,
                "warning_reasons": self.warning_reasons,
            }
        )


@dataclass(frozen=True, slots=True)
class DatasetAcceptanceInventory:
    """Value-free inventory of acceptance-locks for an expected dataset matrix."""

    policy_id: str
    policy_hash: str
    locks: tuple[DatasetAcceptanceLock, ...]
    missing_expected_versions: tuple[Mapping[str, object], ...]
    duplicate_expected_versions: tuple[Mapping[str, object], ...]

    def __post_init__(self) -> None:
        policy_id = _normalize_id(self.policy_id, "policy_id")
        policy_hash = _normalize_sha256_hash(self.policy_hash, "policy_hash")
        locks = tuple(_require_dataset_acceptance_lock(lock) for lock in self.locks)
        missing_expected_versions = tuple(
            _require_summary_mapping(item, "missing_expected_versions[]")
            for item in self.missing_expected_versions
        )
        duplicate_expected_versions = tuple(
            _require_summary_mapping(item, "duplicate_expected_versions[]")
            for item in self.duplicate_expected_versions
        )
        object.__setattr__(self, "policy_id", policy_id)
        object.__setattr__(self, "policy_hash", policy_hash)
        object.__setattr__(self, "locks", locks)
        object.__setattr__(self, "missing_expected_versions", missing_expected_versions)
        object.__setattr__(
            self,
            "duplicate_expected_versions",
            duplicate_expected_versions,
        )

    @property
    def state_counts(self) -> Mapping[str, int]:
        """Return acceptance-lock counts by state."""

        counts = Counter(lock.state.value for lock in self.locks)
        return MappingProxyType(
            {state: counts.get(state, 0) for state in sorted(DATASET_ACCEPTANCE_STATES)}
        )

    @property
    def complete_expected_matrix(self) -> bool:
        """Return true when each expected schema/year has exactly one version."""

        return not self.missing_expected_versions and not self.duplicate_expected_versions


def _normalize_dataset_acceptance_state(
    value: object,
    field_name: str,
) -> DatasetAcceptanceState:
    if isinstance(value, DatasetAcceptanceState):
        return value
    token = _require_text(value, field_name).upper()
    try:
        return DatasetAcceptanceState[token]
    except KeyError as exc:
        allowed = ", ".join(state.value for state in DatasetAcceptanceState)
        msg = f"{field_name} must be one of {allowed}"
        raise DataFoundationValidationError(msg) from exc


def _dataset_acceptance_state_from_reasons(
    blocking_reasons: tuple[str, ...],
    warning_reasons: tuple[str, ...],
) -> DatasetAcceptanceState:
    if blocking_reasons:
        return DatasetAcceptanceState.BLOCKED
    if warning_reasons:
        return DatasetAcceptanceState.ACCEPTED_WITH_WARNINGS
    return DatasetAcceptanceState.ACCEPTED


def _normalize_reason_tuple(value: object, field_name: str) -> tuple[str, ...]:
    reasons = _normalize_text_collection(value, field_name)
    return tuple(reason for reason in reasons if reason)


def _require_dataset_acceptance_lock(value: object) -> DatasetAcceptanceLock:
    if not isinstance(value, DatasetAcceptanceLock):
        msg = "dataset acceptance inventory requires DatasetAcceptanceLock entries"
        raise DataFoundationValidationError(msg)
    return value


def normalize_dataset_acceptance_policy(
    policy: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    """Normalize value-free acceptance criteria for DatasetVersion locks."""

    raw: Mapping[str, object] = (
        DATASET_ACCEPTANCE_DEFAULT_POLICY if policy is None else policy
    )
    if isinstance(raw, str) or not isinstance(raw, Mapping):
        msg = "dataset acceptance policy must be a mapping"
        raise DataFoundationValidationError(msg)

    policy_id = _normalize_id(
        raw.get("policy_id", DATASET_ACCEPTANCE_DEFAULT_POLICY_ID),
        "policy_id",
    )
    expected_source = _normalize_id(
        raw.get("expected_source", "dsrc_databento_historical"),
        "expected_source",
    )
    expected_symbols = _normalize_symbol_universe(
        raw.get("expected_symbols", ("ES", "NQ", "RTY"))
    )
    expected_years = _normalize_expected_years(
        raw.get("expected_years", tuple(range(2018, 2027)))
    )
    expected_schemas = _normalize_expected_schemas(
        raw.get("expected_schemas", DATASET_ACCEPTANCE_DEFAULT_POLICY["expected_schemas"])
    )
    partial_year_end_ts = _normalize_partial_year_end_ts(
        raw.get("partial_year_end_ts", DATASET_ACCEPTANCE_DEFAULT_POLICY["partial_year_end_ts"])
    )
    required_field_groups = _normalize_text_collection(
        raw.get(
            "required_field_groups",
            DATASET_ACCEPTANCE_REQUIRED_FIELD_GROUPS,
        ),
        "required_field_groups",
    )
    required_registry_metadata_keys = _normalize_text_collection(
        raw.get(
            "required_registry_metadata_keys",
            ("continuous_provenance", "partition_contamination_metadata"),
        ),
        "required_registry_metadata_keys",
    )
    missing_evidence_policy = _normalize_dataset_acceptance_state(
        raw.get("missing_evidence_policy", DatasetAcceptanceState.BLOCKED.value),
        "missing_evidence_policy",
    )
    if missing_evidence_policy is DatasetAcceptanceState.ACCEPTED:
        msg = "missing_evidence_policy cannot be ACCEPTED"
        raise DataFoundationValidationError(msg)

    return MappingProxyType(
        {
            "policy_id": policy_id,
            "expected_source": expected_source,
            "expected_symbols": expected_symbols,
            "expected_years": expected_years,
            "expected_schemas": expected_schemas,
            "partial_year_end_ts": partial_year_end_ts,
            "required_field_groups": required_field_groups,
            "required_registry_metadata_keys": required_registry_metadata_keys,
            "row_count_evidence_required": _require_bool(
                raw.get("row_count_evidence_required", True),
                "row_count_evidence_required",
            ),
            "gap_evidence_required": _require_bool(
                raw.get("gap_evidence_required", True),
                "gap_evidence_required",
            ),
            "required_field_evidence_required": _require_bool(
                raw.get("required_field_evidence_required", True),
                "required_field_evidence_required",
            ),
            "missingness_quality_evidence_required": _require_bool(
                raw.get("missingness_quality_evidence_required", True),
                "missingness_quality_evidence_required",
            ),
            "continuous_provenance_required": _require_bool(
                raw.get("continuous_provenance_required", True),
                "continuous_provenance_required",
            ),
            "roll_metadata_required": _require_bool(
                raw.get("roll_metadata_required", True),
                "roll_metadata_required",
            ),
            "missing_evidence_policy": missing_evidence_policy.value,
        }
    )


def compute_dataset_acceptance_policy_hash(policy: Mapping[str, object]) -> str:
    """Return the deterministic hash for normalized acceptance criteria."""

    return hash_config(normalize_dataset_acceptance_policy(policy))


def build_dataset_acceptance_lock(
    dataset_version: DatasetVersion,
    *,
    policy: Mapping[str, object] | None = None,
    coverage_evidence: Mapping[str, object] | None = None,
    schema_id: object | None = None,
    year: object | None = None,
    duplicate_count: object = 1,
    locked_at: object | None = None,
) -> DatasetAcceptanceLock:
    """Build one acceptance-lock from DatasetVersion metadata and coverage evidence."""

    if not isinstance(dataset_version, DatasetVersion):
        msg = "dataset acceptance requires a DatasetVersion"
        raise DataFoundationValidationError(msg)
    normalized_policy = normalize_dataset_acceptance_policy(policy)
    policy_hash = compute_dataset_acceptance_policy_hash(normalized_policy)
    resolved_schema_id = (
        _require_text(schema_id, "schema_id")
        if schema_id is not None
        else _schema_id_for_dataset_version(dataset_version, normalized_policy)
    )
    resolved_year = (
        _require_positive_int(year, "year")
        if year is not None
        else dataset_version.start_ts.year
    )
    duplicates = _require_positive_int(duplicate_count, "duplicate_count")
    evidence = _normalize_acceptance_evidence(coverage_evidence)
    locked_timestamp = (
        datetime.now().astimezone()
        if locked_at is None
        else _parse_aware_datetime(locked_at, "locked_at")
    )

    report, blocking_reasons, warning_reasons = _build_acceptance_coverage_report(
        dataset_version,
        policy=normalized_policy,
        coverage_evidence=evidence,
        schema_id=resolved_schema_id,
        year=resolved_year,
        duplicate_count=duplicates,
    )
    state = _dataset_acceptance_state_from_reasons(
        blocking_reasons,
        warning_reasons,
    )
    return DatasetAcceptanceLock(
        dataset_version_id=dataset_version.dataset_version_id,
        state=state,
        policy_id=str(normalized_policy["policy_id"]),
        policy_hash=policy_hash,
        locked_at=locked_timestamp,
        coverage_report=report,
        blocking_reasons=blocking_reasons,
        warning_reasons=warning_reasons,
    )


def inventory_dataset_acceptance_locks(
    registry_path: str | Path,
    *,
    policy: Mapping[str, object] | None = None,
    locked_at: object | None = None,
) -> DatasetAcceptanceInventory:
    """Inventory in-scope DatasetVersions through the registry and build locks.

    This function resolves exact DatasetVersion ids through
    ``resolve_dataset_version``. It does not read raw provider files or
    materialized value paths.
    """

    normalized_policy = normalize_dataset_acceptance_policy(policy)
    policy_hash = compute_dataset_acceptance_policy_hash(normalized_policy)
    resolved = _ensure_acceptance_registry_ready(registry_path, write=False)
    dataset_ids = _registered_dataset_version_ids(resolved)
    artifacts = _dataset_acceptance_artifact_metadata(resolved)
    records: list[tuple[DatasetVersion, str, int, Mapping[str, object]]] = []

    for dataset_id in dataset_ids:
        version = _resolve_dataset_version_exact(resolved, dataset_id)
        if version is None:
            continue
        schema_id = _schema_id_for_dataset_version(version, normalized_policy)
        if schema_id is None:
            continue
        if version.source != normalized_policy["expected_source"]:
            continue
        year = version.start_ts.year
        if year not in normalized_policy["expected_years"]:
            continue
        records.append((version, schema_id, year, artifacts.get(dataset_id, {})))

    counts = Counter((schema_id, year) for _, schema_id, year, _ in records)
    locks = tuple(
        build_dataset_acceptance_lock(
            version,
            policy=normalized_policy,
            coverage_evidence=_coverage_evidence_from_registry_metadata(
                version,
                metadata,
            ),
            schema_id=schema_id,
            year=year,
            duplicate_count=counts[(schema_id, year)],
            locked_at=locked_at,
        )
        for version, schema_id, year, metadata in records
    )
    missing_expected_versions = _missing_expected_acceptance_versions(
        normalized_policy,
        counts,
    )
    duplicate_expected_versions = _duplicate_expected_acceptance_versions(counts)
    return DatasetAcceptanceInventory(
        policy_id=str(normalized_policy["policy_id"]),
        policy_hash=policy_hash,
        locks=locks,
        missing_expected_versions=missing_expected_versions,
        duplicate_expected_versions=duplicate_expected_versions,
    )


def persist_dataset_acceptance_locks(
    registry_path: str | Path,
    inventory: DatasetAcceptanceInventory,
) -> None:
    """Persist acceptance-locks into the local registry for exact DatasetVersion ids."""

    if not isinstance(inventory, DatasetAcceptanceInventory):
        msg = "persist_dataset_acceptance_locks requires a DatasetAcceptanceInventory"
        raise DataFoundationValidationError(msg)
    resolved = _ensure_acceptance_registry_ready(registry_path, write=True)
    with connect_registry(resolved) as connection:
        for lock in inventory.locks:
            _persist_dataset_acceptance_lock(connection, resolved, lock)


def resolve_dataset_acceptance_lock(
    registry_path: str | Path,
    dataset_version_id: object,
) -> DatasetAcceptanceLock | None:
    """Resolve a persisted acceptance-lock by exact DatasetVersion id."""

    dataset_id = _normalize_id(dataset_version_id, "dataset_version_id")
    resolved = _ensure_acceptance_registry_ready(registry_path, write=False)
    with connect_registry(resolved, read_only=True) as connection:
        row = connection.execute(
            """
            SELECT metadata_json
            FROM dataset_versions
            WHERE data_version = ?
            """,
            (dataset_id,),
        ).fetchone()
    if row is None:
        return None
    payload = _load_registry_metadata_json(str(row["metadata_json"]))
    lock_payload = payload.get("dataset_acceptance_lock")
    if lock_payload is None:
        return None
    if isinstance(lock_payload, str) or not isinstance(lock_payload, Mapping):
        msg = "dataset_acceptance_lock metadata must be a mapping"
        raise DataFoundationValidationError(msg)
    return DatasetAcceptanceLock.from_mapping(lock_payload)


def render_dataset_acceptance_summary(
    inventory: DatasetAcceptanceInventory,
    *,
    persisted: bool = False,
) -> str:
    """Render a value-free markdown summary for review and handoff."""

    if not isinstance(inventory, DatasetAcceptanceInventory):
        msg = "render_dataset_acceptance_summary requires a DatasetAcceptanceInventory"
        raise DataFoundationValidationError(msg)
    lines = [
        "# DatasetVersion Acceptance Summary",
        "",
        "This value-free summary records DatasetVersion acceptance-lock states only.",
        "It contains no raw rows, canonical values, feature values, label values,",
        "provider responses, SQLite content, or roll-calendar data.",
        "",
        f"- Policy: `{inventory.policy_id}`",
        f"- Policy hash: `{inventory.policy_hash}`",
        f"- DatasetVersion locks in inventory: `{len(inventory.locks)}`",
        f"- Expected matrix complete: `{'yes' if inventory.complete_expected_matrix else 'no'}`",
        "",
        "## State Counts",
        "",
        "| State | Count |",
        "| --- | ---: |",
    ]
    for state, count in inventory.state_counts.items():
        lines.append(f"| `{state}` | {count} |")
    lines.extend(
        [
            "",
            "## Per-Version Locks",
            "",
            "| Schema | Year | DatasetVersion | State | Blocking Reasons | Warnings |",
            "| --- | ---: | --- | --- | ---: | ---: |",
        ]
    )
    for lock in sorted(
        inventory.locks,
        key=lambda item: (
            str(item.coverage_report.get("schema_id", "")),
            int(item.coverage_report.get("year", 0)),
            item.dataset_version_id,
        ),
    ):
        schema_id = str(lock.coverage_report.get("schema_id", "unknown"))
        year = int(lock.coverage_report.get("year", 0))
        lines.append(
            "| `{schema}` | {year} | `{dataset}` | `{state}` | {blocking} | {warnings} |".format(
                schema=schema_id,
                year=year,
                dataset=lock.dataset_version_id,
                state=lock.state.value,
                blocking=len(lock.blocking_reasons),
                warnings=len(lock.warning_reasons),
            )
        )

    lines.extend(["", "## Expected Matrix Gaps", ""])
    if not inventory.missing_expected_versions and not inventory.duplicate_expected_versions:
        lines.append("No missing or duplicate expected schema/year slots were found.")
    else:
        if inventory.missing_expected_versions:
            lines.append("Missing expected slots:")
            for item in inventory.missing_expected_versions:
                lines.append(f"- `{item['schema_id']}` `{item['year']}`")
        if inventory.duplicate_expected_versions:
            lines.append("Duplicate expected slots:")
            for item in inventory.duplicate_expected_versions:
                lines.append(
                    f"- `{item['schema_id']}` `{item['year']}` count `{item['count']}`"
                )
    lines.extend(["", "## Locality", ""])
    if persisted:
        lines.extend(
            [
                "Acceptance verdicts and coverage reports were persisted in the local",
                "DatasetVersion registry. This committed summary is metadata-only",
                "and does not include per-row values.",
            ]
        )
    else:
        lines.extend(
            [
                "This summary was generated from a read-only registry inventory.",
                "It does not assert that acceptance-lock persistence succeeded in",
                "the local DatasetVersion registry.",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _normalize_expected_years(value: object) -> tuple[int, ...]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        msg = "expected_years must be an explicit collection of years"
        raise DataFoundationValidationError(msg)
    years = tuple(_require_positive_int(year, "expected_years") for year in value)
    if not years:
        msg = "expected_years must not be empty"
        raise DataFoundationValidationError(msg)
    duplicates = tuple(sorted({year for year in years if years.count(year) > 1}))
    if duplicates:
        msg = "expected_years must not contain duplicate values: "
        raise DataFoundationValidationError(msg + ", ".join(str(year) for year in duplicates))
    return tuple(sorted(years))


def _normalize_expected_schemas(value: object) -> Mapping[str, Mapping[str, str]]:
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "expected_schemas must be a mapping"
        raise DataFoundationValidationError(msg)
    schemas: dict[str, Mapping[str, str]] = {}
    for raw_schema_id, raw_config in value.items():
        schema_id = _normalize_id(raw_schema_id, "expected_schemas.schema_id")
        if isinstance(raw_config, str) or not isinstance(raw_config, Mapping):
            msg = "expected_schemas entries must be mappings"
            raise DataFoundationValidationError(msg)
        bar_size = _require_text(raw_config.get("bar_size"), f"{schema_id}.bar_size")
        what_to_show = _require_text(
            raw_config.get("what_to_show"),
            f"{schema_id}.what_to_show",
        ).upper()
        schemas[schema_id] = MappingProxyType(
            {"bar_size": bar_size, "what_to_show": what_to_show}
        )
    if not schemas:
        msg = "expected_schemas must not be empty"
        raise DataFoundationValidationError(msg)
    return MappingProxyType(schemas)


def _normalize_partial_year_end_ts(value: object) -> Mapping[str, str]:
    if value is None:
        return MappingProxyType({})
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "partial_year_end_ts must be a mapping"
        raise DataFoundationValidationError(msg)
    parsed: dict[str, str] = {}
    for raw_year, raw_ts in value.items():
        year = _require_positive_int(int(raw_year), "partial_year_end_ts.year")
        ts = _parse_aware_datetime(raw_ts, "partial_year_end_ts.value")
        parsed[str(year)] = ts.isoformat()
    return MappingProxyType(parsed)


def _schema_id_for_dataset_version(
    dataset_version: DatasetVersion,
    policy: Mapping[str, object],
) -> str | None:
    schemas = policy["expected_schemas"]
    if isinstance(schemas, str) or not isinstance(schemas, Mapping):
        msg = "normalized policy carries invalid expected_schemas"
        raise DataFoundationValidationError(msg)
    for schema_id, config in schemas.items():
        if isinstance(config, str) or not isinstance(config, Mapping):
            msg = "normalized schema config must be a mapping"
            raise DataFoundationValidationError(msg)
        if (
            dataset_version.bar_size == config["bar_size"]
            and dataset_version.what_to_show == config["what_to_show"]
        ):
            return str(schema_id)
    return None


def _normalize_acceptance_evidence(
    value: Mapping[str, object] | None,
) -> Mapping[str, object]:
    if value is None:
        return MappingProxyType({})
    if isinstance(value, str) or not isinstance(value, Mapping):
        msg = "coverage_evidence must be a mapping"
        raise DataFoundationValidationError(msg)
    return _require_summary_mapping(value, "coverage_evidence")


def _build_acceptance_coverage_report(
    dataset_version: DatasetVersion,
    *,
    policy: Mapping[str, object],
    coverage_evidence: Mapping[str, object],
    schema_id: str | None,
    year: int,
    duplicate_count: int,
) -> tuple[Mapping[str, object], tuple[str, ...], tuple[str, ...]]:
    blocking_reasons: list[str] = []
    warning_reasons: list[str] = []

    schema_dimension = _schema_dimension(
        dataset_version,
        policy,
        schema_id,
        blocking_reasons,
    )
    symbol_dimension = _symbol_dimension(dataset_version, policy, blocking_reasons)
    year_dimension = _year_dimension(dataset_version, policy, year, blocking_reasons)
    duplicate_dimension = _duplicate_dimension(duplicate_count, blocking_reasons)
    row_count_dimension = _evidence_dimension(
        coverage_evidence,
        "row_count_sanity",
        required=bool(policy["row_count_evidence_required"]),
        missing_reason="row-count / expected-bar sanity evidence unavailable",
        blocking_reasons=blocking_reasons,
        warning_reasons=warning_reasons,
    )
    gap_dimension = _evidence_dimension(
        coverage_evidence,
        "gap_coverage",
        required=bool(policy["gap_evidence_required"]),
        missing_reason="gap coverage evidence unavailable",
        blocking_reasons=blocking_reasons,
        warning_reasons=warning_reasons,
    )
    required_field_dimension = _required_field_dimension(
        coverage_evidence,
        policy,
        blocking_reasons,
        warning_reasons,
    )
    missingness_dimension = _evidence_dimension(
        coverage_evidence,
        "missingness_quality_flags",
        required=bool(policy["missingness_quality_evidence_required"]),
        missing_reason="missingness and quality-flag evidence unavailable",
        blocking_reasons=blocking_reasons,
        warning_reasons=warning_reasons,
    )
    provenance_dimension = _continuous_provenance_dimension(
        dataset_version,
        coverage_evidence,
        policy,
        blocking_reasons,
        warning_reasons,
    )
    roll_dimension = _roll_metadata_dimension(
        dataset_version,
        coverage_evidence,
        policy,
        blocking_reasons,
        warning_reasons,
    )
    registry_dimension = MappingProxyType(
        {
            "status": ReportStatus.PASSING.value,
            "resolved_by": "resolve_dataset_version",
            "exact_id": True,
            "fuzzy_fallback": False,
            "duplicate_schema_year_count": duplicate_count,
            "duplicate_status": duplicate_dimension["status"],
        }
    )

    report = _require_summary_mapping(
        {
            "dataset_version_id": dataset_version.dataset_version_id,
            "schema_id": schema_id or "unmatched",
            "year": year,
            "source": dataset_version.source,
            "coverage_dimensions": DATASET_ACCEPTANCE_COVERAGE_DIMENSIONS,
            "schema": schema_dimension,
            "symbol": symbol_dimension,
            "year_date_range": year_dimension,
            "row_count_sanity": row_count_dimension,
            "gap_coverage": gap_dimension,
            "required_field_presence": required_field_dimension,
            "missingness_quality_flags": missingness_dimension,
            "continuous_provenance": provenance_dimension,
            "roll_metadata": roll_dimension,
            "registry_resolution": registry_dimension,
            "coverage_evidence_source": coverage_evidence.get(
                "evidence_source",
                "registry_metadata_only",
            ),
        },
        "coverage_report",
    )
    return report, tuple(blocking_reasons), tuple(warning_reasons)


def _schema_dimension(
    dataset_version: DatasetVersion,
    policy: Mapping[str, object],
    schema_id: str | None,
    blocking_reasons: list[str],
) -> Mapping[str, object]:
    if schema_id is None:
        blocking_reasons.append("schema not present in acceptance policy")
        return MappingProxyType(
            {
                "status": ReportStatus.BLOCKING.value,
                "present": False,
                "bar_size": dataset_version.bar_size,
                "what_to_show": dataset_version.what_to_show,
            }
        )
    if dataset_version.source != policy["expected_source"]:
        blocking_reasons.append("dataset source is outside acceptance policy")
        status = ReportStatus.BLOCKING.value
    else:
        status = ReportStatus.PASSING.value
    return MappingProxyType(
        {
            "status": status,
            "present": status == ReportStatus.PASSING.value,
            "schema_id": schema_id,
            "bar_size": dataset_version.bar_size,
            "what_to_show": dataset_version.what_to_show,
        }
    )


def _symbol_dimension(
    dataset_version: DatasetVersion,
    policy: Mapping[str, object],
    blocking_reasons: list[str],
) -> Mapping[str, object]:
    expected = tuple(str(symbol) for symbol in policy["expected_symbols"])
    observed = dataset_version.symbol_universe
    missing = tuple(symbol for symbol in expected if symbol not in observed)
    extra = tuple(symbol for symbol in observed if symbol not in expected)
    status = ReportStatus.PASSING
    if missing:
        blocking_reasons.append("required symbol coverage missing")
        status = ReportStatus.BLOCKING
    elif extra:
        status = ReportStatus.WARNING
    return MappingProxyType(
        {
            "status": status.value,
            "expected_symbols": expected,
            "observed_symbols": observed,
            "missing_symbols": missing,
            "extra_symbols": extra,
        }
    )


def _year_dimension(
    dataset_version: DatasetVersion,
    policy: Mapping[str, object],
    year: int,
    blocking_reasons: list[str],
) -> Mapping[str, object]:
    expected_years = tuple(int(item) for item in policy["expected_years"])
    partial_years = policy["partial_year_end_ts"]
    if isinstance(partial_years, str) or not isinstance(partial_years, Mapping):
        msg = "normalized policy carries invalid partial_year_end_ts"
        raise DataFoundationValidationError(msg)
    expected_start = datetime.fromisoformat(f"{year}-01-01T00:00:00+00:00")
    expected_end = (
        _parse_aware_datetime(partial_years[str(year)], "partial_year_end_ts")
        if str(year) in partial_years
        else datetime.fromisoformat(f"{year + 1}-01-01T00:00:00+00:00")
    )
    covered = (
        year in expected_years
        and dataset_version.start_ts == expected_start
        and dataset_version.end_ts >= expected_end
    )
    if not covered:
        blocking_reasons.append("required year/date-range coverage missing")
    return MappingProxyType(
        {
            "status": ReportStatus.PASSING.value if covered else ReportStatus.BLOCKING.value,
            "expected_year": year,
            "observed_start_ts": dataset_version.start_ts.isoformat(),
            "observed_end_ts": dataset_version.end_ts.isoformat(),
            "expected_start_ts": expected_start.isoformat(),
            "minimum_end_ts": expected_end.isoformat(),
            "covered": covered,
        }
    )


def _duplicate_dimension(
    duplicate_count: int,
    blocking_reasons: list[str],
) -> Mapping[str, object]:
    if duplicate_count != 1:
        blocking_reasons.append("schema/year registry slot is not unique")
        status = ReportStatus.BLOCKING
    else:
        status = ReportStatus.PASSING
    return MappingProxyType({"status": status.value, "count": duplicate_count})


def _evidence_dimension(
    evidence: Mapping[str, object],
    key: str,
    *,
    required: bool,
    missing_reason: str,
    blocking_reasons: list[str],
    warning_reasons: list[str],
) -> Mapping[str, object]:
    raw = evidence.get(key)
    if raw is None:
        status = ReportStatus.BLOCKING if required else ReportStatus.WARNING
        reason = missing_reason
        if required:
            blocking_reasons.append(reason)
        else:
            warning_reasons.append(reason)
        return MappingProxyType(
            {"status": status.value, "evidence": "unavailable", "reason": reason}
        )
    if isinstance(raw, str) or not isinstance(raw, Mapping):
        msg = f"{key} evidence must be a mapping"
        raise DataFoundationValidationError(msg)
    dimension = dict(_require_summary_mapping(raw, key))
    status = _normalize_status(dimension.get("status", ReportStatus.PASSING), f"{key}.status")
    dimension["status"] = status.value
    if status is ReportStatus.BLOCKING:
        blocking_reasons.append(str(dimension.get("reason", f"{key} is blocking")))
    elif status is ReportStatus.WARNING:
        warning_reasons.append(str(dimension.get("reason", f"{key} has warnings")))
    return MappingProxyType(dimension)


def _required_field_dimension(
    evidence: Mapping[str, object],
    policy: Mapping[str, object],
    blocking_reasons: list[str],
    warning_reasons: list[str],
) -> Mapping[str, object]:
    raw = evidence.get("required_field_presence")
    required_fields = tuple(str(item) for item in policy["required_field_groups"])
    if raw is None:
        if bool(policy["required_field_evidence_required"]):
            blocking_reasons.append("required-field presence evidence unavailable")
            status = ReportStatus.BLOCKING
        else:
            warning_reasons.append("required-field presence evidence unavailable")
            status = ReportStatus.WARNING
        return MappingProxyType(
            {
                "status": status.value,
                "required_field_groups": required_fields,
                "present_field_groups": (),
                "missing_field_groups": required_fields,
                "evidence": "unavailable",
            }
        )
    if isinstance(raw, str) or not isinstance(raw, Mapping):
        msg = "required_field_presence evidence must be a mapping"
        raise DataFoundationValidationError(msg)
    dimension = dict(_require_summary_mapping(raw, "required_field_presence"))
    present = tuple(str(item) for item in dimension.get("present_field_groups", ()))
    missing = tuple(field for field in required_fields if field not in present)
    explicit_missing = tuple(str(item) for item in dimension.get("missing_field_groups", ()))
    missing = tuple(sorted(set(missing + explicit_missing)))
    status = _normalize_status(
        dimension.get("status", ReportStatus.PASSING if not missing else ReportStatus.BLOCKING),
        "required_field_presence.status",
    )
    if missing and status is ReportStatus.PASSING:
        status = ReportStatus.BLOCKING
    if status is ReportStatus.BLOCKING:
        blocking_reasons.append("required field groups missing")
    elif status is ReportStatus.WARNING:
        warning_reasons.append("required field groups have warnings")
    dimension.update(
        {
            "status": status.value,
            "required_field_groups": required_fields,
            "present_field_groups": present,
            "missing_field_groups": missing,
        }
    )
    return MappingProxyType(dimension)


def _continuous_provenance_dimension(
    dataset_version: DatasetVersion,
    evidence: Mapping[str, object],
    policy: Mapping[str, object],
    blocking_reasons: list[str],
    warning_reasons: list[str],
) -> Mapping[str, object]:
    raw = evidence.get("continuous_provenance")
    if raw is None:
        if bool(policy["continuous_provenance_required"]):
            blocking_reasons.append("continuous-series provenance evidence unavailable")
            status = ReportStatus.BLOCKING
        else:
            warning_reasons.append("continuous-series provenance evidence unavailable")
            status = ReportStatus.WARNING
        return MappingProxyType(
            {
                "status": status.value,
                "evidence": "unavailable",
                "expected_series": _expected_continuous_series(dataset_version),
            }
        )
    if isinstance(raw, str) or not isinstance(raw, Mapping):
        msg = "continuous_provenance evidence must be a mapping"
        raise DataFoundationValidationError(msg)
    dimension = dict(_require_summary_mapping(raw, "continuous_provenance"))
    status = _normalize_status(
        dimension.get("status", ReportStatus.PASSING),
        "continuous_provenance.status",
    )
    if status is ReportStatus.BLOCKING:
        blocking_reasons.append("continuous-series provenance is blocking")
    elif status is ReportStatus.WARNING:
        warning_reasons.append("continuous-series provenance has warnings")
    dimension.setdefault("expected_series", _expected_continuous_series(dataset_version))
    dimension["status"] = status.value
    return MappingProxyType(dimension)


def _roll_metadata_dimension(
    dataset_version: DatasetVersion,
    evidence: Mapping[str, object],
    policy: Mapping[str, object],
    blocking_reasons: list[str],
    warning_reasons: list[str],
) -> Mapping[str, object]:
    raw = evidence.get("roll_metadata")
    if raw is None:
        if bool(policy["roll_metadata_required"]):
            blocking_reasons.append("roll / approximate roll-boundary metadata unavailable")
            status = ReportStatus.BLOCKING
        else:
            warning_reasons.append("roll / approximate roll-boundary metadata unavailable")
            status = ReportStatus.WARNING
        return MappingProxyType(
            {
                "status": status.value,
                "roll_policy_id": dataset_version.roll_policy_id,
                "roll_boundary_evidence": "unavailable",
            }
        )
    if isinstance(raw, str) or not isinstance(raw, Mapping):
        msg = "roll_metadata evidence must be a mapping"
        raise DataFoundationValidationError(msg)
    dimension = dict(_require_summary_mapping(raw, "roll_metadata"))
    status = _normalize_status(
        dimension.get("status", ReportStatus.PASSING),
        "roll_metadata.status",
    )
    if status is ReportStatus.BLOCKING:
        blocking_reasons.append("roll metadata is blocking")
    elif status is ReportStatus.WARNING:
        warning_reasons.append("roll metadata has warnings")
    dimension.setdefault("roll_policy_id", dataset_version.roll_policy_id)
    dimension["status"] = status.value
    return MappingProxyType(dimension)


def _expected_continuous_series(dataset_version: DatasetVersion) -> tuple[str, ...]:
    return tuple(f"{symbol}.v.0" for symbol in dataset_version.symbol_universe)


def _coverage_evidence_from_registry_metadata(
    dataset_version: DatasetVersion,
    metadata: Mapping[str, object],
) -> Mapping[str, object]:
    evidence: dict[str, object] = {"evidence_source": "dataset_registry_metadata"}
    provenance = metadata.get("continuous_provenance")
    if isinstance(provenance, Mapping):
        evidence["continuous_provenance"] = {
            "status": ReportStatus.PASSING.value,
            "provider_continuous": provenance.get("provider_continuous"),
            "front_month": provenance.get("front_month"),
            "unadjusted": provenance.get("unadjusted"),
            "not_roll_truth": provenance.get("not_roll_truth"),
            "series_ids": _expected_continuous_series(dataset_version),
        }
    # The local registry currently carries roll_policy_id but not roll-boundary
    # records or row-count/gap/field-presence aggregates; those dimensions stay
    # absent so the acceptance verdict fails closed instead of silently accepting.
    return _require_summary_mapping(evidence, "coverage_evidence")


def _ensure_acceptance_registry_ready(
    registry_path: str | Path,
    *,
    write: bool,
) -> Path:
    resolved = resolve_registry_path(registry_path)
    if not is_local_only_registry_path(resolved):
        msg = "dataset acceptance registry path is not local-only"
        raise DataFoundationValidationError(msg)
    if write:
        status = init_registry(resolved)
    else:
        status = _inspect_existing_acceptance_registry(resolved)
    if not status.valid:
        msg = "dataset acceptance registry is not ready: " + status.status_message
        raise DataFoundationValidationError(msg)
    return resolved


def _inspect_existing_acceptance_registry(path: Path):
    from alpha_system.core.registry import inspect_registry_status

    return inspect_registry_status(path)


def _registered_dataset_version_ids(registry_path: Path) -> tuple[str, ...]:
    with connect_registry(registry_path, read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT data_version
            FROM dataset_versions
            ORDER BY data_version
            """
        ).fetchall()
    return tuple(str(row["data_version"]) for row in rows)


def _resolve_dataset_version_exact(
    registry_path: Path,
    dataset_version_id: str,
) -> DatasetVersion | None:
    from alpha_system.data.foundation.version_registry import resolve_dataset_version

    return resolve_dataset_version(registry_path, dataset_version_id)


def _dataset_acceptance_artifact_metadata(
    registry_path: Path,
) -> Mapping[str, Mapping[str, object]]:
    with connect_registry(registry_path, read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT run_id, metadata_json
            FROM artifact_manifest
            WHERE run_table = 'dataset_versions'
              AND artifact_key = 'databento_dataset_metadata'
            ORDER BY run_id
            """
        ).fetchall()
    artifacts: dict[str, Mapping[str, object]] = {}
    for row in rows:
        payload = _load_registry_metadata_json(str(row["metadata_json"]))
        artifacts[str(row["run_id"])] = _require_summary_mapping(
            payload,
            "artifact_manifest.metadata_json",
        )
    return MappingProxyType(artifacts)


def _load_registry_metadata_json(value: str) -> dict[str, object]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        msg = "registry metadata_json is not valid JSON"
        raise DataFoundationValidationError(msg) from exc
    if isinstance(payload, str) or not isinstance(payload, Mapping):
        msg = "registry metadata_json must be a mapping"
        raise DataFoundationValidationError(msg)
    return dict(payload)


def _missing_expected_acceptance_versions(
    policy: Mapping[str, object],
    counts: Counter[tuple[str, int]],
) -> tuple[Mapping[str, object], ...]:
    schemas = tuple(str(schema_id) for schema_id in policy["expected_schemas"])
    years = tuple(int(year) for year in policy["expected_years"])
    missing = []
    for schema_id in schemas:
        for year in years:
            if counts.get((schema_id, year), 0) == 0:
                missing.append(
                    MappingProxyType(
                        {
                            "schema_id": schema_id,
                            "year": year,
                            "status": ReportStatus.BLOCKING.value,
                        }
                    )
                )
    return tuple(missing)


def _duplicate_expected_acceptance_versions(
    counts: Counter[tuple[str, int]],
) -> tuple[Mapping[str, object], ...]:
    duplicates = []
    for (schema_id, year), count in sorted(counts.items()):
        if count > 1:
            duplicates.append(
                MappingProxyType(
                    {
                        "schema_id": schema_id,
                        "year": year,
                        "count": count,
                        "status": ReportStatus.BLOCKING.value,
                    }
                )
            )
    return tuple(duplicates)


def _persist_dataset_acceptance_lock(
    connection: sqlite3.Connection,
    registry_path: Path,
    lock: DatasetAcceptanceLock,
) -> None:
    row = connection.execute(
        """
        SELECT metadata_json
        FROM dataset_versions
        WHERE data_version = ?
        """,
        (lock.dataset_version_id,),
    ).fetchone()
    if row is None:
        msg = f"DatasetVersion not found for acceptance lock: {lock.dataset_version_id}"
        raise DataFoundationValidationError(msg)
    payload = _load_registry_metadata_json(str(row["metadata_json"]))
    payload["dataset_acceptance_lock"] = lock.to_mapping()
    payload["dataset_acceptance_lock_schema"] = DATASET_ACCEPTANCE_LOCK_METADATA_SCHEMA
    metadata_json = canonical_json(payload)
    lock_hash = hash_config(lock.to_mapping())
    try:
        connection.execute(
            """
            UPDATE dataset_versions
            SET metadata_json = ?,
                status_message = ?
            WHERE data_version = ?
            """,
            (
                metadata_json,
                f"FUTSUB-P02 dataset acceptance lock: {lock.state.value}",
                lock.dataset_version_id,
            ),
        )
        connection.execute(
            """
            INSERT OR REPLACE INTO artifact_manifest (
                artifact_id,
                run_id,
                run_table,
                artifact_key,
                artifact_path,
                content_hash,
                artifact_role,
                created_at,
                metadata_json,
                status_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"art_dataset_acceptance_lock_{lock.dataset_version_id}",
                lock.dataset_version_id,
                "dataset_versions",
                "dataset_acceptance_lock",
                registry_path.as_posix(),
                lock_hash,
                "dataset_acceptance_lock",
                lock.locked_at.isoformat(),
                canonical_json(lock.to_mapping()),
                "FUTSUB-P02 DatasetVersion acceptance-lock",
            ),
        )
    except sqlite3.Error as exc:
        msg = (
            "could not persist DatasetVersion acceptance lock: "
            f"{lock.dataset_version_id}: {exc}"
        )
        raise DataFoundationValidationError(msg) from exc


@dataclass(frozen=True, slots=True)
class DatasetPartitionPlan:
    """Dataset partition plan and locked-test metadata rules.

    The plan is a data-admissibility descriptor only. It does not imply
    research approval, alpha value, tradability, production readiness, or
    permitted locked-partition use without Governance contamination metadata.
    """

    plan_id: str
    development_partition: Mapping[str, object]
    validation_partition: Mapping[str, object]
    locked_test_candidate: Mapping[str, object]
    latest_shadow_candidate: Mapping[str, object] | None
    contamination_metadata_rules: Mapping[str, object]

    def __post_init__(self) -> None:
        plan_id = _normalize_id(self.plan_id, "plan_id")
        development_partition = _normalize_fixed_partition(
            self.development_partition,
            field_name="development_partition",
            expected_partition_id="development_partition",
            expected_start=CANONICAL_DEVELOPMENT_START,
            expected_end=CANONICAL_DEVELOPMENT_END,
        )
        validation_partition = _normalize_fixed_partition(
            self.validation_partition,
            field_name="validation_partition",
            expected_partition_id="validation_partition",
            expected_start=CANONICAL_VALIDATION_START,
            expected_end=CANONICAL_VALIDATION_END,
        )
        locked_test_candidate = _normalize_fixed_partition(
            self.locked_test_candidate,
            field_name="locked_test_candidate",
            expected_partition_id="locked_test_candidate",
            expected_start=CANONICAL_LOCKED_TEST_START,
            expected_end=CANONICAL_LOCKED_TEST_END,
        )
        latest_shadow_candidate = _normalize_latest_shadow_partition(
            self.latest_shadow_candidate,
        )
        contamination_metadata_rules = _normalize_contamination_metadata_rules(
            self.contamination_metadata_rules,
        )
        _validate_canonical_partition_order(
            development_partition,
            validation_partition,
            locked_test_candidate,
        )

        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "development_partition", development_partition)
        object.__setattr__(self, "validation_partition", validation_partition)
        object.__setattr__(self, "locked_test_candidate", locked_test_candidate)
        object.__setattr__(self, "latest_shadow_candidate", latest_shadow_candidate)
        object.__setattr__(
            self,
            "contamination_metadata_rules",
            contamination_metadata_rules,
        )

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> DatasetPartitionPlan:
        """Build a partition plan from structured data and reject loose fields."""

        missing = tuple(
            field for field in REQUIRED_DATASET_PARTITION_PLAN_FIELDS if field not in values
        )
        if missing:
            msg = "DatasetPartitionPlan missing required fields: " + ", ".join(missing)
            raise DataFoundationValidationError(msg)
        extra = tuple(
            field for field in values if field not in REQUIRED_DATASET_PARTITION_PLAN_FIELDS
        )
        if extra:
            msg = "DatasetPartitionPlan includes unsupported fields: " + ", ".join(extra)
            raise DataFoundationValidationError(msg)
        return cls(
            plan_id=_require_text(values["plan_id"], "plan_id"),
            development_partition=values["development_partition"],
            validation_partition=values["validation_partition"],
            locked_test_candidate=values["locked_test_candidate"],
            latest_shadow_candidate=values["latest_shadow_candidate"],
            contamination_metadata_rules=values["contamination_metadata_rules"],
        )

    @classmethod
    def canonical(
        cls,
        *,
        plan_id: object = "dataset_partition_plan_v1",
        latest_shadow_candidate: Mapping[str, object] | None = None,
    ) -> DatasetPartitionPlan:
        """Return the campaign-canonical DATA-P18 partition descriptor."""

        return cls(
            plan_id=_require_text(plan_id, "plan_id"),
            development_partition={
                "partition_id": "development_partition",
                "start_date": CANONICAL_DEVELOPMENT_START.isoformat(),
                "end_date": CANONICAL_DEVELOPMENT_END.isoformat(),
                "role": "development_partition",
            },
            validation_partition={
                "partition_id": "validation_partition",
                "start_date": CANONICAL_VALIDATION_START.isoformat(),
                "end_date": CANONICAL_VALIDATION_END.isoformat(),
                "role": "validation_partition",
            },
            locked_test_candidate={
                "partition_id": "locked_test_candidate",
                "start_date": CANONICAL_LOCKED_TEST_START.isoformat(),
                "end_date": CANONICAL_LOCKED_TEST_END,
                "role": "locked_test_candidate",
            },
            latest_shadow_candidate=latest_shadow_candidate,
            contamination_metadata_rules=DEFAULT_CONTAMINATION_METADATA_RULES,
        )

    @property
    def partition_ids(self) -> tuple[str, ...]:
        """Return the plan's explicit partition identifiers."""

        partition_ids = [
            str(self.development_partition["partition_id"]),
            str(self.validation_partition["partition_id"]),
            str(self.locked_test_candidate["partition_id"]),
        ]
        if self.latest_shadow_candidate is not None:
            partition_ids.append(str(self.latest_shadow_candidate["partition_id"]))
        return tuple(partition_ids)

    @property
    def locked_partition_ids(self) -> tuple[str, ...]:
        """Return partitions requiring Governance metadata outside coverage QA."""

        return tuple(self.contamination_metadata_rules["locked_partition_ids"])

    def permits_coverage_qa(self, partition_id: object) -> bool:
        """Return true when coverage QA may inspect the requested partition."""

        normalized = _normalize_id(partition_id, "partition_id")
        if normalized not in self.partition_ids:
            msg = "partition_id is not present in DatasetPartitionPlan"
            raise DataFoundationValidationError(msg)
        return bool(self.contamination_metadata_rules["data_qa_coverage_inspection_allowed"])

    def to_mapping(self) -> Mapping[str, object]:
        """Return a JSON-stable partition-plan mapping."""

        return MappingProxyType(
            {
                "plan_id": self.plan_id,
                "development_partition": self.development_partition,
                "validation_partition": self.validation_partition,
                "locked_test_candidate": self.locked_test_candidate,
                "latest_shadow_candidate": self.latest_shadow_candidate,
                "contamination_metadata_rules": self.contamination_metadata_rules,
            }
        )


def require_governance_metadata_for_locked_partition_use(
    *,
    partition_id: object,
    purpose: object,
    governance_metadata: Mapping[str, object] | None = None,
    plan: DatasetPartitionPlan | None = None,
) -> bool:
    """Fail closed unless locked-partition use has Governance metadata.

    Coverage QA may inspect coverage across partitions without recording
    contamination. Any non-QA use of `locked_test_candidate` or
    `latest_shadow_candidate` must provide substantive Governance
    contamination metadata.
    """

    normalized_partition_id = _normalize_id(partition_id, "partition_id")
    normalized_purpose = _require_text(purpose, "purpose").lower()
    if plan is not None and not isinstance(plan, DatasetPartitionPlan):
        msg = "plan must be a DatasetPartitionPlan"
        raise DataFoundationValidationError(msg)
    if plan is not None and normalized_partition_id not in plan.partition_ids:
        msg = "partition_id is not present in DatasetPartitionPlan"
        raise DataFoundationValidationError(msg)

    locked_partition_ids = (
        plan.locked_partition_ids if plan is not None else DEFAULT_LOCKED_PARTITION_IDS
    )
    if normalized_purpose in DATASET_PARTITION_QA_PURPOSES:
        return True
    if normalized_partition_id not in locked_partition_ids:
        return True

    if plan is not None:
        rules = plan.contamination_metadata_rules
        if (
            not rules["locked_partition_use_requires_governance_metadata"]
            or not rules["locked_partition_use_requires_contamination_metadata"]
        ):
            msg = "DatasetPartitionPlan does not enforce locked-partition metadata"
            raise DataFoundationValidationError(msg)

    _require_substantive_governance_metadata(governance_metadata)
    return True


__all__ = [
    "CONTAMINATION_METADATA_RULE_FIELDS",
    "COVERAGE_REPORT_FIELDS",
    "CoverageReport",
    "DATASET_ACCEPTANCE_COVERAGE_DIMENSIONS",
    "DATASET_ACCEPTANCE_DEFAULT_POLICY",
    "DATASET_ACCEPTANCE_DEFAULT_POLICY_ID",
    "DATASET_ACCEPTANCE_LOCK_METADATA_SCHEMA",
    "DATASET_ACCEPTANCE_REQUIRED_FIELD_GROUPS",
    "DATASET_ACCEPTANCE_STATES",
    "DATA_QUALITY_REPORT_FIELDS",
    "DATASET_PARTITION_QA_PURPOSES",
    "DATASET_VERSION_ADMISSIBLE_STATES",
    "DATASET_VERSION_FIELDS",
    "DataQualityReport",
    "DatasetAcceptanceInventory",
    "DatasetAcceptanceLock",
    "DatasetAcceptanceState",
    "DatasetPartitionPlan",
    "DatasetVersion",
    "REQUIRED_DATASET_PARTITION_PLAN_FIELDS",
    "ReportStatus",
    "build_dataset_acceptance_lock",
    "compute_dataset_acceptance_policy_hash",
    "compute_quality_report_hash",
    "inventory_dataset_acceptance_locks",
    "normalize_dataset_acceptance_policy",
    "persist_dataset_acceptance_locks",
    "render_dataset_acceptance_summary",
    "require_governance_metadata_for_locked_partition_use",
    "resolve_dataset_acceptance_lock",
]
