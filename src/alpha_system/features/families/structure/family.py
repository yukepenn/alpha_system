"""Causal liquidity sweep and structure primitive feature definitions."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Any

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
from alpha_system.features.primitives import PrimitivePoint, rolling_range
from alpha_system.features.request_gate import (
    FeatureRequestGateDecision,
    require_feature_request_implementation_allowed,
)
from alpha_system.features.semantics import bbo_quote_semantics, is_real_trade_bar
from alpha_system.governance.duplicate_exposure import RegistryReader
from alpha_system.governance.feature_request import FeatureRequest


class StructureFeatureError(ValueError):
    """Raised when Liquidity Structure family computation fails closed."""


class StructureFeatureName(StrEnum):
    """Supported Liquidity Structure feature names for FLF-P12."""

    PRIOR_HIGH_DISTANCE = "prior_high_distance"
    PRIOR_LOW_DISTANCE = "prior_low_distance"
    OPENING_RANGE_HIGH_DISTANCE = "opening_range_high_distance"
    OPENING_RANGE_LOW_DISTANCE = "opening_range_low_distance"
    SWEEP_HIGH_FLAG = "sweep_high_flag"
    SWEEP_LOW_FLAG = "sweep_low_flag"
    FAILED_HIGH_BREAKOUT_FLAG = "failed_high_breakout_flag"
    FAILED_LOW_BREAKOUT_FLAG = "failed_low_breakout_flag"
    CLOSE_LOCATION_VALUE = "close_location_value"
    WICK_REJECTION_SCORE = "wick_rejection_score"
    RANGE_CONTRACTION = "range_contraction"


@dataclass(frozen=True, slots=True)
class StructureInputBundle:
    """Canonical input views for OHLCV structure descriptors plus BBO quality context."""

    ohlcv: OHLCVInputView
    bbo: BBOInputView | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.ohlcv, OHLCVInputView):
            raise StructureFeatureError("StructureInputBundle.ohlcv must be an OHLCVInputView")
        if self.bbo is not None and not isinstance(self.bbo, BBOInputView):
            raise StructureFeatureError("StructureInputBundle.bbo must be a BBOInputView")
        _validated_ohlcv_rows(self.ohlcv.rows)
        if self.bbo is not None:
            _validated_bbo_rows(self.bbo.rows)


@dataclass(frozen=True, slots=True)
class StructureFeatureSpec:
    """Liquidity Structure family view over a governed FLF-P06 ``FeatureSpec``."""

    feature_spec: FeatureSpec
    feature_name: StructureFeatureName

    def __post_init__(self) -> None:
        if not isinstance(self.feature_spec, FeatureSpec):
            raise StructureFeatureError("StructureFeatureSpec.feature_spec must be a FeatureSpec")
        feature_name = _coerce_feature_name(self.feature_name)
        if self.feature_spec.family is not FeatureFamily.LIQUIDITY_STRUCTURE:
            raise StructureFeatureError(
                "StructureFeatureSpec requires FeatureFamily.LIQUIDITY_STRUCTURE"
            )
        object.__setattr__(self, "feature_name", feature_name)

    @property
    def feature_id(self) -> str:
        """Return the stable feature id from the underlying contract."""

        return self.feature_spec.feature_id

    @property
    def family(self) -> FeatureFamily:
        """Return the shared FLF-P06 feature family enum."""

        return self.feature_spec.family

    @property
    def feature_request_id(self) -> str:
        """Return the governed ``freq_`` request id."""

        return self.feature_spec.feature_request_id

    @property
    def inputs(self) -> FeatureInputSpec:
        """Return the underlying input contract."""

        return self.feature_spec.inputs

    @property
    def transform(self) -> TransformSpec:
        """Return the underlying transform contract."""

        return self.feature_spec.transform

    @property
    def window(self) -> WindowSpec:
        """Return the underlying window contract."""

        return self.feature_spec.window

    @property
    def normalization(self) -> NormalizationSpec:
        """Return the underlying normalization contract."""

        return self.feature_spec.normalization

    @property
    def live(self) -> bool:
        """Return whether the underlying contract is live-compatible."""

        return self.feature_spec.live

    @property
    def implementation_eligible(self) -> bool:
        """Return whether the approved request gate admitted implementation."""

        return self.feature_spec.implementation_eligible

    def derive_feature_version(self) -> FeatureVersion:
        """Derive the deterministic version from the underlying contract."""

        return self.feature_spec.derive_feature_version()

    def to_contract_dict(self) -> dict[str, object]:
        """Return the canonical underlying feature contract payload."""

        return self.feature_spec.to_contract_dict()


@dataclass(frozen=True, slots=True)
class PriorExtremeFeatureSpec(StructureFeatureSpec):
    """Prior high/low distance feature contract."""


@dataclass(frozen=True, slots=True)
class OpeningRangeFeatureSpec(StructureFeatureSpec):
    """Opening-range distance feature contract."""


@dataclass(frozen=True, slots=True)
class SweepFeatureSpec(StructureFeatureSpec):
    """Sweep and failed-breakout flag feature contract."""


@dataclass(frozen=True, slots=True)
class WickFeatureSpec(StructureFeatureSpec):
    """Close-location and wick-rejection feature contract."""


@dataclass(frozen=True, slots=True)
class CompressionFeatureSpec(StructureFeatureSpec):
    """Range-contraction feature contract."""


@dataclass(frozen=True, slots=True)
class StructureFeatureDefinition:
    """Approved, versioned Liquidity Structure feature definition."""

    name: StructureFeatureName
    spec: StructureFeatureSpec
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


type _Numeric = int | float | Decimal

_NUMERIC_TYPES = (int, float, Decimal)
_PRIOR_FEATURES = frozenset(
    {
        StructureFeatureName.PRIOR_HIGH_DISTANCE,
        StructureFeatureName.PRIOR_LOW_DISTANCE,
    }
)
_OPENING_RANGE_FEATURES = frozenset(
    {
        StructureFeatureName.OPENING_RANGE_HIGH_DISTANCE,
        StructureFeatureName.OPENING_RANGE_LOW_DISTANCE,
    }
)
_SWEEP_FEATURES = frozenset(
    {
        StructureFeatureName.SWEEP_HIGH_FLAG,
        StructureFeatureName.SWEEP_LOW_FLAG,
        StructureFeatureName.FAILED_HIGH_BREAKOUT_FLAG,
        StructureFeatureName.FAILED_LOW_BREAKOUT_FLAG,
    }
)
_WICK_FEATURES = frozenset(
    {
        StructureFeatureName.CLOSE_LOCATION_VALUE,
        StructureFeatureName.WICK_REJECTION_SCORE,
    }
)
_COMPRESSION_FEATURES = frozenset({StructureFeatureName.RANGE_CONTRACTION})
_ROLLING_PRIOR_FEATURES = _PRIOR_FEATURES | _SWEEP_FEATURES | _COMPRESSION_FEATURES
_FIELDS_BY_FEATURE: dict[StructureFeatureName, tuple[str, ...]] = {
    StructureFeatureName.PRIOR_HIGH_DISTANCE: ("high", "low", "close"),
    StructureFeatureName.PRIOR_LOW_DISTANCE: ("high", "low", "close"),
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
    StructureFeatureName.SWEEP_HIGH_FLAG: ("high", "low", "close"),
    StructureFeatureName.SWEEP_LOW_FLAG: ("high", "low", "close"),
    StructureFeatureName.FAILED_HIGH_BREAKOUT_FLAG: ("high", "low", "close"),
    StructureFeatureName.FAILED_LOW_BREAKOUT_FLAG: ("high", "low", "close"),
    StructureFeatureName.CLOSE_LOCATION_VALUE: ("high", "low", "close"),
    StructureFeatureName.WICK_REJECTION_SCORE: ("open", "high", "low", "close"),
    StructureFeatureName.RANGE_CONTRACTION: ("high", "low"),
}


def supported_structure_features() -> tuple[StructureFeatureName, ...]:
    """Return the complete FLF-P12 Liquidity Structure feature list."""

    return tuple(StructureFeatureName)


def build_structure_feature_definition(
    name: StructureFeatureName | str,
    feature_request: FeatureRequest | Mapping[str, Any] | None,
    registry_reader: RegistryReader | object | None,
    *,
    dataset_version_ids: Sequence[str] = (),
    window_length: int = 3,
    opening_range_minutes: int = 30,
    opening_session_label: str = "RTH",
    reset_on_session: bool = True,
    window: WindowSpec | None = None,
) -> StructureFeatureDefinition:
    """Build one approved Liquidity Structure feature definition.

    The FLF-P05 request gate is the only admission path. Missing, invalid,
    unapproved, duplicate-blocked, or registry-unchecked requests fail closed.
    """

    feature_name = _coerce_feature_name(name)
    window_length = _positive_int(window_length, "window_length")
    opening_range_minutes = _positive_int(opening_range_minutes, "opening_range_minutes")
    opening_session_label = _require_text(opening_session_label, "opening_session_label").upper()
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
        opening_session_label=opening_session_label,
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
    """Build multiple approved Liquidity Structure feature definitions."""

    return tuple(
        build_structure_feature_definition(name, request, registry_reader, **parameters)
        for name, request in feature_requests.items()
    )


def compute_structure_feature(
    definition: StructureFeatureDefinition,
    input_views: StructureInputBundle | OHLCVInputView | CanonicalInputViews,
) -> tuple[FeatureValueRecord, ...]:
    """Compute one Liquidity Structure feature as in-memory value records.

    Values are returned only to the caller. This function does not materialize,
    persist, register, or write feature values.
    """

    definition = _require_definition(definition)
    bundle = _coerce_input_bundle(input_views)
    rows = _validated_ohlcv_rows(bundle.ohlcv.rows)
    bbo_flags_by_available_ts = _bbo_quality_flags_by_available_ts(bundle.bbo)
    if definition.name in _PRIOR_FEATURES:
        points = _prior_distance_points(definition, rows)
    elif definition.name in _OPENING_RANGE_FEATURES:
        points = _opening_range_distance_points(definition, rows)
    elif definition.name in _SWEEP_FEATURES:
        points = _sweep_points(definition, rows)
    elif definition.name in _WICK_FEATURES:
        points = _wick_points(definition, rows)
    elif definition.name in _COMPRESSION_FEATURES:
        points = _range_contraction_points(definition, rows)
    else:
        raise StructureFeatureError(f"unsupported Liquidity Structure feature: {definition.name}")
    return _records_from_points(definition, _attach_bbo_flags(points, bbo_flags_by_available_ts))


def compute_structure_features(
    definitions: Iterable[StructureFeatureDefinition],
    input_views: StructureInputBundle | OHLCVInputView | CanonicalInputViews,
) -> dict[StructureFeatureName, tuple[FeatureValueRecord, ...]]:
    """Compute approved Liquidity Structure definitions against canonical views."""

    return {
        definition.name: compute_structure_feature(definition, input_views)
        for definition in definitions
    }


def _feature_spec(
    name: StructureFeatureName,
    gate_decision: FeatureRequestGateDecision,
    *,
    dataset_version_ids: Sequence[str],
    window_length: int,
    opening_range_minutes: int,
    opening_session_label: str,
    reset_on_session: bool,
    window: WindowSpec | None,
) -> StructureFeatureSpec:
    if gate_decision.feature_request_id is None:
        raise StructureFeatureError("approved FeatureRequestGateDecision must expose freq_ id")
    feature_window = window or _default_window(name, window_length=window_length)
    parameters = _transform_parameters(
        name,
        window_length=window_length,
        opening_range_minutes=opening_range_minutes,
        opening_session_label=opening_session_label,
        reset_on_session=reset_on_session,
    )
    feature_spec = FeatureSpec(
        feature_id=f"liquidity_structure_{name.value}",
        family=FeatureFamily.LIQUIDITY_STRUCTURE,
        feature_request_id=gate_decision.feature_request_id,
        inputs=FeatureInputSpec(
            input_views=("canonical_ohlcv", "canonical_bbo"),
            fields=_input_fields(name),
            dataset_version_ids=tuple(dataset_version_ids),
            input_metadata={
                "consumption_surface": (
                    "alpha_system.features.input_views.StructureInputBundle-compatible "
                    "OHLCVInputView with optional exact-time BBOInputView quality context"
                ),
                "accepted_dataset_version_gate": (
                    "input views are produced upstream from accepted DatasetVersions"
                ),
                "trade_semantics": (
                    "FLF-P04 no_trade rows are gaps for sweep, breakout, wick, "
                    "opening-range, and compression logic"
                ),
                "bbo_quality_surface": (
                    "missing_bbo and bbo_quarantined rows are surfaced only at exact "
                    "available_ts; quotes are never filled or interpolated"
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
            "input": "canonical OHLCV and BBO rows are accepted input-view rows",
            "causality": "outputs use only source rows with available_ts <= output available_ts",
            "missingness": (
                "no_trade rows are OHLCV gaps; BBO missingness is flagged at exact "
                "available_ts without quote forward-fill"
            ),
        },
        available_ts_derivation_rule=(
            "feature.available_ts = current OHLCV input row available_ts; trailing "
            "structure state may use only source rows whose available_ts is <= current "
            "row available_ts; BBO quality flags are joined only by exact available_ts"
        ),
        live=True,
        implementation_eligible=True,
        contract_metadata={
            "campaign": "ALPHA_FEATURE_LABEL_FOUNDATION_V1",
            "phase": "FLF-P12",
            "materialization": "in_memory_records_only",
            "claims": "structure_descriptors_only_no_alpha_or_tradability_claim",
        },
        request_gate_decision=gate_decision,
    )
    return _wrap_feature_spec(name, feature_spec)


def _wrap_feature_spec(
    name: StructureFeatureName,
    feature_spec: FeatureSpec,
) -> StructureFeatureSpec:
    if name in _PRIOR_FEATURES:
        return PriorExtremeFeatureSpec(feature_spec=feature_spec, feature_name=name)
    if name in _OPENING_RANGE_FEATURES:
        return OpeningRangeFeatureSpec(feature_spec=feature_spec, feature_name=name)
    if name in _SWEEP_FEATURES:
        return SweepFeatureSpec(feature_spec=feature_spec, feature_name=name)
    if name in _WICK_FEATURES:
        return WickFeatureSpec(feature_spec=feature_spec, feature_name=name)
    if name in _COMPRESSION_FEATURES:
        return CompressionFeatureSpec(feature_spec=feature_spec, feature_name=name)
    return StructureFeatureSpec(feature_spec=feature_spec, feature_name=name)


def _default_window(name: StructureFeatureName, *, window_length: int) -> WindowSpec:
    if name in _ROLLING_PRIOR_FEATURES:
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
        StructureFeatureName.FAILED_HIGH_BREAKOUT_FLAG: "failed_high_breakout_flag",
        StructureFeatureName.FAILED_LOW_BREAKOUT_FLAG: "failed_low_breakout_flag",
        StructureFeatureName.CLOSE_LOCATION_VALUE: "close_location_value",
        StructureFeatureName.WICK_REJECTION_SCORE: "wick_rejection_score",
        StructureFeatureName.RANGE_CONTRACTION: "range_contraction",
    }[name]


def _transform_parameters(
    name: StructureFeatureName,
    *,
    window_length: int,
    opening_range_minutes: int,
    opening_session_label: str,
    reset_on_session: bool,
) -> dict[str, object]:
    parameters: dict[str, object] = {
        "feature_name": name.value,
        "reset_on_session": reset_on_session,
    }
    if name in _ROLLING_PRIOR_FEATURES:
        parameters["window_length"] = window_length
    if name in _OPENING_RANGE_FEATURES:
        parameters["opening_range_minutes"] = opening_range_minutes
        parameters["opening_session_label"] = opening_session_label
    return parameters


def _input_fields(name: StructureFeatureName) -> tuple[str, ...]:
    base = (
        "available_ts",
        "event_ts",
        "series_id",
        "session_label",
        "quality_flags",
        "bbo.available_ts",
        "bbo.quality_flags",
    )
    return tuple(dict.fromkeys((*base, *_FIELDS_BY_FEATURE[name])))


def _coerce_input_bundle(
    input_views: StructureInputBundle | OHLCVInputView | CanonicalInputViews,
) -> StructureInputBundle:
    if isinstance(input_views, StructureInputBundle):
        return input_views
    if isinstance(input_views, CanonicalInputViews):
        return StructureInputBundle(ohlcv=input_views.ohlcv, bbo=input_views.bbo)
    if isinstance(input_views, OHLCVInputView):
        return StructureInputBundle(ohlcv=input_views)
    raise StructureFeatureError(
        "Liquidity Structure features require StructureInputBundle or canonical input views"
    )


def _validated_ohlcv_rows(rows: Sequence[OHLCVInputRow]) -> tuple[OHLCVInputRow, ...]:
    ordered = tuple(rows)
    for row in ordered:
        if not isinstance(row, OHLCVInputRow):
            raise StructureFeatureError("Structure OHLCV inputs must be OHLCVInputRow")
        _require_aware_datetime(row.available_ts, "OHLCVInputRow.available_ts")
        _require_aware_datetime(row.event_ts, "OHLCVInputRow.event_ts")
        _require_aware_datetime(row.bar_start_ts, "OHLCVInputRow.bar_start_ts")
        _require_aware_datetime(row.bar_end_ts, "OHLCVInputRow.bar_end_ts")
        for field in ("open", "high", "low", "close", "volume"):
            _to_float(getattr(row, field), f"OHLCVInputRow.{field}")
        _require_bar_bounds(row)
        _quality_flags(row.quality_flags)
    return tuple(sorted(ordered, key=lambda row: row.available_ts))


def _validated_bbo_rows(rows: Sequence[BBOInputRow]) -> tuple[BBOInputRow, ...]:
    ordered = tuple(rows)
    for row in ordered:
        if not isinstance(row, BBOInputRow):
            raise StructureFeatureError("Structure BBO inputs must be BBOInputRow")
        _require_aware_datetime(row.available_ts, "BBOInputRow.available_ts")
        _require_aware_datetime(row.event_ts, "BBOInputRow.event_ts")
        _quality_flags(row.quality_flags)
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
        raise StructureFeatureError("Liquidity Structure live features require causal windows")
    return definition


def _records_from_points(
    definition: StructureFeatureDefinition,
    points: Sequence[_FeaturePoint],
) -> tuple[FeatureValueRecord, ...]:
    return tuple(
        FeatureValueRecord(
            feature_version_id=definition.feature_version_id,
            entity_id=point.row.series_id,
            event_ts=point.row.event_ts,
            available_ts=point.row.available_ts,
            value=point.value,
            quality_flags=_quality_flags(point.quality_flags),
        )
        for point in points
    )


def _prior_distance_points(
    definition: StructureFeatureDefinition,
    rows: Sequence[OHLCVInputRow],
) -> tuple[_FeaturePoint, ...]:
    results: list[_FeaturePoint] = []
    for index, row in enumerate(rows):
        current_gap = _current_trade_gap(row)
        if current_gap is not None:
            results.append(current_gap)
            continue
        prior_rows, flags = _prior_window(rows, index, definition)
        if prior_rows is None:
            results.append(_gap_feature_point(row, "input_gap", flags))
            continue
        prior_high = max(_to_float(item.high, "high") for item in prior_rows)
        prior_low = min(_to_float(item.low, "low") for item in prior_rows)
        close = _to_float(row.close, "close")
        value = close - prior_high
        if definition.name is StructureFeatureName.PRIOR_LOW_DISTANCE:
            value = close - prior_low
        results.append(_FeaturePoint(row=row, value=value))
    return tuple(results)


def _opening_range_distance_points(
    definition: StructureFeatureDefinition,
    rows: Sequence[OHLCVInputRow],
) -> tuple[_FeaturePoint, ...]:
    parameters = definition.spec.transform.parameters.to_dict()
    opening_minutes = _int_parameter(definition, "opening_range_minutes")
    opening_session = _require_text(
        parameters.get("opening_session_label"),
        "opening_session_label",
    )
    opening_high: float | None = None
    opening_low: float | None = None
    session_start: datetime | None = None
    previous_key: tuple[str, str] | None = None
    results: list[_FeaturePoint] = []
    for row in rows:
        key = (row.series_id, row.session_label)
        if key != previous_key:
            previous_key = key
            session_start = row.bar_start_ts
            opening_high = None
            opening_low = None

        current_gap = _current_trade_gap(row)
        if current_gap is not None:
            results.append(current_gap)
            continue
        if row.session_label.upper() != opening_session:
            results.append(_gap_feature_point(row, "outside_opening_session"))
            continue
        assert session_start is not None
        in_window = row.bar_start_ts < session_start + _minutes(opening_minutes)
        if in_window:
            row_high = _to_float(row.high, "high")
            row_low = _to_float(row.low, "low")
            opening_high = row_high if opening_high is None else max(opening_high, row_high)
            opening_low = row_low if opening_low is None else min(opening_low, row_low)
        if opening_high is None or opening_low is None:
            results.append(_gap_feature_point(row, "no_opening_trade"))
            continue
        close = _to_float(row.close, "close")
        value = close - opening_high
        if definition.name is StructureFeatureName.OPENING_RANGE_LOW_DISTANCE:
            value = close - opening_low
        results.append(_FeaturePoint(row=row, value=value))
    return tuple(results)


def _sweep_points(
    definition: StructureFeatureDefinition,
    rows: Sequence[OHLCVInputRow],
) -> tuple[_FeaturePoint, ...]:
    results: list[_FeaturePoint] = []
    for index, row in enumerate(rows):
        current_gap = _current_trade_gap(row)
        if current_gap is not None:
            results.append(current_gap)
            continue
        prior_rows, flags = _prior_window(rows, index, definition)
        if prior_rows is None:
            results.append(_gap_feature_point(row, "input_gap", flags))
            continue
        prior_high = max(_to_float(item.high, "high") for item in prior_rows)
        prior_low = min(_to_float(item.low, "low") for item in prior_rows)
        row_high = _to_float(row.high, "high")
        row_low = _to_float(row.low, "low")
        close = _to_float(row.close, "close")
        high_sweep = row_high > prior_high
        low_sweep = row_low < prior_low
        if definition.name is StructureFeatureName.SWEEP_HIGH_FLAG:
            value = 1 if high_sweep else 0
        elif definition.name is StructureFeatureName.SWEEP_LOW_FLAG:
            value = 1 if low_sweep else 0
        elif definition.name is StructureFeatureName.FAILED_HIGH_BREAKOUT_FLAG:
            value = 1 if high_sweep and close <= prior_high else 0
        elif definition.name is StructureFeatureName.FAILED_LOW_BREAKOUT_FLAG:
            value = 1 if low_sweep and close >= prior_low else 0
        else:
            raise StructureFeatureError(f"unsupported sweep feature: {definition.name}")
        results.append(_FeaturePoint(row=row, value=value))
    return tuple(results)


def _wick_points(
    definition: StructureFeatureDefinition,
    rows: Sequence[OHLCVInputRow],
) -> tuple[_FeaturePoint, ...]:
    results: list[_FeaturePoint] = []
    for row in rows:
        current_gap = _current_trade_gap(row)
        if current_gap is not None:
            results.append(current_gap)
            continue
        bar_range = _bar_range(row)
        if bar_range <= 0:
            results.append(_gap_feature_point(row, "zero_range"))
            continue
        if definition.name is StructureFeatureName.CLOSE_LOCATION_VALUE:
            value = (_to_float(row.close, "close") - _to_float(row.low, "low")) / bar_range
        elif definition.name is StructureFeatureName.WICK_REJECTION_SCORE:
            body_high = max(_to_float(row.open, "open"), _to_float(row.close, "close"))
            body_low = min(_to_float(row.open, "open"), _to_float(row.close, "close"))
            upper_wick = _to_float(row.high, "high") - body_high
            lower_wick = body_low - _to_float(row.low, "low")
            value = (lower_wick - upper_wick) / bar_range
        else:
            raise StructureFeatureError(f"unsupported wick feature: {definition.name}")
        results.append(_FeaturePoint(row=row, value=value))
    return tuple(results)


def _range_contraction_points(
    definition: StructureFeatureDefinition,
    rows: Sequence[OHLCVInputRow],
) -> tuple[_FeaturePoint, ...]:
    primitive_ranges = rolling_range(
        (
            PrimitivePoint(
                available_ts=row.available_ts,
                event_ts=row.event_ts,
                value=_bar_range(row) if is_real_trade_bar(row) else None,
                session_label=row.session_label,
                quality_flags=() if is_real_trade_bar(row) else _no_trade_flags(row),
            )
            for row in rows
        ),
        definition.spec.window,
        reset_on_session=_bool_parameter(definition, "reset_on_session"),
    )
    results: list[_FeaturePoint] = []
    for index, row in enumerate(rows):
        current_gap = _current_trade_gap(row)
        if current_gap is not None:
            results.append(current_gap)
            continue
        prior_rows, flags = _prior_window(rows, index, definition)
        if prior_rows is None:
            results.append(_gap_feature_point(row, "input_gap", flags))
            continue
        prior_ranges = [_bar_range(prior_row) for prior_row in prior_rows]
        prior_mean_range = sum(prior_ranges) / len(prior_ranges)
        if prior_mean_range <= 0:
            results.append(_gap_feature_point(row, "zero_prior_range"))
            continue
        current_range = _bar_range(row)
        if current_range <= 0:
            results.append(_gap_feature_point(row, "zero_range"))
            continue
        primitive_result = primitive_ranges[index]
        if primitive_result.is_gap:
            flags = set(_quality_flags(primitive_result.quality_flags))
            flags.discard("insufficient_window")
            if flags:
                results.append(_gap_feature_point(row, "input_gap", tuple(sorted(flags))))
                continue
        results.append(_FeaturePoint(row=row, value=1.0 - current_range / prior_mean_range))
    return tuple(results)


def _prior_window(
    rows: Sequence[OHLCVInputRow],
    index: int,
    definition: StructureFeatureDefinition,
) -> tuple[tuple[OHLCVInputRow, ...], tuple[str, ...]] | tuple[None, tuple[str, ...]]:
    window_length = definition.spec.window.length
    reset_on_session = _bool_parameter(definition, "reset_on_session")
    start = max(0, index - window_length)
    if reset_on_session:
        current_session = rows[index].session_label
        for prior_index in range(index - 1, start - 1, -1):
            if rows[prior_index].session_label != current_session:
                start = prior_index + 1
                break
    window_rows = tuple(rows[start:index])
    if len(window_rows) < window_length:
        return None, ("insufficient_window",)
    gap_flags = _window_gap_flags(window_rows)
    if gap_flags:
        return None, gap_flags
    return window_rows, ()


def _window_gap_flags(rows: Sequence[OHLCVInputRow]) -> tuple[str, ...]:
    flags: set[str] = set()
    for row in rows:
        if not is_real_trade_bar(row):
            flags.add("no_trade")
            flags.update(_quality_flags(row.quality_flags))
    return tuple(sorted(flags))


def _current_trade_gap(row: OHLCVInputRow) -> _FeaturePoint | None:
    if is_real_trade_bar(row):
        return None
    return _gap_feature_point(row, "no_trade", _no_trade_flags(row))


def _no_trade_flags(row: OHLCVInputRow) -> tuple[str, ...]:
    flags = set(_quality_flags(row.quality_flags))
    flags.add("no_trade")
    return tuple(sorted(flags))


def _attach_bbo_flags(
    points: Sequence[_FeaturePoint],
    bbo_flags_by_available_ts: Mapping[datetime, tuple[str, ...]],
) -> tuple[_FeaturePoint, ...]:
    if not bbo_flags_by_available_ts:
        return tuple(points)
    merged: list[_FeaturePoint] = []
    for point in points:
        bbo_flags = bbo_flags_by_available_ts.get(point.row.available_ts, ())
        if not bbo_flags:
            merged.append(point)
            continue
        merged.append(
            _FeaturePoint(
                row=point.row,
                value=point.value,
                quality_flags=tuple(sorted({*point.quality_flags, *bbo_flags})),
            )
        )
    return tuple(merged)


def _bbo_quality_flags_by_available_ts(
    view: BBOInputView | None,
) -> Mapping[datetime, tuple[str, ...]]:
    if view is None:
        return MappingProxyType({})
    flags_by_ts: dict[datetime, set[str]] = {}
    for row in _validated_bbo_rows(view.rows):
        try:
            semantics = bbo_quote_semantics(row)
        except DataFoundationValidationError as exc:
            raise StructureFeatureError(str(exc)) from exc
        flags: set[str] = set()
        if semantics.missing_or_abnormal:
            flags.add("bbo_gap")
            flags.update(_quality_flags(row.quality_flags))
        if not semantics.invariants_hold:
            flags.add("bbo_invariant_violation")
        if flags:
            flags_by_ts.setdefault(row.available_ts, set()).update(flags)
    return MappingProxyType(
        {
            available_ts: tuple(sorted(flags))
            for available_ts, flags in flags_by_ts.items()
        }
    )


def _gap_feature_point(
    row: OHLCVInputRow,
    reason: str,
    extra_flags: Sequence[str] = (),
) -> _FeaturePoint:
    return _FeaturePoint(
        row=row,
        value=None,
        quality_flags=tuple(
            sorted(
                {
                    "structure_gap",
                    reason.strip().lower(),
                    *_quality_flags(extra_flags),
                }
            )
        ),
    )


def _bar_range(row: OHLCVInputRow) -> float:
    return _to_float(row.high, "high") - _to_float(row.low, "low")


def _require_bar_bounds(row: OHLCVInputRow) -> None:
    high = _to_float(row.high, "high")
    low = _to_float(row.low, "low")
    open_ = _to_float(row.open, "open")
    close = _to_float(row.close, "close")
    if high < low:
        raise StructureFeatureError("OHLCVInputRow.high must be >= low")
    if open_ > high or open_ < low or close > high or close < low:
        raise StructureFeatureError("OHLCVInputRow.open and close must be within high/low")


def _minutes(value: int) -> object:
    return timedelta(minutes=value)


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
        raise StructureFeatureError(f"unsupported Liquidity Structure feature: {name}") from exc


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


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise StructureFeatureError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise StructureFeatureError(f"{field_name} must be non-empty")
    return normalized


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
    "CompressionFeatureSpec",
    "OpeningRangeFeatureSpec",
    "PriorExtremeFeatureSpec",
    "StructureFeatureDefinition",
    "StructureFeatureError",
    "StructureFeatureName",
    "StructureFeatureSpec",
    "StructureInputBundle",
    "SweepFeatureSpec",
    "WickFeatureSpec",
    "build_structure_feature_definition",
    "build_structure_feature_definitions",
    "compute_structure_feature",
    "compute_structure_features",
    "supported_structure_features",
]
