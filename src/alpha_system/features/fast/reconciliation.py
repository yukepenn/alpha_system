"""Value-free reconciliation helpers for reference versus fast feature outputs."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from statistics import median
from typing import Any

from alpha_system.core.value_store import load_parquet_values
from alpha_system.features.contracts import FeatureValueRecord
from alpha_system.features.fast.materializer import (
    FAST_PRODUCER_ENGINE_ID,
    FAST_VALUE_SCHEMA_VERSION,
)
from alpha_system.features.registry import REFERENCE_FEATURE_PRODUCER_ENGINE_ID
from alpha_system.governance.serialization import JsonValue


class ReconciliationClassification(StrEnum):
    """Aggregate reconciliation outcome for one logical value series."""

    IDENTICAL = "identical"
    WITHIN_TOLERANCE = "within_tolerance"
    BEYOND_TOLERANCE = "beyond_tolerance"


class ReconciliationDecision(StrEnum):
    """Allowed policy branch for a reconciliation outcome."""

    KEEP_REFERENCE_TAG_PROVENANCE = "keep_reference_tag_provenance"
    BLOCK_SILENT_MIXING = "block_silent_mixing"


@dataclass(frozen=True, slots=True)
class ReconciliationTolerance:
    """Documented numeric tolerance for one feature family or logical series."""

    abs: float = 0.0
    rel: float = 0.0
    reason: str = "exact parity expected"

    def __post_init__(self) -> None:
        if not isinstance(self.abs, int | float) or isinstance(self.abs, bool) or self.abs < 0:
            raise ValueError("abs tolerance must be a non-negative number")
        if not isinstance(self.rel, int | float) or isinstance(self.rel, bool) or self.rel < 0:
            raise ValueError("rel tolerance must be a non-negative number")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")

    @property
    def label(self) -> str:
        """Return a compact value-free tolerance label."""

        if self.abs == 0.0 and self.rel == 0.0:
            return "exact"
        if self.abs == self.rel:
            return f"abs/rel {self.abs:g}"
        return f"abs {self.abs:g}, rel {self.rel:g}"


@dataclass(frozen=True, slots=True)
class ReconciliationSeriesResult:
    """Value-free reconciliation statistics for one logical value series."""

    family_id: str
    logical_series_id: str
    producer_engines: tuple[str, ...]
    value_schema_versions: tuple[str, ...]
    tolerance: ReconciliationTolerance
    classification: ReconciliationClassification
    decision: ReconciliationDecision
    compared_count: int
    exact_count: int
    within_tolerance_count: int
    beyond_tolerance_count: int
    missing_reference_count: int
    missing_candidate_count: int
    quality_flag_mismatch_count: int
    max_abs_diff: float
    median_abs_diff: float

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a JSON-compatible summary without per-row values."""

        return {
            "family_id": self.family_id,
            "logical_series_id": self.logical_series_id,
            "producer_engines": list(self.producer_engines),
            "value_schema_versions": list(self.value_schema_versions),
            "tolerance": self.tolerance.label,
            "tolerance_reason": self.tolerance.reason,
            "classification": self.classification.value,
            "decision": self.decision.value,
            "compared_count": self.compared_count,
            "exact_count": self.exact_count,
            "within_tolerance_count": self.within_tolerance_count,
            "beyond_tolerance_count": self.beyond_tolerance_count,
            "missing_reference_count": self.missing_reference_count,
            "missing_candidate_count": self.missing_candidate_count,
            "quality_flag_mismatch_count": self.quality_flag_mismatch_count,
            "max_abs_diff": self.max_abs_diff,
            "median_abs_diff": self.median_abs_diff,
        }


FEATURE_RECONCILIATION_TOLERANCES: Mapping[str, ReconciliationTolerance] = {
    "base_ohlcv": ReconciliationTolerance(
        abs=5e-8,
        rel=0.0,
        reason="volume_zscore rolling-standard-deviation summation order; other base_ohlcv features exact",
    ),
    "session_calendar_roll": ReconciliationTolerance(
        reason="calendar, session, and roll fields are exact on the governed fixture",
    ),
    "vwap_session_auction": ReconciliationTolerance(
        abs=1e-12,
        rel=1e-12,
        reason="VWAP cumulative floating-point reductions",
    ),
    "regime_vol_compression": ReconciliationTolerance(
        abs=1e-12,
        rel=1e-12,
        reason="ATR/trendiness floating-point reductions; range contraction exact on fixture",
    ),
    "liquidity_pa_structure": ReconciliationTolerance(
        abs=1e-12,
        rel=1e-12,
        reason="finite OHLC ratio features; flags and sweep indicators exact",
    ),
    "volume_activity": ReconciliationTolerance(
        abs=1e-12,
        rel=1e-12,
        reason="volume z-score, range, trendiness, and structure-ratio reductions",
    ),
    "bbo_tradability": ReconciliationTolerance(
        abs=1e-12,
        rel=1e-12,
        reason="spread z-score rolling variance reduction; other BBO fields exact",
    ),
    "cross_market": ReconciliationTolerance(
        abs=1e-12,
        rel=1e-12,
        reason="rolling covariance, variance, residual, and correlation reductions",
    ),
}


def classify_feature_value_records(
    *,
    family_id: str,
    logical_series_id: str,
    reference_records: Sequence[FeatureValueRecord | Mapping[str, Any]],
    candidate_records: Sequence[FeatureValueRecord | Mapping[str, Any]],
    tolerance: ReconciliationTolerance,
    reference_engine_id: str = REFERENCE_FEATURE_PRODUCER_ENGINE_ID,
    candidate_engine_id: str = FAST_PRODUCER_ENGINE_ID,
    reference_value_schema_version: str | None = None,
    candidate_value_schema_version: str = FAST_VALUE_SCHEMA_VERSION,
) -> ReconciliationSeriesResult:
    """Classify one logical series without returning per-row values."""

    family = _require_text(family_id, "family_id")
    series = _require_text(logical_series_id, "logical_series_id")
    if not isinstance(tolerance, ReconciliationTolerance):
        raise ValueError("tolerance must be a ReconciliationTolerance")
    reference_by_key = {_record_key(record): record for record in reference_records}
    candidate_by_key = {_record_key(record): record for record in candidate_records}
    if len(reference_by_key) != len(reference_records):
        raise ValueError("reference_records contain duplicate logical keys")
    if len(candidate_by_key) != len(candidate_records):
        raise ValueError("candidate_records contain duplicate logical keys")

    reference_keys = set(reference_by_key)
    candidate_keys = set(candidate_by_key)
    common_keys = sorted(reference_keys.intersection(candidate_keys))
    missing_reference_count = len(candidate_keys - reference_keys)
    missing_candidate_count = len(reference_keys - candidate_keys)
    quality_flag_mismatch_count = 0
    exact_count = 0
    within_tolerance_count = 0
    beyond_tolerance_count = missing_reference_count + missing_candidate_count
    diffs: list[float] = []

    for key in common_keys:
        reference = reference_by_key[key]
        candidate = candidate_by_key[key]
        if _quality_flags(reference) != _quality_flags(candidate):
            quality_flag_mismatch_count += 1
            beyond_tolerance_count += 1
            continue
        value_diffs = _value_abs_diffs(_value(reference), _value(candidate))
        if value_diffs is None:
            beyond_tolerance_count += 1
            continue
        if value_diffs:
            diffs.extend(value_diffs)
        max_row_diff = max(value_diffs) if value_diffs else 0.0
        if max_row_diff == 0.0:
            exact_count += 1
            within_tolerance_count += 1
            continue
        if _diffs_within_tolerance(
            _value(reference),
            _value(candidate),
            tolerance=tolerance,
        ):
            within_tolerance_count += 1
        else:
            beyond_tolerance_count += 1

    max_abs_diff = max(diffs) if diffs else 0.0
    median_abs_diff = float(median(diffs)) if diffs else 0.0
    if beyond_tolerance_count:
        classification = ReconciliationClassification.BEYOND_TOLERANCE
        decision = ReconciliationDecision.BLOCK_SILENT_MIXING
    elif exact_count == len(common_keys):
        classification = ReconciliationClassification.IDENTICAL
        decision = ReconciliationDecision.KEEP_REFERENCE_TAG_PROVENANCE
    else:
        classification = ReconciliationClassification.WITHIN_TOLERANCE
        decision = ReconciliationDecision.KEEP_REFERENCE_TAG_PROVENANCE

    return ReconciliationSeriesResult(
        family_id=family,
        logical_series_id=series,
        producer_engines=tuple(
            sorted(
                {
                    _require_text(reference_engine_id, "reference_engine_id"),
                    _require_text(candidate_engine_id, "candidate_engine_id"),
                }
            )
        ),
        value_schema_versions=tuple(
            sorted(
                value
                for value in {
                    reference_value_schema_version,
                    candidate_value_schema_version,
                }
                if value is not None
            )
        ),
        tolerance=tolerance,
        classification=classification,
        decision=decision,
        compared_count=len(common_keys),
        exact_count=exact_count,
        within_tolerance_count=within_tolerance_count,
        beyond_tolerance_count=beyond_tolerance_count,
        missing_reference_count=missing_reference_count,
        missing_candidate_count=missing_candidate_count,
        quality_flag_mismatch_count=quality_flag_mismatch_count,
        max_abs_diff=max_abs_diff,
        median_abs_diff=median_abs_diff,
    )


def classify_parquet_feature_series(
    *,
    family_id: str,
    logical_series_id: str,
    reference_parquet_path: str | Path,
    candidate_parquet_path: str | Path,
    tolerance: ReconciliationTolerance,
    reference_engine_id: str = REFERENCE_FEATURE_PRODUCER_ENGINE_ID,
    candidate_engine_id: str = FAST_PRODUCER_ENGINE_ID,
    reference_value_schema_version: str | None = None,
    candidate_value_schema_version: str = FAST_VALUE_SCHEMA_VERSION,
) -> ReconciliationSeriesResult:
    """Read two Parquet value stores via sanctioned readers and classify them."""

    return classify_feature_value_records(
        family_id=family_id,
        logical_series_id=logical_series_id,
        reference_records=load_parquet_values(reference_parquet_path),
        candidate_records=load_parquet_values(candidate_parquet_path),
        tolerance=tolerance,
        reference_engine_id=reference_engine_id,
        candidate_engine_id=candidate_engine_id,
        reference_value_schema_version=reference_value_schema_version,
        candidate_value_schema_version=candidate_value_schema_version,
    )


def reconciliation_decision_text(result: ReconciliationSeriesResult) -> str:
    """Return the human-readable policy decision for a result."""

    if result.decision is ReconciliationDecision.KEEP_REFERENCE_TAG_PROVENANCE:
        return "keep existing valid reference output, tag provenance, do not overwrite"
    return (
        "block silent mixing: treat as V1 bug, explicitly bump value_schema_version, "
        "or re-materialize through the official keystone path"
    )


def _record_key(record: FeatureValueRecord | Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        _record_text(record, "feature_version_id"),
        _record_text(record, "entity_id"),
        _datetime_key(_record_value(record, "event_ts"), "event_ts"),
        _datetime_key(_record_value(record, "available_ts"), "available_ts"),
    )


def _value(record: FeatureValueRecord | Mapping[str, Any]) -> Any:
    return _record_value(record, "value")


def _quality_flags(record: FeatureValueRecord | Mapping[str, Any]) -> tuple[str, ...]:
    value = _record_value(record, "quality_flags")
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if not isinstance(value, Sequence):
        raise ValueError("quality_flags must be a sequence")
    return tuple(str(flag) for flag in value)


def _record_text(record: FeatureValueRecord | Mapping[str, Any], field_name: str) -> str:
    return _require_text(_record_value(record, field_name), field_name)


def _record_value(record: FeatureValueRecord | Mapping[str, Any], field_name: str) -> Any:
    if isinstance(record, FeatureValueRecord):
        return getattr(record, field_name)
    if isinstance(record, Mapping):
        if field_name not in record:
            raise ValueError(f"record missing {field_name}")
        return record[field_name]
    raise ValueError("records must be FeatureValueRecord or mappings")


def _datetime_key(value: object, field_name: str) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return _require_text(value, field_name)


def _value_abs_diffs(reference: Any, candidate: Any) -> list[float] | None:
    if reference is None or candidate is None:
        return [] if reference is candidate else None
    if isinstance(reference, Mapping) or isinstance(candidate, Mapping):
        if not isinstance(reference, Mapping) or not isinstance(candidate, Mapping):
            return None
        if set(reference) != set(candidate):
            return None
        diffs: list[float] = []
        for key in sorted(reference):
            child = _value_abs_diffs(reference[key], candidate[key])
            if child is None:
                return None
            diffs.extend(child)
        return diffs
    if _is_number(reference) and _is_number(candidate):
        reference_float = float(reference)
        candidate_float = float(candidate)
        if not math.isfinite(reference_float) or not math.isfinite(candidate_float):
            return [] if reference_float == candidate_float else None
        return [abs(reference_float - candidate_float)]
    return [] if reference == candidate else None


def _diffs_within_tolerance(
    reference: Any,
    candidate: Any,
    *,
    tolerance: ReconciliationTolerance,
) -> bool:
    if reference is None or candidate is None:
        return reference is candidate
    if isinstance(reference, Mapping) or isinstance(candidate, Mapping):
        if not isinstance(reference, Mapping) or not isinstance(candidate, Mapping):
            return False
        if set(reference) != set(candidate):
            return False
        return all(
            _diffs_within_tolerance(reference[key], candidate[key], tolerance=tolerance)
            for key in sorted(reference)
        )
    if _is_number(reference) and _is_number(candidate):
        return math.isclose(
            float(reference),
            float(candidate),
            abs_tol=float(tolerance.abs),
            rel_tol=float(tolerance.rel),
        )
    return reference == candidate


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    text = value.strip()
    if not text or "\n" in text or "\r" in text:
        raise ValueError(f"{field_name} must be a non-empty single-line string")
    return text


__all__ = [
    "FEATURE_RECONCILIATION_TOLERANCES",
    "ReconciliationClassification",
    "ReconciliationDecision",
    "ReconciliationSeriesResult",
    "ReconciliationTolerance",
    "classify_feature_value_records",
    "classify_parquet_feature_series",
    "reconciliation_decision_text",
]
