from __future__ import annotations

import pytest

from alpha_system.experiments.grid import GridExpansionError, expand_grid


def test_grid_expansion_rejects_max_combination_overflow_with_reason() -> None:
    with pytest.raises(GridExpansionError) as error:
        expand_grid(
            grid_id="overflow",
            max_combinations=3,
            parameter_space={
                "factor": {"lookback": [2, 3]},
                "strategy": {"direction": ["long", "short"]},
            },
        )

    assert error.value.count == 4
    assert error.value.max_combinations == 3
    assert error.value.rejected_configs
    assert "expands to 4 combinations" in error.value.rejected_configs[0].reason
