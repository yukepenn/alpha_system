"""Cost-adjusted and spread-adjusted forward-return labels.

This module computes in-memory label value records from canonical BBO input
views only. It binds every label definition to a governed FLF-P16
``LabelContractSpec`` and does not materialize, register, persist, or expose
labels as live features.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Any

from alpha_system.data.foundation.grid import DenseGridBarRecord
from alpha_system.data.foundation.quotes import (
    BBO_QUARANTINE_QUALITY_FLAG,
    MISSING_BBO_QUALITY_FLAG,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
from alpha_system.features.input_views import (
    BBOInputRow,
    BBOInputView,
    CanonicalInputViews,
    OHLCVInputRow,
)
from alpha_system.features.semantics import bbo_quote_semantics, is_synthetic_no_trade_bar
from alpha_system.governance.label_spec import LabelSpec as GovernanceLabelSpec
from alpha_system.labels.families.fixed_horizon import (
    MAINTENANCE_GUARD_VERSION,
    MAINTENANCE_POLICY_ID,
)
from alpha_system.labels.families.fixed_horizon.family import (
    _guarded_forward_terminal,
)
from alpha_system.labels.roll_guard import (
    DEFAULT_CROSS_ROLL_POLICY,
    DEFAULT_ROLL_WINDOW_DAYS_AFTER,
    DEFAULT_ROLL_WINDOW_DAYS_BEFORE,
    ROLL_GUARD_VERSION,
    ROLL_POLICY_ID,
)
from alpha_system.labels.version import (
    CostAdjustmentSpec,
    LabelContractSpec,
    LabelFamily,
    LabelInputSpec,
    LabelValueRecord,
    LabelVersion,
)


class CostAdjustedLabelError(ValueError):
    """Raised when cost-adjusted label definition or computation fails closed."""


class CostAdjustedLabelName(StrEnum):
    """Supported FLF-P18 cost/spread-adjusted label names."""

    COST_ADJUSTED_FWD_RET = "cost_adjusted_fwd_ret"
    SPREAD_ADJUSTED_FWD_RET = "spread_adjusted_fwd_ret"


@dataclass(frozen=True, slots=True)
class CostAdjustedLabelSpec:
    """Cost-adjusted family view over a governed label contract."""

    label_contract: LabelContractSpec
    label_name: CostAdjustedLabelName

    def __post_init__(self) -> None:
        if not isinstance(self.label_contract, LabelContractSpec):
            raise CostAdjustedLabelError(
                "CostAdjustedLabelSpec.label_contract must be a LabelContractSpec"
            )
        label_name = _coerce_label_name(self.label_name)
        if self.label_contract.family is not LabelFamily.COST_ADJUSTED:
            raise CostAdjustedLabelError(
                "CostAdjustedLabelSpec requires LabelFamily.COST_ADJUSTED"
            )
        _CostModel.from_cost_adjustment(self.label_contract.cost_adjustment, label_name)
        object.__setattr__(self, "label_name", label_name)

    @property
    def label_id(self) -> str:
        """Return the stable label id from the underlying contract."""

        return self.label_contract.label_id

    @property
    def label_spec_id(self) -> str:
        """Return the governed ``lspec_`` id bound to the contract."""

        return self.label_contract.label_spec_id

    @property
    def cost_adjustment(self) -> CostAdjustmentSpec:
        """Return the governed cost adjustment adapted from ``LabelSpec.cost_model``."""

        return self.label_contract.cost_adjustment

    def derive_label_version(self) -> LabelVersion:
        """Derive the deterministic version from the underlying contract."""

        return self.label_contract.derive_label_version()

    def to_contract_dict(self) -> dict[str, object]:
        """Return the canonical underlying label contract payload."""

        return self.label_contract.to_contract_dict()


@dataclass(frozen=True, slots=True)
class CostAdjustedForwardReturnSpec(CostAdjustedLabelSpec):
    """Forward-return label adjusted by explicit spread and bps costs."""


@dataclass(frozen=True, slots=True)
class SpreadAdjustedForwardReturnSpec(CostAdjustedLabelSpec):
    """Forward-return label adjusted by the governed spread model only."""


@dataclass(frozen=True, slots=True)
class CostAdjustedLabelDefinition:
    """Versioned FLF-P18 label definition bound to a governed label contract."""

    name: CostAdjustedLabelName
    spec: CostAdjustedLabelSpec
    version: LabelVersion

    @property
    def label_id(self) -> str:
        """Return the stable label id from the bound contract."""

        return self.spec.label_id

    @property
    def label_version_id(self) -> str:
        """Return the deterministic label-version id."""

        return self.version.label_version_id


@dataclass(frozen=True, slots=True)
class _LabelPoint:
    row: BBOInputRow
    horizon_end_ts: datetime
    label_available_ts: datetime
    value: float | None
    quality_flags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _CostModel:
    fixed_cost_bps: Decimal
    entry_spread_fraction: Decimal
    exit_spread_fraction: Decimal

    @classmethod
    def from_cost_adjustment(
        cls,
        cost_adjustment: CostAdjustmentSpec,
        label_name: CostAdjustedLabelName,
    ) -> _CostModel:
        if not isinstance(cost_adjustment, CostAdjustmentSpec):
            raise CostAdjustedLabelError("cost_adjustment must be a CostAdjustmentSpec")
        payload = cost_adjustment.cost_model.to_dict()
        model = _required_text(payload.get("model"), "cost_model.model")
        entry_fraction, exit_fraction = _spread_fractions(payload)

        if label_name is CostAdjustedLabelName.COST_ADJUSTED_FWD_RET:
            if model != "spread_plus_bps":
                raise CostAdjustedLabelError(
                    "cost_adjusted_fwd_ret requires cost_model.model='spread_plus_bps'"
                )
            fixed_cost_bps = _non_negative_decimal(
                payload.get("fixed_cost_bps"),
                "cost_model.fixed_cost_bps",
            )
            return cls(
                fixed_cost_bps=fixed_cost_bps,
                entry_spread_fraction=entry_fraction,
                exit_spread_fraction=exit_fraction,
            )

        if label_name is CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET:
            if model not in {"spread_adjusted", "spread_plus_bps"}:
                raise CostAdjustedLabelError(
                    "spread_adjusted_fwd_ret requires a spread-adjusted cost_model"
                )
            return cls(
                fixed_cost_bps=Decimal("0"),
                entry_spread_fraction=entry_fraction,
                exit_spread_fraction=exit_fraction,
            )

        raise CostAdjustedLabelError(f"unsupported cost-adjusted label: {label_name}")

    def adjustment_return(self, entry: BBOInputRow, terminal: BBOInputRow) -> Decimal:
        """Return total cost adjustment as a return fraction."""

        return (
            self.fixed_cost_bps / Decimal("10000")
            + self.entry_spread_fraction * (entry.spread / entry.mid)
            + self.exit_spread_fraction * (terminal.spread / terminal.mid)
        )


type _TradeRow = OHLCVInputRow | DenseGridBarRecord

_NUMERIC_TYPES = (int, float, Decimal)
_SPREAD_ADJUSTMENTS: Mapping[str, tuple[Decimal, Decimal]] = {
    "half_spread_round_trip": (Decimal("0.5"), Decimal("0.5")),
    "full_spread_round_trip": (Decimal("1.0"), Decimal("1.0")),
}
_DUPLICATE_BBO_KEY_FLAG = "duplicate_bbo_key"
_INPUT_FIELDS: tuple[str, ...] = (
    "bid",
    "ask",
    "mid",
    "spread",
    "available_ts",
    "event_ts",
    "bar_start_ts",
    "bar_end_ts",
    "series_id",
    "contract_id",
    "quality_flags",
    "has_trade",
    "synthetic",
    "fill_method",
    "provider_bar_ref",
)


def supported_cost_adjusted_labels() -> tuple[CostAdjustedLabelName, ...]:
    """Return the complete FLF-P18 cost/spread-adjusted label list."""

    return tuple(CostAdjustedLabelName)


def build_cost_adjusted_label_definition(
    name: CostAdjustedLabelName | str,
    governance_label_spec: GovernanceLabelSpec | Mapping[str, Any] | None,
    *,
    dataset_version_ids: Sequence[str] = (),
    contract_metadata: Mapping[str, Any] | None = None,
    materialization_scope: Mapping[str, Any] | None = None,
) -> CostAdjustedLabelDefinition:
    """Build one governed cost/spread-adjusted label definition.

    The supplied governance ``LabelSpec`` is consumed through
    ``LabelContractSpec.from_label_spec(...)``. Missing or invalid ``lspec_``
    bindings fail closed in the shared FLF-P16 contract layer.
    """

    label_name = _coerce_label_name(name)
    metadata = {
        "campaign": "ALPHA_FEATURE_LABEL_FOUNDATION_V1",
        "phase": "FLF-P18",
        "scaleout_campaign": "ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1",
        "scaleout_phase": "FUTSUB-P19",
        "label_family": LabelFamily.COST_ADJUSTED.value,
        "label_name": label_name.value,
        "materialization": "in_memory_records_only",
        "claims": "descriptive_label_substrate_only",
        "label_anchor": "source_bar_end_ts",
        "terminal_key": "series_id+contract_id+bar_end_ts",
        "terminal_resolution": "bar_end_aligned_bbo_proxy",
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
        "bbo_proxy_semantics": "time_sampled_forward_filled_tradability_proxy",
        **dict(contract_metadata or {}),
    }
    scope = _materialization_scope_metadata(materialization_scope)
    if scope:
        metadata["materialization_scope"] = scope
    label_contract = LabelContractSpec.from_label_spec(
        label_id=label_name.value,
        family=LabelFamily.COST_ADJUSTED,
        governance_label_spec=governance_label_spec,
        inputs=LabelInputSpec(
            input_views=("canonical_bbo", "dense_grid_ohlcv"),
            fields=_INPUT_FIELDS,
            dataset_version_ids=tuple(dataset_version_ids),
            input_metadata={
                "consumption_surface": "alpha_system.features.input_views.BBOInputView",
                "bbo_quality_tokens": [
                    MISSING_BBO_QUALITY_FLAG,
                    BBO_QUARANTINE_QUALITY_FLAG,
                ],
                "dense_grid_policy": (
                    "synthetic no-trade rows are flagged and are not trade anchors"
                ),
                "quote_policy": (
                    "cost and spread adjustments use bar-end-aligned BBO proxy "
                    "terminals; missing_bbo and bbo_quarantined rows are not filled"
                ),
            },
        ),
        contract_metadata=metadata,
    )
    spec = _wrap_label_spec(label_name, label_contract)
    return CostAdjustedLabelDefinition(
        name=label_name,
        spec=spec,
        version=spec.derive_label_version(),
    )


def build_cost_adjusted_label_definitions(
    label_specs: Mapping[CostAdjustedLabelName | str, GovernanceLabelSpec | Mapping[str, Any]],
    **parameters: Any,
) -> tuple[CostAdjustedLabelDefinition, ...]:
    """Build multiple governed FLF-P18 label definitions."""

    return tuple(
        build_cost_adjusted_label_definition(name, label_spec, **parameters)
        for name, label_spec in label_specs.items()
    )


def compute_cost_adjusted_label(
    definition: CostAdjustedLabelDefinition,
    input_view: BBOInputView | CanonicalInputViews,
    *,
    trade_rows: Iterable[_TradeRow] = (),
) -> tuple[LabelValueRecord, ...]:
    """Compute one cost/spread-adjusted label as in-memory value records.

    Values are returned only to the caller. This function does not materialize,
    persist, register, or write label values.
    """

    definition = _require_definition(definition)
    rows = _validated_rows(_coerce_bbo_view(input_view).rows)
    row_index = _bbo_rows_by_key(rows)
    trade_index = _trade_rows_by_key(trade_rows)
    horizon = _horizon_delta(definition.spec.label_contract.horizon.horizon)
    cost_model = _CostModel.from_cost_adjustment(
        definition.spec.cost_adjustment,
        definition.name,
    )
    roll_calendar_cache: dict[tuple[str, int, int], tuple[Any, ...]] = {}
    records: list[LabelValueRecord] = []
    for row in rows:
        point = _label_point(
            definition,
            row,
            row_index=row_index,
            trade_index=trade_index,
            horizon=horizon,
            cost_model=cost_model,
            roll_calendar_cache=roll_calendar_cache,
        )
        if point is not None:
            records.append(_label_value_record(definition, point))
    return tuple(records)


def compute_cost_adjusted_labels(
    definitions: Iterable[CostAdjustedLabelDefinition],
    input_view: BBOInputView | CanonicalInputViews,
    *,
    trade_rows: Iterable[_TradeRow] = (),
) -> dict[CostAdjustedLabelName, tuple[LabelValueRecord, ...]]:
    """Compute multiple governed FLF-P18 definitions against one BBO view."""

    return {
        definition.name: compute_cost_adjusted_label(
            definition,
            input_view,
            trade_rows=trade_rows,
        )
        for definition in definitions
    }


def _label_point(
    definition: CostAdjustedLabelDefinition,
    row: BBOInputRow,
    *,
    row_index: Mapping[tuple[str, str, datetime], BBOInputRow],
    trade_index: Mapping[tuple[str, datetime], _TradeRow],
    horizon: timedelta,
    cost_model: _CostModel,
    roll_calendar_cache: dict[tuple[str, int, int], tuple[Any, ...]],
) -> _LabelPoint | None:
    horizon_end_ts = row.event_ts + horizon
    terminal = row_index.get((row.series_id, row.contract_id, horizon_end_ts))
    if terminal is None:
        return _gap_label_point(
            row,
            horizon_end_ts=horizon_end_ts,
            label_available_ts=_label_available_ts(
                definition,
                horizon_end_ts=horizon_end_ts,
                source=row,
                terminal=None,
            ),
            reason="missing_terminal_bbo",
        )

    if _DUPLICATE_BBO_KEY_FLAG in row.quality_flags:
        return _gap_label_point(
            row,
            horizon_end_ts=terminal.event_ts,
            label_available_ts=_label_available_ts(
                definition,
                horizon_end_ts=terminal.event_ts,
                source=row,
                terminal=terminal,
            ),
            reason=_DUPLICATE_BBO_KEY_FLAG,
        )
    if _DUPLICATE_BBO_KEY_FLAG in terminal.quality_flags:
        return _gap_label_point(
            row,
            horizon_end_ts=terminal.event_ts,
            label_available_ts=_label_available_ts(
                definition,
                horizon_end_ts=terminal.event_ts,
                source=row,
                terminal=terminal,
            ),
            reason="terminal_duplicate_bbo_key",
            extra_flags=(_DUPLICATE_BBO_KEY_FLAG,),
        )

    guarded = _guarded_cost_terminal(
        row,
        terminal,
        terminal_by_key=row_index,
        roll_calendar_cache=roll_calendar_cache,
    )
    if guarded is None:
        return None
    terminal, guard_flags = guarded
    label_available_ts = _label_available_ts(
        definition,
        horizon_end_ts=terminal.event_ts,
        source=row,
        terminal=terminal,
    )

    trade_row = trade_index.get((row.series_id, row.event_ts))
    if trade_row is not None and _is_synthetic_no_trade(trade_row):
        return _gap_label_point(
            row,
            horizon_end_ts=terminal.event_ts,
            label_available_ts=label_available_ts,
            reason="synthetic_no_trade",
            extra_flags=("no_trade", *guard_flags),
        )

    if not _is_valid_quote(row):
        return _gap_label_point(
            row,
            horizon_end_ts=terminal.event_ts,
            label_available_ts=label_available_ts,
            reason="entry_bbo_gap",
            extra_flags=(*_bbo_gap_flags(row), *guard_flags),
        )
    if not _is_valid_quote(terminal):
        return _gap_label_point(
            row,
            horizon_end_ts=terminal.event_ts,
            label_available_ts=label_available_ts,
            reason="terminal_bbo_gap",
            extra_flags=(*_bbo_gap_flags(terminal), *guard_flags),
        )
    if row.mid <= 0 or terminal.mid <= 0:
        return _gap_label_point(
            row,
            horizon_end_ts=terminal.event_ts,
            label_available_ts=label_available_ts,
            reason="zero_or_negative_mid",
            extra_flags=guard_flags,
        )

    raw_return = (terminal.mid / row.mid) - Decimal("1")
    adjusted_return = raw_return - cost_model.adjustment_return(row, terminal)
    return _LabelPoint(
        row=row,
        horizon_end_ts=terminal.event_ts,
        label_available_ts=label_available_ts,
        value=float(adjusted_return),
        quality_flags=guard_flags,
    )


def _label_value_record(
    definition: CostAdjustedLabelDefinition,
    point: _LabelPoint,
) -> LabelValueRecord:
    return LabelValueRecord(
        label_version_id=definition.label_version_id,
        entity_id=point.row.series_id,
        event_ts=point.row.event_ts,
        horizon_end_ts=point.horizon_end_ts,
        label_available_ts=point.label_available_ts,
        value=point.value,
        label_contract=definition.spec.label_contract,
        quality_flags=point.quality_flags,
    )


def _label_available_ts(
    definition: CostAdjustedLabelDefinition,
    *,
    horizon_end_ts: datetime,
    terminal: BBOInputRow | None,
    source: BBOInputRow | None = None,
) -> datetime:
    candidates = [
        horizon_end_ts,
        definition.spec.label_contract.availability_policy.availability_time,
    ]
    if source is not None:
        candidates.append(source.available_ts)
    if terminal is not None:
        candidates.append(terminal.available_ts)
    return max(candidates)


def _gap_label_point(
    row: BBOInputRow,
    *,
    horizon_end_ts: datetime,
    label_available_ts: datetime,
    reason: str,
    extra_flags: Sequence[str] = (),
) -> _LabelPoint:
    return _LabelPoint(
        row=row,
        horizon_end_ts=horizon_end_ts,
        label_available_ts=label_available_ts,
        value=None,
        quality_flags=_quality_flags(("label_gap", reason, *extra_flags)),
    )


def _wrap_label_spec(
    name: CostAdjustedLabelName,
    label_contract: LabelContractSpec,
) -> CostAdjustedLabelSpec:
    if name is CostAdjustedLabelName.COST_ADJUSTED_FWD_RET:
        return CostAdjustedForwardReturnSpec(
            label_contract=label_contract,
            label_name=name,
        )
    if name is CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET:
        return SpreadAdjustedForwardReturnSpec(
            label_contract=label_contract,
            label_name=name,
        )
    return CostAdjustedLabelSpec(label_contract=label_contract, label_name=name)


def _coerce_bbo_view(input_view: BBOInputView | CanonicalInputViews) -> BBOInputView:
    if isinstance(input_view, CanonicalInputViews):
        return input_view.bbo
    if isinstance(input_view, BBOInputView):
        return input_view
    raise CostAdjustedLabelError("cost-adjusted labels require a BBOInputView")


def _validated_rows(rows: Sequence[BBOInputRow]) -> tuple[BBOInputRow, ...]:
    ordered = tuple(rows)
    for row in ordered:
        if not isinstance(row, BBOInputRow):
            raise CostAdjustedLabelError("cost-adjusted label inputs must be BBOInputRow objects")
        _require_aware_datetime(row.available_ts, "BBOInputRow.available_ts")
        _require_aware_datetime(row.event_ts, "BBOInputRow.event_ts")
        _require_aware_datetime(row.bar_start_ts, "BBOInputRow.bar_start_ts")
        _require_aware_datetime(row.bar_end_ts, "BBOInputRow.bar_end_ts")
        for field in ("bid", "ask", "bid_size", "ask_size", "mid", "spread"):
            _require_decimal(getattr(row, field), f"BBOInputRow.{field}")
    aligned = tuple(_align_bbo_row_to_bar_end(row) for row in ordered)
    return _collapse_duplicate_bbo_keys(tuple(sorted(aligned, key=lambda row: row.available_ts)))


def _align_bbo_row_to_bar_end(row: BBOInputRow) -> BBOInputRow:
    if row.event_ts > row.bar_end_ts:
        raise CostAdjustedLabelError(
            "BBOInputRow.event_ts must be at or before BBOInputRow.bar_end_ts"
        )
    if row.event_ts == row.bar_end_ts:
        return row
    return replace(row, event_ts=row.bar_end_ts)


def _collapse_duplicate_bbo_keys(rows: Sequence[BBOInputRow]) -> tuple[BBOInputRow, ...]:
    by_key: dict[tuple[str, str, datetime], BBOInputRow] = {}
    order: list[tuple[str, str, datetime]] = []
    for row in rows:
        key = (row.series_id, row.contract_id, row.bar_end_ts)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = row
            order.append(key)
            continue
        # Duplicate BBO keys make the quote ambiguous. Keep one deterministic
        # timestamp row for gap reporting, but mark it unusable for cost math.
        by_key[key] = replace(
            existing,
            quality_flags=_quality_flags((*existing.quality_flags, _DUPLICATE_BBO_KEY_FLAG)),
        )
    return tuple(by_key[key] for key in order)


def _bbo_rows_by_key(rows: Sequence[BBOInputRow]) -> dict[tuple[str, str, datetime], BBOInputRow]:
    by_key: dict[tuple[str, str, datetime], BBOInputRow] = {}
    for row in rows:
        key = (row.series_id, row.contract_id, row.bar_end_ts)
        if key in by_key:
            raise CostAdjustedLabelError(
                "BBO rows must not duplicate series_id/contract_id/bar_end_ts"
            )
        by_key[key] = row
    return by_key


def _guarded_cost_terminal(
    source: BBOInputRow,
    terminal: BBOInputRow,
    *,
    terminal_by_key: Mapping[tuple[str, str, datetime], BBOInputRow],
    roll_calendar_cache: dict[tuple[str, int, int], tuple[Any, ...]],
) -> tuple[BBOInputRow, tuple[str, ...]] | None:
    try:
        return _guarded_forward_terminal(
            source,
            terminal,
            terminal_by_key=terminal_by_key,
            roll_calendar_cache=roll_calendar_cache,
        )
    except Exception as exc:  # noqa: BLE001 - normalize shared guard errors for this family.
        raise CostAdjustedLabelError(str(exc)) from exc


def _trade_rows_by_key(rows: Iterable[_TradeRow]) -> dict[tuple[str, datetime], _TradeRow]:
    by_key: dict[tuple[str, datetime], _TradeRow] = {}
    for row in rows:
        if not isinstance(row, OHLCVInputRow | DenseGridBarRecord):
            raise CostAdjustedLabelError(
                "trade_rows must contain OHLCVInputRow or DenseGridBarRecord"
            )
        _require_aware_datetime(row.event_ts, "trade_row.event_ts")
        key = (row.series_id, row.event_ts)
        if key in by_key:
            raise CostAdjustedLabelError("trade_rows must not duplicate series_id/event_ts")
        by_key[key] = row
    return by_key


def _is_valid_quote(row: BBOInputRow) -> bool:
    semantics = _quote_semantics(row)
    return not semantics.missing_or_abnormal and semantics.invariants_hold


def _quote_semantics(row: BBOInputRow):
    try:
        return bbo_quote_semantics(row)
    except DataFoundationValidationError as exc:
        raise CostAdjustedLabelError(str(exc)) from exc


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


def _is_synthetic_no_trade(row: _TradeRow) -> bool:
    try:
        return is_synthetic_no_trade_bar(row)
    except DataFoundationValidationError as exc:
        raise CostAdjustedLabelError(str(exc)) from exc


def _require_definition(definition: CostAdjustedLabelDefinition) -> CostAdjustedLabelDefinition:
    if not isinstance(definition, CostAdjustedLabelDefinition):
        raise CostAdjustedLabelError("compute requires a CostAdjustedLabelDefinition")
    if definition.spec.label_contract.family is not LabelFamily.COST_ADJUSTED:
        raise CostAdjustedLabelError("definition must belong to LabelFamily.COST_ADJUSTED")
    if definition.version != definition.spec.derive_label_version():
        raise CostAdjustedLabelError("definition LabelVersion does not match LabelContractSpec")
    return definition


def _spread_fractions(payload: Mapping[str, object]) -> tuple[Decimal, Decimal]:
    adjustment = payload.get("spread_adjustment")
    if isinstance(adjustment, str):
        normalized = adjustment.strip().lower()
        if normalized in _SPREAD_ADJUSTMENTS:
            return _SPREAD_ADJUSTMENTS[normalized]
        if normalized != "custom_fraction":
            raise CostAdjustedLabelError(
                "cost_model.spread_adjustment must be half_spread_round_trip, "
                "full_spread_round_trip, or custom_fraction"
            )
    if "entry_spread_fraction" not in payload or "exit_spread_fraction" not in payload:
        raise CostAdjustedLabelError(
            "custom spread adjustment requires cost_model.entry_spread_fraction "
            "and cost_model.exit_spread_fraction"
        )
    return (
        _non_negative_decimal(
            payload.get("entry_spread_fraction"),
            "cost_model.entry_spread_fraction",
        ),
        _non_negative_decimal(
            payload.get("exit_spread_fraction"),
            "cost_model.exit_spread_fraction",
        ),
    )


def _horizon_delta(value: str) -> timedelta:
    if not isinstance(value, str) or not value.strip():
        raise CostAdjustedLabelError("LabelSpec.horizon must be a non-empty duration string")
    text = value.strip().lower()
    if text.endswith("m"):
        return _positive_duration(float(text[:-1]), multiplier=60)
    if text.endswith("s"):
        return _positive_duration(float(text[:-1]), multiplier=1)
    if text.endswith("h"):
        return _positive_duration(float(text[:-1]), multiplier=3600)
    raise CostAdjustedLabelError("LabelSpec.horizon must use an s, m, or h duration suffix")


def _positive_duration(value: float, *, multiplier: int) -> timedelta:
    if not math.isfinite(value) or value <= 0:
        raise CostAdjustedLabelError("LabelSpec.horizon must be positive and finite")
    return timedelta(seconds=value * multiplier)


def _coerce_label_name(name: CostAdjustedLabelName | str) -> CostAdjustedLabelName:
    try:
        return CostAdjustedLabelName(name)
    except ValueError as exc:
        raise CostAdjustedLabelError(f"unsupported cost-adjusted label: {name}") from exc


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CostAdjustedLabelError(f"{field_name} must be a non-empty string")
    return value.strip()


def _non_negative_decimal(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, _NUMERIC_TYPES):
        raise CostAdjustedLabelError(f"{field_name} must be numeric")
    parsed = Decimal(str(value))
    if not parsed.is_finite() or parsed < 0:
        raise CostAdjustedLabelError(f"{field_name} must be a finite non-negative value")
    return parsed


def _require_decimal(value: object, field_name: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise CostAdjustedLabelError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise CostAdjustedLabelError(f"{field_name} must be finite")
    return value


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise CostAdjustedLabelError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise CostAdjustedLabelError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quality_flags(flags: Sequence[str]) -> tuple[str, ...]:
    if isinstance(flags, str) or not isinstance(flags, Sequence):
        raise CostAdjustedLabelError("quality_flags must be a sequence of strings")
    normalized: list[str] = []
    for flag in flags:
        if not isinstance(flag, str) or not flag.strip():
            raise CostAdjustedLabelError("quality_flags must contain non-empty strings")
        token = flag.strip().lower()
        if token not in normalized:
            normalized.append(token)
    return tuple(normalized)


def _materialization_scope_metadata(
    value: Mapping[str, Any] | None,
) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise CostAdjustedLabelError("materialization_scope must be a mapping")
    scope: dict[str, str] = {}
    for key, item in value.items():
        key_text = _metadata_text(key, "materialization_scope key")
        item_text = _metadata_text(item, f"materialization_scope.{key_text}")
        scope[key_text] = item_text
    return dict(sorted(scope.items()))


def _metadata_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise CostAdjustedLabelError(f"{field_name} must be a string")
    text = value.strip()
    if not text:
        raise CostAdjustedLabelError(f"{field_name} must be a non-empty string")
    return text


__all__ = [
    "CostAdjustedForwardReturnSpec",
    "CostAdjustedLabelDefinition",
    "CostAdjustedLabelError",
    "CostAdjustedLabelName",
    "CostAdjustedLabelSpec",
    "SpreadAdjustedForwardReturnSpec",
    "build_cost_adjusted_label_definition",
    "build_cost_adjusted_label_definitions",
    "compute_cost_adjusted_label",
    "compute_cost_adjusted_labels",
    "supported_cost_adjusted_labels",
]
