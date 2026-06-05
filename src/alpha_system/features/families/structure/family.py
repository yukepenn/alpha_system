"""Causal liquidity-sweep and market-structure feature definitions."""

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
from alpha_system.features.contracts import (
    FeatureFamily,
    FeatureInputSpec,
    FeatureSpec,
    FeatureValueRecord,
    FeatureVersion,
    NormalizationSpec,
    TransformSpec,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.input_views import (
    BBOInputRow,
    BBOInputView,
    CanonicalInputViews,
    OHLCVInputRow,
    OHLCVInputView,
)
from alpha_system.features.primitives import PrimitivePoint, rolling_mean
from alpha_system.features.request_gate import (
    FeatureRequestGateDecision,
    require_feature_request_implementation_allowed,
)
from alpha_system.features.semantics import (
    BBOQuoteSemantics,
    bbo_quote_semantics,
    is_real_trade_bar,
    is_valid_bbo_quote,
)
from alpha_system.governance.duplicate_exposure import RegistryReader
from alpha_system.governance.feature_request import FeatureRequest


class StructureFeatureError(ValueError):
    """Raised when Liquidity/Structure family computation fails closed."""


class StructureFeatureName(StrEnum):
    """Supported Liquidity/Structure feature names for FLF-P12."""

    PRIOR_HIGH_DISTANCE = "prior_high_distance"
    PRIOR_LOW_DISTANCE = "prior_low_distance"
    OPENING_RANGE_HIGH_DISTANCE = "opening_range_high_distance"
    OPENING_RANGE_LOW_DISTANCE = "opening_range_low_distance"
    SWEEP_HIGH_FLAG = "sweep_high_flag"
    SWEEP_LOW_FLAG = "sweep_low_flag"
    FAILED_BREAKOUT_HIGH_FLAG = "failed_breakout_high_flag"
    FAILED_BREAKOUT_LOW_FLAG = "failed_breakout_low_flag"
    CLOSE_LOCATION_VALUE = "close_location_value"
    WICK_REJECTION_SCORE = "wick_rejection_score"
    RANGE_CONTRACTION = "range_contraction"
    BBO_MID_DISTANCE = "bbo_mid_distance"


@dataclass(frozen=True, slots=True)
class StructureFeatureDefinition:
    """Approved, versioned Liquidity/Structure feature definition."""

    name: StructureFeatureName
    spec: FeatureSpec
    version: FeatureVersion
    request_gate_decision: FeatureRequestGateDecision

    @property
    def feature_id(self) -> str:
        """Return the stable feature id from the bound contract."""

        return self.spec.feature_id

    @property
    def feature_version_id(self) -> str:
        """Return the deterministic feature-version id."""

        return self.version.feature_version_id


@dataclass(frozen=True, slots=True)
class _FeaturePoint:
    row: OHLCVInputRow
    value: float | int | None
    quality_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _BreakoutState:
    level: float
    remaining_bars: int


type _Numeric = int | float | Decimal

_NUMERIC_TYPES = (int, float, Decimal)
_PRIOR_LEVEL_FEATURES = frozenset(
    {
        StructureFeatureName.PRIOR_HIGH_DISTANCE,
        StructureFeatureName.PRIOR_LOW_DISTANCE,
        StructureFeatureName.SWEEP_HIGH_FLAG,
        StructureFeatureName.SWEEP_LOW_FLAG,
        StructureFeatureName.FAILED_BREAKOUT_HIGH_FLAG,
        StructureFeatureName.FAILED_BREAKOUT_LOW_FLAG,
    }
)
_OPENING_RANGE_FEATURES = frozenset(
    {
        StructureFeatureName.OPENING_RANGE_HIGH_DISTANCE,
        StructureFeatureName.OPENING_RANGE_LOW_DISTANCE,
    }
)
_BBO_FEATURES = frozenset({StructureFeatureName.BBO_MID_DISTANCE})
_OHLCV_FIELDS_BY_FEATURE: dict[StructureFeatureName, tuple[str, ...]] = {
    StructureFeatureName.PRIOR_HIGH_DISTANCE: ("high", "low", "close", "session_label"),
    StructureFeatureName.PRIOR_LOW_DISTANCE: ("high", "low", "close", "session_label"),
    StructureFeatureName.OPENING_RANGE_HIGH_DISTANCE: (
        "bar_start_ts",
        "high",
        "low",
        "close",
        "session_label",
    ),
    StructureFeatureName.OPENING_RANGE_LOW_DISTANCE: (
        "bar_start_ts",
        "high",
        "low",
        "close",
        "session_label",
    ),
    StructureFeatureName.SWEEP_HIGH_FLAG: ("high", "low", "close", "session_label"),
    StructureFeatureName.SWEEP_LOW_FLAG: ("high", "low", "close", "session_label"),
    StructureFeatureName.FAILED_BREAKOUT_HIGH_FLAG: (
        "high",
        "low",
        "close",
        "session_label",
    ),
    StructureFeatureName.FAILED_BREAKOUT_LOW_FLAG: (
        "high",
        "low",
        "close",
        "session_label",
    ),
    StructureFeatureName.CLOSE_LOCATION_VALUE: ("high", "low", "close"),
    StructureFeatureName.WICK_REJECTION_SCORE: ("open", "high", "low", "close"),
    StructureFeatureName.RANGE_CONTRACTION: ("high", "low", "session_label"),
    StructureFeatureName.BBO_MID_DISTANCE: ("bar_start_ts", "close", "session_label"),
}
_BBO_FIELDS_BY_FEATURE: dict[StructureFeatureName, tuple[str, ...]] = {
    StructureFeatureName.BBO_MID_DISTANCE: ("bid", "ask", "mid", "spread", "quality_flags"),
}


def supported_structure_features() -> tuple[StructureFeatureName, ...]:
    """Return the complete FLF-P12 Liquidity/Structure feature list."""

    return tuple(StructureFeatureName)


def build_structure_feature_definition(
    name: StructureFeatureName | str,
    feature_request: FeatureRequest | Mapping[str, Any] | None,
    registry_reader: RegistryReader | object | None,
    *,
    dataset_version_ids: Sequence[str] = (),
    window_length: int = 3,
    opening_range_minutes: int = 30,
    failure_window: int = 2,
    reset_on_session: bool = True,
    window: WindowSpec | None = None,
) -> StructureFeatureDefinition:
    """Build one approved Liquidity/Structure feature definition.

    The FLF-P05 request gate is the only admission path. Missing, invalid,
    unapproved, duplicate-blocked, or registry-unchecked requests fail closed.
    """

    feature_name = _coerce_feature_name(name)
    window_length = _positive_int(window_length, "window_length")
    opening_range_minutes = _positive_int(opening_range_minutes, "opening_range_minutes")
    failure_window = _positive_int(failure_window, "failure_window")
    if type(reset_on_session) is not bool:
        raise StructureFeatureError("reset_on_session must be a bool")

    gate_decision = require_feature_request_implementation_allowed(
        feature_request,
        registry_reader,
    )
    spec = _feature_spec(
        feature_name,
        gate_decision,
        dataset_version_ids=dataset_version_ids,
        window_length=window_length,
        opening_range_minutes=opening_range_minutes,
        failure_window=failure_window,
        reset_on_session=reset_on_session,
        window=window,
    )
    return StructureFeatureDefinition(
        name=feature_name,
        spec=spec,
        version=spec.derive_feature_version(),
        request_gate_decision=gate_decision,
    )


def build_structure_feature_definitions(
    feature_requests: Mapping[StructureFeatureName | str, FeatureRequest | Mapping[str, Any]],
    registry_reader: RegistryReader | object | None,
    **parameters: Any,
) -> tuple[StructureFeatureDefinition, ...]:
    """Build multiple approved Liquidity/Structure feature definitions."""

    return tuple(
        build_structure_feature_definition(name, request, registry_reader, **parameters)
        for name, request in feature_requests.items()
    )


def compute_structure_feature(
    definition: StructureFeatureDefinition,
    input_view: OHLCVInputView | CanonicalInputViews,
) -> tuple[FeatureValueRecord, ...]:
    """Compute one Liquidity/Structure feature as in-memory value records.

    Values are returned only to the caller. This function does not materialize,
    persist, register, or write feature values.
    """

    definition = _require_definition(definition)
    rows = _validated_ohlcv_rows(_coerce_ohlcv_view(input_view).rows)
    if definition.name is StructureFeatureName.PRIOR_HIGH_DISTANCE:
        return _records_from_points(definition, _prior_distance_points(rows, definition, high=True))
    if definition.name is StructureFeatureName.PRIOR_LOW_DISTANCE:
        return _records_from_points(definition, _prior_distance_points(rows, definition, high=False))
    if definition.name is StructureFeatureName.OPENING_RANGE_HIGH_DISTANCE:
        return _records_from_points(
            definition,
            _opening_range_distance_points(rows, definition, high=True),
        )
    if definition.name is StructureFeatureName.OPENING_RANGE_LOW_DISTANCE:
        return _records_from_points(
            definition,
            _opening_range_distance_points(rows, definition, high=False),
        )
    if definition.name is StructureFeatureName.SWEEP_HIGH_FLAG:
        return _records_from_points(definition, _sweep_points(rows, definition, high=True))
    if definition.name is StructureFeatureName.SWEEP_LOW_FLAG:
        return _records_from_points(definition, _sweep_points(rows, definition, high=False))
    if definition.name is StructureFeatureName.FAILED_BREAKOUT_HIGH_FLAG:
        return _records_from_points(
            definition,
            _failed_breakout_points(rows, definition, high=True),
        )
    if definition.name is StructureFeatureName.FAILED_BREAKOUT_LOW_FLAG:
        return _records_from_points(
            definition,
            _failed_breakout_points(rows, definition, high=False),
        )
    if definition.name is StructureFeatureName.CLOSE_LOCATION_VALUE:
        return _records_from_points(definition, _close_location_points(rows))
    if definition.name is StructureFeatureName.WICK_REJECTION_SCORE:
        return _records_from_points(definition, _wick_rejection_points(rows))
    if definition.name is StructureFeatureName.RANGE_CONTRACTION:
        return _records_from_points(definition, _range_contraction_points(rows, definition))
    if definition.name is StructureFeatureName.BBO_MID_DISTANCE:
        bbo_rows = _validated_bbo_rows(_coerce_bbo_view(input_view).rows)
        return _records_from_points(definition, _bbo_mid_distance_points(rows, bbo_rows))
    raise StructureFeatureError(f"unsupported Liquidity/Structure feature: {definition.name}")


def compute_structure_features(
    definitions: Iterable[StructureFeatureDefinition],
    input_view: OHLCVInputView | CanonicalInputViews,
) -> dict[StructureFeatureName, tuple[FeatureValueRecord, ...]]:
    """Compute approved Liquidity/Structure definitions against canonical views."""

    return {
        definition.name: compute_structure_feature(definition, input_view)
        for definition in definitions
    }


def _feature_spec(
    name: StructureFeatureName,
    gate_decision: FeatureRequestGateDecision,
    *,
    dataset_version_ids: Sequence[str],
    window_length: int,
    opening_range_minutes: int,
    failure_window: int,
    reset_on_session: bool,
    window: WindowSpec | None,
) -> FeatureSpec:
    if gate_decision.feature_request_id is None:
        raise StructureFeatureError("approved FeatureRequestGateDecision must expose freq_ id")
    feature_window = window or _default_window(name, window_length=window_length)
    parameters = _transform_parameters(
        name,
        window_length=window_length,
        opening_range_minutes=opening_range_minutes,
        failure_window=failure_window,
        reset_on_session=reset_on_session,
    )
    return FeatureSpec(
        feature_id=f"liquidity_structure_{name.value}",
        family=FeatureFamily.LIQUIDITY_STRUCTURE,
        feature_request_id=gate_decision.feature_request_id,
        inputs=FeatureInputSpec(
            input_views=_input_views(name),
            fields=_input_fields(name),
            dataset_version_ids=tuple(dataset_version_ids),
            input_metadata={
                "consumption_surface": "alpha_system.features.input_views.CanonicalInputViews",
                "trade_semantics": "FLF-P04 no_trade rows are gaps for trade logic",
                "bbo_semantics": (
                    "missing_bbo and bbo_quarantined rows are gaps for BBO-derived "
                    "structure values; no quote forward-fill is used"
                ),
            },
        ),
        transform=TransformSpec(
            transform_id=_transform_id(name),
            parameters=parameters,
        ),
        window=feature_window,
        normalization=NormalizationSpec(normalization_id="identity"),
        availability_assumptions={
            "input": "canonical OHLCV/BBO rows are accepted-DatasetVersion input-view rows",
            "causality": "outputs use only source rows with available_ts <= output available_ts",
            "no_trade": "synthetic no-trade rows are not trade bars",
            "bbo_missingness": "missing or quarantined BBO rows are not filled",
        },
        available_ts_derivation_rule=(
            "feature.available_ts = current OHLCV input row available_ts; trailing and "
            "cumulative state may use only rows whose available_ts is <= current row "
            "available_ts; BBO-derived values require same-bar BBO available_ts <= "
            "current OHLCV available_ts"
        ),
        live=True,
        implementation_eligible=True,
        contract_metadata={
            "campaign": "ALPHA_FEATURE_LABEL_FOUNDATION_V1",
            "phase": "FLF-P12",
            "materialization": "in_memory_records_only",
            "claims": "structure_substrate_only_no_alpha_or_tradability_claim",
        },
        request_gate_decision=gate_decision,
    )


def _default_window(name: StructureFeatureName, *, window_length: int) -> WindowSpec:
    if name in _PRIOR_LEVEL_FEATURES or name is StructureFeatureName.RANGE_CONTRACTION:
        return WindowSpec(
            kind=WindowKind.ROLLING,
            length=window_length,
            causality=WindowCausality.CAUSAL,
            offline_only=False,
        )
    if name in _OPENING_RANGE_FEATURES:
        return WindowSpec(
            kind=WindowKind.EXPANDING,
            length=1,
            causality=WindowCausality.CAUSAL,
            offline_only=False,
        )
    return WindowSpec(
        kind=WindowKind.POINT_IN_TIME,
        length=1,
        causality=WindowCausality.CAUSAL,
        offline_only=False,
    )


def _transform_id(name: StructureFeatureName) -> str:
    return {
        StructureFeatureName.PRIOR_HIGH_DISTANCE: "prior_high_distance",
        StructureFeatureName.PRIOR_LOW_DISTANCE: "prior_low_distance",
        StructureFeatureName.OPENING_RANGE_HIGH_DISTANCE: "opening_range_high_distance",
        StructureFeatureName.OPENING_RANGE_LOW_DISTANCE: "opening_range_low_distance",
        StructureFeatureName.SWEEP_HIGH_FLAG: "sweep_high_flag",
        StructureFeatureName.SWEEP_LOW_FLAG: "sweep_low_flag",
        StructureFeatureName.FAILED_BREAKOUT_HIGH_FLAG: "failed_breakout_high_flag",
        StructureFeatureName.FAILED_BREAKOUT_LOW_FLAG: "failed_breakout_low_flag",
        StructureFeatureName.CLOSE_LOCATION_VALUE: "close_location_value",
        StructureFeatureName.WICK_REJECTION_SCORE: "wick_rejection_score",
        StructureFeatureName.RANGE_CONTRACTION: "rolling_mean_range_ratio",
        StructureFeatureName.BBO_MID_DISTANCE: "bbo_mid_distance",
    }[name]


def _transform_parameters(
    name: StructureFeatureName,
    *,
    window_length: int,
    opening_range_minutes: int,
    failure_window: int,
    reset_on_session: bool,
) -> dict[str, object]:
    parameters: dict[str, object] = {
        "feature_name": name.value,
        "reset_on_session": reset_on_session,
    }
    if name in _PRIOR_LEVEL_FEATURES or name is StructureFeatureName.RANGE_CONTRACTION:
        parameters["window_length"] = window_length
    if name in _OPENING_RANGE_FEATURES:
        parameters["opening_range_minutes"] = opening_range_minutes
    if name in {
        StructureFeatureName.FAILED_BREAKOUT_HIGH_FLAG,
        StructureFeatureName.FAILED_BREAKOUT_LOW_FLAG,
    }:
        parameters["failure_window"] = failure_window
    if name in _BBO_FEATURES:
        parameters["bbo_alignment"] = "same_series_same_bar_no_forward_fill"
        parameters["bbo_quality_tokens"] = [
            MISSING_BBO_QUALITY_FLAG,
            BBO_QUARANTINE_QUALITY_FLAG,
        ]
    return parameters


def _input_views(name: StructureFeatureName) -> tuple[str, ...]:
    if name in _BBO_FEATURES:
        return ("canonical_ohlcv", "canonical_bbo")
    return ("canonical_ohlcv",)


def _input_fields(name: StructureFeatureName) -> tuple[str, ...]:
    base = (
        "available_ts",
        "event_ts",
        "series_id",
        "quality_flags",
    )
    bbo_fields = _BBO_FIELDS_BY_FEATURE.get(name, ())
    return tuple(dict.fromkeys((*base, *_OHLCV_FIELDS_BY_FEATURE[name], *bbo_fields)))


def _coerce_ohlcv_view(input_view: OHLCVInputView | CanonicalInputViews) -> OHLCVInputView:
    if isinstance(input_view, CanonicalInputViews):
        return input_view.ohlcv
    if isinstance(input_view, OHLCVInputView):
        return input_view
    raise StructureFeatureError("Liquidity/Structure features require an OHLCVInputView")


def _coerce_bbo_view(input_view: OHLCVInputView | CanonicalInputViews) -> BBOInputView:
    if isinstance(input_view, CanonicalInputViews):
        return input_view.bbo
    raise StructureFeatureError(
        "BBO-derived Liquidity/Structure features require CanonicalInputViews"
    )


def _validated_ohlcv_rows(rows: Sequence[OHLCVInputRow]) -> tuple[OHLCVInputRow, ...]:
    ordered = tuple(rows)
    for row in ordered:
        if not isinstance(row, OHLCVInputRow):
            raise StructureFeatureError("structure inputs must be OHLCVInputRow objects")
        _require_aware_datetime(row.available_ts, "OHLCVInputRow.available_ts")
        _require_aware_datetime(row.event_ts, "OHLCVInputRow.event_ts")
        _require_aware_datetime(row.bar_start_ts, "OHLCVInputRow.bar_start_ts")
        _require_aware_datetime(row.bar_end_ts, "OHLCVInputRow.bar_end_ts")
        for field in ("open", "high", "low", "close", "volume"):
            _to_float(getattr(row, field), f"OHLCVInputRow.{field}")
    return tuple(sorted(ordered, key=lambda row: row.available_ts))


def _validated_bbo_rows(rows: Sequence[BBOInputRow]) -> tuple[BBOInputRow, ...]:
    ordered = tuple(rows)
    for row in ordered:
        if not isinstance(row, BBOInputRow):
            raise StructureFeatureError("BBO-derived structure inputs must be BBOInputRow objects")
        _require_aware_datetime(row.available_ts, "BBOInputRow.available_ts")
        _require_aware_datetime(row.event_ts, "BBOInputRow.event_ts")
        _require_aware_datetime(row.bar_start_ts, "BBOInputRow.bar_start_ts")
        _require_aware_datetime(row.bar_end_ts, "BBOInputRow.bar_end_ts")
        for field in ("bid", "ask", "bid_size", "ask_size", "mid", "spread"):
            _to_float(getattr(row, field), f"BBOInputRow.{field}")
    return tuple(sorted(ordered, key=lambda row: row.available_ts))


def _require_definition(definition: StructureFeatureDefinition) -> StructureFeatureDefinition:
    if not isinstance(definition, StructureFeatureDefinition):
        raise StructureFeatureError("compute requires a StructureFeatureDefinition")
    if definition.spec.family is not FeatureFamily.LIQUIDITY_STRUCTURE:
        raise StructureFeatureError("definition must belong to FeatureFamily.LIQUIDITY_STRUCTURE")
    if not definition.spec.implementation_eligible:
        raise StructureFeatureError("definition is not implementation eligible")
    if not definition.request_gate_decision.implementation_allowed:
        raise StructureFeatureError("FeatureRequest gate did not admit implementation")
    if definition.version != definition.spec.derive_feature_version():
        raise StructureFeatureError("definition FeatureVersion does not match FeatureSpec")
    if not definition.spec.window.is_live_compatible:
        raise StructureFeatureError("Liquidity/Structure live features require causal windows")
    return definition


def _records_from_points(
    definition: StructureFeatureDefinition,
    points: Sequence[_FeaturePoint],
) -> tuple[FeatureValueRecord, ...]:
    return tuple(
        _feature_value_record(
            definition,
            point.row,
            value=point.value,
            quality_flags=point.quality_flags,
        )
        for point in points
    )


def _feature_value_record(
    definition: StructureFeatureDefinition,
    row: OHLCVInputRow,
    *,
    value: float | int | None,
    quality_flags: Sequence[str] = (),
) -> FeatureValueRecord:
    return FeatureValueRecord(
        feature_version_id=definition.feature_version_id,
        entity_id=row.series_id,
        event_ts=row.event_ts,
        available_ts=row.available_ts,
        value=value,
        quality_flags=_quality_flags(quality_flags),
    )


def _prior_distance_points(
    rows: Sequence[OHLCVInputRow],
    definition: StructureFeatureDefinition,
    *,
    high: bool,
) -> tuple[_FeaturePoint, ...]:
    results: list[_FeaturePoint] = []
    for index, row in enumerate(rows):
        if not _is_trade_row(row):
            results.append(_gap_feature_point(row, "no_trade", row.quality_flags))
            continue
        level = _prior_level(rows, index, definition, high=high)
        if level is None:
            results.append(_gap_feature_point(row, "insufficient_window"))
            continue
        if level == 0:
            results.append(_gap_feature_point(row, "zero_prior_level"))
            continue
        close = _to_float(row.close, "close")
        results.append(_FeaturePoint(row=row, value=(close - level) / level))
    return tuple(results)


def _sweep_points(
    rows: Sequence[OHLCVInputRow],
    definition: StructureFeatureDefinition,
    *,
    high: bool,
) -> tuple[_FeaturePoint, ...]:
    results: list[_FeaturePoint] = []
    for index, row in enumerate(rows):
        if not _is_trade_row(row):
            results.append(_gap_feature_point(row, "no_trade", row.quality_flags))
            continue
        level = _prior_level(rows, index, definition, high=high)
        if level is None:
            results.append(_gap_feature_point(row, "insufficient_window"))
            continue
        if high:
            value = 1 if _to_float(row.high, "high") > level >= _to_float(row.close, "close") else 0
        else:
            value = 1 if _to_float(row.low, "low") < level <= _to_float(row.close, "close") else 0
        results.append(_FeaturePoint(row=row, value=value))
    return tuple(results)


def _failed_breakout_points(
    rows: Sequence[OHLCVInputRow],
    definition: StructureFeatureDefinition,
    *,
    high: bool,
) -> tuple[_FeaturePoint, ...]:
    failure_window = _int_parameter(definition, "failure_window")
    active_by_key: dict[tuple[str, str], _BreakoutState] = {}
    results: list[_FeaturePoint] = []
    for index, row in enumerate(rows):
        key = _state_key(row, reset_on_session=_bool_parameter(definition, "reset_on_session"))
        if not _is_trade_row(row):
            results.append(_gap_feature_point(row, "no_trade", row.quality_flags))
            continue

        active = active_by_key.get(key)
        failed = False
        close = _to_float(row.close, "close")
        if active is not None:
            failed = close <= active.level if high else close >= active.level
            if failed or active.remaining_bars <= 1:
                active_by_key.pop(key, None)
            else:
                active_by_key[key] = _BreakoutState(
                    level=active.level,
                    remaining_bars=active.remaining_bars - 1,
                )

        level = _prior_level(rows, index, definition, high=high)
        if level is not None:
            broke_out = close > level if high else close < level
            if broke_out:
                active_by_key[key] = _BreakoutState(
                    level=level,
                    remaining_bars=failure_window,
                )

        results.append(_FeaturePoint(row=row, value=1 if failed else 0))
    return tuple(results)


def _opening_range_distance_points(
    rows: Sequence[OHLCVInputRow],
    definition: StructureFeatureDefinition,
    *,
    high: bool,
) -> tuple[_FeaturePoint, ...]:
    opening_minutes = _int_parameter(definition, "opening_range_minutes")
    state: dict[tuple[str, str], dict[str, float | datetime | None]] = {}
    results: list[_FeaturePoint] = []
    for row in rows:
        key = (row.series_id, row.session_label)
        session_state = state.setdefault(
            key,
            {"session_start": row.bar_start_ts, "opening_high": None, "opening_low": None},
        )
        if row.session_label.upper() != "RTH":
            results.append(_gap_feature_point(row, "outside_rth", row.quality_flags))
            continue
        if not _is_trade_row(row):
            results.append(_gap_feature_point(row, "no_trade", row.quality_flags))
            continue

        session_start = session_state["session_start"]
        if not isinstance(session_start, datetime):
            raise StructureFeatureError("opening range session_start must be a datetime")
        in_opening_window = row.bar_start_ts < session_start + timedelta(minutes=opening_minutes)
        if in_opening_window:
            row_high = _to_float(row.high, "high")
            row_low = _to_float(row.low, "low")
            opening_high = session_state["opening_high"]
            opening_low = session_state["opening_low"]
            session_state["opening_high"] = (
                row_high if opening_high is None else max(float(opening_high), row_high)
            )
            session_state["opening_low"] = (
                row_low if opening_low is None else min(float(opening_low), row_low)
            )

        level = session_state["opening_high"] if high else session_state["opening_low"]
        if level is None:
            results.append(_gap_feature_point(row, "no_opening_trade"))
            continue
        level_float = float(level)
        if level_float == 0:
            results.append(_gap_feature_point(row, "zero_opening_level"))
            continue
        close = _to_float(row.close, "close")
        results.append(_FeaturePoint(row=row, value=(close - level_float) / level_float))
    return tuple(results)


def _close_location_points(rows: Sequence[OHLCVInputRow]) -> tuple[_FeaturePoint, ...]:
    results: list[_FeaturePoint] = []
    for row in rows:
        if not _is_trade_row(row):
            results.append(_gap_feature_point(row, "no_trade", row.quality_flags))
            continue
        high = _to_float(row.high, "high")
        low = _to_float(row.low, "low")
        range_value = high - low
        if range_value <= 0:
            results.append(_gap_feature_point(row, "zero_range"))
            continue
        close = _to_float(row.close, "close")
        results.append(_FeaturePoint(row=row, value=((close - low) - (high - close)) / range_value))
    return tuple(results)


def _wick_rejection_points(rows: Sequence[OHLCVInputRow]) -> tuple[_FeaturePoint, ...]:
    results: list[_FeaturePoint] = []
    for row in rows:
        if not _is_trade_row(row):
            results.append(_gap_feature_point(row, "no_trade", row.quality_flags))
            continue
        high = _to_float(row.high, "high")
        low = _to_float(row.low, "low")
        open_ = _to_float(row.open, "open")
        close = _to_float(row.close, "close")
        range_value = high - low
        if range_value <= 0:
            results.append(_gap_feature_point(row, "zero_range"))
            continue
        upper_wick = high - max(open_, close)
        lower_wick = min(open_, close) - low
        results.append(_FeaturePoint(row=row, value=(lower_wick - upper_wick) / range_value))
    return tuple(results)


def _range_contraction_points(
    rows: Sequence[OHLCVInputRow],
    definition: StructureFeatureDefinition,
) -> tuple[_FeaturePoint, ...]:
    range_points = tuple(_range_primitive_point(row) for row in rows)
    rolling_ranges = rolling_mean(
        range_points,
        definition.spec.window,
        reset_on_session=_bool_parameter(definition, "reset_on_session"),
    )
    results: list[_FeaturePoint] = []
    for row, result in zip(rows, rolling_ranges, strict=True):
        current_range = _current_trade_range(row)
        if result.value is None:
            results.append(_FeaturePoint(row=row, value=None, quality_flags=result.quality_flags))
            continue
        if current_range is None:
            results.append(_gap_feature_point(row, "invalid_range", result.quality_flags))
            continue
        if result.value == 0:
            results.append(_gap_feature_point(row, "zero_range_baseline"))
            continue
        results.append(_FeaturePoint(row=row, value=current_range / result.value))
    return tuple(results)


def _bbo_mid_distance_points(
    rows: Sequence[OHLCVInputRow],
    bbo_rows: Sequence[BBOInputRow],
) -> tuple[_FeaturePoint, ...]:
    bbo_by_bar: dict[tuple[str, datetime], list[BBOInputRow]] = {}
    for quote in bbo_rows:
        bbo_by_bar.setdefault((quote.series_id, quote.bar_start_ts), []).append(quote)
    for quotes in bbo_by_bar.values():
        quotes.sort(key=lambda quote: quote.available_ts)

    results: list[_FeaturePoint] = []
    for row in rows:
        if not _is_trade_row(row):
            results.append(_gap_feature_point(row, "no_trade", row.quality_flags))
            continue
        quotes = bbo_by_bar.get((row.series_id, row.bar_start_ts), [])
        eligible = [quote for quote in quotes if quote.available_ts <= row.available_ts]
        if not eligible:
            future_quote_exists = any(quote.available_ts > row.available_ts for quote in quotes)
            reason = "bbo_after_ohlcv_available_ts" if future_quote_exists else "missing_bbo_match"
            results.append(_gap_feature_point(row, reason, ("bbo_gap",)))
            continue
        quote = eligible[-1]
        if not _is_valid_bbo(quote):
            results.append(_gap_feature_point(row, "bbo_gap", _bbo_gap_flags(quote)))
            continue
        mid = _to_float(quote.mid, "mid")
        if mid <= 0:
            results.append(_gap_feature_point(row, "zero_mid", ("bbo_gap",)))
            continue
        close = _to_float(row.close, "close")
        results.append(_FeaturePoint(row=row, value=(close - mid) / mid))
    return tuple(results)


def _prior_level(
    rows: Sequence[OHLCVInputRow],
    index: int,
    definition: StructureFeatureDefinition,
    *,
    high: bool,
) -> float | None:
    prior_rows = _prior_trade_rows(rows, index, definition)
    if len(prior_rows) < definition.spec.window.length:
        return None
    values = [_to_float(row.high if high else row.low, "prior_level") for row in prior_rows]
    return max(values) if high else min(values)


def _prior_trade_rows(
    rows: Sequence[OHLCVInputRow],
    index: int,
    definition: StructureFeatureDefinition,
) -> tuple[OHLCVInputRow, ...]:
    reset_on_session = _bool_parameter(definition, "reset_on_session")
    current = rows[index]
    selected: list[OHLCVInputRow] = []
    for prior_index in range(index - 1, -1, -1):
        prior = rows[prior_index]
        if prior.series_id != current.series_id:
            continue
        if reset_on_session and prior.session_label != current.session_label:
            continue
        if not _is_trade_row(prior):
            continue
        selected.append(prior)
        if len(selected) == definition.spec.window.length:
            break
    selected.reverse()
    return tuple(selected)


def _range_primitive_point(row: OHLCVInputRow) -> PrimitivePoint:
    if not _is_trade_row(row):
        return PrimitivePoint(
            available_ts=row.available_ts,
            event_ts=row.event_ts,
            value=None,
            session_label=row.session_label,
            quality_flags=_gap_flags("no_trade", row.quality_flags),
        )
    range_value = _current_trade_range(row)
    return PrimitivePoint(
        available_ts=row.available_ts,
        event_ts=row.event_ts,
        value=range_value,
        session_label=row.session_label,
        quality_flags=() if range_value is not None else ("invalid_range",),
    )


def _current_trade_range(row: OHLCVInputRow) -> float | None:
    if not _is_trade_row(row):
        return None
    high = _to_float(row.high, "high")
    low = _to_float(row.low, "low")
    if high < low:
        return None
    return high - low


def _state_key(row: OHLCVInputRow, *, reset_on_session: bool) -> tuple[str, str]:
    return (row.series_id, row.session_label if reset_on_session else "")


def _gap_feature_point(
    row: OHLCVInputRow,
    reason: str,
    extra_flags: Sequence[str] = (),
) -> _FeaturePoint:
    return _FeaturePoint(row=row, value=None, quality_flags=_gap_flags(reason, extra_flags))


def _gap_flags(reason: str, extra_flags: Sequence[str] = ()) -> tuple[str, ...]:
    return tuple(sorted({"structure_gap", reason.strip().lower(), *_quality_flags(extra_flags)}))


def _is_trade_row(row: OHLCVInputRow) -> bool:
    return is_real_trade_bar(row)


def _is_valid_bbo(row: BBOInputRow) -> bool:
    try:
        return is_valid_bbo_quote(row)
    except DataFoundationValidationError as exc:
        raise StructureFeatureError(str(exc)) from exc


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


def _quote_semantics(row: BBOInputRow) -> BBOQuoteSemantics:
    try:
        return bbo_quote_semantics(row)
    except DataFoundationValidationError as exc:
        raise StructureFeatureError(str(exc)) from exc


def _int_parameter(definition: StructureFeatureDefinition, name: str) -> int:
    value = definition.spec.transform.parameters.to_dict().get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise StructureFeatureError(f"{name} parameter must be an integer")
    return value


def _bool_parameter(definition: StructureFeatureDefinition, name: str) -> bool:
    value = definition.spec.transform.parameters.to_dict().get(name)
    if type(value) is not bool:
        raise StructureFeatureError(f"{name} parameter must be a bool")
    return value


def _coerce_feature_name(name: StructureFeatureName | str) -> StructureFeatureName:
    try:
        return StructureFeatureName(name)
    except ValueError as exc:
        raise StructureFeatureError(f"unsupported Liquidity/Structure feature: {name}") from exc


def _positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise StructureFeatureError(f"{field_name} must be a positive integer")
    return value


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise StructureFeatureError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise StructureFeatureError(f"{field_name} must be timezone-aware")
    return value


def _to_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, _NUMERIC_TYPES):
        raise StructureFeatureError(f"{field_name} must be numeric")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise StructureFeatureError(f"{field_name} must be finite")
    return parsed


def _quality_flags(flags: Sequence[str]) -> tuple[str, ...]:
    if isinstance(flags, str) or not isinstance(flags, Sequence):
        raise StructureFeatureError("quality_flags must be a sequence of strings")
    normalized: list[str] = []
    for flag in flags:
        if not isinstance(flag, str) or not flag.strip():
            raise StructureFeatureError("quality_flags must contain non-empty strings")
        token = flag.strip().lower()
        if token not in normalized:
            normalized.append(token)
    return tuple(normalized)


__all__ = [
    "StructureFeatureDefinition",
    "StructureFeatureError",
    "StructureFeatureName",
    "build_structure_feature_definition",
    "build_structure_feature_definitions",
    "compute_structure_feature",
    "compute_structure_features",
    "supported_structure_features",
]
