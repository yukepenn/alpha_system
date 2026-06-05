# Cross-Market ES/NQ/RTY Feature Family

`alpha_system.features.families.cross_market` defines the FLF-P11
Cross-Market ES/NQ/RTY feature family. It is substrate code for research
feature definitions and in-memory fixture calculations only. It does not
materialize feature values, read raw provider files, call external providers,
persist registries, or make alpha, tradability, profitability, broker, paper,
live, or production claims.

## Inputs And Gates

The family consumes per-instrument canonical OHLCV input views from
`alpha_system.features.input_views`. Rows are ordered by `available_ts`, and
every returned `FeatureValueRecord` carries the output row's `available_ts`.

Each feature definition must be built through
`build_cross_market_feature_definition(...)` with an approved governance
`FeatureRequest`. The function consumes the FLF-P05 request gate and duplicate
exposure check. Missing, invalid, unapproved, duplicate-blocked, or
registry-unchecked requests fail closed before a `FeatureSpec` can become
implementation eligible.

Every definition is represented by an FLF-P06 `FeatureSpec` with
`FeatureInputSpec`, `TransformSpec`, `WindowSpec`, and `NormalizationSpec`, and
the deterministic `FeatureVersion` is derived from that contract. Live features
use only causal, non-offline windows anchored on `available_ts`.

## Feature Coverage

The FLF-P11 family covers:

- synchronized ES/NQ/RTY returns;
- NQ-minus-ES and RTY-minus-ES return spreads;
- NQ-vs-ES and RTY-vs-ES rolling beta residuals;
- NQ-vs-ES and RTY-vs-ES rolling correlations;
- confirmation and divergence flags;
- risk-on and risk-off rotation proxy descriptors.

The calculations return in-memory `FeatureValueRecord` tuples. Undefined
values, insufficient windows, zero-variance rolling windows, missing per-market
history, and no-trade inputs are represented as `None` values with quality
flags rather than filled from future or neighboring rows.

## Cross-Market Alignment

The family aligns ES, NQ, and RTY as-of the output `available_ts`. A feature
value at time `t` uses, for each market, only source rows and return primitives
whose own `available_ts <= t`. If one market arrives later than another, earlier
outputs continue to use only the latest value that was available by that output
timestamp. The later-arriving row is not visible to those earlier outputs.

The public `align_cross_market_rows(...)` helper exposes this alignment for
tests and audits. It records each market's source `available_ts` values so
no-lookahead checks can verify that every source timestamp is at or before the
output timestamp.

## No-Trade And BBO Missingness

The family uses FLF-P04 trade-bar semantics through the shared causal primitive
projection. A row flagged with the canonical `no_trade` quality flag is not
treated as a trade bar for cross-market returns, spreads, rolling
relationships, flags, or rotation proxies.

Cross-market return descriptors are not quote-derived features. When optional
BBO views are supplied for quality context, rows carrying `missing_bbo` or
`bbo_quarantined` at the exact output `available_ts` are surfaced as quality
flags. Quotes are not forward-filled or interpolated.

## DatasetVersion Family Boundary

ES, NQ, and RTY inputs must come from one accepted DatasetVersion family. The
family rejects mixed DatasetVersion-family tokens in its in-memory input bundle
and in declared feature-definition `dataset_version_ids`. This keeps deep
history and broker-source validation DatasetVersions separate unless a later
reviewed integration layer explicitly defines a safe composition path.

## Configuration

`configs/features/families/cross_market/README.md` is a placeholder for future
declarative feature-set selections. FLF-P11 does not add materialization config,
registry config, provider config, execution behavior, or persisted feature
values.
