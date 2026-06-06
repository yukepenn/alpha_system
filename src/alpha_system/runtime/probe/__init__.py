"""Signal Probe runtime public surface.

The probe package is a Tier 1 descriptive screen. It is not strategy
validation, not a backtest product, and not a candidate-promotion surface.
"""

from __future__ import annotations

from typing import Any

_EXPORTS = {
    "DirectionPolicy": "alpha_system.runtime.probe.spec",
    "FillPolicy": "alpha_system.runtime.probe.spec",
    "FillTiming": "alpha_system.runtime.probe.spec",
    "SignalFeatureRef": "alpha_system.runtime.probe.spec",
    "SignalLabelRef": "alpha_system.runtime.probe.spec",
    "SignalProbeContractError": "alpha_system.runtime.probe.spec",
    "SignalProbeSpec": "alpha_system.runtime.probe.spec",
    "SignalProbeSpecRef": "alpha_system.runtime.probe.spec",
    "SignalProbeObservation": "alpha_system.runtime.probe.fills",
    "SignalProbeFillError": "alpha_system.runtime.probe.fills",
    "SignalProbePositionSeries": "alpha_system.runtime.probe.fills",
    "build_next_bar_position_series": "alpha_system.runtime.probe.fills",
    "PROBE_REPORT_KIND": "alpha_system.runtime.probe.report",
    "SignalProbeReport": "alpha_system.runtime.probe.report",
    "SignalProbeReportContractError": "alpha_system.runtime.probe.report",
    "ThresholdProbeSummary": "alpha_system.runtime.probe.report",
    "SignalProbeRuntimeError": "alpha_system.runtime.probe.runner",
    "run_signal_probe": "alpha_system.runtime.probe.runner",
}

# Runtime subpackages resolve symbols lazily and keep package-level __all__
# empty for the skeleton convention used by the existing runtime packages.
__all__: list[str] = []


def __getattr__(name: str) -> Any:
    """Resolve signal-probe symbols from their defining modules."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module = importlib.import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return default attrs plus lazily exposed probe runtime symbols."""

    return sorted({*globals(), *_EXPORTS})
