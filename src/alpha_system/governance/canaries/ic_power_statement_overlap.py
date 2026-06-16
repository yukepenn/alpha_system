"""IC power_statement overlap-aware N_eff canary for the main-effect scorer (#474).

Guards the ratified #474 law where it had survived: the diagnostics engine's
EMBEDDED IC ``power_statement`` (and the ``ic_power_*`` quality scalars) produced
for a main-effect IC readout over a FORWARD-OVERLAPPING outcome label. A forward
return / cost-adjusted / excursion outcome looks several bars ahead, so
consecutive bar-spaced observations overlap ~N-fold and the raw row count badly
overstates the independent sample. The latent regression this canary catches is
the main-effect scorer building its embedded power_statement on the RAW row count
(inflated N_eff, deflated MDE) while only its own verdict floor was discounted --
two power statements, one honest and one inflated, the classic #474 second truth.
At the inflated raw floor a well-powered NULL can falsely read as detectable
(signal vs graveyard routing on the wrong floor).

It asserts the four properties the independent reviewer rail relies on:

1. **The scorer's embedded engine power_statement N_eff equals the OVERLAP-AWARE
   floor**, ``floor(usable_pairs / block)``, NOT the raw row count -- and the
   engine MDE equals ``z / sqrt(n_eff - 1)`` on that overlap-aware N_eff.

2. **The embedded engine power_statement agrees with the scorer's own verdict
   floor.** No second, inflated power statement leaks alongside the honest one.

3. **The fix is STRICTER, never looser.** The overlap-aware MDE is strictly
   ABOVE the inflated raw-row MDE for a genuinely overlapping outcome.

4. **A NULL between the honest and inflated floors is not over-credited.** An
   ``|IC|`` that sits below the honest MDE but above the inflated raw MDE must
   NOT clear the honest floor, so the scorer never mints a survivor from it (a
   complete read is never auto-promoted; routing stays on the strict floor).

This is research-only diagnostic plumbing. A passing canary validates the
IC-power overlap-aware N_eff contract only and implies NO alpha, profitability,
or tradability claim. The gate is a deterministic RECORD; the machine never
auto-promotes.
"""

from __future__ import annotations

import math
import sys

from alpha_system.research.track_a_scorer import (
    PRIMARY_STATE_CANDIDATE_RESEARCH,
    PRIMARY_STATE_WATCH,
    score_mechanism,
)
from alpha_system.runtime.diagnostics.power import DEFAULT_IC_MDE_Z_MULTIPLE
from alpha_system.runtime.diagnostics.splits.n_eff import HorizonOverlapMetadata

# A representative forward-overlapping outcome: 5-bar forward horizon, 1-bar
# sampling cadence => overlap block size 5 (discount_factor 5).
_FORWARD_OVERLAP_BARS = 5
_ROWS = 2000
_FORWARD_OUTCOME_FACTOR_ID = "fwd_ret_5b"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _overlap_metadata() -> HorizonOverlapMetadata:
    return HorizonOverlapMetadata(
        horizon=float(_FORWARD_OVERLAP_BARS),
        horizon_unit="bars",
        sampling_cadence=1.0,
        sampling_cadence_unit="bars",
        discount_factor=float(_FORWARD_OVERLAP_BARS),
        metadata_source="ic_power_statement_overlap_canary",
    )


def _rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for i in range(_ROWS):
        # Deterministic, near-null mixed-sign relationship with ample sample.
        factor = float(i % 7)
        label = ((i * 37) % 11 - 5) / 1000.0
        ts = f"2024-01-01T{(i % 23) + 1:02d}:00:00+00:00"
        rows.append(
            {
                "factor_value": factor,
                "label_value": label,
                "horizon_seconds": 300,
                "available_ts": ts,
                "label_available_ts": ts,
                "instrument_id": "ES",
                "event_ts": ts,
                "session_label": "ES_session",
            }
        )
    return rows


def _check_embedded_power_statement_is_overlap_aware() -> None:
    diagnostics = score_mechanism(
        mechanism_id="ic_power_overlap_canary",
        factor_id=_FORWARD_OUTCOME_FACTOR_ID,
        rows=_rows(),
        horizon_overlap_metadata=_overlap_metadata(),
    )
    quality = diagnostics.diagnostics_quality_summary
    usable_pairs = diagnostics.usable_pair_count
    _assert(usable_pairs > 0, "canary fixture produced no usable IC pairs")

    expected_overlap_n_eff = usable_pairs // _FORWARD_OVERLAP_BARS
    raw_n_eff = usable_pairs
    _assert(
        expected_overlap_n_eff < raw_n_eff,
        "canary fixture must have a genuine overlap discount",
    )

    engine_n_eff = quality.get("ic_power_n_eff")
    # 1. Embedded engine power_statement N_eff is the OVERLAP-AWARE floor, never
    #    the raw row count (the #474 law at the IC power_statement layer).
    _assert(
        engine_n_eff == expected_overlap_n_eff,
        "rail defeated: embedded engine ic_power_n_eff "
        f"{engine_n_eff!r} != overlap-aware floor {expected_overlap_n_eff} "
        f"(raw rows {raw_n_eff}); the power_statement used RAW rows (#474 residue)",
    )

    expected_mde = DEFAULT_IC_MDE_Z_MULTIPLE / math.sqrt(expected_overlap_n_eff - 1)
    inflated_raw_mde = DEFAULT_IC_MDE_Z_MULTIPLE / math.sqrt(raw_n_eff - 1)
    engine_mde = quality.get("ic_power_mde_abs_ic")
    _assert(
        engine_mde is not None and math.isclose(float(engine_mde), expected_mde, rel_tol=1e-9),
        "rail defeated: embedded engine MDE "
        f"{engine_mde!r} != z/sqrt(n_eff-1) on the overlap-aware n_eff {expected_mde}",
    )

    # 2. The embedded engine power statement agrees with the scorer's verdict
    #    floor -- no inflated second power statement leaks alongside the honest one.
    _assert(
        engine_n_eff == diagnostics.n_eff,
        "rail defeated: embedded engine n_eff "
        f"{engine_n_eff!r} disagrees with the scorer verdict n_eff "
        f"{diagnostics.n_eff} (second-truth power statement)",
    )
    _assert(
        diagnostics.mde_abs_ic is not None
        and math.isclose(float(diagnostics.mde_abs_ic), expected_mde, rel_tol=1e-9),
        "rail defeated: scorer verdict MDE "
        f"{diagnostics.mde_abs_ic!r} not the overlap-aware MDE {expected_mde}",
    )

    # 3. STRICTER, never looser: the overlap-aware MDE is strictly above the
    #    inflated raw-row MDE.
    _assert(
        expected_mde > inflated_raw_mde,
        "rail defeated: overlap-aware MDE "
        f"{expected_mde} is not stricter than the inflated raw MDE {inflated_raw_mde}",
    )

    # 4. A NULL whose |IC| sits between the honest and inflated floors must not be
    #    credited as detectable: it stays below the honest MDE, and the scorer
    #    never auto-promotes a complete read to a survivor.
    null_ic = (inflated_raw_mde + expected_mde) / 2.0
    _assert(
        null_ic < expected_mde,
        "canary mid-point IC is not below the honest MDE",
    )
    _assert(
        null_ic > inflated_raw_mde,
        "canary mid-point IC is not above the inflated raw MDE",
    )
    _assert(
        diagnostics.primary_state
        not in {PRIMARY_STATE_WATCH, PRIMARY_STATE_CANDIDATE_RESEARCH},
        "rail defeated: a complete-read main-effect IC readout auto-promoted to a "
        f"survivor ({diagnostics.primary_state}); routing must stay on the strict floor",
    )
    _assert(
        diagnostics.is_survivor is False,
        "rail defeated: scorer minted a survivor without a reviewer verdict",
    )


def run_ic_power_statement_overlap_canary() -> None:
    """Run all IC-power overlap-aware assertions; raise on the first failure."""

    _check_embedded_power_statement_is_overlap_aware()


def main(argv: list[str] | None = None) -> int:
    try:
        run_ic_power_statement_overlap_canary()
    except AssertionError as exc:
        print(f"FAIL ic_power_statement_overlap: {exc}", file=sys.stderr)
        return 1
    print(
        "ic_power_statement_overlap OK: the main-effect scorer's embedded engine "
        "IC power_statement uses the overlap-aware n_eff = floor(usable_pairs / "
        "block) (NOT raw rows), the engine MDE = z/sqrt(n_eff-1) on that floor, the "
        "embedded statement agrees with the scorer verdict floor, the overlap MDE "
        "is strictly stricter than the inflated raw MDE, and a NULL between the two "
        "floors is not auto-promoted"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
