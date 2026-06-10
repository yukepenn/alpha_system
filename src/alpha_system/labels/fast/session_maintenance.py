"""Session-close and maintenance-flat fast label pack declarations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelDefinition,
    FixedHorizonLabelName,
)
from alpha_system.labels.version import LabelVersion

from alpha_system.labels.fast.materializer import (
    FastLabelDeclaration,
    FastLabelPack,
    FastLabelPackError,
)

_SESSION_MAINTENANCE_LABELS: tuple[FixedHorizonLabelName, ...] = (
    FixedHorizonLabelName.SESSION_CLOSE,
    FixedHorizonLabelName.MAINTENANCE_FLAT,
)

SESSION_MAINTENANCE_LABEL_IDS: tuple[str, ...] = tuple(
    label_name.value for label_name in _SESSION_MAINTENANCE_LABELS
)


@dataclass(frozen=True, slots=True)
class SessionMaintenancePackCoverage:
    """Value-free coverage summary for the P04 close-out fast pack."""

    label_ids: tuple[str, ...]
    terminal_model: str
    oracle: str
    metadata_note: str

    def to_dict(self) -> dict[str, object]:
        return {
            "label_ids": list(self.label_ids),
            "terminal_model": self.terminal_model,
            "oracle": self.oracle,
            "metadata_note": self.metadata_note,
        }


def build_session_maintenance_label_pack(
    definitions: Sequence[FixedHorizonLabelDefinition],
) -> FastLabelPack:
    """Build the governed session-close / maintenance-flat fast pack."""

    ordered = _ordered_session_maintenance_definitions(definitions)
    return FastLabelPack(
        pack_id="session_maintenance",
        definitions=ordered,
        declarations=tuple(FastLabelDeclaration(definition) for definition in ordered),
        metadata=session_maintenance_pack_coverage().to_dict(),
    )


def supports_session_maintenance_label_pack(
    definitions: Sequence[FixedHorizonLabelDefinition],
) -> bool:
    """Return true when definitions are a governed close-out subset."""

    try:
        _ordered_session_maintenance_definitions(definitions)
    except FastLabelPackError:
        return False
    return True


def session_maintenance_pack_coverage() -> SessionMaintenancePackCoverage:
    """Return a value-free summary of the close-out oracle boundary."""

    return SessionMaintenancePackCoverage(
        label_ids=SESSION_MAINTENANCE_LABEL_IDS,
        terminal_model=(
            "LCFP-P02 TerminalKind.SESSION_CLOSE and "
            "TerminalKind.MAINTENANCE_FLAT on one shared panel"
        ),
        oracle=(
            "alpha_system.labels.families.fixed_horizon "
            "SESSION_CLOSE / MAINTENANCE_FLAT"
        ),
        metadata_note=(
            "label_version_id is reference-derived from LabelContractSpec; "
            "the fast pack emits values only"
        ),
    )


def _ordered_session_maintenance_definitions(
    definitions: Sequence[FixedHorizonLabelDefinition],
) -> tuple[FixedHorizonLabelDefinition, ...]:
    if isinstance(definitions, str) or not isinstance(definitions, Sequence):
        raise FastLabelPackError("session/maintenance label pack requires definitions")
    if not definitions:
        raise FastLabelPackError("session/maintenance label pack requires at least one definition")
    by_name: dict[FixedHorizonLabelName, FixedHorizonLabelDefinition] = {}
    for definition in definitions:
        if not isinstance(definition, FixedHorizonLabelDefinition):
            raise FastLabelPackError(
                "session/maintenance pack entries must be FixedHorizonLabelDefinition objects"
            )
        if definition.name not in _SESSION_MAINTENANCE_LABELS:
            raise FastLabelPackError(
                "session/maintenance fast pack supports only "
                "session_close and maintenance_flat"
            )
        if definition.name in by_name:
            raise FastLabelPackError(f"duplicate close-out label: {definition.name.value}")
        expected = LabelVersion.derive(definition.contract)
        if definition.version != expected:
            raise FastLabelPackError("close-out LabelVersion does not match contract")
        by_name[definition.name] = definition
    return tuple(
        by_name[label_name]
        for label_name in _SESSION_MAINTENANCE_LABELS
        if label_name in by_name
    )


__all__ = [
    "SESSION_MAINTENANCE_LABEL_IDS",
    "SessionMaintenancePackCoverage",
    "build_session_maintenance_label_pack",
    "session_maintenance_pack_coverage",
    "supports_session_maintenance_label_pack",
]
