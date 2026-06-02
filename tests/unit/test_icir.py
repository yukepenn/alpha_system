from __future__ import annotations

import pytest

from alpha_system.research.ic import icir


def test_icir_uses_sample_standard_deviation() -> None:
    result = icir([0.1, 0.2, 0.3])

    assert result["n"] == 3
    assert result["mean_ic"] == pytest.approx(0.2)
    assert result["std_ic"] == pytest.approx(0.1)
    assert result["icir"] == pytest.approx(2.0)


def test_icir_is_none_when_variance_is_zero() -> None:
    result = icir([0.1, 0.1, 0.1])

    assert result["icir"] is None
