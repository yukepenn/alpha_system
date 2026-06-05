"""Strategy-agnostic event outcome labels.

The family consumes governed ``LabelSpec`` records through the FLF-P16 label
contract surface and canonical input views only. It returns in-memory
``LabelValueRecord`` objects; it does not materialize values, read provider
files, expose labels as live features, or implement strategy logic.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Any

from alpha_system.data.foundation.quotes import (
    BBO_QUARANTINE_QUALITY_FLAG,
    MISSING_BBO_QUALITY_FLAG,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.features.contracts import WindowCausality, WindowKind, WindowSpec
from alpha_system.features.input_views import (
    BBOInputRow,
    BBOInputView,
    CanonicalInputViews,
    OHLCVInputView,
)
from alpha_system.features.semantics import TradeBarRow, bbo_quote_semantics, is_real_trade_bar
from alpha_system.governance.label_spec import LabelSpec as GovernanceLabelSpec
from alpha_system.labels.version import (
    LabelContractSpec,
    LabelFamily,
    LabelInputSpec,
    LabelValueRecord,
    LabelVersion,
)


class EventLabelError(ValueError):
    """Raised when event-label definition or computation fails closed."""


class EventLabelName(StrEnum):
    """Supported FLF-P20 strategy-agnostic event labels."""

    BREAKOUT_SUCCESS = "breakout_success"
    RETURN_TO_VWAP = "return_to_vwap"
    SWEEP_OUTCOME = "sweep_outcome"
    LIQUIDITY_QUALITY_FUTURE = "liquidity_quality_future"


class EventDirection(StrEnum):
    """Neutral event direction used to interpret future path outcomes."""

    UP = "up"
    DOWN = "down"


class SweepSide(StrEnum):
    """Neutral side swept by an event."""

    BUY_SIDE = "buy_side"
    SELL_SIDE = "sell_side"


@dataclass(frozen=True, slots=True)
class EventLabelDefinition:
    """Approved, versioned event-label definition bound to a governance `LabelSpec`."""

    name: EventLabelName
    contract: LabelContractSpec
    version: LabelVersion
    horizon_steps: int
    horizon_minutes: int
    direction: EventDirection = EventDirection.UP
    sweep_side: SweepSide = SweepSide.BUY_SIDE
    success_return: float | None = None
    failure_return: float | None = None
    vwap_price: Decimal | None = None
    vwap_tolerance_bps: Decimal = Decimal("0")
    continuation_return: float | None = None
    reversal_return: float | None = None
    max_mean_spread_bps: Decimal | None = None

    @property
    def label_id(self) -> str:
        """Return the stable governed label id."""

        return self.contract.label_id

    @property
    def label_version_id(self) -> str:
        """Return the deterministic label-version id."""

        return self.version.label_version_id

    @property
    def label_spec_id(self) -> str:
        """Return the bound governance `lspec_` id."""

        return self.contract.label_spec_id

    def validate_not_live_feature(self, feature_references: Any) -> object:
        """Fail closed if this label is reachable as a live feature input."""

        return self.contract.validate_live_feature_references(feature_references)


@dataclass(frozen=True, slots=True)
class _EventOutcome:
    value: bool | str | None
    resolution_row: TradeBarRow
    quality_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _LiquidityOutcome:
    value: bool | None
    horizon_end_ts: datetime
    label_available_ts: datetime
    quality_flags: tuple[str, ...] = ()


_NUMERIC_TYPES = (int, float, Decimal)
_TRADE_LABELS = frozenset(
    {
        EventLabelName.BREAKOUT_SUCCESS,
        EventLabelName.RETURN_TO_VWAP,
        EventLabelName.SWEEP_OUTCOME,
    }
)
_EVENT_INPUT_FIELDS: tuple[str, ...] = (
    "instrument_id",
    "series_id",
    "event_ts",
    "available_ts",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quality_flags",
)
_BBO_INPUT_FIELDS: tuple[str, ...] = (
    "series_id",
    "event_ts",
    "available_ts",
    "bid",
    "ask",
    "mid",
    "spread",
    "bid_size",
    "ask_size",
    "quality_flags",
)


def supported_event_labels() -> tuple[EventLabelName, ...]:
    """Return the complete FLF-P20 event-label list."""

    return tuple(EventLabelName)


def build_event_label_definition(
    name: EventLabelName | str,
    governance_label_spec: GovernanceLabelSpec | Mapping[str, Any] | None,
    *,
    dataset_version_ids: Sequence[str] = (),
) -> EventLabelDefinition:
    """Build one governed strategy-agnostic event label definition.

    A valid governance ``LabelSpec`` is required before a label contract or
    version can be derived. Missing or invalid ``lspec_`` bindings fail closed
    through the consumed FLF-P16 contract layer.
    """

    label_name = _coerce_label_name(name)
    spec = _coerce_governance_label_spec(governance_label_spec)
    _validate_label_spec_matches_name(label_name, spec)

    horizon_steps = _positive_int(spec.path_rules.get("horizon_steps"), "path_rules.horizon_steps")
    horizon_minutes = _horizon_minutes(spec, horizon_steps)
    direction = _direction(spec.path_rules.get("direction", "up"))
    sweep_side = _sweep_side(spec.path_rules.get("sweep_side", "buy_side"))
    success_return = _optional_non_negative_float(
        spec.target_stop_rules.get("success_return"),
        "target_stop_rules.success_return",
    )
    failure_return = _optional_non_negative_float(
        spec.target_stop_rules.get("failure_return"),
        "target_stop_rules.failure_return",
    )
    continuation_return = _optional_non_negative_float(
        spec.target_stop_rules.get("continuation_return"),
        "target_stop_rules.continuation_return",
    )
    reversal_return = _optional_non_negative_float(
        spec.target_stop_rules.get("reversal_return"),
        "target_stop_rules.reversal_return",
    )
    vwap_price = _optional_positive_decimal(
        spec.path_rules.get("vwap_price"),
        "path_rules.vwap_price",
    )
    vwap_tolerance_bps = _non_negative_decimal(
        spec.path_rules.get("vwap_tolerance_bps", 0),
        "path_rules.vwap_tolerance_bps",
    )
    max_mean_spread_bps = _optional_non_negative_decimal(
        spec.target_stop_rules.get("max_mean_spread_bps"),
        "target_stop_rules.max_mean_spread_bps",
    )

    _validate_parameters(
        label_name,
        success_return=success_return,
        failure_return=failure_return,
        continuation_return=continuation_return,
        reversal_return=reversal_return,
        vwap_price=vwap_price,
        max_mean_spread_bps=max_mean_spread_bps,
    )

    contract = LabelContractSpec.from_label_spec(
        label_id=label_name.value,
        family=LabelFamily.EVENT,
        governance_label_spec=spec,
        inputs=_label_inputs(label_name, dataset_version_ids),
        window=_future_window(label_name, horizon_steps, horizon_minutes),
        contract_metadata={
            "campaign": "ALPHA_FEATURE_LABEL_FOUNDATION_V1",
            "phase": "FLF-P20",
            "label_family": LabelFamily.EVENT.value,
            "label_name": label_name.value,
            "horizon_steps": horizon_steps,
            "horizon_minutes": horizon_minutes,
            "materialization": "in_memory_records_only",
            "legal_consumer": "labels_only",
            "claims": "descriptive_label_substrate_only",
        },
    )
    return EventLabelDefinition(
        name=label_name,
        contract=contract,
        version=contract.derive_label_version(),
        horizon_steps=horizon_steps,
        horizon_minutes=horizon_minutes,
        direction=direction,
        sweep_side=sweep_side,
        success_return=success_return,
        failure_return=failure_return,
        vwap_price=vwap_price,
        vwap_tolerance_bps=vwap_tolerance_bps,
        continuation_return=continuation_return,
        reversal_return=reversal_return,
        max_mean_spread_bps=max_mean_spread_bps,
    )


def build_event_label_definitions(
    governance_label_specs: Mapping[EventLabelName | str, GovernanceLabelSpec | Mapping[str, Any]],
    *,
    dataset_version_ids: Sequence[str] = (),
) -> tuple[EventLabelDefinition, ...]:
    """Build multiple governed FLF-P20 event-label definitions."""

    if not isinstance(governance_label_specs, Mapping):
        raise EventLabelError("governance_label_specs must be a mapping")
    return tuple(
        build_event_label_definition(
            name,
            governance_label_spec,
            dataset_version_ids=dataset_version_ids,
        )
        for name, governance_label_spec in governance_label_specs.items()
    )


def compute_event_label(
    definition: EventLabelDefinition,
    input_view: OHLCVInputView | BBOInputView | CanonicalInputViews,
    *,
    event_rows: Iterable[TradeBarRow] | None = None,
) -> tuple[LabelValueRecord, ...]:
    """Compute one event label as in-memory ``LabelValueRecord`` objects.

    Event anchors and trade-path outcomes use only FLF-P04 real trade bars.
    Synthetic no-trade rows are not event anchors or future outcome bars. BBO
    outcomes use exact future BBO rows and flag missing/quarantined rows without
    forward filling.
    """

    definition = _require_definition(definition)
    if definition.name is EventLabelName.LIQUIDITY_QUALITY_FUTURE:
        return _compute_liquidity_quality_future(definition, input_view, event_rows=event_rows)
    return _compute_trade_event_label(definition, input_view, event_rows=event_rows)


def compute_event_labels(
    definitions: Iterable[EventLabelDefinition],
    input_view: OHLCVInputView | BBOInputView | CanonicalInputViews,
    *,
    event_rows: Iterable[TradeBarRow] | None = None,
) -> dict[EventLabelName, tuple[LabelValueRecord, ...]]:
    """Compute multiple governed event-label definitions against one input view."""

    return {
        definition.name: compute_event_label(definition, input_view, event_rows=event_rows)
        for definition in definitions
    }


def _compute_trade_event_label(
    definition: EventLabelDefinition,
    input_view: OHLCVInputView | BBOInputView | CanonicalInputViews,
    *,
    event_rows: Iterable[TradeBarRow] | None,
) -> tuple[LabelValueRecord, ...]:
    source_rows = event_rows if event_rows is not None else _coerce_ohlcv_view(input_view).rows
    rows = _real_trade_rows(source_rows)
    records: list[LabelValueRecord] = []
    for series_rows in _rows_by_series(rows).values():
        for event_index, event_row in enumerate(series_rows):
            future_rows = series_rows[event_index + 1 : event_index + 1 + definition.horizon_steps]
            outcome = _resolve_trade_outcome(definition, event_row, future_rows)
            if outcome is None:
                continue
            records.append(_trade_value_record(definition, event_row, outcome))
    return tuple(records)


def _compute_liquidity_quality_future(
    definition: EventLabelDefinition,
    input_view: OHLCVInputView | BBOInputView | CanonicalInputViews,
    *,
    event_rows: Iterable[TradeBarRow] | None,
) -> tuple[LabelValueRecord, ...]:
    source_rows = event_rows if event_rows is not None else _coerce_ohlcv_view(input_view).rows
    trade_rows = _real_trade_rows(source_rows)
    bbo_rows = _validated_bbo_rows(_coerce_bbo_view(input_view).rows)
    bbo_by_series_event = _bbo_rows_by_series_event_ts(bbo_rows)
    records: list[LabelValueRecord] = []
    for event_row in trade_rows:
        outcome = _resolve_liquidity_outcome(
            definition,
            event_row,
            bbo_by_series_event=bbo_by_series_event,
        )
        records.append(_liquidity_value_record(definition, event_row, outcome))
    return tuple(records)


def _resolve_trade_outcome(
    definition: EventLabelDefinition,
    event_row: TradeBarRow,
    future_rows: tuple[TradeBarRow, ...],
) -> _EventOutcome | None:
    if not future_rows:
        return None
    if definition.name is EventLabelName.BREAKOUT_SUCCESS:
        return _breakout_success(definition, event_row, future_rows)
    if definition.name is EventLabelName.RETURN_TO_VWAP:
        return _return_to_vwap(definition, event_row, future_rows)
    if definition.name is EventLabelName.SWEEP_OUTCOME:
        return _sweep_outcome(definition, event_row, future_rows)
    raise EventLabelError(f"unsupported trade event label: {definition.name}")


def _breakout_success(
    definition: EventLabelDefinition,
    event_row: TradeBarRow,
    future_rows: tuple[TradeBarRow, ...],
) -> _EventOutcome | None:
    success_return = _required_float(definition.success_return, "success_return")
    failure_return = _required_float(definition.failure_return, "failure_return")
    entry = _positive_decimal(event_row.close, "event.close")

    for row in future_rows:
        high = _positive_decimal(row.high, "future.high")
        low = _positive_decimal(row.low, "future.low")
        if definition.direction is EventDirection.UP:
            hit_failure = low <= entry * Decimal(str(1 - failure_return))
            hit_success = high >= entry * Decimal(str(1 + success_return))
        else:
            hit_failure = high >= entry * Decimal(str(1 + failure_return))
            hit_success = low <= entry * Decimal(str(1 - success_return))
        if hit_failure:
            return _EventOutcome(
                value=False,
                resolution_row=row,
                quality_flags=("breakout_failed",),
            )
        if hit_success:
            return _EventOutcome(
                value=True,
                resolution_row=row,
                quality_flags=("breakout_success",),
            )

    if len(future_rows) < definition.horizon_steps:
        return None
    return _EventOutcome(
        value=False,
        resolution_row=future_rows[-1],
        quality_flags=("horizon_no_breakout_success",),
    )


def _return_to_vwap(
    definition: EventLabelDefinition,
    event_row: TradeBarRow,
    future_rows: tuple[TradeBarRow, ...],
) -> _EventOutcome | None:
    vwap_price = _required_decimal(definition.vwap_price, "vwap_price")
    tolerance = vwap_price * definition.vwap_tolerance_bps / Decimal("10000")
    event_close = _positive_decimal(event_row.close, "event.close")
    started_above_vwap = event_close >= vwap_price

    for row in future_rows:
        high = _positive_decimal(row.high, "future.high")
        low = _positive_decimal(row.low, "future.low")
        touched = (
            low <= vwap_price + tolerance
            if started_above_vwap
            else high >= vwap_price - tolerance
        )
        if touched:
            return _EventOutcome(
                value=True,
                resolution_row=row,
                quality_flags=("returned_to_vwap",),
            )

    if len(future_rows) < definition.horizon_steps:
        return None
    return _EventOutcome(
        value=False,
        resolution_row=future_rows[-1],
        quality_flags=("horizon_no_return_to_vwap",),
    )


def _sweep_outcome(
    definition: EventLabelDefinition,
    event_row: TradeBarRow,
    future_rows: tuple[TradeBarRow, ...],
) -> _EventOutcome | None:
    continuation_return = _required_float(definition.continuation_return, "continuation_return")
    reversal_return = _required_float(definition.reversal_return, "reversal_return")
    anchor = _positive_decimal(event_row.close, "event.close")

    for row in future_rows:
        high = _positive_decimal(row.high, "future.high")
        low = _positive_decimal(row.low, "future.low")
        if definition.sweep_side is SweepSide.BUY_SIDE:
            hit_reversal = low <= anchor * Decimal(str(1 - reversal_return))
            hit_continuation = high >= anchor * Decimal(str(1 + continuation_return))
        else:
            hit_reversal = high >= anchor * Decimal(str(1 + reversal_return))
            hit_continuation = low <= anchor * Decimal(str(1 - continuation_return))
        if hit_reversal:
            return _EventOutcome(
                value="reversal",
                resolution_row=row,
                quality_flags=("sweep_reversal",),
            )
        if hit_continuation:
            return _EventOutcome(
                value="continuation",
                resolution_row=row,
                quality_flags=("sweep_continuation",),
            )

    if len(future_rows) < definition.horizon_steps:
        return None
    return _EventOutcome(
        value="unresolved",
        resolution_row=future_rows[-1],
        quality_flags=("horizon_sweep_unresolved",),
    )


def _resolve_liquidity_outcome(
    definition: EventLabelDefinition,
    event_row: TradeBarRow,
    *,
    bbo_by_series_event: Mapping[tuple[str, datetime], BBOInputRow],
) -> _LiquidityOutcome:
    event_ts = _aware_datetime(event_row.event_ts, "event.event_ts")
    event_available_ts = _aware_datetime(event_row.available_ts, "event.available_ts")
    horizon_end_ts = event_ts + timedelta(minutes=definition.horizon_minutes)
    expected_event_ts = tuple(
        event_ts + timedelta(minutes=offset)
        for offset in range(1, definition.horizon_minutes + 1)
    )
    future_bbo_rows = tuple(
        bbo_by_series_event.get((_series_id(event_row), future_ts))
        for future_ts in expected_event_ts
    )
    missing_timestamps = tuple(
        expected_ts
        for expected_ts, row in zip(expected_event_ts, future_bbo_rows, strict=True)
        if row is None
    )
    if missing_timestamps:
        return _LiquidityOutcome(
            value=None,
            horizon_end_ts=horizon_end_ts,
            label_available_ts=_label_available_ts_from_candidates(
                definition,
                horizon_end_ts,
                event_available_ts,
            ),
            quality_flags=("bbo_gap", "missing_future_bbo"),
        )

    rows = tuple(row for row in future_bbo_rows if row is not None)
    gap_flags: set[str] = set()
    for row in rows:
        if not _is_valid_bbo_quote(row):
            gap_flags.update(("bbo_gap", "future_bbo_gap", *_bbo_gap_flags(row)))
    if gap_flags:
        return _LiquidityOutcome(
            value=None,
            horizon_end_ts=horizon_end_ts,
            label_available_ts=_label_available_ts_from_candidates(
                definition,
                horizon_end_ts,
                *(row.available_ts for row in rows),
                event_available_ts,
            ),
            quality_flags=tuple(sorted(gap_flags)),
        )

    max_mean_spread_bps = _required_decimal(
        definition.max_mean_spread_bps,
        "max_mean_spread_bps",
    )
    spread_bps_values = tuple(_spread_bps(row) for row in rows)
    mean_spread_bps = sum(spread_bps_values, Decimal("0")) / Decimal(len(spread_bps_values))
    return _LiquidityOutcome(
        value=mean_spread_bps <= max_mean_spread_bps,
        horizon_end_ts=horizon_end_ts,
        label_available_ts=_label_available_ts_from_candidates(
            definition,
            horizon_end_ts,
            *(row.available_ts for row in rows),
            event_available_ts,
        ),
        quality_flags=("future_liquidity_within_threshold",)
        if mean_spread_bps <= max_mean_spread_bps
        else ("future_liquidity_wide",),
    )


def _trade_value_record(
    definition: EventLabelDefinition,
    event_row: TradeBarRow,
    outcome: _EventOutcome,
) -> LabelValueRecord:
    event_ts = _aware_datetime(event_row.event_ts, "event.event_ts")
    resolution_ts = _aware_datetime(outcome.resolution_row.event_ts, "resolution.event_ts")
    return LabelValueRecord(
        label_version_id=definition.label_version_id,
        entity_id=_entity_id(event_row),
        event_ts=event_ts,
        horizon_end_ts=resolution_ts,
        label_available_ts=_label_available_ts_from_candidates(
            definition,
            resolution_ts,
            _aware_datetime(outcome.resolution_row.available_ts, "resolution.available_ts"),
        ),
        value=outcome.value,
        label_contract=definition.contract,
        quality_flags=outcome.quality_flags,
    )


def _liquidity_value_record(
    definition: EventLabelDefinition,
    event_row: TradeBarRow,
    outcome: _LiquidityOutcome,
) -> LabelValueRecord:
    return LabelValueRecord(
        label_version_id=definition.label_version_id,
        entity_id=_entity_id(event_row),
        event_ts=_aware_datetime(event_row.event_ts, "event.event_ts"),
        horizon_end_ts=outcome.horizon_end_ts,
        label_available_ts=outcome.label_available_ts,
        value=outcome.value,
        label_contract=definition.contract,
        quality_flags=outcome.quality_flags,
    )


def _label_available_ts_from_candidates(
    definition: EventLabelDefinition,
    horizon_end_ts: datetime,
    *available_candidates: datetime,
) -> datetime:
    candidates = [
        _aware_datetime(horizon_end_ts, "horizon_end_ts"),
        definition.contract.availability_policy.availability_time,
    ]
    candidates.extend(
        _aware_datetime(candidate, "available_ts") for candidate in available_candidates
    )
    return max(candidates)


def _label_inputs(
    name: EventLabelName,
    dataset_version_ids: Sequence[str],
) -> LabelInputSpec:
    dataset_ids = _text_tuple(dataset_version_ids, "dataset_version_ids", allow_empty=True)
    if name is EventLabelName.LIQUIDITY_QUALITY_FUTURE:
        return LabelInputSpec(
            input_views=("canonical_ohlcv", "dense_grid_ohlcv", "canonical_bbo"),
            fields=tuple(dict.fromkeys((*_EVENT_INPUT_FIELDS, *_BBO_INPUT_FIELDS))),
            dataset_version_ids=dataset_ids,
            input_metadata={
                "consumption_surface": "CanonicalInputViews",
                "event_policy": "event anchors must satisfy is_real_trade_bar",
                "bbo_quality_tokens": [
                    MISSING_BBO_QUALITY_FLAG,
                    BBO_QUARANTINE_QUALITY_FLAG,
                ],
                "quote_policy": (
                    "future BBO rows are exact event_ts rows; missing_bbo and "
                    "bbo_quarantined rows are flagged and never forward-filled"
                ),
            },
        )
    return LabelInputSpec(
        input_views=("canonical_ohlcv", "dense_grid_ohlcv"),
        fields=_EVENT_INPUT_FIELDS,
        dataset_version_ids=dataset_ids,
        input_metadata={
            "consumption_surface": "OHLCVInputView or explicit event_rows",
            "event_policy": "event anchors and outcomes must satisfy is_real_trade_bar",
            "dense_grid_policy": (
                "synthetic no-trade rows are excluded from event and outcome detection"
            ),
        },
    )


def _future_window(
    name: EventLabelName,
    horizon_steps: int,
    horizon_minutes: int,
) -> WindowSpec:
    return WindowSpec(
        kind=WindowKind.FUTURE,
        length=horizon_steps,
        causality=WindowCausality.FUTURE,
        offline_only=True,
        anchor="event_ts",
        parameters={
            "horizon_steps": horizon_steps,
            "horizon_minutes": horizon_minutes,
            "event_label": name.value,
            "legal_consumer": "labels_only",
        },
    )


def _validate_label_spec_matches_name(
    name: EventLabelName,
    spec: GovernanceLabelSpec,
) -> None:
    expected = name.value
    actual = spec.path_rules.get("event_label")
    if actual != expected:
        raise EventLabelError(f"LabelSpec.path_rules.event_label must be {expected}")
    path = spec.path_rules.get("path")
    if path != "strategy_agnostic_event_outcome":
        raise EventLabelError(
            "LabelSpec.path_rules.path must be strategy_agnostic_event_outcome"
        )


def _validate_parameters(
    name: EventLabelName,
    *,
    success_return: float | None,
    failure_return: float | None,
    continuation_return: float | None,
    reversal_return: float | None,
    vwap_price: Decimal | None,
    max_mean_spread_bps: Decimal | None,
) -> None:
    if name is EventLabelName.BREAKOUT_SUCCESS:
        _required_float(success_return, "success_return")
        _required_float(failure_return, "failure_return")
    elif name is EventLabelName.RETURN_TO_VWAP:
        _required_decimal(vwap_price, "vwap_price")
    elif name is EventLabelName.SWEEP_OUTCOME:
        _required_float(continuation_return, "continuation_return")
        _required_float(reversal_return, "reversal_return")
    elif name is EventLabelName.LIQUIDITY_QUALITY_FUTURE:
        _required_decimal(max_mean_spread_bps, "max_mean_spread_bps")
    else:
        raise EventLabelError(f"unsupported event label: {name}")


def _coerce_governance_label_spec(
    value: GovernanceLabelSpec | Mapping[str, Any] | None,
) -> GovernanceLabelSpec:
    if value is None:
        raise EventLabelError("governance LabelSpec lspec_ binding is required")
    try:
        if isinstance(value, GovernanceLabelSpec):
            return GovernanceLabelSpec.from_mapping(value.to_dict())
        if isinstance(value, Mapping):
            return GovernanceLabelSpec.from_mapping(value)
    except ValueError as exc:
        raise EventLabelError("governance LabelSpec lspec_ binding is invalid") from exc
    raise EventLabelError("governance LabelSpec must be a LabelSpec or mapping")


def _require_definition(definition: EventLabelDefinition) -> EventLabelDefinition:
    if not isinstance(definition, EventLabelDefinition):
        raise EventLabelError("definition must be an EventLabelDefinition")
    if definition.contract.family is not LabelFamily.EVENT:
        raise EventLabelError("definition must belong to LabelFamily.EVENT")
    if definition.version != definition.contract.derive_label_version():
        raise EventLabelError("definition LabelVersion does not match LabelContractSpec")
    if not definition.contract.availability_policy.future_data_legal_only_for_labels:
        raise EventLabelError("event-label future data must be labels-only")
    return definition


def _coerce_ohlcv_view(
    input_view: OHLCVInputView | BBOInputView | CanonicalInputViews,
) -> OHLCVInputView:
    if isinstance(input_view, CanonicalInputViews):
        return input_view.ohlcv
    if isinstance(input_view, OHLCVInputView):
        return input_view
    raise EventLabelError("trade event labels require an OHLCVInputView")


def _coerce_bbo_view(
    input_view: OHLCVInputView | BBOInputView | CanonicalInputViews,
) -> BBOInputView:
    if isinstance(input_view, CanonicalInputViews):
        return input_view.bbo
    if isinstance(input_view, BBOInputView):
        return input_view
    raise EventLabelError("liquidity event labels require a BBOInputView or CanonicalInputViews")


def _real_trade_rows(rows: Iterable[TradeBarRow]) -> tuple[TradeBarRow, ...]:
    real_rows: list[TradeBarRow] = []
    for row in rows:
        try:
            if not is_real_trade_bar(row):
                continue
        except DataFoundationValidationError as exc:
            raise EventLabelError(str(exc)) from exc
        _validate_trade_row(row)
        real_rows.append(row)
    return tuple(sorted(real_rows, key=lambda row: (_series_id(row), row.event_ts)))


def _validate_trade_row(row: TradeBarRow) -> None:
    _entity_id(row)
    _series_id(row)
    _aware_datetime(getattr(row, "event_ts", None), "event_ts")
    _aware_datetime(getattr(row, "available_ts", None), "available_ts")
    for field_name in ("open", "high", "low", "close"):
        _positive_decimal(getattr(row, field_name, None), field_name)


def _validated_bbo_rows(rows: Sequence[BBOInputRow]) -> tuple[BBOInputRow, ...]:
    ordered = tuple(rows)
    for row in ordered:
        if not isinstance(row, BBOInputRow):
            raise EventLabelError("liquidity event labels require BBOInputRow inputs")
        _series_id(row)
        _aware_datetime(row.event_ts, "BBOInputRow.event_ts")
        _aware_datetime(row.available_ts, "BBOInputRow.available_ts")
        _non_negative_decimal(row.mid, "BBOInputRow.mid")
        _non_negative_decimal(row.spread, "BBOInputRow.spread")
        _quality_flags(row.quality_flags)
    return tuple(sorted(ordered, key=lambda row: (row.series_id, row.event_ts, row.available_ts)))


def _rows_by_series(rows: Sequence[TradeBarRow]) -> dict[str, tuple[TradeBarRow, ...]]:
    grouped: dict[str, list[TradeBarRow]] = {}
    for row in rows:
        grouped.setdefault(_series_id(row), []).append(row)
    return {
        series_id: tuple(sorted(series_rows, key=lambda row: row.event_ts))
        for series_id, series_rows in grouped.items()
    }


def _bbo_rows_by_series_event_ts(
    rows: Sequence[BBOInputRow],
) -> dict[tuple[str, datetime], BBOInputRow]:
    by_key: dict[tuple[str, datetime], BBOInputRow] = {}
    for row in rows:
        key = (row.series_id, row.event_ts)
        if key in by_key:
            raise EventLabelError("BBO rows must not duplicate series_id/event_ts")
        by_key[key] = row
    return by_key


def _is_valid_bbo_quote(row: BBOInputRow) -> bool:
    semantics = _quote_semantics(row)
    return not semantics.missing_or_abnormal and semantics.invariants_hold


def _quote_semantics(row: BBOInputRow):
    try:
        return bbo_quote_semantics(row)
    except DataFoundationValidationError as exc:
        raise EventLabelError(str(exc)) from exc


def _bbo_gap_flags(row: BBOInputRow) -> tuple[str, ...]:
    semantics = _quote_semantics(row)
    flags = {"bbo_gap", *_quality_flags(row.quality_flags)}
    if semantics.missing_bbo:
        flags.add(MISSING_BBO_QUALITY_FLAG)
    if semantics.bbo_quarantined:
        flags.add(BBO_QUARANTINE_QUALITY_FLAG)
    if not semantics.invariants_hold:
        flags.add("bbo_invariant_violation")
    return tuple(sorted(flags))


def _spread_bps(row: BBOInputRow) -> Decimal:
    mid = _positive_decimal(row.mid, "BBOInputRow.mid")
    spread = _non_negative_decimal(row.spread, "BBOInputRow.spread")
    return spread / mid * Decimal("10000")


def _coerce_label_name(value: EventLabelName | str) -> EventLabelName:
    try:
        return value if isinstance(value, EventLabelName) else EventLabelName(str(value))
    except ValueError as exc:
        raise EventLabelError(f"unsupported event label: {value}") from exc


def _direction(value: object) -> EventDirection:
    try:
        return value if isinstance(value, EventDirection) else EventDirection(str(value))
    except ValueError as exc:
        raise EventLabelError("path_rules.direction must be 'up' or 'down'") from exc


def _sweep_side(value: object) -> SweepSide:
    try:
        return value if isinstance(value, SweepSide) else SweepSide(str(value))
    except ValueError as exc:
        raise EventLabelError("path_rules.sweep_side must be buy_side or sell_side") from exc


def _horizon_minutes(spec: GovernanceLabelSpec, horizon_steps: int) -> int:
    value = spec.path_rules.get("horizon_minutes")
    if value is None:
        parsed = _horizon_minutes_from_text(spec.horizon)
        return parsed if parsed is not None else horizon_steps
    return _positive_int(value, "path_rules.horizon_minutes")


def _horizon_minutes_from_text(value: str) -> int | None:
    if not isinstance(value, str):
        return None
    text = value.strip().lower()
    if not text.endswith("m"):
        return None
    try:
        parsed = int(text[:-1])
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise EventLabelError(f"{field_name} must be a positive integer")
    return value


def _required_float(value: float | None, field_name: str) -> float:
    if value is None:
        raise EventLabelError(f"{field_name} is required")
    return value


def _optional_non_negative_float(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    parsed = _to_float(value, field_name)
    if parsed < 0:
        raise EventLabelError(f"{field_name} must be non-negative")
    return parsed


def _required_decimal(value: Decimal | None, field_name: str) -> Decimal:
    if value is None:
        raise EventLabelError(f"{field_name} is required")
    return value


def _optional_positive_decimal(value: object, field_name: str) -> Decimal | None:
    if value is None:
        return None
    return _positive_decimal(value, field_name)


def _optional_non_negative_decimal(value: object, field_name: str) -> Decimal | None:
    if value is None:
        return None
    return _non_negative_decimal(value, field_name)


def _positive_decimal(value: object, field_name: str) -> Decimal:
    parsed = _decimal(value, field_name)
    if parsed <= 0:
        raise EventLabelError(f"{field_name} must be positive")
    return parsed


def _non_negative_decimal(value: object, field_name: str) -> Decimal:
    parsed = _decimal(value, field_name)
    if parsed < 0:
        raise EventLabelError(f"{field_name} must be non-negative")
    return parsed


def _decimal(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, _NUMERIC_TYPES):
        raise EventLabelError(f"{field_name} must be numeric")
    parsed = Decimal(str(value))
    if not parsed.is_finite():
        raise EventLabelError(f"{field_name} must be finite")
    return parsed


def _to_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, _NUMERIC_TYPES):
        raise EventLabelError(f"{field_name} must be numeric")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise EventLabelError(f"{field_name} must be finite")
    return parsed


def _aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise EventLabelError(f"{field_name} must be a timezone-aware datetime")
    return value


def _entity_id(row: TradeBarRow) -> str:
    value = getattr(row, "instrument_id", None)
    if not isinstance(value, str) or not value.strip():
        raise EventLabelError("event row instrument_id must be a non-empty string")
    return value.strip()


def _series_id(row: TradeBarRow | BBOInputRow) -> str:
    value = getattr(row, "series_id", None)
    if not isinstance(value, str) or not value.strip():
        raise EventLabelError("row series_id must be a non-empty string")
    return value.strip()


def _quality_flags(flags: Sequence[str]) -> tuple[str, ...]:
    if isinstance(flags, str) or not isinstance(flags, Sequence):
        raise EventLabelError("quality_flags must be a sequence of strings")
    normalized: list[str] = []
    for flag in flags:
        if not isinstance(flag, str) or not flag.strip():
            raise EventLabelError("quality_flags must contain non-empty strings")
        token = flag.strip().lower()
        if token not in normalized:
            normalized.append(token)
    return tuple(normalized)


def _text_tuple(
    values: Sequence[str],
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise EventLabelError(f"{field_name} must be a sequence of strings")
    normalized = tuple(_text(value, f"{field_name}[]") for value in values)
    if not normalized and not allow_empty:
        raise EventLabelError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise EventLabelError(f"{field_name} must not contain duplicates")
    return normalized


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EventLabelError(f"{field_name} must be a non-empty string")
    return value.strip()


__all__ = [
    "EventDirection",
    "EventLabelDefinition",
    "EventLabelError",
    "EventLabelName",
    "SweepSide",
    "build_event_label_definition",
    "build_event_label_definitions",
    "compute_event_label",
    "compute_event_labels",
    "supported_event_labels",
]
