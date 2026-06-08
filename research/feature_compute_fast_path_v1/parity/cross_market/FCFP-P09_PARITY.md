# FCFP-P09 Cross-Market Parity Note

This value-free note summarizes the synthetic parity gate for the V1
Cross-Market aligned-panel pack. It does not contain feature values, market data,
provider responses, registry state, or materialized artifacts.

## Scope

- Pack: `alpha_system.features.fast.cross_market_panel`
- Reference oracle: `alpha_system.features.families.cross_market.family`
- Features: all 11 governed Cross-Market features for ES/NQ/RTY
- Alignment covered: `strict_intersection` primary parity gate, plus an `asof`
  policy regression on the same synthetic frame
- Entity id: `ES:NQ:RTY`

## Fixture Coverage

The tiny synthetic fixture covers:

- exact ES/NQ/RTY same-event intersection
- one missing RTY event that must not produce a fast record
- delayed NQ availability where output `available_ts` is the max contributing
  timestamp
- leading missing-history / insufficient-window rows
- ES no-trade return gaps and post-gap propagation
- reset-on-session return gaps at an RTH to ETH boundary
- optional exact-time missing BBO flags with no quote forward-fill
- rolling `zero_benchmark_variance` and `zero_target_variance` branches
- feature-version identity equality with the reference `FeatureSpec`

## Tolerance

Point features are exact on the fixture. Rolling beta-residual and rolling
correlation features use absolute/relative tolerance `1e-12`, justified by
equivalent floating-point covariance, variance, residual, and correlation
reductions in Polars versus the Python reference path.

## Artifact Boundary

The parity test writes temporary JSONL/Parquet value-store outputs only under
pytest temporary directories. No feature values, Parquet files, SQLite files,
raw/canonical data, provider responses, or run-local artifacts are
commit-eligible.
