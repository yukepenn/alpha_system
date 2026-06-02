"""Deterministic factor compute driver for canonical 1-minute bars."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

from alpha_system.factors.base import (
    BaseFactor,
    FactorComputeContext,
    FactorValue,
    factor_value_from_parts,
)
from alpha_system.factors.dependencies import select_declared_bar_inputs
from alpha_system.factors.normalization import (
    NormalizationConfig,
    normalize_factor_value,
    normalization_config_from_parameters,
)
from alpha_system.factors.quality import (
    FactorQualityFlag,
    merge_quality_flags,
    normalize_quality_flags,
    propagate_input_quality_flags,
)
from alpha_system.factors.spec import FactorSpec


COMPUTE_VERSION = "factor_compute_sdk_mvp_v1"


class FactorDriverError(ValueError):
    """Raised when the compute driver receives invalid bars or config."""


def compute_factor_values(
    spec: FactorSpec,
    factor: BaseFactor,
    bars: Iterable[Mapping[str, Any]],
    *,
    data_version: str | None = None,
    compute_version: str = COMPUTE_VERSION,
    normalization_config: NormalizationConfig | None = None,
) -> tuple[FactorValue, ...]:
    """Compute factor values with warmup, reset, lag, and quality propagation."""
    sorted_bars = _sort_bars(tuple(bars))
    if not sorted_bars:
        return ()

    active_data_version = data_version or str(sorted_bars[0]["data_version"])
    active_normalization = normalization_config or normalization_config_from_parameters(
        dict(spec.parameters)
    )
    histories: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    raw_histories: dict[tuple[str, str, str], list[Any]] = defaultdict(list)
    values: list[FactorValue] = []

    for bar in sorted_bars:
        _assert_data_version(bar, active_data_version)
        key = _history_key(bar, session_reset=spec.session_reset)
        inputs = select_declared_bar_inputs(spec, bar, used_fields=factor.used_fields)
        history = histories[key]
        history.append(inputs)
        input_quality = _quality_flags_from_bar(bar)
        available_ts = _factor_available_ts(bar, spec.availability_lag)

        if len(history) < max(spec.warmup_bars, 1):
            quality_flags = propagate_input_quality_flags(
                input_quality,
                extra_flags=(FactorQualityFlag.INSUFFICIENT_WARMUP,),
            )
            values.append(
                factor_value_from_parts(
                    spec=spec,
                    bar=bar,
                    available_ts=available_ts,
                    value=None,
                    normalized_value=None,
                    quality_flags=quality_flags,
                    data_version=active_data_version,
                    compute_version=compute_version,
                )
            )
            raw_histories[key].append(None)
            continue

        context = FactorComputeContext(
            spec=spec,
            bar=bar,
            input_history=tuple(history),
        )
        raw_value = factor.compute(inputs, context)
        normalized = normalize_factor_value(
            raw_value,
            history=tuple(raw_histories[key]),
            config=active_normalization,
        )
        quality_flags = merge_quality_flags(
            propagate_input_quality_flags(input_quality),
            normalized.quality_flags,
        )
        values.append(
            factor_value_from_parts(
                spec=spec,
                bar=bar,
                available_ts=available_ts,
                value=raw_value,
                normalized_value=normalized.normalized_value,
                quality_flags=quality_flags,
                data_version=active_data_version,
                compute_version=compute_version,
            )
        )
        raw_histories[key].append(raw_value)
    return tuple(values)


def _sort_bars(bars: Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        sorted(
            bars,
            key=lambda bar: (
                str(bar["instrument_id"]),
                str(bar["data_version"]),
                _datetime_value(bar["event_ts"], "event_ts"),
                str(bar["session_id"]),
                int(bar["bar_index"]),
            ),
        )
    )


def _history_key(
    bar: Mapping[str, Any],
    *,
    session_reset: bool,
) -> tuple[str, str, str]:
    session_part = str(bar["session_id"]) if session_reset else "__all_sessions__"
    return (str(bar["instrument_id"]), str(bar["data_version"]), session_part)


def _factor_available_ts(bar: Mapping[str, Any], lag: timedelta) -> datetime:
    input_available = _datetime_value(bar["available_ts"], "available_ts")
    return input_available + lag


def _assert_data_version(bar: Mapping[str, Any], data_version: str) -> None:
    actual = str(bar["data_version"])
    if actual != data_version:
        msg = f"bar data_version {actual!r} does not match requested {data_version!r}"
        raise FactorDriverError(msg)


def _quality_flags_from_bar(bar: Mapping[str, Any]) -> tuple[str, ...]:
    flags = bar.get("quality_flags", ())
    if isinstance(flags, str):
        flags = tuple(item for item in flags.split("|") if item)
    if not isinstance(flags, Iterable):
        return normalize_quality_flags((flags,))
    return normalize_quality_flags(flags)


def _datetime_value(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        active = value
    elif isinstance(value, str):
        try:
            active = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            msg = f"{field_name} must be ISO-8601 datetime text"
            raise FactorDriverError(msg) from exc
    else:
        msg = f"{field_name} must be datetime or ISO-8601 text"
        raise FactorDriverError(msg)
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc)
