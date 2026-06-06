from __future__ import annotations

from importlib import import_module

import alpha_system.runtime as runtime


def test_runtime_package_skeleton_imports_cleanly() -> None:
    for module_name in (
        "alpha_system.runtime",
        "alpha_system.runtime.contracts",
        "alpha_system.runtime.diagnostics",
        "alpha_system.runtime.diagnostics.factor",
        "alpha_system.runtime.diagnostics.label",
        "alpha_system.runtime.diagnostics.splits",
        "alpha_system.runtime.diagnostics.cross_market",
        "alpha_system.runtime.cost",
    ):
        module = import_module(module_name)
        assert module.__name__ == module_name


def test_rt_p01_entry_contract_surface_remains_reexported() -> None:
    for public_name in (
        "ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES",
        "RuntimeEntryOutcome",
        "RuntimeEntryReason",
        "RuntimeEntryRequest",
        "RuntimeEntryResult",
        "RuntimeEntryStatus",
        "evaluate_runtime_entry_request",
    ):
        assert public_name in runtime.__all__
        assert getattr(runtime, public_name) is not None


def test_created_subpackage_surfaces_are_empty_until_later_phases() -> None:
    for module_name in (
        "alpha_system.runtime.contracts",
        "alpha_system.runtime.diagnostics",
        "alpha_system.runtime.diagnostics.factor",
        "alpha_system.runtime.diagnostics.label",
        "alpha_system.runtime.diagnostics.splits",
        "alpha_system.runtime.diagnostics.cross_market",
        "alpha_system.runtime.cost",
    ):
        module = import_module(module_name)
        assert module.__all__ == []
