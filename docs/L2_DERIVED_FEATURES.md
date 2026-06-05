# L2-Derived Feature Skeleton

> **Design-only — not implemented.** Future, non-MVP L2/replay concepts for a
> later campaign. No L2 replay, passive-fill, queue, or live/order behavior is
> implemented or authorized in the current system.

ASV1-P26 adds a design-only, fixture-only skeleton for future L2-derived
features. It consumes the ASV1-P25 L2 snapshot and delta contracts and keeps
`event_ts`, `receive_ts`, and `available_ts` distinct.

This layer is not a production L2 processor. It does not replay books,
reconstruct order books, model queues, simulate passive fills, connect to live
feeds, route orders, validate strategies, or write a factor store.

## Feature Categories

The declarative specs in `src/alpha_system/l2/feature_specs.py` represent:

- top-of-book spread;
- top-1 and top-5 displayed-size imbalance;
- displayed depth by side;
- order count by side and level;
- microprice;
- quote update intensity over synthetic deltas;
- liquidity regime tags;
- future order-flow placeholders.

Each declaration wraps a draft `FactorSpec` with `domain="l2"` input fields,
`status="draft"`, zero additional availability lag, fixture-only parameters,
and `materialize_by_default=false`. These specs are compatible with the
FactorSpec and Factor Value Schema architecture but are not registered,
validated for promotion, approved, or materialized.

## Fixture Transforms

`src/alpha_system/l2/features.py` contains deterministic in-memory transforms
for tiny synthetic fixtures only. Input rows must use a data version prefixed by
`l2:synthetic:`. Non-synthetic data versions fail closed.

The transforms emit `FactorValue`-schema-compatible rows:

```text
factor_id
factor_version
instrument_id
event_ts
available_ts
session_id
bar_index
value
normalized_value
quality_flags
data_version
compute_version
```

For this skeleton, `bar_index` is a fixture ordinal because the ASV1-P25 L2
schema does not define canonical bar alignment. Future promotion would need a
reviewed alignment contract before using these features in a real factor store.

## Timing

Derived feature `available_ts` is the latest `available_ts` among the L2 input
rows actually used by that feature value. A feature value is not usable before
that timestamp. Event-rate features are ordered by the ASV1-P25 research order
key, which starts with `available_ts`, not `event_ts`.

Labels and `label_available_ts` values are rejected as inputs. This prevents
future-looking label data from entering L2-derived feature calculations.

## Quality Flags

Input `quality_flags` propagate into derived feature values. Feature-level flags
are added for fixture-only scope, incomplete top of book, missing book levels,
missing sides, missing order counts, and zero denominators.

Missing sides fail conservatively with null feature values. Missing inner depth
levels are not fabricated; the available displayed depth can still be used for
fixture calculations, but the output carries a missing-level quality flag.

## Materialization

ASV1-P26 has no default materialization path. Requests to persist L2-derived
feature values fail closed. No Parquet, Arrow, Feather, SQLite, local DB, factor
store, generated L2 data, or heavy artifact is produced by the feature skeleton
or its tests.

## Limitations

The skeleton is correctness scaffolding for future reviewed campaigns. It makes
no alpha, profitability, robustness, tradability, execution-completeness,
production-readiness, latency, passive-fill, or queue-position claim.
