"""Cross-market ES/NQ/RTY aligned-panel Polars pack for the V1 fast path."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from alpha_system.data.foundation.sources import DataFoundationValidationError
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
from alpha_system.features.families.cross_market import CrossMarketFeatureName
from alpha_system.features.fast.materializer import (
    FastFeatureDeclaration,
    FastFeaturePack,
    PackMaterializerError,
    constant_window_mask,
)
from alpha_system.features.session_truth import (
    SessionTruthClock,
    session_contract_parameters,
    session_truth_clock,
)

_MARKETS: tuple[str, str, str] = ("ES", "NQ", "RTY")
_ENTITY_ID = "ES:NQ:RTY"
_DEFAULT_HORIZON = 1

CROSS_MARKET_FEATURE_IDS: tuple[str, ...] = tuple(
    f"cross_market_{feature_name.value}" for feature_name in CrossMarketFeatureName
)

_FEATURE_ID_TO_NAME: dict[str, CrossMarketFeatureName] = {
    f"cross_market_{feature_name.value}": feature_name
    for feature_name in CrossMarketFeatureName
}
_ROLLING_FEATURES = frozenset(
    {
        CrossMarketFeatureName.NQ_ES_ROLLING_BETA_RESIDUAL,
        CrossMarketFeatureName.RTY_ES_ROLLING_BETA_RESIDUAL,
        CrossMarketFeatureName.NQ_ES_ROLLING_CORRELATION,
        CrossMarketFeatureName.RTY_ES_ROLLING_CORRELATION,
    }
)
_POINT_FEATURES = frozenset(set(CrossMarketFeatureName) - set(_ROLLING_FEATURES))
_SPREAD_PAIRS = {
    CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD: ("NQ", "ES"),
    CrossMarketFeatureName.RTY_MINUS_ES_RETURN_SPREAD: ("RTY", "ES"),
}
_ROLLING_PAIRS = {
    CrossMarketFeatureName.NQ_ES_ROLLING_BETA_RESIDUAL: ("NQ", "ES"),
    CrossMarketFeatureName.NQ_ES_ROLLING_CORRELATION: ("NQ", "ES"),
    CrossMarketFeatureName.RTY_ES_ROLLING_BETA_RESIDUAL: ("RTY", "ES"),
    CrossMarketFeatureName.RTY_ES_ROLLING_CORRELATION: ("RTY", "ES"),
}
_EXPECTED_TRANSFORM_IDS = {
    CrossMarketFeatureName.SYNCHRONIZED_RETURNS: "synchronized_returns",
    CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD: "return_spread",
    CrossMarketFeatureName.RTY_MINUS_ES_RETURN_SPREAD: "return_spread",
    CrossMarketFeatureName.NQ_ES_ROLLING_BETA_RESIDUAL: "rolling_beta_residual",
    CrossMarketFeatureName.RTY_ES_ROLLING_BETA_RESIDUAL: "rolling_beta_residual",
    CrossMarketFeatureName.NQ_ES_ROLLING_CORRELATION: "rolling_correlation",
    CrossMarketFeatureName.RTY_ES_ROLLING_CORRELATION: "rolling_correlation",
    CrossMarketFeatureName.CONFIRMATION_FLAG: "confirmation_flag",
    CrossMarketFeatureName.DIVERGENCE_FLAG: "divergence_flag",
    CrossMarketFeatureName.RISK_ON_ROTATION_PROXY: "risk_on_rotation_proxy",
    CrossMarketFeatureName.RISK_OFF_ROTATION_PROXY: "risk_off_rotation_proxy",
}
_PRIMITIVE_GAP_FLAGS = (
    MISSING_BBO_QUALITY_FLAG,
    BBO_QUARANTINE_QUALITY_FLAG,
    "no_trade",
    "primitive_gap",
    "input_gap",
)
_ROLLING_GAP_FLAG_TOKENS = (
    "bbo_gap",
    "bbo_quarantined",
    "cross_market_gap",
    "es_bbo_gap",
    "es_missing_history",
    "es_return_gap",
    "input_gap",
    "insufficient_window",
    "missing_bbo",
    "no_trade",
    "non_positive_price",
    "nq_bbo_gap",
    "nq_missing_history",
    "nq_return_gap",
    "primitive_gap",
    "rty_bbo_gap",
    "rty_missing_history",
    "rty_return_gap",
    "session_reset",
    "zero_denominator",
)

_PREFIX = "__fcm"
_ROW_INDEX = f"{_PREFIX}_row_index"
_MARKET = f"{_PREFIX}_market"
_ROW_EVENT_TS = f"{_PREFIX}_row_event_ts"
_ROW_AVAILABLE_TS = f"{_PREFIX}_row_available_ts"
_ROW_FLAGS = f"{_PREFIX}_row_quality_flags"
_POINT_FLAGS = f"{_PREFIX}_point_quality_flags"
_POINT_GAP = f"{_PREFIX}_point_gap"
_SESSION = f"{_PREFIX}_session_label"
_SESSION_UPPER = f"{_PREFIX}_session_label_upper"
_CLOSE = f"{_PREFIX}_close"
_PRIOR_CLOSE = f"{_PREFIX}_prior_close"
_PRIOR_POINT_FLAGS = f"{_PREFIX}_prior_point_flags"
_PRIOR_POINT_GAP = f"{_PREFIX}_prior_point_gap"
_RETURN_SEGMENT_START = f"{_PREFIX}_return_segment_start"
_RETURN_SEGMENT = f"{_PREFIX}_return_segment"
_RETURN_SEGMENT_POSITION = f"{_PREFIX}_return_segment_position"
_RETURN_VALUE = f"{_PREFIX}_return"
_RETURN_RESULT_FLAGS = f"{_PREFIX}_return_result_flags"
_RETURN_QUALITY_FLAGS = f"{_PREFIX}_return_quality_flags"
_EVENT_TS = f"{_PREFIX}_event_ts"
_AVAILABLE_TS = f"{_PREFIX}_available_ts"
_BBO_FLAGS = f"{_PREFIX}_bbo_quality_flags"
_BBO_FLAGS_ROW = f"{_PREFIX}_bbo_quality_flags_row"
_PANEL_SEGMENT_START = f"{_PREFIX}_panel_segment_start"
_PANEL_SEGMENT = f"{_PREFIX}_panel_segment"


@dataclass(frozen=True, slots=True)
class _CrossMarketPackConfig:
    horizon: int
    reset_on_session: bool
    alignment_policy: str


@dataclass(frozen=True, slots=True)
class _PackExpression:
    value: Any
    flags: Any


def build_cross_market_pack(feature_set: FeatureSetSpec) -> FastFeaturePack:
    """Build the governed 11-feature Cross-Market fast pack."""

    if not isinstance(feature_set, FeatureSetSpec):
        raise PackMaterializerError("cross_market fast pack requires a FeatureSetSpec")
    config = _validate_cross_market_feature_set(feature_set)
    polars = require_dependency("polars")
    expressions = _cross_market_expressions(polars, feature_set.features)
    return FastFeaturePack(
        feature_set=feature_set,
        declarations=tuple(
            FastFeatureDeclaration(
                feature_spec=feature,
                value_expr=expressions[feature.feature_id].value,
                quality_flags_expr=expressions[feature.feature_id].flags,
                entity_id_expr=polars.lit(_ENTITY_ID),
                event_ts_expr=polars.col(_EVENT_TS),
                available_ts_expr=polars.col(_AVAILABLE_TS),
            )
            for feature in feature_set.features
        ),
        prepare_frame=lambda frame: _prepare_frame(frame, config),
    )


def supports_cross_market_pack(feature_set: FeatureSetSpec) -> bool:
    """Return true when a feature set is a governed cross-market pack subset."""

    if not isinstance(feature_set, FeatureSetSpec):
        return False
    try:
        _validate_cross_market_feature_set(feature_set)
    except PackMaterializerError:
        return False
    return True


def _validate_cross_market_feature_set(feature_set: FeatureSetSpec) -> _CrossMarketPackConfig:
    features = tuple(feature_set.features)
    if not features:
        raise PackMaterializerError("cross_market fast pack requires features")
    feature_ids = tuple(feature.feature_id for feature in features)
    if len(set(feature_ids)) != len(feature_ids):
        raise PackMaterializerError("cross_market fast pack rejects duplicate features")
    unknown = tuple(
        feature_id for feature_id in feature_ids if feature_id not in CROSS_MARKET_FEATURE_IDS
    )
    if unknown:
        raise PackMaterializerError(
            "cross_market fast pack requires governed Cross-Market features: "
            + ", ".join(unknown)
        )
    configs = tuple(_validate_cross_market_feature(feature) for feature in features)
    first = configs[0]
    if any(config != first for config in configs):
        raise PackMaterializerError(
            "cross_market fast pack requires one shared horizon/reset/alignment policy"
        )
    _require_scaleout_substrate_strict_intersection(feature_set, first)
    return first


def _require_scaleout_substrate_strict_intersection(
    feature_set: FeatureSetSpec,
    config: _CrossMarketPackConfig,
) -> None:
    metadata = feature_set.metadata.to_dict()
    if metadata.get("family") != "cross_market_alignment":
        return
    if config.alignment_policy != "strict_intersection":
        raise PackMaterializerError(
            "cross_market_alignment scaleout substrate requires "
            "alignment_policy=strict_intersection"
        )


def _validate_cross_market_feature(feature: FeatureSpec) -> _CrossMarketPackConfig:
    if not isinstance(feature, FeatureSpec):
        raise PackMaterializerError("cross_market pack entries must be FeatureSpec objects")
    if feature.family is not FeatureFamily.CROSS_MARKET:
        raise PackMaterializerError("cross_market pack can only contain Cross-Market features")
    feature_name = _FEATURE_ID_TO_NAME.get(feature.feature_id)
    if feature_name is None:
        raise PackMaterializerError(f"unsupported cross_market feature_id: {feature.feature_id}")
    parameters = feature.transform.parameters.to_dict()
    _require_parameter(parameters, "feature_name", feature_name.value, feature.feature_id)
    _require_parameter(parameters, "markets", list(_MARKETS), feature.feature_id)
    horizon = _positive_int_parameter(parameters, "horizon", feature.feature_id)
    reset_on_session = _bool_parameter(parameters, "reset_on_session", feature.feature_id)
    if reset_on_session:
        _validate_session_contract_parameters(parameters, feature.feature_id)
    alignment_policy = _alignment_policy(parameters.get("alignment_policy", "asof"))
    expected_transform = _EXPECTED_TRANSFORM_IDS[feature_name]
    if feature.transform.transform_id != expected_transform:
        raise PackMaterializerError(
            f"{feature.feature_id} transform must be {expected_transform}"
        )
    if feature.normalization.normalization_id != "identity":
        raise PackMaterializerError(f"{feature.feature_id} normalization must be identity")
    if feature_name in _ROLLING_FEATURES:
        _require_rolling_feature(feature, feature_name, parameters)
    elif feature_name in _POINT_FEATURES:
        _require_point_feature(feature)
        if feature_name in _SPREAD_PAIRS:
            target, benchmark = _SPREAD_PAIRS[feature_name]
            _require_parameter(parameters, "target_market", target, feature.feature_id)
            _require_parameter(parameters, "benchmark_market", benchmark, feature.feature_id)
    return _CrossMarketPackConfig(
        horizon=horizon,
        reset_on_session=reset_on_session,
        alignment_policy=alignment_policy,
    )


def _require_rolling_feature(
    feature: FeatureSpec,
    feature_name: CrossMarketFeatureName,
    parameters: Mapping[str, object],
) -> None:
    if feature.window.kind is not WindowKind.ROLLING:
        raise PackMaterializerError(f"{feature.feature_id} requires a rolling window")
    if not feature.window.is_live_compatible:
        raise PackMaterializerError(f"{feature.feature_id} requires a live-compatible window")
    _require_parameter(parameters, "window_length", feature.window.length, feature.feature_id)
    ddof = parameters.get("ddof")
    if not isinstance(ddof, int) or isinstance(ddof, bool) or ddof < 0:
        raise PackMaterializerError(f"{feature.feature_id} requires non-negative integer ddof")
    target, benchmark = _ROLLING_PAIRS[feature_name]
    _require_parameter(parameters, "target_market", target, feature.feature_id)
    _require_parameter(parameters, "benchmark_market", benchmark, feature.feature_id)


def _require_point_feature(feature: FeatureSpec) -> None:
    if feature.window.kind is not WindowKind.POINT_IN_TIME or feature.window.length != 1:
        raise PackMaterializerError(f"{feature.feature_id} requires a point-in-time window")
    if not feature.window.is_live_compatible:
        raise PackMaterializerError(f"{feature.feature_id} requires a live-compatible window")


def _require_parameter(
    parameters: Mapping[str, object],
    name: str,
    expected: object,
    feature_id: str,
) -> None:
    if parameters.get(name) != expected:
        raise PackMaterializerError(f"{feature_id} requires {name}={expected!r}")


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


def _positive_int_parameter(
    parameters: Mapping[str, object],
    name: str,
    feature_id: str,
) -> int:
    value = parameters.get(name)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise PackMaterializerError(f"{feature_id} requires positive integer {name}")
    return value


def _bool_parameter(
    parameters: Mapping[str, object],
    name: str,
    feature_id: str,
) -> bool:
    value = parameters.get(name)
    if type(value) is not bool:
        raise PackMaterializerError(f"{feature_id} requires boolean {name}")
    return value


def _alignment_policy(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PackMaterializerError("alignment_policy must be a non-empty string")
    text = value.strip().lower()
    if text in {"asof", "as_of"}:
        return "asof"
    if text in {
        "strict_intersection",
        "event_intersection",
        "exact_event_intersection",
        "no_cross_instrument_forward_fill",
    }:
        return "strict_intersection"
    raise PackMaterializerError("alignment_policy must be either asof or strict_intersection")


def _prepare_frame(frame: Any, config: _CrossMarketPackConfig) -> Any:
    pl = require_dependency("polars")
    _require_columns(
        frame,
        (
            "instrument_id",
            "contract_id",
            "series_id",
            "event_ts",
            "available_ts",
            "bar_start_ts",
            "close",
            "quality_flags",
            "session_label",
        ),
    )
    session_clock = _session_clock()
    working = frame.with_row_index(_ROW_INDEX).with_columns(
        (
            _market_expr(pl).alias(_MARKET),
            _datetime_expr(frame, "event_ts", polars=pl).alias(_ROW_EVENT_TS),
            _datetime_expr(frame, "available_ts", polars=pl).alias(_ROW_AVAILABLE_TS),
            pl.col("close").cast(pl.Float64, strict=False).alias(_CLOSE),
            _template_session_label(
                pl,
                _datetime_expr(frame, "bar_start_ts", polars=pl),
                session_clock,
            ).alias(_SESSION),
            _input_quality_flags(pl).alias(_ROW_FLAGS),
        )
    )
    ohlcv = working.filter(pl.col(_CLOSE).is_not_null()).with_columns(
        pl.col(_SESSION).str.to_uppercase().alias(_SESSION_UPPER)
    )
    _validate_ohlcv_frame(ohlcv)
    returns = _returns_frame(ohlcv, config)
    if config.alignment_policy == "strict_intersection":
        panel = _strict_intersection_panel(returns)
    else:
        panel = _asof_panel(returns)
    panel = _attach_bbo_flags(panel, working)
    panel = _finalize_panel(panel)
    return panel


def _validate_ohlcv_frame(frame: Any) -> None:
    if frame.is_empty():
        raise PackMaterializerError("cross_market canonical frame contains no OHLCV rows")
    if frame.get_column(_MARKET).null_count() > 0:
        raise PackMaterializerError("cross_market rows must identify ES, NQ, or RTY")
    present = set(frame.get_column(_MARKET).to_list())
    if present != set(_MARKETS):
        raise PackMaterializerError("cross_market frame must contain exactly ES, NQ, and RTY rows")


def _returns_frame(frame: Any, config: _CrossMarketPackConfig) -> Any:
    pl = require_dependency("polars")
    frame = frame.sort([_MARKET, _ROW_AVAILABLE_TS, _ROW_INDEX])
    frame = frame.with_columns(
        _contains_any_flag(pl, _ROW_FLAGS, ("no_trade",)).alias(f"{_PREFIX}_row_no_trade")
    )
    frame = frame.with_columns(
        (
            pl.when(pl.col(f"{_PREFIX}_row_no_trade"))
            .then(
                pl.concat_list(pl.col(_ROW_FLAGS), _flags(pl, ("no_trade",)))
                .list.unique()
                .list.sort()
            )
            .otherwise(pl.col(_ROW_FLAGS))
            .alias(_POINT_FLAGS)
        )
    )
    frame = frame.with_columns(
        _contains_any_flag(pl, _POINT_FLAGS, _PRIMITIVE_GAP_FLAGS).alias(_POINT_GAP)
    )
    frame = frame.with_columns(
        (
            (pl.col(_SESSION) != pl.col(_SESSION).shift(1).over(_MARKET))
            .fill_null(True)
            .alias(_RETURN_SEGMENT_START)
        )
    ).with_columns(
        pl.col(_RETURN_SEGMENT_START)
        .cast(pl.Int64)
        .cum_sum()
        .over(_MARKET)
        .alias(_RETURN_SEGMENT)
    )
    frame = frame.with_columns(
        (
            pl.col(_CLOSE).shift(config.horizon).over(_MARKET).alias(_PRIOR_CLOSE),
            pl.col(_POINT_FLAGS).shift(config.horizon).over(_MARKET).alias(_PRIOR_POINT_FLAGS),
            pl.col(_POINT_GAP).shift(config.horizon).over(_MARKET).alias(_PRIOR_POINT_GAP),
            pl.col(_MARKET)
            .cum_count()
            .over([_MARKET, _RETURN_SEGMENT])
            .cast(pl.Int64)
            .alias(_RETURN_SEGMENT_POSITION),
        )
    )
    insufficient = pl.col(_PRIOR_CLOSE).is_null()
    session_reset = (
        insufficient.not_() & (pl.col(_RETURN_SEGMENT_POSITION) <= config.horizon)
        if config.reset_on_session
        else pl.lit(False)
    )
    input_gap = pl.col(_POINT_GAP) | pl.col(_PRIOR_POINT_GAP).fill_null(False)
    zero_denominator = (pl.col(_PRIOR_CLOSE) == 0.0).fill_null(False)
    source_flags = (
        pl.concat_list(
            pl.col(_POINT_FLAGS),
            pl.col(_PRIOR_POINT_FLAGS).fill_null(_flags(pl, ())),
        )
        .list.unique()
        .list.sort()
    )
    frame = frame.with_columns(
        (
            pl.when(insufficient | session_reset | input_gap | zero_denominator)
            .then(None)
            .otherwise(pl.col(_CLOSE) / pl.col(_PRIOR_CLOSE) - 1.0)
            .alias(_RETURN_VALUE),
            pl.when(insufficient)
            .then(
                pl.concat_list(
                    _flags(pl, ("insufficient_window", "primitive_gap")),
                    pl.col(_POINT_FLAGS),
                )
                .list.unique()
                .list.sort()
            )
            .when(session_reset)
            .then(
                pl.concat_list(_flags(pl, ("primitive_gap", "session_reset")), source_flags)
                .list.unique()
                .list.sort()
            )
            .when(input_gap)
            .then(
                pl.concat_list(_flags(pl, ("input_gap", "primitive_gap")), source_flags)
                .list.unique()
                .list.sort()
            )
            .when(zero_denominator)
            .then(
                pl.concat_list(_flags(pl, ("primitive_gap", "zero_denominator")), source_flags)
                .list.unique()
                .list.sort()
            )
            .otherwise(_flags(pl, ()))
            .alias(_RETURN_RESULT_FLAGS),
        )
    )
    frame = frame.with_columns(
        (
            pl.when(pl.col(_RETURN_VALUE).is_null())
            .then(
                pl.concat_list(
                    pl.col(_RETURN_RESULT_FLAGS),
                    pl.col(_ROW_FLAGS),
                    _flags(pl, ("cross_market_gap",)),
                    _market_return_gap_flags(pl),
                )
                .list.unique()
                .list.sort()
            )
            .otherwise(
                pl.concat_list(pl.col(_RETURN_RESULT_FLAGS), pl.col(_ROW_FLAGS))
                .list.unique()
                .list.sort()
            )
            .alias(_RETURN_QUALITY_FLAGS)
        )
    )
    return frame


def _strict_intersection_panel(returns: Any) -> Any:
    duplicates = (
        returns.group_by([_MARKET, _ROW_EVENT_TS])
        .len()
        .filter(pl_col("len") > 1)
    )
    if not duplicates.is_empty():
        raise PackMaterializerError("cross_market strict_intersection requires unique event_ts")
    frames = {
        market: returns.filter(pl_col(_MARKET) == market).select(
            (
                pl_col(_ROW_EVENT_TS).alias(_EVENT_TS),
                pl_col(_ROW_AVAILABLE_TS).alias(_market_col(market, "available_ts")),
                pl_col(_RETURN_VALUE).alias(_market_col(market, "return")),
                pl_col(_RETURN_QUALITY_FLAGS).alias(_market_col(market, "return_flags")),
                pl_col(_SESSION_UPPER).alias(_market_col(market, "session_label")),
            )
        )
        for market in _MARKETS
    }
    panel = frames["ES"].join(frames["NQ"], on=_EVENT_TS, how="inner").join(
        frames["RTY"],
        on=_EVENT_TS,
        how="inner",
    )
    panel = panel.with_columns(
        pl_max_horizontal(
            *(_market_col(market, "available_ts") for market in _MARKETS)
        ).alias(_AVAILABLE_TS)
    )
    return panel.with_columns(_session_label_expr().alias(_SESSION)).sort(_AVAILABLE_TS)


def _asof_panel(returns: Any) -> Any:
    pl = require_dependency("polars")
    timeline = returns.select(pl.col(_ROW_AVAILABLE_TS).alias(_AVAILABLE_TS)).unique().sort(
        _AVAILABLE_TS
    )
    panel = timeline
    for market in _MARKETS:
        market_rows = (
            returns.filter(pl.col(_MARKET) == market)
            .select(
                (
                    pl.col(_ROW_AVAILABLE_TS).alias(_market_col(market, "asof_available_ts")),
                    pl.col(_ROW_EVENT_TS).alias(_market_col(market, "event_ts")),
                    pl.col(_RETURN_VALUE).alias(_market_col(market, "return")),
                    pl.col(_RETURN_QUALITY_FLAGS).alias(_market_col(market, "return_flags")),
                    pl.col(_SESSION_UPPER).alias(_market_col(market, "session_label")),
                )
            )
            .sort(_market_col(market, "asof_available_ts"))
        )
        panel = panel.join_asof(
            market_rows,
            left_on=_AVAILABLE_TS,
            right_on=_market_col(market, "asof_available_ts"),
            strategy="backward",
        )
        panel = panel.with_columns(
            (
                pl.when(pl.col(_market_col(market, "asof_available_ts")).is_null())
                .then(_flags(pl, (f"{market.lower()}_missing_history", "cross_market_gap")))
                .otherwise(pl.col(_market_col(market, "return_flags")))
                .alias(_market_col(market, "return_flags"))
            )
        )
    panel = panel.with_columns(
        pl.max_horizontal(*(_market_col(market, "event_ts") for market in _MARKETS))
        .fill_null(pl.col(_AVAILABLE_TS))
        .alias(_EVENT_TS)
    )
    return panel.with_columns(_session_label_expr().alias(_SESSION)).sort(_AVAILABLE_TS)


def _attach_bbo_flags(panel: Any, frame: Any) -> Any:
    pl = require_dependency("polars")
    if "bid" not in frame.columns and "ask" not in frame.columns:
        return panel.with_columns(_flags(pl, ()).alias(_BBO_FLAGS))
    bbo_filter = pl.lit(False)
    if "bid" in frame.columns:
        bbo_filter = bbo_filter | pl.col("bid").is_not_null()
    if "ask" in frame.columns:
        bbo_filter = bbo_filter | pl.col("ask").is_not_null()
    bbo = frame.filter(bbo_filter)
    if bbo.is_empty():
        return panel.with_columns(_flags(pl, ()).alias(_BBO_FLAGS))
    abnormal = bbo.filter(
        _contains_any_flag(pl, _ROW_FLAGS, (MISSING_BBO_QUALITY_FLAG, BBO_QUARANTINE_QUALITY_FLAG))
    )
    if abnormal.is_empty():
        return panel.with_columns(_flags(pl, ()).alias(_BBO_FLAGS))
    abnormal = abnormal.with_columns(
        (
            pl.concat_list(
                pl.col(_ROW_FLAGS),
                _flags(pl, ("bbo_gap",)),
                _market_bbo_gap_flags(pl),
            )
            .list.unique()
            .list.sort()
            .alias(_BBO_FLAGS_ROW)
        )
    )
    aggregate = (
        abnormal.select((pl.col(_ROW_AVAILABLE_TS), pl.col(_BBO_FLAGS_ROW)))
        .explode(_BBO_FLAGS_ROW)
        .group_by(_ROW_AVAILABLE_TS)
        .agg(pl.col(_BBO_FLAGS_ROW).unique().sort().alias(_BBO_FLAGS))
    )
    return (
        panel.join(
            aggregate,
            left_on=_AVAILABLE_TS,
            right_on=_ROW_AVAILABLE_TS,
            how="left",
        )
        .with_columns(pl.col(_BBO_FLAGS).fill_null(_flags(pl, ())).alias(_BBO_FLAGS))
    )


def _finalize_panel(panel: Any) -> Any:
    pl = require_dependency("polars")
    panel = panel.sort(_AVAILABLE_TS).with_columns(
        (pl.col(_SESSION) != pl.col(_SESSION).shift(1)).fill_null(True).alias(
            _PANEL_SEGMENT_START
        )
    )
    panel = panel.with_columns(
        pl.col(_PANEL_SEGMENT_START).cast(pl.Int64).cum_sum().alias(_PANEL_SEGMENT)
    )
    return panel.with_columns(
        (
            pl.lit(_ENTITY_ID).alias("series_id"),
            pl.col(_EVENT_TS).alias("event_ts"),
            pl.col(_AVAILABLE_TS).alias("available_ts"),
        )
    )


def _cross_market_expressions(
    polars: Any,
    features: Sequence[FeatureSpec],
) -> dict[str, _PackExpression]:
    expressions: dict[str, _PackExpression] = {}
    for feature in features:
        feature_name = _FEATURE_ID_TO_NAME[feature.feature_id]
        if feature_name is CrossMarketFeatureName.SYNCHRONIZED_RETURNS:
            expressions[feature.feature_id] = _synchronized_returns_expression(polars)
        elif feature_name in _SPREAD_PAIRS:
            target, benchmark = _SPREAD_PAIRS[feature_name]
            expressions[feature.feature_id] = _spread_expression(polars, target, benchmark)
        elif feature_name is CrossMarketFeatureName.CONFIRMATION_FLAG:
            expressions[feature.feature_id] = _confirmation_expression(polars)
        elif feature_name is CrossMarketFeatureName.DIVERGENCE_FLAG:
            expressions[feature.feature_id] = _divergence_expression(polars)
        elif feature_name in {
            CrossMarketFeatureName.RISK_ON_ROTATION_PROXY,
            CrossMarketFeatureName.RISK_OFF_ROTATION_PROXY,
        }:
            expressions[feature.feature_id] = _rotation_expression(
                polars,
                risk_off=feature_name is CrossMarketFeatureName.RISK_OFF_ROTATION_PROXY,
            )
        elif feature_name in _ROLLING_PAIRS:
            target, benchmark = _ROLLING_PAIRS[feature_name]
            expressions[feature.feature_id] = _rolling_expression(
                polars,
                feature,
                target,
                benchmark,
                correlation=feature_name
                in {
                    CrossMarketFeatureName.NQ_ES_ROLLING_CORRELATION,
                    CrossMarketFeatureName.RTY_ES_ROLLING_CORRELATION,
                },
            )
        else:
            raise PackMaterializerError(f"unsupported cross_market feature: {feature.feature_id}")
    return expressions


def _synchronized_returns_expression(polars: Any) -> _PackExpression:
    pl = polars
    valid = _all_returns_valid(_MARKETS)
    value = (
        pl.when(valid)
        .then(
            pl.struct(
                [
                    pl.col(_market_col("ES", "return")).alias("ES"),
                    pl.col(_market_col("NQ", "return")).alias("NQ"),
                    pl.col(_market_col("RTY", "return")).alias("RTY"),
                ]
            )
        )
        .otherwise(None)
    )
    flags = pl.when(valid).then(pl.col(_BBO_FLAGS)).otherwise(_point_gap_flags(pl, _MARKETS))
    return _PackExpression(value, flags)


def _spread_expression(polars: Any, target: str, benchmark: str) -> _PackExpression:
    pl = polars
    valid = _all_returns_valid((target, benchmark))
    value = (
        pl.when(valid)
        .then(pl.col(_market_col(target, "return")) - pl.col(_market_col(benchmark, "return")))
        .otherwise(None)
    )
    flags = (
        pl.when(valid)
        .then(pl.col(_BBO_FLAGS))
        .otherwise(_point_gap_flags(pl, (target, benchmark)))
    )
    return _PackExpression(value, flags)


def _confirmation_expression(polars: Any) -> _PackExpression:
    pl = polars
    valid = _all_returns_valid(_MARKETS)
    all_positive = (
        (pl.col(_market_col("ES", "return")) > 0)
        & (pl.col(_market_col("NQ", "return")) > 0)
        & (pl.col(_market_col("RTY", "return")) > 0)
    )
    all_negative = (
        (pl.col(_market_col("ES", "return")) < 0)
        & (pl.col(_market_col("NQ", "return")) < 0)
        & (pl.col(_market_col("RTY", "return")) < 0)
    )
    value = (
        pl.when(valid)
        .then(pl.when(all_positive | all_negative).then(1).otherwise(0))
        .otherwise(None)
    )
    flags = pl.when(valid).then(pl.col(_BBO_FLAGS)).otherwise(_point_gap_flags(pl, _MARKETS))
    return _PackExpression(value, flags)


def _divergence_expression(polars: Any) -> _PackExpression:
    pl = polars
    valid = _all_returns_valid(_MARKETS)
    positive = (
        (pl.col(_market_col("ES", "return")) > 0)
        | (pl.col(_market_col("NQ", "return")) > 0)
        | (pl.col(_market_col("RTY", "return")) > 0)
    )
    negative = (
        (pl.col(_market_col("ES", "return")) < 0)
        | (pl.col(_market_col("NQ", "return")) < 0)
        | (pl.col(_market_col("RTY", "return")) < 0)
    )
    value = pl.when(valid).then(pl.when(positive & negative).then(1).otherwise(0)).otherwise(None)
    flags = pl.when(valid).then(pl.col(_BBO_FLAGS)).otherwise(_point_gap_flags(pl, _MARKETS))
    return _PackExpression(value, flags)


def _rotation_expression(polars: Any, *, risk_off: bool) -> _PackExpression:
    pl = polars
    valid = _all_returns_valid(_MARKETS)
    risk_on = (
        (
            pl.col(_market_col("NQ", "return"))
            - pl.col(_market_col("ES", "return"))
            + pl.col(_market_col("RTY", "return"))
            - pl.col(_market_col("ES", "return"))
        )
        / 2.0
    )
    value = pl.when(valid).then(-risk_on if risk_off else risk_on).otherwise(None)
    flags = pl.when(valid).then(pl.col(_BBO_FLAGS)).otherwise(_point_gap_flags(pl, _MARKETS))
    return _PackExpression(value, flags)


def _rolling_expression(
    polars: Any,
    feature: FeatureSpec,
    target: str,
    benchmark: str,
    *,
    correlation: bool,
) -> _PackExpression:
    pl = polars
    parameters = feature.transform.parameters.to_dict()
    window = feature.window.length
    ddof = int(parameters["ddof"])
    denominator = float(max(1, window - ddof))
    group = [_PANEL_SEGMENT] if parameters["reset_on_session"] else ["series_id"]
    target_return = pl.col(_market_col(target, "return"))
    benchmark_return = pl.col(_market_col(benchmark, "return"))
    position = pl.col(_AVAILABLE_TS).cum_count().over(group).cast(pl.Int64)
    insufficient = position < window
    ddof_insufficient = pl.lit(window <= ddof)
    input_gap = target_return.is_null() | benchmark_return.is_null()
    input_gap_count = _rolling_true_count(input_gap, window, group, polars=pl)
    target_sum = _rolling_sum(target_return, window, group, polars=pl)
    benchmark_sum = _rolling_sum(benchmark_return, window, group, polars=pl)
    sample_count = float(window)
    target_mean = target_sum / sample_count
    benchmark_mean = benchmark_sum / sample_count
    # Stable two-pass CENTERED covariance/variance to match the per-row Python
    # reference (_covariance/_variance subtract the window mean BEFORE summing).
    # The one-pass `product_sum - target_sum*benchmark_sum/n` form is algebraically
    # identical but loses precision via catastrophic cancellation -- amplified by
    # division by small variances in short windows to ~1e-5..1e-1 abs diffs on real
    # data. Summing the centered products over the window via explicit per-lag
    # shifts reproduces the reference's two-pass arithmetic, dropping the residual
    # to float reduction-order noise (~1e-12). (FCFP-P13 cross_market parity.)
    def _centered_window_sum(
        left: Any, left_mean: Any, right: Any, right_mean: Any
    ) -> Any:
        terms = [
            (left.shift(lag).over(group) - left_mean)
            * (right.shift(lag).over(group) - right_mean)
            for lag in range(window)
        ]
        total = terms[0]
        for term in terms[1:]:
            total = total + term
        return total

    covariance = (
        _centered_window_sum(target_return, target_mean, benchmark_return, benchmark_mean)
        / denominator
    )
    benchmark_variance = (
        _centered_window_sum(benchmark_return, benchmark_mean, benchmark_return, benchmark_mean)
        / denominator
    )
    target_variance = (
        _centered_window_sum(target_return, target_mean, target_return, target_mean)
        / denominator
    )
    # Robust zero-variance detection (constant return window) -- see
    # constant_window_mask. Preemptive parity hardening for the FCFP-P13 bug class.
    zero_benchmark_variance = constant_window_mask(benchmark_return, window=window, group=group)
    zero_target_variance = constant_window_mask(target_return, window=window, group=group)
    beta = covariance / benchmark_variance
    residual = target_return - beta * benchmark_return
    correlation_value = covariance / (benchmark_variance * target_variance).sqrt()
    value = (
        pl.when(
            insufficient
            | (input_gap_count > 0)
            | ddof_insufficient
            | zero_benchmark_variance
            | (zero_target_variance if correlation else pl.lit(False))
        )
        .then(None)
        .otherwise(correlation_value if correlation else residual)
    )
    flags = (
        pl.when(insufficient | ddof_insufficient)
        .then(
            pl.concat_list(
                _flags(pl, ("cross_market_gap", "insufficient_window")),
                pl.col(_BBO_FLAGS),
            )
            .list.unique()
            .list.sort()
        )
        .when(input_gap_count > 0)
        .then(_rolling_gap_flags(pl, target, benchmark, window, group))
        .when(zero_benchmark_variance)
        .then(
            pl.concat_list(
                _flags(pl, ("cross_market_gap", "zero_benchmark_variance")),
                pl.col(_BBO_FLAGS),
            )
            .list.unique()
            .list.sort()
        )
    )
    if correlation:
        flags = flags.when(zero_target_variance).then(
            pl.concat_list(
                _flags(pl, ("cross_market_gap", "zero_target_variance")),
                pl.col(_BBO_FLAGS),
            )
            .list.unique()
            .list.sort()
        )
    flags = flags.otherwise(pl.col(_BBO_FLAGS))
    return _PackExpression(value, flags)


def _all_returns_valid(markets: Sequence[str]) -> Any:
    valid = pl_col(_market_col(markets[0], "return")).is_not_null()
    for market in markets[1:]:
        valid = valid & pl_col(_market_col(market, "return")).is_not_null()
    return valid


def _point_gap_flags(polars: Any, markets: Sequence[str]) -> Any:
    fragments = [
        _flags(polars, ("cross_market_gap", "input_gap")),
        polars.col(_BBO_FLAGS),
    ]
    for market in markets:
        fragments.append(
            polars.when(polars.col(_market_col(market, "return")).is_null())
            .then(polars.col(_market_col(market, "return_flags")))
            .otherwise(_flags(polars, ()))
        )
    return polars.concat_list(*fragments).list.unique().list.sort()


def _rolling_gap_flags(
    polars: Any,
    target: str,
    benchmark: str,
    window: int,
    group: Sequence[str],
) -> Any:
    fragments = [
        _flags(polars, ("cross_market_gap", "input_gap")),
        polars.col(_BBO_FLAGS),
    ]
    for token in _ROLLING_GAP_FLAG_TOKENS:
        fragments.append(
            _conditional_flags(
                polars,
                _rolling_true_count(
                    _rolling_pair_gap_contains(polars, target, benchmark, token),
                    window,
                    group,
                    polars=polars,
                )
                > 0,
                (token,),
            )
        )
    return polars.concat_list(*fragments).list.unique().list.sort()


def _rolling_pair_gap_contains(
    polars: Any,
    target: str,
    benchmark: str,
    token: str,
) -> Any:
    target_missing = polars.col(_market_col(target, "return")).is_null()
    benchmark_missing = polars.col(_market_col(benchmark, "return")).is_null()
    return (
        (
            (target_missing | benchmark_missing)
            & polars.col(_BBO_FLAGS).list.contains(token).fill_null(False)
        )
        | (
            target_missing
            & polars.col(_market_col(target, "return_flags")).list.contains(token).fill_null(False)
        )
        | (
            benchmark_missing
            & polars.col(_market_col(benchmark, "return_flags"))
            .list.contains(token)
            .fill_null(False)
        )
        | ((target_missing | benchmark_missing) & polars.lit(token == "input_gap"))
    )


def _rolling_sum(expression: Any, window: int, group: Sequence[str], *, polars: Any) -> Any:
    return expression.rolling_sum(window_size=window, min_samples=window).over(list(group))


def _rolling_true_count(condition: Any, window: int, group: Sequence[str], *, polars: Any) -> Any:
    return (
        condition.cast(polars.Int64)
        .rolling_sum(window_size=window, min_samples=window)
        .over(list(group))
        .fill_null(0)
    )


def _session_label_expr() -> Any:
    pl = require_dependency("polars")
    labels = [_market_col(market, "session_label") for market in _MARKETS]
    all_empty = pl.lit(True)
    for label in labels:
        all_empty = all_empty & (pl.col(label).is_null() | (pl.col(label) == ""))
    same_non_empty = pl.col(labels[0]).is_not_null() & (pl.col(labels[0]) != "")
    for label in labels[1:]:
        same_non_empty = same_non_empty & (pl.col(label) == pl.col(labels[0]))
    return (
        pl.when(all_empty)
        .then(pl.lit(""))
        .when(same_non_empty)
        .then(pl.col(labels[0]))
        .otherwise(pl.lit("MIXED"))
    )


def _market_col(market: str, name: str) -> str:
    return f"{_PREFIX}_{market.lower()}_{name}"


def _market_return_gap_flags(polars: Any) -> Any:
    expression = polars.lit([], dtype=polars.List(polars.Utf8))
    for market in _MARKETS:
        expression = polars.when(polars.col(_MARKET) == market).then(
            _flags(polars, (f"{market.lower()}_return_gap",))
        ).otherwise(expression)
    return expression


def _market_bbo_gap_flags(polars: Any) -> Any:
    expression = polars.lit([], dtype=polars.List(polars.Utf8))
    for market in _MARKETS:
        expression = polars.when(polars.col(_MARKET) == market).then(
            _flags(polars, (f"{market.lower()}_bbo_gap",))
        ).otherwise(expression)
    return expression


def _market_expr(polars: Any) -> Any:
    expression = polars.lit(None, dtype=polars.Utf8)
    for column in ("instrument_id", "contract_id", "series_id"):
        candidate = _market_candidate_expr(polars, column)
        expression = polars.when(expression.is_null() & candidate.is_not_null()).then(
            candidate
        ).otherwise(expression)
    return expression


def _market_candidate_expr(polars: Any, column: str) -> Any:
    text = polars.col(column).cast(polars.Utf8, strict=False).str.to_uppercase()
    expression = polars.lit(None, dtype=polars.Utf8)
    for market in _MARKETS:
        token_pattern = rf"(^|_){re.escape(market)}($|_)"
        condition = (
            (text == market)
            | text.str.starts_with(market)
            | text.str.contains(token_pattern)
        ).fill_null(False)
        expression = polars.when(condition).then(polars.lit(market)).otherwise(expression)
    return expression


def _datetime_expr(frame: Any, column: str, *, polars: Any) -> Any:
    dtype = frame.schema[column]
    if dtype in (polars.Utf8, polars.String):
        return polars.col(column).str.to_datetime(time_zone="UTC", strict=True)
    return polars.col(column).cast(polars.Datetime(time_zone="UTC"), strict=False)


def _session_clock() -> SessionTruthClock:
    try:
        return session_truth_clock()
    except DataFoundationValidationError as exc:
        raise PackMaterializerError(str(exc)) from exc


def _local_seconds(
    polars: Any,
    timestamp_expr: Any,
    session_clock: SessionTruthClock,
) -> Any:
    local = timestamp_expr.dt.convert_time_zone(session_clock.timezone)
    return (
        local.dt.hour().cast(polars.Int64) * 3600
        + local.dt.minute().cast(polars.Int64) * 60
        + local.dt.second().cast(polars.Int64)
    )


def _is_rth(polars: Any, timestamp_expr: Any, session_clock: SessionTruthClock) -> Any:
    seconds = _local_seconds(polars, timestamp_expr, session_clock)
    return (seconds >= session_clock.rth_open_seconds) & (
        seconds < session_clock.rth_close_seconds
    )


def _template_session_label(
    polars: Any,
    timestamp_expr: Any,
    session_clock: SessionTruthClock,
) -> Any:
    return polars.when(_is_rth(polars, timestamp_expr, session_clock)).then(
        polars.lit("RTH")
    ).otherwise(polars.lit("ETH"))


def _input_quality_flags(polars: Any) -> Any:
    return (
        polars.col("quality_flags")
        .cast(polars.List(polars.Utf8), strict=False)
        .fill_null(_flags(polars, ()))
        .list.eval(polars.element().str.to_lowercase())
        .list.unique()
        .list.sort()
    )


def _contains_any_flag(polars: Any, list_column: str, flags: Sequence[str]) -> Any:
    expression = polars.col(list_column).list.contains(flags[0]).fill_null(False)
    for flag in flags[1:]:
        expression = expression | polars.col(list_column).list.contains(flag).fill_null(False)
    return expression


def _conditional_flags(polars: Any, condition: Any, values: Sequence[str]) -> Any:
    return polars.when(condition).then(_flags(polars, values)).otherwise(_flags(polars, ()))


def _flags(polars: Any, values: Sequence[str]) -> Any:
    return polars.lit(list(values), dtype=polars.List(polars.Utf8))


def _require_columns(frame: Any, columns: Sequence[str]) -> None:
    missing = tuple(column for column in columns if column not in frame.columns)
    if missing:
        raise PackMaterializerError("canonical frame missing columns: " + ", ".join(missing))


def pl_col(name: str) -> Any:
    return require_dependency("polars").col(name)


def pl_max_horizontal(*names: str) -> Any:
    return require_dependency("polars").max_horizontal(*names)


__all__ = [
    "CROSS_MARKET_FEATURE_IDS",
    "build_cross_market_pack",
    "supports_cross_market_pack",
]
