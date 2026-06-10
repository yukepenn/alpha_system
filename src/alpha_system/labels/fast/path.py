"""Path-label fast pack declarations and guarded scan kernels.

The reference path family remains the oracle. This module only emits values
under reference-derived identities, using the LCFP-P02 shared panel and
terminal-index model when the panel shape is inside the proven boundary.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from alpha_system.features.input_views import OHLCVInputRow, OHLCVInputView
from alpha_system.labels.families.path import (
    PathBarrier,
    PathDirection,
    PathLabelDefinition,
    PathLabelName,
    SameBarBarrierPolicy,
    compute_path_label,
    supported_path_labels,
)
from alpha_system.labels.version import LabelValueRecord, LabelVersion

from alpha_system.labels.fast.materializer import (
    FastLabelDeclaration,
    FastLabelPack,
    FastLabelPackError,
)
from alpha_system.labels.fast.panel import (
    LabelAvailabilityFamily,
    SharedLabelPanel,
    SharedLabelPanelRow,
    TerminalGuardDisposition,
    TerminalIndexModel,
    TerminalKind,
    derive_label_available_ts,
)

PATH_LABEL_IDS: tuple[str, ...] = tuple(label_name.value for label_name in supported_path_labels())
_PATH_LABELS: tuple[PathLabelName, ...] = supported_path_labels()


@dataclass(frozen=True, slots=True)
class PathLabelRoute:
    """Value-free implementation route for one governed path label."""

    label_id: str
    route: str
    fallback: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {
            "label_id": self.label_id,
            "route": self.route,
            "fallback": self.fallback,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class PathLabelPackCoverage:
    """Value-free coverage summary for the P05 path fast pack."""

    label_ids: tuple[str, ...]
    kernelized_label_ids: tuple[str, ...]
    fallback_label_ids: tuple[str, ...]
    routes: tuple[PathLabelRoute, ...]
    terminal_model: str
    same_bar_policy_note: str
    tolerance_note: str

    def to_dict(self) -> dict[str, object]:
        return {
            "label_ids": list(self.label_ids),
            "kernelized_label_ids": list(self.kernelized_label_ids),
            "fallback_label_ids": list(self.fallback_label_ids),
            "routes": [route.to_dict() for route in self.routes],
            "terminal_model": self.terminal_model,
            "same_bar_policy_note": self.same_bar_policy_note,
            "tolerance_note": self.tolerance_note,
        }


def build_path_label_pack(definitions: Sequence[PathLabelDefinition]) -> FastLabelPack:
    """Build the governed MFE/MAE/TBS/triple-barrier fast path-label pack."""

    ordered = _ordered_path_definitions(definitions)
    return FastLabelPack(
        pack_id="path",
        definitions=ordered,
        declarations=tuple(FastLabelDeclaration(definition) for definition in ordered),
        metadata=path_label_pack_coverage().to_dict(),
    )


def supports_path_label_pack(definitions: Sequence[PathLabelDefinition]) -> bool:
    """Return true when definitions are a governed path-label subset."""

    try:
        _ordered_path_definitions(definitions)
    except FastLabelPackError:
        return False
    return True


def path_label_pack_coverage() -> PathLabelPackCoverage:
    """Return a value-free summary of kernel/fallback routing."""

    routes = tuple(
        PathLabelRoute(
            label_id=label_id,
            route="p02_guarded_panel_scan_kernel",
            fallback="reference_path_family_per_row",
            reason=(
                "Kernelized when the P02 terminal model is a fixed-horizon "
                "guarded endpoint for the path horizon and the shared panel "
                "carries the requested OHLCV entry field. Otherwise callers "
                "must route the label through the reference path family."
            ),
        )
        for label_id in PATH_LABEL_IDS
    )
    return PathLabelPackCoverage(
        label_ids=PATH_LABEL_IDS,
        kernelized_label_ids=PATH_LABEL_IDS,
        fallback_label_ids=PATH_LABEL_IDS,
        routes=routes,
        terminal_model=(
            "LCFP-P02 TerminalKind.FIXED_HORIZON with roll and maintenance "
            "guard disposition; scans are bounded to the retained terminal row"
        ),
        same_bar_policy_note=(
            "Same-bar target/stop touches follow SameBarBarrierPolicy exactly: "
            "ambiguous emits a null barrier value and the ambiguity quality flag; "
            "target_first and stop_first force the corresponding first touch."
        ),
        tolerance_note=(
            "Timestamp, identity, event-set, and quality-flag parity are exact. "
            "Float value tests use 1e-12 tolerance because the reference family "
            "calculates with Decimal OHLCV rows while the fast panel stores floats."
        ),
    )


def compute_path_records_from_panel(
    panel: SharedLabelPanel,
    definition: PathLabelDefinition,
    terminal_model: TerminalIndexModel,
) -> tuple[LabelValueRecord, ...]:
    """Compute one path label from a P02 shared panel and terminal model."""

    if not isinstance(panel, SharedLabelPanel):
        raise FastLabelPackError("path label computation requires a SharedLabelPanel")
    if not isinstance(definition, PathLabelDefinition):
        raise FastLabelPackError("path label computation requires a PathLabelDefinition")
    if not isinstance(terminal_model, TerminalIndexModel):
        raise FastLabelPackError("path label computation requires a TerminalIndexModel")
    if not _kernel_supported(panel, definition, terminal_model):
        return _reference_records_from_panel(panel, definition)

    records: list[LabelValueRecord] = []
    for resolution in terminal_model.resolutions:
        source = panel.row_at(resolution.source_index)
        if not _is_real_trade_row(source):
            continue
        if resolution.disposition in {
            TerminalGuardDisposition.DROP,
            TerminalGuardDisposition.INVALID,
        }:
            continue
        if resolution.terminal_index is None:
            continue
        terminal = panel.row_at(resolution.terminal_index)
        future_rows = _future_trade_rows(panel, source=source, terminal=terminal)
        outcome = _resolve_path_outcome(
            definition,
            source=source,
            future_rows=future_rows,
            terminal_was_truncated=resolution.disposition
            is TerminalGuardDisposition.TRUNCATE,
        )
        if outcome is None:
            continue
        value, resolution_row, quality_flags = outcome
        records.append(
            _value_record(
                definition,
                source=source,
                resolution_row=resolution_row,
                value=value,
                quality_flags=_merged_quality_flags(
                    quality_flags,
                    resolution.quality_flags,
                ),
            )
        )
    return tuple(records)


def _ordered_path_definitions(
    definitions: Sequence[PathLabelDefinition],
) -> tuple[PathLabelDefinition, ...]:
    if isinstance(definitions, str) or not isinstance(definitions, Sequence):
        raise FastLabelPackError("path label pack requires a sequence of definitions")
    if not definitions:
        raise FastLabelPackError("path label pack requires at least one definition")
    by_name: dict[PathLabelName, PathLabelDefinition] = {}
    for definition in definitions:
        if not isinstance(definition, PathLabelDefinition):
            raise FastLabelPackError("path pack entries must be PathLabelDefinition objects")
        if definition.name not in _PATH_LABELS:
            raise FastLabelPackError(f"unsupported path label: {definition.name.value}")
        if definition.name in by_name:
            raise FastLabelPackError(f"duplicate path label: {definition.name.value}")
        expected = LabelVersion.derive(definition.contract)
        if definition.version != expected:
            raise FastLabelPackError("path LabelVersion does not match contract")
        by_name[definition.name] = definition
    return tuple(label for name in _PATH_LABELS if (label := by_name.get(name)) is not None)


def _kernel_supported(
    panel: SharedLabelPanel,
    definition: PathLabelDefinition,
    terminal_model: TerminalIndexModel,
) -> bool:
    if terminal_model.request.kind is not TerminalKind.FIXED_HORIZON:
        return False
    if terminal_model.request.horizon_minutes != definition.horizon_steps:
        return False
    if definition.price_field not in {"open", "high", "low", "close"}:
        return False
    if definition.price_field == "open" and any(row.open is None for row in panel.rows):
        return False
    return True


def _resolve_path_outcome(
    definition: PathLabelDefinition,
    *,
    source: SharedLabelPanelRow,
    future_rows: tuple[SharedLabelPanelRow, ...],
    terminal_was_truncated: bool,
) -> tuple[bool | int | float | None, SharedLabelPanelRow, tuple[str, ...]] | None:
    if not future_rows:
        return None

    if definition.name is PathLabelName.MFE:
        if len(future_rows) < definition.horizon_steps and not terminal_was_truncated:
            return None
        value = max(_bar_returns(definition, source, row).favorable for row in future_rows)
        return value, future_rows[-1], ()

    if definition.name is PathLabelName.MAE:
        if len(future_rows) < definition.horizon_steps and not terminal_was_truncated:
            return None
        value = min(_bar_returns(definition, source, row).adverse for row in future_rows)
        return value, future_rows[-1], ()

    barrier, resolution_row = _first_barrier(definition, source, future_rows)
    if barrier is None:
        if len(future_rows) < definition.horizon_steps and not terminal_was_truncated:
            return None
        barrier = PathBarrier.HORIZON
        resolution_row = future_rows[-1]

    if definition.name is PathLabelName.TARGET_BEFORE_STOP:
        value: bool | None = (
            None if barrier is PathBarrier.AMBIGUOUS else barrier is PathBarrier.TARGET
        )
        return value, resolution_row, _barrier_quality_flags(barrier)

    if definition.name is PathLabelName.TRIPLE_BARRIER:
        return _triple_barrier_value(barrier), resolution_row, _barrier_quality_flags(barrier)

    raise FastLabelPackError(f"unsupported path label: {definition.name.value}")


def _first_barrier(
    definition: PathLabelDefinition,
    source: SharedLabelPanelRow,
    future_rows: tuple[SharedLabelPanelRow, ...],
) -> tuple[PathBarrier | None, SharedLabelPanelRow]:
    if definition.target_return is None or definition.stop_return is None:
        raise FastLabelPackError("target and stop returns are required for barrier labels")

    for row in future_rows:
        returns = _bar_returns(definition, source, row)
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


@dataclass(frozen=True, slots=True)
class _DirectionalReturns:
    favorable: float
    adverse: float


def _bar_returns(
    definition: PathLabelDefinition,
    source: SharedLabelPanelRow,
    row: SharedLabelPanelRow,
) -> _DirectionalReturns:
    entry = _entry_price(source, definition.price_field)
    if definition.direction is PathDirection.LONG:
        favorable = (row.high - entry) / entry
        adverse = (row.low - entry) / entry
    else:
        favorable = (entry - row.low) / entry
        adverse = (entry - row.high) / entry
    if not math.isfinite(favorable) or not math.isfinite(adverse):
        raise FastLabelPackError("path label return calculation produced a non-finite value")
    return _DirectionalReturns(favorable=favorable, adverse=adverse)


def _entry_price(row: SharedLabelPanelRow, price_field: str) -> float:
    if price_field == "open":
        value = row.open
    elif price_field == "high":
        value = row.high
    elif price_field == "low":
        value = row.low
    elif price_field == "close":
        value = row.trade_price
    else:
        raise FastLabelPackError("path price_field must be one of open, high, low, close")
    if value is None or value <= 0.0 or not math.isfinite(value):
        raise FastLabelPackError("path entry price must be positive and finite")
    return value


def _future_trade_rows(
    panel: SharedLabelPanel,
    *,
    source: SharedLabelPanelRow,
    terminal: SharedLabelPanelRow,
) -> tuple[SharedLabelPanelRow, ...]:
    rows = []
    for row in panel.rows[source.row_index + 1 : terminal.row_index + 1]:
        if row.series_id != source.series_id or row.contract_id != source.contract_id:
            continue
        if row.event_ts <= source.event_ts or row.event_ts > terminal.event_ts:
            continue
        if _is_real_trade_row(row):
            rows.append(row)
    return tuple(rows)


def _is_real_trade_row(row: SharedLabelPanelRow) -> bool:
    return "no_trade" not in row.quality_flags


def _value_record(
    definition: PathLabelDefinition,
    *,
    source: SharedLabelPanelRow,
    resolution_row: SharedLabelPanelRow,
    value: bool | int | float | None,
    quality_flags: tuple[str, ...],
) -> LabelValueRecord:
    label_available_ts = derive_label_available_ts(
        LabelAvailabilityFamily.PATH,
        definition.contract.availability_policy,
        horizon_end_ts=resolution_row.event_ts,
        resolution_event_ts=resolution_row.event_ts,
        resolution_available_ts=resolution_row.available_ts,
    )
    return LabelValueRecord(
        label_version_id=definition.label_version_id,
        entity_id=source.instrument_id,
        event_ts=source.event_ts,
        horizon_end_ts=resolution_row.event_ts,
        label_available_ts=label_available_ts,
        value=value,
        label_contract=definition.contract,
        quality_flags=quality_flags,
    )


def _barrier_quality_flags(barrier: PathBarrier) -> tuple[str, ...]:
    if barrier is PathBarrier.HORIZON:
        return ("horizon_no_barrier",)
    if barrier is PathBarrier.AMBIGUOUS:
        return ("ambiguous_same_bar_barrier",)
    return ()


def _triple_barrier_value(barrier: PathBarrier) -> int | None:
    if barrier is PathBarrier.TARGET:
        return 1
    if barrier is PathBarrier.STOP:
        return -1
    if barrier is PathBarrier.HORIZON:
        return 0
    if barrier is PathBarrier.AMBIGUOUS:
        return None
    raise FastLabelPackError(f"unsupported barrier outcome: {barrier}")


def _merged_quality_flags(
    path_flags: Sequence[str],
    terminal_flags: Sequence[str],
) -> tuple[str, ...]:
    merged: list[str] = []
    for flag in (*path_flags, *terminal_flags):
        token = str(flag).strip().lower()
        if token and token not in merged:
            merged.append(token)
    return tuple(merged)


def _reference_records_from_panel(
    panel: SharedLabelPanel,
    definition: PathLabelDefinition,
) -> tuple[LabelValueRecord, ...]:
    """Route unsupported panel shapes through the reference path family."""

    fallback_view = OHLCVInputView(tuple(_ohlcv_row(row) for row in panel.rows))
    return compute_path_label(definition, fallback_view)


def _ohlcv_row(row: SharedLabelPanelRow) -> OHLCVInputRow:
    event_ts = row.event_ts
    open_price = row.open if row.open is not None else row.trade_price
    return OHLCVInputRow(
        instrument_id=row.instrument_id,
        contract_id=row.contract_id,
        series_id=row.series_id,
        bar_start_ts=event_ts - timedelta(minutes=1),
        bar_end_ts=row.bar_end_ts,
        event_ts=event_ts,
        available_ts=row.available_ts,
        ingested_at=row.available_ts,
        open=Decimal(str(open_price)),
        high=Decimal(str(row.high)),
        low=Decimal(str(row.low)),
        close=Decimal(str(row.trade_price)),
        volume=Decimal(str(row.volume or 0)),
        data_version=str(panel_data_version(row)),
        quality_flags=tuple(row.quality_flags),
        session_label=row.session_label,
    )


def panel_data_version(row: SharedLabelPanelRow) -> str:
    """Return a stable synthetic data-version token for fallback row adapters."""

    return f"fast_path_panel:{row.series_id}"


__all__ = [
    "PATH_LABEL_IDS",
    "PathLabelPackCoverage",
    "PathLabelRoute",
    "build_path_label_pack",
    "compute_path_records_from_panel",
    "path_label_pack_coverage",
    "supports_path_label_pack",
]
