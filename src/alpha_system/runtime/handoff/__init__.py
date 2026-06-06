"""Reference candidate handoff runtime public surface."""

from __future__ import annotations

from typing import Any

_EXPORTS = {
    "REFERENCE_CANDIDATE_HANDOFF_SCHEMA": "alpha_system.runtime.handoff.reference",
    "REFERENCE_VALIDATION_REQUIRED": "alpha_system.runtime.handoff.reference",
    "ReferenceCandidateHandoff": "alpha_system.runtime.handoff.reference",
    "ReferenceCandidateHandoffContractError": "alpha_system.runtime.handoff.reference",
    "ReferenceRequirement": "alpha_system.runtime.handoff.reference",
    "RuntimeObjectRef": "alpha_system.runtime.handoff.reference",
    "VersionLineageSnapshot": "alpha_system.runtime.handoff.reference",
    "build_reference_candidate_handoff": "alpha_system.runtime.handoff.reference",
}

__all__: list[str] = []


def __getattr__(name: str) -> Any:
    """Resolve handoff symbols from their defining module."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module = importlib.import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return default attrs plus lazily exposed handoff symbols."""

    return sorted({*globals(), *_EXPORTS})
