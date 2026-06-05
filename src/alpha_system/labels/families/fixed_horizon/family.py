"""Fixed-horizon trade-close and midprice forward-return labels."""

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


class FixedHorizonLabelError(ValueError):
    """Raised when fixed-horizon label construction or calculation fails closed."""


class FixedHorizonLabelName(StrEnum):
    """Supported FLF-P17 fixed-horizon label names."""

    FWD_RET_1M = "fwd_ret_1m"
    FWD_RET_3M = "fwd_ret_3m"
    FWD_RET_5M = "fwd_ret_5m"
    FWD_RET_10M = "fwd_ret_10m"
    FWD_RET_30M = "fwd_ret_30m"
    MID_FWD_RET_1M = "mid_fwd_ret_1m"
    MID_FWD_RET_3M = "mid_fwd_ret_3m"
    MID_FWD_RET_5M = "mid_fwd_ret_5m"
    MID_FWD_RET_10M = "mid_fwd_ret_10m"
    MID_FWD_RET_30M = "mid_fwd_ret_30m"


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
        FixedHorizonLabelName.FWD_RET_30M,
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
    FixedHorizonLabelName.FWD_RET_30M: 30,
    FixedHorizonLabelName.MID_FWD_RET_1M: 1,
    FixedHorizonLabelName.MID_FWD_RET_3M: 3,
    FixedHorizonLabelName.MID_FWD_RET_5M: 5,
    FixedHorizonLabelName.MID_FWD_RET_10M: 10,
    FixedHorizonLabelName.MID_FWD_RET_30M: 30,
}
_PATH_BY_PRICE_BASIS: dict[str, str] = {
    "close": "trade_price_forward_return",
    "mid": "midprice_forward_return",
}
_NUMERIC_TYPES = (int, float, Decimal)


def supported_fixed_horizon_labels() -> tuple[FixedHorizonLabelName, ...]:
    """Return the complete FLF-P17 fixed-horizon label list."""

    return tuple(FixedHorizonLabelName)


def build_fixed_horizon_label_definition(
    name: FixedHorizonLabelName | str,
    governance_label_spec: LabelSpec | Mapping[str, Any] | None,
    *,
    dataset_version_ids: Sequence[str] = (),
) -> FixedHorizonLabelDefinition:
    """Build one governed fixed-horizon label definition.

    A valid governance `LabelSpec` is the only admission path. Missing,
    malformed, horizon-mismatched, or family-mismatched `lspec_` bindings fail
    before a label version can be derived.
    """

    label_name = _coerce_label_name(name)
    spec = _coerce_governance_label_spec(governance_label_spec)
    _validate_label_spec_matches_name(label_name, spec)
    contract = LabelContractSpec.from_label_spec(
        label_id=label_name.value,
        family=LabelFamily.FIXED_HORIZON,
        governance_label_spec=spec,
        inputs=_label_inputs(label_name, dataset_version_ids),
        window=_future_window(label_name),
        contract_metadata={
            "campaign": "ALPHA_FEATURE_LABEL_FOUNDATION_V1",
            "phase": "FLF-P17",
            "materialization": "in_memory_records_only",
            "price_basis": _price_basis(label_name),
            "horizon_minutes": _HORIZON_MINUTES[label_name],
            "legal_consumer": "labels_only",
            "claims": "descriptive_label_substrate_only",
        },
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
    terminal_by_key = _index_by_series_event_ts(rows)
    records: list[LabelValueRecord] = []
    for source in rows:
        terminal = terminal_by_key.get(_terminal_key(source, definition.horizon_minutes))
        if terminal is None:
            continue
        value, flags = _trade_price_return(source, terminal)
        records.append(_label_value_record(definition, source, terminal, value, flags))
    return tuple(records)


def _compute_midprice_forward_returns(
    definition: FixedHorizonLabelDefinition,
    input_view: BBOInputView,
) -> tuple[LabelValueRecord, ...]:
    rows = _validated_bbo_rows(input_view.rows)
    terminal_by_key = _index_by_series_event_ts(rows)
    records: list[LabelValueRecord] = []
    for source in rows:
        terminal = terminal_by_key.get(_terminal_key(source, definition.horizon_minutes))
        if terminal is None:
            continue
        value, flags = _midprice_return(source, terminal)
        records.append(_label_value_record(definition, source, terminal, value, flags))
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
    return WindowSpec(
        kind=WindowKind.FUTURE,
        length=_HORIZON_MINUTES[name],
        causality=WindowCausality.FUTURE,
        offline_only=True,
        anchor="event_ts",
        parameters={
            "horizon_minutes": _HORIZON_MINUTES[name],
            "price_basis": _price_basis(name),
            "legal_consumer": "labels_only",
        },
    )


def _validate_label_spec_matches_name(
    name: FixedHorizonLabelName,
    spec: LabelSpec,
) -> None:
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


def _index_by_series_event_ts[
    RowT: (OHLCVInputRow, BBOInputRow),
](rows: Sequence[RowT]) -> dict[tuple[str, datetime], RowT]:
    index: dict[tuple[str, datetime], RowT] = {}
    for row in rows:
        key = (row.series_id, row.event_ts)
        if key in index:
            raise FixedHorizonLabelError(
                "fixed-horizon labels require unique rows per series_id and event_ts"
            )
        index[key] = row
    return index


def _terminal_key(
    row: OHLCVInputRow | BBOInputRow,
    horizon_minutes: int,
) -> tuple[str, datetime]:
    return (row.series_id, row.event_ts + timedelta(minutes=horizon_minutes))


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


__all__ = [
    "FixedHorizonLabelDefinition",
    "FixedHorizonLabelError",
    "FixedHorizonLabelName",
    "build_fixed_horizon_label_definition",
    "build_fixed_horizon_label_definitions",
    "compute_fixed_horizon_label",
    "compute_fixed_horizon_labels",
    "supported_fixed_horizon_labels",
]
