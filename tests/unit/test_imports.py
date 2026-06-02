from __future__ import annotations

import importlib


SUBPACKAGES = (
    "backtest",
    "cli",
    "core",
    "data",
    "execution",
    "experiments",
    "factors",
    "l2",
    "labels",
    "management",
    "portfolio",
    "reports",
    "research",
    "signals",
    "strategies",
)


def test_top_level_package_imports() -> None:
    module = importlib.import_module("alpha_system")

    assert module.__name__ == "alpha_system"


def test_subpackages_import() -> None:
    for subpackage in SUBPACKAGES:
        module_name = f"alpha_system.{subpackage}"
        module = importlib.import_module(module_name)

        assert module.__name__ == module_name
