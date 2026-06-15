"""Cross-idea multiplicity canary for the family-FDR correction (Stage A).

Guards ``governance/family_fdr_correction.py`` against silent drift in the
multiplicity math. It asserts three things the independent reviewer rail relies
on:

1. **Textbook BH / Bonferroni.** On the classic Benjamini-Hochberg (1995)
   p-value vector, the step-up BH correction at FDR alpha=0.05 rejects exactly
   the first four nulls, and Bonferroni at FWER alpha=0.05 rejects exactly the
   first three. Hardcoded expected rejection sets.

2. **The historical pa_setup REWORK reproduces deterministically.** The first
   shelved setup signal (``prior_session_high_sweep_and_reclaim``, ES_2020_120m,
   net_excursion) was 1 of a co-mined batch of m=7 sibling pa_setup ideas with a
   per-test surrogate p ``(0+1)/(64+1) = 0.0153846`` at run_count=64. The
   reviewer adjudicated REWORK because 64 surrogates cannot even RESOLVE a passing
   corrected p (finest resolvable p ``1/65`` > Bonferroni ``0.05/7 = 0.0071``).
   This canary asserts the gate now reaches the SAME conclusion without a human:
   ``resolution_adequate == False`` AND ``eligible == False``. It checks both the
   m=7 (all siblings) and m=5 (net_excursion-only) interpretations -- the signal
   is not-eligible under both; m=7 is the reviewer's primary reading.

3. **Non-vacuity.** A clearly-significant, resolution-adequate idea (p=0.0001,
   run_count=10000, m=5) is ``eligible == True`` -- the gate is not a constant
   reject.

This is research-only diagnostic plumbing. A passing canary validates the
correction math only and implies NO alpha, profitability, or tradability claim.
The gate is a deterministic RECORD; the machine never auto-promotes.
"""

from __future__ import annotations

import sys

from alpha_system.governance.family_fdr_correction import (
    FDR_METHOD_BENJAMINI_HOCHBERG,
    FDR_METHOD_BONFERRONI,
    correct_family,
    resolution_adequate,
    surrogate_p_upper_bound,
)

# Classic Benjamini-Hochberg (1995) ordered p-value vector (m = 15).
_BH_1995_P_VALUES: tuple[float, ...] = (
    0.0001,
    0.0004,
    0.0019,
    0.0095,
    0.0201,
    0.0278,
    0.0298,
    0.0344,
    0.0459,
    0.3240,
    0.4262,
    0.5719,
    0.6528,
    0.7590,
    1.0000,
)
# BH step-up at FDR alpha=0.05 rejects the first four (ranks 1..4).
_BH_EXPECTED_REJECTED = frozenset(f"i{index}" for index in range(4))
# Bonferroni at FWER alpha=0.05 (threshold 0.05/15 = 0.003333) rejects the first three.
_BONFERRONI_EXPECTED_REJECTED = frozenset(f"i{index}" for index in range(3))

# Historical pa_setup REWORK numbers (reviewer-confirmed).
_REWORK_SIGNAL_KEY = "prior_session_high_sweep_and_reclaim"
_REWORK_RUN_COUNT = 64
_REWORK_GATE_PASS_COUNT = 0
_REWORK_FAMILY_SIZE_PRIMARY = 7  # all co-mined siblings (reviewer's primary reading)
_REWORK_FAMILY_SIZE_NET_EXCURSION = 5  # the net_excursion-only subset
_REWORK_ALPHA = 0.05
_REWORK_EXPECTED_P = 1.0 / 65.0  # (0 + 1) / (64 + 1) = 0.0153846...


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _check_textbook_corrections() -> None:
    entries = [
        {"idea_key": f"i{index}", "p_value": p_value, "run_count": 1_000_000}
        for index, p_value in enumerate(_BH_1995_P_VALUES)
    ]

    bh_verdicts = correct_family(
        entries, alpha_fw=0.05, method=FDR_METHOD_BENJAMINI_HOCHBERG
    )
    bh_rejected = frozenset(v.idea_key for v in bh_verdicts if v.rejected_null)
    _assert(
        bh_rejected == _BH_EXPECTED_REJECTED,
        f"BH textbook mismatch: rejected {sorted(bh_rejected)} != "
        f"{sorted(_BH_EXPECTED_REJECTED)}",
    )

    bonferroni_verdicts = correct_family(
        entries, alpha_fw=0.05, method=FDR_METHOD_BONFERRONI
    )
    bonferroni_rejected = frozenset(
        v.idea_key for v in bonferroni_verdicts if v.rejected_null
    )
    _assert(
        bonferroni_rejected == _BONFERRONI_EXPECTED_REJECTED,
        f"Bonferroni textbook mismatch: rejected {sorted(bonferroni_rejected)} != "
        f"{sorted(_BONFERRONI_EXPECTED_REJECTED)}",
    )


def _rework_batch(family_size: int) -> list[dict[str, object]]:
    """Build the historical batch: the signal + (family_size - 1) null siblings.

    The siblings are non-significant by construction (gate_pass_count high) so
    the batch shape matches the reviewer's: one candidate signal among siblings.
    """

    entries: list[dict[str, object]] = [
        {
            "idea_key": _REWORK_SIGNAL_KEY,
            "gate_pass_count": _REWORK_GATE_PASS_COUNT,
            "run_count": _REWORK_RUN_COUNT,
        }
    ]
    for sibling in range(family_size - 1):
        entries.append(
            {
                "idea_key": f"sibling_{sibling}",
                "gate_pass_count": 20,
                "run_count": _REWORK_RUN_COUNT,
            }
        )
    return entries


def _check_historical_rework() -> None:
    # The per-test surrogate p is exactly the reviewer's 1/65.
    observed_p = surrogate_p_upper_bound(_REWORK_GATE_PASS_COUNT, _REWORK_RUN_COUNT)
    _assert(
        abs(observed_p - _REWORK_EXPECTED_P) < 1e-12,
        f"REWORK per-test p {observed_p} != expected 1/65 = {_REWORK_EXPECTED_P}",
    )

    for family_size in (_REWORK_FAMILY_SIZE_PRIMARY, _REWORK_FAMILY_SIZE_NET_EXCURSION):
        # 64 surrogates cannot resolve the corrected per-test threshold.
        _assert(
            resolution_adequate(_REWORK_RUN_COUNT, family_size, _REWORK_ALPHA) is False,
            f"REWORK m={family_size}: 64 surrogates should be resolution-inadequate",
        )
        verdicts = correct_family(
            _rework_batch(family_size),
            alpha_fw=_REWORK_ALPHA,
            method=FDR_METHOD_BONFERRONI,
        )
        signal = next(v for v in verdicts if v.idea_key == _REWORK_SIGNAL_KEY)
        _assert(
            signal.family_size == family_size,
            f"REWORK m={family_size}: family_size {signal.family_size} mismatch",
        )
        _assert(
            abs(signal.p_value - _REWORK_EXPECTED_P) < 1e-12,
            f"REWORK m={family_size}: signal p {signal.p_value} != 1/65",
        )
        _assert(
            signal.resolution_adequate is False,
            f"REWORK m={family_size}: signal must be resolution-inadequate",
        )
        _assert(
            signal.eligible is False,
            f"REWORK m={family_size}: signal must be NOT eligible (reviewer REWORK)",
        )
        _assert(
            "resolution_inadequate" in signal.reason,
            f"REWORK m={family_size}: reason must cite resolution inadequacy; "
            f"got {signal.reason!r}",
        )


def _check_non_vacuous_eligible() -> None:
    # A clearly-significant, resolution-adequate idea in a small family is eligible.
    entries = [{"idea_key": "strong", "p_value": 0.0001, "run_count": 10_000}]
    for sibling in range(4):  # m = 5
        entries.append(
            {"idea_key": f"weak_{sibling}", "p_value": 0.9, "run_count": 10_000}
        )
    verdicts = correct_family(entries, alpha_fw=0.05, method=FDR_METHOD_BENJAMINI_HOCHBERG)
    strong = next(v for v in verdicts if v.idea_key == "strong")
    _assert(strong.family_size == 5, f"non-vacuous: family_size {strong.family_size} != 5")
    _assert(
        strong.resolution_adequate is True,
        "non-vacuous: 10000 surrogates must be resolution-adequate for m=5",
    )
    _assert(strong.rejected_null is True, "non-vacuous: p=0.0001 must reject the null")
    _assert(strong.eligible is True, "non-vacuous: strong signal must be eligible")


def run_family_fdr_budget_canary() -> None:
    """Run all multiplicity assertions; raise on the first failure."""

    _check_textbook_corrections()
    _check_historical_rework()
    _check_non_vacuous_eligible()


def main(argv: list[str] | None = None) -> int:
    try:
        run_family_fdr_budget_canary()
    except AssertionError as exc:
        print(f"FAIL family_fdr_budget: {exc}", file=sys.stderr)
        return 1
    print(
        "family_fdr_budget OK: BH/Bonferroni textbook, pa_setup REWORK reproduced "
        "(m=7 & m=5, p=1/65, run_count=64 -> not eligible), non-vacuous eligible"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
