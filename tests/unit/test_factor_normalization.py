from __future__ import annotations

import pytest

from alpha_system.factors.normalization import (
    NormalizationConfig,
    normalize_factor_value,
    normalization_config_from_parameters,
)


def test_identity_normalization_is_deterministic() -> None:
    result = normalize_factor_value(3, history=(1, 2))

    assert result.normalized_value == 3.0
    assert result.quality_flags == ()


def test_rolling_zscore_uses_only_prior_history_plus_current_value() -> None:
    result = normalize_factor_value(
        3,
        history=(1, 2),
        config=NormalizationConfig(
            method="rolling_zscore",
            window_bars=3,
            min_periods=3,
        ),
    )

    assert result.normalized_value == pytest.approx(1.224744871)
    assert result.quality_flags == ()


def test_rolling_zscore_marks_insufficient_periods() -> None:
    result = normalize_factor_value(
        3,
        history=(1,),
        config=NormalizationConfig(
            method="rolling_zscore",
            window_bars=3,
            min_periods=3,
        ),
    )

    assert result.normalized_value is None
    assert result.quality_flags == ("normalization_unavailable",)


def test_normalization_config_parses_factor_parameters() -> None:
    config = normalization_config_from_parameters(
        {"normalization": {"method": "rolling_zscore", "window_bars": 5, "min_periods": 3}}
    )

    assert config.method == "rolling_zscore"
    assert config.window_bars == 5
    assert config.min_periods == 3
