"""Causal Base OHLCV feature definitions and in-memory calculations."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Any

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
    CanonicalInputViews,
    OHLCVInputRow,
    OHLCVInputView,
)
from alpha_system.features.primitives import (
    PrimitivePoint,
    PrimitiveResult,
    average_true_range,
    bars_from_trade_rows,
    causal_zscore,
    log_returns,
    points_from_trade_rows,
    rolling_volatility,
    simple_returns,
)
from alpha_system.features.request_gate import (
    FeatureRequestGateDecision,
    require_feature_request_implementation_allowed,
)
from alpha_system.features.semantics import is_real_trade_bar
from alpha_system.governance.duplicate_exposure import RegistryReader
from alpha_system.governance.feature_request import FeatureRequest


class OHLCVFeatureError(ValueError):
    """Raised when Base OHLCV family computation fails closed."""


class OHLCVFeatureName(StrEnum):
    """Supported Base OHLCV feature names for FLF-P08."""

    RETURNS = "returns"
    LOG_RETURNS = "log_returns"
    ROLLING_VOLATILITY = "rolling_volatility"
    ROLLING_RANGE = "rolling_range"
    ATR = "atr"
    VOLUME_ZSCORE = "volume_zscore"
    ROLLING_VOLUME = "rolling_volume"
    SESSION_MINUTE = "session_minute"
    RTH_FLAG = "rth_flag"
    ETH_FLAG = "eth_flag"
    OPENING_RANGE = "opening_range"
    OVERNIGHT_RANGE = "overnight_range"
    VWAP = "vwap"
    ANCHORED_VWAP = "anchored_vwap"
    DISTANCE_TO_VWAP = "distance_to_vwap"
    RANGE_POSITION = "range_position"
    TRENDINESS = "trendiness"


@dataclass(frozen=True, slots=True)
class OHLCVFeatureDefinition:
    """Approved, versioned Base OHLCV feature definition."""

    name: OHLCVFeatureName
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


type _Numeric = int | float | Decimal

_NUMERIC_TYPES = (int, float, Decimal)
_ROLLING_FEATURES = frozenset(
    {
        OHLCVFeatureName.ROLLING_VOLATILITY,
        OHLCVFeatureName.ROLLING_RANGE,
        OHLCVFeatureName.ATR,
        OHLCVFeatureName.VOLUME_ZSCORE,
        OHLCVFeatureName.ROLLING_VOLUME,
        OHLCVFeatureName.RANGE_POSITION,
        OHLCVFeatureName.TRENDINESS,
    }
)
_EXPANDING_FEATURES = frozenset(
    {
        OHLCVFeatureName.OPENING_RANGE,
        OHLCVFeatureName.OVERNIGHT_RANGE,
        OHLCVFeatureName.VWAP,
        OHLCVFeatureName.ANCHORED_VWAP,
        OHLCVFeatureName.DISTANCE_TO_VWAP,
    }
)
_SESSION_METADATA_INPUT_FIELDS = frozenset(
    {
        "session_label",
        "session_segment",
        "rth_flag",
        "eth_flag",
        "session_minute",
        "minutes_from_rth_open",
    }
)
_OHLCV_FIELDS_BY_FEATURE: dict[OHLCVFeatureName, tuple[str, ...]] = {
    OHLCVFeatureName.RETURNS: ("close",),
    OHLCVFeatureName.LOG_RETURNS: ("close",),
    OHLCVFeatureName.ROLLING_VOLATILITY: ("close",),
    OHLCVFeatureName.ROLLING_RANGE: ("high", "low"),
    OHLCVFeatureName.ATR: ("high", "low", "close"),
    OHLCVFeatureName.VOLUME_ZSCORE: ("volume",),
    OHLCVFeatureName.ROLLING_VOLUME: ("volume",),
    OHLCVFeatureName.SESSION_MINUTE: ("bar_start_ts", "session_label"),
    OHLCVFeatureName.RTH_FLAG: ("session_label",),
    OHLCVFeatureName.ETH_FLAG: ("session_label",),
    OHLCVFeatureName.OPENING_RANGE: ("bar_start_ts", "high", "low", "session_label"),
    OHLCVFeatureName.OVERNIGHT_RANGE: ("high", "low", "session_label"),
    OHLCVFeatureName.VWAP: ("high", "low", "close", "volume", "session_label"),
    OHLCVFeatureName.ANCHORED_VWAP: ("high", "low", "close", "volume", "session_label"),
    OHLCVFeatureName.DISTANCE_TO_VWAP: ("high", "low", "close", "volume", "session_label"),
    OHLCVFeatureName.RANGE_POSITION: ("high", "low", "close"),
    OHLCVFeatureName.TRENDINESS: ("close",),
}


def supported_ohlcv_features() -> tuple[OHLCVFeatureName, ...]:
    """Return the complete FLF-P08 Base OHLCV feature list."""

    return tuple(OHLCVFeatureName)


def build_ohlcv_feature_definition(
    name: OHLCVFeatureName | str,
    feature_request: FeatureRequest | Mapping[str, Any] | None,
    registry_reader: RegistryReader | object | None,
    *,
    dataset_version_ids: Sequence[str] = (),
    window_length: int = 3,
    horizon: int = 1,
    opening_range_minutes: int = 30,
    anchor_session_label: str | None = "RTH",
    reset_on_session: bool = True,
    ddof: int = 0,
    window: WindowSpec | None = None,
) -> OHLCVFeatureDefinition:
    """Build one approved Base OHLCV feature definition.

    The FLF-P05 request gate is the only admission path. Missing, invalid,
    unapproved, duplicate-blocked, or registry-unchecked requests fail closed.
    """

    feature_name = _coerce_feature_name(name)
    window_length = _positive_int(window_length, "window_length")
    horizon = _positive_int(horizon, "horizon")
    opening_range_minutes = _positive_int(opening_range_minutes, "opening_range_minutes")
    ddof = _non_negative_int(ddof, "ddof")
    if type(reset_on_session) is not bool:
        raise OHLCVFeatureError("reset_on_session must be a bool")

    gate_decision = require_feature_request_implementation_allowed(
        feature_request,
        registry_reader,
    )
    spec = _feature_spec(
        feature_name,
        gate_decision,
        dataset_version_ids=dataset_version_ids,
        window_length=window_length,
        horizon=horizon,
        opening_range_minutes=opening_range_minutes,
        anchor_session_label=anchor_session_label,
        reset_on_session=reset_on_session,
        ddof=ddof,
        window=window,
    )
    return OHLCVFeatureDefinition(
        name=feature_name,
        spec=spec,
        version=spec.derive_feature_version(),
        request_gate_decision=gate_decision,
    )


def build_ohlcv_feature_definitions(
    feature_requests: Mapping[OHLCVFeatureName | str, FeatureRequest | Mapping[str, Any]],
    registry_reader: RegistryReader | object | None,
    **parameters: Any,
) -> tuple[OHLCVFeatureDefinition, ...]:
    """Build multiple approved Base OHLCV feature definitions."""

    return tuple(
        build_ohlcv_feature_definition(name, request, registry_reader, **parameters)
        for name, request in feature_requests.items()
    )


def compute_ohlcv_feature(
    definition: OHLCVFeatureDefinition,
    input_view: OHLCVInputView | CanonicalInputViews,
) -> tuple[FeatureValueRecord, ...]:
    """Compute one Base OHLCV feature as in-memory value records.

    Values are returned only to the caller. This function does not materialize,
    persist, register, or write feature values.
    """

    definition = _require_definition(definition)
    rows = _validated_rows(_coerce_ohlcv_view(input_view).rows)
    if definition.name is OHLCVFeatureName.RETURNS:
        return _records_from_primitive_results(
            definition,
            rows,
            simple_returns(
                points_from_trade_rows(rows, "close"),
                _int_parameter(definition, "horizon"),
                reset_on_session=_bool_parameter(definition, "reset_on_session"),
            ),
        )
    if definition.name is OHLCVFeatureName.LOG_RETURNS:
        return _records_from_primitive_results(
            definition,
            rows,
            log_returns(
                points_from_trade_rows(rows, "close"),
                _int_parameter(definition, "horizon"),
                reset_on_session=_bool_parameter(definition, "reset_on_session"),
            ),
        )
    if definition.name is OHLCVFeatureName.ROLLING_VOLATILITY:
        return _records_from_primitive_results(
            definition,
            rows,
            rolling_volatility(
                _return_points(rows, definition),
                definition.spec.window,
                ddof=_int_parameter(definition, "ddof"),
                reset_on_session=_bool_parameter(definition, "reset_on_session"),
            ),
        )
    if definition.name is OHLCVFeatureName.ROLLING_RANGE:
        return _records_from_points(definition, _rolling_range_points(rows, definition))
    if definition.name is OHLCVFeatureName.ATR:
        return _records_from_primitive_results(
            definition,
            rows,
            average_true_range(
                bars_from_trade_rows(rows),
                definition.spec.window,
                reset_on_session=_bool_parameter(definition, "reset_on_session"),
            ),
        )
    if definition.name is OHLCVFeatureName.VOLUME_ZSCORE:
        return _records_from_primitive_results(
            definition,
            rows,
            causal_zscore(
                points_from_trade_rows(rows, "volume"),
                definition.spec.window,
                ddof=_int_parameter(definition, "ddof"),
                reset_on_session=_bool_parameter(definition, "reset_on_session"),
            ),
        )
    if definition.name is OHLCVFeatureName.ROLLING_VOLUME:
        return _records_from_points(definition, _rolling_volume_points(rows, definition))
    if definition.name is OHLCVFeatureName.SESSION_MINUTE:
        return _records_from_points(definition, _session_minute_points(rows))
    if definition.name is OHLCVFeatureName.RTH_FLAG:
        return _records_from_points(definition, _session_flag_points(rows, "RTH"))
    if definition.name is OHLCVFeatureName.ETH_FLAG:
        return _records_from_points(definition, _session_flag_points(rows, "ETH"))
    if definition.name is OHLCVFeatureName.OPENING_RANGE:
        return _records_from_points(definition, _opening_range_points(rows, definition))
    if definition.name is OHLCVFeatureName.OVERNIGHT_RANGE:
        return _records_from_points(definition, _overnight_range_points(rows))
    if definition.name is OHLCVFeatureName.VWAP:
        return _records_from_points(definition, _vwap_points(rows, session_reset=True))
    if definition.name is OHLCVFeatureName.ANCHORED_VWAP:
        return _records_from_points(definition, _anchored_vwap_points(rows, definition))
    if definition.name is OHLCVFeatureName.DISTANCE_TO_VWAP:
        return _records_from_points(definition, _distance_to_vwap_points(rows))
    if definition.name is OHLCVFeatureName.RANGE_POSITION:
        return _records_from_points(definition, _range_position_points(rows, definition))
    if definition.name is OHLCVFeatureName.TRENDINESS:
        return _records_from_points(definition, _trendiness_points(rows, definition))
    raise OHLCVFeatureError(f"unsupported OHLCV feature: {definition.name}")


def compute_ohlcv_features(
    definitions: Iterable[OHLCVFeatureDefinition],
    input_view: OHLCVInputView | CanonicalInputViews,
) -> dict[OHLCVFeatureName, tuple[FeatureValueRecord, ...]]:
    """Compute approved Base OHLCV definitions against one canonical OHLCV view."""

    return {
        definition.name: compute_ohlcv_feature(definition, input_view)
        for definition in definitions
    }


def _feature_spec(
    name: OHLCVFeatureName,
    gate_decision: FeatureRequestGateDecision,
    *,
    dataset_version_ids: Sequence[str],
    window_length: int,
    horizon: int,
    opening_range_minutes: int,
    anchor_session_label: str | None,
    reset_on_session: bool,
    ddof: int,
    window: WindowSpec | None,
) -> FeatureSpec:
    if gate_decision.feature_request_id is None:
        raise OHLCVFeatureError("approved FeatureRequestGateDecision must expose freq_ id")
    feature_window = window or _default_window(name, window_length=window_length, horizon=horizon)
    parameters = _transform_parameters(
        name,
        window_length=window_length,
        horizon=horizon,
        opening_range_minutes=opening_range_minutes,
        anchor_session_label=anchor_session_label,
        reset_on_session=reset_on_session,
        ddof=ddof,
    )
    input_fields = _input_fields(name)
    return FeatureSpec(
        feature_id=f"base_ohlcv_{name.value}",
        family=FeatureFamily.BASE_OHLCV,
        feature_request_id=gate_decision.feature_request_id,
        inputs=FeatureInputSpec(
            input_views=("canonical_ohlcv",),
            fields=input_fields,
            dataset_version_ids=tuple(dataset_version_ids),
            input_metadata=_input_metadata(input_fields),
        ),
        transform=TransformSpec(
            transform_id=_transform_id(name),
            parameters=parameters,
        ),
        window=feature_window,
        normalization=NormalizationSpec(
            normalization_id=(
                "causal_zscore" if name is OHLCVFeatureName.VOLUME_ZSCORE else "identity"
            ),
            parameters={"reset_on_session": reset_on_session}
            if name is OHLCVFeatureName.VOLUME_ZSCORE
            else {},
        ),
        availability_assumptions={
            "input": "canonical OHLCV rows are accepted-DatasetVersion input-view rows",
            "causality": "outputs use only source rows with available_ts <= output available_ts",
        },
        available_ts_derivation_rule=(
            "feature.available_ts = current input row available_ts; trailing and cumulative "
            "state may use only source rows whose available_ts is <= current row available_ts"
        ),
        live=True,
        implementation_eligible=True,
        contract_metadata={
            "campaign": "ALPHA_FEATURE_LABEL_FOUNDATION_V1",
            "phase": "FLF-P08",
            "materialization": "in_memory_records_only",
            "claims": "substrate_only_no_alpha_or_tradability_claim",
        },
        request_gate_decision=gate_decision,
    )


def _default_window(
    name: OHLCVFeatureName,
    *,
    window_length: int,
    horizon: int,
) -> WindowSpec:
    if name in _ROLLING_FEATURES:
        return WindowSpec(
            kind=WindowKind.ROLLING,
            length=window_length,
            causality=WindowCausality.CAUSAL,
            offline_only=False,
        )
    if name in {OHLCVFeatureName.RETURNS, OHLCVFeatureName.LOG_RETURNS}:
        return WindowSpec(
            kind=WindowKind.ROLLING,
            length=horizon,
            causality=WindowCausality.CAUSAL,
            offline_only=False,
        )
    if name in _EXPANDING_FEATURES:
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


def _transform_id(name: OHLCVFeatureName) -> str:
    return {
        OHLCVFeatureName.RETURNS: "return",
        OHLCVFeatureName.LOG_RETURNS: "log_return",
        OHLCVFeatureName.ROLLING_VOLATILITY: "rolling_volatility",
        OHLCVFeatureName.ROLLING_RANGE: "rolling_range",
        OHLCVFeatureName.ATR: "average_true_range",
        OHLCVFeatureName.VOLUME_ZSCORE: "identity",
        OHLCVFeatureName.ROLLING_VOLUME: "rolling_volume_sum",
        OHLCVFeatureName.SESSION_MINUTE: "session_minute",
        OHLCVFeatureName.RTH_FLAG: "rth_flag",
        OHLCVFeatureName.ETH_FLAG: "eth_flag",
        OHLCVFeatureName.OPENING_RANGE: "opening_range",
        OHLCVFeatureName.OVERNIGHT_RANGE: "overnight_range",
        OHLCVFeatureName.VWAP: "vwap",
        OHLCVFeatureName.ANCHORED_VWAP: "anchored_vwap",
        OHLCVFeatureName.DISTANCE_TO_VWAP: "distance_to_vwap",
        OHLCVFeatureName.RANGE_POSITION: "range_position",
        OHLCVFeatureName.TRENDINESS: "trendiness",
    }[name]


def _transform_parameters(
    name: OHLCVFeatureName,
    *,
    window_length: int,
    horizon: int,
    opening_range_minutes: int,
    anchor_session_label: str | None,
    reset_on_session: bool,
    ddof: int,
) -> dict[str, object]:
    parameters: dict[str, object] = {
        "feature_name": name.value,
        "reset_on_session": reset_on_session,
    }
    if name in _ROLLING_FEATURES:
        parameters["window_length"] = window_length
    if name in {
        OHLCVFeatureName.RETURNS,
        OHLCVFeatureName.LOG_RETURNS,
        OHLCVFeatureName.ROLLING_VOLATILITY,
    }:
        parameters["horizon"] = horizon
    if name in {OHLCVFeatureName.ROLLING_VOLATILITY, OHLCVFeatureName.VOLUME_ZSCORE}:
        parameters["ddof"] = ddof
    if name is OHLCVFeatureName.OPENING_RANGE:
        parameters["opening_range_minutes"] = opening_range_minutes
    if name is OHLCVFeatureName.ANCHORED_VWAP and anchor_session_label is not None:
        parameters["anchor_session_label"] = anchor_session_label.upper()
    return parameters


def _input_fields(name: OHLCVFeatureName) -> tuple[str, ...]:
    base = (
        "available_ts",
        "event_ts",
        "series_id",
        "quality_flags",
    )
    return tuple(dict.fromkeys((*base, *_OHLCV_FIELDS_BY_FEATURE[name])))


def _input_metadata(fields: Sequence[str]) -> dict[str, object]:
    metadata: dict[str, object] = {
        "consumption_surface": "alpha_system.features.input_views.OHLCVInputView",
        "trade_semantics": "FLF-P04 no_trade rows are gaps for trade logic",
    }
    field_roles = {
        field: "SESSION_METADATA"
        for field in sorted(set(fields).intersection(_SESSION_METADATA_INPUT_FIELDS))
    }
    if field_roles:
        metadata["field_roles"] = field_roles
    return metadata


def _coerce_ohlcv_view(input_view: OHLCVInputView | CanonicalInputViews) -> OHLCVInputView:
    if isinstance(input_view, CanonicalInputViews):
        return input_view.ohlcv
    if isinstance(input_view, OHLCVInputView):
        return input_view
    raise OHLCVFeatureError("Base OHLCV features require an OHLCVInputView")


def _validated_rows(rows: Sequence[OHLCVInputRow]) -> tuple[OHLCVInputRow, ...]:
    ordered = tuple(rows)
    for row in ordered:
        if not isinstance(row, OHLCVInputRow):
            raise OHLCVFeatureError("OHLCV feature inputs must be OHLCVInputRow objects")
        _require_aware_datetime(row.available_ts, "OHLCVInputRow.available_ts")
        _require_aware_datetime(row.event_ts, "OHLCVInputRow.event_ts")
        _require_aware_datetime(row.bar_start_ts, "OHLCVInputRow.bar_start_ts")
        for field in ("open", "high", "low", "close", "volume"):
            _to_float(getattr(row, field), f"OHLCVInputRow.{field}")
    return tuple(sorted(ordered, key=lambda row: row.available_ts))


def _require_definition(definition: OHLCVFeatureDefinition) -> OHLCVFeatureDefinition:
    if not isinstance(definition, OHLCVFeatureDefinition):
        raise OHLCVFeatureError("compute requires an OHLCVFeatureDefinition")
    if definition.spec.family is not FeatureFamily.BASE_OHLCV:
        raise OHLCVFeatureError("definition must belong to FeatureFamily.BASE_OHLCV")
    if not definition.spec.implementation_eligible:
        raise OHLCVFeatureError("definition is not implementation eligible")
    if not definition.request_gate_decision.implementation_allowed:
        raise OHLCVFeatureError("FeatureRequest gate did not admit implementation")
    if definition.version != definition.spec.derive_feature_version():
        raise OHLCVFeatureError("definition FeatureVersion does not match FeatureSpec")
    if not definition.spec.window.is_live_compatible:
        raise OHLCVFeatureError("Base OHLCV live features require causal windows")
    return definition


def _records_from_primitive_results(
    definition: OHLCVFeatureDefinition,
    rows: Sequence[OHLCVInputRow],
    results: Sequence[PrimitiveResult],
) -> tuple[FeatureValueRecord, ...]:
    if len(rows) != len(results):
        raise OHLCVFeatureError("primitive output length must match OHLCV row length")
    return tuple(
        _feature_value_record(
            definition,
            row,
            value=result.value,
            quality_flags=result.quality_flags,
        )
        for row, result in zip(rows, results, strict=True)
    )


def _records_from_points(
    definition: OHLCVFeatureDefinition,
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
    definition: OHLCVFeatureDefinition,
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


def _return_points(
    rows: Sequence[OHLCVInputRow],
    definition: OHLCVFeatureDefinition,
) -> tuple[PrimitivePoint, ...]:
    returns = simple_returns(
        points_from_trade_rows(rows, "close"),
        _int_parameter(definition, "horizon"),
        reset_on_session=_bool_parameter(definition, "reset_on_session"),
    )
    return tuple(
        PrimitivePoint(
            available_ts=result.available_ts,
            value=result.value,
            session_label=result.session_label,
            quality_flags=result.quality_flags,
        )
        for result in returns
    )


def _rolling_range_points(
    rows: Sequence[OHLCVInputRow],
    definition: OHLCVFeatureDefinition,
) -> tuple[_FeaturePoint, ...]:
    return _rolling_reduce_rows(
        rows,
        definition,
        reducer=lambda window_rows: max(_to_float(row.high, "high") for row in window_rows)
        - min(_to_float(row.low, "low") for row in window_rows),
    )


def _rolling_volume_points(
    rows: Sequence[OHLCVInputRow],
    definition: OHLCVFeatureDefinition,
) -> tuple[_FeaturePoint, ...]:
    return _rolling_reduce_rows(
        rows,
        definition,
        reducer=lambda window_rows: sum(_to_float(row.volume, "volume") for row in window_rows),
    )


def _range_position_points(
    rows: Sequence[OHLCVInputRow],
    definition: OHLCVFeatureDefinition,
) -> tuple[_FeaturePoint, ...]:
    def reducer(window_rows: Sequence[OHLCVInputRow]) -> float | None:
        low = min(_to_float(row.low, "low") for row in window_rows)
        high = max(_to_float(row.high, "high") for row in window_rows)
        if high == low:
            return None
        return (_to_float(window_rows[-1].close, "close") - low) / (high - low)

    return _rolling_reduce_rows(rows, definition, reducer=reducer, null_reason="zero_range")


def _trendiness_points(
    rows: Sequence[OHLCVInputRow],
    definition: OHLCVFeatureDefinition,
) -> tuple[_FeaturePoint, ...]:
    def reducer(window_rows: Sequence[OHLCVInputRow]) -> float | None:
        closes = [_to_float(row.close, "close") for row in window_rows]
        denominator = sum(abs(closes[index] - closes[index - 1]) for index in range(1, len(closes)))
        if denominator == 0:
            return None
        return abs(closes[-1] - closes[0]) / denominator

    return _rolling_reduce_rows(rows, definition, reducer=reducer, null_reason="zero_movement")


def _rolling_reduce_rows(
    rows: Sequence[OHLCVInputRow],
    definition: OHLCVFeatureDefinition,
    *,
    reducer: Any,
    null_reason: str = "undefined",
) -> tuple[_FeaturePoint, ...]:
    window_length = definition.spec.window.length
    reset_on_session = _bool_parameter(definition, "reset_on_session")
    results: list[_FeaturePoint] = []
    for index, row in enumerate(rows):
        start = _window_start(rows, index, window_length, reset_on_session=reset_on_session)
        window_rows = rows[start : index + 1]
        if len(window_rows) < window_length:
            results.append(_gap_feature_point(row, "insufficient_window"))
            continue
        gap_flags = _window_gap_flags(window_rows)
        if gap_flags:
            results.append(_gap_feature_point(row, "input_gap", gap_flags))
            continue
        value = reducer(window_rows)
        if value is None:
            results.append(_gap_feature_point(row, null_reason))
            continue
        results.append(_FeaturePoint(row=row, value=value))
    return tuple(results)


def _window_start(
    rows: Sequence[OHLCVInputRow],
    index: int,
    window_length: int,
    *,
    reset_on_session: bool,
) -> int:
    start = max(0, index - window_length + 1)
    if not reset_on_session:
        return start
    current_session = rows[index].session_label
    for prior_index in range(index - 1, start - 1, -1):
        if rows[prior_index].session_label != current_session:
            return prior_index + 1
    return start


def _session_minute_points(rows: Sequence[OHLCVInputRow]) -> tuple[_FeaturePoint, ...]:
    results: list[_FeaturePoint] = []
    segment_start: datetime | None = None
    previous_session = object()
    for row in rows:
        session_key = (row.series_id, row.session_label)
        if session_key != previous_session:
            segment_start = row.bar_start_ts
            previous_session = session_key
        assert segment_start is not None
        elapsed = int((row.bar_start_ts - segment_start).total_seconds() // 60)
        if elapsed < 0:
            results.append(_gap_feature_point(row, "negative_session_elapsed"))
            continue
        results.append(_FeaturePoint(row=row, value=elapsed))
    return tuple(results)


def _session_flag_points(
    rows: Sequence[OHLCVInputRow],
    session_label: str,
) -> tuple[_FeaturePoint, ...]:
    normalized = session_label.upper()
    return tuple(
        _FeaturePoint(row=row, value=1 if row.session_label.upper() == normalized else 0)
        for row in rows
    )


def _opening_range_points(
    rows: Sequence[OHLCVInputRow],
    definition: OHLCVFeatureDefinition,
) -> tuple[_FeaturePoint, ...]:
    opening_minutes = _int_parameter(definition, "opening_range_minutes")
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
        if row.session_label.upper() != "RTH":
            results.append(_gap_feature_point(row, "outside_rth"))
            continue
        assert session_start is not None
        in_window = row.bar_start_ts < session_start + timedelta(minutes=opening_minutes)
        if in_window and _is_trade_row(row):
            row_high = _to_float(row.high, "high")
            row_low = _to_float(row.low, "low")
            opening_high = row_high if opening_high is None else max(opening_high, row_high)
            opening_low = row_low if opening_low is None else min(opening_low, row_low)
        if opening_high is None or opening_low is None:
            results.append(_gap_feature_point(row, "no_opening_trade", row.quality_flags))
            continue
        results.append(_FeaturePoint(row=row, value=opening_high - opening_low))
    return tuple(results)


def _overnight_range_points(rows: Sequence[OHLCVInputRow]) -> tuple[_FeaturePoint, ...]:
    eth_high: float | None = None
    eth_low: float | None = None
    frozen_overnight_range: float | None = None
    previous_session: str | None = None
    results: list[_FeaturePoint] = []
    for row in rows:
        session = row.session_label.upper()
        if session != previous_session and session == "ETH":
            eth_high = None
            eth_low = None
            frozen_overnight_range = None
        if session != previous_session and previous_session == "ETH":
            frozen_overnight_range = (
                None if eth_high is None or eth_low is None else eth_high - eth_low
            )
        previous_session = session

        if session == "ETH":
            if _is_trade_row(row):
                row_high = _to_float(row.high, "high")
                row_low = _to_float(row.low, "low")
                eth_high = row_high if eth_high is None else max(eth_high, row_high)
                eth_low = row_low if eth_low is None else min(eth_low, row_low)
            if eth_high is None or eth_low is None:
                results.append(_gap_feature_point(row, "no_overnight_trade", row.quality_flags))
            else:
                results.append(_FeaturePoint(row=row, value=eth_high - eth_low))
            continue

        if session == "RTH" and frozen_overnight_range is not None:
            results.append(_FeaturePoint(row=row, value=frozen_overnight_range))
        else:
            results.append(_gap_feature_point(row, "no_overnight_range", row.quality_flags))
    return tuple(results)


def _vwap_points(
    rows: Sequence[OHLCVInputRow],
    *,
    session_reset: bool,
) -> tuple[_FeaturePoint, ...]:
    cumulative_price_volume = 0.0
    cumulative_volume = 0.0
    previous_session: tuple[str, str] | None = None
    results: list[_FeaturePoint] = []
    for row in rows:
        session_key = (row.series_id, row.session_label)
        if session_reset and session_key != previous_session:
            cumulative_price_volume = 0.0
            cumulative_volume = 0.0
        previous_session = session_key
        if not _is_trade_row(row):
            results.append(_gap_feature_point(row, "no_trade", row.quality_flags))
            continue
        volume = _to_float(row.volume, "volume")
        if volume <= 0:
            results.append(_gap_feature_point(row, "zero_volume", row.quality_flags))
            continue
        cumulative_price_volume += _typical_price(row) * volume
        cumulative_volume += volume
        results.append(_FeaturePoint(row=row, value=cumulative_price_volume / cumulative_volume))
    return tuple(results)


def _anchored_vwap_points(
    rows: Sequence[OHLCVInputRow],
    definition: OHLCVFeatureDefinition,
) -> tuple[_FeaturePoint, ...]:
    parameters = definition.spec.transform.parameters.to_dict()
    anchor = parameters.get("anchor_session_label")
    anchor_session_label = str(anchor).upper() if anchor is not None else None
    cumulative_price_volume = 0.0
    cumulative_volume = 0.0
    active = anchor_session_label is None
    previous_session: tuple[str, str] | None = None
    results: list[_FeaturePoint] = []
    for row in rows:
        session_key = (row.series_id, row.session_label)
        if session_key != previous_session and (
            anchor_session_label is None or row.session_label.upper() == anchor_session_label
        ):
            active = True
            cumulative_price_volume = 0.0
            cumulative_volume = 0.0
        previous_session = session_key
        if not active:
            results.append(_gap_feature_point(row, "before_anchor"))
            continue
        if not _is_trade_row(row):
            results.append(_gap_feature_point(row, "no_trade", row.quality_flags))
            continue
        volume = _to_float(row.volume, "volume")
        if volume <= 0:
            results.append(_gap_feature_point(row, "zero_volume", row.quality_flags))
            continue
        cumulative_price_volume += _typical_price(row) * volume
        cumulative_volume += volume
        results.append(_FeaturePoint(row=row, value=cumulative_price_volume / cumulative_volume))
    return tuple(results)


def _distance_to_vwap_points(rows: Sequence[OHLCVInputRow]) -> tuple[_FeaturePoint, ...]:
    vwap_points = _vwap_points(rows, session_reset=True)
    results: list[_FeaturePoint] = []
    for point in vwap_points:
        if point.value is None:
            results.append(point)
            continue
        if point.value == 0:
            results.append(_gap_feature_point(point.row, "zero_vwap"))
            continue
        close = _to_float(point.row.close, "close")
        results.append(_FeaturePoint(row=point.row, value=(close - point.value) / point.value))
    return tuple(results)


def _window_gap_flags(rows: Sequence[OHLCVInputRow]) -> tuple[str, ...]:
    flags: set[str] = set()
    for row in rows:
        if not _is_trade_row(row):
            flags.add("no_trade")
            flags.update(_quality_flags(row.quality_flags))
    return tuple(sorted(flags))


def _gap_feature_point(
    row: OHLCVInputRow,
    reason: str,
    extra_flags: Sequence[str] = (),
) -> _FeaturePoint:
    return _FeaturePoint(
        row=row,
        value=None,
        quality_flags=tuple(sorted({"ohlcv_gap", reason, *_quality_flags(extra_flags)})),
    )


def _is_trade_row(row: OHLCVInputRow) -> bool:
    return is_real_trade_bar(row)


def _typical_price(row: OHLCVInputRow) -> float:
    return (
        _to_float(row.high, "high") + _to_float(row.low, "low") + _to_float(row.close, "close")
    ) / 3.0


def _int_parameter(definition: OHLCVFeatureDefinition, name: str) -> int:
    value = definition.spec.transform.parameters.to_dict().get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise OHLCVFeatureError(f"{name} parameter must be an integer")
    return value


def _bool_parameter(definition: OHLCVFeatureDefinition, name: str) -> bool:
    value = definition.spec.transform.parameters.to_dict().get(name)
    if type(value) is not bool:
        raise OHLCVFeatureError(f"{name} parameter must be a bool")
    return value


def _coerce_feature_name(name: OHLCVFeatureName | str) -> OHLCVFeatureName:
    try:
        return OHLCVFeatureName(name)
    except ValueError as exc:
        raise OHLCVFeatureError(f"unsupported Base OHLCV feature: {name}") from exc


def _positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise OHLCVFeatureError(f"{field_name} must be a positive integer")
    return value


def _non_negative_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise OHLCVFeatureError(f"{field_name} must be a non-negative integer")
    return value


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise OHLCVFeatureError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise OHLCVFeatureError(f"{field_name} must be timezone-aware")
    return value


def _to_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, _NUMERIC_TYPES):
        raise OHLCVFeatureError(f"{field_name} must be numeric")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise OHLCVFeatureError(f"{field_name} must be finite")
    return parsed


def _quality_flags(flags: Sequence[str]) -> tuple[str, ...]:
    if isinstance(flags, str) or not isinstance(flags, Sequence):
        raise OHLCVFeatureError("quality_flags must be a sequence of strings")
    normalized: list[str] = []
    for flag in flags:
        if not isinstance(flag, str) or not flag.strip():
            raise OHLCVFeatureError("quality_flags must contain non-empty strings")
        token = flag.strip().lower()
        if token not in normalized:
            normalized.append(token)
    return tuple(normalized)


__all__ = [
    "OHLCVFeatureDefinition",
    "OHLCVFeatureError",
    "OHLCVFeatureName",
    "build_ohlcv_feature_definition",
    "build_ohlcv_feature_definitions",
    "compute_ohlcv_feature",
    "compute_ohlcv_features",
    "supported_ohlcv_features",
]
