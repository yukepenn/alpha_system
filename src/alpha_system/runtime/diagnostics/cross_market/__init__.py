"""Cross-market diagnostics runtime surface."""

from __future__ import annotations

from typing import Any

_RUNTIME_MODULE = "alpha_system.runtime.diagnostics.cross_market.runtime"

_EXPORTS = {
    "CROSS_MARKET_DIAGNOSTICS_REPORT_KIND": _RUNTIME_MODULE,
    "CROSS_MARKET_DIAGNOSTICS_THRESHOLD_PROFILE": _RUNTIME_MODULE,
    "CrossMarketDiagnosticsConfig": _RUNTIME_MODULE,
    "CrossMarketDiagnosticsError": _RUNTIME_MODULE,
    "CrossMarketDiagnosticsReport": _RUNTIME_MODULE,
    "CrossMarketDiagnosticsRunResult": _RUNTIME_MODULE,
    "LeadLagSummary": _RUNTIME_MODULE,
    "PairRelationshipSummary": _RUNTIME_MODULE,
    "RegimeCorrelationSummary": _RUNTIME_MODULE,
    "SymbolAlignmentSummary": _RUNTIME_MODULE,
    "build_cross_market_diagnostics_report": _RUNTIME_MODULE,
    "build_cross_market_diagnostics_run": _RUNTIME_MODULE,
    "resolve_cross_market_dataset_version": _RUNTIME_MODULE,
}

# Preserve the package scaffold expectation while resolving runtime symbols lazily.
__all__: list[str] = []


def __getattr__(name: str) -> Any:
    """Resolve cross-market diagnostics symbols from their defining module."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module = importlib.import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return default attrs plus lazily exposed cross-market diagnostics symbols."""

    return sorted({*globals(), *_EXPORTS})
