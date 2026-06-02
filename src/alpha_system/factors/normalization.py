"""Point-in-time-safe factor normalization helpers."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from alpha_system.factors.quality import FactorQualityFlag, normalize_quality_flags


class FactorNormalizationError(ValueError):
    """Raised when a normalization configuration is invalid."""


@dataclass(frozen=True, slots=True)
class NormalizationConfig:
    """Deterministic normalization configuration.

    ``history`` supplied to the normalizer must contain only prior point-in-time
    values. The current value is included by this helper, so no future values are
    required or accepted.
    """

    method: str = "identity"
    window_bars: int = 0
    min_periods: int = 1


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    normalized_value: float | None
    quality_flags: tuple[str, ...] = ()


def normalization_config_from_parameters(parameters: Any) -> NormalizationConfig:
    """Build a normalization config from a FactorSpec ``parameters`` mapping."""
    if not isinstance(parameters, dict):
        return NormalizationConfig()
    payload = parameters.get("normalization", {})
    if payload in (None, ""):
        return NormalizationConfig()
    if not isinstance(payload, dict):
        msg = "normalization parameters must be a mapping"
        raise FactorNormalizationError(msg)

    method = str(payload.get("method", "identity")).strip().lower()
    window_bars = _non_negative_int(payload.get("window_bars", 0), "window_bars")
    min_periods = _positive_int(payload.get("min_periods", 1), "min_periods")
    return NormalizationConfig(
        method=method,
        window_bars=window_bars,
        min_periods=min_periods,
    )


def normalize_factor_value(
    value: Any,
    *,
    history: Iterable[Any] = (),
    config: NormalizationConfig | None = None,
) -> NormalizationResult:
    """Normalize a factor value using only prior values plus the current value."""
    active_config = config or NormalizationConfig()
    if value is None:
        return NormalizationResult(normalized_value=None)

    current = _to_float(value)
    if current is None:
        return NormalizationResult(
            normalized_value=None,
            quality_flags=normalize_quality_flags((FactorQualityFlag.NON_NUMERIC_VALUE,)),
        )

    if active_config.method == "identity":
        return NormalizationResult(normalized_value=current)
    if active_config.method != "rolling_zscore":
        msg = f"unsupported normalization method: {active_config.method}"
        raise FactorNormalizationError(msg)

    prior_values = tuple(item for item in (_to_float(item) for item in history) if item is not None)
    if active_config.window_bars > 0:
        prior_values = prior_values[-max(active_config.window_bars - 1, 0) :]
    sample = (*prior_values, current)
    if len(sample) < active_config.min_periods:
        return NormalizationResult(
            normalized_value=None,
            quality_flags=normalize_quality_flags(
                (FactorQualityFlag.NORMALIZATION_UNAVAILABLE,)
            ),
        )

    mean = sum(sample) / len(sample)
    variance = sum((item - mean) ** 2 for item in sample) / len(sample)
    if variance == 0:
        return NormalizationResult(normalized_value=0.0)
    return NormalizationResult(
        normalized_value=(current - mean) / math.sqrt(variance)
    )


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, int | float):
        if not math.isfinite(float(value)):
            return None
        return float(value)
    return None


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"normalization {field_name} must be a non-negative integer"
        raise FactorNormalizationError(msg)
    if value < 0:
        msg = f"normalization {field_name} must be non-negative"
        raise FactorNormalizationError(msg)
    return value


def _positive_int(value: Any, field_name: str) -> int:
    parsed = _non_negative_int(value, field_name)
    if parsed <= 0:
        msg = f"normalization {field_name} must be positive"
        raise FactorNormalizationError(msg)
    return parsed
