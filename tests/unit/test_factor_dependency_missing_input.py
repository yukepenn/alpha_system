from __future__ import annotations

import pytest

from alpha_system.factors.dependencies import (
    FactorDependencyResolutionError,
    select_declared_bar_inputs,
)
from tests.fixtures.factors.synthetic import factor_spec, make_bars


def test_missing_declared_input_is_rejected() -> None:
    spec = factor_spec()
    bar = dict(make_bars(["100"])[0])
    bar.pop("close")

    with pytest.raises(FactorDependencyResolutionError, match="missing declared"):
        select_declared_bar_inputs(spec, bar, used_fields=("close_price",))
