# FUTCORE-P18 Regime Diagnostics

`FUTCORE-P18` records value-free regime momentum/reversion diagnostics for the
single approved regime StudySpec from `FUTCORE-P14`.

## Scope

Covered StudySpec:

- `sspec_267cc052e37668339c38d179` / `aspec_eb962fc197eaf3955c5e4711`:
  regime-gated momentum versus reversion over the locked development partition.

Diagnostics used the Research Runtime tool surface only: runtime entry/input
resolution, factor diagnostics, label diagnostics, session split diagnostics,
regime split diagnostics, signal-probe diagnostics, cost stress diagnostics,
`RuntimeToolResult`, and `RuntimeRunSummary`.

The resolved locked input surface references DatasetVersion
`dsv_databento_ohlcv_05404069799decb0`, five registered FeaturePacks, and three
registered LabelPacks for `5m`, `10m`, and `30m`. No source primitive, runtime,
feature, label, data, broker, execution, or CLI code was edited.

## Reports

Commit-eligible report artifacts:

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/INDEX.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/FUTCORE-P18_regime_summary.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/sspec_267cc052e37668339c38d179/runtime_reports.json`

Runtime status is `INCONCLUSIVE`. The joined 5m surface contains 6,862
observations, and the resolved `5m`, `10m`, and `30m` horizons contain 20,406
joined observations in total. Materialized value coverage is ES-only in this
lock; NQ and RTY cells are zero-count limitations and are not inferred or
substituted.

## Regime Splits

The exact StudySpec gate remains unresolved because the locked packs do not
expose a materialized `base_ohlcv_trendiness` input, explicit range-compression
activation binding, or failed directional extension state. The reports keep
trend/chop and momentum/reversion gate cells visible as inconclusive cells.

Available split inputs support descriptive high/low volatility and
range-compression summaries over locked OHLCV-derived packs. Those split
summaries are diagnostics only; they are not a replacement for the unresolved
gate and are not a promotion decision.

## Stability And Matrix

The StudySpec's declared `VariantBudget` is four. The report records four
predeclared variant cells: momentum and reversion modes over short and long
trailing gate windows. No post-diagnostic variants were added, and the binary
signal probes used the completed-bar direction threshold fixed at `0.5` rather
than a return-magnitude grid.

The session and horizon matrix covers `full_session`, `RTH_only`, `ETH_only`,
`ETH_evening`, `ETH_overnight`, `pre_RTH`, `RTH`, `post_RTH`, and
`RTH_with_ETH_context`. In the locked joined surface, RTH-related cells have
zero eligible observations and are preserved as zero-count diagnostics. The
primary `15m` horizon is unresolved because no registered 15m LabelPack resolves
in the locked local registry. The `1m` and `3m` horizons remain diagnostic-only
and are not a promotion basis.

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
