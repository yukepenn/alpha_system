# Diagnostics Report Contracts

RT-P06 adds the shared diagnostics contract surface under
`alpha_system.runtime.diagnostics`. It defines the common objects imported by
the parallel diagnostics phases RT-P07 through RT-P11. It does not run
diagnostics, resolve data, compute statistics, call providers, or make any
alpha, tradability, profitability, strategy, backtest, portfolio, or production
readiness claim.

## Contracts

`DiagnosticsRunSpec` is the pre-execution diagnostics request. It references an
RT-P04 `StudyRunSpec` and `RuntimePlan` by id and content hash, stores the
diagnostics family (`factor`, `label`, `splits`, `cross_market`, or `cost`),
and starts from the established `DIAGNOSTICS_READY` state. It is value-free:
the payload stores references and JSON-compatible metadata, not feature values,
label values, bars, rows, arrays, provider output, or heavy artifact paths.

`DiagnosticsRunRecord` is the visible lifecycle record for a diagnostics run.
It uses the RT-P05 `StudyRunResultState` enum rather than introducing a
parallel state model. A complete record links a value-free diagnostics report
reference. Failed, rejected, inconclusive, and blocked records must carry a
visible RT-P05 `RunRejectionReason` record so the reason remains auditable.

The current rejection linkage intentionally uses the RT-P05 rejection reason
surface. The fuller `RejectionReasonRecord` decision-state contract remains
scoped to RT-P15.

## Decision States

Diagnostics contracts use the runtime lifecycle states already named by the
campaign:

```text
DIAGNOSTICS_READY
  -> DIAGNOSTICS_RUNNING
  -> DIAGNOSTICS_COMPLETE
  -> DIAGNOSTICS_FAILED
Terminal at any stage: REJECTED | INCONCLUSIVE | BLOCKED
```

No diagnostics object can move into prohibited MVP states such as
`ALPHA_VALIDATED`, `FACTOR_PROMOTED`, `STRATEGY_READY`, `PORTFOLIO_READY`,
`LIVE_READY`, `PAPER_READY`, `PROFITABLE`, `TRADABLE`, or
`PRODUCTION_READY`.

## Report Shape

`DiagnosticsReport` is the shared descriptive report base. Family-specific
reports in later phases should specialize this shape by composition or
subclassing while preserving the same fields and restrictions:

- `report_kind` and `diagnostics_family`;
- `diagnostics_run_spec_ref`;
- diagnostics `status`;
- `lineage_refs` for version and run references;
- scalar-only `coverage_summary`;
- scalar-only `quality_summary`;
- explicit non-empty `limitations`;
- optional `DiagnosticsQualityGate` entries;
- visible rejection reason records for failed, rejected, inconclusive, or
  blocked reports.

The report payload marks itself as descriptive and non-promotional. A diagnostic
quality-gate `PASS` is only a diagnostics gate result. It is not alpha
validation and is not evidence of tradability, profitability, strategy
readiness, or production readiness.

## No Raw Or Heavy Data

Diagnostics reports and records are commit-eligible contract summaries only.
They must not embed raw or heavy data:

- no feature or label value arrays;
- no canonical bars, provider rows, or market rows;
- no DataFrame, Series, NumPy, Parquet, Arrow, Feather, DBN, ZST, SQLite, DB,
  WAL, or cache references;
- no local provider output;
- no materialized runtime values.

The shared report validators reject raw/value-bearing field names, non-scalar
summary fields, heavy artifact suffixes, and promotional claim phrases.

## Specialization Expectations

RT-P07 through RT-P11 should import these shared objects and add only the
family-specific orchestration they own:

- RT-P07 `FactorDiagnosticsReport`: factor diagnostics summaries over existing
  research primitives.
- RT-P08 `LabelDiagnosticsReport`: label diagnostics summaries.
- RT-P09 `RegimeSplitReport` / `SessionSplitReport`: split diagnostics
  summaries.
- RT-P10 `CrossMarketDiagnosticsReport`: cross-market diagnostics summaries.
- RT-P11 cost reports: cost and cost-stress diagnostics summaries.

Those phases should not edit the shared RT-P06 files. They should keep raw
runtime outputs local-only and attach only value-free report or artifact
references to runtime records.
