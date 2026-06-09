"""VWAP / session-auction Polars pack for the V1 fast producer path."""

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
from alpha_system.features.families.ohlcv import OHLCVFeatureName
from alpha_system.features.fast.materializer import (
    FastFeatureDeclaration,
    FastFeaturePack,
    PackMaterializerError,
)

VWAP_SESSION_AUCTION_FEATURE_NAMES: tuple[OHLCVFeatureName, ...] = (
    OHLCVFeatureName.VWAP,
    OHLCVFeatureName.ANCHORED_VWAP,
    OHLCVFeatureName.DISTANCE_TO_VWAP,
    OHLCVFeatureName.OPENING_RANGE,
    OHLCVFeatureName.OVERNIGHT_RANGE,
)
VWAP_SESSION_AUCTION_FEATURE_IDS: tuple[str, ...] = tuple(
    f"base_ohlcv_{feature_name.value}" for feature_name in VWAP_SESSION_AUCTION_FEATURE_NAMES
)

_FEATURE_ID_TO_NAME: dict[str, OHLCVFeatureName] = {
    f"base_ohlcv_{feature_name.value}": feature_name
    for feature_name in VWAP_SESSION_AUCTION_FEATURE_NAMES
}

_PREFIX = "__fsa"
_BAR_START = f"{_PREFIX}_bar_start_ts"
_HIGH = f"{_PREFIX}_high"
_LOW = f"{_PREFIX}_low"
_CLOSE = f"{_PREFIX}_close"
_VOLUME = f"{_PREFIX}_volume"
_INPUT_FLAGS = f"{_PREFIX}_input_quality_flags"
_SESSION = f"{_PREFIX}_session_label"
_IS_TRADE = f"{_PREFIX}_is_trade"
_IS_RTH = f"{_PREFIX}_is_rth"
_IS_ETH = f"{_PREFIX}_is_eth"
_IS_SEGMENT_START = f"{_PREFIX}_is_segment_start"
_SEGMENT = f"{_PREFIX}_segment"
_OVERNIGHT_SEGMENT = f"{_PREFIX}_overnight_segment"
_SEGMENT_START = f"{_PREFIX}_segment_start_ts"
_TYPICAL_PRICE = f"{_PREFIX}_typical_price"
_ETH_HIGH_INPUT = f"{_PREFIX}_eth_high_input"
_ETH_LOW_INPUT = f"{_PREFIX}_eth_low_input"
_ETH_HIGH = f"{_PREFIX}_eth_high"
_ETH_LOW = f"{_PREFIX}_eth_low"
_ETH_RANGE = f"{_PREFIX}_eth_range"
_FROZEN_OVERNIGHT_RANGE = f"{_PREFIX}_frozen_overnight_range"
_SEGMENT_SERIES = f"{_PREFIX}_segment_series_id"
_SEGMENT_SESSION = f"{_PREFIX}_segment_session_label"
_SEGMENT_ETH_RANGE = f"{_PREFIX}_segment_eth_range"
_PREVIOUS_SEGMENT_SESSION = f"{_PREFIX}_previous_segment_session"
_PREVIOUS_SEGMENT_ETH_RANGE = f"{_PREFIX}_previous_segment_eth_range"


@dataclass(frozen=True, slots=True)
class _PackExpression:
    value: Any
    flags: Any


def build_vwap_session_auction_pack(feature_set: FeatureSetSpec) -> FastFeaturePack:
    """Build the governed VWAP / session-auction fast pack."""

    if not isinstance(feature_set, FeatureSetSpec):
        raise PackMaterializerError("vwap_session_auction fast pack requires a FeatureSetSpec")
    _validate_vwap_session_auction_feature_set(feature_set)
    polars = require_dependency("polars")
    expressions = _vwap_session_auction_expressions(polars, feature_set.features)
    anchor_labels = _anchor_labels(feature_set.features)
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
        prepare_frame=lambda frame: _prepare_frame(frame, anchor_labels=anchor_labels),
    )


def supports_vwap_session_auction_pack(feature_set: FeatureSetSpec) -> bool:
    """Return true when a feature set is a governed VWAP pack subset."""

    if not isinstance(feature_set, FeatureSetSpec):
        return False
    try:
        _validate_vwap_session_auction_feature_set(feature_set)
    except PackMaterializerError:
        return False
    return True


def _validate_vwap_session_auction_feature_set(feature_set: FeatureSetSpec) -> None:
    features = tuple(feature_set.features)
    if not features:
        raise PackMaterializerError("vwap_session_auction fast pack requires features")
    feature_ids = tuple(feature.feature_id for feature in features)
    if len(set(feature_ids)) != len(feature_ids):
        raise PackMaterializerError("vwap_session_auction fast pack rejects duplicate features")
    unknown = tuple(
        feature_id
        for feature_id in feature_ids
        if feature_id not in VWAP_SESSION_AUCTION_FEATURE_IDS
    )
    if unknown:
        raise PackMaterializerError(
            "vwap_session_auction fast pack requires governed VWAP / "
            "session-auction features: " + ", ".join(unknown)
        )
    for feature in features:
        _validate_vwap_session_auction_feature(feature)


def _validate_vwap_session_auction_feature(feature: FeatureSpec) -> None:
    if not isinstance(feature, FeatureSpec):
        raise PackMaterializerError(
            "vwap_session_auction pack entries must be FeatureSpec objects"
        )
    if feature.family is not FeatureFamily.BASE_OHLCV:
        raise PackMaterializerError(
            "vwap_session_auction pack can only contain governed Base OHLCV features"
        )
    feature_name = _FEATURE_ID_TO_NAME.get(feature.feature_id)
    if feature_name is None:
        raise PackMaterializerError(
            f"unsupported vwap_session_auction feature_id: {feature.feature_id}"
        )
    parameters = feature.transform.parameters.to_dict()
    _require_parameter(parameters, "feature_name", feature_name.value, feature.feature_id)
    _require_parameter(parameters, "reset_on_session", True, feature.feature_id)
    if feature_name is OHLCVFeatureName.OPENING_RANGE:
        opening_minutes = parameters.get("opening_range_minutes")
        if not isinstance(opening_minutes, int) or isinstance(opening_minutes, bool):
            raise PackMaterializerError(
                f"{feature.feature_id} requires integer opening_range_minutes"
            )
        if opening_minutes <= 0:
            raise PackMaterializerError(
                f"{feature.feature_id} requires positive opening_range_minutes"
            )
    if feature_name is OHLCVFeatureName.ANCHORED_VWAP:
        anchor = parameters.get("anchor_session_label")
        if anchor is not None and (not isinstance(anchor, str) or not anchor.strip()):
            raise PackMaterializerError(
                f"{feature.feature_id} requires non-empty anchor_session_label when present"
            )
    if feature.window.kind is not WindowKind.EXPANDING or feature.window.length != 1:
        raise PackMaterializerError(f"{feature.feature_id} requires an expanding window")
    if not feature.window.is_live_compatible:
        raise PackMaterializerError(f"{feature.feature_id} requires a live-compatible window")
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


def _anchor_labels(features: Sequence[FeatureSpec]) -> tuple[str, ...]:
    labels: list[str] = []
    for feature in features:
        if _FEATURE_ID_TO_NAME[feature.feature_id] is not OHLCVFeatureName.ANCHORED_VWAP:
            continue
        anchor = feature.transform.parameters.to_dict().get("anchor_session_label")
        if anchor is not None:
            label = str(anchor).upper()
            if label not in labels:
                labels.append(label)
    return tuple(labels)


def _vwap_session_auction_expressions(
    polars: Any,
    features: Sequence[FeatureSpec],
) -> dict[str, _PackExpression]:
    pl = polars
    expressions: dict[str, _PackExpression] = {}
    for feature in features:
        feature_name = _FEATURE_ID_TO_NAME[feature.feature_id]
        if feature_name is OHLCVFeatureName.VWAP:
            expressions[feature.feature_id] = _vwap_expression(pl)
        elif feature_name is OHLCVFeatureName.ANCHORED_VWAP:
            expressions[feature.feature_id] = _anchored_vwap_expression(
                pl,
                _anchor_label(feature),
            )
        elif feature_name is OHLCVFeatureName.DISTANCE_TO_VWAP:
            expressions[feature.feature_id] = _distance_to_vwap_expression(pl)
        elif feature_name is OHLCVFeatureName.OPENING_RANGE:
            expressions[feature.feature_id] = _opening_range_expression(
                pl,
                _int_parameter(feature, "opening_range_minutes"),
            )
        elif feature_name is OHLCVFeatureName.OVERNIGHT_RANGE:
            expressions[feature.feature_id] = _overnight_range_expression(pl)
        else:
            raise PackMaterializerError(f"unsupported VWAP feature: {feature_name}")
    return expressions


def _anchor_label(feature: FeatureSpec) -> str | None:
    anchor = feature.transform.parameters.to_dict().get("anchor_session_label")
    return None if anchor is None else str(anchor).upper()


def _int_parameter(feature: FeatureSpec, name: str) -> int:
    value = feature.transform.parameters.to_dict().get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise PackMaterializerError(f"{feature.feature_id} requires integer {name}")
    return value


def _prepare_frame(frame: Any, *, anchor_labels: Sequence[str]) -> Any:
    pl = require_dependency("polars")
    _require_columns(
        frame,
        (
            "series_id",
            "bar_start_ts",
            "high",
            "low",
            "close",
            "volume",
            "quality_flags",
            "session_label",
        ),
    )
    prepared = frame.with_columns(
        (
            _bar_start_ts(pl).alias(_BAR_START),
            pl.col("high").cast(pl.Float64, strict=False).alias(_HIGH),
            pl.col("low").cast(pl.Float64, strict=False).alias(_LOW),
            pl.col("close").cast(pl.Float64, strict=False).alias(_CLOSE),
            pl.col("volume").cast(pl.Float64, strict=False).alias(_VOLUME),
            _input_quality_flags(pl).alias(_INPUT_FLAGS),
            _session_label(pl).alias(_SESSION),
        )
    )
    segment_start = (
        (
            pl.col("series_id").cast(pl.Utf8) != pl.col("series_id").cast(pl.Utf8).shift(1)
        )
        | (pl.col(_SESSION) != pl.col(_SESSION).shift(1))
    ).fill_null(True)
    overnight_segment_start = (pl.col(_SESSION) != pl.col(_SESSION).shift(1)).fill_null(True)
    prepared = prepared.with_columns(
        (
            pl.col(_INPUT_FLAGS)
            .list.contains("no_trade")
            .fill_null(False)
            .not_()
            .alias(_IS_TRADE),
            (pl.col(_SESSION) == "RTH").alias(_IS_RTH),
            (pl.col(_SESSION) == "ETH").alias(_IS_ETH),
            segment_start.alias(_IS_SEGMENT_START),
        )
    )
    prepared = prepared.with_columns(
        (
            pl.col(_IS_SEGMENT_START).cast(pl.Int64).cum_sum().alias(_SEGMENT),
            overnight_segment_start.cast(pl.Int64).cum_sum().alias(_OVERNIGHT_SEGMENT),
            ((pl.col(_HIGH) + pl.col(_LOW) + pl.col(_CLOSE)) / 3.0).alias(_TYPICAL_PRICE),
        )
    )
    prepared = prepared.with_columns(
        pl.col(_BAR_START).first().over(_SEGMENT).alias(_SEGMENT_START)
    )
    prepared = _with_overnight_columns(prepared, polars=pl)
    for anchor_label in anchor_labels:
        prepared = prepared.with_columns(
            (
                (pl.col(_IS_SEGMENT_START) & (pl.col(_SESSION) == anchor_label))
                .cast(pl.Int64)
                .cum_sum()
                .over("series_id")
                .alias(_anchor_block_column(anchor_label))
            )
        )
    return prepared


def _with_overnight_columns(frame: Any, *, polars: Any) -> Any:
    pl = polars
    prepared = frame.with_columns(
        (
            pl.when(pl.col(_IS_ETH) & pl.col(_IS_TRADE))
            .then(pl.col(_HIGH))
            .otherwise(None)
            .alias(_ETH_HIGH_INPUT),
            pl.when(pl.col(_IS_ETH) & pl.col(_IS_TRADE))
            .then(pl.col(_LOW))
            .otherwise(None)
            .alias(_ETH_LOW_INPUT),
        )
    )
    prepared = prepared.with_columns(
        (
            pl.col(_ETH_HIGH_INPUT)
            .cum_max()
            .forward_fill()
            .over(_OVERNIGHT_SEGMENT)
            .alias(_ETH_HIGH),
            pl.col(_ETH_LOW_INPUT)
            .cum_min()
            .forward_fill()
            .over(_OVERNIGHT_SEGMENT)
            .alias(_ETH_LOW),
        )
    )
    prepared = prepared.with_columns(
        (
            pl.when(pl.col(_ETH_HIGH).is_null() | pl.col(_ETH_LOW).is_null())
            .then(None)
            .otherwise(pl.col(_ETH_HIGH) - pl.col(_ETH_LOW))
            .alias(_ETH_RANGE)
        )
    )
    segment_summary = prepared.group_by(_OVERNIGHT_SEGMENT, maintain_order=True).agg(
        (
            pl.col("series_id").first().alias(_SEGMENT_SERIES),
            pl.col(_SESSION).first().alias(_SEGMENT_SESSION),
            pl.col(_ETH_RANGE).last().alias(_SEGMENT_ETH_RANGE),
        )
    )
    segment_summary = segment_summary.with_columns(
        (
            pl.col(_SEGMENT_SESSION).shift(1).alias(_PREVIOUS_SEGMENT_SESSION),
            pl.col(_SEGMENT_ETH_RANGE).shift(1).alias(_PREVIOUS_SEGMENT_ETH_RANGE),
        )
    )
    segment_summary = segment_summary.with_columns(
        (
            pl.when(pl.col(_PREVIOUS_SEGMENT_SESSION) == "ETH")
            .then(pl.col(_PREVIOUS_SEGMENT_ETH_RANGE))
            .otherwise(None)
            .alias(_FROZEN_OVERNIGHT_RANGE)
        )
    )
    return prepared.join(
        segment_summary.select((_OVERNIGHT_SEGMENT, _FROZEN_OVERNIGHT_RANGE)),
        on=_OVERNIGHT_SEGMENT,
        how="left",
    )


def _vwap_expression(polars: Any) -> _PackExpression:
    pl = polars
    raw_vwap = _vwap_raw(pl, group_columns=(_SEGMENT,))
    value = (
        pl.when(_is_no_trade(pl) | _is_zero_volume(pl))
        .then(None)
        .otherwise(raw_vwap)
    )
    return _PackExpression(value, _vwap_gap_flags(pl))


def _anchored_vwap_expression(polars: Any, anchor_label: str | None) -> _PackExpression:
    pl = polars
    if anchor_label is None:
        active = pl.lit(True)
        group_columns = (_SEGMENT,)
    else:
        anchor_block = _anchor_block_column(anchor_label)
        active = pl.col(anchor_block) > 0
        group_columns = ("series_id", anchor_block)
    raw_vwap = _vwap_raw(pl, group_columns=group_columns, active=active)
    value = (
        pl.when(active.not_())
        .then(None)
        .when(_is_no_trade(pl) | _is_zero_volume(pl))
        .then(None)
        .otherwise(raw_vwap)
    )
    flags = (
        pl.when(active.not_())
        .then(_gap_flags(pl, "before_anchor"))
        .when(_is_no_trade(pl))
        .then(_gap_flags(pl, "no_trade", pl.col(_INPUT_FLAGS)))
        .when(_is_zero_volume(pl))
        .then(_gap_flags(pl, "zero_volume", pl.col(_INPUT_FLAGS)))
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _distance_to_vwap_expression(polars: Any) -> _PackExpression:
    pl = polars
    raw_vwap = _vwap_raw(pl, group_columns=(_SEGMENT,))
    zero_vwap = raw_vwap == 0.0
    value = (
        pl.when(_is_no_trade(pl) | _is_zero_volume(pl) | zero_vwap)
        .then(None)
        .otherwise((pl.col(_CLOSE) - raw_vwap) / raw_vwap)
    )
    flags = (
        pl.when(_is_no_trade(pl))
        .then(_gap_flags(pl, "no_trade", pl.col(_INPUT_FLAGS)))
        .when(_is_zero_volume(pl))
        .then(_gap_flags(pl, "zero_volume", pl.col(_INPUT_FLAGS)))
        .when(zero_vwap)
        .then(_gap_flags(pl, "zero_vwap"))
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _opening_range_expression(polars: Any, opening_minutes: int) -> _PackExpression:
    pl = polars
    in_window = pl.col(_BAR_START) < (
        pl.col(_SEGMENT_START) + pl.duration(minutes=opening_minutes)
    )
    high_input = (
        pl.when(pl.col(_IS_RTH) & in_window & pl.col(_IS_TRADE))
        .then(pl.col(_HIGH))
        .otherwise(None)
    )
    low_input = (
        pl.when(pl.col(_IS_RTH) & in_window & pl.col(_IS_TRADE))
        .then(pl.col(_LOW))
        .otherwise(None)
    )
    opening_high = high_input.cum_max().forward_fill().over(_SEGMENT)
    opening_low = low_input.cum_min().forward_fill().over(_SEGMENT)
    missing_open = opening_high.is_null() | opening_low.is_null()
    value = (
        pl.when(pl.col(_IS_RTH).not_() | missing_open)
        .then(None)
        .otherwise(opening_high - opening_low)
    )
    flags = (
        pl.when(pl.col(_IS_RTH).not_())
        .then(_gap_flags(pl, "outside_rth"))
        .when(missing_open)
        .then(_gap_flags(pl, "no_opening_trade", pl.col(_INPUT_FLAGS)))
        .otherwise(_flags(pl, ()))
    )
    return _PackExpression(value, flags)


def _overnight_range_expression(polars: Any) -> _PackExpression:
    pl = polars
    eth_missing = pl.col(_IS_ETH) & pl.col(_ETH_RANGE).is_null()
    rth_has_range = pl.col(_IS_RTH) & pl.col(_FROZEN_OVERNIGHT_RANGE).is_not_null()
    value = (
        pl.when(pl.col(_IS_ETH) & pl.col(_ETH_RANGE).is_not_null())
        .then(pl.col(_ETH_RANGE))
        .when(rth_has_range)
        .then(pl.col(_FROZEN_OVERNIGHT_RANGE))
        .otherwise(None)
    )
    flags = (
        pl.when(eth_missing)
        .then(_gap_flags(pl, "no_overnight_trade", pl.col(_INPUT_FLAGS)))
        .when(pl.col(_IS_ETH))
        .then(_flags(pl, ()))
        .when(rth_has_range)
        .then(_flags(pl, ()))
        .otherwise(_gap_flags(pl, "no_overnight_range", pl.col(_INPUT_FLAGS)))
    )
    return _PackExpression(value, flags)


def _vwap_raw(
    polars: Any,
    *,
    group_columns: Sequence[str],
    active: Any | None = None,
) -> Any:
    pl = polars
    active_expr = pl.lit(True) if active is None else active
    valid = active_expr & pl.col(_IS_TRADE) & (pl.col(_VOLUME) > 0.0)
    price_volume = (
        pl.when(valid)
        .then(pl.col(_TYPICAL_PRICE) * pl.col(_VOLUME))
        .otherwise(0.0)
    )
    volume = pl.when(valid).then(pl.col(_VOLUME)).otherwise(0.0)
    cumulative_price_volume = price_volume.cum_sum().over(list(group_columns))
    cumulative_volume = volume.cum_sum().over(list(group_columns))
    return cumulative_price_volume / cumulative_volume


def _vwap_gap_flags(polars: Any) -> Any:
    pl = polars
    return (
        pl.when(_is_no_trade(pl))
        .then(_gap_flags(pl, "no_trade", pl.col(_INPUT_FLAGS)))
        .when(_is_zero_volume(pl))
        .then(_gap_flags(pl, "zero_volume", pl.col(_INPUT_FLAGS)))
        .otherwise(_flags(pl, ()))
    )


def _is_no_trade(polars: Any) -> Any:
    return polars.col(_IS_TRADE).not_()


def _is_zero_volume(polars: Any) -> Any:
    return polars.col(_VOLUME) <= 0.0


def _gap_flags(polars: Any, reason: str, extra_flags: Any | None = None) -> Any:
    base_flags = _flags(polars, tuple(sorted(("ohlcv_gap", reason))))
    if extra_flags is None:
        return base_flags
    return polars.concat_list(base_flags, extra_flags).list.unique().list.sort()


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


def _session_label(polars: Any) -> Any:
    return polars.col("session_label").cast(polars.Utf8).str.to_uppercase()


def _flags(polars: Any, values: Sequence[str]) -> Any:
    return polars.lit(list(values), dtype=polars.List(polars.Utf8))


def _anchor_block_column(anchor_label: str) -> str:
    token = re.sub(r"[^A-Z0-9]+", "_", anchor_label.upper()).strip("_").lower()
    if not token:
        raise PackMaterializerError("anchor_session_label cannot normalize to an empty token")
    return f"{_PREFIX}_anchor_block_{token}"


def _require_columns(frame: Any, columns: Sequence[str]) -> None:
    missing = tuple(column for column in columns if column not in frame.columns)
    if missing:
        raise PackMaterializerError("canonical frame missing columns: " + ", ".join(missing))


__all__ = [
    "VWAP_SESSION_AUCTION_FEATURE_IDS",
    "VWAP_SESSION_AUCTION_FEATURE_NAMES",
    "build_vwap_session_auction_pack",
    "supports_vwap_session_auction_pack",
]
