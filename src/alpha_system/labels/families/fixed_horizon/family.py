"""Fixed-horizon and close-out trade-close forward-return labels."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Any
from zoneinfo import ZoneInfo

from alpha_system.data.foundation.rolls import (
    RollCalendarRecord,
    build_analytic_cme_equity_index_quarterly_roll_calendar,
)
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
    OHLCVInputRow,
    OHLCVInputView,
)
from alpha_system.features.semantics import bbo_quote_semantics, is_real_trade_bar
from alpha_system.governance.label_spec import LabelSpec
from alpha_system.labels.version import (
    LabelContractSpec,
    LabelFamily,
    LabelInputSpec,
    LabelValueRecord,
    LabelVersion,
)
from alpha_system.labels.roll_guard import (
    DEFAULT_CROSS_ROLL_POLICY,
    DEFAULT_ROLL_WINDOW_DAYS_AFTER,
    DEFAULT_ROLL_WINDOW_DAYS_BEFORE,
    ROLL_GUARD_VERSION,
    ROLL_POLICY_ID,
    RollGuardAction,
    evaluate_roll_guard,
)


class FixedHorizonLabelError(ValueError):
    """Raised when fixed-horizon label construction or calculation fails closed."""


class FixedHorizonLabelName(StrEnum):
    """Supported fixed-horizon and close-out label names."""

    FWD_RET_1M = "fwd_ret_1m"
    FWD_RET_3M = "fwd_ret_3m"
    FWD_RET_5M = "fwd_ret_5m"
    FWD_RET_10M = "fwd_ret_10m"
    FWD_RET_15M = "fwd_ret_15m"
    FWD_RET_30M = "fwd_ret_30m"
    FWD_RET_60M = "fwd_ret_60m"
    FWD_RET_120M = "fwd_ret_120m"
    FWD_RET_240M = "fwd_ret_240m"
    SESSION_CLOSE = "session_close"
    MAINTENANCE_FLAT = "maintenance_flat"
    MID_FWD_RET_1M = "mid_fwd_ret_1m"
    MID_FWD_RET_3M = "mid_fwd_ret_3m"
    MID_FWD_RET_5M = "mid_fwd_ret_5m"
    MID_FWD_RET_10M = "mid_fwd_ret_10m"
    MID_FWD_RET_30M = "mid_fwd_ret_30m"


OVERLAP_METADATA_VERSION = "horizon_overlap_metadata_v1"


@dataclass(frozen=True, slots=True)
class HorizonOverlapMetadata:
    """Rows-vs-effective-samples metadata for overlapping fixed-horizon labels."""

    label_id: str
    horizon_minutes: int
    raw_row_count: int
    effective_sample_count: int
    sampling_interval_minutes: int = 1
    method: str = "floor(raw_row_count / horizon_bars)"
    rows_are_independent: bool = False
    metadata_version: str = OVERLAP_METADATA_VERSION

    @property
    def horizon_bars(self) -> int:
        return max(1, math.ceil(self.horizon_minutes / self.sampling_interval_minutes))

    @property
    def overlap_fraction(self) -> float:
        if self.raw_row_count <= 0:
            return 0.0
        return 1.0 - (self.effective_sample_count / self.raw_row_count)

    def to_dict(self) -> dict[str, int | float | str | bool]:
        return {
            "metadata_version": self.metadata_version,
            "label_id": self.label_id,
            "horizon_minutes": self.horizon_minutes,
            "sampling_interval_minutes": self.sampling_interval_minutes,
            "horizon_bars": self.horizon_bars,
            "raw_row_count": self.raw_row_count,
            "effective_sample_count": self.effective_sample_count,
            "overlap_fraction": self.overlap_fraction,
            "rows_are_independent": self.rows_are_independent,
            "method": self.method,
        }


@dataclass(frozen=True, slots=True)
class FixedHorizonLabelDefinition:
    """Governed, versioned fixed-horizon label definition."""

    name: FixedHorizonLabelName
    contract: LabelContractSpec
    version: LabelVersion

    def __post_init__(self) -> None:
        name = _coerce_label_name(self.name)
        if not isinstance(self.contract, LabelContractSpec):
            raise FixedHorizonLabelError("contract must be a LabelContractSpec")
        if self.contract.family is not LabelFamily.FIXED_HORIZON:
            raise FixedHorizonLabelError("contract must belong to LabelFamily.FIXED_HORIZON")
        if self.contract.label_id != name.value:
            raise FixedHorizonLabelError("contract label_id must match the label name")
        if not isinstance(self.version, LabelVersion):
            raise FixedHorizonLabelError("version must be a LabelVersion")
        if self.version != self.contract.derive_label_version():
            raise FixedHorizonLabelError("LabelVersion does not match LabelContractSpec")
        object.__setattr__(self, "name", name)

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

    @property
    def horizon_minutes(self) -> int:
        """Return the fixed forward horizon in minutes."""

        if self.name in _CLOSE_OUT_LABELS:
            raise FixedHorizonLabelError(
                f"{self.name.value} is a symbolic close-out horizon, not a fixed minute horizon"
            )
        return _HORIZON_MINUTES[self.name]

    @property
    def is_midprice(self) -> bool:
        """Return whether this definition consumes canonical BBO midprice."""

        return self.name in _MIDPRICE_LABELS

    @property
    def price_basis(self) -> str:
        """Return the source price basis used by this label."""

        return "mid" if self.is_midprice else "close"

    def validate_not_live_feature(self, feature_references: Any) -> object:
        """Fail closed if this label is reachable as a live feature input."""

        return self.contract.validate_live_feature_references(feature_references)


_TRADE_PRICE_LABELS: frozenset[FixedHorizonLabelName] = frozenset(
    {
        FixedHorizonLabelName.FWD_RET_1M,
        FixedHorizonLabelName.FWD_RET_3M,
        FixedHorizonLabelName.FWD_RET_5M,
        FixedHorizonLabelName.FWD_RET_10M,
        FixedHorizonLabelName.FWD_RET_15M,
        FixedHorizonLabelName.FWD_RET_30M,
        FixedHorizonLabelName.FWD_RET_60M,
        FixedHorizonLabelName.FWD_RET_120M,
        FixedHorizonLabelName.FWD_RET_240M,
        FixedHorizonLabelName.SESSION_CLOSE,
        FixedHorizonLabelName.MAINTENANCE_FLAT,
    }
)
_MIDPRICE_LABELS: frozenset[FixedHorizonLabelName] = frozenset(
    {
        FixedHorizonLabelName.MID_FWD_RET_1M,
        FixedHorizonLabelName.MID_FWD_RET_3M,
        FixedHorizonLabelName.MID_FWD_RET_5M,
        FixedHorizonLabelName.MID_FWD_RET_10M,
        FixedHorizonLabelName.MID_FWD_RET_30M,
    }
)
_HORIZON_MINUTES: dict[FixedHorizonLabelName, int] = {
    FixedHorizonLabelName.FWD_RET_1M: 1,
    FixedHorizonLabelName.FWD_RET_3M: 3,
    FixedHorizonLabelName.FWD_RET_5M: 5,
    FixedHorizonLabelName.FWD_RET_10M: 10,
    FixedHorizonLabelName.FWD_RET_15M: 15,
    FixedHorizonLabelName.FWD_RET_30M: 30,
    FixedHorizonLabelName.FWD_RET_60M: 60,
    FixedHorizonLabelName.FWD_RET_120M: 120,
    FixedHorizonLabelName.FWD_RET_240M: 240,
    FixedHorizonLabelName.MID_FWD_RET_1M: 1,
    FixedHorizonLabelName.MID_FWD_RET_3M: 3,
    FixedHorizonLabelName.MID_FWD_RET_5M: 5,
    FixedHorizonLabelName.MID_FWD_RET_10M: 10,
    FixedHorizonLabelName.MID_FWD_RET_30M: 30,
}
_CLOSE_OUT_LABELS: frozenset[FixedHorizonLabelName] = frozenset(
    {
        FixedHorizonLabelName.SESSION_CLOSE,
        FixedHorizonLabelName.MAINTENANCE_FLAT,
    }
)
_CLOSE_OUT_HORIZON_LENGTH = 1
_CLOSE_OUT_PATH = "trade_price_close_out_return"
_PATH_BY_PRICE_BASIS: dict[str, str] = {
    "close": "trade_price_forward_return",
    "mid": "midprice_forward_return",
}
_NUMERIC_TYPES = (int, float, Decimal)
_KNOWN_ROLL_ROOTS: frozenset[str] = frozenset({"ES", "NQ", "RTY"})
_MAINTENANCE_TIMEZONE = ZoneInfo("America/Chicago")
_RTH_SESSION_OPEN = time(8, 30)
_RTH_SESSION_CLOSE = time(15, 0)
_MAINTENANCE_BREAK_START = time(16, 0)
_MAINTENANCE_BREAK_END = time(17, 0)
MAINTENANCE_GUARD_VERSION = "maintenance_crossing_guard_v1"
MAINTENANCE_POLICY_ID = "cme_index_futures_daily_maintenance_break_v1"


def supported_fixed_horizon_labels() -> tuple[FixedHorizonLabelName, ...]:
    """Return the complete FLF-P17 fixed-horizon label list."""

    return tuple(FixedHorizonLabelName)


def compute_horizon_overlap_metadata(
    name: FixedHorizonLabelName | str,
    *,
    raw_row_count: int,
    sampling_interval_minutes: int = 1,
) -> HorizonOverlapMetadata:
    """Return conservative overlap-aware N_eff metadata for one label output."""

    label_name = _coerce_label_name(name)
    if isinstance(raw_row_count, bool) or not isinstance(raw_row_count, int) or raw_row_count < 0:
        raise FixedHorizonLabelError("raw_row_count must be a non-negative integer")
    if (
        isinstance(sampling_interval_minutes, bool)
        or not isinstance(sampling_interval_minutes, int)
        or sampling_interval_minutes <= 0
    ):
        raise FixedHorizonLabelError("sampling_interval_minutes must be a positive integer")
    horizon_minutes = _HORIZON_MINUTES[label_name]
    horizon_bars = max(1, math.ceil(horizon_minutes / sampling_interval_minutes))
    effective = 0 if raw_row_count == 0 else max(1, raw_row_count // horizon_bars)
    effective = min(raw_row_count, effective)
    return HorizonOverlapMetadata(
        label_id=label_name.value,
        horizon_minutes=horizon_minutes,
        sampling_interval_minutes=sampling_interval_minutes,
        raw_row_count=raw_row_count,
        effective_sample_count=effective,
    )


def build_fixed_horizon_label_definition(
    name: FixedHorizonLabelName | str,
    governance_label_spec: LabelSpec | Mapping[str, Any] | None,
    *,
    dataset_version_ids: Sequence[str] = (),
    materialization_scope: Mapping[str, Any] | None = None,
) -> FixedHorizonLabelDefinition:
    """Build one governed fixed-horizon label definition.

    A valid governance `LabelSpec` is the only admission path. Missing,
    malformed, horizon-mismatched, or family-mismatched `lspec_` bindings fail
    before a label version can be derived.
    """

    label_name = _coerce_label_name(name)
    spec = _coerce_governance_label_spec(governance_label_spec)
    _validate_label_spec_matches_name(label_name, spec)
    if _is_close_out_label(label_name):
        contract_metadata = _close_out_contract_metadata(label_name)
    else:
        contract_metadata = {
            "campaign": "ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1",
            "phase": "FUTSUB-P17" if _is_extended_horizon(label_name) else "FUTSUB-P16",
            "materialization": "in_memory_records_only",
            "price_basis": _price_basis(label_name),
            "horizon_minutes": _HORIZON_MINUTES[label_name],
            "legal_consumer": "labels_only",
            "claims": "descriptive_label_substrate_only",
            "terminal_key": "series_id+contract_id+event_ts",
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
        }
        if _is_extended_horizon(label_name):
            contract_metadata["horizon_overlap_metadata"] = _horizon_overlap_contract_metadata(
                label_name
            )
    scope = _materialization_scope_metadata(materialization_scope)
    if scope:
        contract_metadata["materialization_scope"] = scope

    contract = LabelContractSpec.from_label_spec(
        label_id=label_name.value,
        family=LabelFamily.FIXED_HORIZON,
        governance_label_spec=spec,
        inputs=_label_inputs(label_name, dataset_version_ids),
        window=_future_window(label_name),
        contract_metadata=contract_metadata,
    )
    return FixedHorizonLabelDefinition(
        name=label_name,
        contract=contract,
        version=contract.derive_label_version(),
    )


def build_fixed_horizon_label_definitions(
    governance_label_specs: Mapping[
        FixedHorizonLabelName | str,
        LabelSpec | Mapping[str, Any] | None,
    ],
    *,
    dataset_version_ids: Sequence[str] = (),
) -> tuple[FixedHorizonLabelDefinition, ...]:
    """Build multiple fixed-horizon definitions from governed label specs."""

    if not isinstance(governance_label_specs, Mapping):
        raise FixedHorizonLabelError("governance_label_specs must be a mapping")
    return tuple(
        build_fixed_horizon_label_definition(
            name,
            governance_spec,
            dataset_version_ids=dataset_version_ids,
        )
        for name, governance_spec in governance_label_specs.items()
    )


def compute_fixed_horizon_label(
    definition: FixedHorizonLabelDefinition,
    input_view: OHLCVInputView | BBOInputView | CanonicalInputViews,
) -> tuple[LabelValueRecord, ...]:
    """Compute one fixed-horizon label as in-memory value records.

    Trailing rows without an exact horizon terminal row are excluded. The
    function does not fill, interpolate, materialize, persist, or register
    label values.
    """

    definition = _require_definition(definition)
    if definition.is_midprice:
        return _compute_midprice_forward_returns(definition, _coerce_bbo_view(input_view))
    return _compute_trade_price_forward_returns(definition, _coerce_ohlcv_view(input_view))


def compute_fixed_horizon_labels(
    definitions: Iterable[FixedHorizonLabelDefinition],
    input_views: OHLCVInputView | BBOInputView | CanonicalInputViews,
) -> dict[FixedHorizonLabelName, tuple[LabelValueRecord, ...]]:
    """Compute fixed-horizon labels for the supplied governed definitions."""

    return {
        definition.name: compute_fixed_horizon_label(definition, input_views)
        for definition in definitions
    }


def _compute_trade_price_forward_returns(
    definition: FixedHorizonLabelDefinition,
    input_view: OHLCVInputView,
) -> tuple[LabelValueRecord, ...]:
    rows = _validated_trade_rows(input_view.rows)
    terminal_by_key = _index_by_series_contract_event_ts(rows)
    roll_calendar_cache: dict[tuple[str, int, int], tuple[RollCalendarRecord, ...]] = {}
    if _is_close_out_label(definition.name):
        return _compute_trade_price_close_out_returns(
            definition,
            rows,
            terminal_by_key=terminal_by_key,
            roll_calendar_cache=roll_calendar_cache,
        )
    records: list[LabelValueRecord] = []
    for source in rows:
        terminal = terminal_by_key.get(_terminal_key(source, definition.horizon_minutes))
        if terminal is None:
            continue
        guarded = _guarded_forward_terminal(
            source,
            terminal,
            terminal_by_key=terminal_by_key,
            roll_calendar_cache=roll_calendar_cache,
        )
        if guarded is None:
            continue
        terminal, guard_flags = guarded
        value, flags = _trade_price_return(source, terminal)
        records.append(
            _label_value_record(
                definition,
                source,
                terminal,
                value,
                (*flags, *guard_flags),
            )
        )
    return tuple(records)


def _compute_trade_price_close_out_returns(
    definition: FixedHorizonLabelDefinition,
    rows: tuple[OHLCVInputRow, ...],
    *,
    terminal_by_key: Mapping[tuple[str, str, datetime], OHLCVInputRow],
    roll_calendar_cache: dict[tuple[str, int, int], tuple[RollCalendarRecord, ...]],
) -> tuple[LabelValueRecord, ...]:
    terminal_by_scope = _close_out_terminal_by_scope(rows, definition.name)
    records: list[LabelValueRecord] = []
    for source in rows:
        terminal = terminal_by_scope.get(_close_out_scope_key(source, definition.name))
        if terminal is None or terminal.event_ts <= source.event_ts:
            continue
        guarded = _guarded_forward_terminal(
            source,
            terminal,
            terminal_by_key=terminal_by_key,
            roll_calendar_cache=roll_calendar_cache,
        )
        if guarded is None:
            continue
        terminal, guard_flags = guarded
        value, flags = _trade_price_return(source, terminal)
        records.append(
            _label_value_record(
                definition,
                source,
                terminal,
                value,
                (*flags, *guard_flags),
            )
        )
    return tuple(records)


def _compute_midprice_forward_returns(
    definition: FixedHorizonLabelDefinition,
    input_view: BBOInputView,
) -> tuple[LabelValueRecord, ...]:
    rows = _validated_bbo_rows(input_view.rows)
    terminal_by_key = _index_by_series_contract_event_ts(rows)
    roll_calendar_cache: dict[tuple[str, int, int], tuple[RollCalendarRecord, ...]] = {}
    records: list[LabelValueRecord] = []
    for source in rows:
        terminal = terminal_by_key.get(_terminal_key(source, definition.horizon_minutes))
        if terminal is None:
            continue
        guarded = _guarded_forward_terminal(
            source,
            terminal,
            terminal_by_key=terminal_by_key,
            roll_calendar_cache=roll_calendar_cache,
        )
        if guarded is None:
            continue
        terminal, guard_flags = guarded
        value, flags = _midprice_return(source, terminal)
        records.append(
            _label_value_record(
                definition,
                source,
                terminal,
                value,
                (*flags, *guard_flags),
            )
        )
    return tuple(records)


def _trade_price_return(
    source: OHLCVInputRow,
    terminal: OHLCVInputRow,
) -> tuple[float | None, tuple[str, ...]]:
    flags: set[str] = set()
    if not _is_real_trade_bar(source):
        flags.update(_gap_flags(source, "source_not_trade"))
    if not _is_real_trade_bar(terminal):
        flags.update(_gap_flags(terminal, "horizon_not_trade"))
    if flags:
        return None, tuple(sorted(flags))

    source_close = _to_positive_float(source.close, "OHLCVInputRow.close")
    terminal_close = _to_positive_float(terminal.close, "OHLCVInputRow.close")
    value = terminal_close / source_close - 1.0
    if not math.isfinite(value):
        return None, ("non_finite_return",)
    return value, ()


def _midprice_return(
    source: BBOInputRow,
    terminal: BBOInputRow,
) -> tuple[float | None, tuple[str, ...]]:
    flags: set[str] = set()
    if not _is_valid_bbo_quote(source):
        flags.update(_bbo_gap_flags(source, "source_bbo_gap"))
    if not _is_valid_bbo_quote(terminal):
        flags.update(_bbo_gap_flags(terminal, "horizon_bbo_gap"))
    if flags:
        return None, tuple(sorted(flags))

    source_mid = _to_positive_float(source.mid, "BBOInputRow.mid")
    terminal_mid = _to_positive_float(terminal.mid, "BBOInputRow.mid")
    value = terminal_mid / source_mid - 1.0
    if not math.isfinite(value):
        return None, ("non_finite_return",)
    return value, ()


def _label_value_record(
    definition: FixedHorizonLabelDefinition,
    source: OHLCVInputRow | BBOInputRow,
    terminal: OHLCVInputRow | BBOInputRow,
    value: float | None,
    quality_flags: Sequence[str],
) -> LabelValueRecord:
    return LabelValueRecord(
        label_version_id=definition.label_version_id,
        entity_id=source.series_id,
        event_ts=source.event_ts,
        horizon_end_ts=terminal.event_ts,
        label_available_ts=_label_available_ts(definition, terminal),
        value=value,
        label_contract=definition.contract,
        quality_flags=_quality_flags(quality_flags),
    )


def _label_available_ts(
    definition: FixedHorizonLabelDefinition,
    terminal: OHLCVInputRow | BBOInputRow,
) -> datetime:
    terminal_available_ts = _require_aware_datetime(terminal.available_ts, "terminal.available_ts")
    return max(terminal_available_ts, definition.contract.availability_policy.availability_time)


def _label_inputs(
    name: FixedHorizonLabelName,
    dataset_version_ids: Sequence[str],
) -> LabelInputSpec:
    dataset_ids = _text_tuple(dataset_version_ids, "dataset_version_ids", allow_empty=True)
    if name in _MIDPRICE_LABELS:
        return LabelInputSpec(
            input_views=("canonical_bbo",),
            fields=(
                "series_id",
                "contract_id",
                "event_ts",
                "bar_end_ts",
                "available_ts",
                "bid",
                "ask",
                "mid",
                "quality_flags",
            ),
            dataset_version_ids=dataset_ids,
            input_metadata={
                "consumption_surface": "alpha_system.features.input_views.BBOInputView",
                "price_basis": "mid",
                "bbo_quality_tokens": [
                    MISSING_BBO_QUALITY_FLAG,
                    BBO_QUARANTINE_QUALITY_FLAG,
                ],
                "missingness": (
                    "missing_bbo and bbo_quarantined rows are gaps; no forward fill "
                    "or interpolation is performed"
                ),
            },
        )
    return LabelInputSpec(
        input_views=("canonical_ohlcv", "dense_grid_ohlcv"),
        fields=(
                "series_id",
                "contract_id",
                "event_ts",
                "bar_end_ts",
                "available_ts",
            "close",
            "volume",
            "quality_flags",
        ),
        dataset_version_ids=dataset_ids,
        input_metadata={
            "consumption_surface": "alpha_system.features.input_views.OHLCVInputView",
            "price_basis": "close",
            "trade_semantics": (
                "dense-grid no_trade rows are gaps and are never treated as trade bars"
            ),
        },
    )


def _future_window(name: FixedHorizonLabelName) -> WindowSpec:
    if _is_close_out_label(name):
        return WindowSpec(
            kind=WindowKind.FUTURE,
            length=_CLOSE_OUT_HORIZON_LENGTH,
            causality=WindowCausality.FUTURE,
            offline_only=True,
            anchor="event_ts",
            parameters=_close_out_window_parameters(name),
        )
    parameters: dict[str, Any] = {
        "horizon_minutes": _HORIZON_MINUTES[name],
        "price_basis": _price_basis(name),
        "legal_consumer": "labels_only",
        "terminal_key": "series_id+contract_id+event_ts",
        "roll_policy_id": ROLL_POLICY_ID,
        "roll_guard_version": ROLL_GUARD_VERSION,
        "roll_cross_policy": DEFAULT_CROSS_ROLL_POLICY.value,
        "maintenance_policy_id": MAINTENANCE_POLICY_ID,
        "maintenance_guard_version": MAINTENANCE_GUARD_VERSION,
    }
    if _is_extended_horizon(name):
        parameters["horizon_overlap_metadata"] = _horizon_overlap_contract_metadata(name)
    return WindowSpec(
        kind=WindowKind.FUTURE,
        length=_HORIZON_MINUTES[name],
        causality=WindowCausality.FUTURE,
        offline_only=True,
        anchor="event_ts",
        parameters=parameters,
    )


def _is_extended_horizon(name: FixedHorizonLabelName) -> bool:
    if _is_close_out_label(name):
        return False
    return _HORIZON_MINUTES[name] >= 60


def _is_close_out_label(name: FixedHorizonLabelName) -> bool:
    return name in _CLOSE_OUT_LABELS


def _close_out_contract_metadata(name: FixedHorizonLabelName) -> dict[str, Any]:
    return {
        "campaign": "ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1",
        "phase": "FUTSUB-P18",
        "materialization": "in_memory_records_only",
        "price_basis": "close",
        "close_out_horizon": name.value,
        "close_out_terminal": _close_out_terminal_description(name),
        "legal_consumer": "labels_only",
        "claims": "descriptive_label_substrate_only",
        "terminal_key": "series_id+contract_id+event_ts",
        "terminal_scope": "series_id+contract_id+close_out_boundary",
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
        "horizon_overlap_metadata": {
            "metadata_version": OVERLAP_METADATA_VERSION,
            "raw_row_count_field": "value_record_count",
            "effective_sample_count_rule": "count distinct close-out terminal events",
            "rows_are_independent": False,
            "n_eff_never_exceeds_raw_rows": True,
        },
    }


def _close_out_window_parameters(name: FixedHorizonLabelName) -> dict[str, Any]:
    return {
        "close_out_horizon": name.value,
        "price_basis": "close",
        "legal_consumer": "labels_only",
        "terminal_key": "series_id+contract_id+event_ts",
        "terminal_scope": "series_id+contract_id+close_out_boundary",
        "terminal_rule": _close_out_terminal_description(name),
        "roll_policy_id": ROLL_POLICY_ID,
        "roll_guard_version": ROLL_GUARD_VERSION,
        "roll_cross_policy": DEFAULT_CROSS_ROLL_POLICY.value,
        "maintenance_policy_id": MAINTENANCE_POLICY_ID,
        "maintenance_guard_version": MAINTENANCE_GUARD_VERSION,
        "maintenance_crossing_policy": "drop",
    }


def _close_out_terminal_description(name: FixedHorizonLabelName) -> str:
    if name is FixedHorizonLabelName.SESSION_CLOSE:
        return "last RTH trade bar at or before 15:00 America/Chicago for the CME trade date"
    if name is FixedHorizonLabelName.MAINTENANCE_FLAT:
        return "last trade bar at or before the 16:00 America/Chicago maintenance break for the CME trade date"
    raise FixedHorizonLabelError(f"unsupported close-out label: {name}")


def _horizon_overlap_contract_metadata(name: FixedHorizonLabelName) -> dict[str, object]:
    horizon_minutes = _HORIZON_MINUTES[name]
    return {
        "metadata_version": OVERLAP_METADATA_VERSION,
        "horizon_minutes": horizon_minutes,
        "sampling_interval_minutes": 1,
        "horizon_bars": horizon_minutes,
        "raw_row_count_field": "value_record_count",
        "effective_sample_count_rule": "floor(raw_row_count / horizon_bars)",
        "rows_are_independent": False,
        "n_eff_never_exceeds_raw_rows": True,
    }


def _validate_label_spec_matches_name(
    name: FixedHorizonLabelName,
    spec: LabelSpec,
) -> None:
    if _is_close_out_label(name):
        if spec.horizon != name.value:
            raise FixedHorizonLabelError(
                f"LabelSpec.horizon must be {name.value} for {name.value}"
            )
        actual_path = spec.path_rules.get("path")
        if actual_path != _CLOSE_OUT_PATH:
            raise FixedHorizonLabelError(
                f"LabelSpec.path_rules.path must be {_CLOSE_OUT_PATH} for {name.value}"
            )
        terminal = spec.path_rules.get("close_out_terminal")
        if terminal is not None and terminal != name.value:
            raise FixedHorizonLabelError(
                f"LabelSpec.path_rules.close_out_terminal must be {name.value}"
            )
        return

    expected_horizon = f"{_HORIZON_MINUTES[name]}m"
    if spec.horizon != expected_horizon:
        raise FixedHorizonLabelError(
            f"LabelSpec.horizon must be {expected_horizon} for {name.value}"
        )

    expected_path = _PATH_BY_PRICE_BASIS[_price_basis(name)]
    actual_path = spec.path_rules.get("path")
    if actual_path != expected_path:
        raise FixedHorizonLabelError(
            f"LabelSpec.path_rules.path must be {expected_path} for {name.value}"
        )

    path_horizon = spec.path_rules.get("horizon_minutes")
    if path_horizon is not None and path_horizon != _HORIZON_MINUTES[name]:
        raise FixedHorizonLabelError(
            f"LabelSpec.path_rules.horizon_minutes must match {name.value}"
        )


def _coerce_governance_label_spec(
    value: LabelSpec | Mapping[str, Any] | None,
) -> LabelSpec:
    if value is None:
        raise FixedHorizonLabelError("governance LabelSpec lspec_ binding is required")
    try:
        if isinstance(value, LabelSpec):
            return LabelSpec.from_mapping(value.to_dict())
        return LabelSpec.from_mapping(value)
    except ValueError as exc:
        raise FixedHorizonLabelError("governance LabelSpec lspec_ binding is invalid") from exc


def _require_definition(
    definition: FixedHorizonLabelDefinition,
) -> FixedHorizonLabelDefinition:
    if not isinstance(definition, FixedHorizonLabelDefinition):
        raise FixedHorizonLabelError("compute requires a FixedHorizonLabelDefinition")
    if definition.contract.family is not LabelFamily.FIXED_HORIZON:
        raise FixedHorizonLabelError("definition must belong to LabelFamily.FIXED_HORIZON")
    if definition.version != definition.contract.derive_label_version():
        raise FixedHorizonLabelError("definition LabelVersion does not match LabelContractSpec")
    if not definition.contract.availability_policy.future_data_legal_only_for_labels:
        raise FixedHorizonLabelError("fixed-horizon future data must be labels-only")
    return definition


def _coerce_ohlcv_view(
    input_view: OHLCVInputView | BBOInputView | CanonicalInputViews,
) -> OHLCVInputView:
    if isinstance(input_view, CanonicalInputViews):
        return input_view.ohlcv
    if isinstance(input_view, OHLCVInputView):
        return input_view
    raise FixedHorizonLabelError("trade-price labels require an OHLCVInputView")


def _coerce_bbo_view(
    input_view: OHLCVInputView | BBOInputView | CanonicalInputViews,
) -> BBOInputView:
    if isinstance(input_view, CanonicalInputViews):
        return input_view.bbo
    if isinstance(input_view, BBOInputView):
        return input_view
    raise FixedHorizonLabelError("midprice labels require a BBOInputView")


def _validated_trade_rows(rows: Sequence[OHLCVInputRow]) -> tuple[OHLCVInputRow, ...]:
    ordered = tuple(rows)
    for row in ordered:
        if not isinstance(row, OHLCVInputRow):
            raise FixedHorizonLabelError("trade-price labels require OHLCVInputRow inputs")
        _require_aware_datetime(row.event_ts, "OHLCVInputRow.event_ts")
        _require_aware_datetime(row.available_ts, "OHLCVInputRow.available_ts")
        _require_aware_datetime(row.bar_end_ts, "OHLCVInputRow.bar_end_ts")
        _to_positive_float(row.close, "OHLCVInputRow.close")
        _quality_flags(row.quality_flags)
    return _sorted_rows(ordered)


def _validated_bbo_rows(rows: Sequence[BBOInputRow]) -> tuple[BBOInputRow, ...]:
    ordered = tuple(rows)
    for row in ordered:
        if not isinstance(row, BBOInputRow):
            raise FixedHorizonLabelError("midprice labels require BBOInputRow inputs")
        _require_aware_datetime(row.event_ts, "BBOInputRow.event_ts")
        _require_aware_datetime(row.available_ts, "BBOInputRow.available_ts")
        _require_aware_datetime(row.bar_end_ts, "BBOInputRow.bar_end_ts")
        for field in ("bid", "ask", "mid", "spread"):
            _to_float(getattr(row, field), f"BBOInputRow.{field}")
        _quality_flags(row.quality_flags)
    return _sorted_rows(ordered)


def _sorted_rows[
    RowT: (OHLCVInputRow, BBOInputRow),
](rows: Sequence[RowT]) -> tuple[RowT, ...]:
    return tuple(sorted(rows, key=lambda row: (row.series_id, row.event_ts, row.available_ts)))


def _index_by_series_contract_event_ts[
    RowT: (OHLCVInputRow, BBOInputRow),
](rows: Sequence[RowT]) -> dict[tuple[str, str, datetime], RowT]:
    index: dict[tuple[str, str, datetime], RowT] = {}
    for row in rows:
        key = (row.series_id, row.contract_id, row.event_ts)
        if key in index:
            raise FixedHorizonLabelError(
                "fixed-horizon labels require unique rows per series_id, contract_id, and event_ts"
            )
        index[key] = row
    return index


def _terminal_key(
    row: OHLCVInputRow | BBOInputRow,
    horizon_minutes: int,
) -> tuple[str, str, datetime]:
    return (
        row.series_id,
        row.contract_id,
        row.event_ts + timedelta(minutes=horizon_minutes),
    )


def _guarded_forward_terminal[
    RowT: (OHLCVInputRow, BBOInputRow),
](
    source: RowT,
    terminal: RowT,
    *,
    terminal_by_key: Mapping[tuple[str, str, datetime], RowT],
    roll_calendar_cache: dict[tuple[str, int, int], tuple[RollCalendarRecord, ...]],
) -> tuple[RowT, tuple[str, ...]] | None:
    if source.contract_id != terminal.contract_id:
        return None
    if _crosses_maintenance_break(source.event_ts, terminal.event_ts):
        return None

    root_symbol = _root_symbol(source)
    if root_symbol is None:
        return terminal, ()

    calendar = _roll_calendar_for_window(
        root_symbol,
        source.event_ts,
        terminal.event_ts,
        cache=roll_calendar_cache,
    )
    verdict = evaluate_roll_guard(
        entry_ts=source.event_ts,
        label_horizon_ts=terminal.event_ts,
        calendar=calendar,
        policy=DEFAULT_CROSS_ROLL_POLICY,
        root_symbol=root_symbol,
        roll_window_days_before=DEFAULT_ROLL_WINDOW_DAYS_BEFORE,
        roll_window_days_after=DEFAULT_ROLL_WINDOW_DAYS_AFTER,
    )
    if verdict.action in {RollGuardAction.DROP, RollGuardAction.INVALID} or not verdict.valid:
        return None
    if verdict.action is RollGuardAction.TRUNCATE:
        if verdict.effective_label_horizon_ts is None:
            return None
        truncated = terminal_by_key.get(
            (source.series_id, source.contract_id, verdict.effective_label_horizon_ts)
        )
        if truncated is None:
            return None
        return truncated, _roll_guard_flags(verdict.action.value)
    if verdict.action is RollGuardAction.FLAG:
        return terminal, _roll_guard_flags(verdict.action.value)
    return terminal, ()


def _close_out_terminal_by_scope(
    rows: tuple[OHLCVInputRow, ...],
    name: FixedHorizonLabelName,
) -> dict[tuple[str, str, str], OHLCVInputRow]:
    terminals: dict[tuple[str, str, str], OHLCVInputRow] = {}
    for row in rows:
        if not _is_close_out_terminal_candidate(row, name):
            continue
        key = _close_out_scope_key(row, name)
        previous = terminals.get(key)
        if previous is None or row.event_ts > previous.event_ts:
            terminals[key] = row
    return terminals


def _is_close_out_terminal_candidate(
    row: OHLCVInputRow,
    name: FixedHorizonLabelName,
) -> bool:
    local = _maintenance_local(row.event_ts)
    if name is FixedHorizonLabelName.SESSION_CLOSE:
        return _RTH_SESSION_OPEN <= local.time() <= _RTH_SESSION_CLOSE
    if name is FixedHorizonLabelName.MAINTENANCE_FLAT:
        return local.time() <= _MAINTENANCE_BREAK_START
    raise FixedHorizonLabelError(f"unsupported close-out label: {name}")


def _close_out_scope_key(
    row: OHLCVInputRow | BBOInputRow,
    name: FixedHorizonLabelName,
) -> tuple[str, str, str]:
    trade_date = _cme_trade_date(row.event_ts).isoformat()
    if name is FixedHorizonLabelName.SESSION_CLOSE:
        boundary = f"rth_close:{trade_date}"
    elif name is FixedHorizonLabelName.MAINTENANCE_FLAT:
        boundary = f"maintenance_break:{trade_date}"
    else:
        raise FixedHorizonLabelError(f"unsupported close-out label: {name}")
    return (row.series_id, row.contract_id, boundary)


def _cme_trade_date(value: datetime) -> Any:
    local = _maintenance_local(value)
    if local.time() >= _MAINTENANCE_BREAK_END:
        return local.date() + timedelta(days=1)
    return local.date()


def _maintenance_local(value: datetime) -> datetime:
    return _require_aware_datetime(value, "event_ts").astimezone(_MAINTENANCE_TIMEZONE)


def _roll_calendar_for_window(
    root_symbol: str,
    entry_ts: datetime,
    terminal_ts: datetime,
    *,
    cache: dict[tuple[str, int, int], tuple[RollCalendarRecord, ...]],
) -> tuple[RollCalendarRecord, ...]:
    start_year = min(entry_ts.year, terminal_ts.year)
    end_year = max(entry_ts.year, terminal_ts.year)
    key = (root_symbol, start_year, end_year)
    if key not in cache:
        cache[key] = build_analytic_cme_equity_index_quarterly_roll_calendar(
            root_symbols=(root_symbol,),
            start_year=start_year,
            end_year=end_year,
        )
    return cache[key]


def _roll_guard_flags(action: str) -> tuple[str, ...]:
    return _quality_flags(
        (
            "roll_splice_guard",
            f"roll_splice_{action}",
            ROLL_POLICY_ID,
            ROLL_GUARD_VERSION,
        )
    )


def _crosses_maintenance_break(entry_ts: datetime, terminal_ts: datetime) -> bool:
    entry_local = _require_aware_datetime(entry_ts, "entry_ts").astimezone(
        _MAINTENANCE_TIMEZONE
    )
    terminal_local = _require_aware_datetime(terminal_ts, "terminal_ts").astimezone(
        _MAINTENANCE_TIMEZONE
    )
    if terminal_local < entry_local:
        return False

    day = entry_local.date()
    end_day = terminal_local.date()
    while day <= end_day:
        break_start = datetime.combine(day, _MAINTENANCE_BREAK_START, _MAINTENANCE_TIMEZONE)
        break_end = datetime.combine(day, _MAINTENANCE_BREAK_END, _MAINTENANCE_TIMEZONE)
        if entry_local < break_end and terminal_local > break_start:
            return True
        day += timedelta(days=1)
    return False


def _root_symbol(row: OHLCVInputRow | BBOInputRow) -> str | None:
    candidates = (row.instrument_id, row.contract_id, row.series_id)
    for value in candidates:
        text = value.upper()
        tokens = tuple(token for token in re.split(r"[^A-Z0-9]+|_", text) if token)
        for root in sorted(_KNOWN_ROLL_ROOTS, key=len, reverse=True):
            if root in tokens or text.startswith(root):
                return root
            if any(token.startswith(root) and token[len(root) :].isdigit() for token in tokens):
                return root
    return None


def _is_real_trade_bar(row: OHLCVInputRow) -> bool:
    try:
        return is_real_trade_bar(row)
    except DataFoundationValidationError as exc:
        raise FixedHorizonLabelError(str(exc)) from exc


def _is_valid_bbo_quote(row: BBOInputRow) -> bool:
    semantics = _quote_semantics(row)
    return not semantics.missing_or_abnormal and semantics.invariants_hold


def _quote_semantics(row: BBOInputRow) -> Any:
    try:
        return bbo_quote_semantics(row)
    except DataFoundationValidationError as exc:
        raise FixedHorizonLabelError(str(exc)) from exc


def _gap_flags(row: OHLCVInputRow, reason: str) -> tuple[str, ...]:
    return _quality_flags((reason, *row.quality_flags))


def _bbo_gap_flags(row: BBOInputRow, reason: str) -> tuple[str, ...]:
    semantics = _quote_semantics(row)
    flags = {"bbo_gap", reason, *_quality_flags(row.quality_flags)}
    if semantics.missing_bbo:
        flags.add(MISSING_BBO_QUALITY_FLAG)
    if semantics.bbo_quarantined:
        flags.add(BBO_QUARANTINE_QUALITY_FLAG)
    if not semantics.invariants_hold:
        flags.add("bbo_invariant_violation")
    return tuple(sorted(flags))


def _price_basis(name: FixedHorizonLabelName) -> str:
    return "mid" if name in _MIDPRICE_LABELS else "close"


def _coerce_label_name(name: FixedHorizonLabelName | str) -> FixedHorizonLabelName:
    try:
        return FixedHorizonLabelName(name)
    except ValueError as exc:
        raise FixedHorizonLabelError(f"unsupported fixed-horizon label: {name}") from exc


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise FixedHorizonLabelError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise FixedHorizonLabelError(f"{field_name} must be timezone-aware")
    return value


def _to_positive_float(value: object, field_name: str) -> float:
    parsed = _to_float(value, field_name)
    if parsed <= 0:
        raise FixedHorizonLabelError(f"{field_name} must be positive")
    return parsed


def _to_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, _NUMERIC_TYPES):
        raise FixedHorizonLabelError(f"{field_name} must be numeric")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise FixedHorizonLabelError(f"{field_name} must be finite")
    return parsed


def _text_tuple(
    values: Sequence[str],
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise FixedHorizonLabelError(f"{field_name} must be a sequence of strings")
    parsed: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise FixedHorizonLabelError(f"{field_name} entries must be non-empty strings")
        parsed.append(value.strip())
    if not parsed and not allow_empty:
        raise FixedHorizonLabelError(f"{field_name} must not be empty")
    return tuple(parsed)


def _quality_flags(flags: Sequence[str]) -> tuple[str, ...]:
    if isinstance(flags, str) or not isinstance(flags, Sequence):
        raise FixedHorizonLabelError("quality_flags must be a sequence of strings")
    normalized: set[str] = set()
    for flag in flags:
        if not isinstance(flag, str) or not flag.strip():
            raise FixedHorizonLabelError("quality_flags entries must be non-empty strings")
        normalized.add(flag.strip().lower())
    return tuple(sorted(normalized))


def _materialization_scope_metadata(
    value: Mapping[str, Any] | None,
) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise FixedHorizonLabelError("materialization_scope must be a mapping")
    scope: dict[str, str] = {}
    for key, item in value.items():
        key_text = _metadata_text(key, "materialization_scope key")
        item_text = _metadata_text(item, f"materialization_scope.{key_text}")
        scope[key_text] = item_text
    return dict(sorted(scope.items()))


def _metadata_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise FixedHorizonLabelError(f"{field_name} must be a string")
    text = value.strip()
    if not text:
        raise FixedHorizonLabelError(f"{field_name} must be a non-empty string")
    return text


__all__ = [
    "FixedHorizonLabelDefinition",
    "FixedHorizonLabelError",
    "FixedHorizonLabelName",
    "HorizonOverlapMetadata",
    "MAINTENANCE_GUARD_VERSION",
    "MAINTENANCE_POLICY_ID",
    "OVERLAP_METADATA_VERSION",
    "build_fixed_horizon_label_definition",
    "build_fixed_horizon_label_definitions",
    "compute_horizon_overlap_metadata",
    "compute_fixed_horizon_label",
    "compute_fixed_horizon_labels",
    "supported_fixed_horizon_labels",
]
