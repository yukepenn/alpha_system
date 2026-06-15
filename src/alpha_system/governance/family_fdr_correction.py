"""Pure cross-idea family-wise multiplicity correction (Stage A, additive).

A co-mined *batch* of sibling ideas tested against the same slice shares a
family-wise error surface: testing many ideas at once manufactures false
positives at the batch level exactly as a single test does at the row level
(cf. ``law-overlap-aware-ic-power-n-eff`` one layer up). The per-idea
``surrogate_fdr_gate`` is a single-test block-shuffle zero-pass gate and the
``family_budget`` de-dups *variants within one family*; neither controls
cross-idea multiplicity. This module supplies the missing correction math.

It is PURE: deterministic functions over per-idea ``(idea_key, p_value,
run_count)`` (or ``(idea_key, gate_pass_count, run_count)``) tuples plus a
family-wise ``alpha`` and a ``method`` (Benjamini-Hochberg or Bonferroni). It
performs NO I/O and is NOT wired into any live verdict path -- ``testability_gate``
/ ``memory_router`` / ``verdict_report`` / ``fast_probe`` are untouched in
Stage A.

A signal is *eligible* (may reach the independent reviewer shelf as a corrected
candidate) ONLY when BOTH hold:

1. **Resolution adequacy:** its surrogate ``run_count`` is large enough that the
   finest resolvable per-test p ``1/(run_count+1)`` can clear the family-wise
   corrected per-test threshold ``alpha_fw / m`` -- i.e.
   ``run_count >= ceil(m / alpha_fw) - 1``.
2. **Corrected significance:** its per-test surrogate p ``(pass+1)/(run+1)``
   clears the family-wise / FDR-corrected threshold across its co-mined batch.

This is research-only diagnostic plumbing. It defines no PnL/value truth and
makes NO profitability, tradability, or alpha claim. The result of this gate is
a deterministic RECORD of multiplicity-eligibility; the machine NEVER
auto-promotes -- promotion still requires the independent reviewer rail.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.validation import (
    GovernanceValidationError,
    ValidationIssue,
)

# Correction methods.
FDR_METHOD_BENJAMINI_HOCHBERG = "benjamini_hochberg"
FDR_METHOD_BONFERRONI = "bonferroni"
FDR_METHODS = (FDR_METHOD_BENJAMINI_HOCHBERG, FDR_METHOD_BONFERRONI)

# Default policy constants (per DESIGN section 5). These are DEFAULTS ONLY --
# ``alpha_fw`` and ``method`` are parameters on every public entry point. The
# Benjamini-Hochberg FDR alpha=0.10 substrate default controls the expected
# false-discovery proportion for a wide exploratory setup sweep feeding a
# downstream independent rail; Bonferroni FWER 0.05 is the conservative mode.
DEFAULT_FDR_METHOD = FDR_METHOD_BENJAMINI_HOCHBERG
DEFAULT_FDR_ALPHA = 0.10
DEFAULT_BONFERRONI_ALPHA = 0.05

# Reason codes (value-free; mirror the reviewer's REWORK vocabulary).
REASON_ELIGIBLE = "eligible"
REASON_RESOLUTION_INADEQUATE = "resolution_inadequate"
REASON_FAMILY_FDR_NOT_CLEARED = "family_fdr_not_cleared"
REASON_NOT_CLEARED_AND_UNRESOLVED = "resolution_inadequate;family_fdr_not_cleared"


@dataclass(frozen=True, slots=True)
class FamilyFdrVerdict:
    """Per-idea deterministic multiplicity verdict for one co-mined batch.

    ``eligible`` is ``rejected_null AND resolution_adequate``; it is NOT a
    promotion -- only a record that the idea cleared the family-wise correction
    at adequate surrogate resolution and may therefore reach the independent
    reviewer shelf as a corrected candidate.
    """

    idea_key: str
    p_value: float
    corrected_threshold: float
    rejected_null: bool
    resolution_adequate: bool
    eligible: bool
    reason: str
    method: str
    alpha_fw: float
    family_size: int

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a strict JSON-compatible representation."""

        return {
            "idea_key": self.idea_key,
            "p_value": self.p_value,
            "corrected_threshold": self.corrected_threshold,
            "rejected_null": self.rejected_null,
            "resolution_adequate": self.resolution_adequate,
            "eligible": self.eligible,
            "reason": self.reason,
            "method": self.method,
            "alpha_fw": self.alpha_fw,
            "family_size": self.family_size,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> FamilyFdrVerdict:
        """Build a ``FamilyFdrVerdict`` from a mapping (round-trip helper)."""

        return cls(
            idea_key=str(payload["idea_key"]),
            p_value=float(payload["p_value"]),
            corrected_threshold=float(payload["corrected_threshold"]),
            rejected_null=bool(payload["rejected_null"]),
            resolution_adequate=bool(payload["resolution_adequate"]),
            eligible=bool(payload["eligible"]),
            reason=str(payload["reason"]),
            method=str(payload["method"]),
            alpha_fw=float(payload["alpha_fw"]),
            family_size=int(payload["family_size"]),
        )


def surrogate_p_upper_bound(gate_pass_count: int, run_count: int) -> float:
    """Per-test surrogate p upper bound ``(gate_pass_count + 1)/(run_count + 1)``.

    This is the conservative (add-one) upper bound on the block-shuffle
    zero-pass p: a signal that passed the per-idea gate has 0 surrogate passes,
    giving ``1/(run_count + 1)`` -- the finest p the surrogate count can resolve.
    """

    if type(gate_pass_count) is not int or gate_pass_count < 0:
        raise GovernanceValidationError(
            ValidationIssue(
                field="gate_pass_count",
                code="invalid_gate_pass_count",
                message="gate_pass_count must be a non-negative integer",
                expected="int >= 0",
                actual=str(gate_pass_count),
            )
        )
    if type(run_count) is not int or run_count < 0:
        raise GovernanceValidationError(
            ValidationIssue(
                field="run_count",
                code="invalid_run_count",
                message="run_count must be a non-negative integer",
                expected="int >= 0",
                actual=str(run_count),
            )
        )
    if gate_pass_count > run_count:
        raise GovernanceValidationError(
            ValidationIssue(
                field="gate_pass_count",
                code="gate_pass_count_exceeds_run_count",
                message="gate_pass_count must not exceed run_count",
                expected=f"<= {run_count}",
                actual=str(gate_pass_count),
            )
        )
    return (gate_pass_count + 1) / (run_count + 1)


def resolution_adequate(run_count: int, m: int, alpha_fw: float) -> bool:
    """Return True iff ``run_count`` can resolve the corrected per-test threshold.

    The finest resolvable per-test surrogate p is ``1/(run_count + 1)``. It must
    be ``<= alpha_fw / m`` for the corrected threshold to be even resolvable,
    which is equivalent to ``run_count >= ceil(m / alpha_fw) - 1``.
    """

    _require_positive_int(run_count, field="run_count", allow_zero=True)
    _require_positive_int(m, field="m")
    _require_alpha(alpha_fw)
    required_run_count = math.ceil(m / alpha_fw) - 1
    return run_count >= required_run_count


def correct_family(
    entries: Iterable[Mapping[str, Any] | Any],
    alpha_fw: float = DEFAULT_FDR_ALPHA,
    method: str = DEFAULT_FDR_METHOD,
) -> tuple[FamilyFdrVerdict, ...]:
    """Correct a co-mined batch of per-idea p-values for family-wise multiplicity.

    ``entries`` is an iterable of ``{idea_key, p_value, run_count}`` or
    ``{idea_key, gate_pass_count, run_count}`` mappings (or any object exposing
    those attributes). ``method`` is Benjamini-Hochberg (step-up, controls the
    expected false-discovery proportion at ``alpha_fw``) or Bonferroni (controls
    the family-wise error rate at ``alpha_fw``).

    Returns one ``FamilyFdrVerdict`` per idea, in the input order. The family
    size ``m`` is the number of entries. Each verdict is eligible iff it both
    rejects the null under the correction AND its surrogate ``run_count``
    resolves the corrected per-test threshold.
    """

    resolved_method = _require_method(method)
    _require_alpha(alpha_fw)
    parsed = _parse_entries(entries)
    family_size = len(parsed)
    if family_size == 0:
        return ()

    rejected_flags, thresholds = _apply_method(parsed, alpha_fw, resolved_method)

    verdicts: list[FamilyFdrVerdict] = []
    for index, (idea_key, p_value, run_count) in enumerate(parsed):
        rejected = rejected_flags[index]
        resolvable = resolution_adequate(run_count, family_size, alpha_fw)
        eligible = rejected and resolvable
        verdicts.append(
            FamilyFdrVerdict(
                idea_key=idea_key,
                p_value=p_value,
                corrected_threshold=thresholds[index],
                rejected_null=rejected,
                resolution_adequate=resolvable,
                eligible=eligible,
                reason=_reason_for(rejected, resolvable),
                method=resolved_method,
                alpha_fw=alpha_fw,
                family_size=family_size,
            )
        )
    return tuple(verdicts)


def _apply_method(
    parsed: list[tuple[str, float, int]],
    alpha_fw: float,
    method: str,
) -> tuple[list[bool], list[float]]:
    """Return per-entry (rejected, corrected_threshold) lists in input order."""

    family_size = len(parsed)
    if method == FDR_METHOD_BONFERRONI:
        threshold = alpha_fw / family_size
        rejected = [p_value <= threshold for _key, p_value, _run in parsed]
        thresholds = [threshold for _ in parsed]
        return rejected, thresholds

    # Benjamini-Hochberg step-up. Sort p ascending; the largest rank k with
    # p_(k) <= (k/m) * alpha_fw rejects nulls for all ranks <= k. The per-entry
    # "corrected_threshold" reported is that entry's own BH line (rank/m)*alpha
    # so each verdict carries the line it was compared against.
    order = sorted(range(family_size), key=lambda i: parsed[i][1])
    largest_rank = 0
    for position, original_index in enumerate(order, start=1):
        p_value = parsed[original_index][1]
        bh_line = (position / family_size) * alpha_fw
        if p_value <= bh_line:
            largest_rank = position
    rejected = [False] * family_size
    thresholds = [0.0] * family_size
    for position, original_index in enumerate(order, start=1):
        thresholds[original_index] = (position / family_size) * alpha_fw
        if position <= largest_rank:
            rejected[original_index] = True
    return rejected, thresholds


def _reason_for(rejected: bool, resolvable: bool) -> str:
    if rejected and resolvable:
        return REASON_ELIGIBLE
    if not rejected and not resolvable:
        return REASON_NOT_CLEARED_AND_UNRESOLVED
    if not resolvable:
        return REASON_RESOLUTION_INADEQUATE
    return REASON_FAMILY_FDR_NOT_CLEARED


def _parse_entries(
    entries: Iterable[Mapping[str, Any] | Any],
) -> list[tuple[str, float, int]]:
    if isinstance(entries, Mapping) or isinstance(entries, str) or entries is None:
        raise GovernanceValidationError(
            ValidationIssue(
                field="entries",
                code="invalid_entries_type",
                message="entries must be an iterable of per-idea mappings",
                expected="iterable of {idea_key, p_value|gate_pass_count, run_count}",
                actual=type(entries).__name__,
            )
        )
    parsed: list[tuple[str, float, int]] = []
    seen_keys: set[str] = set()
    issues: list[ValidationIssue] = []
    for index, entry in enumerate(entries):
        idea_key, p_value, run_count = _parse_entry(entry, index, issues)
        if idea_key is None:
            continue
        if idea_key in seen_keys:
            issues.append(
                ValidationIssue(
                    field=f"entries[{index}].idea_key",
                    code="duplicate_idea_key",
                    message="family entries must have unique idea_key values",
                    expected="unique idea_key",
                    actual=idea_key,
                )
            )
            continue
        seen_keys.add(idea_key)
        assert p_value is not None
        assert run_count is not None
        parsed.append((idea_key, p_value, run_count))
    if issues:
        raise GovernanceValidationError(issues)
    return parsed


def _parse_entry(
    entry: Mapping[str, Any] | Any,
    index: int,
    issues: list[ValidationIssue],
) -> tuple[str | None, float | None, int | None]:
    get = _entry_getter(entry)
    idea_key_raw = get("idea_key")
    if not isinstance(idea_key_raw, str) or not idea_key_raw.strip():
        issues.append(
            ValidationIssue(
                field=f"entries[{index}].idea_key",
                code="empty_required_field",
                message="entry idea_key must be a non-empty string",
                expected="non-empty string",
                actual=str(idea_key_raw),
            )
        )
        return None, None, None
    idea_key = idea_key_raw

    run_count_raw = get("run_count")
    if type(run_count_raw) is not int or run_count_raw < 0:
        issues.append(
            ValidationIssue(
                field=f"entries[{index}].run_count",
                code="invalid_run_count",
                message="entry run_count must be a non-negative integer",
                expected="int >= 0",
                actual=str(run_count_raw),
            )
        )
        return None, None, None
    run_count = run_count_raw

    p_value_raw = get("p_value")
    if p_value_raw is None:
        gate_pass_raw = get("gate_pass_count")
        if gate_pass_raw is None:
            issues.append(
                ValidationIssue(
                    field=f"entries[{index}]",
                    code="missing_p_value_or_gate_pass_count",
                    message="entry must carry either p_value or gate_pass_count",
                    expected="p_value or gate_pass_count",
                    actual="neither",
                )
            )
            return None, None, None
        try:
            p_value = surrogate_p_upper_bound(gate_pass_raw, run_count)
        except GovernanceValidationError as exc:
            issues.extend(exc.issues)
            return None, None, None
        return idea_key, p_value, run_count

    if isinstance(p_value_raw, bool) or not isinstance(p_value_raw, int | float):
        issues.append(
            ValidationIssue(
                field=f"entries[{index}].p_value",
                code="invalid_p_value",
                message="entry p_value must be a number in [0, 1]",
                expected="float in [0, 1]",
                actual=str(p_value_raw),
            )
        )
        return None, None, None
    p_value = float(p_value_raw)
    if not math.isfinite(p_value) or p_value < 0.0 or p_value > 1.0:
        issues.append(
            ValidationIssue(
                field=f"entries[{index}].p_value",
                code="invalid_p_value",
                message="entry p_value must be a finite number in [0, 1]",
                expected="float in [0, 1]",
                actual=str(p_value_raw),
            )
        )
        return None, None, None
    return idea_key, p_value, run_count


def _entry_getter(entry: Mapping[str, Any] | Any):
    if isinstance(entry, Mapping):
        return lambda key: entry.get(key)
    return lambda key: getattr(entry, key, None)


def _require_method(method: str) -> str:
    if method not in FDR_METHODS:
        raise GovernanceValidationError(
            ValidationIssue(
                field="method",
                code="invalid_fdr_method",
                message="method must be a supported FDR correction method",
                expected=" | ".join(FDR_METHODS),
                actual=str(method),
            )
        )
    return method


def _require_alpha(alpha_fw: float) -> None:
    if isinstance(alpha_fw, bool) or not isinstance(alpha_fw, int | float):
        raise GovernanceValidationError(
            ValidationIssue(
                field="alpha_fw",
                code="invalid_alpha_fw",
                message="alpha_fw must be a number in (0, 1)",
                expected="float in (0, 1)",
                actual=str(alpha_fw),
            )
        )
    value = float(alpha_fw)
    if not math.isfinite(value) or value <= 0.0 or value >= 1.0:
        raise GovernanceValidationError(
            ValidationIssue(
                field="alpha_fw",
                code="invalid_alpha_fw",
                message="alpha_fw must be a finite number strictly in (0, 1)",
                expected="float in (0, 1)",
                actual=str(alpha_fw),
            )
        )


def _require_positive_int(value: int, *, field: str, allow_zero: bool = False) -> None:
    floor = 0 if allow_zero else 1
    if type(value) is not int or value < floor:
        raise GovernanceValidationError(
            ValidationIssue(
                field=field,
                code=f"invalid_{field}",
                message=f"{field} must be an integer >= {floor}",
                expected=f"int >= {floor}",
                actual=str(value),
            )
        )


__all__ = [
    "DEFAULT_BONFERRONI_ALPHA",
    "DEFAULT_FDR_ALPHA",
    "DEFAULT_FDR_METHOD",
    "FDR_METHODS",
    "FDR_METHOD_BENJAMINI_HOCHBERG",
    "FDR_METHOD_BONFERRONI",
    "REASON_ELIGIBLE",
    "REASON_FAMILY_FDR_NOT_CLEARED",
    "REASON_NOT_CLEARED_AND_UNRESOLVED",
    "REASON_RESOLUTION_INADEQUATE",
    "FamilyFdrVerdict",
    "correct_family",
    "resolution_adequate",
    "surrogate_p_upper_bound",
]
