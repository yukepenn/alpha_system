"""Volume / activity Polars pack for the V1 fast path."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from alpha_system.data.storage import require_dependency
from alpha_system.features.contracts import (
    FeatureFamily,
    FeatureSetSpec,
    FeatureSpec,
    WindowKind,
)
from alpha_system.features.families.ohlcv import OHLCVFeatureName
from alpha_system.features.families.structure import StructureFeatureName
from alpha_system.features.fast.materializer import (
    FastFeatureDeclaration,
    FastFeaturePack,
    PackMaterializerError,
    constant_window_mask,
)

VOLUME_ACTIVITY_WINDOW_LENGTH = 20
VOLUME_ACTIVITY_HORIZON = 1
VOLUME_ACTIVITY_DDOF = 0
VOLUME_ACTIVITY_RESET_ON_SESSION = True
VOLUME_ACTIVITY_FEATURE_IDS: tuple[str, ...] = (
    "base_ohlcv_rolling_volume",
    "base_ohlcv_volume_zscore",
    "base_ohlcv_session_minute",
    "base_ohlcv_rolling_range",
    "base_ohlcv_range_position",
    "base_ohlcv_trendiness",
    "liquidity_structure_close_location_value",
    "liquidity_structure_wick_rejection_score",
)

_OHLCV_FEATURE_ID_TO_NAME: dict[str, OHLCVFeatureName] = {
    "base_ohlcv_rolling_volume": OHLCVFeatureName.ROLLING_VOLUME,
    "base_ohlcv_volume_zscore": OHLCVFeatureName.VOLUME_ZSCORE,
    "base_ohlcv_session_minute": OHLCVFeatureName.SESSION_MINUTE,
    "base_ohlcv_rolling_range": OHLCVFeatureName.ROLLING_RANGE,
    "base_ohlcv_range_position": OHLCVFeatureName.RANGE_POSITION,
    "base_ohlcv_trendiness": OHLCVFeatureName.TRENDINESS,
}
_STRUCTURE_FEATURE_ID_TO_NAME: dict[str, StructureFeatureName] = {
    "liquidity_structure_close_location_value": StructureFeatureName.CLOSE_LOCATION_VALUE,
    "liquidity_structure_wick_rejection_score": StructureFeatureName.WICK_REJECTION_SCORE,
}
_ROLLING_OHLCV_FEATURES = frozenset(
    {
        OHLCVFeatureName.ROLLING_VOLUME,
        OHLCVFeatureName.VOLUME_ZSCORE,
        OHLCVFeatureName.ROLLING_RANGE,
        OHLCVFeatureName.RANGE_POSITION,
        OHLCVFeatureName.TRENDINESS,
    }
)
_GAP_QUALITY_FLAGS = (
    "missing_bbo",
    "bbo_quarantined",
    "no_trade",
    "primitive_gap",
    "input_gap",
)

_PREFIX = "__fva"
_SERIES = f"{_PREFIX}_series_id"
_SESSION = f"{_PREFIX}_session_label"
_SEGMENT_START = f"{_PREFIX}_segment_start"
_SEGMENT = f"{_PREFIX}_segment"
_SEGMENT_START_TS = f"{_PREFIX}_segment_start_ts"
_BAR_START = f"{_PREFIX}_bar_start_ts"
_INPUT_FLAGS = f"{_PREFIX}_input_quality_flags"
_OPEN = f"{_PREFIX}_open"
_HIGH = f"{_PREFIX}_high"
_LOW = f"{_PREFIX}_low"
_CLOSE = f"{_PREFIX}_close"
_VOLUME = f"{_PREFIX}_volume"
_BAR_RANGE = f"{_PREFIX}_bar_range"
_NO_TRADE = f"{_PREFIX}_no_trade"


@dataclass(frozen=True, slots=True)
class _PackExpression:
    value: Any
    flags: Any


def build_volume_activity_pack(feature_set: FeatureSetSpec) -> FastFeaturePack:
    """Build the governed volume / activity fast pack."""

    if not isinstance(feature_set, FeatureSetSpec):
        raise PackMaterializerError("volume_activity fast pack requires a FeatureSetSpec")
    _validate_volume_activity_feature_set(feature_set)
    polars = require_dependency("polars")
    expressions = _volume_activity_expressions(polars, feature_set.features)
    return FastFeaturePack(
        feature_set=feature_set,
        declarations=tuple(
            FastFeatureDeclaration(
                feature_spec=feature,
                value_expr=expressions[feature.feature_id].value,
                quality_flags_expr=expressions[feature.feature_id].flags,
            )
            for feature in feature_set.features
        ),
        prepare_frame=_prepare_frame,
    )


def supports_volume_activity_pack(feature_set: FeatureSetSpec) -> bool:
    """Return true when a feature set is exactly the governed volume/activity pack."""

    if not isinstance(feature_set, FeatureSetSpec):
        return False
    try:
        _validate_volume_activity_feature_set(feature_set)
    except PackMaterializerError:
        return False
    return True


def _validate_volume_activity_feature_set(feature_set: FeatureSetSpec) -> None:
    features = tuple(feature_set.features)
    feature_ids = tuple(feature.feature_id for feature in features)
    if set(feature_ids) != set(VOLUME_ACTIVITY_FEATURE_IDS) or len(feature_ids) != len(
        VOLUME_ACTIVITY_FEATURE_IDS
    ):
        raise PackMaterializerError(
            "volume_activity fast pack requires exactly the governed volume/activity "
            "primitive bindings"
        )
    for feature in features:
        _validate_volume_activity_feature(feature)


def _validate_volume_activity_feature(feature: FeatureSpec) -> None:
    if not isinstance(feature, FeatureSpec):
        raise PackMaterializerError("volume_activity pack entries must be FeatureSpec objects")
    if feature.feature_id in _OHLCV_FEATURE_ID_TO_NAME:
        _validate_ohlcv_feature(feature)
        return
    if feature.feature_id in _STRUCTURE_FEATURE_ID_TO_NAME:
        _validate_structure_feature(feature)
        return
    raise PackMaterializerError(f"unsupported volume_activity feature_id: {feature.feature_id}")


def _validate_ohlcv_feature(feature: FeatureSpec) -> None:
    if feature.family is not FeatureFamily.BASE_OHLCV:
        raise PackMaterializerError("volume_activity OHLCV bindings must be Base OHLCV features")
    feature_name = _OHLCV_FEATURE_ID_TO_NAME[feature.feature_id]
    parameters = feature.transform.parameters.to_dict()
    _require_parameter(parameters, "feature_name", feature_name.value, feature.feature_id)
    _require_parameter(
        parameters,
        "reset_on_session",
        VOLUME_ACTIVITY_RESET_ON_SESSION,
        feature.feature_id,
    )
    if feature_name in _ROLLING_OHLCV_FEATURES:
        _require_rolling_window(feature, length=VOLUME_ACTIVITY_WINDOW_LENGTH)
        _require_parameter(
            parameters,
            "window_length",
            VOLUME_ACTIVITY_WINDOW_LENGTH,
            feature.feature_id,
        )
    if feature_name is OHLCVFeatureName.SESSION_MINUTE:
        _require_point_in_time_window(feature)
    if feature_name is OHLCVFeatureName.VOLUME_ZSCORE:
        _require_parameter(parameters, "ddof", VOLUME_ACTIVITY_DDOF, feature.feature_id)
        _require_parameter(
            feature.normalization.parameters.to_dict(),
            "reset_on_session",
            VOLUME_ACTIVITY_RESET_ON_SESSION,
            feature.feature_id,
        )
    expected_transform = {
        OHLCVFeatureName.ROLLING_VOLUME: "rolling_volume_sum",
        OHLCVFeatureName.VOLUME_ZSCORE: "identity",
        OHLCVFeatureName.SESSION_MINUTE: "session_minute",
        OHLCVFeatureName.ROLLING_RANGE: "rolling_range",
        OHLCVFeatureName.RANGE_POSITION: "range_position",
        OHLCVFeatureName.TRENDINESS: "trendiness",
    }[feature_name]
    if feature.transform.transform_id != expected_transform:
        raise PackMaterializerError(
            f"{feature.feature_id} transform must be {expected_transform}"
        )
    expected_normalization = (
        "causal_zscore" if feature_name is OHLCVFeatureName.VOLUME_ZSCORE else "identity"
    )
    if feature.normalization.normalization_id != expected_normalization:
        raise PackMaterializerError(
            f"{feature.feature_id} normalization must be {expected_normalization}"
        )


def _validate_structure_feature(feature: FeatureSpec) -> None:
    if feature.family is not FeatureFamily.LIQUIDITY_STRUCTURE:
        raise PackMaterializerError(
            "volume_activity structure bindings must be Liquidity Structure features"
        )
    feature_name = _STRUCTURE_FEATURE_ID_TO_NAME[feature.feature_id]
    parameters = feature.transform.parameters.to_dict()
    _require_parameter(parameters, "feature_name", feature_name.value, feature.feature_id)
    _require_parameter(
        parameters,
        "reset_on_session",
        VOLUME_ACTIVITY_RESET_ON_SESSION,
        feature.feature_id,
    )
    _require_point_in_time_window(feature)
    if feature.transform.transform_id != feature_name.value:
        raise PackMaterializerError(
            f"{feature.feature_id} transform must be {feature_name.value}"
        )
    if feature.normalization.normalization_id != "identity":
        raise PackMaterializerError(f"{feature.feature_id} normalization must be identity")


def _require_parameter(
    parameters: Mapping[str, object],
    name: str,
    expected: object,
    feature_id: str,
) -> None:
    if parameters.get(name) != expected:
        raise PackMaterializerError(f"{feature_id} requires {name}={expected!r}")


def _require_rolling_window(feature: FeatureSpec, *, length: int) -> None:
    if feature.window.kind is not WindowKind.ROLLING or feature.window.length != length:
        raise PackMaterializerError(
            f"{feature.feature_id} requires a causal rolling window of length {length}"
        )
    if not feature.window.is_live_compatible:
        raise PackMaterializerError(f"{feature.feature_id} requires a live-compatible window")


def _require_point_in_time_window(feature: FeatureSpec) -> None:
    if feature.window.kind is not WindowKind.POINT_IN_TIME or feature.window.length != 1:
        raise PackMaterializerError(f"{feature.feature_id} requires a point-in-time window")
    if not feature.window.is_live_compatible:
        raise PackMaterializerError(f"{feature.feature_id} requires a live-compatible window")


def _volume_activity_expressions(
    polars: Any,
    features: Sequence[FeatureSpec],
) -> dict[str, _PackExpression]:
    expressions: dict[str, _PackExpression] = {}
    for feature in features:
        if feature.feature_id in _OHLCV_FEATURE_ID_TO_NAME:
            feature_name = _OHLCV_FEATURE_ID_TO_NAME[feature.feature_id]
            expressions[feature.feature_id] = _ohlcv_expression(polars, feature_name)
        elif feature.feature_id in _STRUCTURE_FEATURE_ID_TO_NAME:
            feature_name = _STRUCTURE_FEATURE_ID_TO_NAME[feature.feature_id]
            expressions[feature.feature_id] = _wick_expression(polars, feature_name)
        else:
            raise PackMaterializerError(
                f"unsupported volume_activity feature_id: {feature.feature_id}"
            )
    return expressions


def _prepare_frame(frame: Any) -> Any:
    pl = require_dependency("polars")
    _require_columns(
        frame,
        (
            "series_id",
            "bar_start_ts",
            "session_label",
            "quality_flags",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ),
    )
    prepared = frame.with_columns(
        (
            pl.col("series_id").cast(pl.Utf8).alias(_SERIES),
            pl.col("session_label").cast(pl.Utf8).alias(_SESSION),
            _bar_start_ts(pl).alias(_BAR_START),
            _input_quality_flags(pl).alias(_INPUT_FLAGS),
            pl.col("open").cast(pl.Float64, strict=False).alias(_OPEN),
            pl.col("high").cast(pl.Float64, strict=False).alias(_HIGH),
            pl.col("low").cast(pl.Float64, strict=False).alias(_LOW),
            pl.col("close").cast(pl.Float64, strict=False).alias(_CLOSE),
            pl.col("volume").cast(pl.Float64, strict=False).alias(_VOLUME),
        )
    )
    prepared = prepared.with_columns(
        (
            pl.col(_INPUT_FLAGS).list.contains("no_trade").fill_null(False).alias(_NO_TRADE),
            (pl.col(_HIGH) - pl.col(_LOW)).alias(_BAR_RANGE),
        )
    )
    segment_start = (
        (pl.col(_SERIES) != pl.col(_SERIES).shift(1))
        | (pl.col(_SESSION) != pl.col(_SESSION).shift(1))
    ).fill_null(True)
    return (
        prepared.with_columns(segment_start.alias(_SEGMENT_START))
        .with_columns(pl.col(_SEGMENT_START).cast(pl.Int64).cum_sum().alias(_SEGMENT))
        .with_columns(pl.col(_BAR_START).first().over(_SEGMENT).alias(_SEGMENT_START_TS))
    )


def _ohlcv_expression(polars: Any, feature_name: OHLCVFeatureName) -> _PackExpression:
    if feature_name is OHLCVFeatureName.ROLLING_VOLUME:
        return _rolling_volume_expression(polars)
    if feature_name is OHLCVFeatureName.VOLUME_ZSCORE:
        return _volume_zscore_expression(polars)
    if feature_name is OHLCVFeatureName.SESSION_MINUTE:
        return _session_minute_expression(polars)
    if feature_name is OHLCVFeatureName.ROLLING_RANGE:
        return _rolling_range_expression(polars)
    if feature_name is OHLCVFeatureName.RANGE_POSITION:
        return _range_position_expression(polars)
    if feature_name is OHLCVFeatureName.TRENDINESS:
        return _trendiness_expression(polars)
    raise PackMaterializerError(f"unsupported volume_activity OHLCV feature: {feature_name}")


def _rolling_volume_expression(polars: Any) -> _PackExpression:
    pl = polars
    window = VOLUME_ACTIVITY_WINDOW_LENGTH
    group_position = _group_position(pl)
    rolling_no_trade_count = _rolling_true_count(pl.col(_NO_TRADE), window, polars=pl)
    rolling_flag_counts = _ohlcv_no_trade_flag_counts(pl, window)
    insufficient = group_position < window
    value = (
        pl.when(insufficient | (rolling_no_trade_count > 0))
        .then(None)
        .otherwise(
            pl.col(_VOLUME)
            .rolling_sum(window_size=window, min_samples=window)
            .over(_SEGMENT)
        )
    )
    return _PackExpression(
        value,
        _ohlcv_rolling_flags(
            pl,
            insufficient=insufficient,
            rolling_no_trade_count=rolling_no_trade_count,
            rolling_flag_counts=rolling_flag_counts,
        ),
    )


def _volume_zscore_expression(polars: Any) -> _PackExpression:
    pl = polars
    window = VOLUME_ACTIVITY_WINDOW_LENGTH
    group_position = _group_position(pl)
    point_gap = _contains_any_flag(pl, _GAP_QUALITY_FLAGS)
    rolling_gap_count = _rolling_true_count(point_gap, window, polars=pl)
    partial_flag_counts = {
        flag: _cumulative_true_count(_point_has_flag(pl, flag), polars=pl)
        for flag in _GAP_QUALITY_FLAGS
    }
    rolling_flag_counts = {
        flag: _rolling_true_count(_point_has_flag(pl, flag), window, polars=pl)
        for flag in _GAP_QUALITY_FLAGS
    }
    mean = pl.col(_VOLUME).rolling_mean(window_size=window, min_samples=window).over(_SEGMENT)
    std = (
        pl.col(_VOLUME)
        .rolling_std(
            window_size=window,
            min_samples=window,
            ddof=VOLUME_ACTIVITY_DDOF,
        )
        .over(_SEGMENT)
    )
    insufficient = group_position < window
    # Robust zero-variance detection (constant window) -- see constant_window_mask.
    zero_variance = constant_window_mask(
        pl.col(_VOLUME), window=window, group=_SEGMENT
    ).fill_null(False)
    value = (
        pl.when(insufficient | (rolling_gap_count > 0) | zero_variance)
        .then(None)
        .otherwise((pl.col(_VOLUME) - mean) / std)
    )
    flags = (
        pl.when(insufficient)
        .then(
            _primitive_gap_flags(
                pl,
                ("insufficient_window",),
                flag_counts=partial_flag_counts,
            )
        )
        .when(rolling_gap_count > 0)
        .then(
            _primitive_gap_flags(
                pl,
                ("input_gap",),
                flag_counts=rolling_flag_counts,
            )
        )
        .when(zero_variance)
        .then(
            _primitive_gap_flags(
                pl,
                ("zero_variance",),
                flag_counts=rolling_flag_counts,
            )
        )
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _session_minute_expression(polars: Any) -> _PackExpression:
    pl = polars
    elapsed = (pl.col(_BAR_START) - pl.col(_SEGMENT_START_TS)).dt.total_minutes().cast(pl.Int64)
    negative = elapsed < 0
    value = pl.when(negative).then(None).otherwise(elapsed)
    flags = (
        pl.when(negative)
        .then(_ohlcv_flags(pl, ("negative_session_elapsed",)))
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _rolling_range_expression(polars: Any) -> _PackExpression:
    pl = polars
    window = VOLUME_ACTIVITY_WINDOW_LENGTH
    group_position = _group_position(pl)
    rolling_no_trade_count = _rolling_true_count(pl.col(_NO_TRADE), window, polars=pl)
    rolling_flag_counts = _ohlcv_no_trade_flag_counts(pl, window)
    insufficient = group_position < window
    raw_value = (
        pl.col(_HIGH).rolling_max(window_size=window, min_samples=window).over(_SEGMENT)
        - pl.col(_LOW).rolling_min(window_size=window, min_samples=window).over(_SEGMENT)
    )
    value = pl.when(insufficient | (rolling_no_trade_count > 0)).then(None).otherwise(raw_value)
    return _PackExpression(
        value,
        _ohlcv_rolling_flags(
            pl,
            insufficient=insufficient,
            rolling_no_trade_count=rolling_no_trade_count,
            rolling_flag_counts=rolling_flag_counts,
        ),
    )


def _range_position_expression(polars: Any) -> _PackExpression:
    pl = polars
    window = VOLUME_ACTIVITY_WINDOW_LENGTH
    group_position = _group_position(pl)
    rolling_no_trade_count = _rolling_true_count(pl.col(_NO_TRADE), window, polars=pl)
    rolling_flag_counts = _ohlcv_no_trade_flag_counts(pl, window)
    insufficient = group_position < window
    rolling_low = pl.col(_LOW).rolling_min(window_size=window, min_samples=window).over(_SEGMENT)
    rolling_high = pl.col(_HIGH).rolling_max(window_size=window, min_samples=window).over(_SEGMENT)
    range_ = rolling_high - rolling_low
    zero_range = range_ == 0.0
    value = (
        pl.when(insufficient | (rolling_no_trade_count > 0) | zero_range)
        .then(None)
        .otherwise((pl.col(_CLOSE) - rolling_low) / range_)
    )
    flags = (
        pl.when(insufficient)
        .then(_ohlcv_flags(pl, ("insufficient_window",)))
        .when(rolling_no_trade_count > 0)
        .then(
            _ohlcv_window_gap_flags(
                pl,
                rolling_no_trade_count=rolling_no_trade_count,
                rolling_flag_counts=rolling_flag_counts,
            )
        )
        .when(zero_range)
        .then(_ohlcv_flags(pl, ("zero_range",)))
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _trendiness_expression(polars: Any) -> _PackExpression:
    pl = polars
    window = VOLUME_ACTIVITY_WINDOW_LENGTH
    group_position = _group_position(pl)
    rolling_no_trade_count = _rolling_true_count(pl.col(_NO_TRADE), window, polars=pl)
    rolling_flag_counts = _ohlcv_no_trade_flag_counts(pl, window)
    insufficient = group_position < window
    close_diff = (pl.col(_CLOSE) - pl.col(_CLOSE).shift(1).over(_SEGMENT)).abs()
    denominator = close_diff.rolling_sum(window_size=window - 1, min_samples=window - 1).over(
        _SEGMENT
    )
    numerator = (pl.col(_CLOSE) - pl.col(_CLOSE).shift(window - 1).over(_SEGMENT)).abs()
    zero_movement = denominator == 0.0
    value = (
        pl.when(insufficient | (rolling_no_trade_count > 0) | zero_movement)
        .then(None)
        .otherwise(numerator / denominator)
    )
    flags = (
        pl.when(insufficient)
        .then(_ohlcv_flags(pl, ("insufficient_window",)))
        .when(rolling_no_trade_count > 0)
        .then(
            _ohlcv_window_gap_flags(
                pl,
                rolling_no_trade_count=rolling_no_trade_count,
                rolling_flag_counts=rolling_flag_counts,
            )
        )
        .when(zero_movement)
        .then(_ohlcv_flags(pl, ("zero_movement",)))
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _wick_expression(polars: Any, feature_name: StructureFeatureName) -> _PackExpression:
    pl = polars
    zero_range = pl.col(_BAR_RANGE) <= 0.0
    body_high = pl.max_horizontal(pl.col(_OPEN), pl.col(_CLOSE))
    body_low = pl.min_horizontal(pl.col(_OPEN), pl.col(_CLOSE))
    if feature_name is StructureFeatureName.CLOSE_LOCATION_VALUE:
        raw_value = (pl.col(_CLOSE) - pl.col(_LOW)) / pl.col(_BAR_RANGE)
    elif feature_name is StructureFeatureName.WICK_REJECTION_SCORE:
        upper_wick = pl.col(_HIGH) - body_high
        lower_wick = body_low - pl.col(_LOW)
        raw_value = (lower_wick - upper_wick) / pl.col(_BAR_RANGE)
    else:
        raise PackMaterializerError(
            f"unsupported volume_activity structure feature: {feature_name}"
        )
    value = pl.when(pl.col(_NO_TRADE) | zero_range).then(None).otherwise(raw_value)
    flags = (
        pl.when(pl.col(_NO_TRADE))
        .then(_structure_current_gap_flags(pl))
        .when(zero_range)
        .then(_structure_flags(pl, ("zero_range",)))
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _ohlcv_rolling_flags(
    polars: Any,
    *,
    insufficient: Any,
    rolling_no_trade_count: Any,
    rolling_flag_counts: Mapping[str, Any],
) -> Any:
    pl = polars
    return (
        pl.when(insufficient)
        .then(_ohlcv_flags(pl, ("insufficient_window",)))
        .when(rolling_no_trade_count > 0)
        .then(
            _ohlcv_window_gap_flags(
                pl,
                rolling_no_trade_count=rolling_no_trade_count,
                rolling_flag_counts=rolling_flag_counts,
            )
        )
        .otherwise(_flags(pl, ()))
    )


def _ohlcv_window_gap_flags(
    polars: Any,
    *,
    rolling_no_trade_count: Any,
    rolling_flag_counts: Mapping[str, Any],
) -> Any:
    fragments = [_ohlcv_flags(polars, ("input_gap",))]
    for flag in _GAP_QUALITY_FLAGS:
        fragments.append(
            _conditional_flags(
                polars,
                rolling_flag_counts[flag] > 0,
                (flag,),
            )
        )
    fragments.append(_conditional_flags(polars, rolling_no_trade_count > 0, ("no_trade",)))
    return polars.concat_list(*fragments).list.unique().list.sort()


def _primitive_gap_flags(
    polars: Any,
    reasons: Sequence[str],
    *,
    flag_counts: Mapping[str, Any],
) -> Any:
    fragments = [_flags(polars, ("primitive_gap", *reasons))]
    for flag in _GAP_QUALITY_FLAGS:
        fragments.append(_conditional_flags(polars, flag_counts[flag] > 0, (flag,)))
    return polars.concat_list(*fragments).list.unique().list.sort()


def _structure_current_gap_flags(polars: Any) -> Any:
    pl = polars
    return (
        pl.concat_list(_structure_flags(pl, ("no_trade",)), pl.col(_INPUT_FLAGS))
        .list.unique()
        .list.sort()
    )


def _ohlcv_flags(polars: Any, values: Sequence[str]) -> Any:
    return polars.concat_list(
        _flags(polars, ("ohlcv_gap",)),
        _flags(polars, values),
    ).list.unique().list.sort()


def _structure_flags(polars: Any, values: Sequence[str]) -> Any:
    return polars.concat_list(
        _flags(polars, ("structure_gap",)),
        _flags(polars, values),
    ).list.unique().list.sort()


def _conditional_flags(polars: Any, condition: Any, values: Sequence[str]) -> Any:
    return polars.when(condition).then(_flags(polars, values)).otherwise(_flags(polars, ()))


def _contains_any_flag(polars: Any, flags: Sequence[str]) -> Any:
    result = _point_has_flag(polars, flags[0])
    for flag in flags[1:]:
        result = result | _point_has_flag(polars, flag)
    return result


def _point_has_flag(polars: Any, flag: str) -> Any:
    if flag == "no_trade":
        return polars.col(_NO_TRADE) | _contains_flag(polars, flag)
    return _contains_flag(polars, flag)


def _contains_flag(polars: Any, flag: str) -> Any:
    return polars.col(_INPUT_FLAGS).list.contains(flag).fill_null(False)


def _ohlcv_no_trade_flag_counts(polars: Any, window: int) -> dict[str, Any]:
    return {
        flag: _rolling_true_count(
            polars.col(_NO_TRADE) & _point_has_flag(polars, flag),
            window,
            polars=polars,
        )
        for flag in _GAP_QUALITY_FLAGS
    }


def _rolling_true_count(condition: Any, window: int, *, polars: Any) -> Any:
    return (
        condition.cast(polars.Int64)
        .rolling_sum(window_size=window, min_samples=window)
        .over(_SEGMENT)
        .fill_null(0)
    )


def _cumulative_true_count(condition: Any, *, polars: Any) -> Any:
    return condition.cast(polars.Int64).cum_sum().over(_SEGMENT).fill_null(0)


def _group_position(polars: Any) -> Any:
    return polars.col(_CLOSE).cum_count().over(_SEGMENT).cast(polars.Int64)


def _input_quality_flags(polars: Any) -> Any:
    pl = polars
    return (
        pl.col("quality_flags")
        .fill_null(_flags(pl, ()))
        .list.eval(pl.element().str.to_lowercase())
        .list.unique()
        .list.sort()
    )


def _bar_start_ts(polars: Any) -> Any:
    return polars.col("bar_start_ts").cast(polars.Datetime("us", "UTC"), strict=False)


def _flags(polars: Any, values: Sequence[str]) -> Any:
    return polars.lit(list(values), dtype=polars.List(polars.Utf8))


def _require_columns(frame: Any, columns: Sequence[str]) -> None:
    missing = tuple(column for column in columns if column not in frame.columns)
    if missing:
        raise PackMaterializerError("canonical frame missing columns: " + ", ".join(missing))


__all__ = [
    "VOLUME_ACTIVITY_DDOF",
    "VOLUME_ACTIVITY_FEATURE_IDS",
    "VOLUME_ACTIVITY_HORIZON",
    "VOLUME_ACTIVITY_RESET_ON_SESSION",
    "VOLUME_ACTIVITY_WINDOW_LENGTH",
    "build_volume_activity_pack",
    "supports_volume_activity_pack",
]
