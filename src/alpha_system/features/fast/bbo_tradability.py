"""BBO tradability / top-book Polars pack for the V1 fast path."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from alpha_system.data.foundation.quotes import (
    BBO_QUARANTINE_QUALITY_FLAG,
    MISSING_BBO_QUALITY_FLAG,
)
from alpha_system.data.storage import require_dependency
from alpha_system.features.contracts import (
    FeatureFamily,
    FeatureSetSpec,
    FeatureSpec,
    WindowKind,
)
from alpha_system.features.families.bbo import BBOFeatureName
from alpha_system.features.fast.materializer import (
    FastFeatureDeclaration,
    FastFeaturePack,
    PackMaterializerError,
    constant_window_mask,
)

BBO_TRADABILITY_WINDOW_LENGTH = 3
BBO_TRADABILITY_DDOF = 0
BBO_TRADABILITY_RESET_ON_SESSION = True
BBO_TRADABILITY_WIDE_SPREAD_BPS_THRESHOLD = 25.0
BBO_TRADABILITY_LOW_DEPTH_THRESHOLD = 1.0
BBO_TRADABILITY_FEATURE_IDS: tuple[str, ...] = tuple(
    f"bbo_tradability_{feature_name.value}" for feature_name in BBOFeatureName
)

_FEATURE_ID_TO_NAME: dict[str, BBOFeatureName] = {
    f"bbo_tradability_{feature_name.value}": feature_name for feature_name in BBOFeatureName
}
_POINT_IN_TIME_FEATURES = frozenset(
    feature_name
    for feature_name in BBOFeatureName
    if feature_name is not BBOFeatureName.SPREAD_ZSCORE
)
_POINT_FLAG_TOKENS = (
    "bbo_gap",
    MISSING_BBO_QUALITY_FLAG,
    BBO_QUARANTINE_QUALITY_FLAG,
    "bbo_invariant_violation",
    "input_gap",
    "no_trade",
)

_PREFIX = "__fbt"
_SESSION = f"{_PREFIX}_session_label"
_SEGMENT_START = f"{_PREFIX}_segment_start"
_SEGMENT = f"{_PREFIX}_segment"
_INPUT_FLAGS = f"{_PREFIX}_input_quality_flags"
_EVENT_TS = f"{_PREFIX}_event_ts"
_AVAILABLE_TS = f"{_PREFIX}_available_ts"
_BAR_END_TS = f"{_PREFIX}_bar_end_ts"
_BID = f"{_PREFIX}_bid"
_ASK = f"{_PREFIX}_ask"
_BID_SIZE = f"{_PREFIX}_bid_size"
_ASK_SIZE = f"{_PREFIX}_ask_size"
_MID = f"{_PREFIX}_mid"
_SPREAD = f"{_PREFIX}_spread"
_SPREAD_TICKS = f"{_PREFIX}_spread_ticks"
_MICROPRICE_STORED = f"{_PREFIX}_microprice_stored"
_MISSING_BBO = f"{_PREFIX}_missing_bbo"
_BBO_QUARANTINED = f"{_PREFIX}_bbo_quarantined"
_INVARIANTS_HOLD = f"{_PREFIX}_invariants_hold"
_VALID_QUOTE = f"{_PREFIX}_valid_quote"
_VALID_SIZES = f"{_PREFIX}_valid_sizes"
_POINT_FLAGS = f"{_PREFIX}_point_flags"
_SPREAD_POINT = f"{_PREFIX}_spread_point"


@dataclass(frozen=True, slots=True)
class _PackExpression:
    value: Any
    flags: Any


def build_bbo_tradability_pack(feature_set: FeatureSetSpec) -> FastFeaturePack:
    """Build the governed BBO tradability fast pack."""

    if not isinstance(feature_set, FeatureSetSpec):
        raise PackMaterializerError("bbo_tradability fast pack requires a FeatureSetSpec")
    _validate_bbo_feature_set(feature_set)
    polars = require_dependency("polars")
    expressions = _bbo_expressions(polars, feature_set.features)
    return FastFeaturePack(
        feature_set=feature_set,
        declarations=tuple(
            FastFeatureDeclaration(
                feature_spec=feature,
                value_expr=expressions[feature.feature_id].value,
                quality_flags_expr=expressions[feature.feature_id].flags,
                event_ts_expr=polars.col(_EVENT_TS),
                available_ts_expr=polars.col(_AVAILABLE_TS),
            )
            for feature in feature_set.features
        ),
        prepare_frame=_prepare_frame,
    )


def supports_bbo_tradability_pack(feature_set: FeatureSetSpec) -> bool:
    """Return true when a feature set is a governed BBO pack subset."""

    if not isinstance(feature_set, FeatureSetSpec):
        return False
    try:
        _validate_bbo_feature_set(feature_set)
    except PackMaterializerError:
        return False
    return True


def _validate_bbo_feature_set(feature_set: FeatureSetSpec) -> None:
    features = tuple(feature_set.features)
    if not features:
        raise PackMaterializerError("bbo_tradability fast pack requires features")
    feature_ids = tuple(feature.feature_id for feature in features)
    if len(set(feature_ids)) != len(feature_ids):
        raise PackMaterializerError("bbo_tradability fast pack rejects duplicate features")
    unknown = tuple(
        feature_id for feature_id in feature_ids if feature_id not in BBO_TRADABILITY_FEATURE_IDS
    )
    if unknown:
        raise PackMaterializerError(
            "bbo_tradability fast pack requires governed BBO features: "
            + ", ".join(unknown)
        )
    for feature in features:
        _validate_bbo_feature(feature)


def _validate_bbo_feature(feature: FeatureSpec) -> None:
    if not isinstance(feature, FeatureSpec):
        raise PackMaterializerError("bbo_tradability pack entries must be FeatureSpec objects")
    if feature.family is not FeatureFamily.BBO_TRADABILITY:
        raise PackMaterializerError(
            "bbo_tradability pack can only contain BBO Tradability features"
        )
    feature_name = _FEATURE_ID_TO_NAME.get(feature.feature_id)
    if feature_name is None:
        raise PackMaterializerError(f"unsupported bbo_tradability feature_id: {feature.feature_id}")
    parameters = feature.transform.parameters.to_dict()
    _require_parameter(parameters, "feature_name", feature_name.value, feature.feature_id)
    _require_quality_tokens(parameters, feature.feature_id)
    expected_transform = _expected_transform_id(feature_name)
    if feature.transform.transform_id != expected_transform:
        raise PackMaterializerError(
            f"{feature.feature_id} transform must be {expected_transform}"
        )
    if feature_name is BBOFeatureName.SPREAD_ZSCORE:
        window_length = _declared_rolling_window_length(feature)
        _require_rolling_window(feature, length=window_length)
        _require_parameter(
            parameters,
            "window_length",
            window_length,
            feature.feature_id,
        )
        _require_parameter(
            parameters,
            "reset_on_session",
            BBO_TRADABILITY_RESET_ON_SESSION,
            feature.feature_id,
        )
        _require_parameter(parameters, "ddof", BBO_TRADABILITY_DDOF, feature.feature_id)
        _require_parameter(
            feature.normalization.parameters.to_dict(),
            "reset_on_session",
            BBO_TRADABILITY_RESET_ON_SESSION,
            feature.feature_id,
        )
        _require_parameter(
            feature.normalization.parameters.to_dict(),
            "ddof",
            BBO_TRADABILITY_DDOF,
            feature.feature_id,
        )
        if feature.normalization.normalization_id != "causal_zscore":
            raise PackMaterializerError(
                f"{feature.feature_id} normalization must be causal_zscore"
            )
        return
    if feature_name in _POINT_IN_TIME_FEATURES:
        _require_point_in_time_window(feature)
        if feature.normalization.normalization_id != "identity":
            raise PackMaterializerError(f"{feature.feature_id} normalization must be identity")
    if feature_name is BBOFeatureName.WIDE_SPREAD_FLAG:
        _require_parameter(
            parameters,
            "wide_spread_bps_threshold",
            BBO_TRADABILITY_WIDE_SPREAD_BPS_THRESHOLD,
            feature.feature_id,
        )
    if feature_name is BBOFeatureName.LOW_DEPTH_FLAG:
        _require_parameter(
            parameters,
            "low_depth_threshold",
            BBO_TRADABILITY_LOW_DEPTH_THRESHOLD,
            feature.feature_id,
        )


def _expected_transform_id(feature_name: BBOFeatureName) -> str:
    return {
        BBOFeatureName.MID: "identity",
        BBOFeatureName.SPREAD: "identity",
        BBOFeatureName.SPREAD_TICKS: "identity",
        BBOFeatureName.SPREAD_BPS: "spread_bps",
        BBOFeatureName.SPREAD_ZSCORE: "identity",
        BBOFeatureName.BID_SIZE: "identity",
        BBOFeatureName.ASK_SIZE: "identity",
        BBOFeatureName.TOP_BOOK_DEPTH: "top_book_depth",
        BBOFeatureName.TOP_BOOK_IMBALANCE: "top_book_imbalance",
        BBOFeatureName.MICROPRICE: "microprice",
        BBOFeatureName.MICROPRICE_MINUS_MID: "microprice_minus_mid",
        BBOFeatureName.MISSING_BBO_FLAG: "missing_bbo_flag",
        BBOFeatureName.BAD_QUOTE_FLAG: "bad_quote_flag",
        BBOFeatureName.WIDE_SPREAD_FLAG: "wide_spread_flag",
        BBOFeatureName.LOW_DEPTH_FLAG: "low_depth_flag",
    }[feature_name]


def _require_parameter(
    parameters: Mapping[str, object],
    name: str,
    expected: object,
    feature_id: str,
) -> None:
    if parameters.get(name) != expected:
        raise PackMaterializerError(f"{feature_id} requires {name}={expected!r}")


def _require_quality_tokens(parameters: Mapping[str, object], feature_id: str) -> None:
    tokens = parameters.get("quality_tokens")
    if not isinstance(tokens, Sequence) or isinstance(tokens, str):
        raise PackMaterializerError(f"{feature_id} requires governed quality_tokens")
    if tuple(tokens) != (MISSING_BBO_QUALITY_FLAG, BBO_QUARANTINE_QUALITY_FLAG):
        raise PackMaterializerError(f"{feature_id} requires governed BBO quality tokens")


def _require_rolling_window(feature: FeatureSpec, *, length: int) -> None:
    if feature.window.kind is not WindowKind.ROLLING or feature.window.length != length:
        raise PackMaterializerError(
            f"{feature.feature_id} requires a causal rolling window of length {length}"
        )
    if not feature.window.is_live_compatible:
        raise PackMaterializerError(f"{feature.feature_id} requires a live-compatible window")


def _declared_rolling_window_length(feature: FeatureSpec) -> int:
    length = feature.window.length
    if not isinstance(length, int) or length <= 0:
        raise PackMaterializerError(
            f"{feature.feature_id} requires a positive rolling window length"
        )
    return length


def _require_point_in_time_window(feature: FeatureSpec) -> None:
    if feature.window.kind is not WindowKind.POINT_IN_TIME or feature.window.length != 1:
        raise PackMaterializerError(f"{feature.feature_id} requires a point-in-time window")
    if not feature.window.is_live_compatible:
        raise PackMaterializerError(f"{feature.feature_id} requires a live-compatible window")


def _prepare_frame(frame: Any) -> Any:
    pl = require_dependency("polars")
    _require_columns(
        frame,
        (
            "series_id",
            "event_ts",
            "available_ts",
            "bar_end_ts",
            "quality_flags",
            "session_label",
            "bid",
            "ask",
            "bid_size",
            "ask_size",
            "mid",
            "spread",
        ),
    )
    prepared = frame.with_columns(
        (
            pl.col("session_label").cast(pl.Utf8).alias(_SESSION),
            pl.col("event_ts").cast(pl.Datetime("us", "UTC"), strict=False).alias(_EVENT_TS),
            pl.col("available_ts")
            .cast(pl.Datetime("us", "UTC"), strict=False)
            .alias(_AVAILABLE_TS),
            pl.col("bar_end_ts").cast(pl.Datetime("us", "UTC"), strict=False).alias(_BAR_END_TS),
            _input_quality_flags(pl).alias(_INPUT_FLAGS),
            pl.col("bid").cast(pl.Float64, strict=False).alias(_BID),
            pl.col("ask").cast(pl.Float64, strict=False).alias(_ASK),
            pl.col("bid_size").cast(pl.Float64, strict=False).alias(_BID_SIZE),
            pl.col("ask_size").cast(pl.Float64, strict=False).alias(_ASK_SIZE),
            pl.col("mid").cast(pl.Float64, strict=False).alias(_MID),
            pl.col("spread").cast(pl.Float64, strict=False).alias(_SPREAD),
            _optional_float_column(pl, frame, "spread_ticks").alias(_SPREAD_TICKS),
            _optional_float_column(pl, frame, "microprice").alias(_MICROPRICE_STORED),
        )
    )
    prepared = prepared.with_columns(
        (
            _contains_flag(pl, MISSING_BBO_QUALITY_FLAG).alias(_MISSING_BBO),
            _contains_flag(pl, BBO_QUARANTINE_QUALITY_FLAG).alias(_BBO_QUARANTINED),
            _quote_invariants_hold(pl).alias(_INVARIANTS_HOLD),
        )
    )
    prepared = prepared.with_columns(
        (
            (
                ~(pl.col(_MISSING_BBO) | pl.col(_BBO_QUARANTINED))
                & pl.col(_INVARIANTS_HOLD)
            ).alias(_VALID_QUOTE),
            (
                (pl.col(_BID_SIZE) > 0.0)
                & (pl.col(_ASK_SIZE) > 0.0)
                & ((pl.col(_BID_SIZE) + pl.col(_ASK_SIZE)) > 0.0)
            )
            .fill_null(False)
            .alias(_VALID_SIZES),
        )
    )
    prepared = prepared.with_columns(
        (
            pl.when(pl.col(_VALID_QUOTE))
            .then(_flags(pl, ()))
            .otherwise(_bbo_gap_flags(pl))
            .alias(_POINT_FLAGS),
            pl.when(pl.col(_VALID_QUOTE))
            .then(pl.col(_SPREAD))
            .otherwise(None)
            .alias(_SPREAD_POINT),
        )
    )
    segment_start = (pl.col(_SESSION) != pl.col(_SESSION).shift(1)).fill_null(True)
    return (
        prepared.with_columns(segment_start.alias(_SEGMENT_START))
        .with_columns(pl.col(_SEGMENT_START).cast(pl.Int64).cum_sum().alias(_SEGMENT))
        .sort(_AVAILABLE_TS)
    )


def _quote_invariants_hold(polars: Any) -> Any:
    pl = polars
    required_present = (
        pl.col(_BID).is_not_null()
        & pl.col(_ASK).is_not_null()
        & pl.col(_BID_SIZE).is_not_null()
        & pl.col(_ASK_SIZE).is_not_null()
        & pl.col(_MID).is_not_null()
        & pl.col(_SPREAD).is_not_null()
        & pl.col(_AVAILABLE_TS).is_not_null()
        & pl.col(_BAR_END_TS).is_not_null()
    )
    arithmetic = (
        (pl.col(_ASK) >= pl.col(_BID))
        & ((pl.col(_MID) - ((pl.col(_BID) + pl.col(_ASK)) / 2.0)).abs() <= 1e-9)
        & ((pl.col(_SPREAD) - (pl.col(_ASK) - pl.col(_BID))).abs() <= 1e-9)
        & (pl.col(_AVAILABLE_TS) >= pl.col(_BAR_END_TS))
    )
    stored_microprice_valid = (
        pl.col(_MICROPRICE_STORED).is_null()
        | (
            (pl.col(_BID_SIZE) > 0.0)
            & (pl.col(_ASK_SIZE) > 0.0)
            & (pl.col(_BID) <= pl.col(_MICROPRICE_STORED))
            & (pl.col(_MICROPRICE_STORED) <= pl.col(_ASK))
        )
    )
    return (required_present & arithmetic & stored_microprice_valid).fill_null(False)


def _bbo_expressions(
    polars: Any,
    features: Sequence[FeatureSpec],
) -> dict[str, _PackExpression]:
    expressions: dict[str, _PackExpression] = {}
    for feature in features:
        expressions[feature.feature_id] = _bbo_expression(polars, feature)
    return expressions


def _bbo_expression(polars: Any, feature: FeatureSpec) -> _PackExpression:
    pl = polars
    feature_name = _FEATURE_ID_TO_NAME[feature.feature_id]
    spread_bps = pl.col(_SPREAD) / pl.col(_MID) * 10_000.0
    top_book_depth = pl.col(_BID_SIZE) + pl.col(_ASK_SIZE)
    size_denominator = pl.col(_BID_SIZE) + pl.col(_ASK_SIZE)
    top_book_imbalance = (pl.col(_BID_SIZE) - pl.col(_ASK_SIZE)) / size_denominator
    microprice = (pl.col(_ASK) * pl.col(_BID_SIZE) + pl.col(_BID) * pl.col(_ASK_SIZE)) / (
        size_denominator
    )

    if feature_name is BBOFeatureName.MID:
        return _valid_quote_expression(pl, pl.col(_MID))
    if feature_name is BBOFeatureName.SPREAD:
        return _valid_quote_expression(pl, pl.col(_SPREAD))
    if feature_name is BBOFeatureName.SPREAD_TICKS:
        missing_ticks = pl.col(_SPREAD_TICKS).is_null()
        return _conditional_quote_expression(
            pl,
            pl.col(_SPREAD_TICKS),
            invalid=missing_ticks,
            reason="missing_spread_ticks",
        )
    if feature_name is BBOFeatureName.SPREAD_BPS:
        zero_or_negative_mid = (pl.col(_MID) <= 0.0).fill_null(True)
        return _conditional_quote_expression(
            pl,
            spread_bps,
            invalid=zero_or_negative_mid,
            reason="zero_or_negative_mid",
        )
    if feature_name is BBOFeatureName.SPREAD_ZSCORE:
        return _spread_zscore_expression(pl, _declared_rolling_window_length(feature))
    if feature_name is BBOFeatureName.BID_SIZE:
        return _valid_quote_expression(pl, pl.col(_BID_SIZE))
    if feature_name is BBOFeatureName.ASK_SIZE:
        return _valid_quote_expression(pl, pl.col(_ASK_SIZE))
    if feature_name is BBOFeatureName.TOP_BOOK_DEPTH:
        return _valid_quote_expression(pl, top_book_depth)
    if feature_name is BBOFeatureName.TOP_BOOK_IMBALANCE:
        return _conditional_quote_expression(
            pl,
            top_book_imbalance,
            invalid=~pl.col(_VALID_SIZES),
            reason="invalid_bbo_size",
        )
    if feature_name is BBOFeatureName.MICROPRICE:
        return _conditional_quote_expression(
            pl,
            microprice,
            invalid=~pl.col(_VALID_SIZES),
            reason="invalid_bbo_size",
        )
    if feature_name is BBOFeatureName.MICROPRICE_MINUS_MID:
        return _conditional_quote_expression(
            pl,
            microprice - pl.col(_MID),
            invalid=~pl.col(_VALID_SIZES),
            reason="invalid_bbo_size",
        )
    if feature_name is BBOFeatureName.MISSING_BBO_FLAG:
        return _flag_expression(pl, pl.col(_MISSING_BBO), (MISSING_BBO_QUALITY_FLAG,))
    if feature_name is BBOFeatureName.BAD_QUOTE_FLAG:
        missing_or_abnormal = pl.col(_MISSING_BBO) | pl.col(_BBO_QUARANTINED)
        flags = pl.concat_list(
            _conditional_flags(pl, pl.col(_MISSING_BBO), (MISSING_BBO_QUALITY_FLAG,)),
            _conditional_flags(pl, pl.col(_BBO_QUARANTINED), (BBO_QUARANTINE_QUALITY_FLAG,)),
        ).list.unique(maintain_order=True)
        return _PackExpression(
            pl.when(missing_or_abnormal).then(1).otherwise(0),
            flags,
        )
    if feature_name is BBOFeatureName.WIDE_SPREAD_FLAG:
        zero_or_negative_mid = (pl.col(_MID) <= 0.0).fill_null(True)
        value = (
            pl.when(~pl.col(_VALID_QUOTE) | zero_or_negative_mid)
            .then(None)
            .otherwise(
                pl.when(spread_bps > BBO_TRADABILITY_WIDE_SPREAD_BPS_THRESHOLD)
                .then(1)
                .otherwise(0)
            )
        )
        flags = (
            pl.when(~pl.col(_VALID_QUOTE))
            .then(_bbo_gap_flags(pl))
            .when(zero_or_negative_mid)
            .then(_quote_gap_flags(pl, "zero_or_negative_mid"))
            .otherwise(_flags(pl, ()))
        )
        return _PackExpression(value, flags)
    if feature_name is BBOFeatureName.LOW_DEPTH_FLAG:
        value = (
            pl.when(~pl.col(_VALID_QUOTE))
            .then(None)
            .otherwise(
                pl.when(top_book_depth < BBO_TRADABILITY_LOW_DEPTH_THRESHOLD)
                .then(1)
                .otherwise(0)
            )
        )
        flags = pl.when(~pl.col(_VALID_QUOTE)).then(_bbo_gap_flags(pl)).otherwise(_flags(pl, ()))
        return _PackExpression(value, flags)
    raise PackMaterializerError(f"unsupported BBO feature: {feature_name}")


def _valid_quote_expression(polars: Any, raw_value: Any) -> _PackExpression:
    value = polars.when(~polars.col(_VALID_QUOTE)).then(None).otherwise(raw_value)
    flags = polars.when(~polars.col(_VALID_QUOTE)).then(_bbo_gap_flags(polars)).otherwise(
        _flags(polars, ())
    )
    return _PackExpression(value, flags)


def _conditional_quote_expression(
    polars: Any,
    raw_value: Any,
    *,
    invalid: Any,
    reason: str,
) -> _PackExpression:
    value = (
        polars.when(~polars.col(_VALID_QUOTE) | invalid)
        .then(None)
        .otherwise(raw_value)
    )
    flags = (
        polars.when(~polars.col(_VALID_QUOTE))
        .then(_bbo_gap_flags(polars))
        .when(invalid)
        .then(_quote_gap_flags(polars, reason))
        .otherwise(_flags(polars, ()))
    )
    return _PackExpression(value, flags)


def _spread_zscore_expression(polars: Any, window: int) -> _PackExpression:
    pl = polars
    group_position = _group_position(pl)
    rolling_gap_count = _rolling_true_count(pl.col(_SPREAD_POINT).is_null(), window, polars=pl)
    flag_counts = {
        flag: _rolling_true_count(_point_has_flag(pl, flag), window, polars=pl)
        for flag in _POINT_FLAG_TOKENS
    }
    mean = (
        pl.col(_SPREAD_POINT)
        .rolling_mean(window_size=window, min_samples=window)
        .over(_SEGMENT)
    )
    std = (
        pl.col(_SPREAD_POINT)
        .rolling_std(
            window_size=window,
            min_samples=window,
            ddof=BBO_TRADABILITY_DDOF,
        )
        .over(_SEGMENT)
    )
    insufficient = group_position < window
    # Robust zero-variance detection (constant window) -- see constant_window_mask.
    zero_variance = constant_window_mask(
        pl.col(_SPREAD_POINT), window=window, group=_SEGMENT
    ).fill_null(False)
    value = (
        pl.when(insufficient | (rolling_gap_count > 0) | zero_variance)
        .then(None)
        .otherwise((pl.col(_SPREAD_POINT) - mean) / std)
    )
    flags = (
        pl.when(insufficient)
        .then(
            _primitive_gap_flags(
                pl,
                ("insufficient_window",),
                flag_counts=flag_counts,
            )
        )
        .when(rolling_gap_count > 0)
        .then(_primitive_gap_flags(pl, ("input_gap",), flag_counts=flag_counts))
        .when(zero_variance)
        .then(_primitive_gap_flags(pl, ("zero_variance",), flag_counts=flag_counts))
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _flag_expression(polars: Any, condition: Any, values: Sequence[str]) -> _PackExpression:
    return _PackExpression(
        polars.when(condition).then(1).otherwise(0),
        polars.when(condition).then(_flags(polars, values)).otherwise(_flags(polars, ())),
    )


def _bbo_gap_flags(polars: Any) -> Any:
    pl = polars
    return pl.concat_list(
        _flags(pl, ("bbo_gap",)),
        pl.col(_INPUT_FLAGS),
        _conditional_flags(pl, pl.col(_MISSING_BBO), (MISSING_BBO_QUALITY_FLAG,)),
        _conditional_flags(pl, pl.col(_BBO_QUARANTINED), (BBO_QUARANTINE_QUALITY_FLAG,)),
        _conditional_flags(pl, ~pl.col(_INVARIANTS_HOLD), ("bbo_invariant_violation",)),
    ).list.unique().list.sort()


def _quote_gap_flags(polars: Any, reason: str) -> Any:
    return (
        polars.concat_list(_bbo_gap_flags(polars), _flags(polars, (reason,)))
        .list.unique()
        .list.sort()
    )


def _primitive_gap_flags(
    polars: Any,
    reasons: Sequence[str],
    *,
    flag_counts: Mapping[str, Any],
) -> Any:
    fragments = [_flags(polars, ("primitive_gap", *reasons))]
    for flag in _POINT_FLAG_TOKENS:
        fragments.append(_conditional_flags(polars, flag_counts[flag] > 0, (flag,)))
    return polars.concat_list(*fragments).list.unique().list.sort()


def _conditional_flags(polars: Any, condition: Any, values: Sequence[str]) -> Any:
    return polars.when(condition).then(_flags(polars, values)).otherwise(_flags(polars, ()))


def _rolling_true_count(condition: Any, window: int, *, polars: Any) -> Any:
    return (
        condition.cast(polars.Int64)
        .rolling_sum(window_size=window, min_samples=1)
        .over(_SEGMENT)
        .fill_null(0)
    )


def _group_position(polars: Any) -> Any:
    return polars.col(_AVAILABLE_TS).cum_count().over(_SEGMENT).cast(polars.Int64)


def _point_has_flag(polars: Any, flag: str) -> Any:
    return polars.col(_POINT_FLAGS).list.contains(flag).fill_null(False)


def _contains_flag(polars: Any, flag: str) -> Any:
    return polars.col(_INPUT_FLAGS).list.contains(flag).fill_null(False)


def _input_quality_flags(polars: Any) -> Any:
    pl = polars
    return (
        pl.col("quality_flags")
        .cast(pl.List(pl.Utf8), strict=False)
        .fill_null(_flags(pl, ()))
        .list.eval(pl.element().str.to_lowercase())
        .list.unique(maintain_order=True)
    )


def _optional_float_column(polars: Any, frame: Any, column: str) -> Any:
    if column not in frame.columns:
        return polars.lit(None, dtype=polars.Float64)
    return polars.col(column).cast(polars.Float64, strict=False)


def _flags(polars: Any, values: Sequence[str]) -> Any:
    return polars.lit(list(values), dtype=polars.List(polars.Utf8))


def _require_columns(frame: Any, columns: Sequence[str]) -> None:
    missing = tuple(column for column in columns if column not in frame.columns)
    if missing:
        raise PackMaterializerError("canonical frame missing columns: " + ", ".join(missing))


__all__ = [
    "BBO_TRADABILITY_DDOF",
    "BBO_TRADABILITY_FEATURE_IDS",
    "BBO_TRADABILITY_LOW_DEPTH_THRESHOLD",
    "BBO_TRADABILITY_RESET_ON_SESSION",
    "BBO_TRADABILITY_WIDE_SPREAD_BPS_THRESHOLD",
    "BBO_TRADABILITY_WINDOW_LENGTH",
    "build_bbo_tradability_pack",
    "supports_bbo_tradability_pack",
]
