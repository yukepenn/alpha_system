"""Liquidity sweep / price-action structure Polars pack for the V1 fast path."""

from __future__ import annotations

import re
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
from alpha_system.features.families.structure import StructureFeatureName
from alpha_system.features.fast.materializer import (
    FastFeatureDeclaration,
    FastFeaturePack,
    PackMaterializerError,
)

LIQUIDITY_PA_STRUCTURE_FEATURE_IDS: tuple[str, ...] = tuple(
    f"liquidity_structure_{feature_name.value}" for feature_name in StructureFeatureName
)

_FEATURE_ID_TO_NAME: dict[str, StructureFeatureName] = {
    f"liquidity_structure_{feature_name.value}": feature_name
    for feature_name in StructureFeatureName
}
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
_PROPAGATED_PRIOR_FLAGS = (
    "bbo_quarantined",
    "input_gap",
    "missing_bbo",
    "no_trade",
    "primitive_gap",
)

_PREFIX = "__flps"
_SERIES = f"{_PREFIX}_series_id"
_SESSION = f"{_PREFIX}_session_label"
_SESSION_UPPER = f"{_PREFIX}_session_label_upper"
_SEGMENT_START = f"{_PREFIX}_segment_start"
_SEGMENT = f"{_PREFIX}_segment"
_SEGMENT_START_TS = f"{_PREFIX}_segment_start_ts"
_BAR_START = f"{_PREFIX}_bar_start_ts"
_INPUT_FLAGS = f"{_PREFIX}_input_quality_flags"
_OPEN = f"{_PREFIX}_open"
_HIGH = f"{_PREFIX}_high"
_LOW = f"{_PREFIX}_low"
_CLOSE = f"{_PREFIX}_close"
_BAR_RANGE = f"{_PREFIX}_bar_range"
_NO_TRADE = f"{_PREFIX}_no_trade"


@dataclass(frozen=True, slots=True)
class _PackExpression:
    value: Any
    flags: Any


@dataclass(frozen=True, slots=True)
class _PriorConfig:
    window: int
    reset_on_session: bool


@dataclass(frozen=True, slots=True)
class _OpeningRangeConfig:
    opening_range_minutes: int
    opening_session_label: str


def build_liquidity_pa_structure_pack(feature_set: FeatureSetSpec) -> FastFeaturePack:
    """Build the governed liquidity-sweep / PA-structure fast pack."""

    if not isinstance(feature_set, FeatureSetSpec):
        raise PackMaterializerError("liquidity_pa_structure fast pack requires a FeatureSetSpec")
    _validate_liquidity_pa_structure_feature_set(feature_set)
    polars = require_dependency("polars")
    prior_configs = _prior_configs(feature_set.features)
    opening_configs = _opening_range_configs(feature_set.features)
    expressions = _liquidity_pa_structure_expressions(polars, feature_set.features)
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
        prepare_frame=lambda frame: _prepare_frame(
            frame,
            prior_configs=prior_configs,
            opening_configs=opening_configs,
        ),
    )


def supports_liquidity_pa_structure_pack(feature_set: FeatureSetSpec) -> bool:
    """Return true when every requested feature is governed liquidity structure."""

    if not isinstance(feature_set, FeatureSetSpec):
        return False
    try:
        _validate_liquidity_pa_structure_feature_set(feature_set)
    except PackMaterializerError:
        return False
    return True


def _validate_liquidity_pa_structure_feature_set(feature_set: FeatureSetSpec) -> None:
    features = tuple(feature_set.features)
    if not features:
        raise PackMaterializerError("liquidity_pa_structure fast pack requires features")
    feature_ids = tuple(feature.feature_id for feature in features)
    if len(set(feature_ids)) != len(feature_ids):
        raise PackMaterializerError("liquidity_pa_structure fast pack rejects duplicate features")
    for feature in features:
        _validate_liquidity_pa_structure_feature(feature)


def _validate_liquidity_pa_structure_feature(feature: FeatureSpec) -> None:
    if not isinstance(feature, FeatureSpec):
        raise PackMaterializerError(
            "liquidity_pa_structure pack entries must be FeatureSpec objects"
        )
    if feature.family is not FeatureFamily.LIQUIDITY_STRUCTURE:
        raise PackMaterializerError(
            "liquidity_pa_structure pack can only contain Liquidity Structure features"
        )
    feature_name = _FEATURE_ID_TO_NAME.get(feature.feature_id)
    if feature_name is None:
        raise PackMaterializerError(
            f"unsupported liquidity_pa_structure feature_id: {feature.feature_id}"
        )
    parameters = feature.transform.parameters.to_dict()
    _require_parameter(parameters, "feature_name", feature_name.value, feature.feature_id)
    _require_bool_parameter(parameters, "reset_on_session", feature.feature_id)
    if feature.transform.transform_id != feature_name.value:
        raise PackMaterializerError(
            f"{feature.feature_id} transform must be {feature_name.value}"
        )
    if feature.normalization.normalization_id != "identity":
        raise PackMaterializerError(f"{feature.feature_id} normalization must be identity")
    if feature_name in _ROLLING_PRIOR_FEATURES:
        _require_rolling_window(feature)
        _require_parameter(parameters, "window_length", feature.window.length, feature.feature_id)
        return
    if feature_name in _OPENING_RANGE_FEATURES:
        _require_expanding_window(feature)
        opening_minutes = parameters.get("opening_range_minutes")
        if not isinstance(opening_minutes, int) or isinstance(opening_minutes, bool):
            raise PackMaterializerError(
                f"{feature.feature_id} requires integer opening_range_minutes"
            )
        if opening_minutes <= 0:
            raise PackMaterializerError(
                f"{feature.feature_id} requires positive opening_range_minutes"
            )
        opening_session = parameters.get("opening_session_label")
        if not isinstance(opening_session, str) or not opening_session.strip():
            raise PackMaterializerError(
                f"{feature.feature_id} requires non-empty opening_session_label"
            )
        return
    if feature_name in _WICK_FEATURES:
        _require_point_in_time_window(feature)
        return
    raise PackMaterializerError(f"unsupported Liquidity Structure feature: {feature_name}")


def _require_parameter(
    parameters: Mapping[str, object],
    name: str,
    expected: object,
    feature_id: str,
) -> None:
    if parameters.get(name) != expected:
        raise PackMaterializerError(f"{feature_id} requires {name}={expected!r}")


def _require_bool_parameter(
    parameters: Mapping[str, object],
    name: str,
    feature_id: str,
) -> None:
    if type(parameters.get(name)) is not bool:
        raise PackMaterializerError(f"{feature_id} requires boolean {name}")


def _require_rolling_window(feature: FeatureSpec) -> None:
    if feature.window.kind is not WindowKind.ROLLING:
        raise PackMaterializerError(f"{feature.feature_id} requires a rolling window")
    if feature.window.length <= 0:
        raise PackMaterializerError(f"{feature.feature_id} requires a positive window length")
    if not feature.window.is_live_compatible:
        raise PackMaterializerError(f"{feature.feature_id} requires a live-compatible window")


def _require_expanding_window(feature: FeatureSpec) -> None:
    if feature.window.kind is not WindowKind.EXPANDING or feature.window.length != 1:
        raise PackMaterializerError(f"{feature.feature_id} requires an expanding window")
    if not feature.window.is_live_compatible:
        raise PackMaterializerError(f"{feature.feature_id} requires a live-compatible window")


def _require_point_in_time_window(feature: FeatureSpec) -> None:
    if feature.window.kind is not WindowKind.POINT_IN_TIME or feature.window.length != 1:
        raise PackMaterializerError(f"{feature.feature_id} requires a point-in-time window")
    if not feature.window.is_live_compatible:
        raise PackMaterializerError(f"{feature.feature_id} requires a live-compatible window")


def _prior_configs(features: Sequence[FeatureSpec]) -> tuple[_PriorConfig, ...]:
    configs: list[_PriorConfig] = []
    for feature in features:
        feature_name = _FEATURE_ID_TO_NAME[feature.feature_id]
        if feature_name not in _ROLLING_PRIOR_FEATURES:
            continue
        config = _prior_config(feature)
        if config not in configs:
            configs.append(config)
    return tuple(configs)


def _prior_config(feature: FeatureSpec) -> _PriorConfig:
    parameters = feature.transform.parameters.to_dict()
    reset_on_session = parameters["reset_on_session"]
    if type(reset_on_session) is not bool:
        raise PackMaterializerError(f"{feature.feature_id} requires boolean reset_on_session")
    return _PriorConfig(window=feature.window.length, reset_on_session=reset_on_session)


def _opening_range_configs(features: Sequence[FeatureSpec]) -> tuple[_OpeningRangeConfig, ...]:
    configs: list[_OpeningRangeConfig] = []
    for feature in features:
        feature_name = _FEATURE_ID_TO_NAME[feature.feature_id]
        if feature_name not in _OPENING_RANGE_FEATURES:
            continue
        config = _opening_range_config(feature)
        if config not in configs:
            configs.append(config)
    return tuple(configs)


def _opening_range_config(feature: FeatureSpec) -> _OpeningRangeConfig:
    parameters = feature.transform.parameters.to_dict()
    return _OpeningRangeConfig(
        opening_range_minutes=int(parameters["opening_range_minutes"]),
        opening_session_label=str(parameters["opening_session_label"]).upper(),
    )


def _liquidity_pa_structure_expressions(
    polars: Any,
    features: Sequence[FeatureSpec],
) -> dict[str, _PackExpression]:
    expressions: dict[str, _PackExpression] = {}
    for feature in features:
        feature_name = _FEATURE_ID_TO_NAME[feature.feature_id]
        if feature_name in _PRIOR_FEATURES:
            expressions[feature.feature_id] = _prior_distance_expression(
                polars,
                feature_name,
                _prior_config(feature),
            )
        elif feature_name in _OPENING_RANGE_FEATURES:
            expressions[feature.feature_id] = _opening_range_distance_expression(
                polars,
                feature_name,
                _opening_range_config(feature),
            )
        elif feature_name in _SWEEP_FEATURES:
            expressions[feature.feature_id] = _sweep_expression(
                polars,
                feature_name,
                _prior_config(feature),
            )
        elif feature_name in _WICK_FEATURES:
            expressions[feature.feature_id] = _wick_expression(polars, feature_name)
        elif feature_name in _COMPRESSION_FEATURES:
            expressions[feature.feature_id] = _range_contraction_expression(
                polars,
                _prior_config(feature),
            )
        else:
            raise PackMaterializerError(f"unsupported Liquidity Structure feature: {feature_name}")
    return expressions


def _prepare_frame(
    frame: Any,
    *,
    prior_configs: Sequence[_PriorConfig],
    opening_configs: Sequence[_OpeningRangeConfig],
) -> Any:
    pl = require_dependency("polars")
    _require_columns(
        frame,
        (
            "series_id",
            "bar_start_ts",
            "open",
            "high",
            "low",
            "close",
            "quality_flags",
            "session_label",
        ),
    )
    prepared = frame.with_columns(
        (
            pl.col("series_id").cast(pl.Utf8).alias(_SERIES),
            pl.col("session_label").cast(pl.Utf8).alias(_SESSION),
            pl.col("session_label").cast(pl.Utf8).str.to_uppercase().alias(_SESSION_UPPER),
            _bar_start_ts(pl).alias(_BAR_START),
            _input_quality_flags(pl).alias(_INPUT_FLAGS),
            pl.col("open").cast(pl.Float64, strict=False).alias(_OPEN),
            pl.col("high").cast(pl.Float64, strict=False).alias(_HIGH),
            pl.col("low").cast(pl.Float64, strict=False).alias(_LOW),
            pl.col("close").cast(pl.Float64, strict=False).alias(_CLOSE),
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
    prepared = prepared.with_columns(segment_start.alias(_SEGMENT_START)).with_columns(
        pl.col(_SEGMENT_START).cast(pl.Int64).cum_sum().alias(_SEGMENT)
    )
    prepared = prepared.with_columns(
        pl.col(_BAR_START).first().over(_SEGMENT).alias(_SEGMENT_START_TS)
    )
    expressions: list[Any] = []
    for config in prior_configs:
        expressions.extend(_prior_prepare_expressions(pl, config))
    for config in opening_configs:
        expressions.extend(_opening_prepare_expressions(pl, config))
    if not expressions:
        return prepared
    return prepared.with_columns(expressions)


def _prior_prepare_expressions(polars: Any, config: _PriorConfig) -> tuple[Any, ...]:
    pl = polars
    group = _prior_group(config)
    prior_high = pl.col(_HIGH).shift(1).over(group)
    prior_low = pl.col(_LOW).shift(1).over(group)
    prior_range = pl.col(_BAR_RANGE).shift(1).over(group)
    prior_no_trade = pl.col(_NO_TRADE).shift(1).over(group).fill_null(False)
    expressions: list[Any] = [
        _group_position(pl, group).alias(_prior_position_column(config)),
        prior_high.rolling_max(window_size=config.window, min_samples=config.window)
        .over(group)
        .alias(_prior_high_column(config)),
        prior_low.rolling_min(window_size=config.window, min_samples=config.window)
        .over(group)
        .alias(_prior_low_column(config)),
        (
            prior_range.rolling_sum(window_size=config.window, min_samples=config.window).over(
                group
            )
            / float(config.window)
        ).alias(_prior_mean_range_column(config)),
        _rolling_true_count(prior_no_trade, config.window, group, polars=pl).alias(
            _prior_no_trade_count_column(config)
        ),
    ]
    for flag in _PROPAGATED_PRIOR_FLAGS:
        prior_flag = (
            (pl.col(_NO_TRADE) & _contains_flag(pl, flag)).shift(1).over(group).fill_null(False)
        )
        expressions.append(
            _rolling_true_count(prior_flag, config.window, group, polars=pl).alias(
                _prior_flag_count_column(config, flag)
            )
        )
    return tuple(expressions)


def _opening_prepare_expressions(
    polars: Any,
    config: _OpeningRangeConfig,
) -> tuple[Any, ...]:
    pl = polars
    in_opening_session = pl.col(_SESSION_UPPER) == config.opening_session_label.upper()
    in_window = pl.col(_BAR_START) < (
        pl.col(_SEGMENT_START_TS) + pl.duration(minutes=config.opening_range_minutes)
    )
    high_input = (
        pl.when(in_opening_session & in_window & _is_trade(pl))
        .then(pl.col(_HIGH))
        .otherwise(None)
    )
    low_input = (
        pl.when(in_opening_session & in_window & _is_trade(pl))
        .then(pl.col(_LOW))
        .otherwise(None)
    )
    return (
        high_input.cum_max()
        .forward_fill()
        .over(_SEGMENT)
        .alias(_opening_high_column(config)),
        low_input.cum_min()
        .forward_fill()
        .over(_SEGMENT)
        .alias(_opening_low_column(config)),
    )


def _prior_distance_expression(
    polars: Any,
    feature_name: StructureFeatureName,
    config: _PriorConfig,
) -> _PackExpression:
    pl = polars
    prior_high = pl.col(_prior_high_column(config))
    prior_low = pl.col(_prior_low_column(config))
    value = (
        pl.when(_prior_gap_condition(pl, config))
        .then(None)
        .when(feature_name is StructureFeatureName.PRIOR_HIGH_DISTANCE)
        .then(pl.col(_CLOSE) - prior_high)
        .otherwise(pl.col(_CLOSE) - prior_low)
    )
    return _PackExpression(value, _prior_gap_flags(pl, config))


def _opening_range_distance_expression(
    polars: Any,
    feature_name: StructureFeatureName,
    config: _OpeningRangeConfig,
) -> _PackExpression:
    pl = polars
    opening_high = pl.col(_opening_high_column(config))
    opening_low = pl.col(_opening_low_column(config))
    outside_opening_session = pl.col(_SESSION_UPPER) != config.opening_session_label.upper()
    no_opening_trade = opening_high.is_null() | opening_low.is_null()
    value = (
        pl.when(_is_no_trade(pl) | outside_opening_session | no_opening_trade)
        .then(None)
        .when(feature_name is StructureFeatureName.OPENING_RANGE_HIGH_DISTANCE)
        .then(pl.col(_CLOSE) - opening_high)
        .otherwise(pl.col(_CLOSE) - opening_low)
    )
    flags = (
        pl.when(_is_no_trade(pl))
        .then(_structure_current_gap_flags(pl))
        .when(outside_opening_session)
        .then(_structure_flags(pl, ("outside_opening_session",)))
        .when(no_opening_trade)
        .then(_structure_flags(pl, ("no_opening_trade",)))
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _sweep_expression(
    polars: Any,
    feature_name: StructureFeatureName,
    config: _PriorConfig,
) -> _PackExpression:
    pl = polars
    prior_high = pl.col(_prior_high_column(config))
    prior_low = pl.col(_prior_low_column(config))
    high_sweep = pl.col(_HIGH) > prior_high
    low_sweep = pl.col(_LOW) < prior_low
    if feature_name is StructureFeatureName.SWEEP_HIGH_FLAG:
        raw_value = high_sweep.cast(pl.Int64)
    elif feature_name is StructureFeatureName.SWEEP_LOW_FLAG:
        raw_value = low_sweep.cast(pl.Int64)
    elif feature_name is StructureFeatureName.FAILED_HIGH_BREAKOUT_FLAG:
        raw_value = (high_sweep & (pl.col(_CLOSE) <= prior_high)).cast(pl.Int64)
    elif feature_name is StructureFeatureName.FAILED_LOW_BREAKOUT_FLAG:
        raw_value = (low_sweep & (pl.col(_CLOSE) >= prior_low)).cast(pl.Int64)
    else:
        raise PackMaterializerError(f"unsupported sweep feature: {feature_name}")
    value = pl.when(_prior_gap_condition(pl, config)).then(None).otherwise(raw_value)
    return _PackExpression(value, _prior_gap_flags(pl, config))


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
        raise PackMaterializerError(f"unsupported wick feature: {feature_name}")
    value = pl.when(_is_no_trade(pl) | zero_range).then(None).otherwise(raw_value)
    flags = (
        pl.when(_is_no_trade(pl))
        .then(_structure_current_gap_flags(pl))
        .when(zero_range)
        .then(_structure_flags(pl, ("zero_range",)))
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _range_contraction_expression(polars: Any, config: _PriorConfig) -> _PackExpression:
    pl = polars
    prior_mean_range = pl.col(_prior_mean_range_column(config))
    prior_insufficient = _prior_insufficient(pl, config)
    prior_input_gap = _prior_input_gap(pl, config)
    zero_prior_range = prior_mean_range <= 0.0
    zero_range = pl.col(_BAR_RANGE) <= 0.0
    value = (
        pl.when(
            _is_no_trade(pl)
            | prior_insufficient
            | prior_input_gap
            | zero_prior_range
            | zero_range
        )
        .then(None)
        .otherwise(1.0 - pl.col(_BAR_RANGE) / prior_mean_range)
    )
    flags = (
        pl.when(_is_no_trade(pl))
        .then(_structure_current_gap_flags(pl))
        .when(prior_insufficient)
        .then(_structure_flags(pl, ("input_gap", "insufficient_window")))
        .when(prior_input_gap)
        .then(_prior_window_gap_flags(pl, config))
        .when(zero_prior_range)
        .then(_structure_flags(pl, ("zero_prior_range",)))
        .when(zero_range)
        .then(_structure_flags(pl, ("zero_range",)))
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _prior_gap_condition(polars: Any, config: _PriorConfig) -> Any:
    return _is_no_trade(polars) | _prior_insufficient(polars, config) | _prior_input_gap(
        polars,
        config,
    )


def _prior_gap_flags(polars: Any, config: _PriorConfig) -> Any:
    pl = polars
    return (
        pl.when(_is_no_trade(pl))
        .then(_structure_current_gap_flags(pl))
        .when(_prior_insufficient(pl, config))
        .then(_structure_flags(pl, ("input_gap", "insufficient_window")))
        .when(_prior_input_gap(pl, config))
        .then(_prior_window_gap_flags(pl, config))
        .otherwise(_flags(pl, ()))
    )


def _prior_insufficient(polars: Any, config: _PriorConfig) -> Any:
    return polars.col(_prior_position_column(config)) <= config.window


def _prior_input_gap(polars: Any, config: _PriorConfig) -> Any:
    return polars.col(_prior_no_trade_count_column(config)) > 0


def _prior_window_gap_flags(polars: Any, config: _PriorConfig) -> Any:
    pl = polars
    fragments = [_structure_flags(pl, ("input_gap",))]
    for flag in _PROPAGATED_PRIOR_FLAGS:
        fragments.append(
            _conditional_flags(
                pl,
                pl.col(_prior_flag_count_column(config, flag)) > 0,
                (flag,),
            )
        )
    return pl.concat_list(*fragments).list.unique().list.sort()


def _structure_current_gap_flags(polars: Any) -> Any:
    pl = polars
    return (
        pl.concat_list(_structure_flags(pl, ("no_trade",)), pl.col(_INPUT_FLAGS))
        .list.unique()
        .list.sort()
    )


def _structure_flags(polars: Any, values: Sequence[str]) -> Any:
    return polars.concat_list(
        _flags(polars, ("structure_gap",)),
        _flags(polars, values),
    ).list.unique().list.sort()


def _conditional_flags(polars: Any, condition: Any, values: Sequence[str]) -> Any:
    return polars.when(condition).then(_flags(polars, values)).otherwise(_flags(polars, ()))


def _is_trade(polars: Any) -> Any:
    return polars.col(_NO_TRADE).not_()


def _is_no_trade(polars: Any) -> Any:
    return polars.col(_NO_TRADE)


def _contains_flag(polars: Any, flag: str) -> Any:
    return polars.col(_INPUT_FLAGS).list.contains(flag).fill_null(False)


def _rolling_true_count(
    condition: Any,
    window: int,
    group: Sequence[str],
    *,
    polars: Any,
) -> Any:
    return (
        condition.cast(polars.Int64)
        .rolling_sum(window_size=window, min_samples=window)
        .over(list(group))
        .fill_null(0)
    )


def _group_position(polars: Any, group: Sequence[str]) -> Any:
    return polars.col(_CLOSE).cum_count().over(list(group)).cast(polars.Int64)


def _prior_group(config: _PriorConfig) -> list[str]:
    return [_SEGMENT] if config.reset_on_session else [_SERIES]


def _input_quality_flags(polars: Any) -> Any:
    pl = polars
    return (
        pl.col("quality_flags")
        .cast(pl.List(pl.Utf8), strict=False)
        .fill_null(_flags(pl, ()))
        .list.eval(pl.element().str.to_lowercase())
        .list.unique()
        .list.sort()
    )


def _bar_start_ts(polars: Any) -> Any:
    return polars.col("bar_start_ts").cast(polars.Datetime("us", "UTC"), strict=False)


def _flags(polars: Any, values: Sequence[str]) -> Any:
    return polars.lit(list(values), dtype=polars.List(polars.Utf8))


def _token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    if not token:
        raise PackMaterializerError("fast structure column token cannot be empty")
    return token


def _prior_config_token(config: _PriorConfig) -> str:
    reset = "session" if config.reset_on_session else "series"
    return f"w{config.window}_{reset}"


def _prior_position_column(config: _PriorConfig) -> str:
    return f"{_PREFIX}_prior_position_{_prior_config_token(config)}"


def _prior_high_column(config: _PriorConfig) -> str:
    return f"{_PREFIX}_prior_high_{_prior_config_token(config)}"


def _prior_low_column(config: _PriorConfig) -> str:
    return f"{_PREFIX}_prior_low_{_prior_config_token(config)}"


def _prior_mean_range_column(config: _PriorConfig) -> str:
    return f"{_PREFIX}_prior_mean_range_{_prior_config_token(config)}"


def _prior_no_trade_count_column(config: _PriorConfig) -> str:
    return f"{_PREFIX}_prior_no_trade_count_{_prior_config_token(config)}"


def _prior_flag_count_column(config: _PriorConfig, flag: str) -> str:
    return f"{_PREFIX}_prior_flag_{_token(flag)}_count_{_prior_config_token(config)}"


def _opening_config_token(config: _OpeningRangeConfig) -> str:
    return f"{_token(config.opening_session_label)}_{config.opening_range_minutes}m"


def _opening_high_column(config: _OpeningRangeConfig) -> str:
    return f"{_PREFIX}_opening_high_{_opening_config_token(config)}"


def _opening_low_column(config: _OpeningRangeConfig) -> str:
    return f"{_PREFIX}_opening_low_{_opening_config_token(config)}"


def _require_columns(frame: Any, columns: Sequence[str]) -> None:
    missing = tuple(column for column in columns if column not in frame.columns)
    if missing:
        raise PackMaterializerError("canonical frame missing columns: " + ", ".join(missing))


__all__ = [
    "LIQUIDITY_PA_STRUCTURE_FEATURE_IDS",
    "build_liquidity_pa_structure_pack",
    "supports_liquidity_pa_structure_pack",
]
