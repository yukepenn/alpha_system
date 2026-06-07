# FUTCORE-P19 Liquidity / PA Diagnostics

`FUTCORE-P19` records value-free liquidity-sweep and objective price-action
diagnostics for the two approved liquidity/PA StudySpecs from `FUTCORE-P14`.

## Scope

Covered StudySpecs:

- `sspec_27bf1262b0bd23d27191cc86` / `aspec_df2d040e45564c259ef3de6d`:
  sweep close-back-inside objective price-action context.
- `sspec_02c400a561891171a33c0c66` / `aspec_39ffc190cfbfa6ba0b1a2a25`:
  failed-breakout reversal context.

Diagnostics used the Research Runtime tool surface only: runtime entry/input
resolution, factor diagnostics, label diagnostics, session split diagnostics,
spread/liquidity split diagnostics, signal-probe diagnostics, cost stress
diagnostics, `RuntimeToolResult`, and `RuntimeRunSummary`.

The resolved locked input surface references DatasetVersion
`dsv_databento_ohlcv_05404069799decb0`, six registered FeaturePacks, and three
registered LabelPacks for `5m`, `10m`, and `30m`. No source primitive, runtime,
feature, label, data, broker, execution, or CLI code was edited.

## Reports

Commit-eligible report artifacts:

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/INDEX.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/FUTCORE-P19_liquidity_pa_summary.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/sspec_27bf1262b0bd23d27191cc86/runtime_reports.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/sspec_02c400a561891171a33c0c66/runtime_reports.json`

Runtime status is `INCONCLUSIVE` for both StudySpecs. Each report contains
6,862 joined `5m` rows, 20,406 joined `10m` rows, and 20,406 joined `30m`
rows over the resolved locked label packs. The `15m` primary horizon is
unresolved because no registered 15m LabelPack resolves in the locked P03/P14
binding.

## Trigger Counts

Exact objective-rule trigger counts are unresolved. The locked packs expose
OHLCV returns, range, range-position, session, and volume/activity context, but
they do not expose materialized trigger flags for prior high/low sweep,
close-back-inside, wick rejection, displacement, compression breakout, or
failed-breakout reversal.

The reports keep each objective rule as an explicit unresolved count cell with
`pilot_side_recomputation_performed: false`. No raw provider data, canonical
bars, or pilot-side trigger reconstruction was used.

## Spread And Liquidity Splits

Spread buckets are unresolved because no locked BBO or spread FeaturePack is
bound to these StudySpecs. Liquidity buckets are descriptive activity-proxy
splits derived from the locked `base_ohlcv_volume_zscore` pack: thin,
normal, thick, and unresolved cells are reported by horizon and session.

All joined rows are ETH in the locked surface because the resolved RTH flag is
zero throughout this pack. RTH cells are preserved as zero-count diagnostics,
not inferred or filled. The `1m` and `3m` horizons remain diagnostic-only and
are not a promotion basis.

## Cost Boundary

Cost diagnostics carry through the pinned nonzero profiles `base`, `stress_1`,
`stress_2`, and `double_cost`. `zero_cost` is recorded only as diagnostic
context and is not a continuation or promotion basis.

Cost outputs are sensitivity summaries over runtime probe fills. They are not
signal outcome, execution, broker, order, deployment, or capital-allocation
evidence.

## Boundary Confirmation

The diagnostics are value-free summary and metadata artifacts only. They include
counts, split keys, report references, pack ids, hashes, statuses, and
limitations, but no row-level feature values, label values, provider responses,
heavy artifacts, or local run artifacts. No promotion decision, reviewer action,
PR, merge, live operation, paper operation, broker call, order routing, or
deployment action was performed by the executor.
