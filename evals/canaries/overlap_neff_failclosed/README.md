# Canary: overlap_neff_failclosed (forward-overlap N_eff, #474 law)

Purpose: guard the ratified #474 law -- a FORWARD-OVERLAPPING outcome label
(forward/cost-adjusted return, `mfe`/`mae` excursion, triple-barrier, derived
`net_excursion`) looks several bars ahead, so consecutive bar-spaced
observations overlap and the raw row count badly overstates the independent
sample. Such an outcome MUST carry an overlap-discounted N_eff. The latent
regression this canary catches is the SILENT fallback to raw rows /
`discount_factor == 1` when an OPTIONAL horizon field (`required_future_bars`)
is left unset.

Runner: `src/alpha_system/governance/canaries/overlap_neff_failclosed.py`,
registered in `tools/hooks/canary_runner.py`. It exercises the shared
fail-closed helper
(`src/alpha_system/runtime/diagnostics/splits/n_eff.py::forward_overlap_block_size`
/ `is_forward_overlapping_outcome`) and the main-effect fast-probe metadata
builder
(`src/alpha_system/research_lane/fast_probe.py::_main_effect_overlap_metadata`),
asserting:

1. **Classification is by TYPE, not by an optional field.** Forward families
   classify as forward-overlapping; the binary contemporaneous outcome does not.

2. **A known multi-bar horizon is discounted.** `forward_overlap_block_size`
   returns the horizon block and the estimator's N_eff is STRICTLY below the raw
   row count (`discount_factor > 1`).

3. **Fail-closed when the horizon is unknown.** A forward-overlapping outcome
   with NO derivable horizon RAISES `NEffSampleReportingError` -- it NEVER
   silently returns block size 1 / raw rows. Both the shared helper and the
   main-effect fast-probe metadata builder fail closed.

4. **A non-overlapping outcome stays undiscounted** (block size 1, raw rows), so
   the fix does not over-penalize a contemporaneous outcome.

Why: the #474 law was previously enforced contingent on the OPTIONAL
`slice_spec.required_future_bars` field. When unset on a forward-overlapping
outcome, BOTH the main-effect IC-power site and the setup conditioned-N_eff site
silently used `discount_factor=1` (raw rows), inflating apparent power by
~sqrt(horizon) and manufacturing false signals. The fix keys the discount on the
OUTCOME LABEL TYPE and fails closed when the block size cannot be derived. This
canary turns that latent silent-raw regression into a caught one -- without a
human.

The canary constructs its synthetic, value-free inputs programmatically; this
directory documents the canary for human audit and carries no real market data,
factor values, labels, or scores. A passing canary validates the overlap-aware
N_eff fail-closed contract only and implies NO alpha, profitability, or
tradability claim. The verdict is a deterministic RECORD; the machine never
auto-promotes.
