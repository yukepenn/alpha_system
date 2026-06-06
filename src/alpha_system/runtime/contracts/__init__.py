"""Runtime contract namespace for pre-execution Research Runtime phases."""

from __future__ import annotations

from typing import Any

_EXPORTS = {
    "CAMPAIGN_PARTITIONS": "alpha_system.runtime.contracts.plan",
    "DOUBLE_COST_PROFILE": "alpha_system.runtime.contracts.plan",
    "RuntimeContractError": "alpha_system.runtime.contracts.run_spec",
    "RuntimeLifecycleState": "alpha_system.runtime.contracts.run_spec",
    "RuntimePlan": "alpha_system.runtime.contracts.plan",
    "RuntimePlanValidationResult": "alpha_system.runtime.contracts.plan",
    "RuntimeRequest": "alpha_system.runtime.contracts.run_spec",
    "StudyRunSpec": "alpha_system.runtime.contracts.run_spec",
    "validate_runtime_plan": "alpha_system.runtime.contracts.plan",
}

# Preserve the RT-P00 scaffold expectation while resolving RT-P04 symbols lazily.
__all__: list[str] = []


def __getattr__(name: str) -> Any:
    """Resolve RT-P04 contract symbols from their defining modules."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module = importlib.import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return the default module attrs plus lazily exposed contract symbols."""

    return sorted({*globals(), *_EXPORTS})
