"""Factor diagnostics runtime surface."""

from __future__ import annotations

from typing import Any

_EXPORTS = {
    "FACTOR_DIAGNOSTICS_REPORT_KIND": "alpha_system.runtime.diagnostics.factor.runtime",
    "FACTOR_DIAGNOSTICS_THRESHOLD_PROFILE": "alpha_system.runtime.diagnostics.factor.runtime",
    "FactorDiagnosticsError": "alpha_system.runtime.diagnostics.factor.runtime",
    "FactorDiagnosticsReport": "alpha_system.runtime.diagnostics.factor.runtime",
    "FactorDiagnosticsRunResult": "alpha_system.runtime.diagnostics.factor.runtime",
    "FactorDiagnosticsThresholds": "alpha_system.runtime.diagnostics.factor.runtime",
    "build_factor_diagnostics_report": "alpha_system.runtime.diagnostics.factor.runtime",
    "build_factor_diagnostics_run": "alpha_system.runtime.diagnostics.factor.runtime",
}

# Preserve the RT-P02 scaffold expectation while resolving RT-P07 symbols lazily.
__all__: list[str] = []


def __getattr__(name: str) -> Any:
    """Resolve factor diagnostics symbols from their defining module."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module = importlib.import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return default attrs plus lazily exposed factor diagnostics symbols."""

    return sorted({*globals(), *_EXPORTS})
