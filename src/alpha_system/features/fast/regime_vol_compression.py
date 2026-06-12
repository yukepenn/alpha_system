"""Regime / volatility / compression Polars pack for the V1 fast path."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from alpha_system.data.foundation.sources import DataFoundationValidationError
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
)
from alpha_system.features.session_truth import (
    SessionTruthClock,
    session_contract_parameters,
    session_truth_clock,
)

REGIME_VOL_COMPRESSION_FEATURE_IDS: tuple[str, ...] = (
    "base_ohlcv_atr",
    "base_ohlcv_trendiness",
    "liquidity_structure_range_contraction",
)
_REGIME_VOL_COMPRESSION_SUPPORTED_FEATURE_IDS: tuple[str, ...] = (
    "base_ohlcv_atr",
    "base_ohlcv_returns",
    "base_ohlcv_rolling_range",
    "base_ohlcv_trendiness",
    "liquidity_structure_range_contraction",
)

_OHLCV_FEATURE_ID_TO_NAME: dict[str, OHLCVFeatureName] = {
    "base_ohlcv_atr": OHLCVFeatureName.ATR,
    "base_ohlcv_returns": OHLCVFeatureName.RETURNS,
    "base_ohlcv_rolling_range": OHLCVFeatureName.ROLLING_RANGE,
    "base_ohlcv_trendiness": OHLCVFeatureName.TRENDINESS,
}
_STRUCTURE_FEATURE_ID_TO_NAME: dict[str, StructureFeatureName] = {
    "liquidity_structure_range_contraction": StructureFeatureName.RANGE_CONTRACTION,
}
_PRIMITIVE_GAP_FLAGS = (
    "missing_bbo",
    "bbo_quarantined",
    "no_trade",
    "primitive_gap",
    "input_gap",
)

_PREFIX = "__frvc"
_SERIES = f"{_PREFIX}_series_id"
_SESSION = f"{_PREFIX}_session_label"
_SEGMENT_START = f"{_PREFIX}_segment_start"
_SEGMENT = f"{_PREFIX}_segment"
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


def build_regime_vol_compression_pack(feature_set: FeatureSetSpec) -> FastFeaturePack:
    """Build the governed regime / volatility / compression fast pack."""

    if not isinstance(feature_set, FeatureSetSpec):
        raise PackMaterializerError(
            "regime_vol_compression fast pack requires a FeatureSetSpec"
        )
    _validate_regime_vol_compression_feature_set(feature_set)
    polars = require_dependency("polars")
    expressions = _regime_vol_compression_expressions(polars, feature_set.features)
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


def supports_regime_vol_compression_pack(feature_set: FeatureSetSpec) -> bool:
    """Return true when a feature set is a governed regime pack subset."""

    if not isinstance(feature_set, FeatureSetSpec):
        return False
    try:
        _validate_regime_vol_compression_feature_set(feature_set)
    except PackMaterializerError:
        return False
    return True


def _validate_regime_vol_compression_feature_set(feature_set: FeatureSetSpec) -> None:
    features = tuple(feature_set.features)
    if not features:
        raise PackMaterializerError("regime_vol_compression fast pack requires features")
    feature_ids = tuple(feature.feature_id for feature in features)
    if len(set(feature_ids)) != len(feature_ids):
        raise PackMaterializerError("regime_vol_compression fast pack rejects duplicate features")
    unknown = tuple(
        feature_id
        for feature_id in feature_ids
        if feature_id not in _REGIME_VOL_COMPRESSION_SUPPORTED_FEATURE_IDS
    )
    if unknown:
        raise PackMaterializerError(
            "regime_vol_compression fast pack requires governed regime features: "
            + ", ".join(unknown)
        )
    for feature in features:
        _validate_regime_vol_compression_feature(feature)


def _validate_regime_vol_compression_feature(feature: FeatureSpec) -> None:
    if not isinstance(feature, FeatureSpec):
        raise PackMaterializerError(
            "regime_vol_compression pack entries must be FeatureSpec objects"
        )
    if feature.feature_id in _OHLCV_FEATURE_ID_TO_NAME:
        _validate_ohlcv_feature(feature)
        return
    if feature.feature_id in _STRUCTURE_FEATURE_ID_TO_NAME:
        _validate_structure_feature(feature)
        return
    raise PackMaterializerError(
        f"unsupported regime_vol_compression feature_id: {feature.feature_id}"
    )


def _validate_ohlcv_feature(feature: FeatureSpec) -> None:
    if feature.family is not FeatureFamily.BASE_OHLCV:
        raise PackMaterializerError("atr/trendiness pack entries must be Base OHLCV features")
    feature_name = _OHLCV_FEATURE_ID_TO_NAME[feature.feature_id]
    parameters = feature.transform.parameters.to_dict()
    _require_parameter(parameters, "feature_name", feature_name.value, feature.feature_id)
    _require_bool_parameter(parameters, "reset_on_session", feature.feature_id)
    if bool(parameters["reset_on_session"]):
        _validate_session_contract_parameters(parameters, feature.feature_id)
    _require_window(feature)
    if feature_name is not OHLCVFeatureName.RETURNS:
        _require_parameter(parameters, "window_length", feature.window.length, feature.feature_id)
    expected_transform = {
        OHLCVFeatureName.ATR: "average_true_range",
        OHLCVFeatureName.RETURNS: "return",
        OHLCVFeatureName.ROLLING_RANGE: "rolling_range",
        OHLCVFeatureName.TRENDINESS: "trendiness",
    }[feature_name]
    if feature.transform.transform_id != expected_transform:
        raise PackMaterializerError(
            f"{feature.feature_id} transform must be {expected_transform}"
        )
    if feature.normalization.normalization_id != "identity":
        raise PackMaterializerError(f"{feature.feature_id} normalization must be identity")


def _validate_structure_feature(feature: FeatureSpec) -> None:
    if feature.family is not FeatureFamily.LIQUIDITY_STRUCTURE:
        raise PackMaterializerError(
            "range_contraction pack entry must be a Liquidity Structure feature"
        )
    feature_name = _STRUCTURE_FEATURE_ID_TO_NAME[feature.feature_id]
    parameters = feature.transform.parameters.to_dict()
    _require_parameter(parameters, "feature_name", feature_name.value, feature.feature_id)
    _require_bool_parameter(parameters, "reset_on_session", feature.feature_id)
    if bool(parameters["reset_on_session"]):
        _validate_session_contract_parameters(parameters, feature.feature_id)
    _require_parameter(parameters, "window_length", feature.window.length, feature.feature_id)
    _require_window(feature)
    if feature.transform.transform_id != "range_contraction":
        raise PackMaterializerError(
            f"{feature.feature_id} transform must be range_contraction"
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


def _require_bool_parameter(
    parameters: Mapping[str, object],
    name: str,
    feature_id: str,
) -> None:
    if type(parameters.get(name)) is not bool:
        raise PackMaterializerError(f"{feature_id} requires boolean {name}")


def _validate_session_contract_parameters(
    parameters: Mapping[str, object],
    feature_id: str,
) -> None:
    try:
        expected = session_contract_parameters()
    except DataFoundationValidationError as exc:
        raise PackMaterializerError(str(exc)) from exc
    for name, value in expected.items():
        _require_parameter(parameters, name, value, feature_id)


def _require_window(feature: FeatureSpec) -> None:
    if feature.window.kind is not WindowKind.ROLLING:
        raise PackMaterializerError(f"{feature.feature_id} requires a rolling window")
    if not feature.window.is_live_compatible:
        raise PackMaterializerError(f"{feature.feature_id} requires a live-compatible window")


def _regime_vol_compression_expressions(
    polars: Any,
    features: Sequence[FeatureSpec],
) -> dict[str, _PackExpression]:
    expressions: dict[str, _PackExpression] = {}
    for feature in features:
        if feature.feature_id == "base_ohlcv_atr":
            expressions[feature.feature_id] = _atr_expression(polars, feature)
        elif feature.feature_id == "base_ohlcv_returns":
            expressions[feature.feature_id] = _returns_expression(polars, feature)
        elif feature.feature_id == "base_ohlcv_rolling_range":
            expressions[feature.feature_id] = _rolling_range_expression(polars, feature)
        elif feature.feature_id == "base_ohlcv_trendiness":
            expressions[feature.feature_id] = _trendiness_expression(polars, feature)
        elif feature.feature_id == "liquidity_structure_range_contraction":
            expressions[feature.feature_id] = _range_contraction_expression(polars, feature)
        else:
            raise PackMaterializerError(
                f"unsupported regime_vol_compression feature_id: {feature.feature_id}"
            )
    return expressions


def _returns_expression(polars: Any, feature: FeatureSpec) -> _PackExpression:
    pl = polars
    parameters = feature.transform.parameters.to_dict()
    reset_on_session = bool(parameters["reset_on_session"])
    group = _window_group(feature)
    horizon = int(parameters.get("horizon", 1))
    prior_close = pl.col(_CLOSE).shift(horizon).over(group)
    current_gap = _contains_any_flag(pl, _PRIMITIVE_GAP_FLAGS)
    prior_gap = current_gap.shift(horizon).over(group).fill_null(False)
    current_no_trade = pl.col(_NO_TRADE)
    prior_no_trade = current_no_trade.shift(horizon).over(group).fill_null(False)
    insufficient = prior_close.is_null()
    session_reset = pl.lit(False)
    session_reset_flags = _flags(pl, ("primitive_gap", "session_reset"))
    if reset_on_session:
        prior_segment = pl.col(_SEGMENT).shift(horizon).over([_SERIES])
        session_reset = prior_segment.is_not_null() & (prior_segment != pl.col(_SEGMENT))
        session_reset_flags = _session_reset_flags(pl, horizon)
    zero_denominator = prior_close == 0.0
    value = (
        pl.when(insufficient | current_gap | prior_gap | zero_denominator)
        .then(None)
        .otherwise(pl.col(_CLOSE) / prior_close - 1.0)
    )
    flags = (
        pl.when(session_reset)
        .then(session_reset_flags)
        .when(insufficient)
        .then(_flags(pl, ("insufficient_window", "primitive_gap")))
        .when(current_no_trade | prior_no_trade)
        .then(_flags(pl, ("input_gap", "no_trade", "primitive_gap")))
        .when(current_gap | prior_gap)
        .then(_flags(pl, ("input_gap", "primitive_gap")))
        .when(zero_denominator)
        .then(_flags(pl, ("primitive_gap", "zero_denominator")))
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _prepare_frame(frame: Any) -> Any:
    pl = require_dependency("polars")
    _require_columns(
        frame,
        (
            "series_id",
            "session_label",
            "bar_start_ts",
            "quality_flags",
            "open",
            "high",
            "low",
            "close",
        ),
    )
    session_clock = _session_clock()
    prepared = frame.with_columns(
        (
            pl.col("series_id").cast(pl.Utf8).alias(_SERIES),
            _template_session_label(pl, session_clock).alias(_SESSION),
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
    return prepared.with_columns(segment_start.alias(_SEGMENT_START)).with_columns(
        pl.col(_SEGMENT_START).cast(pl.Int64).cum_sum().alias(_SEGMENT)
    )


def _atr_expression(polars: Any, feature: FeatureSpec) -> _PackExpression:
    pl = polars
    window = feature.window.length
    group = _window_group(feature)
    group_position = _group_position(pl, group)
    current_primitive_gap = _contains_any_flag(pl, _PRIMITIVE_GAP_FLAGS)
    valid_close = pl.when(current_primitive_gap.not_()).then(pl.col(_CLOSE)).otherwise(None)
    previous_valid_close = valid_close.forward_fill().over(group).shift(1).over(group)
    high_low = pl.col(_HIGH) - pl.col(_LOW)
    true_range = (
        pl.when(current_primitive_gap)
        .then(None)
        .when(previous_valid_close.is_null())
        .then(high_low)
        .otherwise(
            pl.max_horizontal(
                high_low,
                (pl.col(_HIGH) - previous_valid_close).abs(),
                (pl.col(_LOW) - previous_valid_close).abs(),
            )
        )
    )
    rolling_gap_count = _rolling_true_count(current_primitive_gap, window, group, polars=pl)
    partial_gap_count = _cumulative_true_count(current_primitive_gap, group, polars=pl)
    rolling_no_trade_count = _rolling_true_count(pl.col(_NO_TRADE), window, group, polars=pl)
    partial_no_trade_count = _cumulative_true_count(pl.col(_NO_TRADE), group, polars=pl)
    rolling_input_gap_count = _rolling_true_count(
        _contains_flag(pl, "input_gap"),
        window,
        group,
        polars=pl,
    )
    partial_input_gap_count = _cumulative_true_count(
        _contains_flag(pl, "input_gap"),
        group,
        polars=pl,
    )
    rolling_missing_bbo_count = _rolling_true_count(
        _contains_flag(pl, "missing_bbo"),
        window,
        group,
        polars=pl,
    )
    partial_missing_bbo_count = _cumulative_true_count(
        _contains_flag(pl, "missing_bbo"),
        group,
        polars=pl,
    )
    rolling_bbo_quarantined_count = _rolling_true_count(
        _contains_flag(pl, "bbo_quarantined"),
        window,
        group,
        polars=pl,
    )
    partial_bbo_quarantined_count = _cumulative_true_count(
        _contains_flag(pl, "bbo_quarantined"),
        group,
        polars=pl,
    )
    insufficient = group_position < window
    rolling_mean = true_range.rolling_mean(window_size=window, min_samples=window).over(group)
    value = (
        pl.when(insufficient | (rolling_gap_count > 0))
        .then(None)
        .otherwise(rolling_mean)
    )
    flags = (
        pl.when(insufficient)
        .then(
            _primitive_gap_flags(
                pl,
                insufficient=True,
                gap_count=partial_gap_count,
                no_trade_count=partial_no_trade_count,
                input_gap_count=partial_input_gap_count,
                missing_bbo_count=partial_missing_bbo_count,
                bbo_quarantined_count=partial_bbo_quarantined_count,
            )
        )
        .when(rolling_gap_count > 0)
        .then(
            _primitive_gap_flags(
                pl,
                insufficient=False,
                gap_count=rolling_gap_count,
                no_trade_count=rolling_no_trade_count,
                input_gap_count=rolling_input_gap_count,
                missing_bbo_count=rolling_missing_bbo_count,
                bbo_quarantined_count=rolling_bbo_quarantined_count,
            )
        )
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _rolling_range_expression(polars: Any, feature: FeatureSpec) -> _PackExpression:
    pl = polars
    window = feature.window.length
    group = _window_group(feature)
    group_position = _group_position(pl, group)
    rolling_no_trade_count = _rolling_true_count(pl.col(_NO_TRADE), window, group, polars=pl)
    insufficient = group_position < window
    rolling_range = (
        pl.col(_HIGH).rolling_max(window_size=window, min_samples=window).over(group)
        - pl.col(_LOW).rolling_min(window_size=window, min_samples=window).over(group)
    )
    value = (
        pl.when(insufficient | (rolling_no_trade_count > 0))
        .then(None)
        .otherwise(rolling_range)
    )
    flags = (
        pl.when(insufficient)
        .then(_flags(pl, ("insufficient_window", "ohlcv_gap")))
        .when(rolling_no_trade_count > 0)
        .then(_flags(pl, ("input_gap", "no_trade", "ohlcv_gap")))
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _trendiness_expression(polars: Any, feature: FeatureSpec) -> _PackExpression:
    pl = polars
    window = feature.window.length
    group = _window_group(feature)
    group_position = _group_position(pl, group)
    close_diff = (pl.col(_CLOSE) - pl.col(_CLOSE).shift(1).over(group)).abs()
    if window <= 1:
        denominator = pl.lit(0.0)
    else:
        denominator = close_diff.rolling_sum(
            window_size=window - 1,
            min_samples=window - 1,
        ).over(group)
    numerator = (pl.col(_CLOSE) - pl.col(_CLOSE).shift(window - 1).over(group)).abs()
    rolling_no_trade_count = _rolling_true_count(pl.col(_NO_TRADE), window, group, polars=pl)
    insufficient = group_position < window
    zero_movement = denominator == 0.0
    value = (
        pl.when(insufficient | (rolling_no_trade_count > 0) | zero_movement)
        .then(None)
        .otherwise(numerator / denominator)
    )
    flags = (
        pl.when(insufficient)
        .then(_flags(pl, ("insufficient_window", "ohlcv_gap")))
        .when(rolling_no_trade_count > 0)
        .then(_flags(pl, ("input_gap", "no_trade", "ohlcv_gap")))
        .when(zero_movement)
        .then(_flags(pl, ("ohlcv_gap", "zero_movement")))
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _range_contraction_expression(polars: Any, feature: FeatureSpec) -> _PackExpression:
    pl = polars
    window = feature.window.length
    group = _window_group(feature)
    group_position = _group_position(pl, group)
    prior_range = pl.col(_BAR_RANGE).shift(1).over(group)
    prior_no_trade = pl.col(_NO_TRADE).shift(1).over(group).fill_null(False)
    prior_range_sum = prior_range.rolling_sum(window_size=window, min_samples=window).over(group)
    prior_gap_count = _rolling_true_count(prior_no_trade, window, group, polars=pl)
    prior_mean_range = prior_range_sum / float(window)
    current_range = pl.col(_BAR_RANGE)
    current_no_trade = pl.col(_NO_TRADE)
    prior_insufficient = group_position <= window
    prior_input_gap = prior_gap_count > 0
    zero_prior_range = prior_mean_range <= 0.0
    zero_range = current_range <= 0.0
    value = (
        pl.when(
            current_no_trade
            | prior_insufficient
            | prior_input_gap
            | zero_prior_range
            | zero_range
        )
        .then(None)
        .otherwise(1.0 - current_range / prior_mean_range)
    )
    flags = (
        pl.when(current_no_trade)
        .then(_structure_current_gap_flags(pl))
        .when(prior_insufficient)
        .then(_flags(pl, ("input_gap", "insufficient_window", "structure_gap")))
        .when(prior_input_gap)
        .then(_flags(pl, ("input_gap", "no_trade", "structure_gap")))
        .when(zero_prior_range)
        .then(_flags(pl, ("structure_gap", "zero_prior_range")))
        .when(zero_range)
        .then(_flags(pl, ("structure_gap", "zero_range")))
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _window_group(feature: FeatureSpec) -> list[str]:
    reset_on_session = feature.transform.parameters.to_dict()["reset_on_session"]
    return [_SEGMENT] if reset_on_session else [_SERIES]


def _group_position(polars: Any, group: Sequence[str]) -> Any:
    return polars.col(_BAR_RANGE).cum_count().over(list(group)).cast(polars.Int64)


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


def _cumulative_true_count(condition: Any, group: Sequence[str], *, polars: Any) -> Any:
    return condition.cast(polars.Int64).cum_sum().over(list(group)).fill_null(0)


def _primitive_gap_flags(
    polars: Any,
    *,
    insufficient: bool,
    gap_count: Any,
    no_trade_count: Any,
    input_gap_count: Any,
    missing_bbo_count: Any,
    bbo_quarantined_count: Any,
) -> Any:
    pl = polars
    fragments = [
        _flags(pl, ("primitive_gap",)),
        _conditional_flags(pl, gap_count > 0, ("input_gap",)),
        _conditional_flags(pl, no_trade_count > 0, ("no_trade",)),
        _conditional_flags(pl, input_gap_count > 0, ("input_gap",)),
        _conditional_flags(pl, missing_bbo_count > 0, ("missing_bbo",)),
        _conditional_flags(pl, bbo_quarantined_count > 0, ("bbo_quarantined",)),
    ]
    if insufficient:
        fragments.append(_flags(pl, ("insufficient_window",)))
    return pl.concat_list(*fragments).list.unique().list.sort()


def _structure_current_gap_flags(polars: Any) -> Any:
    pl = polars
    return (
        pl.concat_list(_flags(pl, ("no_trade", "structure_gap")), pl.col(_INPUT_FLAGS))
        .list.unique()
        .list.sort()
    )


def _conditional_flags(polars: Any, condition: Any, values: Sequence[str]) -> Any:
    return polars.when(condition).then(_flags(polars, values)).otherwise(_flags(polars, ()))


def _session_reset_flags(polars: Any, horizon: int) -> Any:
    pl = polars
    window_flags = [
        pl.col(_INPUT_FLAGS).shift(offset).over([_SERIES]).fill_null(_flags(pl, ()))
        for offset in range(horizon + 1)
    ]
    return (
        pl.concat_list(
            _flags(pl, ("primitive_gap", "session_reset")),
            *window_flags,
        )
        .list.unique()
        .list.sort()
    )


def _contains_any_flag(polars: Any, flags: Sequence[str]) -> Any:
    result = _contains_flag(polars, flags[0])
    for flag in flags[1:]:
        result = result | _contains_flag(polars, flag)
    return result


def _contains_flag(polars: Any, flag: str) -> Any:
    return polars.col(_INPUT_FLAGS).list.contains(flag).fill_null(False)


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


def _session_clock() -> SessionTruthClock:
    try:
        return session_truth_clock()
    except DataFoundationValidationError as exc:
        raise PackMaterializerError(str(exc)) from exc


def _bar_start_ts(polars: Any) -> Any:
    return polars.col("bar_start_ts").cast(polars.Datetime("us", "UTC"), strict=False)


def _local_bar_start(polars: Any, session_clock: SessionTruthClock) -> Any:
    return _bar_start_ts(polars).dt.convert_time_zone(session_clock.timezone)


def _local_seconds(polars: Any, session_clock: SessionTruthClock) -> Any:
    local = _local_bar_start(polars, session_clock)
    return (
        local.dt.hour().cast(polars.Int64) * 3600
        + local.dt.minute().cast(polars.Int64) * 60
        + local.dt.second().cast(polars.Int64)
    )


def _is_rth(polars: Any, session_clock: SessionTruthClock) -> Any:
    seconds = _local_seconds(polars, session_clock)
    return (seconds >= session_clock.rth_open_seconds) & (
        seconds < session_clock.rth_close_seconds
    )


def _template_session_label(polars: Any, session_clock: SessionTruthClock) -> Any:
    return polars.when(_is_rth(polars, session_clock)).then(
        polars.lit("RTH")
    ).otherwise(polars.lit("ETH"))


def _flags(polars: Any, values: Sequence[str]) -> Any:
    return polars.lit(list(values), dtype=polars.List(polars.Utf8))


def _require_columns(frame: Any, columns: Sequence[str]) -> None:
    missing = tuple(column for column in columns if column not in frame.columns)
    if missing:
        raise PackMaterializerError("canonical frame missing columns: " + ", ".join(missing))


__all__ = [
    "REGIME_VOL_COMPRESSION_FEATURE_IDS",
    "build_regime_vol_compression_pack",
    "supports_regime_vol_compression_pack",
]
