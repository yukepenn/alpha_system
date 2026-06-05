# Liquidity/Structure Feature Family

`alpha_system.features.families.structure` defines the FLF-P12 liquidity-sweep
and market-structure primitive feature family. It is substrate code for
research feature definitions and in-memory fixture calculations only. It does
not materialize feature values, read raw provider files, call external
providers, persist registries, or make alpha, tradability, profitability,
broker, paper, live, or production claims.

## Inputs And Gates

The family consumes canonical OHLCV and, for BBO-derived descriptors, canonical
BBO input views from `alpha_system.features.input_views`. Rows are ordered by
`available_ts`, and every returned `FeatureValueRecord` carries the current
OHLCV input row's `available_ts`.

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

- prior high and prior low distance;
- opening-range high and opening-range low distance;
- sweep-high and sweep-low flags;
- failed-breakout high and failed-breakout low flags;
- close location value;
- wick rejection score;
- range contraction;
- BBO mid distance with same-bar quote alignment.

The calculations return in-memory `FeatureValueRecord` tuples. Undefined
values, insufficient windows, zero denominators, no-trade inputs, quote gaps,
and unavailable same-bar BBO inputs are represented as `None` values with
quality flags rather than filled from future or neighboring rows.

## Dense-Grid No-Trade Semantics

The family uses FLF-P04 trade-bar semantics. A row flagged with the canonical
`no_trade` quality flag is not treated as a trade bar for prior-level,
opening-range, sweep, failed-breakout, close-location, wick, range-contraction,
or BBO-distance calculations.

No synthetic no-trade row is used as price movement, range expansion, breakout
state, opening-range contribution, or quote-distance input.

## BBO Missingness And Quality

The BBO-derived descriptor requires a same-series, same-bar BBO row whose
`available_ts` is no later than the current OHLCV row's `available_ts`. It does
not carry quotes forward from a previous bar.

Rows carrying the canonical `missing_bbo` token or the canonical
`bbo_quarantined` token are not treated as usable quotes. Missing,
quarantined, invariant-violating, or unavailable BBO rows produce explicit gap
flags.

## Causality

Feature rows are calculated in `available_ts` order. A feature value at time `t`
may use only source rows whose `available_ts <= t`. Centered and future windows
are rejected for live Liquidity/Structure definitions. The family does not
expose offline-looking variants.

## Configuration

`configs/features/families/structure/README.md` is a placeholder for future
declarative feature-set selections. FLF-P12 does not add materialization
config, registry config, provider config, or execution behavior.
