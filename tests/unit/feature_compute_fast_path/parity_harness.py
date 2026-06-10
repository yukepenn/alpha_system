from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from statistics import median
from typing import Any

import pytest

from alpha_system.features.contracts import FeatureValueRecord
from alpha_system.labels.version import LabelValueRecord

GAP_FLAGS = frozenset(
    {
        "insufficient_window",
        "input_gap",
        "session_reset",
        "primitive_gap",
        "ohlcv_gap",
        "no_trade",
    }
)


@dataclass(frozen=True, slots=True)
class FeatureParityTolerance:
    """Numeric tolerance for one parity assertion."""

    abs: float = 0.0
    rel: float = 0.0
    reason: str = "exact parity expected"


def assert_feature_records_match(
    reference_records: tuple[FeatureValueRecord, ...],
    fast_records: tuple[FeatureValueRecord, ...],
    *,
    expected_feature_version_id: str,
    tolerance: FeatureParityTolerance = FeatureParityTolerance(),
) -> None:
    """Assert value, availability, gap, flag, and identity parity."""

    assert reference_records, "reference engine produced no records"
    assert fast_records, "fast engine produced no records"
    assert {record.feature_version_id for record in reference_records} == {
        expected_feature_version_id
    }
    assert {record.feature_version_id for record in fast_records} == {
        expected_feature_version_id
    }

    reference_by_key = {_record_key(record): record for record in reference_records}
    fast_by_key = {_record_key(record): record for record in fast_records}
    assert fast_by_key.keys() == reference_by_key.keys()

    reference_gaps = {_record_key(record) for record in reference_records if _is_gap(record)}
    fast_gaps = {_record_key(record) for record in fast_records if _is_gap(record)}
    assert fast_gaps == reference_gaps

    for key, reference in reference_by_key.items():
        fast = fast_by_key[key]
        assert fast.available_ts == reference.available_ts
        assert fast.quality_flags == reference.quality_flags
        _assert_values_match(reference.value, fast.value, tolerance=tolerance)


@dataclass(frozen=True, slots=True)
class LabelParityTolerance:
    """Numeric tolerance for one label parity assertion."""

    abs: float = 0.0
    rel: float = 0.0
    reason: str = "exact label parity expected"


@dataclass(frozen=True, slots=True)
class LabelParityStats:
    """Value-free summary of one label parity comparison."""

    label_version_id: str
    record_count: int
    compared_value_count: int
    null_value_count: int
    quality_flagged_count: int
    max_abs_diff: float
    median_abs_diff: float
    tolerance: LabelParityTolerance


def assert_label_records_match(
    reference_records: tuple[LabelValueRecord, ...],
    fast_records: tuple[LabelValueRecord, ...],
    *,
    expected_label_version_id: str,
    tolerance: LabelParityTolerance = LabelParityTolerance(),
) -> None:
    """Assert label value, availability, horizon, flags, and identity parity."""

    assert reference_records, "reference engine produced no label records"
    assert fast_records, "fast engine produced no label records"
    assert {record.label_version_id for record in reference_records} == {
        expected_label_version_id
    }
    assert {record.label_version_id for record in fast_records} == {
        expected_label_version_id
    }

    reference_by_key = {_label_record_key(record): record for record in reference_records}
    fast_by_key = {_label_record_key(record): record for record in fast_records}
    assert fast_by_key.keys() == reference_by_key.keys()

    for key, reference in reference_by_key.items():
        fast = fast_by_key[key]
        assert fast.horizon_end_ts == reference.horizon_end_ts
        assert fast.label_available_ts == reference.label_available_ts
        assert fast.quality_flags == reference.quality_flags
        assert fast.label_spec_id == reference.label_spec_id
        _assert_values_match(reference.value, fast.value, tolerance=tolerance)


def assert_and_summarize_label_records_match(
    reference_records: tuple[LabelValueRecord, ...],
    fast_records: tuple[LabelValueRecord, ...],
    *,
    expected_label_version_id: str,
    tolerance: LabelParityTolerance = LabelParityTolerance(),
) -> LabelParityStats:
    """Assert parity and return value-free comparison counts/diff stats."""

    assert_label_records_match(
        reference_records,
        fast_records,
        expected_label_version_id=expected_label_version_id,
        tolerance=tolerance,
    )
    reference_by_key = {_label_record_key(record): record for record in reference_records}
    fast_by_key = {_label_record_key(record): record for record in fast_records}
    numeric_diffs: list[float] = []
    for key, reference in reference_by_key.items():
        _collect_numeric_abs_diffs(reference.value, fast_by_key[key].value, numeric_diffs)
    return LabelParityStats(
        label_version_id=expected_label_version_id,
        record_count=len(reference_records),
        compared_value_count=len(reference_records),
        null_value_count=sum(1 for record in reference_records if record.value is None),
        quality_flagged_count=sum(1 for record in reference_records if record.quality_flags),
        max_abs_diff=max(numeric_diffs, default=0.0),
        median_abs_diff=median(numeric_diffs) if numeric_diffs else 0.0,
        tolerance=tolerance,
    )


def _record_key(record: FeatureValueRecord) -> tuple[str, str, datetime, datetime]:
    return (
        record.feature_version_id,
        record.entity_id,
        record.event_ts,
        record.available_ts,
    )


def _label_record_key(record: LabelValueRecord) -> tuple[str, str, datetime]:
    return (
        record.label_version_id,
        record.entity_id,
        record.event_ts,
    )


def _is_gap(record: FeatureValueRecord) -> bool:
    return record.value is None or bool(GAP_FLAGS.intersection(record.quality_flags))


def _assert_values_match(
    reference_value: Any,
    fast_value: Any,
    *,
    tolerance: FeatureParityTolerance | LabelParityTolerance,
) -> None:
    if reference_value is None or fast_value is None:
        assert fast_value is reference_value
        return
    if isinstance(reference_value, Mapping) and isinstance(fast_value, Mapping):
        assert fast_value.keys() == reference_value.keys()
        for key, nested_reference in reference_value.items():
            _assert_values_match(
                nested_reference,
                fast_value[key],
                tolerance=tolerance,
            )
        return
    if isinstance(reference_value, bool) or isinstance(fast_value, bool):
        assert fast_value == reference_value
        return
    if isinstance(reference_value, int | float) and isinstance(fast_value, int | float):
        if tolerance.abs == 0.0 and tolerance.rel == 0.0:
            assert fast_value == reference_value
            return
        assert math.isfinite(float(reference_value))
        assert math.isfinite(float(fast_value))
        assert fast_value == pytest.approx(
            reference_value,
            abs=tolerance.abs,
            rel=tolerance.rel,
        ), tolerance.reason
        return
    assert fast_value == reference_value


def _collect_numeric_abs_diffs(
    reference_value: Any,
    fast_value: Any,
    diffs: list[float],
) -> None:
    if reference_value is None or fast_value is None:
        return
    if isinstance(reference_value, Mapping) and isinstance(fast_value, Mapping):
        for key, nested_reference in reference_value.items():
            _collect_numeric_abs_diffs(nested_reference, fast_value[key], diffs)
        return
    if (
        isinstance(reference_value, int | float)
        and not isinstance(reference_value, bool)
        and isinstance(fast_value, int | float)
        and not isinstance(fast_value, bool)
    ):
        diffs.append(abs(float(fast_value) - float(reference_value)))
