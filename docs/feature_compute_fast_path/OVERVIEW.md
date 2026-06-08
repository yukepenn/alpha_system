# Feature Compute Fast Path Overview

`FEATURE_COMPUTE_FAST_PATH_V1` is a producer-compute campaign for a
single-machine, local, columnar, batch/vectorized, incremental feature/label
materialization path. The goal is to stop large-scale backfill from depending on
the per-row Python reference engine for throughput, while retaining that
reference engine as the correctness oracle.

## Parity Discipline

The V1 path is not accepted for a family or label pack until a synthetic-fixture
reference-parity test proves the fast output matches the reference output for:

- feature or label values, exact where required and within documented tolerance
  where floating-point differences are expected
- `available_ts` and `label_available_ts`
- insufficient-window, input-gap, and session-reset rows
- missingness and quality flags
- reference feature or label identity

Unexplained differences are blockers. Benchmark evidence is required before the
campaign can make a runtime-speed claim.

## Retained Oracle

The existing reference engine remains in place and is never deleted or weakened.
The V1 path produces values for existing governed feature and label definitions;
it does not create new feature identities, label identities, AlphaSpecs, or alpha
hypotheses.

## Boundaries

This campaign is substrate/infra engineering only. It does not include live
trading, paper trading, broker operations, order routing, production deployment,
external provider calls, Ray/GPU/cluster work, a feature-compiler/DSL platform,
new feature/label families, parameter search, or profitability/tradability
claims.

Raw/canonical data, feature values, label values, provider responses, local
SQLite registries, heavy artifacts, logs, caches, and `runs/**` artifacts remain
local-only and are never committed.

## Evidence Directory

`research/feature_compute_fast_path_v1/` is reserved for commit-eligible,
value-free summaries produced by later phases: parity reports, benchmark
summaries, and reconciliation summaries. Per-row values, Parquet outputs,
SQLite registries, and provider responses are not commit-eligible there.
