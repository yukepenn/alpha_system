from __future__ import annotations

from alpha_system.features.scaleout.driver import (
    _unit_executor_for_family,
    materialize_liquidity_sweep_pa_structure_unit,
)


def test_liquidity_pa_scaleout_driver_dispatches_to_p10_executor() -> None:
    assert (
        _unit_executor_for_family("liquidity_sweep_pa_structure")
        is materialize_liquidity_sweep_pa_structure_unit
    )
