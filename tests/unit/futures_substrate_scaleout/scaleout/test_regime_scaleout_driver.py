from __future__ import annotations

from alpha_system.features.scaleout import load_scaleout_config, run_scaleout
from alpha_system.features.scaleout.driver import (
    _unit_executor_for_family,
    materialize_regime_volatility_compression_unit,
)

CONFIG_PATH = "configs/features/scaleout/regime_volatility_compression.json"


def test_regime_scaleout_driver_dispatches_to_p09_executor() -> None:
    assert (
        _unit_executor_for_family("regime_volatility_compression")
        is materialize_regime_volatility_compression_unit
    )


def test_regime_scaleout_full_window_preview_has_accepted_units() -> None:
    config = load_scaleout_config(CONFIG_PATH)

    summary = run_scaleout(config, rollout="full-window")

    assert summary.accepted_unit_count == 24
    assert summary.planned_count == 24
    assert summary.failed_count == 0
    assert {record.unit.year for record in summary.records} == set(range(2019, 2027))
    assert {record.unit.symbol for record in summary.records} == {"ES", "NQ", "RTY"}
    assert all(record.unit.dataset_version_id for record in summary.records)
    assert all(record.feature_version_ids for record in summary.records)
