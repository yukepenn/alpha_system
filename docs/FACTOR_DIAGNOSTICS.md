# Factor Diagnostics

## Purpose

The intraday diagnostics engine is a Tier 0 research tool. It compares versioned factor values with versioned future labels to produce diagnostic statistics, warnings, and a compact local manifest.

Diagnostics are not strategy PnL truth, not a backtest, not a candidate approval decision, and not tradability evidence. They are inputs for later review.

## Required Alignment

Every joined row must match:

- `factor_id` and `factor_version`
- `label_id` and `label_version`
- `data_version`
- `instrument_id`
- `event_ts`
- `session_id`
- optional configured horizon in seconds

The factor row must carry `available_ts`. The label row must carry `label_available_ts` and label path metadata with `session_id`, `label_version`, `horizon_end_ts`, `required_future_bars`, and `observed_future_bars`.

The diagnostics join rejects labels whose `label_available_ts` is before the aligned factor `available_ts`. The label layer also validates that `label_available_ts` is at or after `horizon_end_ts`.

## Diagnostic Families

Directional continuous factors:

- Pearson IC
- Rank IC
- IC by horizon
- IC decay
- IC by day, week, and month
- ICIR
- bucket monotonicity

Nonlinear bucket factors:

- bucket forward returns
- tail expectancy
- U-shape profile
- extreme bucket hit rate
- MFE and MAE by bucket when matching labels are present

Event trigger factors:

- event study counts
- conditional forward returns
- false breakout rate
- target-before-stop probability when matching labels are present
- post-event MFE and MAE when matching labels are present

Regime filters:

- with-filter versus without-filter uplift
- filter coverage
- false rejection rate
- conditional improvement statistics

Execution filters:

- spread sensitivity
- liquidity sensitivity
- slippage sensitivity
- volume participation sensitivity
- adverse selection proxy

Management features:

- target-before-stop probability
- time-to-target
- time-to-stop
- breakeven usefulness
- trailing stop usefulness

Management-feature outputs are diagnostic statistics only. They do not account for fills, orders, positions, commissions, capital, or execution state.

## Warning Discipline

The engine emits warnings for:

- insufficient sample size
- missing label coverage
- unstable horizon coverage
- high missing-factor rate
- invalid version references
- possible alignment gaps
- unsupported diagnostic type

Warnings stay in the diagnostic summary, run manifest, and optional temp/local registry records.

## Statistical Limits

These diagnostics are descriptive and fixture-testable. They do not control for multiple testing, universe selection, costs, capacity, fills, or later strategy rules. Small samples, sparse event triggers, unstable horizon coverage, and missing path labels can make a statistic unsuitable for decision-making without more review.

## Artifacts

`alpha study run` writes a compact `diagnostic_summary.json` and `run_manifest.json` under the configured local output directory. The default path is `artifacts/factor_studies/`, which is local-only for generated outputs and must not be committed.

Optional registry writes must use a temp/local SQLite path outside the repository. The command may record both `study_runs` and `factor_validation_runs` rows with `decision_status = diagnostic_recorded`; this is a record of diagnostics only and not candidate promotion.
