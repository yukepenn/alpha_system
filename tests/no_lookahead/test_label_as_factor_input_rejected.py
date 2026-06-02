from __future__ import annotations

import pytest

from alpha_system.factors.dependencies import (
    FactorDependencyResolutionError,
    select_declared_bar_inputs,
    validate_compute_dependencies,
)
from alpha_system.factors.spec import FactorSpec, FactorSpecError
from tests.fixtures.factors.synthetic import factor_payload, factor_spec, make_bars


def test_factor_spec_rejects_label_like_declared_input() -> None:
    payload = factor_payload(
        input_fields=[
            {
                "name": "future_return_label",
                "domain": "bar",
                "source_field": "forward_return_1m",
            }
        ],
    )

    with pytest.raises(FactorSpecError, match="label"):
        FactorSpec.from_mapping(payload)


def test_compute_rejects_label_columns_in_available_bar_data() -> None:
    spec = factor_spec()
    bar = dict(make_bars(["100"])[0])
    bar["label_available_ts"] = bar["available_ts"]

    with pytest.raises(FactorDependencyResolutionError, match="label"):
        select_declared_bar_inputs(spec, bar, used_fields=("close_price",))


def test_compute_rejects_label_like_available_columns() -> None:
    spec = factor_spec()

    with pytest.raises(FactorDependencyResolutionError, match="label"):
        validate_compute_dependencies(
            spec,
            available_columns=("close", "forward_return_1m"),
        )
