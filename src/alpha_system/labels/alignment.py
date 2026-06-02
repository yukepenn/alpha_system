"""Point-in-time label alignment policy and live-consumption guards."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from alpha_system.labels.spec import LabelSpec
from alpha_system.labels.validation import validate_label_record


class LabelAlignmentError(ValueError):
    """Raised when label alignment or consumption policy is violated."""


ALIGNMENT_KEY_FIELDS: tuple[str, ...] = (
    "instrument_id",
    "event_ts",
    "session_id",
    "horizon",
    "data_version",
    "label_version",
)

LIVE_LABEL_PURPOSES: frozenset[str] = frozenset(
    {"live_factor_input", "live_strategy_input", "factor_input", "strategy_input"}
)


@dataclass(frozen=True, slots=True)
class LabelAlignmentKey:
    instrument_id: str
    event_ts: datetime
    session_id: str
    horizon: timedelta
    data_version: str
    label_version: str

    def as_tuple(self) -> tuple[str, datetime, str, timedelta, str, str]:
        return (
            self.instrument_id,
            self.event_ts,
            self.session_id,
            self.horizon,
            self.data_version,
            self.label_version,
        )


def alignment_key_for_label(label: LabelSpec | Mapping[str, Any]) -> LabelAlignmentKey:
    """Build the required factor-label research alignment key."""
    spec = validate_label_record(label)
    metadata = dict(spec.path_metadata)
    return LabelAlignmentKey(
        instrument_id=spec.instrument_id,
        event_ts=spec.event_ts,
        session_id=str(metadata["session_id"]),
        horizon=spec.horizon,
        data_version=spec.data_version,
        label_version=str(metadata["label_version"]),
    )


def assert_research_join_purpose(purpose: str) -> None:
    """Reject any attempt to use labels as live factor or strategy inputs."""
    normalized = purpose.strip().lower()
    if normalized in LIVE_LABEL_PURPOSES or "live" in normalized:
        msg = "labels are research targets and cannot be live inputs"
        raise LabelAlignmentError(msg)


def reject_labels_as_factor_inputs(inputs: Iterable[Any]) -> None:
    """Raise if a proposed factor input collection contains labels."""
    _reject_label_consumption(inputs, consumer="factor")


def reject_labels_as_strategy_inputs(inputs: Iterable[Any]) -> None:
    """Raise if a proposed strategy input collection contains labels."""
    _reject_label_consumption(inputs, consumer="strategy")


def research_label_join_index(
    labels: Iterable[LabelSpec | Mapping[str, Any]],
    *,
    purpose: str = "research",
) -> dict[LabelAlignmentKey, LabelSpec]:
    """Return a point-in-time research join index keyed only by alignment fields."""
    assert_research_join_purpose(purpose)
    index: dict[LabelAlignmentKey, LabelSpec] = {}
    for label in labels:
        spec = validate_label_record(label)
        key = alignment_key_for_label(spec)
        if key in index:
            msg = f"duplicate label alignment key: {key.as_tuple()}"
            raise LabelAlignmentError(msg)
        index[key] = spec
    return index


def _reject_label_consumption(inputs: Iterable[Any], *, consumer: str) -> None:
    for item in inputs:
        if isinstance(item, LabelSpec):
            msg = f"labels cannot be {consumer} inputs"
            raise LabelAlignmentError(msg)
        if isinstance(item, Mapping):
            keys = {str(key).lower() for key in item}
            domain = str(item.get("domain", "")).lower()
            source = str(item.get("source_field", item.get("name", ""))).lower()
            if "label_type" in keys or "label_available_ts" in keys:
                msg = f"label records cannot be {consumer} inputs"
                raise LabelAlignmentError(msg)
            if domain == "label" or "label" in source:
                msg = f"label fields cannot be {consumer} inputs"
                raise LabelAlignmentError(msg)
        elif isinstance(item, str) and "label" in item.lower():
            msg = f"label fields cannot be {consumer} inputs"
            raise LabelAlignmentError(msg)
