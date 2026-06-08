"""Causal transform, window, and normalization primitives.

All public live primitives in this module order inputs by ``available_ts`` and
use only values at or before the output row's availability timestamp.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from alpha_system.features.contracts import (
    NormalizationSpec,
    TransformSpec,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.semantics import (
    BBOQuoteRow,
    TradeBarRow,
    has_missing_or_abnormal_bbo,
    is_real_trade_bar,
)

type Numeric = int | float | Decimal
_NUMERIC_TYPES = (int, float, Decimal)

GAP_QUALITY_FLAGS: frozenset[str] = frozenset(
    {
        "missing_bbo",
        "bbo_quarantined",
        "no_trade",
        "primitive_gap",
        "input_gap",
    }
)
SUPPORTED_LIVE_TRANSFORMS: frozenset[str] = frozenset(
    {
        "identity",
        "rolling_mean",
        "rolling_std",
        "rolling_volatility",
        "rolling_min",
        "rolling_max",
        "rolling_range",
        "simple_return",
        "return",
        "log_return",
    }
)
SUPPORTED_NORMALIZATIONS: frozenset[str] = frozenset(
    {
        "identity",
        "causal_zscore",
        "zscore",
        "causal_demean",
        "demean",
        "causal_minmax",
        "minmax",
        "minmax_scale",
    }
)


class PrimitiveSpecError(ValueError):
    """Raised when primitive specs fail closed."""


@dataclass(frozen=True, slots=True)
class PrimitivePoint:
    """One primitive input value keyed by explicit ``available_ts``."""

    available_ts: datetime
    value: float | None
    event_ts: datetime | None = None
    session_label: str = ""
    quality_flags: Sequence[str] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "available_ts",
            _require_aware_datetime(self.available_ts, "PrimitivePoint.available_ts"),
        )
        if self.event_ts is not None:
            object.__setattr__(
                self,
                "event_ts",
                _require_aware_datetime(self.event_ts, "PrimitivePoint.event_ts"),
            )
        if self.value is not None:
            object.__setattr__(self, "value", _to_finite_float(self.value, "value"))
        object.__setattr__(self, "session_label", _optional_text(self.session_label))
        object.__setattr__(
            self,
            "quality_flags",
            _normalize_quality_flags(self.quality_flags),
        )

    @property
    def is_gap(self) -> bool:
        """Return true when the point cannot be used as an observed input."""

        return self.value is None or bool(GAP_QUALITY_FLAGS.intersection(self.quality_flags))


@dataclass(frozen=True, slots=True)
class OHLCVPrimitiveBar:
    """OHLCV input for true-range/ATR-style primitives."""

    available_ts: datetime
    high: float | None
    low: float | None
    close: float | None
    event_ts: datetime | None = None
    session_label: str = ""
    quality_flags: Sequence[str] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "available_ts",
            _require_aware_datetime(self.available_ts, "OHLCVPrimitiveBar.available_ts"),
        )
        if self.event_ts is not None:
            object.__setattr__(
                self,
                "event_ts",
                _require_aware_datetime(self.event_ts, "OHLCVPrimitiveBar.event_ts"),
            )
        for field_name in ("high", "low", "close"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _to_finite_float(value, field_name))
        object.__setattr__(self, "session_label", _optional_text(self.session_label))
        object.__setattr__(
            self,
            "quality_flags",
            _normalize_quality_flags(self.quality_flags),
        )

    @property
    def is_gap(self) -> bool:
        """Return true when the bar cannot be used as an observed trade bar."""

        return (
            self.high is None
            or self.low is None
            or self.close is None
            or bool(GAP_QUALITY_FLAGS.intersection(self.quality_flags))
        )


@dataclass(frozen=True, slots=True)
class PrimitiveResult:
    """Primitive output with causality/audit metadata."""

    available_ts: datetime
    value: float | None
    input_count: int
    source_available_ts: Sequence[datetime] = ()
    session_label: str = ""
    quality_flags: Sequence[str] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "available_ts",
            _require_aware_datetime(self.available_ts, "PrimitiveResult.available_ts"),
        )
        if self.value is not None:
            object.__setattr__(self, "value", _to_finite_float(self.value, "value"))
        if self.input_count < 0:
            raise PrimitiveSpecError("PrimitiveResult.input_count must be non-negative")
        object.__setattr__(
            self,
            "source_available_ts",
            tuple(
                _require_aware_datetime(timestamp, "PrimitiveResult.source_available_ts")
                for timestamp in self.source_available_ts
            ),
        )
        object.__setattr__(self, "session_label", _optional_text(self.session_label))
        object.__setattr__(
            self,
            "quality_flags",
            _normalize_quality_flags(self.quality_flags),
        )

    @property
    def is_gap(self) -> bool:
        """Return true when the primitive surfaced a gap instead of a value."""

        return self.value is None or bool(GAP_QUALITY_FLAGS.intersection(self.quality_flags))


@dataclass(frozen=True, slots=True)
class PrimitivePipeline:
    """Spec-bound live primitive pipeline."""

    transform: TransformSpec
    window: WindowSpec
    normalization: NormalizationSpec

    def __post_init__(self) -> None:
        _require_transform_spec(self.transform)
        _require_live_window_spec(self.window)
        _require_normalization_spec(self.normalization)

    def describe(self) -> dict[str, Any]:
        """Return a JSON-compatible description sourced from FLF-P06 specs."""

        return {
            "transform": self.transform.to_dict(),
            "window": self.window.to_dict(),
            "normalization": self.normalization.to_dict(),
            "causality": "available_ts_trailing_only",
            "live_compatible": True,
        }

    def apply(self, points: Iterable[PrimitivePoint]) -> tuple[PrimitiveResult, ...]:
        """Apply transform then normalization using only live-safe primitives."""

        transformed = apply_transform_spec(
            points,
            self.transform,
            self.window,
            reset_on_session=_bool_parameter(
                self.transform.parameters.to_dict(),
                "reset_on_session",
                default=False,
            ),
        )
        return apply_normalization_spec(transformed, self.normalization, self.window)


def build_live_primitive(
    transform: TransformSpec,
    window: WindowSpec,
    normalization: NormalizationSpec,
) -> PrimitivePipeline:
    """Build a live-safe primitive pipeline from FLF-P06 contract specs."""

    return PrimitivePipeline(
        transform=transform,
        window=window,
        normalization=normalization,
    )


def describe_live_primitive(
    transform: TransformSpec,
    window: WindowSpec,
    normalization: NormalizationSpec,
) -> dict[str, Any]:
    """Describe a live primitive without calculating values."""

    return build_live_primitive(transform, window, normalization).describe()


def apply_live_primitive(
    points: Iterable[PrimitivePoint],
    transform: TransformSpec,
    window: WindowSpec,
    normalization: NormalizationSpec,
) -> tuple[PrimitiveResult, ...]:
    """Apply a live-safe primitive pipeline built from FLF-P06 contract specs."""

    return build_live_primitive(transform, window, normalization).apply(points)


def points_from_trade_rows(rows: Iterable[TradeBarRow], field: str) -> tuple[PrimitivePoint, ...]:
    """Project trade rows into primitive points without treating no-trade rows as bars."""

    field_name = _require_field_name(field)
    points: list[PrimitivePoint] = []
    for row in rows:
        if not is_real_trade_bar(row):
            points.append(_gap_point_from_row(row, reason="no_trade"))
            continue
        points.append(
            PrimitivePoint(
                available_ts=row.available_ts,
                event_ts=row.event_ts,
                value=_to_finite_float(getattr(row, field_name), field_name),
                session_label=row.session_label,
                quality_flags=row.quality_flags,
            )
        )
    return tuple(points)


def points_from_bbo_rows(rows: Iterable[BBOQuoteRow], field: str) -> tuple[PrimitivePoint, ...]:
    """Project BBO rows into primitive points, surfacing missing BBO as gaps."""

    field_name = _require_field_name(field)
    points: list[PrimitivePoint] = []
    for row in rows:
        if has_missing_or_abnormal_bbo(row):
            points.append(_gap_point_from_row(row, reason="missing_bbo"))
            continue
        points.append(
            PrimitivePoint(
                available_ts=row.available_ts,
                event_ts=row.event_ts,
                value=_to_finite_float(getattr(row, field_name), field_name),
                session_label=row.session_label,
                quality_flags=row.quality_flags,
            )
        )
    return tuple(points)


def bars_from_trade_rows(rows: Iterable[TradeBarRow]) -> tuple[OHLCVPrimitiveBar, ...]:
    """Project trade rows into OHLCV primitive bars for true range calculations."""

    bars: list[OHLCVPrimitiveBar] = []
    for row in rows:
        if not is_real_trade_bar(row):
            bars.append(
                OHLCVPrimitiveBar(
                    available_ts=row.available_ts,
                    event_ts=row.event_ts,
                    high=None,
                    low=None,
                    close=None,
                    session_label=row.session_label,
                    quality_flags=_with_quality_flag(row.quality_flags, "no_trade"),
                )
            )
            continue
        bars.append(
            OHLCVPrimitiveBar(
                available_ts=row.available_ts,
                event_ts=row.event_ts,
                high=row.high,
                low=row.low,
                close=row.close,
                session_label=row.session_label,
                quality_flags=row.quality_flags,
            )
        )
    return tuple(bars)


def rolling_mean(
    points: Iterable[PrimitivePoint],
    window: int | WindowSpec,
    *,
    reset_on_session: bool = False,
) -> tuple[PrimitiveResult, ...]:
    """Trailing causal rolling mean keyed by ``available_ts``."""

    return _rolling_reduce(
        points,
        window,
        reducer=_mean,
        reset_on_session=reset_on_session,
    )


def rolling_std(
    points: Iterable[PrimitivePoint],
    window: int | WindowSpec,
    *,
    ddof: int = 0,
    reset_on_session: bool = False,
) -> tuple[PrimitiveResult, ...]:
    """Trailing causal rolling standard deviation keyed by ``available_ts``."""

    if ddof < 0:
        raise PrimitiveSpecError("ddof must be non-negative")

    def reducer(values: Sequence[float]) -> float | None:
        if len(values) <= ddof:
            return None
        mean_value = _mean(values)
        variance = sum((value - mean_value) ** 2 for value in values) / (len(values) - ddof)
        return math.sqrt(variance)

    return _rolling_reduce(
        points,
        window,
        reducer=reducer,
        reset_on_session=reset_on_session,
        null_reason="insufficient_window",
    )


def rolling_volatility(
    points: Iterable[PrimitivePoint],
    window: int | WindowSpec,
    *,
    ddof: int = 0,
    reset_on_session: bool = False,
) -> tuple[PrimitiveResult, ...]:
    """Trailing causal rolling volatility alias for standard deviation."""

    return rolling_std(points, window, ddof=ddof, reset_on_session=reset_on_session)


def rolling_min(
    points: Iterable[PrimitivePoint],
    window: int | WindowSpec,
    *,
    reset_on_session: bool = False,
) -> tuple[PrimitiveResult, ...]:
    """Trailing causal rolling minimum keyed by ``available_ts``."""

    return _rolling_reduce(points, window, reducer=min, reset_on_session=reset_on_session)


def rolling_max(
    points: Iterable[PrimitivePoint],
    window: int | WindowSpec,
    *,
    reset_on_session: bool = False,
) -> tuple[PrimitiveResult, ...]:
    """Trailing causal rolling maximum keyed by ``available_ts``."""

    return _rolling_reduce(points, window, reducer=max, reset_on_session=reset_on_session)


def rolling_range(
    points: Iterable[PrimitivePoint],
    window: int | WindowSpec,
    *,
    reset_on_session: bool = False,
) -> tuple[PrimitiveResult, ...]:
    """Trailing causal rolling range keyed by ``available_ts``."""

    return _rolling_reduce(
        points,
        window,
        reducer=lambda values: max(values) - min(values),
        reset_on_session=reset_on_session,
    )


def simple_returns(
    points: Iterable[PrimitivePoint],
    horizon: int | WindowSpec = 1,
    *,
    reset_on_session: bool = False,
) -> tuple[PrimitiveResult, ...]:
    """Simple trailing returns over a causal horizon."""

    return _return_values(points, horizon, math.log1p, reset_on_session, log_return=False)


def log_returns(
    points: Iterable[PrimitivePoint],
    horizon: int | WindowSpec = 1,
    *,
    reset_on_session: bool = False,
) -> tuple[PrimitiveResult, ...]:
    """Log trailing returns over a causal horizon."""

    return _return_values(points, horizon, math.log, reset_on_session, log_return=True)


def true_range(
    bars: Iterable[OHLCVPrimitiveBar],
    *,
    reset_on_session: bool = False,
) -> tuple[PrimitiveResult, ...]:
    """Causal true-range values from OHLCV bars ordered by ``available_ts``."""

    ordered = _ordered_bars(bars)
    previous_close: float | None = None
    previous_close_available_ts: datetime | None = None
    previous_session = ""
    results: list[PrimitiveResult] = []
    for bar in ordered:
        if reset_on_session and bar.session_label != previous_session:
            previous_close = None
            previous_close_available_ts = None
        previous_session = bar.session_label
        if bar.is_gap:
            results.append(_gap_bar_result(bar, "input_gap"))
            continue
        assert bar.high is not None
        assert bar.low is not None
        assert bar.close is not None
        if previous_close is None:
            value = bar.high - bar.low
            source_available_ts = (bar.available_ts,)
        else:
            value = max(
                bar.high - bar.low,
                abs(bar.high - previous_close),
                abs(bar.low - previous_close),
            )
            assert previous_close_available_ts is not None
            source_available_ts = (previous_close_available_ts, bar.available_ts)
        results.append(
            PrimitiveResult(
                available_ts=bar.available_ts,
                value=value,
                input_count=1,
                source_available_ts=source_available_ts,
                session_label=bar.session_label,
            )
        )
        previous_close = bar.close
        previous_close_available_ts = bar.available_ts
    return tuple(results)


def average_true_range(
    bars: Iterable[OHLCVPrimitiveBar],
    window: int | WindowSpec,
    *,
    reset_on_session: bool = False,
) -> tuple[PrimitiveResult, ...]:
    """ATR-style trailing mean of causal true-range values."""

    tr_points = (
        PrimitivePoint(
            available_ts=result.available_ts,
            value=result.value,
            session_label=result.session_label,
            quality_flags=result.quality_flags,
        )
        for result in true_range(bars, reset_on_session=reset_on_session)
    )
    return rolling_mean(tr_points, window, reset_on_session=reset_on_session)


def causal_zscore(
    points: Iterable[PrimitivePoint],
    window: int | WindowSpec,
    *,
    ddof: int = 0,
    reset_on_session: bool = False,
) -> tuple[PrimitiveResult, ...]:
    """Causal z-score using only the trailing window available at each timestamp."""

    if ddof < 0:
        raise PrimitiveSpecError("ddof must be non-negative")

    def reducer(values: Sequence[float]) -> float | None:
        if len(values) <= ddof:
            return None
        mean_value = _mean(values)
        variance = sum((value - mean_value) ** 2 for value in values) / (len(values) - ddof)
        std_value = math.sqrt(variance)
        if std_value == 0:
            return None
        return (values[-1] - mean_value) / std_value

    return _rolling_reduce(
        points,
        window,
        reducer=reducer,
        reset_on_session=reset_on_session,
        null_reason="zero_variance",
    )


def causal_demean(
    points: Iterable[PrimitivePoint],
    window: int | WindowSpec,
    *,
    reset_on_session: bool = False,
) -> tuple[PrimitiveResult, ...]:
    """Causal demeaned value using the trailing window mean."""

    return _rolling_reduce(
        points,
        window,
        reducer=lambda values: values[-1] - _mean(values),
        reset_on_session=reset_on_session,
    )


def causal_minmax_scale(
    points: Iterable[PrimitivePoint],
    window: int | WindowSpec,
    *,
    reset_on_session: bool = False,
) -> tuple[PrimitiveResult, ...]:
    """Causal min-max scaling using the trailing window range."""

    def reducer(values: Sequence[float]) -> float | None:
        min_value = min(values)
        max_value = max(values)
        if max_value == min_value:
            return None
        return (values[-1] - min_value) / (max_value - min_value)

    return _rolling_reduce(
        points,
        window,
        reducer=reducer,
        reset_on_session=reset_on_session,
        null_reason="zero_range",
    )


def session_reset_groups(
    points: Iterable[PrimitivePoint],
) -> tuple[tuple[PrimitivePoint, ...], ...]:
    """Split an available-time ordered series whenever the session label changes."""

    groups: list[list[PrimitivePoint]] = []
    for point in _ordered_points(points):
        if not groups or point.session_label != groups[-1][-1].session_label:
            groups.append([point])
        else:
            groups[-1].append(point)
    return tuple(tuple(group) for group in groups)


def apply_transform_spec(
    points: Iterable[PrimitivePoint],
    transform: TransformSpec,
    window: WindowSpec,
    *,
    reset_on_session: bool = False,
) -> tuple[PrimitiveResult, ...]:
    """Apply a live-safe transform selected by ``TransformSpec``."""

    transform = _require_transform_spec(transform)
    window = _require_live_window_spec(window)
    transform_id = transform.transform_id
    parameters = transform.parameters.to_dict()
    if transform_id not in SUPPORTED_LIVE_TRANSFORMS:
        raise PrimitiveSpecError(f"unsupported live transform_id: {transform_id}")
    if transform_id == "identity":
        return _identity_results(points)
    if transform_id == "rolling_mean":
        return rolling_mean(points, window, reset_on_session=reset_on_session)
    if transform_id == "rolling_std":
        return rolling_std(
            points,
            window,
            ddof=_int_parameter(parameters, "ddof", default=0),
            reset_on_session=reset_on_session,
        )
    if transform_id == "rolling_volatility":
        return rolling_volatility(
            points,
            window,
            ddof=_int_parameter(parameters, "ddof", default=0),
            reset_on_session=reset_on_session,
        )
    if transform_id == "rolling_min":
        return rolling_min(points, window, reset_on_session=reset_on_session)
    if transform_id == "rolling_max":
        return rolling_max(points, window, reset_on_session=reset_on_session)
    if transform_id == "rolling_range":
        return rolling_range(points, window, reset_on_session=reset_on_session)
    if transform_id in {"simple_return", "return"}:
        return simple_returns(
            points,
            _int_parameter(parameters, "horizon", default=window.length),
            reset_on_session=reset_on_session,
        )
    if transform_id == "log_return":
        return log_returns(
            points,
            _int_parameter(parameters, "horizon", default=window.length),
            reset_on_session=reset_on_session,
        )
    raise PrimitiveSpecError(f"unsupported live transform_id: {transform_id}")


def apply_normalization_spec(
    values: Iterable[PrimitiveResult],
    normalization: NormalizationSpec,
    window: WindowSpec,
) -> tuple[PrimitiveResult, ...]:
    """Apply causal normalization selected by ``NormalizationSpec``."""

    normalization = _require_normalization_spec(normalization)
    window = _require_live_window_spec(window)
    normalization_id = normalization.normalization_id
    parameters = normalization.parameters.to_dict()
    if normalization_id not in SUPPORTED_NORMALIZATIONS:
        raise PrimitiveSpecError(f"unsupported normalization_id: {normalization_id}")
    if normalization_id == "identity":
        return tuple(values)
    points = (
        PrimitivePoint(
            available_ts=value.available_ts,
            value=value.value,
            session_label=value.session_label,
            quality_flags=value.quality_flags,
        )
        for value in values
    )
    reset_on_session = _bool_parameter(parameters, "reset_on_session", default=False)
    if normalization_id in {"causal_zscore", "zscore"}:
        return causal_zscore(
            points,
            window,
            ddof=_int_parameter(parameters, "ddof", default=0),
            reset_on_session=reset_on_session,
        )
    if normalization_id in {"causal_demean", "demean"}:
        return causal_demean(points, window, reset_on_session=reset_on_session)
    if normalization_id in {"causal_minmax", "minmax", "minmax_scale"}:
        return causal_minmax_scale(points, window, reset_on_session=reset_on_session)
    raise PrimitiveSpecError(f"unsupported normalization_id: {normalization_id}")


def _rolling_reduce(
    points: Iterable[PrimitivePoint],
    window: int | WindowSpec,
    *,
    reducer: Callable[[Sequence[float]], float | None],
    reset_on_session: bool,
    null_reason: str = "undefined",
) -> tuple[PrimitiveResult, ...]:
    window_shape = _window_shape(window)
    ordered = _ordered_points(points)
    results: list[PrimitiveResult] = []
    for index, point in enumerate(ordered):
        window_points = _causal_window_points(
            ordered,
            index,
            window_shape,
            reset_on_session=reset_on_session,
        )
        if len(window_points) < window_shape.minimum_count:
            results.append(_gap_result(point, "insufficient_window", window_points))
            continue
        if any(window_point.is_gap for window_point in window_points):
            results.append(_gap_result(point, "input_gap", window_points))
            continue
        values = [window_point.value for window_point in window_points]
        if any(value is None for value in values):
            results.append(_gap_result(point, "input_gap", window_points))
            continue
        reduced = reducer([float(value) for value in values if value is not None])
        if reduced is None:
            results.append(_gap_result(point, null_reason, window_points))
            continue
        results.append(
            PrimitiveResult(
                available_ts=point.available_ts,
                value=reduced,
                input_count=len(window_points),
                source_available_ts=tuple(item.available_ts for item in window_points),
                session_label=point.session_label,
            )
        )
    return tuple(results)


def _return_values(
    points: Iterable[PrimitivePoint],
    horizon: int | WindowSpec,
    transform: Callable[[float], float],
    reset_on_session: bool,
    *,
    log_return: bool,
) -> tuple[PrimitiveResult, ...]:
    horizon_length = _positive_horizon(horizon)
    ordered = _ordered_points(points)
    results: list[PrimitiveResult] = []
    for index, point in enumerate(ordered):
        prior_index = index - horizon_length
        if prior_index < 0:
            results.append(_gap_result(point, "insufficient_window", (point,)))
            continue
        prior = ordered[prior_index]
        if reset_on_session and prior.session_label != point.session_label:
            results.append(_gap_result(point, "session_reset", (prior, point)))
            continue
        if reset_on_session and any(
            ordered[between_index].session_label != point.session_label
            for between_index in range(prior_index, index + 1)
        ):
            source_points = tuple(ordered[prior_index : index + 1])
            results.append(_gap_result(point, "session_reset", source_points))
            continue
        if point.is_gap or prior.is_gap or point.value is None or prior.value is None:
            results.append(_gap_result(point, "input_gap", (prior, point)))
            continue
        if prior.value == 0:
            results.append(_gap_result(point, "zero_denominator", (prior, point)))
            continue
        if log_return and (point.value <= 0 or prior.value <= 0):
            results.append(_gap_result(point, "non_positive_price", (prior, point)))
            continue
        if log_return:
            value = transform(point.value / prior.value)
        else:
            value = point.value / prior.value - 1.0
        results.append(
            PrimitiveResult(
                available_ts=point.available_ts,
                value=value,
                input_count=2,
                source_available_ts=(prior.available_ts, point.available_ts),
                session_label=point.session_label,
            )
        )
    return tuple(results)


@dataclass(frozen=True, slots=True)
class _WindowShape:
    length: int
    kind: WindowKind
    minimum_count: int


def _window_shape(window: int | WindowSpec) -> _WindowShape:
    if isinstance(window, int):
        length = _positive_int(window, "window")
        return _WindowShape(length=length, kind=WindowKind.ROLLING, minimum_count=length)
    spec = _require_live_window_spec(window)
    if spec.kind is WindowKind.POINT_IN_TIME:
        return _WindowShape(length=1, kind=WindowKind.POINT_IN_TIME, minimum_count=1)
    if spec.kind is WindowKind.EXPANDING:
        return _WindowShape(
            length=spec.length,
            kind=WindowKind.EXPANDING,
            minimum_count=spec.length,
        )
    if spec.kind is WindowKind.ROLLING:
        return _WindowShape(length=spec.length, kind=WindowKind.ROLLING, minimum_count=spec.length)
    raise PrimitiveSpecError("live primitives only support point_in_time, rolling, or expanding")


def _causal_window_points(
    points: Sequence[PrimitivePoint],
    index: int,
    shape: _WindowShape,
    *,
    reset_on_session: bool,
) -> tuple[PrimitivePoint, ...]:
    current = points[index]
    if shape.kind is WindowKind.EXPANDING:
        # Expanding windows span the whole (optionally session-scoped) history, so
        # the session boundary must be searched back to the start.
        start = 0
        if reset_on_session:
            for prior_index in range(index - 1, -1, -1):
                if points[prior_index].session_label != current.session_label:
                    start = prior_index + 1
                    break
        return tuple(points[start : index + 1])
    # Rolling / point-in-time windows are bounded by ``shape.length``, so a session
    # reset can only shrink the window within the last ``length`` bars. Bound the
    # backward session scan to that span: scanning all the way to index 0 made
    # reset_on_session rolling features (e.g. ATR rolling_mean) O(n^2) and hung a
    # full-year unit. The result is identical -- the original took
    # max(session_start, index - length + 1), which only depends on session
    # boundaries inside the window.
    lower = max(0, index - shape.length + 1)
    start = lower
    if reset_on_session:
        for prior_index in range(index - 1, lower - 1, -1):
            if points[prior_index].session_label != current.session_label:
                start = prior_index + 1
                break
    return tuple(points[start : index + 1])


def _identity_results(points: Iterable[PrimitivePoint]) -> tuple[PrimitiveResult, ...]:
    return tuple(
        PrimitiveResult(
            available_ts=point.available_ts,
            value=point.value,
            input_count=1,
            source_available_ts=(point.available_ts,),
            session_label=point.session_label,
            quality_flags=point.quality_flags,
        )
        for point in _ordered_points(points)
    )


def _ordered_points(points: Iterable[PrimitivePoint]) -> tuple[PrimitivePoint, ...]:
    enumerated = tuple(enumerate(points))
    for _, point in enumerated:
        if not isinstance(point, PrimitivePoint):
            raise PrimitiveSpecError("primitive inputs must be PrimitivePoint objects")
    return tuple(
        point
        for _, point in sorted(enumerated, key=lambda item: (item[1].available_ts, item[0]))
    )


def _ordered_bars(bars: Iterable[OHLCVPrimitiveBar]) -> tuple[OHLCVPrimitiveBar, ...]:
    enumerated = tuple(enumerate(bars))
    for _, bar in enumerated:
        if not isinstance(bar, OHLCVPrimitiveBar):
            raise PrimitiveSpecError("true_range inputs must be OHLCVPrimitiveBar objects")
    return tuple(
        bar for _, bar in sorted(enumerated, key=lambda item: (item[1].available_ts, item[0]))
    )


def _gap_result(
    point: PrimitivePoint,
    reason: str,
    source_points: Sequence[PrimitivePoint],
) -> PrimitiveResult:
    flags = {reason, "primitive_gap"}
    for source_point in source_points:
        flags.update(source_point.quality_flags)
    return PrimitiveResult(
        available_ts=point.available_ts,
        value=None,
        input_count=len(source_points),
        source_available_ts=tuple(source_point.available_ts for source_point in source_points),
        session_label=point.session_label,
        quality_flags=tuple(sorted(flags)),
    )


def _gap_bar_result(bar: OHLCVPrimitiveBar, reason: str) -> PrimitiveResult:
    return PrimitiveResult(
        available_ts=bar.available_ts,
        value=None,
        input_count=1,
        source_available_ts=(bar.available_ts,),
        session_label=bar.session_label,
        quality_flags=tuple(sorted({"primitive_gap", reason, *bar.quality_flags})),
    )


def _gap_point_from_row(row: TradeBarRow | BBOQuoteRow, *, reason: str) -> PrimitivePoint:
    return PrimitivePoint(
        available_ts=row.available_ts,
        event_ts=row.event_ts,
        value=None,
        session_label=row.session_label,
        quality_flags=_with_quality_flag(row.quality_flags, reason),
    )


def _with_quality_flag(flags: Sequence[str], flag: str) -> tuple[str, ...]:
    return tuple(sorted({*_normalize_quality_flags(flags), flag.lower()}))


def _require_transform_spec(transform: TransformSpec) -> TransformSpec:
    if not isinstance(transform, TransformSpec):
        raise PrimitiveSpecError("transform must be an FLF-P06 TransformSpec")
    return transform


def _require_normalization_spec(normalization: NormalizationSpec) -> NormalizationSpec:
    if not isinstance(normalization, NormalizationSpec):
        raise PrimitiveSpecError("normalization must be an FLF-P06 NormalizationSpec")
    return normalization


def _require_live_window_spec(window: WindowSpec) -> WindowSpec:
    if not isinstance(window, WindowSpec):
        raise PrimitiveSpecError("window must be an FLF-P06 WindowSpec")
    if window.anchor != "available_ts":
        raise PrimitiveSpecError("live primitives require WindowSpec.anchor='available_ts'")
    if window.causality is not WindowCausality.CAUSAL or window.offline_only:
        raise PrimitiveSpecError(
            "live primitives cannot bind centered, future, or offline-only windows"
        )
    if window.kind in {WindowKind.CENTERED, WindowKind.FUTURE}:
        raise PrimitiveSpecError("centered/future windows are offline-only")
    return window


def _positive_horizon(horizon: int | WindowSpec) -> int:
    if isinstance(horizon, WindowSpec):
        _require_live_window_spec(horizon)
        return horizon.length
    return _positive_int(horizon, "horizon")


def _positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise PrimitiveSpecError(f"{field_name} must be a positive integer")
    return value


def _int_parameter(parameters: dict[str, Any], key: str, *, default: int) -> int:
    value = parameters.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool):
        raise PrimitiveSpecError(f"{key} parameter must be an integer")
    return value


def _bool_parameter(parameters: dict[str, Any], key: str, *, default: bool) -> bool:
    value = parameters.get(key, default)
    if type(value) is not bool:
        raise PrimitiveSpecError(f"{key} parameter must be a bool")
    return value


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise PrimitiveSpecError(f"{field_name} must be a timezone-aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise PrimitiveSpecError(f"{field_name} must be timezone-aware")
    return value


def _require_field_name(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PrimitiveSpecError("field must be a non-empty string")
    return value.strip()


def _optional_text(value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise PrimitiveSpecError("session_label must be a string")
    return value.strip()


def _normalize_quality_flags(flags: Sequence[str]) -> tuple[str, ...]:
    if isinstance(flags, str) or not isinstance(flags, Sequence):
        raise PrimitiveSpecError("quality_flags must be a sequence of strings")
    normalized: list[str] = []
    for flag in flags:
        if not isinstance(flag, str) or not flag.strip():
            raise PrimitiveSpecError("quality_flags must contain non-empty strings")
        token = flag.strip().lower()
        if token not in normalized:
            normalized.append(token)
    return tuple(normalized)


def _to_finite_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, _NUMERIC_TYPES):
        raise PrimitiveSpecError(f"{field_name} must be a finite numeric value")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise PrimitiveSpecError(f"{field_name} must be finite")
    return parsed


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


__all__ = [
    "GAP_QUALITY_FLAGS",
    "OHLCVPrimitiveBar",
    "PrimitivePipeline",
    "PrimitivePoint",
    "PrimitiveResult",
    "PrimitiveSpecError",
    "SUPPORTED_LIVE_TRANSFORMS",
    "SUPPORTED_NORMALIZATIONS",
    "apply_live_primitive",
    "apply_normalization_spec",
    "apply_transform_spec",
    "average_true_range",
    "bars_from_trade_rows",
    "build_live_primitive",
    "causal_demean",
    "causal_minmax_scale",
    "causal_zscore",
    "describe_live_primitive",
    "log_returns",
    "points_from_bbo_rows",
    "points_from_trade_rows",
    "rolling_max",
    "rolling_mean",
    "rolling_min",
    "rolling_range",
    "rolling_std",
    "rolling_volatility",
    "session_reset_groups",
    "simple_returns",
    "true_range",
]
