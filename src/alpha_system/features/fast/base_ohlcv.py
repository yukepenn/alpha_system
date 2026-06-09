"""Base OHLCV Polars pack for the V1 fast producer path."""

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
from alpha_system.features.fast.materializer import (
    FastFeatureDeclaration,
    FastFeaturePack,
    PackMaterializerError,
    constant_window_mask,
)

BASE_OHLCV_WINDOW_LENGTH = 20
BASE_OHLCV_HORIZON = 1
BASE_OHLCV_DDOF = 0
BASE_OHLCV_RESET_ON_SESSION = False
BASE_OHLCV_FEATURE_IDS: tuple[str, ...] = (
    "base_ohlcv_returns",
    "base_ohlcv_log_returns",
    "base_ohlcv_rolling_volatility",
    "base_ohlcv_rolling_range",
    "base_ohlcv_range_position",
    "base_ohlcv_volume_zscore",
)

_FEATURE_ID_TO_NAME: dict[str, str] = {
    "base_ohlcv_returns": "returns",
    "base_ohlcv_log_returns": "log_returns",
    "base_ohlcv_rolling_volatility": "rolling_volatility",
    "base_ohlcv_rolling_range": "rolling_range",
    "base_ohlcv_range_position": "range_position",
    "base_ohlcv_volume_zscore": "volume_zscore",
}
_RETURN_FEATURE_IDS = frozenset({"base_ohlcv_returns", "base_ohlcv_log_returns"})
_ROLLING_20_FEATURE_IDS = frozenset(
    {
        "base_ohlcv_rolling_volatility",
        "base_ohlcv_rolling_range",
        "base_ohlcv_range_position",
        "base_ohlcv_volume_zscore",
    }
)
_PRIMITIVE_GAP_FLAGS = (
    "missing_bbo",
    "bbo_quarantined",
    "no_trade",
    "primitive_gap",
    "input_gap",
)


@dataclass(frozen=True, slots=True)
class _PackExpression:
    value: Any
    flags: Any


def build_base_ohlcv_pack(feature_set: FeatureSetSpec) -> FastFeaturePack:
    """Build the governed six-feature Base OHLCV fast pack."""

    if not isinstance(feature_set, FeatureSetSpec):
        raise PackMaterializerError("base_ohlcv fast pack requires a FeatureSetSpec")
    _validate_base_ohlcv_feature_set(feature_set)
    polars = require_dependency("polars")
    expressions = _base_ohlcv_expressions(polars)
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
    )


def supports_base_ohlcv_pack(feature_set: FeatureSetSpec) -> bool:
    """Return true when a feature set is exactly the V1 Base OHLCV pack."""

    if not isinstance(feature_set, FeatureSetSpec):
        return False
    try:
        _validate_base_ohlcv_feature_set(feature_set)
    except PackMaterializerError:
        return False
    return True


def _validate_base_ohlcv_feature_set(feature_set: FeatureSetSpec) -> None:
    features = tuple(feature_set.features)
    feature_ids = tuple(feature.feature_id for feature in features)
    if set(feature_ids) != set(BASE_OHLCV_FEATURE_IDS) or len(feature_ids) != len(
        BASE_OHLCV_FEATURE_IDS
    ):
        raise PackMaterializerError(
            "base_ohlcv fast pack requires exactly the six governed Base OHLCV features"
        )
    for feature in features:
        _validate_base_ohlcv_feature(feature)


def _validate_base_ohlcv_feature(feature: FeatureSpec) -> None:
    if not isinstance(feature, FeatureSpec):
        raise PackMaterializerError("base_ohlcv pack entries must be FeatureSpec objects")
    if feature.family is not FeatureFamily.BASE_OHLCV:
        raise PackMaterializerError("base_ohlcv pack can only contain Base OHLCV features")
    feature_name = _FEATURE_ID_TO_NAME.get(feature.feature_id)
    if feature_name is None:
        raise PackMaterializerError(f"unsupported base_ohlcv feature_id: {feature.feature_id}")
    parameters = feature.transform.parameters.to_dict()
    _require_parameter(parameters, "feature_name", feature_name, feature.feature_id)
    _require_parameter(
        parameters,
        "reset_on_session",
        BASE_OHLCV_RESET_ON_SESSION,
        feature.feature_id,
    )
    if feature.feature_id in _RETURN_FEATURE_IDS:
        _require_parameter(parameters, "horizon", BASE_OHLCV_HORIZON, feature.feature_id)
        _require_window(feature, length=BASE_OHLCV_HORIZON)
    if feature.feature_id in _ROLLING_20_FEATURE_IDS:
        _require_window(feature, length=BASE_OHLCV_WINDOW_LENGTH)
    if feature.feature_id == "base_ohlcv_rolling_volatility":
        _require_parameter(parameters, "horizon", BASE_OHLCV_HORIZON, feature.feature_id)
        _require_parameter(parameters, "ddof", BASE_OHLCV_DDOF, feature.feature_id)
    if feature.feature_id == "base_ohlcv_volume_zscore":
        _require_parameter(parameters, "ddof", BASE_OHLCV_DDOF, feature.feature_id)
        _require_parameter(
            feature.normalization.parameters.to_dict(),
            "reset_on_session",
            BASE_OHLCV_RESET_ON_SESSION,
            feature.feature_id,
        )
    expected_normalization = (
        "causal_zscore" if feature.feature_id == "base_ohlcv_volume_zscore" else "identity"
    )
    if feature.normalization.normalization_id != expected_normalization:
        raise PackMaterializerError(
            f"{feature.feature_id} normalization must be {expected_normalization}"
        )


def _require_parameter(
    parameters: Mapping[str, object],
    name: str,
    expected: object,
    feature_id: str,
) -> None:
    if parameters.get(name) != expected:
        raise PackMaterializerError(f"{feature_id} requires {name}={expected!r}")


def _require_window(feature: FeatureSpec, *, length: int) -> None:
    if feature.window.kind is not WindowKind.ROLLING or feature.window.length != length:
        raise PackMaterializerError(
            f"{feature.feature_id} requires a causal rolling window of length {length}"
        )
    if not feature.window.is_live_compatible:
        raise PackMaterializerError(f"{feature.feature_id} requires a live-compatible window")


def _base_ohlcv_expressions(polars: Any) -> dict[str, _PackExpression]:
    pl = polars
    empty_flags = _flags(pl, ())
    close = pl.col("close").cast(pl.Float64)
    high = pl.col("high").cast(pl.Float64)
    low = pl.col("low").cast(pl.Float64)
    volume = pl.col("volume").cast(pl.Float64)
    row_index = pl.int_range(0, pl.len())

    row_no_trade = _contains_flag(pl, "no_trade")
    row_primitive_gap = _contains_any_flag(pl, _PRIMITIVE_GAP_FLAGS)
    prior_close = close.shift(BASE_OHLCV_HORIZON)
    prior_primitive_gap = row_primitive_gap.shift(BASE_OHLCV_HORIZON).fill_null(False)
    prior_no_trade = row_no_trade.shift(BASE_OHLCV_HORIZON).fill_null(False)
    return_insufficient = prior_close.is_null()
    return_input_gap = row_primitive_gap | prior_primitive_gap
    return_no_trade_gap = row_no_trade | prior_no_trade
    return_zero_denominator = (prior_close == 0.0).fill_null(False)
    returns_value = (
        pl.when(return_insufficient | return_input_gap | return_zero_denominator)
        .then(None)
        .otherwise(close / prior_close - 1.0)
    )
    log_non_positive = ((close <= 0.0) | (prior_close <= 0.0)).fill_null(False)
    log_returns_value = (
        pl.when(
            return_insufficient
            | return_input_gap
            | return_zero_denominator
            | log_non_positive
        )
        .then(None)
        .otherwise((close / prior_close).log())
    )
    returns_flags = _return_flags(
        pl,
        insufficient=return_insufficient,
        input_gap=return_input_gap,
        no_trade_gap=return_no_trade_gap,
        zero_denominator=return_zero_denominator,
        non_positive=None,
        empty_flags=empty_flags,
    )
    log_returns_flags = _return_flags(
        pl,
        insufficient=return_insufficient,
        input_gap=return_input_gap,
        no_trade_gap=return_no_trade_gap,
        zero_denominator=return_zero_denominator,
        non_positive=log_non_positive,
        empty_flags=empty_flags,
    )

    return_gap = return_insufficient | return_input_gap | return_zero_denominator
    rolling_return_gap_count = _rolling_true_count(pl, return_gap)
    rolling_return_no_trade_count = _rolling_true_count(pl, return_no_trade_gap)
    rolling_return_insufficient_count = _rolling_true_count(pl, return_insufficient)
    partial_return_no_trade_count = _partial_true_count(return_no_trade_gap)
    rolling_volatility_value = (
        pl.when((row_index < BASE_OHLCV_WINDOW_LENGTH - 1) | (rolling_return_gap_count > 0))
        .then(None)
        .otherwise(
            returns_value.rolling_std(
                window_size=BASE_OHLCV_WINDOW_LENGTH,
                min_samples=BASE_OHLCV_WINDOW_LENGTH,
                ddof=BASE_OHLCV_DDOF,
            )
        )
    )
    rolling_volatility_flags = _primitive_rolling_flags(
        pl,
        row_index=row_index,
        rolling_gap_count=rolling_return_gap_count,
        rolling_no_trade_count=rolling_return_no_trade_count,
        rolling_insufficient_count=rolling_return_insufficient_count,
        partial_no_trade_count=partial_return_no_trade_count,
        empty_flags=empty_flags,
    )

    rolling_no_trade_count = _rolling_true_count(pl, row_no_trade)
    rolling_range_raw = (
        high.rolling_max(
            window_size=BASE_OHLCV_WINDOW_LENGTH,
            min_samples=BASE_OHLCV_WINDOW_LENGTH,
        )
        - low.rolling_min(
            window_size=BASE_OHLCV_WINDOW_LENGTH,
            min_samples=BASE_OHLCV_WINDOW_LENGTH,
        )
    )
    rolling_range_value = (
        pl.when((row_index < BASE_OHLCV_WINDOW_LENGTH - 1) | (rolling_no_trade_count > 0))
        .then(None)
        .otherwise(rolling_range_raw)
    )
    rolling_ohlcv_flags = _ohlcv_rolling_flags(
        pl,
        row_index=row_index,
        rolling_no_trade_count=rolling_no_trade_count,
        empty_flags=empty_flags,
    )

    rolling_low = low.rolling_min(
        window_size=BASE_OHLCV_WINDOW_LENGTH,
        min_samples=BASE_OHLCV_WINDOW_LENGTH,
    )
    rolling_high = high.rolling_max(
        window_size=BASE_OHLCV_WINDOW_LENGTH,
        min_samples=BASE_OHLCV_WINDOW_LENGTH,
    )
    rolling_high_low_range = rolling_high - rolling_low
    range_zero = rolling_high_low_range == 0.0
    range_position_value = (
        pl.when(
            (row_index < BASE_OHLCV_WINDOW_LENGTH - 1)
            | (rolling_no_trade_count > 0)
            | range_zero
        )
        .then(None)
        .otherwise((close - rolling_low) / rolling_high_low_range)
    )
    range_position_flags = (
        pl.when(row_index < BASE_OHLCV_WINDOW_LENGTH - 1)
        .then(_flags(pl, ("insufficient_window", "ohlcv_gap")))
        .when(rolling_no_trade_count > 0)
        .then(_flags(pl, ("input_gap", "no_trade", "ohlcv_gap")))
        .when(range_zero)
        .then(_flags(pl, ("ohlcv_gap", "zero_range")))
        .otherwise(empty_flags)
    )

    volume_gap_count = _rolling_true_count(pl, row_primitive_gap)
    volume_no_trade_count = _rolling_true_count(pl, row_no_trade)
    partial_volume_no_trade_count = _partial_true_count(row_no_trade)
    volume_mean = volume.rolling_mean(
        window_size=BASE_OHLCV_WINDOW_LENGTH,
        min_samples=BASE_OHLCV_WINDOW_LENGTH,
    )
    volume_std = volume.rolling_std(
        window_size=BASE_OHLCV_WINDOW_LENGTH,
        min_samples=BASE_OHLCV_WINDOW_LENGTH,
        ddof=BASE_OHLCV_DDOF,
    )
    # Robust zero-variance detection (constant window) -- see constant_window_mask.
    volume_zero_variance = constant_window_mask(volume, window=BASE_OHLCV_WINDOW_LENGTH)
    volume_zscore_value = (
        pl.when(
            (row_index < BASE_OHLCV_WINDOW_LENGTH - 1)
            | (volume_gap_count > 0)
            | volume_zero_variance
        )
        .then(None)
        .otherwise((volume - volume_mean) / volume_std)
    )
    volume_zscore_flags = (
        pl.when(row_index < BASE_OHLCV_WINDOW_LENGTH - 1)
        .then(
            pl.when(partial_volume_no_trade_count > 0)
            .then(_flags(pl, ("insufficient_window", "no_trade", "primitive_gap")))
            .otherwise(_flags(pl, ("insufficient_window", "primitive_gap")))
        )
        .when(volume_gap_count > 0)
        .then(
            pl.when(volume_no_trade_count > 0)
            .then(_flags(pl, ("input_gap", "no_trade", "primitive_gap")))
            .otherwise(_flags(pl, ("input_gap", "primitive_gap")))
        )
        .when(volume_zero_variance)
        .then(_flags(pl, ("primitive_gap", "zero_variance")))
        .otherwise(empty_flags)
    )

    return {
        "base_ohlcv_returns": _PackExpression(returns_value, returns_flags),
        "base_ohlcv_log_returns": _PackExpression(log_returns_value, log_returns_flags),
        "base_ohlcv_rolling_volatility": _PackExpression(
            rolling_volatility_value,
            rolling_volatility_flags,
        ),
        "base_ohlcv_rolling_range": _PackExpression(rolling_range_value, rolling_ohlcv_flags),
        "base_ohlcv_range_position": _PackExpression(
            range_position_value,
            range_position_flags,
        ),
        "base_ohlcv_volume_zscore": _PackExpression(volume_zscore_value, volume_zscore_flags),
    }


def _return_flags(
    polars: Any,
    *,
    insufficient: Any,
    input_gap: Any,
    no_trade_gap: Any,
    zero_denominator: Any,
    non_positive: Any | None,
    empty_flags: Any,
) -> Any:
    pl = polars
    flags = (
        pl.when(insufficient)
        .then(_flags(pl, ("insufficient_window", "primitive_gap")))
        .when(input_gap)
        .then(
            pl.when(no_trade_gap)
            .then(_flags(pl, ("input_gap", "no_trade", "primitive_gap")))
            .otherwise(_flags(pl, ("input_gap", "primitive_gap")))
        )
        .when(zero_denominator)
        .then(_flags(pl, ("primitive_gap", "zero_denominator")))
    )
    if non_positive is not None:
        flags = flags.when(non_positive).then(_flags(pl, ("non_positive_price", "primitive_gap")))
    return flags.otherwise(empty_flags)


def _primitive_rolling_flags(
    polars: Any,
    *,
    row_index: Any,
    rolling_gap_count: Any,
    rolling_no_trade_count: Any,
    rolling_insufficient_count: Any,
    partial_no_trade_count: Any,
    empty_flags: Any,
) -> Any:
    pl = polars
    return (
        pl.when(row_index < BASE_OHLCV_WINDOW_LENGTH - 1)
        .then(
            pl.when(partial_no_trade_count > 0)
            .then(
                _flags(
                    pl,
                    (
                        "input_gap",
                        "insufficient_window",
                        "no_trade",
                        "primitive_gap",
                    ),
                )
            )
            .otherwise(_flags(pl, ("insufficient_window", "primitive_gap")))
        )
        .when(rolling_gap_count > 0)
        .then(
            pl.when((rolling_no_trade_count > 0) & (rolling_insufficient_count > 0))
            .then(
                _flags(
                    pl,
                    (
                        "input_gap",
                        "insufficient_window",
                        "no_trade",
                        "primitive_gap",
                    ),
                )
            )
            .when(rolling_no_trade_count > 0)
            .then(_flags(pl, ("input_gap", "no_trade", "primitive_gap")))
            .when(rolling_insufficient_count > 0)
            .then(_flags(pl, ("input_gap", "insufficient_window", "primitive_gap")))
            .otherwise(_flags(pl, ("input_gap", "primitive_gap")))
        )
        .otherwise(empty_flags)
    )


def _ohlcv_rolling_flags(
    polars: Any,
    *,
    row_index: Any,
    rolling_no_trade_count: Any,
    empty_flags: Any,
) -> Any:
    pl = polars
    return (
        pl.when(row_index < BASE_OHLCV_WINDOW_LENGTH - 1)
        .then(_flags(pl, ("insufficient_window", "ohlcv_gap")))
        .when(rolling_no_trade_count > 0)
        .then(_flags(pl, ("input_gap", "no_trade", "ohlcv_gap")))
        .otherwise(empty_flags)
    )


def _rolling_true_count(polars: Any, condition: Any) -> Any:
    return (
        condition.cast(polars.Int64)
        .rolling_sum(
            window_size=BASE_OHLCV_WINDOW_LENGTH,
            min_samples=BASE_OHLCV_WINDOW_LENGTH,
        )
        .fill_null(0)
    )


def _partial_true_count(condition: Any) -> Any:
    return condition.cast(int).cum_sum().fill_null(0)


def _contains_any_flag(polars: Any, flags: Sequence[str]) -> Any:
    result = _contains_flag(polars, flags[0])
    for flag in flags[1:]:
        result = result | _contains_flag(polars, flag)
    return result


def _contains_flag(polars: Any, flag: str) -> Any:
    return polars.col("quality_flags").list.contains(flag).fill_null(False)


def _flags(polars: Any, values: Sequence[str]) -> Any:
    return polars.lit(list(values), dtype=polars.List(polars.Utf8))


__all__ = [
    "BASE_OHLCV_DDOF",
    "BASE_OHLCV_FEATURE_IDS",
    "BASE_OHLCV_HORIZON",
    "BASE_OHLCV_RESET_ON_SESSION",
    "BASE_OHLCV_WINDOW_LENGTH",
    "build_base_ohlcv_pack",
    "supports_base_ohlcv_pack",
]
