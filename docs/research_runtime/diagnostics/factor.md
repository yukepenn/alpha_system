# Factor Diagnostics Runtime

RT-P07 adds the factor-family diagnostics runtime at
`alpha_system.runtime.diagnostics.factor`. It is a local-only Tier 0 diagnostic
orchestrator. It consumes the shared RT-P06 diagnostics contracts and produces a
`FactorDiagnosticsReport` summary plus a visible `DiagnosticsRunRecord`.

The runtime does not resolve data, materialize features or labels, read raw
provider files, call external providers, run a signal probe, run a grid, run a
backtest, or add any broker, paper, live, order, account, strategy, portfolio,
deployment, alpha-search, or promotion behavior.

## Inputs

The public builders accept:

- a `DiagnosticsRunSpec`, `DiagnosticsRunSpecRef`, or reference mapping for the
  factor diagnostics run;
- an in-memory resolved factor/label observation view supplied by existing
  runtime input surfaces;
- lineage references such as the study-run spec id, runtime-plan id,
  DatasetVersion id, feature-pack ref, and label-pack ref;
- optional descriptive thresholds from
  `FactorDiagnosticsThresholds`.

Observation rows are synthetic-testable mappings with scalar fields such as
`factor_value`, `label_value`, `available_ts`, `label_available_ts`, and optional
`horizon_seconds`. Rows missing `available_ts` or `label_available_ts` are not
silently accepted; they surface a visible rejection reason. The full
availability and locked-test audit remains scoped to the later no-lookahead
runtime audit phase.

## Orchestration Boundary

The runtime delegates relationship summaries to existing research primitives:

- `alpha_system.research.ic.pearson_ic`
- `alpha_system.research.ic.rank_ic`
- `alpha_system.research.ic.ic_decay`
- `alpha_system.research.buckets.bucket_forward_returns`
- `alpha_system.research.buckets.bucket_monotonicity`
- `alpha_system.research.buckets.tail_expectancy`

It does not re-implement IC, RankIC, decay, or bucket-return math, and it does
not edit the consumed research packages.

## Report Shape

`FactorDiagnosticsReport` wraps the shared RT-P06 `DiagnosticsReport` and keeps
only compact scalar summaries:

- coverage ratio and usable pair count;
- missingness rate and missing input counts;
- outlier count and outlier rate;
- IC and RankIC summary;
- bucket monotonicity direction, rank correlation, sign changes, and tail
  expectancy;
- decay slope and first/last populated horizon summary;
- explicit limitations.

The report embeds no raw feature observations, label observations, market rows,
provider output, arrays, DataFrames, local database paths, or heavy artifact
paths.

## Outcomes

Clean descriptive diagnostics end in `DIAGNOSTICS_COMPLETE`. Failing or
non-runnable conditions stay visible:

- missing `available_ts` or `label_available_ts` -> `REJECTED`;
- low coverage, high missingness, or high outlier rate ->
  `DIAGNOSTICS_FAILED`;
- no rows, insufficient sample, unavailable IC/RankIC, or insufficient bucket
  population -> `INCONCLUSIVE`.

Every failed, rejected, or inconclusive report carries at least one RT-P05
`RunRejectionReason`, and the paired `DiagnosticsRunRecord` repeats the same
terminal state and reasons.

## Interpretation

A factor diagnostic PASS is not alpha validation. It is only a descriptive
quality/coverage result for a resolved factor/label view. It makes no claim that
a factor is predictive, robust, tradable, profitable, promotable, strategy-ready,
or production-ready. Later runtime phases own signal probes, cost stress,
bounded variants, no-lookahead audit, evidence drafts, and handoffs.

## Local Checks

```bash
PYTHONPATH=src python -c "import alpha_system.runtime.diagnostics.factor"
PYTHONPATH=src python -m pytest tests/unit/runtime/diagnostics/factor -q
test -f docs/research_runtime/diagnostics/factor.md
```
