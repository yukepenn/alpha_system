"""Deterministic label generation from canonical 1-minute bar records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from math import sqrt
from typing import Any

from alpha_system.core.enums import LabelType
from alpha_system.labels.path_metrics import (
    compute_mfe_mae,
    compute_stop_target_ordering,
)
from alpha_system.labels.spec import (
    FORWARD_RETURN_LABEL_TYPES_BY_MINUTE,
    LabelSpec,
)


DEFAULT_FORWARD_RETURN_HORIZONS: tuple[int, ...] = (1, 3, 5, 10, 30)
DEFAULT_PATH_HORIZONS: tuple[int, ...] = (1, 3, 5, 10, 30)


@dataclass(frozen=True, slots=True)
class _Bar:
    instrument_id: str
    session_id: str
    bar_index: int
    bar_start_ts: datetime
    bar_end_ts: datetime
    event_ts: datetime
    available_ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    vwap: Decimal
    trade_count: int
    bid: Decimal | None
    ask: Decimal | None
    spread: Decimal | None
    source_version: str
    data_version: str
    quality_flags: tuple[str, ...]

    def path_mapping(self) -> dict[str, Any]:
        return {
            "bar_index": self.bar_index,
            "event_ts": self.event_ts,
            "high": self.high,
            "low": self.low,
            "close": self.close,
        }


@dataclass(frozen=True, slots=True)
class _Window:
    bars: tuple[_Bar, ...]
    terminal: _Bar | None
    horizon_end_ts: datetime
    label_available_ts: datetime
    insufficient: bool
    reason: str


def generate_standard_labels(
    bars: Iterable[Mapping[str, Any] | Any],
    *,
    label_version: str = "v1",
    forward_horizons: Sequence[int] = DEFAULT_FORWARD_RETURN_HORIZONS,
    path_horizons: Sequence[int] = DEFAULT_PATH_HORIZONS,
    target_return: Decimal | str = Decimal("0.01"),
    stop_return: Decimal | str = Decimal("0.01"),
) -> tuple[LabelSpec, ...]:
    """Generate the ASV1-P10 standard label families for sorted bar fixtures."""
    labels: list[LabelSpec] = []
    labels.extend(
        generate_forward_return_labels(
            bars,
            horizons_minutes=forward_horizons,
            label_version=label_version,
        )
    )
    labels.extend(
        generate_mfe_mae_labels(
            bars,
            horizons_minutes=path_horizons,
            label_version=label_version,
        )
    )
    labels.extend(
        generate_stop_target_ordering_labels(
            bars,
            horizons_minutes=path_horizons,
            target_return=target_return,
            stop_return=stop_return,
            label_version=label_version,
        )
    )
    labels.extend(
        generate_future_realized_volatility_labels(
            bars,
            horizons_minutes=path_horizons,
            label_version=label_version,
        )
    )
    labels.extend(
        generate_future_spread_liquidity_labels(
            bars,
            horizons_minutes=path_horizons,
            label_version=label_version,
        )
    )
    return tuple(labels)


def generate_forward_return_labels(
    bars: Iterable[Mapping[str, Any] | Any],
    *,
    horizons_minutes: Sequence[int] = DEFAULT_FORWARD_RETURN_HORIZONS,
    label_version: str = "v1",
) -> tuple[LabelSpec, ...]:
    """Generate close-to-close forward return labels for standard horizons."""
    normalized = _normalize_bars(bars)
    labels: list[LabelSpec] = []
    for group in _group_bars(normalized):
        for index, bar in enumerate(group):
            for horizon_minutes in horizons_minutes:
                label_type = FORWARD_RETURN_LABEL_TYPES_BY_MINUTE[horizon_minutes]
                window = _window_for_horizon(group, index, horizon_minutes)
                metadata = _base_metadata(
                    bar,
                    window,
                    horizon_minutes=horizon_minutes,
                    label_version=label_version,
                )
                if window.terminal is None or bar.close <= Decimal("0"):
                    value = None
                else:
                    value = float((window.terminal.close / bar.close) - Decimal("1"))
                    metadata["terminal_close"] = str(window.terminal.close)
                labels.append(
                    _label(
                        bar,
                        horizon_minutes=horizon_minutes,
                        label_type=label_type,
                        value=value,
                        path_metadata=metadata,
                    )
                )
    return tuple(labels)


def generate_mfe_mae_labels(
    bars: Iterable[Mapping[str, Any] | Any],
    *,
    horizons_minutes: Sequence[int] = DEFAULT_PATH_HORIZONS,
    label_version: str = "v1",
) -> tuple[LabelSpec, ...]:
    """Generate MFE and MAE labels with path metadata for each horizon."""
    normalized = _normalize_bars(bars)
    labels: list[LabelSpec] = []
    for group in _group_bars(normalized):
        for index, bar in enumerate(group):
            for horizon_minutes in horizons_minutes:
                window = _window_for_horizon(group, index, horizon_minutes)
                metadata = _base_metadata(
                    bar,
                    window,
                    horizon_minutes=horizon_minutes,
                    label_version=label_version,
                )
                if window.insufficient:
                    mfe_value = None
                    mae_value = None
                    excursion_metadata = {"insufficient_path": True}
                else:
                    metrics = compute_mfe_mae(
                        entry_price=bar.close,
                        path_bars=(path_bar.path_mapping() for path_bar in window.bars),
                    )
                    mfe_value = metrics.mfe
                    mae_value = metrics.mae
                    excursion_metadata = metrics.path_metadata
                path_metadata = {**metadata, **excursion_metadata}
                labels.append(
                    _label(
                        bar,
                        horizon_minutes=horizon_minutes,
                        label_type=LabelType.MFE_BY_HORIZON,
                        value=mfe_value,
                        path_metadata=path_metadata,
                    )
                )
                labels.append(
                    _label(
                        bar,
                        horizon_minutes=horizon_minutes,
                        label_type=LabelType.MAE_BY_HORIZON,
                        value=mae_value,
                        path_metadata=path_metadata,
                    )
                )
    return tuple(labels)


def generate_stop_target_ordering_labels(
    bars: Iterable[Mapping[str, Any] | Any],
    *,
    horizons_minutes: Sequence[int] = DEFAULT_PATH_HORIZONS,
    target_return: Decimal | str = Decimal("0.01"),
    stop_return: Decimal | str = Decimal("0.01"),
    label_version: str = "v1",
) -> tuple[LabelSpec, ...]:
    """Generate conservative target-before-stop and stop-before-target labels."""
    normalized = _normalize_bars(bars)
    target = _decimal(target_return)
    stop = _decimal(stop_return)
    labels: list[LabelSpec] = []
    for group in _group_bars(normalized):
        for index, bar in enumerate(group):
            for horizon_minutes in horizons_minutes:
                window = _window_for_horizon(group, index, horizon_minutes)
                metadata = _base_metadata(
                    bar,
                    window,
                    horizon_minutes=horizon_minutes,
                    label_version=label_version,
                )
                if window.insufficient:
                    target_before_stop = None
                    stop_before_target = None
                    ordering_metadata = {"insufficient_path": True}
                else:
                    ordering = compute_stop_target_ordering(
                        entry_price=bar.close,
                        path_bars=(path_bar.path_mapping() for path_bar in window.bars),
                        target_return=target,
                        stop_return=stop,
                    )
                    target_before_stop = ordering.target_before_stop
                    stop_before_target = ordering.stop_before_target
                    ordering_metadata = ordering.path_metadata
                    ordering_metadata["ordering"] = ordering.ordering
                path_metadata = {**metadata, **ordering_metadata}
                labels.append(
                    _label(
                        bar,
                        horizon_minutes=horizon_minutes,
                        label_type=LabelType.TARGET_BEFORE_STOP,
                        value=target_before_stop,
                        path_metadata=path_metadata,
                    )
                )
                labels.append(
                    _label(
                        bar,
                        horizon_minutes=horizon_minutes,
                        label_type=LabelType.STOP_BEFORE_TARGET,
                        value=stop_before_target,
                        path_metadata=path_metadata,
                    )
                )
    return tuple(labels)


def generate_future_realized_volatility_labels(
    bars: Iterable[Mapping[str, Any] | Any],
    *,
    horizons_minutes: Sequence[int] = DEFAULT_PATH_HORIZONS,
    label_version: str = "v1",
) -> tuple[LabelSpec, ...]:
    """Generate future realized volatility labels from close-to-close returns."""
    normalized = _normalize_bars(bars)
    labels: list[LabelSpec] = []
    for group in _group_bars(normalized):
        for index, bar in enumerate(group):
            for horizon_minutes in horizons_minutes:
                window = _window_for_horizon(group, index, horizon_minutes)
                metadata = _base_metadata(
                    bar,
                    window,
                    horizon_minutes=horizon_minutes,
                    label_version=label_version,
                )
                returns = _forward_returns(bar.close, window.bars)
                if window.insufficient or len(returns) < 2:
                    value = None
                    metadata["insufficient_return_count"] = len(returns)
                else:
                    mean = sum(returns) / len(returns)
                    variance = sum((item - mean) ** 2 for item in returns) / len(returns)
                    value = sqrt(variance)
                    metadata["return_count"] = len(returns)
                labels.append(
                    _label(
                        bar,
                        horizon_minutes=horizon_minutes,
                        label_type=LabelType.FUTURE_REALIZED_VOLATILITY,
                        value=value,
                        path_metadata=metadata,
                    )
                )
    return tuple(labels)


def generate_future_spread_liquidity_labels(
    bars: Iterable[Mapping[str, Any] | Any],
    *,
    horizons_minutes: Sequence[int] = DEFAULT_PATH_HORIZONS,
    label_version: str = "v1",
) -> tuple[LabelSpec, ...]:
    """Generate future spread/liquidity labels using mean spread as value."""
    normalized = _normalize_bars(bars)
    labels: list[LabelSpec] = []
    for group in _group_bars(normalized):
        for index, bar in enumerate(group):
            for horizon_minutes in horizons_minutes:
                window = _window_for_horizon(group, index, horizon_minutes)
                metadata = _base_metadata(
                    bar,
                    window,
                    horizon_minutes=horizon_minutes,
                    label_version=label_version,
                )
                spreads = tuple(_bar_spread(path_bar) for path_bar in window.bars)
                if window.insufficient or not spreads or any(item is None for item in spreads):
                    value = None
                    metadata["insufficient_spread_count"] = len(
                        [item for item in spreads if item is not None]
                    )
                else:
                    numeric_spreads = tuple(item for item in spreads if item is not None)
                    avg_spread = sum(numeric_spreads, Decimal("0")) / Decimal(
                        len(numeric_spreads)
                    )
                    total_volume = sum((path_bar.volume for path_bar in window.bars), Decimal("0"))
                    avg_trade_count = sum(path_bar.trade_count for path_bar in window.bars) / len(
                        window.bars
                    )
                    value = float(avg_spread)
                    metadata.update(
                        {
                            "average_spread": str(avg_spread),
                            "total_volume": str(total_volume),
                            "average_trade_count": avg_trade_count,
                        }
                    )
                labels.append(
                    _label(
                        bar,
                        horizon_minutes=horizon_minutes,
                        label_type=LabelType.FUTURE_SPREAD_LIQUIDITY,
                        value=value,
                        path_metadata=metadata,
                    )
                )
    return tuple(labels)


def _normalize_bars(bars: Iterable[Mapping[str, Any] | Any]) -> tuple[_Bar, ...]:
    normalized: list[_Bar] = []
    for raw in bars:
        if isinstance(raw, Mapping):
            payload = raw
        elif is_dataclass(raw):
            payload = asdict(raw)
        else:
            payload = {
                key: getattr(raw, key)
                for key in (
                    "instrument_id",
                    "session_id",
                    "bar_index",
                    "bar_start_ts",
                    "bar_end_ts",
                    "event_ts",
                    "available_ts",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "vwap",
                    "trade_count",
                    "bid",
                    "ask",
                    "spread",
                    "source_version",
                    "data_version",
                    "quality_flags",
                )
            }
        normalized.append(
            _Bar(
                instrument_id=str(payload["instrument_id"]),
                session_id=str(payload["session_id"]),
                bar_index=int(payload["bar_index"]),
                bar_start_ts=_datetime(payload["bar_start_ts"]),
                bar_end_ts=_datetime(payload["bar_end_ts"]),
                event_ts=_datetime(payload["event_ts"]),
                available_ts=_datetime(payload["available_ts"]),
                open=_decimal(payload["open"]),
                high=_decimal(payload["high"]),
                low=_decimal(payload["low"]),
                close=_decimal(payload["close"]),
                volume=_decimal(payload["volume"]),
                vwap=_decimal(payload["vwap"]),
                trade_count=int(payload["trade_count"]),
                bid=_optional_decimal(payload["bid"]),
                ask=_optional_decimal(payload["ask"]),
                spread=_optional_decimal(payload["spread"]),
                source_version=str(payload["source_version"]),
                data_version=str(payload["data_version"]),
                quality_flags=tuple(str(flag) for flag in payload["quality_flags"]),
            )
        )
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                row.instrument_id,
                row.data_version,
                row.session_id,
                row.bar_index,
                row.event_ts,
            ),
        )
    )


def _group_bars(bars: tuple[_Bar, ...]) -> tuple[tuple[_Bar, ...], ...]:
    groups: dict[tuple[str, str, str], list[_Bar]] = {}
    for bar in bars:
        key = (bar.instrument_id, bar.data_version, bar.session_id)
        groups.setdefault(key, []).append(bar)
    return tuple(tuple(group) for group in groups.values())


def _window_for_horizon(group: tuple[_Bar, ...], index: int, horizon_minutes: int) -> _Window:
    current = group[index]
    by_index = {bar.bar_index: bar for bar in group}
    target_index = current.bar_index + int(horizon_minutes)
    required_indexes = range(current.bar_index + 1, target_index + 1)
    path_bars = tuple(by_index[item] for item in required_indexes if item in by_index)
    terminal = by_index.get(target_index)
    session_close_bar = max(group, key=lambda bar: bar.bar_end_ts)
    if terminal is None or len(path_bars) != int(horizon_minutes):
        return _Window(
            bars=path_bars,
            terminal=None,
            horizon_end_ts=session_close_bar.bar_end_ts,
            label_available_ts=max(session_close_bar.available_ts, current.available_ts),
            insufficient=True,
            reason="insufficient_future_bars_before_session_close",
        )
    return _Window(
        bars=path_bars,
        terminal=terminal,
        horizon_end_ts=terminal.event_ts,
        label_available_ts=terminal.available_ts,
        insufficient=False,
        reason="complete",
    )


def _base_metadata(
    bar: _Bar,
    window: _Window,
    *,
    horizon_minutes: int,
    label_version: str,
) -> dict[str, Any]:
    return {
        "session_id": bar.session_id,
        "bar_index": bar.bar_index,
        "label_version": label_version,
        "source_version": bar.source_version,
        "horizon_minutes": int(horizon_minutes),
        "horizon_end_ts": _datetime_to_text(window.horizon_end_ts),
        "label_available_ts": _datetime_to_text(window.label_available_ts),
        "required_future_bars": int(horizon_minutes),
        "observed_future_bars": len(window.bars),
        "insufficient_future": window.insufficient,
        "insufficient_reason": window.reason if window.insufficient else "",
        "clamped_to_session_close": window.insufficient,
    }


def _label(
    bar: _Bar,
    *,
    horizon_minutes: int,
    label_type: LabelType,
    value: Any,
    path_metadata: Mapping[str, Any],
) -> LabelSpec:
    return LabelSpec.from_mapping(
        {
            "label_id": _label_id(label_type, horizon_minutes),
            "instrument_id": bar.instrument_id,
            "event_ts": bar.event_ts,
            "horizon": timedelta(minutes=horizon_minutes),
            "label_type": label_type,
            "value": value,
            "path_metadata": dict(path_metadata),
            "data_version": bar.data_version,
            "label_available_ts": _available_ts_from_metadata_or_bar(path_metadata, bar),
        }
    )


def _available_ts_from_metadata_or_bar(metadata: Mapping[str, Any], bar: _Bar) -> datetime:
    value = metadata.get("label_available_ts")
    if value is None:
        horizon_end = _datetime(metadata["horizon_end_ts"])
        return max(horizon_end, bar.available_ts)
    return _datetime(value)


def _label_id(label_type: LabelType, horizon_minutes: int) -> str:
    if label_type in FORWARD_RETURN_LABEL_TYPES_BY_MINUTE.values():
        return label_type.value
    return f"{label_type.value}_{horizon_minutes}m"


def _forward_returns(entry_close: Decimal, path_bars: Sequence[_Bar]) -> tuple[float, ...]:
    if entry_close <= Decimal("0"):
        return ()
    returns: list[float] = []
    previous = entry_close
    for bar in path_bars:
        if previous <= Decimal("0"):
            return ()
        returns.append(float((bar.close / previous) - Decimal("1")))
        previous = bar.close
    return tuple(returns)


def _bar_spread(bar: _Bar) -> Decimal | None:
    if bar.spread is not None:
        return bar.spread
    if bar.bid is not None and bar.ask is not None:
        return bar.ask - bar.bid
    return None


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _optional_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    return _decimal(value)


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        msg = "bar timestamps must be timezone-aware"
        raise ValueError(msg)
    return parsed.astimezone(timezone.utc)


def _datetime_to_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
