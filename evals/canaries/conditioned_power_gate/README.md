# Canary: conditioned_power_gate (conditional SETUP power, task #52)

Purpose: guard the fix for the "mass-production of underpowered nulls" failure
mode. The pre-test testability gate's N_eff/MDE check
(`src/alpha_system/research_lane/testability_gate.py::_check_n_eff_mde_and_dedup`)
historically accepted the AUTHOR-SUPPLIED, UNCONDITIONED slice `n_eff`/`MDE` for
every study kind and only enforced a `(0, 1]` plausibility floor. For a
`context_not_equal_trigger` (conditional SETUP) idea the unconditioned figure is
the full-slice power, but the real power is governed by the CONDITIONED
(entry-context AND event-trigger) joint-firing event count, collapsed to
NON-OVERLAPPING at the label horizon (the ratified #474 overlap rule applied to
the conditioned event series).

Empirically (idea
`research/intraday_system_custody_v0/fq08_chop_vwap_stretch_meanrev_es2020_30m_net_excursion.idea.yaml`,
slice `ES_2020_30m`): the author recorded `n_eff=11213` / `MDE=0.0185`, but only
~1.4% of rows satisfy BOTH the context and the trigger predicate and those events
cluster heavily inside the 30-bar horizon, so the honest non-overlapping
conditioned `n_eff` is an order of magnitude smaller and the conditioned `MDE`
several-fold larger. The pre-fix gate PASSED it anyway -> the underpowered setup
slipped through and its downstream verdict misrepresented power.

Runner: `src/alpha_system/governance/canaries/conditioned_power_gate.py`,
registered in `tools/hooks/canary_runner.py`. It builds SYNTHETIC in-memory
context + trigger feature rows (NO data root, NO parquet backend, per the #503
CI-equivalent-env lesson) that mirror the FQ08 case (~1.4% joint firing, heavy
intra-horizon clustering) and exercises the shared conditioned-power core
(`src/alpha_system/research_lane/conditioned_power.py::conditioned_power_from_injected_rows`
+ `conditioned_power_verdict`), asserting:

1. **Conditioned n_eff << unconditioned grid.** For the FQ08-shaped sparse +
   clustered joint-firing series the conditioned non-overlapping `n_eff`
   (#474-discounted by the 30-bar horizon) is far below the unconditioned row
   count.

2. **The gate FAILS CLOSED on the underpowered conditioned slice.** The conditioned
   `MDE` is above the plausible-effect floor
   (`PLAUSIBLE_CONDITIONED_ABS_IC_FLOOR = 0.05`), so the verdict is FAIL with the
   typed `UNDERPOWERED_CONDITIONED` issue code -- distinct from `DATA_GAP` and from
   the conditioned-power precondition error.

3. **A genuinely well-powered conditioned setup still PASSES.** A dense joint-firing
   series whose #474-discounted conditioned `n_eff` yields an `MDE` at/below the
   floor passes, so the fix does not over-fire.

Why a floor of 0.05: a conditional setup edge is a strong, detectable effect; a
conditioned `MDE` above `0.05` means the probe cannot even detect a `|rank-IC|` of
`0.05` at the `z=1.96` level, so the slice is underpowered for any plausible
conditional effect. It is small enough that a genuinely well-powered conditioned
slice (`n_eff >= ~1538`) passes. The constant is overridable per call.

This is research-only diagnostic plumbing. A passing canary validates the
conditioned-power gate contract only and implies NO alpha, profitability, or
tradability claim. The gate is a deterministic RECORD; the machine never
auto-promotes.
