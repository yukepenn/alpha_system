"""EvidenceDraft runtime public surface."""

from __future__ import annotations

from typing import Any

_EXPORTS = {
    "EVIDENCE_DRAFT_SCHEMA": "alpha_system.runtime.evidence.draft",
    "EvidenceDraft": "alpha_system.runtime.evidence.draft",
    "EvidenceDraftContractError": "alpha_system.runtime.evidence.draft",
    "EvidenceSectionSummary": "alpha_system.runtime.evidence.draft",
    "build_evidence_draft": "alpha_system.runtime.evidence.draft",
}

__all__: list[str] = []


def __getattr__(name: str) -> Any:
    """Resolve evidence draft symbols from their defining module."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module = importlib.import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return default attrs plus lazily exposed evidence draft symbols."""

    return sorted({*globals(), *_EXPORTS})
