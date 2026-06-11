"""Shared runtime diagnostics contracts and descriptive report surface."""

from __future__ import annotations

from typing import Any

_EXPORTS = {
    "DIAGNOSTICS_FAILURE_STATES": "alpha_system.runtime.diagnostics.contracts",
    "DIAGNOSTICS_LIFECYCLE_STATES": "alpha_system.runtime.diagnostics.contracts",
    "DiagnosticsContractError": "alpha_system.runtime.diagnostics.contracts",
    "DiagnosticsFamily": "alpha_system.runtime.diagnostics.contracts",
    "DiagnosticsHalfLifeProtocol": "alpha_system.runtime.diagnostics.contracts",
    "DiagnosticsQualityGate": "alpha_system.runtime.diagnostics.report",
    "DiagnosticsQualityGateStatus": "alpha_system.runtime.diagnostics.report",
    "DiagnosticsReport": "alpha_system.runtime.diagnostics.report",
    "DiagnosticsReportContractError": "alpha_system.runtime.diagnostics.report",
    "DiagnosticsReportRef": "alpha_system.runtime.diagnostics.contracts",
    "DiagnosticsRunRecord": "alpha_system.runtime.diagnostics.contracts",
    "DiagnosticsRunSpec": "alpha_system.runtime.diagnostics.contracts",
    "DiagnosticsRunSpecRef": "alpha_system.runtime.diagnostics.contracts",
    "RuntimePlanRef": "alpha_system.runtime.diagnostics.contracts",
    "StudyRunRecordRef": "alpha_system.runtime.diagnostics.contracts",
}

# Preserve the RT-P02 scaffold expectation while resolving RT-P06 symbols lazily.
__all__: list[str] = []


def __getattr__(name: str) -> Any:
    """Resolve shared diagnostics symbols from their defining modules."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module = importlib.import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return the default module attrs plus lazily exposed diagnostics symbols."""

    return sorted({*globals(), *_EXPORTS})
