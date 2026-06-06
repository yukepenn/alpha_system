"""Cost-stress runtime public surface."""

from __future__ import annotations

from typing import Any

_EXPORTS = {
    "COST_MODEL_VERSION_SCHEMA": "alpha_system.runtime.cost.model_version",
    "COST_SENSITIVITY_REPORT_KIND": "alpha_system.runtime.cost.report",
    "CostModelVersion": "alpha_system.runtime.cost.model_version",
    "CostModelVersionError": "alpha_system.runtime.cost.model_version",
    "CostProfileSummary": "alpha_system.runtime.cost.report",
    "CostSensitivityReport": "alpha_system.runtime.cost.report",
    "CostSessionSummary": "alpha_system.runtime.cost.report",
    "CostStressFill": "alpha_system.runtime.cost.runtime",
    "CostStressProfile": "alpha_system.runtime.cost.spec",
    "CostStressRuntimeError": "alpha_system.runtime.cost.runtime",
    "CostStressSpec": "alpha_system.runtime.cost.spec",
    "CostStressSpecError": "alpha_system.runtime.cost.spec",
    "CostStressThresholds": "alpha_system.runtime.cost.runtime",
    "SessionCostPenalty": "alpha_system.runtime.cost.spec",
    "build_cost_sensitivity_report": "alpha_system.runtime.cost.runtime",
    "load_cost_stress_config": "alpha_system.runtime.cost.spec",
}

# Symbols are resolved lazily from their defining modules via __getattr__ below
# (callers and tests import them from this package path), but package-level
# __all__ is kept empty to match the runtime subpackage convention shared with
# the factor/label/splits/cross_market diagnostics packages and enforced by
# tests/unit/runtime/test_package_skeleton.py.
__all__: list[str] = []


def __getattr__(name: str) -> Any:
    """Resolve cost runtime symbols from their defining module."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module = importlib.import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return default attrs plus lazily exposed cost runtime symbols."""

    return sorted({*globals(), *_EXPORTS})
