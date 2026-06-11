"""Strategy-agnostic path labels over trade-truth OHLCV bars.

The family consumes the FLF-P16 governance-bound label contracts and FLF-P04
trade-bar predicates. It returns in-memory `LabelValueRecord` objects only; it
does not materialize values, read provider files, or expose labels as features.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from alpha_system.data.foundation.rolls import RollCalendarRecord
from alpha_system.features.input_views import OHLCVInputView
from alpha_system.features.semantics import TradeBarRow, is_real_trade_bar
from alpha_system.governance.label_spec import LabelSpec as GovernanceLabelSpec
from alpha_system.labels.families.fixed_horizon import (
    MAINTENANCE_GUARD_VERSION,
    MAINTENANCE_POLICY_ID,
)
from alpha_system.labels.families.fixed_horizon.family import _guarded_forward_terminal
from alpha_system.labels.roll_guard import (
    DEFAULT_CROSS_ROLL_POLICY,
    DEFAULT_ROLL_WINDOW_DAYS_AFTER,
    DEFAULT_ROLL_WINDOW_DAYS_BEFORE,
    ROLL_GUARD_VERSION,
    ROLL_POLICY_ID,
)
from alpha_system.labels.version import (
    LabelContractSpec,
    LabelFamily,
    LabelInputSpec,
    LabelValueRecord,
    LabelVersion,
)


class PathLabelError(ValueError):
    """Raised when path-label definition or computation fails closed."""


class PathLabelName(StrEnum):
    """Supported FLF-P19 path labels."""

    MFE = "mfe"
    MAE = "mae"
    TARGET_BEFORE_STOP = "target_before_stop"
    TRIPLE_BARRIER = "triple_barrier"


class PathDirection(StrEnum):
    """Directional interpretation for strategy-agnostic path outcomes."""

    LONG = "long"
    SHORT = "short"


class SameBarBarrierPolicy(StrEnum):
    """Policy for OHLCV bars where target and stop are both crossed."""

    AMBIGUOUS = "ambiguous"
    TARGET_FIRST = "target_first"
    STOP_FIRST = "stop_first"


class PathBarrier(StrEnum):
    """Barrier resolution types for target/stop path labels."""

    TARGET = "target"
    STOP = "stop"
    HORIZON = "horizon"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class PathLabelDefinition:
    """Approved, versioned path-label definition bound to a governance `LabelSpec`."""

    name: PathLabelName
    contract: LabelContractSpec
    version: LabelVersion
    horizon_steps: int
    price_field: str
    direction: PathDirection
    same_bar_policy: SameBarBarrierPolicy
    target_return: float | None = None
    stop_return: float | None = None

    @property
    def label_id(self) -> str:
        """Return the stable label id from the bound contract."""

        return self.contract.label_id

    @property
    def label_version_id(self) -> str:
        """Return the deterministic label-version id."""

        return self.version.label_version_id


@dataclass(frozen=True, slots=True)
class _PathOutcome:
    value: bool | int | float | None
    resolution_row: TradeBarRow
    quality_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _DirectionalReturns:
    favorable: float
    adverse: float


_PRICE_FIELDS = frozenset({"open", "high", "low", "close"})
_BARRIER_LABELS = frozenset(
    {PathLabelName.TARGET_BEFORE_STOP, PathLabelName.TRIPLE_BARRIER}
)


def supported_path_labels() -> tuple[PathLabelName, ...]:
    """Return the complete FLF-P19 path label list."""

    return tuple(PathLabelName)


def build_path_label_definition(
    name: PathLabelName | str,
    governance_label_spec: GovernanceLabelSpec | Mapping[str, Any] | None,
    *,
    dataset_version_ids: Sequence[str] = (),
    price_field: str | None = None,
    contract_metadata: Mapping[str, Any] | None = None,
    materialization_scope: Mapping[str, Any] | None = None,
) -> PathLabelDefinition:
    """Build one strategy-agnostic path label from a governed `LabelSpec`.

    The governance `LabelSpec` supplies horizon, path rules, barrier rules,
    availability policy, and leakage checks. Missing or invalid governance
    binding fails closed through the consumed FLF-P16 contracts.
    """

    label_name = _coerce_label_name(name)
    spec = _coerce_governance_label_spec(governance_label_spec)
    path_rules = spec.path_rules
    target_stop_rules = spec.target_stop_rules
    horizon_steps = _positive_int(path_rules.get("horizon_steps"), "path_rules.horizon_steps")
    resolved_price_field = _price_field(price_field or path_rules.get("price_field", "close"))
    direction = _direction(path_rules.get("direction", target_stop_rules.get("direction", "long")))
    same_bar_policy = _same_bar_policy(target_stop_rules.get("same_bar_policy", "ambiguous"))
    target_return = _optional_float(target_stop_rules.get("target_return"), "target_return")
    stop_return = _optional_float(target_stop_rules.get("stop_return"), "stop_return")

    if label_name in _BARRIER_LABELS:
        target_return = _required_target(target_return)
        stop_return = _required_stop(stop_return)

    metadata = {
        "campaign": "ALPHA_FEATURE_LABEL_FOUNDATION_V1",
        "phase": "FLF-P19",
        "scaleout_campaign": "ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1",
        "scaleout_phase": "FUTSUB-P20",
        "label_family": LabelFamily.PATH.value,
        "label_name": label_name.value,
        "materialization": "in_memory_records_only",
        "claims": "descriptive_label_substrate_only",
        "path_scan": "positional_real_trade_bar_window",
        "terminal_key": "series_id+contract_id+event_ts",
        "terminal_resolution": "full_path_window_guarded_before_scan",
        "roll_policy_id": ROLL_POLICY_ID,
        "roll_guard_version": ROLL_GUARD_VERSION,
        "roll_cross_policy": DEFAULT_CROSS_ROLL_POLICY.value,
        "roll_window": {
            "days_before": DEFAULT_ROLL_WINDOW_DAYS_BEFORE,
            "days_after": DEFAULT_ROLL_WINDOW_DAYS_AFTER,
        },
        "maintenance_policy_id": MAINTENANCE_POLICY_ID,
        "maintenance_guard_version": MAINTENANCE_GUARD_VERSION,
        "maintenance_crossing_policy": "drop",
        **dict(contract_metadata or {}),
    }
    scope = _materialization_scope_metadata(materialization_scope)
    if scope:
        metadata["materialization_scope"] = scope

    contract = LabelContractSpec.from_label_spec(
        label_id=f"path_{label_name.value}",
        family=LabelFamily.PATH,
        governance_label_spec=spec,
        inputs=LabelInputSpec(
            input_views=("canonical_ohlcv",),
            fields=_label_input_fields(resolved_price_field),
            dataset_version_ids=tuple(dataset_version_ids),
            input_metadata={
                "source": "accepted DatasetVersion canonical OHLCV rows",
                "trade_truth": "FLF-P04 is_real_trade_bar predicate",
            },
        ),
        contract_metadata={
            **metadata,
            "horizon_steps": horizon_steps,
            "price_field": resolved_price_field,
            "direction": direction.value,
            "same_bar_policy": same_bar_policy.value,
        },
    )
    return PathLabelDefinition(
        name=label_name,
        contract=contract,
        version=contract.derive_label_version(),
        horizon_steps=horizon_steps,
        price_field=resolved_price_field,
        direction=direction,
        same_bar_policy=same_bar_policy,
        target_return=target_return,
        stop_return=stop_return,
    )


def build_path_label_definitions(
    governance_label_specs: Mapping[PathLabelName | str, GovernanceLabelSpec | Mapping[str, Any]],
    *,
    dataset_version_ids: Sequence[str] = (),
    price_field: str | None = None,
) -> tuple[PathLabelDefinition, ...]:
    """Build multiple path-label definitions from governed `LabelSpec` records."""

    return tuple(
        build_path_label_definition(
            name,
            governance_label_spec,
            dataset_version_ids=dataset_version_ids,
            price_field=price_field,
        )
        for name, governance_label_spec in governance_label_specs.items()
    )


def compute_path_label(
    definition: PathLabelDefinition,
    input_view: OHLCVInputView | Iterable[TradeBarRow],
) -> tuple[LabelValueRecord, ...]:
    """Compute one path label as in-memory `LabelValueRecord` objects.

    Synthetic no-trade rows are filtered through `is_real_trade_bar` before any
    excursion or barrier calculation. Rows whose forward path is not yet
    resolvable are omitted rather than emitted with a premature availability
    timestamp.
    """

    definition = _require_definition(definition)
    rows = _real_trade_rows(input_view)
    terminal_by_key = _terminal_by_key(rows)
    roll_calendar_cache: dict[tuple[str, int, int], tuple[RollCalendarRecord, ...]] = {}
    records: list[LabelValueRecord] = []
    for entry_index, entry_row in enumerate(rows):
        outcome = _resolve_path_outcome(
            definition,
            rows,
            entry_index,
            terminal_by_key=terminal_by_key,
            roll_calendar_cache=roll_calendar_cache,
        )
        if outcome is None:
            continue
        records.append(_value_record(definition, entry_row, outcome))
    return tuple(records)


def compute_path_labels(
    definitions: Iterable[PathLabelDefinition],
    input_view: OHLCVInputView | Iterable[TradeBarRow],
) -> dict[PathLabelName, tuple[LabelValueRecord, ...]]:
    """Compute multiple path-label definitions against one canonical OHLCV view."""

    return {
        definition.name: compute_path_label(definition, input_view)
        for definition in definitions
    }


def _resolve_path_outcome(
    definition: PathLabelDefinition,
    rows: tuple[TradeBarRow, ...],
    entry_index: int,
    *,
    terminal_by_key: Mapping[tuple[str, str, datetime], TradeBarRow],
    roll_calendar_cache: dict[tuple[str, int, int], tuple[RollCalendarRecord, ...]],
) -> _PathOutcome | None:
    entry_row = rows[entry_index]
    future_rows = rows[entry_index + 1 : entry_index + 1 + definition.horizon_steps]
    if not future_rows:
        return None
    guarded = _guarded_path_window(
        entry_row,
        future_rows,
        terminal_by_key=terminal_by_key,
        roll_calendar_cache=roll_calendar_cache,
    )
    if guarded is None:
        return None
    future_rows, guard_flags = guarded

    if definition.name is PathLabelName.MFE:
        if len(future_rows) < definition.horizon_steps:
            return None
        value = max(_bar_returns(definition, entry_row, row).favorable for row in future_rows)
        return _PathOutcome(
            value=value,
            resolution_row=future_rows[-1],
            quality_flags=guard_flags,
        )

    if definition.name is PathLabelName.MAE:
        if len(future_rows) < definition.horizon_steps:
            return None
        value = min(_bar_returns(definition, entry_row, row).adverse for row in future_rows)
        return _PathOutcome(
            value=value,
            resolution_row=future_rows[-1],
            quality_flags=guard_flags,
        )

    barrier, resolution_row = _first_barrier(definition, entry_row, future_rows)
    if barrier is None:
        if len(future_rows) < definition.horizon_steps:
            return None
        barrier = PathBarrier.HORIZON
        resolution_row = future_rows[-1]

    if definition.name is PathLabelName.TARGET_BEFORE_STOP:
        target_before_stop_value: bool | None = (
            None if barrier is PathBarrier.AMBIGUOUS else barrier is PathBarrier.TARGET
        )
        return _PathOutcome(
            value=target_before_stop_value,
            resolution_row=resolution_row,
            quality_flags=_merge_quality_flags(_barrier_quality_flags(barrier), guard_flags),
        )
    if definition.name is PathLabelName.TRIPLE_BARRIER:
        return _PathOutcome(
            value=_triple_barrier_value(barrier),
            resolution_row=resolution_row,
            quality_flags=_merge_quality_flags(_barrier_quality_flags(barrier), guard_flags),
        )
    raise PathLabelError(f"unsupported path label: {definition.name}")


def _guarded_path_window(
    entry_row: TradeBarRow,
    future_rows: tuple[TradeBarRow, ...],
    *,
    terminal_by_key: Mapping[tuple[str, str, datetime], TradeBarRow],
    roll_calendar_cache: dict[tuple[str, int, int], tuple[RollCalendarRecord, ...]],
) -> tuple[tuple[TradeBarRow, ...], tuple[str, ...]] | None:
    terminal = future_rows[-1]
    if not _path_segment_is_contract_scoped(entry_row, future_rows):
        return None
    try:
        guarded = _guarded_forward_terminal(
            entry_row,
            terminal,
            terminal_by_key=terminal_by_key,
            roll_calendar_cache=roll_calendar_cache,
        )
    except Exception as exc:  # noqa: BLE001 - normalize shared guard errors for this family.
        raise PathLabelError("path label guard evaluation failed") from exc
    if guarded is None:
        return None
    effective_terminal, guard_flags = guarded
    if _row_key(effective_terminal) == _row_key(terminal):
        return future_rows, guard_flags
    truncated: list[TradeBarRow] = []
    for row in future_rows:
        truncated.append(row)
        if _row_key(row) == _row_key(effective_terminal):
            return tuple(truncated), guard_flags
    return None


def _path_segment_is_contract_scoped(
    entry_row: TradeBarRow,
    future_rows: tuple[TradeBarRow, ...],
) -> bool:
    entry_key = (_series_id(entry_row), _contract_id(entry_row))
    return all((_series_id(row), _contract_id(row)) == entry_key for row in future_rows)


def _terminal_by_key(rows: tuple[TradeBarRow, ...]) -> dict[tuple[str, str, datetime], TradeBarRow]:
    result: dict[tuple[str, str, datetime], TradeBarRow] = {}
    for row in rows:
        key = _row_key(row)
        if key in result:
            raise PathLabelError(
                "path labels require unique rows per series_id, contract_id, and event_ts"
            )
        result[key] = row
    return result


def _row_key(row: TradeBarRow) -> tuple[str, str, datetime]:
    return (_series_id(row), _contract_id(row), _aware_datetime(row.event_ts, "event_ts"))


def _series_id(row: TradeBarRow) -> str:
    value = getattr(row, "series_id", None)
    if not isinstance(value, str) or not value.strip():
        raise PathLabelError("trade row series_id must be a non-empty string")
    return value.strip()


def _contract_id(row: TradeBarRow) -> str:
    value = getattr(row, "contract_id", None)
    if not isinstance(value, str) or not value.strip():
        raise PathLabelError("trade row contract_id must be a non-empty string")
    return value.strip()


def _first_barrier(
    definition: PathLabelDefinition,
    entry_row: TradeBarRow,
    future_rows: tuple[TradeBarRow, ...],
) -> tuple[PathBarrier | None, TradeBarRow]:
    if definition.target_return is None or definition.stop_return is None:
        raise PathLabelError("target and stop returns are required for barrier labels")

    for row in future_rows:
        returns = _bar_returns(definition, entry_row, row)
        hit_target = returns.favorable >= definition.target_return
        hit_stop = returns.adverse <= definition.stop_return
        if hit_target and hit_stop:
            if definition.same_bar_policy is SameBarBarrierPolicy.TARGET_FIRST:
                return PathBarrier.TARGET, row
            if definition.same_bar_policy is SameBarBarrierPolicy.STOP_FIRST:
                return PathBarrier.STOP, row
            return PathBarrier.AMBIGUOUS, row
        if hit_target:
            return PathBarrier.TARGET, row
        if hit_stop:
            return PathBarrier.STOP, row
    return None, future_rows[-1]


def _bar_returns(
    definition: PathLabelDefinition,
    entry_row: TradeBarRow,
    row: TradeBarRow,
) -> _DirectionalReturns:
    entry = _positive_decimal(getattr(entry_row, definition.price_field), definition.price_field)
    high = _positive_decimal(getattr(row, "high"), "high")
    low = _positive_decimal(getattr(row, "low"), "low")
    if definition.direction is PathDirection.LONG:
        favorable = (high - entry) / entry
        adverse = (low - entry) / entry
    else:
        favorable = (entry - low) / entry
        adverse = (entry - high) / entry
    return _DirectionalReturns(favorable=float(favorable), adverse=float(adverse))


def _value_record(
    definition: PathLabelDefinition,
    entry_row: TradeBarRow,
    outcome: _PathOutcome,
) -> LabelValueRecord:
    event_ts = _aware_datetime(getattr(entry_row, "event_ts"), "entry.event_ts")
    resolution_event_ts = _aware_datetime(
        getattr(outcome.resolution_row, "event_ts"),
        "resolution.event_ts",
    )
    resolution_available_ts = _aware_datetime(
        getattr(outcome.resolution_row, "available_ts"),
        "resolution.available_ts",
    )
    label_available_ts = max(
        resolution_event_ts,
        resolution_available_ts,
        definition.contract.availability_policy.availability_time,
    )
    return LabelValueRecord(
        label_version_id=definition.label_version_id,
        entity_id=_entity_id(entry_row),
        event_ts=event_ts,
        horizon_end_ts=resolution_event_ts,
        label_available_ts=label_available_ts,
        value=outcome.value,
        label_contract=definition.contract,
        quality_flags=outcome.quality_flags,
    )


def _real_trade_rows(input_view: OHLCVInputView | Iterable[TradeBarRow]) -> tuple[TradeBarRow, ...]:
    source_rows = input_view.rows if isinstance(input_view, OHLCVInputView) else tuple(input_view)
    rows: list[TradeBarRow] = []
    for row in source_rows:
        if is_real_trade_bar(row):
            _validate_trade_row(row)
            rows.append(row)
    return tuple(sorted(rows, key=lambda row: _aware_datetime(row.event_ts, "event_ts")))


def _validate_trade_row(row: TradeBarRow) -> None:
    _entity_id(row)
    _aware_datetime(getattr(row, "event_ts", None), "event_ts")
    _aware_datetime(getattr(row, "available_ts", None), "available_ts")
    for field_name in ("open", "high", "low", "close"):
        _positive_decimal(getattr(row, field_name, None), field_name)


def _coerce_governance_label_spec(
    value: GovernanceLabelSpec | Mapping[str, Any] | None,
) -> GovernanceLabelSpec:
    if value is None:
        raise PathLabelError("governance LabelSpec is required for path labels")
    try:
        if isinstance(value, GovernanceLabelSpec):
            return GovernanceLabelSpec.from_mapping(value.to_dict())
        if isinstance(value, Mapping):
            return GovernanceLabelSpec.from_mapping(value)
    except ValueError as exc:
        raise PathLabelError("governance LabelSpec is invalid") from exc
    raise PathLabelError("governance LabelSpec must be a LabelSpec or mapping")


def _require_definition(definition: PathLabelDefinition) -> PathLabelDefinition:
    if not isinstance(definition, PathLabelDefinition):
        raise PathLabelError("definition must be a PathLabelDefinition")
    return definition


def _coerce_label_name(value: PathLabelName | str) -> PathLabelName:
    try:
        return value if isinstance(value, PathLabelName) else PathLabelName(str(value))
    except ValueError as exc:
        raise PathLabelError(f"unsupported path label: {value}") from exc


def _direction(value: object) -> PathDirection:
    try:
        return value if isinstance(value, PathDirection) else PathDirection(str(value))
    except ValueError as exc:
        raise PathLabelError("path direction must be 'long' or 'short'") from exc


def _same_bar_policy(value: object) -> SameBarBarrierPolicy:
    try:
        if isinstance(value, SameBarBarrierPolicy):
            return value
        return SameBarBarrierPolicy(str(value))
    except ValueError as exc:
        raise PathLabelError(
            "same_bar_policy must be ambiguous, target_first, or stop_first"
        ) from exc


def _price_field(value: object) -> str:
    if not isinstance(value, str) or value not in _PRICE_FIELDS:
        raise PathLabelError("price_field must be one of open, high, low, close")
    return value


def _label_input_fields(price_field: str) -> tuple[str, ...]:
    fields = ("event_ts", "available_ts", price_field, "high", "low", "quality_flags")
    return tuple(dict.fromkeys(fields))


def _positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PathLabelError(f"{field_name} must be a positive integer")
    return value


def _optional_float(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float | Decimal):
        raise PathLabelError(f"{field_name} must be a finite number")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise PathLabelError(f"{field_name} must be finite")
    return parsed


def _required_target(value: float | None) -> float:
    if value is None or value <= 0:
        raise PathLabelError("target_return must be positive for barrier labels")
    return value


def _required_stop(value: float | None) -> float:
    if value is None or value >= 0:
        raise PathLabelError("stop_return must be negative for barrier labels")
    return value


def _positive_decimal(value: object, field_name: str) -> Decimal:
    if not isinstance(value, Decimal) or value <= 0 or not value.is_finite():
        raise PathLabelError(f"{field_name} must be a positive finite Decimal")
    return value


def _aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise PathLabelError(f"{field_name} must be a timezone-aware datetime")
    return value


def _entity_id(row: TradeBarRow) -> str:
    value = getattr(row, "instrument_id", None)
    if not isinstance(value, str) or not value.strip():
        raise PathLabelError("trade row instrument_id must be a non-empty string")
    return value.strip()


def _barrier_quality_flags(barrier: PathBarrier) -> tuple[str, ...]:
    if barrier is PathBarrier.HORIZON:
        return ("horizon_no_barrier",)
    if barrier is PathBarrier.AMBIGUOUS:
        return ("ambiguous_same_bar_barrier",)
    return ()


def _merge_quality_flags(*groups: Sequence[str]) -> tuple[str, ...]:
    flags: list[str] = []
    for group in groups:
        for flag in group:
            if not isinstance(flag, str) or not flag.strip():
                raise PathLabelError("quality_flags must contain non-empty strings")
            token = flag.strip().lower()
            if token not in flags:
                flags.append(token)
    return tuple(flags)


def _materialization_scope_metadata(
    value: Mapping[str, Any] | None,
) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise PathLabelError("materialization_scope must be a mapping")
    scope: dict[str, str] = {}
    for key, item in value.items():
        key_text = _metadata_text(key, "materialization_scope key")
        item_text = _metadata_text(item, f"materialization_scope.{key_text}")
        scope[key_text] = item_text
    return dict(sorted(scope.items()))


def _metadata_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise PathLabelError(f"{field_name} must be a string")
    text = value.strip()
    if not text:
        raise PathLabelError(f"{field_name} must be a non-empty string")
    return text


def _triple_barrier_value(barrier: PathBarrier) -> int | None:
    if barrier is PathBarrier.TARGET:
        return 1
    if barrier is PathBarrier.STOP:
        return -1
    if barrier is PathBarrier.HORIZON:
        return 0
    if barrier is PathBarrier.AMBIGUOUS:
        return None
    raise PathLabelError(f"unsupported barrier outcome: {barrier}")


__all__ = [
    "PathBarrier",
    "PathDirection",
    "PathLabelDefinition",
    "PathLabelError",
    "PathLabelName",
    "SameBarBarrierPolicy",
    "build_path_label_definition",
    "build_path_label_definitions",
    "compute_path_label",
    "compute_path_labels",
    "supported_path_labels",
]
