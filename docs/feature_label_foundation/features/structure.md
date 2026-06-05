# Liquidity Sweep / Structure Primitive Feature Family

`alpha_system.features.families.structure` defines the FLF-P12 Liquidity
Sweep / Structure Primitive feature family. It is substrate code for research
feature definitions and in-memory fixture calculations only. It does not
materialize feature values, read raw provider files, call external providers,
persist registries, or make alpha, tradability, profitability, broker, paper,
live, or production claims.

## Inputs And Gates

The family consumes canonical OHLCV input views and optional exact-time BBO
quality context from `alpha_system.features.input_views`. Rows are ordered by
`available_ts`, and every returned `FeatureValueRecord` carries the current
OHLCV row's `available_ts`.

Each feature definition must be built through
`build_structure_feature_definition(...)` with an approved governance
`FeatureRequest`. The function consumes the FLF-P05 request gate and duplicate
exposure check. Missing, invalid, unapproved, duplicate-blocked, or
registry-unchecked requests fail closed before a `FeatureSpec` can become
implementation eligible.

Every definition is represented by an FLF-P06 `FeatureSpec` with
`FeatureInputSpec`, `TransformSpec`, `WindowSpec`, and `NormalizationSpec`, and
the deterministic `FeatureVersion` is derived from that contract. Live features
use only causal, non-offline windows anchored on `available_ts`.

## Feature Coverage

The FLF-P12 family covers:

- prior high distance and prior low distance;
- opening-range high distance and opening-range low distance;
- sweep-high and sweep-low flags;
- failed-high-breakout and failed-low-breakout flags;
- close location value;
- wick rejection score;
- range contraction.

The calculations return in-memory `FeatureValueRecord` tuples. Undefined
values, insufficient windows, zero ranges, no prior real-trade window, no
opening real-trade state, and no-trade inputs are represented as `None` values
with quality flags rather than filled from future or synthetic rows.

## No-Trade And BBO Missingness

The family uses FLF-P04 trade-bar semantics. A row flagged with the canonical
`no_trade` quality flag is not treated as a trade bar for prior-high/low,
opening-range, sweep, failed-breakout, wick, close-location, or range
contraction calculations. Rolling structure descriptors surface gaps when the
trailing causal window contains a no-trade row.

Optional BBO rows are used only for exact-`available_ts` quality context. Rows
carrying `missing_bbo` or `bbo_quarantined` are surfaced as quality flags on the
matching output timestamp. Quotes are not forward-filled, interpolated, or used
as price levels for structure descriptors.

## Causality

Feature rows are calculated in `available_ts` order. A feature value at time `t`
may use only source rows whose `available_ts <= t`. Prior-high/low, sweep,
failed-breakout, and range-contraction windows exclude the current row from the
prior reference level and use only trailing real-trade rows. Centered and future
windows are rejected for live Liquidity Structure definitions. The family does
not expose offline-looking variants.

## Configuration

`configs/features/families/structure/README.md` is a placeholder for future
declarative feature-set selections. FLF-P12 does not add materialization config,
registry config, provider config, execution behavior, or persisted feature
values.
