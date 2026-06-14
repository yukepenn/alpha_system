"""Session / calendar / roll Polars pack for the V1 fast producer path."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date as Date
from datetime import time, timedelta
from functools import lru_cache
from typing import Any

from alpha_system.data.foundation.rolls import (
    CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS,
    build_analytic_cme_equity_index_quarterly_roll_calendar,
)
from alpha_system.data.foundation.sessions import (
    SessionTemplate,
    load_session_template_by_id,
    load_trading_calendar_records,
)
from alpha_system.data.foundation.sources import DataFoundationValidationError
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
from alpha_system.labels.roll_guard import (
    DEFAULT_ROLL_WINDOW_DAYS_AFTER,
    DEFAULT_ROLL_WINDOW_DAYS_BEFORE,
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
    timezone: str
    open_seconds: int
    close_seconds: int
    eth_start_seconds: int
    eth_crosses_midnight: bool


@dataclass(frozen=True, slots=True)
class _CalendarFlagTables:
    start_year: int
    end_year: int
    month_end_sessions: frozenset[str]
    quarter_end_sessions: frozenset[str]
    roll_window_dates_by_root: Mapping[str, frozenset[str]]


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
    template = _session_template_from_parameters(parameters, feature.feature_id)
    rth_open = _clock_parameter(parameters, "rth_open_time_local", feature.feature_id)
    rth_close = _clock_parameter(parameters, "rth_close_time_local", feature.feature_id)
    if rth_open != template.rth_start:
        raise PackMaterializerError(
            f"{feature.feature_id} requires rth_open_time_local from the session template"
        )
    if rth_close != template.rth_end:
        raise PackMaterializerError(
            f"{feature.feature_id} requires rth_close_time_local from the session template"
        )
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
    calendar_tables = _calendar_flag_tables()
    if feature_name is SessionFeatureName.SESSION_ID:
        session_label = _template_session_label(pl, rth_clock)
        session_id = pl.concat_str(
            [
                pl.col("series_id").cast(pl.Utf8),
                _template_trade_date(pl, rth_clock),
                session_label,
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
        value = _is_rth(pl, rth_clock).cast(pl.Int64)
        return _PackExpression(value, _quality_flags(pl, empty))
    if feature_name is SessionFeatureName.ETH_SEGMENT_FLAG:
        value = _is_rth(pl, rth_clock).not_().cast(pl.Int64)
        return _PackExpression(value, _quality_flags(pl, empty))
    if feature_name is SessionFeatureName.DAY_OF_WEEK:
        value = (_bar_start_ts(pl).dt.weekday() - 1).cast(pl.Int64)
        return _PackExpression(value, _quality_flags(pl, empty))
    if feature_name is SessionFeatureName.IS_OPEX_DAY_FLAG:
        value = _is_third_friday(pl, rth_clock).cast(pl.Int64)
        return _PackExpression(value, _quality_flags(pl, empty))
    if feature_name is SessionFeatureName.IS_QUAD_WITCH_DAY_FLAG:
        trade_dt = _template_trade_datetime(pl, rth_clock)
        value = (
            _is_third_friday(pl, rth_clock)
            & trade_dt.dt.month().is_in(list(CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS))
        ).cast(pl.Int64)
        return _PackExpression(value, _quality_flags(pl, empty))
    if feature_name is SessionFeatureName.IS_MONTH_END_SESSION_FLAG:
        value, extra_flags = _covered_calendar_flag(
            pl,
            rth_clock,
            calendar_tables.month_end_sessions,
            calendar_tables=calendar_tables,
        )
        return _PackExpression(value, _quality_flags(pl, extra_flags))
    if feature_name is SessionFeatureName.IS_QUARTER_END_SESSION_FLAG:
        value, extra_flags = _covered_calendar_flag(
            pl,
            rth_clock,
            calendar_tables.quarter_end_sessions,
            calendar_tables=calendar_tables,
        )
        return _PackExpression(value, _quality_flags(pl, extra_flags))
    if feature_name is SessionFeatureName.IN_ROLL_WINDOW_FLAG:
        value = _roll_window_flag(pl, rth_clock, calendar_tables).cast(pl.Int64)
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
    template = _session_template_from_parameters(parameters, feature.feature_id)
    return _RthClock(
        timezone=template.timezone,
        open_seconds=_seconds_since_midnight(template.rth_start),
        close_seconds=_seconds_since_midnight(template.rth_end),
        eth_start_seconds=_seconds_since_midnight(template.eth_start),
        eth_crosses_midnight=_seconds_since_midnight(template.eth_end)
        <= _seconds_since_midnight(template.eth_start),
    )


def _session_template_from_parameters(
    parameters: Mapping[str, object],
    feature_id: str,
) -> SessionTemplate:
    template_id = parameters.get("session_template_id")
    if not isinstance(template_id, str) or not template_id.strip():
        raise PackMaterializerError(f"{feature_id} requires session_template_id")
    try:
        template = load_session_template_by_id(template_id=template_id)
    except DataFoundationValidationError as exc:
        raise PackMaterializerError(str(exc)) from exc
    timezone = parameters.get("session_timezone")
    if timezone != template.timezone:
        raise PackMaterializerError(
            f"{feature_id} requires session_timezone={template.timezone!r}"
        )
    return template


def _seconds_since_midnight(value: time) -> int:
    return value.hour * 3600 + value.minute * 60 + value.second


def _local_bar_start(polars: Any, rth_clock: _RthClock) -> Any:
    return _bar_start_ts(polars).dt.convert_time_zone(rth_clock.timezone)


def _local_seconds(polars: Any, rth_clock: _RthClock) -> Any:
    local = _local_bar_start(polars, rth_clock)
    return (
        local.dt.hour().cast(polars.Int64) * 3600
        + local.dt.minute().cast(polars.Int64) * 60
        + local.dt.second().cast(polars.Int64)
    )


def _is_rth(polars: Any, rth_clock: _RthClock) -> Any:
    seconds = _local_seconds(polars, rth_clock)
    return (seconds >= rth_clock.open_seconds) & (seconds < rth_clock.close_seconds)


def _template_session_label(polars: Any, rth_clock: _RthClock) -> Any:
    return polars.when(_is_rth(polars, rth_clock)).then(
        polars.lit("RTH")
    ).otherwise(polars.lit("ETH"))


def _template_trade_date(polars: Any, rth_clock: _RthClock) -> Any:
    return _template_trade_datetime(polars, rth_clock).dt.strftime("%Y-%m-%d")


def _template_trade_datetime(polars: Any, rth_clock: _RthClock) -> Any:
    local = _local_bar_start(polars, rth_clock)
    if not rth_clock.eth_crosses_midnight:
        return local
    seconds = _local_seconds(polars, rth_clock)
    return polars.when(seconds >= rth_clock.eth_start_seconds).then(
        local.dt.offset_by("1d")
    ).otherwise(local)


def _local_date(polars: Any, rth_clock: _RthClock) -> Any:
    return _local_bar_start(polars, rth_clock).dt.strftime("%Y-%m-%d")


def _is_third_friday(polars: Any, rth_clock: _RthClock) -> Any:
    trade_dt = _template_trade_datetime(polars, rth_clock)
    day = trade_dt.dt.day()
    return (trade_dt.dt.weekday() == 5) & (day >= 15) & (day <= 21)


def _covered_calendar_flag(
    polars: Any,
    rth_clock: _RthClock,
    session_dates: frozenset[str],
    *,
    calendar_tables: _CalendarFlagTables,
) -> tuple[Any, Any]:
    pl = polars
    trade_dt = _template_trade_datetime(pl, rth_clock)
    trade_date = trade_dt.dt.strftime("%Y-%m-%d")
    covered = (trade_dt.dt.year() >= calendar_tables.start_year) & (
        trade_dt.dt.year() <= calendar_tables.end_year
    )
    hit = trade_date.is_in(sorted(session_dates))
    value = pl.when(covered.not_()).then(pl.lit(None, dtype=pl.Int64)).otherwise(
        hit.cast(pl.Int64)
    )
    flags = _conditional_flags(pl, covered.not_(), "session_calendar_coverage_absent")
    return value, flags


def _roll_window_flag(
    polars: Any,
    rth_clock: _RthClock,
    calendar_tables: _CalendarFlagTables,
) -> Any:
    pl = polars
    root = pl.col("instrument_id").cast(pl.Utf8).str.to_uppercase()
    local_date = _local_date(pl, rth_clock)
    expression = pl.lit(False)
    for root_symbol, dates in sorted(calendar_tables.roll_window_dates_by_root.items()):
        expression = expression | ((root == root_symbol) & local_date.is_in(sorted(dates)))
    return expression


@lru_cache(maxsize=1)
def _calendar_flag_tables() -> _CalendarFlagTables:
    try:
        records = load_trading_calendar_records()
    except DataFoundationValidationError as exc:
        raise PackMaterializerError(str(exc)) from exc
    if not records:
        raise PackMaterializerError("session calendar records are required for DK-P01 flags")
    years = tuple(sorted({record.date.year for record in records}))
    start_year = years[0]
    end_year = years[-1]
    full_holidays = frozenset(record.date for record in records if record.is_holiday)
    month_end_sessions: set[str] = set()
    quarter_end_sessions: set[str] = set()
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            end_session = _last_trading_session_of_month(
                year,
                month,
                full_holidays=full_holidays,
            )
            month_end_sessions.add(end_session.isoformat())
            if month in CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS:
                quarter_end_sessions.add(end_session.isoformat())
    roll_dates: dict[str, set[str]] = {}
    try:
        roll_calendar = build_analytic_cme_equity_index_quarterly_roll_calendar(
            start_year=start_year,
            end_year=end_year,
        )
    except DataFoundationValidationError as exc:
        raise PackMaterializerError(str(exc)) from exc
    for record in roll_calendar:
        root_dates = roll_dates.setdefault(record.root_symbol, set())
        for offset in range(
            -DEFAULT_ROLL_WINDOW_DAYS_BEFORE,
            DEFAULT_ROLL_WINDOW_DAYS_AFTER + 1,
        ):
            root_dates.add((record.roll_date + timedelta(days=offset)).isoformat())
    return _CalendarFlagTables(
        start_year=start_year,
        end_year=end_year,
        month_end_sessions=frozenset(month_end_sessions),
        quarter_end_sessions=frozenset(quarter_end_sessions),
        roll_window_dates_by_root={
            root_symbol: frozenset(dates) for root_symbol, dates in roll_dates.items()
        },
    )


def _last_trading_session_of_month(
    year: int,
    month: int,
    *,
    full_holidays: frozenset[Date],
) -> Date:
    if month == 12:
        cursor = Date(year + 1, 1, 1) - timedelta(days=1)
    else:
        cursor = Date(year, month + 1, 1) - timedelta(days=1)
    while cursor.weekday() >= 5 or cursor in full_holidays:
        cursor -= timedelta(days=1)
    if cursor.year != year or cursor.month != month:
        raise PackMaterializerError("calendar coverage produced no trading session for month")
    return cursor


def _rth_minutes(
    polars: Any,
    rth_clock: _RthClock,
    *,
    from_open: bool,
) -> tuple[Any, Any]:
    pl = polars
    seconds = _local_seconds(pl, rth_clock)
    if from_open:
        raw_minutes = ((seconds - rth_clock.open_seconds) / 60.0).floor().cast(pl.Int64)
    else:
        raw_minutes = ((rth_clock.close_seconds - seconds) / 60.0).floor().cast(pl.Int64)
    outside_rth = _is_rth(pl, rth_clock).not_()
    before_open = seconds < rth_clock.open_seconds
    after_close = seconds >= rth_clock.close_seconds
    value = pl.when(outside_rth).then(None).otherwise(raw_minutes)
    extra_flags = pl.concat_list(
        _conditional_flags(pl, outside_rth, "outside_rth"),
        _conditional_flags(pl, outside_rth & before_open, "before_rth_open"),
        _conditional_flags(pl, outside_rth & after_close, "after_rth_close"),
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


def _flags(polars: Any, values: Sequence[str]) -> Any:
    return polars.lit(list(values), dtype=polars.List(polars.Utf8))


__all__ = [
    "SESSION_CALENDAR_ROLL_FEATURE_IDS",
    "build_session_calendar_roll_pack",
    "supports_session_calendar_roll_pack",
]
