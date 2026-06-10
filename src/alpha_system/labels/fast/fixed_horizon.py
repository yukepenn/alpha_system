"""Fixed-horizon label pack declaration for the V1 fast producer path."""

from __future__ import annotations

import re
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

_MINUTE_HORIZON_TOKEN = re.compile(r"^(?:mid_)?fwd_ret_(?P<minutes>[1-9][0-9]*)m$")


def _horizon_minutes_or_none(label_name: FixedHorizonLabelName) -> int | None:
    match = _MINUTE_HORIZON_TOKEN.match(label_name.value)
    if match is None:
        return None
    return int(match.group("minutes"))


_FAST_FIXED_HORIZON_LABELS: tuple[FixedHorizonLabelName, ...] = tuple(
    label_name
    for label_name in supported_fixed_horizon_labels()
    if _horizon_minutes_or_none(label_name) is not None
)
_ROUTED_TO_LCFP_P04_LABELS: tuple[FixedHorizonLabelName, ...] = tuple(
    label_name
    for label_name in supported_fixed_horizon_labels()
    if _horizon_minutes_or_none(label_name) is None
)

FIXED_HORIZON_LABEL_IDS: tuple[str, ...] = tuple(
    label_name.value for label_name in _FAST_FIXED_HORIZON_LABELS
)


@dataclass(frozen=True, slots=True)
class FixedHorizonPackCoverage:
    """Value-free coverage summary for the governed fixed-horizon pack."""

    label_ids: tuple[str, ...]
    close_horizons_minutes: tuple[int, ...]
    mid_horizons_minutes: tuple[int, ...]
    routed_to_lcfp_p04_label_ids: tuple[str, ...]
    governance_gap_note: str

    def to_dict(self) -> dict[str, object]:
        return {
            "label_ids": list(self.label_ids),
            "close_horizons_minutes": list(self.close_horizons_minutes),
            "mid_horizons_minutes": list(self.mid_horizons_minutes),
            "routed_to_lcfp_p04_label_ids": list(self.routed_to_lcfp_p04_label_ids),
            "governance_gap_note": self.governance_gap_note,
        }


def build_fixed_horizon_label_pack(
    definitions: Sequence[FixedHorizonLabelDefinition],
) -> FastLabelPack:
    """Build the governed fixed-horizon label pack.

    The governed reference family is the oracle boundary. This builder accepts
    non-empty subsets of the fixed-minute ``FixedHorizonLabelName`` values and
    derives no new labels or identities.

    The pack uses one shared P02 panel per symbol-year and caches one terminal
    model per distinct horizon minute. The P02 ``TerminalRequest`` is scoped to
    one horizon, so the guard pass cannot be literally single-pass across all
    horizons without widening that contract; panel loading and input adaptation
    stay single-pass, and terminal work is de-duplicated per horizon.
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
            for label_name in _FAST_FIXED_HORIZON_LABELS
            if not label_name.value.startswith("mid_")
        }
    )
    mid_horizons = sorted(
        {
            _horizon_minutes(label_name)
            for label_name in _FAST_FIXED_HORIZON_LABELS
            if label_name.value.startswith("mid_")
        }
    )
    return FixedHorizonPackCoverage(
        label_ids=FIXED_HORIZON_LABEL_IDS,
        close_horizons_minutes=tuple(close_horizons),
        mid_horizons_minutes=tuple(mid_horizons),
        routed_to_lcfp_p04_label_ids=tuple(
            label_name.value for label_name in _ROUTED_TO_LCFP_P04_LABELS
        ),
        governance_gap_note=(
            "LCFP-P03 fast coverage includes governed fixed-minute trade-price "
            "1/3/5/10/15/30/60/120/240m labels and governed fixed-minute "
            "midprice 1/3/5/10/30m labels. Symbolic close-out labels "
            "session_close and maintenance_flat are intentionally routed to "
            "LCFP-P04 and are not computed by this pack."
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
        if _horizon_minutes_or_none(definition.name) is None:
            raise FastLabelPackError(
                "fixed-horizon fast pack supports fixed-minute labels only; "
                f"{definition.name.value} is routed to LCFP-P04"
            )
        if definition.name in by_name:
            raise FastLabelPackError(f"duplicate fixed-horizon label: {definition.name.value}")
        expected = LabelVersion.derive(definition.contract)
        if definition.version != expected:
            raise FastLabelPackError("fixed-horizon LabelVersion does not match contract")
        by_name[definition.name] = definition

    expected_names = _FAST_FIXED_HORIZON_LABELS
    actual_names = frozenset(by_name)
    extra = tuple(name.value for name in actual_names if name not in set(expected_names))
    if extra:
        raise FastLabelPackError(
            "fixed-horizon label pack requires governed labels: "
            + ", ".join(sorted(extra))
        )
    return tuple(by_name[name] for name in expected_names if name in by_name)


def _horizon_minutes(label_name: FixedHorizonLabelName) -> int:
    horizon_minutes = _horizon_minutes_or_none(label_name)
    if horizon_minutes is None:
        raise FastLabelPackError(
            f"{label_name.value} is not a fixed-minute horizon; routed to LCFP-P04"
        )
    return horizon_minutes


__all__ = [
    "FIXED_HORIZON_LABEL_IDS",
    "FixedHorizonPackCoverage",
    "build_fixed_horizon_label_pack",
    "fixed_horizon_pack_coverage",
    "supports_fixed_horizon_label_pack",
]
