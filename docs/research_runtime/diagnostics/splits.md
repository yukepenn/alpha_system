# Split Diagnostics

RT-P09 adds `alpha_system.runtime.diagnostics.splits`, the session and regime
split diagnostics surface for the Research Runtime. It produces
`SessionSplitReport` and `RegimeSplitReport` objects that carry the shared
RT-P06 `DiagnosticsReport` contract, `DiagnosticsFamily.SPLITS`, a
`DiagnosticsQualityGate`, scalar split summaries, limitations, and visible
rejection reasons when a split cannot be reported.

## Split Families

Session splits describe RTH versus ETH and intraday open, mid, and close
segments. Assignment uses explicit row session metadata when present. If a row
does not carry the session label or segment, the runtime derives the metadata
from `available_ts` and the resolved `RuntimeInputPack.session_scope` windows.

Regime splits describe volatility, spread, liquidity, and trend/range metadata
buckets. The runtime expects those buckets to be present as already-resolved
metadata fields such as `volatility_bucket`, `spread_bucket`,
`liquidity_bucket`, and `trend_state`.

## Orchestrated Primitive

The split runtime calls `alpha_system.research.regimes` directly:

- `regime_filter_coverage`
- `regime_filter_uplift`
- `false_rejection_rate`
- `conditional_strategy_improvement`

It does not re-implement regime diagnostics math. The runtime only prepares a
boolean `regime_filter` view for each split bucket and summarizes the primitive
outputs as scalar descriptive fields.

## Availability Discipline

Split assignment is conditioned on metadata available at `available_ts`.
`label_available_ts` is used only as an outcome-availability guard when label
outcomes are present. Label outcome fields and future outcome fields are
rejected as conditioning fields, so labels cannot become split inputs.

Rows with missing `available_ts` are excluded and recorded as visible
`data_unavailable` reasons. Rows with `label_available_ts` before
`available_ts` are excluded and recorded as `leakage_risk` reasons.

## Report Posture

The reports are descriptive and non-promotional. A split with different scalar
summaries across buckets is only a heterogeneity description. It is not
validation of an alpha claim, not a recommendation, and not a
strategy-conditioning conclusion.

Low-sample or unavailable splits fail closed. The split summary remains visible
with `status = "inconclusive"` plus a `low_sample` or `data_unavailable`
reason, and the shared report status becomes `INCONCLUSIVE` or `REJECTED` when
the RT-P06 contract requires a visible rejection reason.

## Limitations

The split runtime does not load provider data, materialize features or labels,
run a signal probe, run cost stress, create a candidate, or call broker/live/
paper/deployment paths. It stores no raw values, arrays, bars, rows, provider
responses, local paths, databases, caches, logs, or heavy artifacts in report
objects. Tiny synthetic fixtures under
`tests/fixtures/runtime/diagnostics/splits/` are the only data-like files added
for this phase.

