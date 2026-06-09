"""Fixed-horizon label pack declaration for the V1 fast producer path."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelDefinition,
    FixedHorizonLabelName,
    supported_fixed_horizon_labels,
)
from alpha_system.labels.version import LabelVersion

from alpha_system.labels.fast.materializer import (
    FastLabelDeclaration,
    FastLabelPack,
    FastLabelPackError,
)

FIXED_HORIZON_LABEL_IDS: tuple[str, ...] = tuple(
    label_name.value for label_name in supported_fixed_horizon_labels()
)


@dataclass(frozen=True, slots=True)
class FixedHorizonPackCoverage:
    """Value-free coverage summary for the governed fixed-horizon pack."""

    label_ids: tuple[str, ...]
    close_horizons_minutes: tuple[int, ...]
    mid_horizons_minutes: tuple[int, ...]
    governance_gap_note: str

    def to_dict(self) -> dict[str, object]:
        return {
            "label_ids": list(self.label_ids),
            "close_horizons_minutes": list(self.close_horizons_minutes),
            "mid_horizons_minutes": list(self.mid_horizons_minutes),
            "governance_gap_note": self.governance_gap_note,
        }


def build_fixed_horizon_label_pack(
    definitions: Sequence[FixedHorizonLabelDefinition],
) -> FastLabelPack:
    """Build the governed fixed-horizon label pack.

    The governed reference family is the oracle boundary. This builder accepts
    non-empty subsets of the current ``FixedHorizonLabelName`` set and derives
    no new labels or identities.
    """

    ordered = _ordered_fixed_horizon_definitions(definitions)
    return FastLabelPack(
        pack_id="fixed_horizon",
        definitions=ordered,
        declarations=tuple(FastLabelDeclaration(definition) for definition in ordered),
        metadata=fixed_horizon_pack_coverage().to_dict(),
    )


def supports_fixed_horizon_label_pack(
    definitions: Sequence[FixedHorizonLabelDefinition],
) -> bool:
    """Return true when definitions are a governed fixed-horizon subset."""

    try:
        _ordered_fixed_horizon_definitions(definitions)
    except FastLabelPackError:
        return False
    return True


def fixed_horizon_pack_coverage() -> FixedHorizonPackCoverage:
    """Return a value-free summary of the governed fixed-horizon oracle boundary."""

    close_horizons = sorted(
        {
            _horizon_minutes(label_name)
            for label_name in supported_fixed_horizon_labels()
            if not label_name.value.startswith("mid_")
        }
    )
    mid_horizons = sorted(
        {
            _horizon_minutes(label_name)
            for label_name in supported_fixed_horizon_labels()
            if label_name.value.startswith("mid_")
        }
    )
    return FixedHorizonPackCoverage(
        label_ids=FIXED_HORIZON_LABEL_IDS,
        close_horizons_minutes=tuple(close_horizons),
        mid_horizons_minutes=tuple(mid_horizons),
        governance_gap_note=(
            "Governed FixedHorizonLabelName currently covers trade-price "
            "1/3/5/10/15/30m and midprice 1/3/5/10/30m labels only; longer "
            "FUTSUB narrative horizons require governance before V1 may "
            "materialize them."
        ),
    )


def _ordered_fixed_horizon_definitions(
    definitions: Sequence[FixedHorizonLabelDefinition],
) -> tuple[FixedHorizonLabelDefinition, ...]:
    if isinstance(definitions, str) or not isinstance(definitions, Sequence):
        raise FastLabelPackError("fixed-horizon label pack requires a sequence of definitions")
    if not definitions:
        raise FastLabelPackError("fixed-horizon label pack requires at least one definition")
    by_name: dict[FixedHorizonLabelName, FixedHorizonLabelDefinition] = {}
    for definition in definitions:
        if not isinstance(definition, FixedHorizonLabelDefinition):
            raise FastLabelPackError(
                "fixed-horizon label pack entries must be FixedHorizonLabelDefinition objects"
            )
        if definition.name in by_name:
            raise FastLabelPackError(f"duplicate fixed-horizon label: {definition.name.value}")
        expected = LabelVersion.derive(definition.contract)
        if definition.version != expected:
            raise FastLabelPackError("fixed-horizon LabelVersion does not match contract")
        by_name[definition.name] = definition

    expected_names = tuple(supported_fixed_horizon_labels())
    actual_names = frozenset(by_name)
    extra = tuple(name.value for name in actual_names if name not in set(expected_names))
    if extra:
        raise FastLabelPackError(
            "fixed-horizon label pack requires governed labels: "
            + ", ".join(sorted(extra))
        )
    return tuple(by_name[name] for name in expected_names if name in by_name)


def _horizon_minutes(label_name: FixedHorizonLabelName) -> int:
    token = label_name.value.removeprefix("mid_fwd_ret_").removeprefix("fwd_ret_")
    return int(token.removesuffix("m"))


__all__ = [
    "FIXED_HORIZON_LABEL_IDS",
    "FixedHorizonPackCoverage",
    "build_fixed_horizon_label_pack",
    "fixed_horizon_pack_coverage",
    "supports_fixed_horizon_label_pack",
]
