"""Session / calendar / roll Polars pack for the V1 fast producer path."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import time
from typing import Any

from alpha_system.data.storage import require_dependency
from alpha_system.features.contracts import (
    FeatureFamily,
    FeatureSetSpec,
    FeatureSpec,
    WindowCausality,
    WindowKind,
)
from alpha_system.features.families.session import SessionFeatureName
from alpha_system.features.fast.materializer import (
    FastFeatureDeclaration,
    FastFeaturePack,
    PackMaterializerError,
)

SESSION_CALENDAR_ROLL_FEATURE_IDS: tuple[str, ...] = tuple(
    f"session_calendar_roll_{feature_name.value}" for feature_name in SessionFeatureName
)

_FEATURE_ID_TO_NAME: dict[str, SessionFeatureName] = {
    f"session_calendar_roll_{feature_name.value}": feature_name
    for feature_name in SessionFeatureName
}
_OFFLINE_ROLL_COUNTDOWN_FEATURES = frozenset(
    {
        SessionFeatureName.BARS_TO_ROLL,
        SessionFeatureName.MINUTES_TO_ROLL,
    }
)


@dataclass(frozen=True, slots=True)
class _PackExpression:
    value: Any
    flags: Any


@dataclass(frozen=True, slots=True)
class _RthClock:
    open_seconds: int
    close_seconds: int


def build_session_calendar_roll_pack(feature_set: FeatureSetSpec) -> FastFeaturePack:
    """Build the governed Session / Calendar / Roll fast pack."""

    if not isinstance(feature_set, FeatureSetSpec):
        raise PackMaterializerError("session_calendar_roll fast pack requires a FeatureSetSpec")
    _validate_session_calendar_roll_feature_set(feature_set)
    polars = require_dependency("polars")
    expressions = _session_calendar_roll_expressions(polars, feature_set.features)
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


def supports_session_calendar_roll_pack(feature_set: FeatureSetSpec) -> bool:
    """Return true when a feature set is a governed session pack subset."""

    if not isinstance(feature_set, FeatureSetSpec):
        return False
    try:
        _validate_session_calendar_roll_feature_set(feature_set)
    except PackMaterializerError:
        return False
    return True


def _validate_session_calendar_roll_feature_set(feature_set: FeatureSetSpec) -> None:
    features = tuple(feature_set.features)
    if not features:
        raise PackMaterializerError("session_calendar_roll fast pack requires features")
    feature_ids = tuple(feature.feature_id for feature in features)
    if len(set(feature_ids)) != len(feature_ids):
        raise PackMaterializerError("session_calendar_roll fast pack rejects duplicate features")
    unknown = tuple(
        feature_id
        for feature_id in feature_ids
        if feature_id not in SESSION_CALENDAR_ROLL_FEATURE_IDS
    )
    if unknown:
        raise PackMaterializerError(
            "session_calendar_roll fast pack requires governed Session / Calendar / "
            "Roll features: " + ", ".join(unknown)
        )
    for feature in features:
        _validate_session_calendar_roll_feature(feature)


def _validate_session_calendar_roll_feature(feature: FeatureSpec) -> None:
    if not isinstance(feature, FeatureSpec):
        raise PackMaterializerError(
            "session_calendar_roll pack entries must be FeatureSpec objects"
        )
    if feature.family is not FeatureFamily.SESSION_CALENDAR_ROLL:
        raise PackMaterializerError(
            "session_calendar_roll pack can only contain Session / Calendar / Roll features"
        )
    feature_name = _FEATURE_ID_TO_NAME.get(feature.feature_id)
    if feature_name is None:
        raise PackMaterializerError(
            f"unsupported session_calendar_roll feature_id: {feature.feature_id}"
        )
    parameters = feature.transform.parameters.to_dict()
    _require_parameter(parameters, "feature_name", feature_name.value, feature.feature_id)
    _require_parameter(
        parameters,
        "roll_transition_source",
        "contract_id_or_series_id_transition",
        feature.feature_id,
    )
    _require_parameter(
        parameters,
        "metadata_absence_policy",
        "flag_absent_never_fabricate",
        feature.feature_id,
    )
    rth_open = _clock_parameter(parameters, "rth_open_time_utc", feature.feature_id)
    rth_close = _clock_parameter(parameters, "rth_close_time_utc", feature.feature_id)
    if rth_close <= rth_open:
        raise PackMaterializerError(f"{feature.feature_id} requires rth_close_time_utc after open")
    if feature_name in _OFFLINE_ROLL_COUNTDOWN_FEATURES:
        if (
            feature.window.kind is not WindowKind.FUTURE
            or feature.window.causality is not WindowCausality.FUTURE
            or not feature.window.offline_only
            or feature.live
        ):
            raise PackMaterializerError(
                f"{feature.feature_id} must be offline-only/non-causal"
            )
        return
    if feature.window.kind is not WindowKind.POINT_IN_TIME or feature.window.length != 1:
        raise PackMaterializerError(f"{feature.feature_id} requires a point-in-time window")
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


def _clock_parameter(parameters: Mapping[str, object], name: str, feature_id: str) -> time:
    value = parameters.get(name)
    if not isinstance(value, str):
        raise PackMaterializerError(f"{feature_id} requires {name}=HH:MM")
    parts = value.split(":")
    if len(parts) != 2:
        raise PackMaterializerError(f"{feature_id} requires {name}=HH:MM")
    try:
        return time(hour=int(parts[0], 10), minute=int(parts[1], 10))
    except ValueError as exc:
        raise PackMaterializerError(f"{feature_id} requires {name}=HH:MM") from exc


def _session_calendar_roll_expressions(
    polars: Any,
    features: Sequence[FeatureSpec],
) -> dict[str, _PackExpression]:
    pl = polars
    roll = _roll_expressions(pl)
    expressions: dict[str, _PackExpression] = {}
    for feature in features:
        feature_name = _FEATURE_ID_TO_NAME[feature.feature_id]
        expressions[feature.feature_id] = _feature_expression(
            pl,
            feature_name,
            _rth_clock(feature),
            roll=roll,
        )
    return expressions


def _feature_expression(
    polars: Any,
    feature_name: SessionFeatureName,
    rth_clock: _RthClock,
    *,
    roll: Mapping[str, Any],
) -> _PackExpression:
    pl = polars
    empty = _flags(pl, ())
    if feature_name is SessionFeatureName.SESSION_ID:
        session_id = pl.concat_str(
            [
                pl.col("series_id").cast(pl.Utf8),
                _bar_start_ts(pl).dt.strftime("%Y-%m-%d"),
                _session_label(pl),
            ],
            separator=":",
        )
        return _PackExpression(session_id, _quality_flags(pl, empty))
    if feature_name is SessionFeatureName.MINUTES_FROM_RTH_OPEN:
        value, extra_flags = _rth_minutes(pl, rth_clock, from_open=True)
        return _PackExpression(value, _quality_flags(pl, extra_flags))
    if feature_name is SessionFeatureName.MINUTES_TO_RTH_CLOSE:
        value, extra_flags = _rth_minutes(pl, rth_clock, from_open=False)
        return _PackExpression(value, _quality_flags(pl, extra_flags))
    if feature_name is SessionFeatureName.RTH_SEGMENT_FLAG:
        value = (_session_label(pl) == "RTH").cast(pl.Int64)
        return _PackExpression(value, _quality_flags(pl, empty))
    if feature_name is SessionFeatureName.ETH_SEGMENT_FLAG:
        value = (_session_label(pl) == "ETH").cast(pl.Int64)
        return _PackExpression(value, _quality_flags(pl, empty))
    if feature_name is SessionFeatureName.DAY_OF_WEEK:
        value = (_bar_start_ts(pl).dt.weekday() - 1).cast(pl.Int64)
        return _PackExpression(value, _quality_flags(pl, empty))
    if feature_name is SessionFeatureName.BARS_TO_ROLL:
        absent = roll["target_index"].is_null()
        flags = _conditional_flags(pl, absent, "roll_transition_absent")
        return _PackExpression(roll["bars_to_roll"], _quality_flags(pl, flags))
    if feature_name is SessionFeatureName.MINUTES_TO_ROLL:
        absent = roll["target_index"].is_null()
        flags = _conditional_flags(pl, absent, "roll_transition_absent")
        return _PackExpression(roll["minutes_to_roll"], _quality_flags(pl, flags))
    if feature_name is SessionFeatureName.MINUTES_TO_EXPIRATION:
        flags = _flags(pl, ("expiration_metadata_absent",))
        return _PackExpression(pl.lit(None, dtype=pl.Int64), _quality_flags(pl, flags))
    if feature_name is SessionFeatureName.HALT_STATUS_FLAG:
        flags = _flags(pl, ("status_metadata_absent",))
        return _PackExpression(pl.lit(None, dtype=pl.Int64), _quality_flags(pl, flags))
    raise PackMaterializerError(f"unsupported Session feature: {feature_name}")


def _rth_clock(feature: FeatureSpec) -> _RthClock:
    parameters = feature.transform.parameters.to_dict()
    return _RthClock(
        open_seconds=_seconds_since_midnight(
            _clock_parameter(parameters, "rth_open_time_utc", feature.feature_id)
        ),
        close_seconds=_seconds_since_midnight(
            _clock_parameter(parameters, "rth_close_time_utc", feature.feature_id)
        ),
    )


def _seconds_since_midnight(value: time) -> int:
    return value.hour * 3600 + value.minute * 60 + value.second


def _rth_minutes(
    polars: Any,
    rth_clock: _RthClock,
    *,
    from_open: bool,
) -> tuple[Any, Any]:
    pl = polars
    label = _session_label(pl)
    seconds = (
        _bar_start_ts(pl).dt.hour().cast(pl.Int64) * 3600
        + _bar_start_ts(pl).dt.minute().cast(pl.Int64) * 60
        + _bar_start_ts(pl).dt.second().cast(pl.Int64)
    )
    if from_open:
        raw_minutes = ((seconds - rth_clock.open_seconds) / 60.0).floor().cast(pl.Int64)
        negative_flag = "before_rth_open"
    else:
        raw_minutes = ((rth_clock.close_seconds - seconds) / 60.0).floor().cast(pl.Int64)
        negative_flag = "after_rth_close"
    outside_rth = label != "RTH"
    negative = raw_minutes < 0
    value = pl.when(outside_rth | negative).then(None).otherwise(raw_minutes)
    extra_flags = pl.concat_list(
        _conditional_flags(pl, outside_rth, "outside_rth"),
        _conditional_flags(pl, (label == "RTH") & negative, negative_flag),
    )
    return value, extra_flags


def _roll_expressions(polars: Any) -> dict[str, Any]:
    pl = polars
    bar_start = _bar_start_ts(pl)
    available = _available_ts(pl)
    order_by = [bar_start, available]
    roll_key = pl.concat_str(
        [
            pl.col("contract_id").cast(pl.Utf8),
            pl.lit("\0"),
            pl.col("series_id").cast(pl.Utf8),
        ]
    )
    position = pl.int_range(0, pl.len()).over("instrument_id", order_by=order_by)
    next_key = roll_key.shift(-1).over("instrument_id", order_by=order_by)
    transition = (next_key != roll_key).fill_null(False)
    raw_target = pl.when(transition).then(position + 1).otherwise(None)
    target_index = raw_target.backward_fill().over("instrument_id", order_by=order_by)
    raw_target_ts = (
        pl.when(transition)
        .then(bar_start.shift(-1).over("instrument_id", order_by=order_by))
        .otherwise(None)
    )
    target_ts = raw_target_ts.backward_fill().over("instrument_id", order_by=order_by)
    bars_to_roll = pl.when(target_index.is_null()).then(None).otherwise(target_index - position)
    minutes_to_roll = (
        pl.when(target_ts.is_null())
        .then(None)
        .otherwise((target_ts - bar_start).dt.total_minutes())
    )
    return {
        "target_index": target_index,
        "bars_to_roll": bars_to_roll.cast(pl.Int64),
        "minutes_to_roll": minutes_to_roll.cast(pl.Int64),
    }


def _quality_flags(polars: Any, extra_flags: Any) -> Any:
    pl = polars
    base_flags = _input_quality_flags(pl)
    synthetic_no_trade = _synthetic_no_trade(pl, base_flags)
    no_trade_position_only = (
        base_flags.list.contains("no_trade").fill_null(False) & synthetic_no_trade.not_()
    )
    return (
        pl.concat_list(
            base_flags,
            _conditional_flags(pl, synthetic_no_trade, "synthetic_no_trade_position_only"),
            _conditional_flags(pl, no_trade_position_only, "no_trade_position_only"),
            extra_flags,
        )
        .list.unique()
        .list.sort()
    )


def _synthetic_no_trade(polars: Any, base_flags: Any) -> Any:
    pl = polars
    return (
        pl.col("synthetic").cast(pl.Boolean, strict=False).fill_null(False)
        & pl.col("has_trade").cast(pl.Boolean, strict=False).fill_null(True).not_()
        & (pl.col("fill_method").cast(pl.Utf8, strict=False) == "previous_close").fill_null(False)
        & pl.col("provider_bar_ref").is_null()
        & (pl.col("volume").cast(pl.Float64, strict=False) == 0.0).fill_null(False)
        & base_flags.list.contains("no_trade").fill_null(False)
    )


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


def _conditional_flags(polars: Any, condition: Any, flag: str) -> Any:
    return (
        polars.when(condition)
        .then(_flags(polars, (flag,)))
        .otherwise(_flags(polars, ()))
    )


def _bar_start_ts(polars: Any) -> Any:
    return polars.col("bar_start_ts").cast(polars.Datetime("us", "UTC"), strict=False)


def _available_ts(polars: Any) -> Any:
    return polars.col("available_ts").cast(polars.Datetime("us", "UTC"), strict=False)


def _session_label(polars: Any) -> Any:
    return polars.col("session_label").cast(polars.Utf8).str.to_uppercase()


def _flags(polars: Any, values: Sequence[str]) -> Any:
    return polars.lit(list(values), dtype=polars.List(polars.Utf8))


__all__ = [
    "SESSION_CALENDAR_ROLL_FEATURE_IDS",
    "build_session_calendar_roll_pack",
    "supports_session_calendar_roll_pack",
]
