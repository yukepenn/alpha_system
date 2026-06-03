from __future__ import annotations

import pytest

from alpha_system.experiments.management_grid import ManagementGridExpansionError, expand_management_grid


def test_management_grid_max_combinations_overflow_is_rejected_not_truncated() -> None:
    with pytest.raises(ManagementGridExpansionError) as error:
        expand_management_grid(
            grid_id="overflow",
            max_combinations=3,
            parameter_space={
                "management": {
                    "fixed_stop.stop_pct": ["0.01", "0.02"],
                    "cooldown.bars": [1, 2],
                }
            },
        )

    assert error.value.count == 4
    assert error.value.max_combinations == 3
    assert error.value.rejected_configs[0].config_id == "grid"
    assert "expands to 4 combinations" in error.value.rejected_configs[0].reason
