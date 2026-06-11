"""LCFP-P08 repair regression: full label definition grid wiring.

The production scaleout wiring must expose the complete configured
name x horizon surface for every label family (the P01 baseline surface):
fixed_base 6, fixed_extended 3, close_out 2, cost_adjusted 18 (2 labels x 9
horizons), path 28 (4 metrics x 7 horizons). Before the repair the
cost_adjusted and path configs collapsed to one default-horizon definition
per label name (2/18 and 4/28).
"""

from __future__ import annotations

import pytest

from alpha_system.features.scaleout import (
    ScaleoutTarget,
    build_scaleout_units,
    load_scaleout_config,
)
from alpha_system.features.scaleout.driver import (
    _fast_label_definitions_for_unit,
    _label_config_needs_horizon_grid,
)

TARGET = ScaleoutTarget(symbols=("ES",), years=(2024,))

FAMILY_SURFACE = {
    # family: (config path, expected units, expected definitions)
    "fixed_base": ("configs/labels/scaleout/fixed_horizon.json", 6, 6),
    "fixed_extended": ("configs/labels/scaleout/extended_horizon.json", 3, 3),
    "close_out": ("configs/labels/scaleout/session_close_maintenance_flat.json", 2, 2),
    "cost_adjusted": ("configs/labels/scaleout/cost_adjusted.json", 9, 18),
    "path": ("configs/labels/scaleout/path.json", 7, 28),
}


@pytest.mark.parametrize(
    ("family", "config_path", "expected_units", "expected_definitions"),
    [
        (family, config_path, units, definitions)
        for family, (config_path, units, definitions) in FAMILY_SURFACE.items()
    ],
)
def test_label_units_cover_the_full_configured_grid(
    family: str,
    config_path: str,
    expected_units: int,
    expected_definitions: int,
) -> None:
    config = load_scaleout_config(config_path)
    units = build_scaleout_units(config, target=TARGET)

    assert len(units) == expected_units
    assert (
        sum(len(_fast_label_definitions_for_unit(config, unit)) for unit in units)
        == expected_definitions
    )


def test_horizon_grid_units_carry_distinct_horizons_and_identities() -> None:
    for family, horizon_count in (("cost_adjusted", 9), ("path", 7)):
        config = load_scaleout_config(FAMILY_SURFACE[family][0])
        assert _label_config_needs_horizon_grid(config)
        units = build_scaleout_units(config, target=TARGET)
        horizons = {unit.horizon for unit in units}
        assert len(horizons) == horizon_count
        assert horizons == set(config.horizons)
        assert len({unit.unit_id for unit in units}) == len(units)
        assert len({unit.partition_id for unit in units}) == len(units)
        for unit in units:
            # Every governed label name rides in every horizon unit.
            assert unit.feature_names == config.label_names
            assert unit.horizon in unit.partition_id


def test_horizon_grid_definitions_use_the_unit_horizon() -> None:
    config = load_scaleout_config(FAMILY_SURFACE["path"][0])
    units = build_scaleout_units(config, target=TARGET)
    by_horizon = {unit.horizon: unit for unit in units}
    definitions = _fast_label_definitions_for_unit(config, by_horizon["240m"])
    assert {definition.horizon_steps for definition in definitions} == {240}
    assert len(definitions) == 4

    cost_config = load_scaleout_config(FAMILY_SURFACE["cost_adjusted"][0])
    cost_units = build_scaleout_units(cost_config, target=TARGET)
    cost_by_horizon = {unit.horizon: unit for unit in cost_units}
    cost_definitions = _fast_label_definitions_for_unit(cost_config, cost_by_horizon["120m"])
    assert len(cost_definitions) == 2
    assert {
        definition.spec.label_contract.horizon.horizon for definition in cost_definitions
    } == {"120m"}


def test_fixed_family_unit_identities_are_unchanged_by_the_grid_repair() -> None:
    """Name-grain families must keep their established unit ids (FUTSUB
    P16-P18 materialized against them)."""

    config = load_scaleout_config(FAMILY_SURFACE["fixed_base"][0])
    assert not _label_config_needs_horizon_grid(config)
    units = build_scaleout_units(config, target=TARGET)
    assert all(unit.horizon == "" for unit in units)
    assert all("horizon" not in unit.to_dict() for unit in units)
    # Golden id computed before the repair (ES 2024 fwd_ret_1m unit): the
    # identity payload of name-grain units must not change.
    by_partition = {unit.partition_id: unit.unit_id for unit in units}
    assert by_partition["ES_2024_fwd_ret_1m"] == "mbu_68b7777e24a6eb98ef16e40d"
