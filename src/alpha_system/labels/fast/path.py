"""Path-label fast pack declarations and vectorized positional scan kernels.

The reference path family remains the oracle. Its horizon is positional:
``horizon_steps`` forward REAL TRADE BARS, not fixed minutes. The fast kernel
keeps that positional record set while applying the shared roll-splice and
maintenance-crossing guard to the full path window before measuring excursions
or barrier touches. Values are emitted under reference-derived identities only.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
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
from alpha_system.labels.families.fixed_horizon.family import _guarded_forward_terminal
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
    TerminalIndexModel,
    derive_label_available_ts,
)

PATH_LABEL_IDS: tuple[str, ...] = tuple(label_name.value for label_name in supported_path_labels())
_PATH_LABELS: tuple[PathLabelName, ...] = supported_path_labels()
_PATH_WINDOW_GUARD_CACHE_MAX = 16
_PATH_WINDOW_GUARD_CACHE: dict[tuple[object, ...], tuple[tuple[str, ...] | None, ...]] = {}


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
            route="positional_trade_bar_scan_kernel",
            fallback="reference_path_family_per_row",
            reason=(
                "Kernelized when the shared panel carries the requested OHLCV "
                "entry field for every real trade row. Otherwise callers must "
                "route the label through the reference path family."
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
            "guarded positional horizon: horizon_steps forward real trade "
            "bars per entry row, contract-scoped on series_id+contract_id and "
            "checked against the shared roll-splice and maintenance-crossing "
            "guard before excursion or barrier values are measured"
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
    terminal_model: TerminalIndexModel | None = None,
) -> tuple[LabelValueRecord, ...]:
    """Compute one path label from a shared panel with reference semantics.

    ``terminal_model`` is accepted for backward signature compatibility and is
    ignored: the reference path family resolves horizons positionally over
    real trade bars, so no fixed-minute terminal-index model participates.
    """

    if not isinstance(panel, SharedLabelPanel):
        raise FastLabelPackError("path label computation requires a SharedLabelPanel")
    if not isinstance(definition, PathLabelDefinition):
        raise FastLabelPackError("path label computation requires a PathLabelDefinition")
    if terminal_model is not None and not isinstance(terminal_model, TerminalIndexModel):
        raise FastLabelPackError("terminal_model must be a TerminalIndexModel or None")
    trade_rows = _sorted_real_trade_rows(panel)
    if not _kernel_supported(definition, trade_rows):
        return _reference_records_from_panel(panel, definition)
    if not trade_rows:
        return ()

    panel_cache_key = id(panel)
    if definition.name in (PathLabelName.MFE, PathLabelName.MAE):
        return _excursion_records(definition, trade_rows, panel_cache_key=panel_cache_key)
    return _barrier_records(definition, trade_rows, panel_cache_key=panel_cache_key)


def _sorted_real_trade_rows(panel: SharedLabelPanel) -> tuple[SharedLabelPanelRow, ...]:
    """Return real trade rows ordered exactly like the reference family."""

    return tuple(
        sorted(
            (row for row in panel.rows if _is_real_trade_row(row)),
            key=lambda row: row.event_ts,
        )
    )


def _excursion_records(
    definition: PathLabelDefinition,
    trade_rows: tuple[SharedLabelPanelRow, ...],
    *,
    panel_cache_key: int,
) -> tuple[LabelValueRecord, ...]:
    """Vectorized MFE/MAE over the positional forward trade-bar window.

    The reference emits one record per entry row with a FULL ``horizon_steps``
    forward window; the excursion extreme over the window factors through the
    window max(high)/min(low) because float subtraction and division by a
    fixed positive entry price are monotone in the bar extreme.
    """

    horizon = definition.horizon_steps
    count = len(trade_rows)
    if count <= horizon:
        return ()
    window_max_high, window_min_low = _forward_window_extremes(trade_rows, horizon)
    guard_results = _path_window_guard_results(
        trade_rows,
        horizon,
        panel_cache_key=panel_cache_key,
    )
    is_mfe = definition.name is PathLabelName.MFE
    is_long = definition.direction is PathDirection.LONG
    records: list[LabelValueRecord] = []
    for index in range(count - horizon):
        source = trade_rows[index]
        terminal_index = index + horizon
        guard_flags = guard_results[index]
        if guard_flags is None:
            continue
        entry = _entry_price(source, definition.price_field)
        if is_long:
            value = (
                (window_max_high[index] - entry) / entry
                if is_mfe
                else (window_min_low[index] - entry) / entry
            )
        else:
            value = (
                (entry - window_min_low[index]) / entry
                if is_mfe
                else (entry - window_max_high[index]) / entry
            )
        if not math.isfinite(value):
            raise FastLabelPackError(
                "path label return calculation produced a non-finite value"
            )
        records.append(
            _value_record(
                definition,
                source=source,
                resolution_row=trade_rows[terminal_index],
                value=value,
                quality_flags=guard_flags,
            )
        )
    return tuple(records)


def _forward_window_extremes(
    trade_rows: tuple[SharedLabelPanelRow, ...],
    horizon: int,
) -> tuple[list[float], list[float]]:
    """Return (max high, min low) over rows[i+1 : i+1+horizon] for full windows.

    Output index ``i`` covers entries ``0 .. len(rows) - horizon - 1`` — exactly
    the entries whose forward window holds ``horizon`` trade bars. Computed with
    Polars rolling extremes (O(n) native) instead of a per-entry rescan.
    """

    import polars as pl

    high = pl.Series("high", [row.high for row in trade_rows], dtype=pl.Float64)
    low = pl.Series("low", [row.low for row in trade_rows], dtype=pl.Float64)
    # rolling extreme at index j summarizes [j - horizon + 1, j]; the forward
    # window of entry i is [i + 1, i + horizon], i.e. trailing index i + horizon.
    window_max_high = high.rolling_max(window_size=horizon).slice(horizon).to_list()
    window_min_low = low.rolling_min(window_size=horizon).slice(horizon).to_list()
    return window_max_high, window_min_low


def _barrier_records(
    definition: PathLabelDefinition,
    trade_rows: tuple[SharedLabelPanelRow, ...],
    *,
    panel_cache_key: int,
) -> tuple[LabelValueRecord, ...]:
    """Target-before-stop / triple-barrier with reference positional semantics.

    A vectorized full-window screen resolves the common no-touch case
    (HORIZON outcome) without scanning; only entries whose forward window can
    touch a barrier run the first-touch scan, which stops at the touching bar
    exactly like the reference family.
    """

    if definition.target_return is None or definition.stop_return is None:
        raise FastLabelPackError("target and stop returns are required for barrier labels")
    horizon = definition.horizon_steps
    count = len(trade_rows)
    if count < 2:
        return ()
    guard_results = _path_window_guard_results(
        trade_rows,
        horizon,
        panel_cache_key=panel_cache_key,
    )
    full_window_count = max(count - horizon, 0)
    no_touch = [False] * (count - 1)
    if full_window_count > 0:
        window_max_high, window_min_low = _forward_window_extremes(trade_rows, horizon)
        for index in range(full_window_count):
            entry = _entry_price(trade_rows[index], definition.price_field)
            if definition.direction is PathDirection.LONG:
                favorable_max = (window_max_high[index] - entry) / entry
                adverse_min = (window_min_low[index] - entry) / entry
            else:
                favorable_max = (entry - window_min_low[index]) / entry
                adverse_min = (entry - window_max_high[index]) / entry
            no_touch[index] = (
                favorable_max < definition.target_return
                and adverse_min > definition.stop_return
            )

    records: list[LabelValueRecord] = []
    for index in range(count - 1):
        source = trade_rows[index]
        future_rows = trade_rows[index + 1 : index + 1 + horizon]
        if not future_rows:
            continue
        guard_flags = guard_results[index]
        if guard_flags is None:
            continue
        if no_touch[index]:
            barrier: PathBarrier | None = PathBarrier.HORIZON
            resolution_row = trade_rows[index + horizon]
        else:
            barrier, resolution_row = _first_barrier(definition, source, future_rows)
            if barrier is None:
                if len(future_rows) < horizon:
                    continue
                barrier = PathBarrier.HORIZON
                resolution_row = future_rows[-1]
        if definition.name is PathLabelName.TARGET_BEFORE_STOP:
            value: bool | int | None = (
                None if barrier is PathBarrier.AMBIGUOUS else barrier is PathBarrier.TARGET
            )
        elif definition.name is PathLabelName.TRIPLE_BARRIER:
            value = _triple_barrier_value(barrier)
        else:  # pragma: no cover - guarded by caller routing
            raise FastLabelPackError(f"unsupported path label: {definition.name.value}")
        records.append(
            _value_record(
                definition,
                source=source,
                resolution_row=resolution_row,
                value=value,
                quality_flags=_merge_quality_flags(
                    _barrier_quality_flags(barrier),
                    guard_flags,
                ),
            )
        )
    return tuple(records)


def _path_window_guard_results(
    trade_rows: tuple[SharedLabelPanelRow, ...],
    horizon: int,
    *,
    panel_cache_key: int,
) -> tuple[tuple[str, ...] | None, ...]:
    count = len(trade_rows)
    if count < 2:
        return ()
    cache_key = (
        panel_cache_key,
        horizon,
        count,
        trade_rows[0].terminal_key,
        trade_rows[-1].terminal_key,
    )
    cached = _PATH_WINDOW_GUARD_CACHE.get(cache_key)
    if cached is not None:
        return cached
    terminal_by_key = _terminal_by_key(trade_rows)
    contract_segment_ends = _contract_segment_ends(trade_rows)
    roll_calendar_cache: dict[tuple[str, int, int], tuple[object, ...]] = {}
    results: list[tuple[str, ...] | None] = []
    for index, source in enumerate(trade_rows[:-1]):
        terminal_index = min(index + horizon, count - 1)
        if terminal_index >= contract_segment_ends[index]:
            results.append(None)
            continue
        results.append(
            _path_window_guard_flags(
                source,
                trade_rows[terminal_index],
                terminal_by_key=terminal_by_key,
                roll_calendar_cache=roll_calendar_cache,
            )
        )
    value = tuple(results)
    while len(_PATH_WINDOW_GUARD_CACHE) >= _PATH_WINDOW_GUARD_CACHE_MAX:
        _PATH_WINDOW_GUARD_CACHE.pop(next(iter(_PATH_WINDOW_GUARD_CACHE)), None)
    _PATH_WINDOW_GUARD_CACHE[cache_key] = value
    return value


def _path_window_guard_flags(
    source: SharedLabelPanelRow,
    terminal: SharedLabelPanelRow,
    *,
    terminal_by_key: Mapping[tuple[str, str, datetime], SharedLabelPanelRow],
    roll_calendar_cache: dict[tuple[str, int, int], tuple[object, ...]],
) -> tuple[str, ...] | None:
    try:
        guarded = _guarded_forward_terminal(
            source,
            terminal,
            terminal_by_key=terminal_by_key,
            roll_calendar_cache=roll_calendar_cache,
        )
    except Exception as exc:  # noqa: BLE001 - normalize shared guard errors for this family.
        raise FastLabelPackError("path label guard evaluation failed") from exc
    if guarded is None:
        return None
    effective_terminal, guard_flags = guarded
    if effective_terminal.terminal_key != terminal.terminal_key:
        return None
    return tuple(guard_flags)


def _terminal_by_key(
    trade_rows: tuple[SharedLabelPanelRow, ...],
) -> dict[tuple[str, str, datetime], SharedLabelPanelRow]:
    return {row.terminal_key: row for row in trade_rows}


def _contract_segment_ends(trade_rows: tuple[SharedLabelPanelRow, ...]) -> list[int]:
    count = len(trade_rows)
    ends = [count] * count
    current_end = count
    for index in range(count - 1, -1, -1):
        if index == count - 1:
            current_end = count
        else:
            current_key = (trade_rows[index].series_id, trade_rows[index].contract_id)
            next_key = (trade_rows[index + 1].series_id, trade_rows[index + 1].contract_id)
            if current_key != next_key:
                current_end = index + 1
        ends[index] = current_end
    return ends


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
    definition: PathLabelDefinition,
    trade_rows: tuple[SharedLabelPanelRow, ...],
) -> bool:
    if definition.price_field not in {"open", "high", "low", "close"}:
        return False
    if definition.price_field == "open" and any(row.open is None for row in trade_rows):
        return False
    return True


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


def _merge_quality_flags(*groups: Sequence[str]) -> tuple[str, ...]:
    flags: list[str] = []
    for group in groups:
        for flag in group:
            if not isinstance(flag, str) or not flag.strip():
                raise FastLabelPackError("quality_flags must contain non-empty strings")
            token = flag.strip().lower()
            if token not in flags:
                flags.append(token)
    return tuple(flags)


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
