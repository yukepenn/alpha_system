# Canary: binary_overlap_conditioned_neff (binary multi-bar conditioned N_eff, task #74)

Purpose: guard the fix for the #74 divergence between the conditioned-power GATE
and the fast-probe conditioned-power READOUT on a BINARY multi-bar path label.

The #52 conditioned-power gate
(`src/alpha_system/research_lane/conditioned_power.py`) derived its overlap block
via `forward_overlap_block_size(outcome_label_type, ...)` -- keyed on the label
TYPE. For a binary path label like `target_before_stop` the `outcome_label_type`
is `None`, and that type-only helper returns block size 1 (NO overlap discount)
even when the slice carries `required_future_bars > 1`. But a binary path label
whose lookahead window spans `required_future_bars` bars on a 1m cadence IS
forward-OVERLAPPING by its HORIZON: consecutive joint-firing events share
`required_future_bars - 1` of their lookahead bars. So the gate reported the RAW
joint-firing count as the conditioned `n_eff` -- a ~horizon-fold inflation that
resurrects the exact #474 regression the #52 gate was meant to prevent.

Empirically (FQ08 ES_2020 15m): the pre-fix gate reported
`overlap_block_size=1`, `conditioned_n_eff=1530`, `MDE 0.0501`; the HONEST #474
discount is `~1530 / 15 = 102`, `MDE ~0.195` -- a ~15x `n_eff` inflation that made
the gate dishonest for binary multi-bar conditional setups.

Meanwhile the fast-probe READOUT
(`src/alpha_system/research/conditional_probe.py::_conditioned_power_n_eff`, wired
from `fast_probe` with `outcome_overlap_bars=slice_spec.required_future_bars`)
ALREADY discounts the conditioned event series by `required_future_bars` whenever
it exceeds 1 -- regardless of label type. So pre-fix the GATE (block 1) and the
READOUT (block `required_future_bars`) reported TWO DIFFERENT conditioned `n_eff`
for the SAME binary multi-bar slice. The fix makes the gate's block derivation
(`conditioned_power._conditioned_overlap_block_size`) mirror the readout's
exactly: a binary path label (`outcome_label_type` None) discounts by
`required_future_bars`; a typed forward-overlapping outcome still delegates to the
fail-closed `forward_overlap_block_size` helper. Continuous-outcome
(`net_excursion`) behavior is unchanged (block = horizon in both).

Runner: `src/alpha_system/governance/canaries/binary_overlap_conditioned_neff.py`,
registered in `tools/hooks/canary_runner.py`. It builds SYNTHETIC in-memory
context + trigger feature rows (NO data root, NO parquet backend, per the #503
CI-equivalent-env lesson) for a BINARY path label (`outcome_label_type` None) with
`required_future_bars > 1` and a clustered joint-firing series, and exercises the
shared conditioned-power core
(`conditioned_power_from_injected_rows` + `conditioned_power_verdict`), asserting:

1. **Binary multi-bar block = horizon (the fix).** The gate's `overlap_block_size`
   equals `required_future_bars`, so the conditioned `n_eff` is #474-discounted to
   `~events / required_future_bars` -- NOT the raw joint-firing count. This
   assertion FAILS on the pre-fix code (which left the binary block at 1 and
   reported the raw count).

2. **Gate == readout.** The gate's conditioned `n_eff` EQUALS the fast-probe
   readout's `_conditioned_power_n_eff` for the SAME conditioned event count and
   horizon -- the single-truth requirement of the fix.

3. **The gate FAILS CLOSED.** The honest (discounted) conditioned `MDE` is above
   the plausible-effect floor (`PLAUSIBLE_CONDITIONED_ABS_IC_FLOOR = 0.05`), so the
   verdict is FAIL with the typed `UNDERPOWERED_CONDITIONED` issue code.

4. **A genuinely single-bar binary outcome stays undiscounted.** With
   `required_future_bars` None / 1 the block is 1 and the conditioned `n_eff` is
   the raw event count, still matching the readout -- the fix does not
   over-penalize a contemporaneous binary outcome.

The canary constructs its synthetic, value-free inputs programmatically; this
directory documents the canary for human audit and carries no real market data,
factor values, labels, or scores. A passing canary validates the
conditioned-power gate==readout overlap contract only and implies NO alpha,
profitability, or tradability claim. The verdict is a deterministic RECORD; the
machine never auto-promotes.
