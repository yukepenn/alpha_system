from __future__ import annotations

from alpha_system.features.scaleout import load_scaleout_config, run_scaleout
from alpha_system.features.scaleout.driver import (
    _unit_executor_for_family,
    materialize_v1_feature_unit,
    materialize_volume_activity_unit,
)

CONFIG_PATH = "configs/features/scaleout/volume_activity.json"


def test_volume_activity_scaleout_driver_defaults_to_v1_with_reference_fallback() -> None:
    assert _unit_executor_for_family("volume_activity") is materialize_v1_feature_unit
    assert (
        _unit_executor_for_family("volume_activity", engine="reference")
        is materialize_volume_activity_unit
    )


def test_volume_activity_scaleout_full_window_preview_has_accepted_units() -> None:
    config = load_scaleout_config(CONFIG_PATH)

    summary = run_scaleout(config, rollout="full-window")

    assert summary.accepted_unit_count == 24
    assert summary.planned_count == 24
    assert summary.failed_count == 0
    assert {record.unit.year for record in summary.records} == set(range(2019, 2027))
    assert {record.unit.symbol for record in summary.records} == {"ES", "NQ", "RTY"}
    assert all(record.unit.dataset_version_id for record in summary.records)
    assert all(record.feature_version_ids for record in summary.records)
