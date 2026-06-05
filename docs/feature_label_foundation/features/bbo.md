# BBO Tradability Feature Family

`alpha_system.features.families.bbo` defines the FLF-P09 BBO tradability feature
family. It is substrate code for research feature definitions and in-memory
fixture calculations only. It does not materialize feature values, read raw
provider files, call external providers, persist registries, or make alpha,
tradability, profitability, broker, paper, live, or production claims.

## Inputs And Gates

The family consumes canonical BBO input views from
`alpha_system.features.input_views`. Rows are ordered by `available_ts`, and
every returned `FeatureValueRecord` carries the current input row's
`available_ts`.

Each feature definition must be built through
`build_bbo_feature_definition(...)` with an approved governance
`FeatureRequest`. The function consumes the FLF-P05 request gate and duplicate
exposure check. Missing, invalid, unapproved, duplicate-blocked, or
registry-unchecked requests fail closed before a `FeatureSpec` can become
implementation eligible.

Every definition is represented by an FLF-P06 `FeatureSpec` with
`FeatureInputSpec`, `TransformSpec`, `WindowSpec`, and `NormalizationSpec`, and
the deterministic `FeatureVersion` is derived from that contract. The BBO
package also exposes BBO-specific contract wrappers:

- `BBOFeatureSpec`
- `SpreadFeatureSpec`
- `MicropriceFeatureSpec`
- `TopBookImbalanceFeatureSpec`
- `LiquidityQualityFeatureSpec`

Live features use only causal, non-offline windows anchored on `available_ts`.

## Feature Coverage

The FLF-P09 family covers:

- mid, spread, spread ticks, spread bps, and causal spread z-score;
- bid size, ask size, top-book depth, and top-book imbalance;
- microprice and microprice minus mid;
- missing-BBO, bad-quote, wide-spread, and low-depth flags.

The calculations return in-memory `FeatureValueRecord` tuples. Undefined
values, insufficient windows, invalid size denominators, unavailable optional
spread ticks, and quote-quality gaps are represented as `None` values with
quality flags rather than filled from future or neighboring rows.

## BBO Missingness And Quality

The family uses FLF-P04 BBO semantics. Rows carrying the canonical
`missing_bbo` token or the canonical `bbo_quarantined` token are not treated as
usable quotes for quote-derived values. The `missing_bbo_flag` feature is
derived from `missing_bbo`. The `bad_quote_flag` feature is derived only from
the `missing_bbo` and `bbo_quarantined` tokens; there is no assumed input column
named `bad_quote_flag`.

Quarantined or missing rows can still produce explicit flag features, but they
do not contribute to spread, spread bps, spread z-score, microprice, imbalance,
wide-spread, or low-depth calculations. Rolling BBO features propagate a gap
when a trailing causal window contains a missing or quarantined quote.

## Microprice And Depth

Microprice and top-book imbalance require valid positive bid and ask sizes.
Rows with zero or invalid size denominators produce `None` with quality flags.
Top-book depth itself is the current bid size plus ask size for an otherwise
valid BBO row and is not forward-filled.

## Causality

Feature rows are calculated in `available_ts` order. A feature value at time `t`
may use only source rows whose `available_ts <= t`. Centered and future windows
are rejected for live BBO definitions. The family does not expose
offline-looking variants.

## Configuration

`configs/features/families/bbo/README.md` is a placeholder for future
declarative feature-set selections. FLF-P09 does not add materialization config,
registry config, provider config, or execution behavior.
