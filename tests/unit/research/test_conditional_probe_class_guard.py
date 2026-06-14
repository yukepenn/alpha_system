from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.mechanism_card import EXPLORATORY_STAMP
from alpha_system.research.conditional_probe import (
    ConditionalPredicate,
    ConditionalProbeError,
    ConditionalProbeSpec,
    build_path_label_observation_set,
)

PATH_LABEL = generate_governance_id(
    GovernanceIdKind.LABEL_SPEC,
    {"family": "path", "name": "target_before_stop", "version": 1},
)


def test_conditional_probe_rejects_single_class_conditioned_path_labels() -> None:
    with pytest.raises(ConditionalProbeError, match="two distinct classes"):
        build_path_label_observation_set(
            _probe(),
            context_factor_values=_factor_rows((1.0, 1.0, 1.0)),
            trigger_factor_values=_trigger_rows((1.0, 1.0, 1.0)),
            path_labels=_path_label_rows((True, True, True)),
        )


def test_conditional_probe_accepts_two_class_conditioned_path_labels() -> None:
    observation_set = build_path_label_observation_set(
        _probe(),
        context_factor_values=_factor_rows((1.0, 1.0, 1.0)),
        trigger_factor_values=_trigger_rows((1.0, 1.0, 1.0)),
        path_labels=_path_label_rows((True, False, True)),
    )

    assert len(observation_set.aligned_observations) == 3
    assert len(observation_set.conditioned_observations) == 3


def _probe() -> ConditionalProbeSpec:
    return ConditionalProbeSpec(
        setup_spec_id="setup_testability_class_guard",
        stamp=EXPLORATORY_STAMP,
        path_label=PATH_LABEL,
        context=ConditionalPredicate(
            factor_id="context_fixture",
            factor_version="ctx:v1",
            value_field="normalized_value",
            operator=">=",
            threshold=0.5,
        ),
        trigger=ConditionalPredicate(
            factor_id="trigger_fixture",
            factor_version="trg:v1",
            value_field="normalized_value",
            operator=">",
            threshold=0.0,
        ),
        allowed_variants=("baseline",),
        fixed_geometry={"horizon": "30m"},
    )


def _factor_rows(values: tuple[float, ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        _factor_row("context_fixture", "ctx:v1", index, value)
        for index, value in enumerate(values)
    )


def _trigger_rows(values: tuple[float, ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        _factor_row("trigger_fixture", "trg:v1", index, value)
        for index, value in enumerate(values)
    )


def _factor_row(
    factor_id: str,
    factor_version: str,
    index: int,
    value: float,
) -> dict[str, object]:
    event_ts = _event_ts(index)
    return {
        "factor_id": factor_id,
        "factor_version": factor_version,
        "instrument_id": "SYNTH",
        "event_ts": _text(event_ts),
        "available_ts": _text(event_ts + timedelta(seconds=1)),
        "session_id": "XNYS:2026-01-02:regular",
        "bar_index": index + 1,
        "value": value,
        "normalized_value": value,
        "data_version": "data:v1",
    }


def _path_label_rows(values: tuple[bool, ...]) -> tuple[dict[str, object], ...]:
    return tuple(_label_row(index, value) for index, value in enumerate(values))


def _label_row(index: int, value: bool) -> dict[str, object]:
    event_ts = _event_ts(index)
    horizon_end_ts = event_ts + timedelta(minutes=30)
    return {
        "label_id": PATH_LABEL,
        "instrument_id": "SYNTH",
        "event_ts": _text(event_ts),
        "horizon": 1800,
        "label_type": "target_before_stop",
        "value": value,
        "path_metadata": {
            "session_id": "XNYS:2026-01-02:regular",
            "label_version": "labels:v1",
            "horizon_end_ts": _text(horizon_end_ts),
            "required_future_bars": 30,
            "observed_future_bars": 30,
            "path_label_binding": PATH_LABEL,
        },
        "data_version": "data:v1",
        "label_available_ts": _text(horizon_end_ts + timedelta(seconds=1)),
    }


def _event_ts(index: int) -> datetime:
    return datetime(2026, 1, 2, 14, 31 + index, tzinfo=UTC)


def _text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
