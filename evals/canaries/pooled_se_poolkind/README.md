# Canary: pooled_se_poolkind (cross-partition OOS pooled SE)

Purpose: guard the cross-partition pooled OOS aggregator
(`src/alpha_system/governance/pooled_hypothesis.py::aggregate_pooled_metric`)
against the silent-independence bug. The runner
(`src/alpha_system/governance/canaries/pooled_se_poolkind.py`, registered in
`tools/hooks/canary_runner.py`) asserts:

1. **Independent back-compat.** With an explicit `pooled_correlation=0.0` the
   pooled SE is exactly the historical independent `sqrt(sum se^2)/K` and the
   effective N is the independent `sum(n_eff_i)`. A genuinely-uncorrelated pool
   is unchanged.

2. **The rail is no longer silently defeated.** A set of overlapping components
   whose naive (`rho = 0`) pooled z CLEARS significance does NOT clear under the
   corrected, conservative pool-kind default `rho`: the corrected pooled SE is
   strictly larger, the corrected pooled z strictly smaller, and the corrected
   effective N strictly smaller than the naive `sum`. The inflated significance
   is withdrawn deterministically -- without a human.

3. **Worst-case collapse + fail-loud.** A `CROSS_HORIZON` pool defaults to the
   worst-case `rho = 1.0`, where the pooled SE collapses to `mean(se_i)` and the
   effective N is floored at the weakest single member (never the naive sum). An
   out-of-range correlation input (`rho = 1.5`) fails closed with
   `invalid_pooled_correlation`.

Why: pooling overlapping horizons on the same bars (autocorrelated) or
contemporaneously correlated index symbols (ES/NQ/RTY ~0.5-0.8) with a naive
`sqrt(sum se^2)/K` SE and `sum(n_eff)` UNDERSTATES the pooled SE and OVERSTATES
power, inflating the pooled z and waving noise through the family-FDR gate. This
is the #474 overlap sin one layer up. The fix branches the pooled SE / effective
N on `pool_kind` and an explicit (or conservative default) average pairwise
correlation `rho`, and surfaces the assumption on the result so a reviewer can
see WHAT correlation the pooled significance rests on.

The canary constructs its synthetic, value-free inputs programmatically; this
directory documents the canary for human audit and carries no real market data,
factor values, labels, or scores. A passing canary validates the
correlation-aware pooling math only and implies NO alpha, profitability, or
tradability claim. The pooled verdict is a deterministic RECORD; the machine
never auto-promotes.
