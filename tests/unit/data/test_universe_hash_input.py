from __future__ import annotations

from pathlib import Path

from alpha_system.data.universe import load_universe_config


def test_universe_example_hash_input_is_deterministic() -> None:
    universe = load_universe_config(Path("configs/universes/examples/tiny_multi_symbol.json"))

    assert universe.hash_input()["schema"] == "universe_spec_v1"
    assert universe.config_hash() == load_universe_config(
        Path("configs/universes/examples/tiny_multi_symbol.json")
    ).config_hash()
