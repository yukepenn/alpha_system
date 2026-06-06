# Cross-Market Diagnostics Runtime

RT-P10 adds `alpha_system.runtime.diagnostics.cross_market`, the Tier 0
Cross-Market ES/NQ/RTY diagnostics runtime for the Research Runtime MVP. It
turns resolved runtime inputs plus a caller-supplied diagnostics view into a
descriptive `CrossMarketDiagnosticsReport` and a visible `DiagnosticsRunRecord`.

The runtime is local-only. It consumes accepted DatasetVersion metadata and
registered FeatureStore/LabelStore pack handles through `RuntimeInputPack`, and
it exposes `resolve_cross_market_dataset_version()` as the DatasetVersion
registry helper that delegates lookup to
`alpha_system.data.foundation.version_registry.resolve_dataset_version`. It does
not read raw provider files, call Databento or IBKR, materialize feature or
label stores, persist heavy outputs, build a multi-asset strategy, run a
backtest, or create portfolio scope.

## Inputs

Required inputs are:

- an RT-P06 `DiagnosticsRunSpec` or `DiagnosticsRunSpecRef` for
  `DiagnosticsFamily.CROSS_MARKET`;
- a resolved `RuntimeInputPack` binding an approved `AlphaSpec`, approved
  `StudySpec`, one accepted DatasetVersion, and registered feature/label pack
  handles;
- a small in-memory diagnostics observation view supplied by the caller, with
  `symbol` or `instrument_id`, `event_ts`, `available_ts`, one configured
  scalar metric field, and optional descriptive `regime_label`;
- optional `CrossMarketDiagnosticsConfig` thresholds.

Accepted DatasetVersion lifecycle states remain `VERSIONED` and
`READY_FOR_RESEARCH`. ES/NQ/RTY must be bound to a single DatasetVersion family;
mixed Databento plus IBKR source families and feature/label pack DatasetVersion
mismatches are rejected.

## No-Lookahead Alignment

The runtime groups observations by exact `event_ts`. A synchronized snapshot is
created only when every required symbol is present at that exact timestamp and
every symbol is available by the snapshot `decision_ts`. If a caller supplies
`decision_ts`, every instrument must be available by that timestamp. If it is
not supplied, the runtime waits until the slowest instrument's `available_ts`
for that exact timestamp.

There is no nearest join, forward fill, or cross-instrument look-ahead fill. A
missing slower instrument remains missing and is surfaced through coverage,
missingness, quality gates, and rejection reasons.

## Orchestrated Primitive

Pair correlation, lead/lag correlation, and regime-conditioned correlation are
delegated to:

- `alpha_system.research.correlation.correlations_to_existing_factors`

The runtime prepares exact-timestamp synchronized scalar views and calls the
existing primitive. It does not implement Pearson, rank correlation, or
cross-market correlation math. Spread and residual sections are arithmetic
descriptors over synchronized pairs only; they are not fitted models.

## Report Fields

`CrossMarketDiagnosticsReport.to_dict()` includes the shared RT-P06 report
payload plus scalar cross-market sections:

- `cross_market_timestamp_sync`
- `cross_market_symbol_summaries`
- `cross_market_pair_summaries`
- `cross_market_lead_lag_summaries`
- `cross_market_regime_summaries`
- `diagnostics_run_record`

The shared `coverage_summary` includes input count, required symbol count,
aligned snapshot count, missing `available_ts` count, unavailable-at-decision
count, missing metric count, duplicate aligned count, minimum per-symbol
coverage, maximum per-symbol missingness, and pack/input handle counts.

The shared `quality_summary` includes diagnostic terminal-state summary, quality
gate counts, pair/lead-lag/regime summary counts, maximum absolute delegated
correlation summaries, timestamp skew summaries, residual/spread section count,
and visible rejection reason count.

The report embeds no raw provider output, no value tables, no local DB paths, no
heavy artifact paths, and no generated runtime data files.

## Outcomes

Clean descriptive diagnostics end in `DIAGNOSTICS_COMPLETE`. Non-complete runs
stay visible:

- missing or late `available_ts`, label-only fields in the diagnostics view,
  missing governance references, mixed source families, or DatasetVersion
  mismatches -> `REJECTED`;
- low aligned coverage, high missingness, or weak timestamp synchronization ->
  `DIAGNOSTICS_FAILED`;
- no inputs, too few aligned snapshots, or unavailable delegated correlation
  summaries -> `INCONCLUSIVE`.

Every failed, rejected, or inconclusive report carries at least one RT-P05
`RunRejectionReason`, and the paired `DiagnosticsRunRecord` repeats the same
terminal state and reasons.

## Interpretation

This is a descriptive diagnostics runtime only. A complete cross-market
diagnostic is not alpha validation, not a promotion decision, not a strategy
result, and not evidence for broker, paper, live, order-routing, deployment, or
portfolio readiness. Later Research Runtime phases own signal probes, cost
stress, evidence drafts, and handoffs.

## Local Checks

```bash
PYTHONPATH=src python -c "import alpha_system.runtime.diagnostics.cross_market"
PYTHONPATH=src python -m pytest tests/unit/runtime/diagnostics/cross_market -q
test -f docs/research_runtime/diagnostics/cross_market.md
```
