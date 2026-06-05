# Base OHLCV Feature Family

`alpha_system.features.families.ohlcv` defines the FLF-P08 Base OHLCV feature
family. It is substrate code for research feature definitions and in-memory
fixture calculations only. It does not materialize feature values, read raw
provider files, call external providers, persist registries, or make alpha,
tradability, profitability, broker, paper, live, or production claims.

## Inputs And Gates

The family consumes canonical OHLCV input views from
`alpha_system.features.input_views`. Rows are ordered by `available_ts`, and
every returned `FeatureValueRecord` carries the current input row's
`available_ts`.

Each feature definition must be built through
`build_ohlcv_feature_definition(...)` with an approved governance
`FeatureRequest`. The function consumes the FLF-P05 request gate and duplicate
exposure check. Missing, invalid, unapproved, duplicate-blocked, or
registry-unchecked requests fail closed before a `FeatureSpec` can become
implementation eligible.

Every definition is represented by an FLF-P06 `FeatureSpec` with
`FeatureInputSpec`, `TransformSpec`, `WindowSpec`, and `NormalizationSpec`, and
the deterministic `FeatureVersion` is derived from that contract. Live features
use only causal, non-offline windows anchored on `available_ts`.

## Feature Coverage

The FLF-P08 family covers:

- returns and log returns;
- rolling volatility, rolling range, ATR, rolling volume, and volume z-score;
- session minute, RTH flag, and ETH flag;
- opening range and overnight range;
- VWAP, anchored VWAP, and distance to VWAP;
- range position and trendiness.

The calculations return in-memory `FeatureValueRecord` tuples. Undefined
values, insufficient windows, zero denominators, no-volume VWAP inputs, and
no-trade inputs are represented as `None` values with quality flags rather than
filled from future or synthetic rows.

## Dense-Grid No-Trade Semantics

The family uses FLF-P04 trade-bar semantics. A row flagged with the canonical
`no_trade` quality flag is not treated as a trade bar for return, range, volume,
VWAP, or trend calculations. Rolling and cumulative features either propagate a
gap at that row or carry only previously observed real-trade state where the
feature definition permits it.

No synthetic no-trade row is used as volume, price movement, range expansion, or
VWAP contribution.

## Causality

Feature rows are calculated in `available_ts` order. A feature value at time `t`
may use only source rows whose `available_ts <= t`. Centered and future windows
are rejected for live Base OHLCV definitions. The family does not expose
offline-looking variants.

## Configuration

`configs/features/families/ohlcv/README.md` is a placeholder for future
declarative feature-set selections. FLF-P08 does not add materialization config,
registry config, provider config, or execution behavior.
