from __future__ import annotations

from alpha_system.features.scaleout.driver import (
    _unit_executor_for_family,
    materialize_v1_feature_unit,
    materialize_liquidity_sweep_pa_structure_unit,
)


def test_liquidity_pa_scaleout_driver_defaults_to_v1_with_reference_fallback() -> None:
    assert _unit_executor_for_family("liquidity_sweep_pa_structure") is materialize_v1_feature_unit
    assert (
        _unit_executor_for_family("liquidity_sweep_pa_structure", engine="reference")
        is materialize_liquidity_sweep_pa_structure_unit
    )
