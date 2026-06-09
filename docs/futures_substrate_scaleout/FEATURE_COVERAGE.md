# Feature Coverage

`FUTSUB-P15` records the value-free feature-family coverage matrix for
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`.

The machine-reviewable matrix lives at
`research/futures_substrate_scaleout_v1/matrices/feature_family_coverage.md`.
It covers all eight governed FeaturePack families across ES, NQ, RTY, and
2018-2026. It records status, registered row counts, quality/missingness
summary rates, BBO flag rates, and explicit gaps without committing feature
values or local registry files.

## Coverage Result

Scope: 8 families x 3 symbols x 9 years = 216 cells.

| Cell class | Count | Meaning |
| --- | ---: | --- |
| Present clean | 144 | 2020-2025 cells with accepted required DatasetVersions. |
| Present warned | 48 | 2019 and 2026 cells with accepted-with-warnings input metadata. |
| Expected-excluded | 24 | 2018 cells blocked by required `ohlcv_1m` / `bbo_1m` DatasetVersion state. |
| Unexpected gap | 0 | No accepted/warned feature-family cell was missing from the registry. |

The feature integration gate is coverage-mapped: all accepted/warned 2019-2026
family / symbol / year cells resolve to registered FeatureVersions with value
rows. Coverage is not inferred from a subset; every 2018 non-present cell is
listed as an expected exclusion, and there are no unexpected gaps.

## Quality Context

All committed quality evidence is summary metadata only.

- Registered row counts range from 138,593 to 357,420 across present/warned
  cells, depending on year, symbol, and dense-grid requirements.
- Every present/warned cell has complete family registry membership for its
  actual registered FeatureVersion set.
- `available_ts` missing rate is 0.000000 in the aggregate pass across all
  present/warned family cells.
- Null-like and quality-flag rates are explicitly recorded in the matrix. They
  are surfaced value gaps or quality flags, not silent coverage.
- BBO flag rates are recorded per symbol/year for missing-BBO, bad-quote,
  wide-spread, and low-depth flags. They remain value-free summary statistics.

## Expected Exclusions

2018 remains excluded for all eight families and all three symbols. The
underlying blocked locks are:

- `ohlcv_1m` 2018: `BLOCKED`
- `bbo_1m` 2018: `BLOCKED`

The documented root cause is the RTY 2018 sparse-history coverage gap. The
feature materialization window uses dataset-level fallback, so ES/NQ 2018
feature cells are not fabricated from per-symbol acceptance.

## Downstream Contract

- `FUTSUB-P16` and later label materialization phases should consume the
  2019-2026 feature substrate and preserve 2019 / 2026 warning context.
- Label and Core Pilot rerun phases must not treat 2018 as available unless a
  later dataset-acceptance owner changes the accepted window.
- A registered feature-family cell is a coverage fact, not a claim that every
  per-row feature value is non-null.
- This page makes no profitability, tradability, paper/live/broker/order,
  production, deployment, or capital-allocation claim.
