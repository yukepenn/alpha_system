from __future__ import annotations

import pytest

from alpha_system.factors.dependencies import (
    FactorDependencyResolutionError,
    select_declared_bar_inputs,
    validate_compute_dependencies,
)
from tests.fixtures.factors.synthetic import factor_payload, factor_spec, make_bars


def test_dependency_resolution_returns_only_declared_inputs() -> None:
    spec = factor_spec()
    bar = make_bars(["100"])[0]

    inputs = select_declared_bar_inputs(spec, bar, used_fields=("close_price",))

    assert inputs == {"close_price": bar["close"]}


def test_dependency_resolution_rejects_ad_hoc_columns() -> None:
    spec = factor_spec()
    bar = dict(make_bars(["100"])[0])
    bar["raw_close"] = bar["close"]

    with pytest.raises(FactorDependencyResolutionError, match="ad-hoc"):
        select_declared_bar_inputs(spec, bar, used_fields=("close_price",))


def test_compute_dependencies_require_canonical_bar_source_fields() -> None:
    spec = factor_spec(
        input_fields=[
            {"name": "close_price", "domain": "bar", "source_field": "noncanonical"}
        ],
    )

    with pytest.raises(FactorDependencyResolutionError, match="canonical"):
        validate_compute_dependencies(spec, available_columns=("noncanonical",))


def test_compute_dependencies_reject_undeclared_used_fields() -> None:
    spec = factor_spec()

    with pytest.raises(FactorDependencyResolutionError, match="undeclared"):
        validate_compute_dependencies(spec, used_fields=("close_price", "raw_close"))


def test_compute_dependencies_reject_non_bar_domains() -> None:
    spec = factor_spec(
        input_fields=[
            {"name": "close_price", "domain": "quote", "source_field": "close"}
        ],
    )

    with pytest.raises(FactorDependencyResolutionError, match="canonical bar"):
        validate_compute_dependencies(spec)
