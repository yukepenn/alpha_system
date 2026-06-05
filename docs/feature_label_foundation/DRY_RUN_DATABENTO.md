# Small Local Databento DatasetVersion Dry Run

FLF-P26 adds a bounded feature/label dry-run path for one accepted local
Databento DatasetVersion slice. The path resolves the DatasetVersion through
the local registry, validates supplied canonical mappings through
`CanonicalBarRecord.from_mapping`, `CanonicalBBORecord.from_mapping`, and
`DenseGridBarRecord.from_mapping`, and delegates value production to the
existing feature and label materialization engines.

This dry run does not pull data, call a provider, read raw provider files, or
write inside the repository. Feature and label values are local-only under
`ALPHA_DATA_ROOT`; committed output is limited to this row-free summary and the
CI-safe synthetic integration test.

## Operator Command

Run the real local dry run only when the accepted local registry and canonical
DatasetVersion slice already exist:

```bash
export ALPHA_DATA_ROOT=~/alpha_data/alpha_system
alpha feature dry-run --dataset dsv_databento_ohlcv_<hex> --small --local-only
```

The phase implementation provides the engine surface for this command. Later
tooling can bind the command to the same helper without adding provider calls or
raw-file readers.

## Bounded Scope

- One accepted DatasetVersion, resolved from the local registry.
- Prefer `development_partition`; locked-test use still requires governance
  contamination metadata.
- A small row cap is enforced before materialization.
- A small approved feature set and label set is materialized under
  `ALPHA_DATA_ROOT` only.
- The row-free summary records counts, partition, lifecycle state, quality and
  coverage status, BBO missingness counts, synthetic no-trade counts, and
  blocking flags.

The summary never includes raw rows, feature values, label values, provider
responses, local registry contents, or local artifact paths.

## Executor Result

Result: `PASS_WITH_WARNINGS`.

The executor workspace did not receive a real local Databento DatasetVersion id,
registry evidence, or canonical row slice, so the real operator dry run was not
performed. No external call was attempted. The CI-safe integration test creates
a temporary accepted synthetic DatasetVersion in a temporary registry, feeds
canonical mappings through the same resolver and canonical loaders, materializes
a bounded feature/label sample under a temporary `ALPHA_DATA_ROOT`, and asserts
that the committed-facing summary is row-free.

## Safety Statement

This phase makes no alpha, predictive, profitability, tradability, strategy,
backtest, broker, live, paper, deployment, or production-readiness claim. A
feature is not alpha. A label is not alpha. A successful dry run only shows that
the local accepted-DatasetVersion consumption path can drive the feature and
label engines in bounded mode.
