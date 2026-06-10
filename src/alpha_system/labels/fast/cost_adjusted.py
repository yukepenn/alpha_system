"""Cost-adjusted fast label pack declarations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from alpha_system.labels.families.cost_adjusted import (
    CostAdjustedLabelDefinition,
    CostAdjustedLabelName,
    supported_cost_adjusted_labels,
)
from alpha_system.labels.version import LabelVersion

from alpha_system.labels.fast.materializer import (
    FastLabelDeclaration,
    FastLabelPack,
    FastLabelPackError,
)

_COST_ADJUSTED_LABELS: tuple[CostAdjustedLabelName, ...] = supported_cost_adjusted_labels()

COST_ADJUSTED_LABEL_IDS: tuple[str, ...] = tuple(
    label_name.value for label_name in _COST_ADJUSTED_LABELS
)


@dataclass(frozen=True, slots=True)
class CostAdjustedPackCoverage:
    """Value-free coverage summary for the P04 cost-adjusted fast pack."""

    label_ids: tuple[str, ...]
    cost_profile_source: str
    bbo_proxy_note: str
    metadata_note: str

    def to_dict(self) -> dict[str, object]:
        return {
            "label_ids": list(self.label_ids),
            "cost_profile_source": self.cost_profile_source,
            "bbo_proxy_note": self.bbo_proxy_note,
            "metadata_note": self.metadata_note,
        }


def build_cost_adjusted_label_pack(
    definitions: Sequence[CostAdjustedLabelDefinition],
) -> FastLabelPack:
    """Build the governed cost/spread-adjusted fast pack."""

    ordered = _ordered_cost_adjusted_definitions(definitions)
    return FastLabelPack(
        pack_id="cost_adjusted",
        definitions=ordered,
        declarations=tuple(FastLabelDeclaration(definition) for definition in ordered),
        metadata=cost_adjusted_pack_coverage().to_dict(),
    )


def supports_cost_adjusted_label_pack(
    definitions: Sequence[CostAdjustedLabelDefinition],
) -> bool:
    """Return true when definitions are a governed cost-adjusted subset."""

    try:
        _ordered_cost_adjusted_definitions(definitions)
    except FastLabelPackError:
        return False
    return True


def cost_adjusted_pack_coverage() -> CostAdjustedPackCoverage:
    """Return a value-free summary of the cost-adjusted oracle boundary."""

    return CostAdjustedPackCoverage(
        label_ids=COST_ADJUSTED_LABEL_IDS,
        cost_profile_source="alpha_system.backtest.costs",
        bbo_proxy_note=(
            "BBO spread is a proxy input only; the pack makes no "
            "execution-quality claim"
        ),
        metadata_note=(
            "label_version_id is reference-derived from LabelContractSpec; "
            "the fast pack emits values only"
        ),
    )


def _ordered_cost_adjusted_definitions(
    definitions: Sequence[CostAdjustedLabelDefinition],
) -> tuple[CostAdjustedLabelDefinition, ...]:
    if isinstance(definitions, str) or not isinstance(definitions, Sequence):
        raise FastLabelPackError("cost-adjusted label pack requires definitions")
    if not definitions:
        raise FastLabelPackError("cost-adjusted label pack requires at least one definition")
    by_name: dict[CostAdjustedLabelName, CostAdjustedLabelDefinition] = {}
    for definition in definitions:
        if not isinstance(definition, CostAdjustedLabelDefinition):
            raise FastLabelPackError(
                "cost-adjusted pack entries must be CostAdjustedLabelDefinition objects"
            )
        if definition.name not in _COST_ADJUSTED_LABELS:
            raise FastLabelPackError(f"unsupported cost-adjusted label: {definition.name.value}")
        if definition.name in by_name:
            raise FastLabelPackError(f"duplicate cost-adjusted label: {definition.name.value}")
        expected = LabelVersion.derive(definition.spec.label_contract)
        if definition.version != expected:
            raise FastLabelPackError("cost-adjusted LabelVersion does not match contract")
        by_name[definition.name] = definition
    return tuple(
        by_name[label_name]
        for label_name in _COST_ADJUSTED_LABELS
        if label_name in by_name
    )


__all__ = [
    "COST_ADJUSTED_LABEL_IDS",
    "CostAdjustedPackCoverage",
    "build_cost_adjusted_label_pack",
    "cost_adjusted_pack_coverage",
    "supports_cost_adjusted_label_pack",
]
