from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest

from alpha_system.features.contracts import FeatureValueRecord

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


def _record_key(record: FeatureValueRecord) -> tuple[str, str, datetime, datetime]:
    return (
        record.feature_version_id,
        record.entity_id,
        record.event_ts,
        record.available_ts,
    )


def _is_gap(record: FeatureValueRecord) -> bool:
    return record.value is None or bool(GAP_FLAGS.intersection(record.quality_flags))


def _assert_values_match(
    reference_value: Any,
    fast_value: Any,
    *,
    tolerance: FeatureParityTolerance,
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
