from __future__ import annotations

import importlib
from types import ModuleType


SUBPACKAGES = (
    "roles",
    "permissions",
    "tools",
    "queue",
    "separation",
    "records",
    "memory",
    "dry_run",
)


def test_agent_factory_package_and_subpackages_import() -> None:
    assert importlib.import_module("alpha_system.agent_factory") is not None

    for name in SUBPACKAGES:
        module = importlib.import_module(f"alpha_system.agent_factory.{name}")
        assert isinstance(module, ModuleType)


def test_agent_factory_subpackages_are_empty_import_skeletons() -> None:
    for name in SUBPACKAGES:
        module = importlib.import_module(f"alpha_system.agent_factory.{name}")

        assert isinstance(module.__all__, list)
        assert module.__doc__ is not None
        assert module.__doc__.strip()


def test_agent_factory_entry_contract_surface_is_preserved() -> None:
    assert importlib.import_module("alpha_system.agent_factory.entry_contract") is not None
