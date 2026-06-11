"""Shared label panel and terminal contract for fast label producers.

This module is value-free contract substrate: it normalizes one synthetic or
canonical symbol-year panel, resolves guarded terminal indices, and derives
label availability timestamps from the governed ``LabelAvailabilityPolicy``.
It does not calculate label values, write registries, or derive identities.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta, time
from decimal import Decimal
from enum import StrEnum
from functools import lru_cache
from types import MappingProxyType
from typing import Any
from zoneinfo import ZoneInfo

from alpha_system.data.foundation.quotes import (
    BBO_QUARANTINE_QUALITY_FLAG,
    MISSING_BBO_QUALITY_FLAG,
)
from alpha_system.data.foundation.rolls import (
    RollCalendarRecord,
    build_analytic_cme_equity_index_quarterly_roll_calendar,
)
from alpha_system.labels.fast.materializer import FastLabelPackError
from alpha_system.labels.roll_guard import (
    DEFAULT_CROSS_ROLL_POLICY,
    DEFAULT_ROLL_WINDOW_DAYS_AFTER,
    DEFAULT_ROLL_WINDOW_DAYS_BEFORE,
    ROLL_GUARD_VERSION,
    ROLL_POLICY_ID,
    RollCrossPolicy,
    RollGuardAction,
    evaluate_roll_guard,
)
from alpha_system.labels.version import LabelAvailabilityPolicy, LabelContractSpec

_KNOWN_ROLL_ROOTS: frozenset[str] = frozenset({"ES", "NQ", "RTY"})
_MAINTENANCE_TIMEZONE = ZoneInfo("America/Chicago")
_RTH_SESSION_OPEN = time(8, 30)
_RTH_SESSION_CLOSE = time(15, 0)
_MAINTENANCE_BREAK_START = time(16, 0)
_MAINTENANCE_BREAK_END = time(17, 0)

MAINTENANCE_GUARD_VERSION = "maintenance_crossing_guard_v1"
MAINTENANCE_POLICY_ID = "cme_index_futures_daily_maintenance_break_v1"

QUALITY_FLAG_INSUFFICIENT_WINDOW = "insufficient_window"
QUALITY_FLAG_INPUT_GAP = "input_gap"
QUALITY_FLAG_SESSION_RESET = "session_reset"
QUALITY_FLAG_MAINTENANCE_CROSSING = "maintenance_crossing"
QUALITY_FLAG_BBO_GAP = "bbo_gap"
_DUPLICATE_BBO_KEY_FLAG = "duplicate_bbo_key"


class TerminalKind(StrEnum):
    """Terminal-index modes shared by the fast label packs."""

    FIXED_HORIZON = "fixed_horizon"
    SESSION_CLOSE = "session_close"
    MAINTENANCE_FLAT = "maintenance_flat"
    ROLL_TRUNCATION = "roll_truncation"


class TerminalGuardDisposition(StrEnum):
    """Guard disposition for one source row's terminal window."""

    PASS = "pass"
    DROP = "drop"
    TRUNCATE = "truncate"
    FLAG = "flag"
    INVALID = "invalid"


class LabelAvailabilityFamily(StrEnum):
    """Family-specific ``label_available_ts`` derivation modes."""

    FIXED_HORIZON = "fixed_horizon"
    COST_ADJUSTED = "cost_adjusted"
    PATH = "path"
    EVENT = "event"


@dataclass(frozen=True, slots=True)
class MaintenanceWindow:
    """One ex-ante daily CME maintenance window carried by a shared panel."""

    start_ts: datetime
    end_ts: datetime
    timezone: str = "America/Chicago"
    policy_id: str = MAINTENANCE_POLICY_ID
    guard_version: str = MAINTENANCE_GUARD_VERSION

    def __post_init__(self) -> None:
        start = _coerce_datetime(self.start_ts, "MaintenanceWindow.start_ts")
        end = _coerce_datetime(self.end_ts, "MaintenanceWindow.end_ts")
        if end <= start:
            raise FastLabelPackError("maintenance window end_ts must be after start_ts")
        object.__setattr__(self, "start_ts", start)
        object.__setattr__(self, "end_ts", end)


@dataclass(frozen=True, slots=True)
class SharedLabelPanelRow:
    """One wide immutable row in the shared label panel."""

    row_index: int
    instrument_id: str
    series_id: str
    contract_id: str
    event_ts: datetime
    bar_end_ts: datetime
    available_ts: datetime
    open: float | None
    trade_price: float
    high: float
    low: float
    volume: float | None
    bid: float | None = None
    ask: float | None = None
    bid_size: float | None = None
    ask_size: float | None = None
    mid: float | None = None
    spread: float | None = None
    microprice: float | None = None
    bbo_present: bool = False
    bbo_missing: bool = True
    bbo_quarantined: bool = False
    bbo_invariant_violation: bool = False
    quality_flags: Sequence[str] = ()
    bbo_quality_flags: Sequence[str] = ()
    session_label: str = ""
    session_segment_id: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.row_index, bool) or not isinstance(self.row_index, int):
            raise FastLabelPackError("SharedLabelPanelRow.row_index must be an integer")
        for field_name in ("instrument_id", "series_id", "contract_id"):
            object.__setattr__(self, field_name, _require_text(getattr(self, field_name)))
        object.__setattr__(self, "event_ts", _coerce_datetime(self.event_ts, "event_ts"))
        object.__setattr__(
            self,
            "bar_end_ts",
            _coerce_datetime(self.bar_end_ts, "bar_end_ts"),
        )
        object.__setattr__(
            self,
            "available_ts",
            _coerce_datetime(self.available_ts, "available_ts"),
        )
        object.__setattr__(
            self,
            "open",
            _to_positive_float(self.open, "open") if self.open is not None else None,
        )
        for field_name in ("trade_price", "high", "low"):
            object.__setattr__(
                self,
                field_name,
                _to_positive_float(getattr(self, field_name), field_name),
            )
        object.__setattr__(self, "volume", _to_float_or_none(self.volume, "volume"))
        for field_name in (
            "bid",
            "ask",
            "bid_size",
            "ask_size",
            "mid",
            "spread",
            "microprice",
        ):
            object.__setattr__(
                self,
                field_name,
                _to_float_or_none(getattr(self, field_name), field_name),
            )
        object.__setattr__(self, "quality_flags", _quality_flags(self.quality_flags))
        object.__setattr__(self, "bbo_quality_flags", _quality_flags(self.bbo_quality_flags))
        object.__setattr__(self, "session_label", str(self.session_label or ""))
        segment = self.session_segment_id or _session_segment_id(
            self.series_id,
            self.session_label,
            self.event_ts,
        )
        object.__setattr__(self, "session_segment_id", _require_text(segment))

    @property
    def terminal_key(self) -> tuple[str, str, datetime]:
        """Return the exact terminal lookup key used by the reference family."""

        return (self.series_id, self.contract_id, self.event_ts)


@dataclass(frozen=True, slots=True)
class SharedBBOQuoteRow:
    """One normalized BBO quote row anchored to its bar-end timestamp.

    Real canonical BBO event timestamps can be sub-minute samples. Post-P19
    cost-adjusted labels resolve source and terminal quotes by
    ``series_id + contract_id + bar_end_ts`` and emit records at ``bar_end_ts``.
    """

    instrument_id: str
    series_id: str
    contract_id: str
    event_ts: datetime
    bar_end_ts: datetime
    available_ts: datetime
    bid: float | None = None
    ask: float | None = None
    bid_size: float | None = None
    ask_size: float | None = None
    mid: float | None = None
    spread: float | None = None
    microprice: float | None = None
    bbo_missing: bool = False
    bbo_quarantined: bool = False
    bbo_invariant_violation: bool = False
    bbo_quality_flags: Sequence[str] = ()

    def __post_init__(self) -> None:
        for field_name in ("instrument_id", "series_id", "contract_id"):
            object.__setattr__(self, field_name, _require_text(getattr(self, field_name)))
        event_ts = _coerce_datetime(self.event_ts, "event_ts")
        bar_end_ts = _coerce_datetime(self.bar_end_ts, "bar_end_ts")
        if event_ts > bar_end_ts:
            raise FastLabelPackError(
                "SharedBBOQuoteRow.event_ts must be at or before bar_end_ts"
            )
        object.__setattr__(self, "event_ts", bar_end_ts)
        object.__setattr__(self, "bar_end_ts", bar_end_ts)
        object.__setattr__(
            self,
            "available_ts",
            _coerce_datetime(self.available_ts, "available_ts"),
        )
        for field_name in (
            "bid",
            "ask",
            "bid_size",
            "ask_size",
            "mid",
            "spread",
            "microprice",
        ):
            object.__setattr__(
                self,
                field_name,
                _to_float_or_none(getattr(self, field_name), field_name),
            )
        object.__setattr__(self, "bbo_quality_flags", _quality_flags(self.bbo_quality_flags))


@dataclass(frozen=True, slots=True)
class SharedLabelPanel:
    """Immutable shared per-symbol-year label panel."""

    symbol: str
    year: int
    rows: Sequence[SharedLabelPanelRow]
    roll_calendar: Sequence[RollCalendarRecord | Mapping[str, object]] = ()
    maintenance_windows: Sequence[MaintenanceWindow] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    bbo_rows: Sequence[SharedBBOQuoteRow] = ()
    _index_by_terminal_key: Mapping[tuple[str, str, datetime], int] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        symbol = _require_text(self.symbol).upper()
        if isinstance(self.year, bool) or not isinstance(self.year, int) or self.year < 1970:
            raise FastLabelPackError("SharedLabelPanel.year must be an integer >= 1970")
        rows = tuple(self.rows)
        if not rows:
            raise FastLabelPackError("SharedLabelPanel.rows must be non-empty")
        normalized_rows: list[SharedLabelPanelRow] = []
        index: dict[tuple[str, str, datetime], int] = {}
        for position, row in enumerate(rows):
            if not isinstance(row, SharedLabelPanelRow):
                raise FastLabelPackError("SharedLabelPanel rows must be SharedLabelPanelRow")
            normalized = row
            if normalized.row_index != position:
                normalized = _replace_row_index(normalized, position)
            key = normalized.terminal_key
            if key in index:
                raise FastLabelPackError(
                    "shared label panel requires unique series_id, contract_id, event_ts rows"
                )
            index[key] = position
            normalized_rows.append(normalized)
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "rows", tuple(normalized_rows))
        object.__setattr__(self, "roll_calendar", _coerce_roll_calendar(self.roll_calendar))
        object.__setattr__(self, "maintenance_windows", tuple(self.maintenance_windows))
        bbo_rows = _collapse_duplicate_bbo_quote_rows(tuple(self.bbo_rows))
        for quote_row in bbo_rows:
            if not isinstance(quote_row, SharedBBOQuoteRow):
                raise FastLabelPackError("SharedLabelPanel.bbo_rows must be SharedBBOQuoteRow")
        object.__setattr__(self, "bbo_rows", bbo_rows)
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )
        object.__setattr__(self, "_index_by_terminal_key", MappingProxyType(index))

    def row_at(self, row_index: int) -> SharedLabelPanelRow:
        """Return a row by immutable panel index."""

        if isinstance(row_index, bool) or not isinstance(row_index, int):
            raise FastLabelPackError("row_index must be an integer")
        return self.rows[row_index]

    def terminal_index_for(
        self,
        *,
        series_id: str,
        contract_id: str,
        event_ts: datetime,
    ) -> int | None:
        """Return the exact same-contract terminal row index, if present."""

        key = (
            _require_text(series_id),
            _require_text(contract_id),
            _coerce_datetime(event_ts, "event_ts"),
        )
        return self._index_by_terminal_key.get(key)


@dataclass(frozen=True, slots=True)
class TerminalRequest:
    """Batch terminal-index request for one terminal kind."""

    kind: TerminalKind | str
    horizon_minutes: int | None = None
    roll_policy: RollCrossPolicy | str = DEFAULT_CROSS_ROLL_POLICY
    price_basis: str = "close"

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _coerce_terminal_kind(self.kind))
        object.__setattr__(self, "roll_policy", _coerce_roll_policy(self.roll_policy))
        if self.horizon_minutes is not None:
            if (
                isinstance(self.horizon_minutes, bool)
                or not isinstance(self.horizon_minutes, int)
                or self.horizon_minutes <= 0
            ):
                raise FastLabelPackError("horizon_minutes must be a positive integer")
        if self.kind in {TerminalKind.FIXED_HORIZON, TerminalKind.ROLL_TRUNCATION}:
            if self.horizon_minutes is None:
                raise FastLabelPackError(f"{self.kind.value} terminals require horizon_minutes")
        if self.kind in {TerminalKind.SESSION_CLOSE, TerminalKind.MAINTENANCE_FLAT}:
            if self.horizon_minutes is not None:
                raise FastLabelPackError(f"{self.kind.value} terminals do not accept minutes")
        price_basis = _require_text(self.price_basis).lower()
        if price_basis not in {"close", "mid"}:
            raise FastLabelPackError("TerminalRequest.price_basis must be close or mid")
        object.__setattr__(self, "price_basis", price_basis)


@dataclass(frozen=True, slots=True)
class TerminalResolution:
    """Terminal-index resolution and guard metadata for one source row."""

    source_index: int
    kind: TerminalKind
    requested_terminal_ts: datetime | None
    terminal_index: int | None
    effective_terminal_ts: datetime | None
    disposition: TerminalGuardDisposition
    reason: str
    roll_policy: RollCrossPolicy
    quality_flags: Sequence[str] = ()

    def __post_init__(self) -> None:
        if isinstance(self.source_index, bool) or not isinstance(self.source_index, int):
            raise FastLabelPackError("TerminalResolution.source_index must be an integer")
        if self.requested_terminal_ts is not None:
            object.__setattr__(
                self,
                "requested_terminal_ts",
                _coerce_datetime(self.requested_terminal_ts, "requested_terminal_ts"),
            )
        if self.terminal_index is not None and (
            isinstance(self.terminal_index, bool) or not isinstance(self.terminal_index, int)
        ):
            raise FastLabelPackError("TerminalResolution.terminal_index must be an integer")
        if self.effective_terminal_ts is not None:
            object.__setattr__(
                self,
                "effective_terminal_ts",
                _coerce_datetime(self.effective_terminal_ts, "effective_terminal_ts"),
            )
        object.__setattr__(self, "kind", _coerce_terminal_kind(self.kind))
        object.__setattr__(self, "disposition", _coerce_disposition(self.disposition))
        object.__setattr__(self, "roll_policy", _coerce_roll_policy(self.roll_policy))
        object.__setattr__(self, "reason", _require_text(self.reason))
        object.__setattr__(self, "quality_flags", _quality_flags(self.quality_flags))

    @property
    def has_terminal(self) -> bool:
        """Return whether this resolution retained a terminal row."""

        return self.terminal_index is not None


@dataclass(frozen=True, slots=True)
class TerminalIndexModel:
    """Computed-once terminal-index model for one panel and request."""

    request: TerminalRequest
    resolutions: Sequence[TerminalResolution]

    def __post_init__(self) -> None:
        if not isinstance(self.request, TerminalRequest):
            raise FastLabelPackError("TerminalIndexModel.request must be a TerminalRequest")
        object.__setattr__(self, "resolutions", tuple(self.resolutions))


@dataclass(frozen=True, slots=True)
class LabelQualityMetadata:
    """Value-free gap and quality metadata derived from terminal resolution."""

    source_index: int
    terminal_index: int | None
    gap_reasons: Sequence[str]
    quality_flags: Sequence[str]
    bbo_missing: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "gap_reasons", _quality_flags(self.gap_reasons))
        object.__setattr__(self, "quality_flags", _quality_flags(self.quality_flags))


def build_shared_label_panel(
    *,
    symbol: str,
    year: int,
    ohlcv_rows: Sequence[Mapping[str, Any]],
    bbo_rows: Sequence[Mapping[str, Any]] = (),
    roll_calendar: Iterable[RollCalendarRecord | Mapping[str, object]] | None = None,
    root_symbol: str | None = None,
) -> SharedLabelPanel:
    """Build one wide immutable symbol-year label panel from synthetic/canonical rows."""

    if not ohlcv_rows:
        raise FastLabelPackError("shared label panel requires OHLCV rows")
    bbo_by_key = _index_bbo_rows(bbo_rows)
    rows: list[SharedLabelPanelRow] = []
    for ohlcv in sorted(
        ohlcv_rows,
        key=lambda item: (
            _require_text(item["series_id"]),
            _coerce_datetime(item["event_ts"], "event_ts"),
            _coerce_datetime(item["available_ts"], "available_ts"),
        ),
    ):
        event_ts = _coerce_datetime(ohlcv["event_ts"], "event_ts")
        series_id = _require_text(ohlcv["series_id"])
        contract_id = _require_text(ohlcv["contract_id"])
        bbo = bbo_by_key.get((series_id, contract_id, event_ts))
        rows.append(_shared_panel_row(len(rows), ohlcv, bbo))

    start_ts = min(row.event_ts for row in rows)
    end_ts = max(row.event_ts for row in rows)
    root = _normalize_root_symbol(root_symbol) if root_symbol is not None else _root_symbol(rows[0])
    calendar = (
        _coerce_roll_calendar(roll_calendar)
        if roll_calendar is not None
        else _analytic_roll_calendar(root, start_ts, end_ts)
    )
    return SharedLabelPanel(
        symbol=symbol,
        year=year,
        rows=tuple(rows),
        roll_calendar=calendar,
        maintenance_windows=_maintenance_windows(start_ts, end_ts),
        metadata={
            "contract_surface": "alpha_system.labels.fast.shared_label_panel.v1",
            "bbo_semantics": "BBO columns are proxy inputs only and are presence flagged",
            "roll_policy_id": ROLL_POLICY_ID,
            "roll_guard_version": ROLL_GUARD_VERSION,
            "maintenance_policy_id": MAINTENANCE_POLICY_ID,
            "maintenance_guard_version": MAINTENANCE_GUARD_VERSION,
        },
        bbo_rows=tuple(_shared_bbo_quote_row(row) for row in bbo_rows),
    )


def _shared_bbo_quote_row(bbo: Mapping[str, Any]) -> SharedBBOQuoteRow:
    flags = _quality_flags(bbo.get("quality_flags", ()))
    return SharedBBOQuoteRow(
        instrument_id=_require_text(bbo["instrument_id"]),
        series_id=_require_text(bbo["series_id"]),
        contract_id=_require_text(bbo["contract_id"]),
        event_ts=_coerce_datetime(bbo["event_ts"], "event_ts"),
        bar_end_ts=_coerce_datetime(bbo["bar_end_ts"], "bar_end_ts"),
        available_ts=_coerce_datetime(bbo["available_ts"], "available_ts"),
        bid=_to_float_or_none(bbo.get("bid"), "bid"),
        ask=_to_float_or_none(bbo.get("ask"), "ask"),
        bid_size=_to_float_or_none(bbo.get("bid_size"), "bid_size"),
        ask_size=_to_float_or_none(bbo.get("ask_size"), "ask_size"),
        mid=_to_float_or_none(bbo.get("mid"), "mid"),
        spread=_to_float_or_none(bbo.get("spread"), "spread"),
        microprice=_to_float_or_none(bbo.get("microprice"), "microprice"),
        bbo_missing=MISSING_BBO_QUALITY_FLAG in flags,
        bbo_quarantined=BBO_QUARANTINE_QUALITY_FLAG in flags,
        bbo_invariant_violation=not _bbo_invariants_hold(bbo),
        bbo_quality_flags=flags,
    )


def _collapse_duplicate_bbo_quote_rows(
    rows: Sequence[SharedBBOQuoteRow],
) -> tuple[SharedBBOQuoteRow, ...]:
    by_key: dict[tuple[str, str, datetime], SharedBBOQuoteRow] = {}
    order: list[tuple[str, str, datetime]] = []
    validated: list[SharedBBOQuoteRow] = []
    for row in rows:
        if not isinstance(row, SharedBBOQuoteRow):
            raise FastLabelPackError("SharedLabelPanel.bbo_rows must be SharedBBOQuoteRow")
        validated.append(row)
    for row in sorted(validated, key=lambda item: item.available_ts):
        key = (row.series_id, row.contract_id, row.bar_end_ts)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = row
            order.append(key)
            continue
        by_key[key] = replace(
            existing,
            bbo_quality_flags=_quality_flags(
                (*existing.bbo_quality_flags, _DUPLICATE_BBO_KEY_FLAG)
            ),
        )
    return tuple(by_key[key] for key in order)


def resolve_terminal_indices(
    panel: SharedLabelPanel,
    request: TerminalRequest,
) -> TerminalIndexModel:
    """Resolve terminal row indices once for every row in ``panel``."""

    if not isinstance(panel, SharedLabelPanel):
        raise FastLabelPackError("resolve_terminal_indices requires a SharedLabelPanel")
    request = request if isinstance(request, TerminalRequest) else TerminalRequest(request)
    close_out_indices = (
        _close_out_terminal_indices(panel, request.kind)
        if request.kind in {TerminalKind.SESSION_CLOSE, TerminalKind.MAINTENANCE_FLAT}
        else {}
    )
    resolutions = tuple(
        _resolve_terminal_for_row(panel, row, request, close_out_indices)
        for row in panel.rows
    )
    return TerminalIndexModel(request=request, resolutions=resolutions)


def derive_label_available_ts(
    family: LabelAvailabilityFamily | str,
    availability: LabelAvailabilityPolicy | LabelContractSpec,
    *,
    horizon_end_ts: datetime,
    terminal_available_ts: datetime | None = None,
    resolution_event_ts: datetime | None = None,
    resolution_available_ts: datetime | None = None,
    relevant_available_ts: Sequence[datetime] = (),
) -> datetime:
    """Derive ``label_available_ts`` using the governed family policy."""

    family = _coerce_availability_family(family)
    policy = _coerce_availability_policy(availability)
    horizon_end = _coerce_datetime(horizon_end_ts, "horizon_end_ts")
    candidates = [horizon_end, policy.availability_time]
    if family is LabelAvailabilityFamily.FIXED_HORIZON:
        if terminal_available_ts is None:
            raise FastLabelPackError("fixed-horizon availability requires terminal_available_ts")
        candidates.append(_coerce_datetime(terminal_available_ts, "terminal_available_ts"))
    elif family is LabelAvailabilityFamily.COST_ADJUSTED:
        if terminal_available_ts is not None:
            candidates.append(_coerce_datetime(terminal_available_ts, "terminal_available_ts"))
    elif family is LabelAvailabilityFamily.PATH:
        if resolution_event_ts is None or resolution_available_ts is None:
            raise FastLabelPackError(
                "path availability requires resolution_event_ts and resolution_available_ts"
            )
        candidates.extend(
            (
                _coerce_datetime(resolution_event_ts, "resolution_event_ts"),
                _coerce_datetime(resolution_available_ts, "resolution_available_ts"),
            )
        )
    else:
        candidates.extend(
            _coerce_datetime(item, "relevant_available_ts") for item in relevant_available_ts
        )
    return max(candidates)


def quality_metadata_for_resolution(
    panel: SharedLabelPanel,
    resolution: TerminalResolution,
    *,
    price_basis: str = "close",
) -> LabelQualityMetadata:
    """Return value-free gap/missingness flags for one terminal resolution."""

    if not isinstance(panel, SharedLabelPanel) or not isinstance(resolution, TerminalResolution):
        raise FastLabelPackError("quality metadata requires a panel and terminal resolution")
    price_basis = _require_text(price_basis).lower()
    if price_basis not in {"close", "mid"}:
        raise FastLabelPackError("price_basis must be close or mid")
    source = panel.row_at(resolution.source_index)
    terminal = (
        panel.row_at(resolution.terminal_index)
        if resolution.terminal_index is not None
        else None
    )
    flags = set(resolution.quality_flags)
    gap_reasons: set[str] = set()
    flags.update(_input_gap_flags(source, price_basis=price_basis, role="source"))
    if terminal is None:
        gap_reasons.add(QUALITY_FLAG_INSUFFICIENT_WINDOW)
    else:
        flags.update(_input_gap_flags(terminal, price_basis=price_basis, role="terminal"))
    for flag in flags:
        if flag in {
            QUALITY_FLAG_INSUFFICIENT_WINDOW,
            QUALITY_FLAG_INPUT_GAP,
            QUALITY_FLAG_SESSION_RESET,
            QUALITY_FLAG_MAINTENANCE_CROSSING,
            QUALITY_FLAG_BBO_GAP,
        }:
            gap_reasons.add(flag)
    return LabelQualityMetadata(
        source_index=resolution.source_index,
        terminal_index=resolution.terminal_index,
        gap_reasons=tuple(sorted(gap_reasons)),
        quality_flags=tuple(sorted(flags)),
        bbo_missing=(
            (price_basis == "mid" and source.bbo_missing)
            or (price_basis == "mid" and terminal is not None and terminal.bbo_missing)
        ),
    )


def _resolve_terminal_for_row(
    panel: SharedLabelPanel,
    source: SharedLabelPanelRow,
    request: TerminalRequest,
    close_out_indices: Mapping[tuple[str, str, str], int],
) -> TerminalResolution:
    if request.kind in {TerminalKind.FIXED_HORIZON, TerminalKind.ROLL_TRUNCATION}:
        assert request.horizon_minutes is not None
        requested_ts = source.event_ts + timedelta(minutes=request.horizon_minutes)
        terminal_index = panel.terminal_index_for(
            series_id=source.series_id,
            contract_id=source.contract_id,
            event_ts=requested_ts,
        )
    else:
        requested_ts = None
        terminal_index = close_out_indices.get(_close_out_scope_key(source, request.kind))
    if terminal_index is None:
        return TerminalResolution(
            source_index=source.row_index,
            kind=request.kind,
            requested_terminal_ts=requested_ts,
            terminal_index=None,
            effective_terminal_ts=None,
            disposition=TerminalGuardDisposition.DROP,
            reason=QUALITY_FLAG_INSUFFICIENT_WINDOW,
            roll_policy=request.roll_policy,
            quality_flags=(QUALITY_FLAG_INSUFFICIENT_WINDOW,),
        )
    terminal = panel.row_at(terminal_index)
    if terminal.event_ts <= source.event_ts:
        return TerminalResolution(
            source_index=source.row_index,
            kind=request.kind,
            requested_terminal_ts=terminal.event_ts,
            terminal_index=None,
            effective_terminal_ts=None,
            disposition=TerminalGuardDisposition.DROP,
            reason=QUALITY_FLAG_INSUFFICIENT_WINDOW,
            roll_policy=request.roll_policy,
            quality_flags=(QUALITY_FLAG_INSUFFICIENT_WINDOW,),
        )
    return _guard_terminal(panel, source, terminal, request)


def _guard_terminal(
    panel: SharedLabelPanel,
    source: SharedLabelPanelRow,
    terminal: SharedLabelPanelRow,
    request: TerminalRequest,
) -> TerminalResolution:
    if source.contract_id != terminal.contract_id:
        return _dropped_resolution(
            source,
            terminal,
            request,
            reason="contract_splice",
            flags=(QUALITY_FLAG_INSUFFICIENT_WINDOW,),
        )
    if _crosses_maintenance_break(source.event_ts, terminal.event_ts):
        return _dropped_resolution(
            source,
            terminal,
            request,
            reason=QUALITY_FLAG_MAINTENANCE_CROSSING,
            flags=(
                QUALITY_FLAG_SESSION_RESET,
                QUALITY_FLAG_MAINTENANCE_CROSSING,
                MAINTENANCE_POLICY_ID,
                MAINTENANCE_GUARD_VERSION,
            ),
        )

    root_symbol = _root_symbol(source)
    if root_symbol is None:
        return _kept_resolution(source, terminal, request, TerminalGuardDisposition.PASS, ())

    verdict = evaluate_roll_guard(
        entry_ts=source.event_ts,
        label_horizon_ts=terminal.event_ts,
        calendar=panel.roll_calendar,
        policy=request.roll_policy,
        root_symbol=root_symbol,
        roll_window_days_before=DEFAULT_ROLL_WINDOW_DAYS_BEFORE,
        roll_window_days_after=DEFAULT_ROLL_WINDOW_DAYS_AFTER,
    )
    roll_flags = _roll_guard_flags(verdict.action.value)
    if verdict.action is RollGuardAction.DROP or not verdict.valid:
        disposition = (
            TerminalGuardDisposition.INVALID
            if verdict.action is RollGuardAction.INVALID
            else TerminalGuardDisposition.DROP
        )
        return TerminalResolution(
            source_index=source.row_index,
            kind=request.kind,
            requested_terminal_ts=terminal.event_ts,
            terminal_index=None,
            effective_terminal_ts=verdict.effective_label_horizon_ts,
            disposition=disposition,
            reason=verdict.reason,
            roll_policy=request.roll_policy,
            quality_flags=roll_flags,
        )
    if verdict.action is RollGuardAction.TRUNCATE:
        if verdict.effective_label_horizon_ts is None:
            return _dropped_resolution(
                source,
                terminal,
                request,
                reason="roll_truncation_terminal_missing",
                flags=(*roll_flags, QUALITY_FLAG_INSUFFICIENT_WINDOW),
            )
        truncated_index = panel.terminal_index_for(
            series_id=source.series_id,
            contract_id=source.contract_id,
            event_ts=verdict.effective_label_horizon_ts,
        )
        if truncated_index is None:
            return _dropped_resolution(
                source,
                terminal,
                request,
                reason="roll_truncation_terminal_missing",
                flags=(*roll_flags, QUALITY_FLAG_INSUFFICIENT_WINDOW),
            )
        truncated = panel.row_at(truncated_index)
        return _kept_resolution(
            source,
            truncated,
            request,
            TerminalGuardDisposition.TRUNCATE,
            roll_flags,
            requested_terminal_ts=terminal.event_ts,
            reason=verdict.reason,
        )
    if verdict.action is RollGuardAction.FLAG:
        return _kept_resolution(
            source,
            terminal,
            request,
            TerminalGuardDisposition.FLAG,
            roll_flags,
            reason=verdict.reason,
        )
    return _kept_resolution(source, terminal, request, TerminalGuardDisposition.PASS, ())


def _kept_resolution(
    source: SharedLabelPanelRow,
    terminal: SharedLabelPanelRow,
    request: TerminalRequest,
    disposition: TerminalGuardDisposition,
    flags: Sequence[str],
    *,
    requested_terminal_ts: datetime | None = None,
    reason: str | None = None,
) -> TerminalResolution:
    return TerminalResolution(
        source_index=source.row_index,
        kind=request.kind,
        requested_terminal_ts=requested_terminal_ts or terminal.event_ts,
        terminal_index=terminal.row_index,
        effective_terminal_ts=terminal.event_ts,
        disposition=disposition,
        reason=reason or disposition.value,
        roll_policy=request.roll_policy,
        quality_flags=flags,
    )


def _dropped_resolution(
    source: SharedLabelPanelRow,
    terminal: SharedLabelPanelRow,
    request: TerminalRequest,
    *,
    reason: str,
    flags: Sequence[str],
) -> TerminalResolution:
    return TerminalResolution(
        source_index=source.row_index,
        kind=request.kind,
        requested_terminal_ts=terminal.event_ts,
        terminal_index=None,
        effective_terminal_ts=None,
        disposition=TerminalGuardDisposition.DROP,
        reason=reason,
        roll_policy=request.roll_policy,
        quality_flags=flags,
    )


def _shared_panel_row(
    row_index: int,
    ohlcv: Mapping[str, Any],
    bbo: Mapping[str, Any] | None,
) -> SharedLabelPanelRow:
    event_ts = _coerce_datetime(ohlcv["event_ts"], "event_ts")
    series_id = _require_text(ohlcv["series_id"])
    session_label = str(ohlcv.get("session_label") or "")
    bbo_flags = _quality_flags(bbo.get("quality_flags", ())) if bbo is not None else ()
    bbo_missing = bbo is None or MISSING_BBO_QUALITY_FLAG in bbo_flags
    bbo_quarantined = bbo is not None and BBO_QUARANTINE_QUALITY_FLAG in bbo_flags
    bbo_invariant = bbo is not None and not _bbo_invariants_hold(bbo)
    return SharedLabelPanelRow(
        row_index=row_index,
        instrument_id=_require_text(ohlcv["instrument_id"]),
        series_id=series_id,
        contract_id=_require_text(ohlcv["contract_id"]),
        event_ts=event_ts,
        bar_end_ts=_coerce_datetime(ohlcv["bar_end_ts"], "bar_end_ts"),
        available_ts=_coerce_datetime(ohlcv["available_ts"], "available_ts"),
        open=_to_positive_float(ohlcv.get("open", ohlcv["close"]), "open"),
        trade_price=_to_positive_float(ohlcv["close"], "close"),
        high=_to_positive_float(ohlcv["high"], "high"),
        low=_to_positive_float(ohlcv["low"], "low"),
        volume=_to_float_or_none(ohlcv.get("volume"), "volume"),
        bid=_to_float_or_none(bbo.get("bid"), "bid") if bbo is not None else None,
        ask=_to_float_or_none(bbo.get("ask"), "ask") if bbo is not None else None,
        bid_size=_to_float_or_none(bbo.get("bid_size"), "bid_size") if bbo is not None else None,
        ask_size=_to_float_or_none(bbo.get("ask_size"), "ask_size") if bbo is not None else None,
        mid=_to_float_or_none(bbo.get("mid"), "mid") if bbo is not None else None,
        spread=_to_float_or_none(bbo.get("spread"), "spread") if bbo is not None else None,
        microprice=_to_float_or_none(bbo.get("microprice"), "microprice")
        if bbo is not None
        else None,
        bbo_present=(
            bbo is not None
            and not bbo_missing
            and not bbo_quarantined
            and not bbo_invariant
        ),
        bbo_missing=bbo_missing,
        bbo_quarantined=bbo_quarantined,
        bbo_invariant_violation=bbo_invariant,
        quality_flags=_quality_flags(ohlcv.get("quality_flags", ())),
        bbo_quality_flags=bbo_flags,
        session_label=session_label,
        session_segment_id=_session_segment_id(series_id, session_label, event_ts),
    )


def _index_bbo_rows(
    bbo_rows: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, str, datetime], Mapping[str, Any]]:
    index: dict[tuple[str, str, datetime], Mapping[str, Any]] = {}
    for row in bbo_rows:
        key = (
            _require_text(row["series_id"]),
            _require_text(row["contract_id"]),
            _coerce_datetime(row["event_ts"], "event_ts"),
        )
        if key in index:
            raise FastLabelPackError("BBO rows must be unique by series_id, contract_id, event_ts")
        index[key] = row
    return index


def _close_out_terminal_indices(
    panel: SharedLabelPanel,
    kind: TerminalKind,
) -> dict[tuple[str, str, str], int]:
    terminals: dict[tuple[str, str, str], int] = {}
    for row in panel.rows:
        if not _is_close_out_terminal_candidate(row, kind):
            continue
        key = _close_out_scope_key(row, kind)
        previous = terminals.get(key)
        if previous is None or row.event_ts > panel.row_at(previous).event_ts:
            terminals[key] = row.row_index
    return terminals


def _is_close_out_terminal_candidate(row: SharedLabelPanelRow, kind: TerminalKind) -> bool:
    local = _maintenance_local(row.event_ts)
    if kind is TerminalKind.SESSION_CLOSE:
        return _RTH_SESSION_OPEN <= local.time() <= _RTH_SESSION_CLOSE
    if kind is TerminalKind.MAINTENANCE_FLAT:
        return local.time() <= _MAINTENANCE_BREAK_START
    raise FastLabelPackError(f"unsupported close-out terminal kind: {kind}")


def _close_out_scope_key(row: SharedLabelPanelRow, kind: TerminalKind) -> tuple[str, str, str]:
    trade_date = _cme_trade_date(row.event_ts).isoformat()
    if kind is TerminalKind.SESSION_CLOSE:
        boundary = f"rth_close:{trade_date}"
    elif kind is TerminalKind.MAINTENANCE_FLAT:
        boundary = f"maintenance_break:{trade_date}"
    else:
        raise FastLabelPackError(f"unsupported close-out terminal kind: {kind}")
    return (row.series_id, row.contract_id, boundary)


def _cme_trade_date(value: datetime) -> Any:
    local = _maintenance_local(value)
    if local.time() >= _MAINTENANCE_BREAK_END:
        return local.date() + timedelta(days=1)
    return local.date()


@lru_cache(maxsize=1 << 18)
def _maintenance_local_cached(value: datetime) -> datetime:
    return value.astimezone(_MAINTENANCE_TIMEZONE)


def _maintenance_local(value: datetime) -> datetime:
    # Pure timezone conversion, memoized: terminal resolution converts the
    # same panel timestamps once per horizon per role, which dominated the
    # guard scan in the LCFP-P08 profile.
    return _maintenance_local_cached(_coerce_datetime(value, "event_ts"))


def _maintenance_windows(start_ts: datetime, end_ts: datetime) -> tuple[MaintenanceWindow, ...]:
    start_local = _maintenance_local(start_ts)
    end_local = _maintenance_local(end_ts)
    day = start_local.date()
    windows: list[MaintenanceWindow] = []
    while day <= end_local.date():
        start = datetime.combine(day, _MAINTENANCE_BREAK_START, _MAINTENANCE_TIMEZONE)
        end = datetime.combine(day, _MAINTENANCE_BREAK_END, _MAINTENANCE_TIMEZONE)
        windows.append(
            MaintenanceWindow(
                start_ts=start.astimezone(UTC),
                end_ts=end.astimezone(UTC),
            )
        )
        day += timedelta(days=1)
    return tuple(windows)


def _crosses_maintenance_break(entry_ts: datetime, terminal_ts: datetime) -> bool:
    entry_local = _maintenance_local(entry_ts)
    terminal_local = _maintenance_local(terminal_ts)
    if terminal_local < entry_local:
        return False
    day = entry_local.date()
    while day <= terminal_local.date():
        break_start = datetime.combine(day, _MAINTENANCE_BREAK_START, _MAINTENANCE_TIMEZONE)
        break_end = datetime.combine(day, _MAINTENANCE_BREAK_END, _MAINTENANCE_TIMEZONE)
        if entry_local < break_end and terminal_local > break_start:
            return True
        day += timedelta(days=1)
    return False


def _analytic_roll_calendar(
    root_symbol: str | None,
    start_ts: datetime,
    end_ts: datetime,
) -> tuple[RollCalendarRecord, ...]:
    if root_symbol is None:
        return ()
    return build_analytic_cme_equity_index_quarterly_roll_calendar(
        root_symbols=(root_symbol,),
        start_year=min(start_ts.year, end_ts.year),
        end_year=max(start_ts.year, end_ts.year),
    )


def _coerce_roll_calendar(
    calendar: Iterable[RollCalendarRecord | Mapping[str, object]],
) -> tuple[RollCalendarRecord, ...]:
    return tuple(
        item if isinstance(item, RollCalendarRecord) else RollCalendarRecord.from_mapping(item)
        for item in calendar
    )


def _root_symbol(row: SharedLabelPanelRow) -> str | None:
    return _root_symbol_cached((row.instrument_id, row.contract_id, row.series_id))


@lru_cache(maxsize=4096)
def _root_symbol_cached(candidates: tuple[str, str, str]) -> str | None:
    for value in candidates:
        text = value.upper()
        tokens = tuple(token for token in re.split(r"[^A-Z0-9]+|_", text) if token)
        for root in sorted(_KNOWN_ROLL_ROOTS, key=len, reverse=True):
            if root in tokens or text.startswith(root):
                return root
            if any(token.startswith(root) and token[len(root) :].isdigit() for token in tokens):
                return root
    return None


def _normalize_root_symbol(value: str) -> str:
    root = _require_text(value).upper()
    if root not in _KNOWN_ROLL_ROOTS:
        allowed = ", ".join(sorted(_KNOWN_ROLL_ROOTS))
        raise FastLabelPackError(f"root_symbol must be one of: {allowed}")
    return root


def _roll_guard_flags(action: str) -> tuple[str, ...]:
    return _quality_flags(
        (
            "roll_splice_guard",
            f"roll_splice_{action}",
            ROLL_POLICY_ID,
            ROLL_GUARD_VERSION,
        )
    )


def _input_gap_flags(
    row: SharedLabelPanelRow,
    *,
    price_basis: str,
    role: str,
) -> tuple[str, ...]:
    flags: set[str] = set()
    if price_basis == "close":
        if "no_trade" in row.quality_flags:
            flags.update((QUALITY_FLAG_INPUT_GAP, f"{role}_not_trade", *row.quality_flags))
    else:
        if not row.bbo_present:
            flags.update(
                (
                    QUALITY_FLAG_INPUT_GAP,
                    QUALITY_FLAG_BBO_GAP,
                    f"{role}_bbo_gap",
                    *row.bbo_quality_flags,
                )
            )
            if row.bbo_missing:
                flags.add(MISSING_BBO_QUALITY_FLAG)
            if row.bbo_quarantined:
                flags.add(BBO_QUARANTINE_QUALITY_FLAG)
            if row.bbo_invariant_violation:
                flags.add("bbo_invariant_violation")
    return tuple(sorted(flags))


def _bbo_invariants_hold(row: Mapping[str, Any]) -> bool:
    bid = _to_float_or_none(row.get("bid"), "bid")
    ask = _to_float_or_none(row.get("ask"), "ask")
    bid_size = _to_float_or_none(row.get("bid_size"), "bid_size")
    ask_size = _to_float_or_none(row.get("ask_size"), "ask_size")
    mid = _to_float_or_none(row.get("mid"), "mid")
    spread = _to_float_or_none(row.get("spread"), "spread")
    if None in {bid, ask, bid_size, ask_size, mid, spread}:
        return False
    assert bid is not None
    assert ask is not None
    assert bid_size is not None
    assert ask_size is not None
    assert mid is not None
    assert spread is not None
    if ask < bid:
        return False
    if bid_size <= 0.0 or ask_size <= 0.0:
        return False
    if not math.isclose(mid, (bid + ask) / 2.0, rel_tol=0.0, abs_tol=0.0):
        return False
    return math.isclose(spread, ask - bid, rel_tol=0.0, abs_tol=0.0)


def _replace_row_index(row: SharedLabelPanelRow, row_index: int) -> SharedLabelPanelRow:
    return SharedLabelPanelRow(
        row_index=row_index,
        instrument_id=row.instrument_id,
        series_id=row.series_id,
        contract_id=row.contract_id,
        event_ts=row.event_ts,
        bar_end_ts=row.bar_end_ts,
        available_ts=row.available_ts,
        open=row.open,
        trade_price=row.trade_price,
        high=row.high,
        low=row.low,
        volume=row.volume,
        bid=row.bid,
        ask=row.ask,
        bid_size=row.bid_size,
        ask_size=row.ask_size,
        mid=row.mid,
        spread=row.spread,
        microprice=row.microprice,
        bbo_present=row.bbo_present,
        bbo_missing=row.bbo_missing,
        bbo_quarantined=row.bbo_quarantined,
        bbo_invariant_violation=row.bbo_invariant_violation,
        quality_flags=row.quality_flags,
        bbo_quality_flags=row.bbo_quality_flags,
        session_label=row.session_label,
        session_segment_id=row.session_segment_id,
    )


def _session_segment_id(series_id: str, session_label: str, event_ts: datetime) -> str:
    label = (session_label or "unknown").strip().lower() or "unknown"
    return f"{series_id}:{label}:{_cme_trade_date(event_ts).isoformat()}"


def _coerce_availability_policy(
    value: LabelAvailabilityPolicy | LabelContractSpec,
) -> LabelAvailabilityPolicy:
    if isinstance(value, LabelContractSpec):
        return value.availability_policy
    if not isinstance(value, LabelAvailabilityPolicy):
        raise FastLabelPackError("availability must be a LabelAvailabilityPolicy or contract")
    return value


def _coerce_terminal_kind(value: TerminalKind | str) -> TerminalKind:
    if isinstance(value, TerminalKind):
        return value
    if isinstance(value, str):
        try:
            return TerminalKind(value.strip().lower())
        except ValueError as exc:
            allowed = ", ".join(item.value for item in TerminalKind)
            raise FastLabelPackError(f"terminal kind must be one of: {allowed}") from exc
    raise FastLabelPackError("terminal kind must be a string")


def _coerce_disposition(value: TerminalGuardDisposition | str) -> TerminalGuardDisposition:
    if isinstance(value, TerminalGuardDisposition):
        return value
    if isinstance(value, str):
        try:
            return TerminalGuardDisposition(value.strip().lower())
        except ValueError as exc:
            allowed = ", ".join(item.value for item in TerminalGuardDisposition)
            raise FastLabelPackError(f"terminal disposition must be one of: {allowed}") from exc
    raise FastLabelPackError("terminal disposition must be a string")


def _coerce_roll_policy(value: RollCrossPolicy | str) -> RollCrossPolicy:
    if isinstance(value, RollCrossPolicy):
        return value
    if isinstance(value, str):
        try:
            return RollCrossPolicy(value.strip().lower())
        except ValueError as exc:
            allowed = ", ".join(item.value for item in RollCrossPolicy)
            raise FastLabelPackError(f"roll policy must be one of: {allowed}") from exc
    raise FastLabelPackError("roll policy must be a string")


def _coerce_availability_family(value: LabelAvailabilityFamily | str) -> LabelAvailabilityFamily:
    if isinstance(value, LabelAvailabilityFamily):
        return value
    if isinstance(value, str):
        try:
            return LabelAvailabilityFamily(value.strip().lower())
        except ValueError as exc:
            allowed = ", ".join(item.value for item in LabelAvailabilityFamily)
            raise FastLabelPackError(f"availability family must be one of: {allowed}") from exc
    raise FastLabelPackError("availability family must be a string")


def _quality_flags(value: object) -> tuple[str, ...]:
    if value is None:
        flags: Sequence[object] = ()
    elif isinstance(value, str):
        flags = (value,)
    elif isinstance(value, Sequence):
        flags = value
    else:
        raise FastLabelPackError("quality flags must be a sequence of strings")
    normalized: set[str] = set()
    for flag in flags:
        if not isinstance(flag, str) or not flag.strip():
            raise FastLabelPackError("quality flag entries must be non-empty strings")
        normalized.add(flag.strip().lower())
    return tuple(sorted(normalized))


def _coerce_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise FastLabelPackError(f"{field_name} must be a timezone-aware datetime")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise FastLabelPackError(f"{field_name} must be timezone-aware")
    return parsed.astimezone(UTC)


def _to_positive_float(value: object, field_name: str) -> float:
    parsed = _to_float(value, field_name)
    if parsed <= 0.0:
        raise FastLabelPackError(f"{field_name} must be positive")
    return parsed


def _to_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or value is None:
        raise FastLabelPackError(f"{field_name} must be numeric")
    if isinstance(value, Decimal):
        value = float(value)
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise FastLabelPackError(f"{field_name} must be numeric") from exc
    if not math.isfinite(parsed):
        raise FastLabelPackError(f"{field_name} must be finite")
    return parsed


def _to_float_or_none(value: object, field_name: str) -> float | None:
    if value is None or value == "":
        return None
    return _to_float(value, field_name)


def _require_text(value: object) -> str:
    if not isinstance(value, str):
        raise FastLabelPackError("value must be a non-empty string")
    text = value.strip()
    if not text or "\n" in text or "\r" in text:
        raise FastLabelPackError("value must be a non-empty single-line string")
    return text


__all__ = [
    "MAINTENANCE_GUARD_VERSION",
    "MAINTENANCE_POLICY_ID",
    "QUALITY_FLAG_BBO_GAP",
    "QUALITY_FLAG_INPUT_GAP",
    "QUALITY_FLAG_INSUFFICIENT_WINDOW",
    "QUALITY_FLAG_MAINTENANCE_CROSSING",
    "QUALITY_FLAG_SESSION_RESET",
    "LabelAvailabilityFamily",
    "LabelQualityMetadata",
    "MaintenanceWindow",
    "SharedLabelPanel",
    "SharedBBOQuoteRow",
    "SharedLabelPanelRow",
    "TerminalGuardDisposition",
    "TerminalIndexModel",
    "TerminalKind",
    "TerminalRequest",
    "TerminalResolution",
    "build_shared_label_panel",
    "derive_label_available_ts",
    "quality_metadata_for_resolution",
    "resolve_terminal_indices",
]
