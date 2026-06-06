"""Bounded Grid runtime public surface.

The grid package gates bounded variant spaces before any grid execution. It
orchestrates existing experiments primitives and records descriptive guard
outcomes only.
"""

from __future__ import annotations

from typing import Any

_EXPORTS = {
    "BoundedGridBindingRef": "alpha_system.runtime.grid.contracts",
    "BoundedGridContractError": "alpha_system.runtime.grid.contracts",
    "BoundedGridOutcome": "alpha_system.runtime.grid.contracts",
    "BoundedGridRunRecord": "alpha_system.runtime.grid.contracts",
    "BoundedGridSpec": "alpha_system.runtime.grid.contracts",
    "BoundedGridSpecRef": "alpha_system.runtime.grid.contracts",
    "BoundedGridValidationResult": "alpha_system.runtime.grid.contracts",
    "ParameterAxis": "alpha_system.runtime.grid.contracts",
    "VariantBudget": "alpha_system.runtime.grid.contracts",
    "guard_bounded_grid": "alpha_system.runtime.grid.contracts",
    "validate_bounded_grid_request": "alpha_system.runtime.grid.contracts",
}

__all__: list[str] = []


def __getattr__(name: str) -> Any:
    """Resolve bounded-grid symbols from their defining module."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module = importlib.import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return default attrs plus lazily exposed bounded-grid symbols."""

    return sorted({*globals(), *_EXPORTS})
