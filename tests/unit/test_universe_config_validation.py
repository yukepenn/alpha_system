from __future__ import annotations

import pytest

from alpha_system.core.instrument_master import InstrumentMasterCatalog
from alpha_system.data.universe import UniverseSpec, UniverseSpecError


def test_universe_config_supports_required_multi_symbol_fields() -> None:
    universe = UniverseSpec.from_mapping(_universe_payload())

    assert universe.universe_id == "tiny_multi"
    assert universe.data_version == "synthetic:universe:v1"
    assert universe.active_instrument_ids("2026-01-02") == ("EQ_US_SYNTH_A", "EQ_US_SYNTH_B")
    assert universe.members[0].exchange == "XNYS"
    assert universe.members[0].currency == "USD"
    assert universe.members[0].timezone == "America/New_York"
    assert universe.inclusion_rules == ("explicit_synthetic_fixture_members",)
    assert universe.exclusion_rules == ("no_real_market_data",)
    assert universe.future_sector_constraints[0].parameters["sector"] == "synthetic_sector"
    assert universe.future_asset_constraints[0].parameters["asset_class"] == "equity"
    assert len(universe.config_hash()) == 64


def test_universe_config_hash_is_deterministic_when_member_order_changes() -> None:
    payload = _universe_payload()
    reversed_payload = {**payload, "instruments": list(reversed(payload["instruments"]))}

    assert UniverseSpec.from_mapping(payload).config_hash() == UniverseSpec.from_mapping(reversed_payload).config_hash()


def test_universe_rejects_enabled_future_constraints() -> None:
    payload = {
        **_universe_payload(),
        "future_sector_constraints": [{"constraint_id": "sector", "enabled": True}],
    }

    with pytest.raises(UniverseSpecError, match="representation only"):
        UniverseSpec.from_mapping(payload)


def test_symbol_only_members_resolve_to_instrument_id_through_master() -> None:
    catalog = InstrumentMasterCatalog.from_mappings((_instrument_payload(),))
    universe = UniverseSpec.from_mapping(
        {
            "universe_id": "symbol_resolution",
            "name": "Symbol Resolution",
            "data_version": "synthetic:universe:v1",
            "instruments": [{"symbol": "SYN-A", "start_date": "2026-01-01"}],
        },
        instrument_master=catalog,
    )

    assert universe.members[0].instrument_id == "EQ_US_SYNTH_A"
    assert universe.members[0].metadata["multiplier"] == "1"
    assert universe.resolve_symbol("SYN-A", active_date="2026-01-02") == "EQ_US_SYNTH_A"


def test_symbol_only_members_require_instrument_master() -> None:
    with pytest.raises(UniverseSpecError, match="instrument master"):
        UniverseSpec.from_mapping(
            {
                "universe_id": "missing_master",
                "name": "Missing Master",
                "data_version": "synthetic:universe:v1",
                "instruments": [{"symbol": "SYN-A"}],
            }
        )


def _universe_payload() -> dict[str, object]:
    return {
        "universe_id": "tiny_multi",
        "name": "Tiny Multi",
        "data_version": "synthetic:universe:v1",
        "inclusion_rules": ["explicit_synthetic_fixture_members"],
        "exclusion_rules": ["no_real_market_data"],
        "future_sector_constraints": [
            {
                "constraint_id": "sector_contract",
                "mode": "contract_only",
                "enabled": False,
                "sector": "synthetic_sector",
                "max_exposure": "0.50",
            }
        ],
        "future_asset_constraints": [
            {
                "constraint_id": "asset_contract",
                "mode": "contract_only",
                "enabled": False,
                "asset_class": "equity",
                "max_exposure": "1.00",
            }
        ],
        "instruments": [
            {
                "instrument_id": "EQ_US_SYNTH_A",
                "symbol": "SYN-A",
                "asset_class": "equity",
                "exchange": "XNYS",
                "currency": "USD",
                "timezone": "America/New_York",
                "start_date": "2026-01-01",
                "end_date": None,
                "data_version": "synthetic:bars:v1",
                "inclusion_rules": ["listed_in_fixture_config"],
                "exclusion_rules": [],
            },
            {
                "instrument_id": "EQ_US_SYNTH_B",
                "symbol": "SYN-B",
                "asset_class": "equity",
                "exchange": "XCME",
                "currency": "USD",
                "timezone": "America/Chicago",
                "start_date": "2026-01-01",
                "end_date": None,
                "data_version": "synthetic:bars:v1",
                "inclusion_rules": ["listed_in_fixture_config"],
                "exclusion_rules": [],
            },
        ],
    }


def _instrument_payload() -> dict[str, object]:
    return {
        "instrument_id": "EQ_US_SYNTH_A",
        "symbol": "SYN-A",
        "asset_class": "equity",
        "exchange": "XNYS",
        "currency": "USD",
        "timezone": "America/New_York",
        "tick_size": "0.01",
        "lot_size": "1",
        "multiplier": "1",
        "start_date": "2026-01-01",
        "end_date": None,
        "corporate_action_policy": "point_in_time",
        "metadata": {"calendar_id": "XNYS_SYNTH"},
    }
