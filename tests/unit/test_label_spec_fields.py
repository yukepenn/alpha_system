from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from alpha_system.core.enums import LabelType
from alpha_system.labels.spec import (
    REQUIRED_LABEL_RECORD_FIELDS,
    STANDARD_LABEL_TYPES,
    LabelSpec,
    LabelSpecError,
    label_record_field_names,
)


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "label_id": "forward_return_1m",
        "instrument_id": "SYNTH_LABEL",
        "event_ts": "2026-01-02T14:31:00Z",
        "horizon": "1m",
        "label_type": "forward_return_1m",
        "value": 0.01,
        "path_metadata": {
            "session_id": "XNYS:2026-01-02:regular",
            "label_version": "v1",
            "horizon_end_ts": "2026-01-02T14:32:00Z",
            "required_future_bars": 1,
            "observed_future_bars": 1,
            "insufficient_future": False,
        },
        "data_version": "data:synthetic-labels:v1",
        "label_available_ts": "2026-01-02T14:32:05Z",
    }
    payload.update(overrides)
    return payload


def test_label_spec_contains_exact_required_record_fields() -> None:
    assert label_record_field_names() == REQUIRED_LABEL_RECORD_FIELDS
    assert tuple(LabelSpec.from_mapping(_payload()).to_dict()) == REQUIRED_LABEL_RECORD_FIELDS


def test_label_type_enum_covers_standard_label_families() -> None:
    expected = {
        "forward_return_1m",
        "forward_return_3m",
        "forward_return_5m",
        "forward_return_10m",
        "forward_return_30m",
        "mfe_by_horizon",
        "mae_by_horizon",
        "target_before_stop",
        "stop_before_target",
        "future_realized_volatility",
        "future_spread_liquidity",
    }

    assert {label_type.value for label_type in STANDARD_LABEL_TYPES} == expected
    assert {label_type.value for label_type in LabelType} >= expected


@pytest.mark.parametrize("field", REQUIRED_LABEL_RECORD_FIELDS)
def test_missing_required_label_spec_field_is_rejected(field: str) -> None:
    payload = _payload()
    payload.pop(field)

    with pytest.raises(LabelSpecError, match="missing required"):
        LabelSpec.from_mapping(payload)


def test_unexpected_label_spec_field_is_rejected() -> None:
    with pytest.raises(LabelSpecError, match="unexpected fields"):
        LabelSpec.from_mapping(_payload(session_id="not-a-top-level-field"))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("label_type", "unknown_label", "unsupported label_type"),
        ("horizon", 0, "horizon"),
        ("event_ts", datetime(2026, 1, 2, 14, 31), "timezone-aware"),
        ("label_available_ts", "2026-01-02T14:30:59Z", "label_available_ts"),
        ("label_id", "Bad Label", "label_id"),
        ("path_metadata", [], "path_metadata"),
    ),
)
def test_invalid_label_spec_fields_are_rejected(
    field: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(LabelSpecError, match=message):
        LabelSpec.from_mapping(_payload(**{field: value}))


def test_horizon_seconds_are_normalized_to_timedelta() -> None:
    spec = LabelSpec.from_mapping(_payload(horizon=timedelta(minutes=3)))

    assert spec.horizon == timedelta(minutes=3)
    assert spec.event_ts.tzinfo == timezone.utc
