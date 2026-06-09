# FUTSUB-P15 Feature-Family Coverage Matrix

Value-free coverage and quality matrix for
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` / `FUTSUB-P15`.

This report contains registry ids, status codes, counts, rates, and metadata
only. It contains no raw rows, canonical values, feature values, provider
responses, local SQLite content, Parquet payloads, profitability language,
tradability claims, paper/live/broker/order language, or production claims.

## Inputs

- Feature registry read path: `alpha feature list --alpha-data-root
  $ALPHA_DATA_ROOT --json`, backed by the local `FeatureRegistry`.
- Registry-backed report path: `alpha feature report --kind both` for a
  representative registered feature, and registry-backed value-store handles
  for aggregate null/flag counts.
- Dataset warning/blocking states: `alpha registry dataset-acceptance inventory
  --registry-path $ALPHA_DATA_ROOT/registry/datasets.sqlite --config
  configs/data/dataset_acceptance/futsub_p02_policy.json --json` plus
  `research/futures_substrate_scaleout_v1/dataset_acceptance/acceptance_summary.md`.
- Expected 2018 exclusion evidence:
  `research/futures_substrate_scaleout_v1/dataset_acceptance/2018_BLOCKED_DIAGNOSIS.md`.
- Family scope configs: `configs/features/scaleout/*.json`.

## Legend

| Code | Meaning | Gap class |
| --- | --- | --- |
| `P` | Present: required family cell has registered FeatureVersions and registry-backed value rows for the cell. | none |
| `W` | Present with warnings: same as `P`, but at least one required input DatasetVersion is `ACCEPTED_WITH_WARNINGS` (2019 warning metadata or 2026 partial-year warning). | none |
| `EE` | Expected-excluded: required input DatasetVersion is `BLOCKED`; no feature cell is expected. | expected |
| `UG` | Unexpected gap: required input DatasetVersion is accepted/warned but no registered feature cell resolves. | unexpected |

## Cell Counts

Scope is 8 families x 3 symbols x 9 years = 216 matrix cells.

| Status | Cells |
| --- | ---: |
| `P` | 144 |
| `W` | 48 |
| `EE` | 24 |
| `UG` | 0 |

Present and warned cells together cover all accepted / accepted-with-warnings
2019-2026 feature-family cells. The only non-present cells are the 2018
expected exclusions. No unexpected family / symbol / year gaps were found.

## Status Matrix

| Family | Symbol | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `base_ohlcv` | `ES` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `base_ohlcv` | `NQ` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `base_ohlcv` | `RTY` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `session_calendar_maintenance` | `ES` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `session_calendar_maintenance` | `NQ` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `session_calendar_maintenance` | `RTY` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `vwap_session_auction` | `ES` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `vwap_session_auction` | `NQ` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `vwap_session_auction` | `RTY` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `regime_volatility_compression` | `ES` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `regime_volatility_compression` | `NQ` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `regime_volatility_compression` | `RTY` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `liquidity_sweep_pa_structure` | `ES` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `liquidity_sweep_pa_structure` | `NQ` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `liquidity_sweep_pa_structure` | `RTY` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `volume_activity` | `ES` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `volume_activity` | `NQ` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `volume_activity` | `RTY` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `bbo_tradability_top_book` | `ES` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `bbo_tradability_top_book` | `NQ` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `bbo_tradability_top_book` | `RTY` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cross_market_alignment` | `ES` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cross_market_alignment` | `NQ` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cross_market_alignment` | `RTY` | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |

`cross_market_alignment` is registered as one shared `ES_NQ_RTY_<year>`
aligned-panel partition per year. The three symbol rows above are backed by the
same shared panel for each year; they are not independent per-symbol Parquet
files.

## Registered FeatureVersions Per Present Cell

The FeaturePack configs use governed labels, and some labels bind to existing
primitive FeatureVersions. The counts below are the actual registered
FeatureVersions per present family cell in the local feature registry.

| Family | Required schemas | Registered FeatureVersions per present cell | Present/warned cells |
| --- | --- | ---: | ---: |
| `base_ohlcv` | `ohlcv_1m` | 6 | 24 |
| `session_calendar_maintenance` | `ohlcv_1m`, `ohlcv_dense_research_grid` | 10 | 24 |
| `vwap_session_auction` | `ohlcv_1m` | 6 | 24 |
| `regime_volatility_compression` | `ohlcv_1m` | 5 | 24 |
| `liquidity_sweep_pa_structure` | `ohlcv_1m` | 9 | 24 |
| `volume_activity` | `ohlcv_1m` | 8 | 24 |
| `bbo_tradability_top_book` | `bbo_1m` | 11 | 24 |
| `cross_market_alignment` | `ohlcv_1m`, `ohlcv_dense_research_grid` | 11 shared-panel versions | 24 symbol-rendered cells / 8 shared panels |

All present/warned cells have the expected registered FeatureVersion count for
their family. No accepted/warned cell had a zero or partial registry count.

## Registered Row Counts By Cell

Counts are registry `value_record_count` values. For present cells, every
FeatureVersion in the family cell shares the same row count unless otherwise
noted; no present cell had a mismatched min/max within its family cell.
Coverage fraction versus the registry-resolved feature grid is therefore
`1.000` for every `P` or `W` cell below. `EE` cells have no expected feature
row count.

| Family | Symbol | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_ohlcv` | `ES` | `EE` | 349532 | 349608 | 353363 | 354119 | 353153 | 346858 | 344561 | 140639 |
| `base_ohlcv` | `NQ` | `EE` | 349845 | 348929 | 353393 | 354112 | 353358 | 346992 | 344529 | 140610 |
| `base_ohlcv` | `RTY` | `EE` | 328841 | 338085 | 339895 | 345162 | 342436 | 333540 | 333557 | 138593 |
| `session_calendar_maintenance` | `ES` | `EE` | 356040 | 357300 | 357420 | 356040 | 356040 | 347085 | 345705 | 140640 |
| `session_calendar_maintenance` | `NQ` | `EE` | 356040 | 357300 | 357420 | 356040 | 356040 | 347085 | 345703 | 140640 |
| `session_calendar_maintenance` | `RTY` | `EE` | 356040 | 357300 | 357420 | 356033 | 356040 | 347084 | 345700 | 140640 |
| `vwap_session_auction` | `ES` | `EE` | 349532 | 349608 | 353363 | 354119 | 353153 | 346858 | 344561 | 140639 |
| `vwap_session_auction` | `NQ` | `EE` | 349845 | 348929 | 353393 | 354112 | 353358 | 346992 | 344529 | 140610 |
| `vwap_session_auction` | `RTY` | `EE` | 328841 | 338085 | 339895 | 345162 | 342436 | 333540 | 333557 | 138593 |
| `regime_volatility_compression` | `ES` | `EE` | 349532 | 349608 | 353363 | 354119 | 353153 | 346858 | 344561 | 140639 |
| `regime_volatility_compression` | `NQ` | `EE` | 349845 | 348929 | 353393 | 354112 | 353358 | 346992 | 344529 | 140610 |
| `regime_volatility_compression` | `RTY` | `EE` | 328841 | 338085 | 339895 | 345162 | 342436 | 333540 | 333557 | 138593 |
| `liquidity_sweep_pa_structure` | `ES` | `EE` | 349532 | 349608 | 353363 | 354119 | 353153 | 346858 | 344561 | 140639 |
| `liquidity_sweep_pa_structure` | `NQ` | `EE` | 349845 | 348929 | 353393 | 354112 | 353358 | 346992 | 344529 | 140610 |
| `liquidity_sweep_pa_structure` | `RTY` | `EE` | 328841 | 338085 | 339895 | 345162 | 342436 | 333540 | 333557 | 138593 |
| `volume_activity` | `ES` | `EE` | 349532 | 349608 | 353363 | 354119 | 353153 | 346858 | 344561 | 140639 |
| `volume_activity` | `NQ` | `EE` | 349845 | 348929 | 353393 | 354112 | 353358 | 346992 | 344529 | 140610 |
| `volume_activity` | `RTY` | `EE` | 328841 | 338085 | 339895 | 345162 | 342436 | 333540 | 333557 | 138593 |
| `bbo_tradability_top_book` | `ES` | `EE` | 349532 | 349608 | 353363 | 354119 | 353153 | 346858 | 344561 | 140639 |
| `bbo_tradability_top_book` | `NQ` | `EE` | 349845 | 348929 | 353393 | 354112 | 353358 | 346992 | 344529 | 140610 |
| `bbo_tradability_top_book` | `RTY` | `EE` | 328841 | 338085 | 339895 | 345162 | 342436 | 333540 | 333557 | 138593 |
| `cross_market_alignment` | `ES` | `EE` | 356040 | 357300 | 357420 | 356033 | 356040 | 347084 | 345700 | 140640 |
| `cross_market_alignment` | `NQ` | `EE` | 356040 | 357300 | 357420 | 356033 | 356040 | 347084 | 345700 | 140640 |
| `cross_market_alignment` | `RTY` | `EE` | 356040 | 357300 | 357420 | 356033 | 356040 | 347084 | 345700 | 140640 |

## Quality / Missingness Summary

Aggregate rates below were computed from registry-backed value-store handles.
They are summary statistics only. Nonzero null-like and quality-flag rates are
recorded as value gaps or surfaced quality flags, not as silent coverage.

| Family | Present/warned cells | Max null-like rate | Max quality-flag rate | Max missing `available_ts` rate |
| --- | ---: | ---: | ---: | ---: |
| `base_ohlcv` | 24 | 0.000582 | 0.000582 | 0.000000 |
| `session_calendar_maintenance` | 24 | 0.600000 | 0.630557 | 0.000000 |
| `vwap_session_auction` | 24 | 0.166667 | 0.166667 | 0.000000 |
| `regime_volatility_compression` | 24 | 0.029328 | 0.029328 | 0.000000 |
| `liquidity_sweep_pa_structure` | 24 | 0.050285 | 0.050285 | 0.000000 |
| `volume_activity` | 24 | 0.036638 | 0.036638 | 0.000000 |
| `bbo_tradability_top_book` | 24 | 0.168652 | 0.168653 | 0.000000 |
| `cross_market_alignment` | 24 | 0.148649 | 0.148649 | 0.000000 |

The high session/calendar null-like rate is expected quality context for fields
that can be undefined before roll, expiration, or halt metadata is available.
Downstream consumers must treat surfaced gaps and flags as data-quality context;
they must not infer complete values from a registered cell alone.

## BBO Flag Rates

Rates are per BBO family cell and count the flag feature value equal to `1`
divided by the registered row count for that flag FeatureVersion.

| Symbol | Year | Rows | Missing BBO | Bad Quote | Wide Spread | Low Depth |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `ES` | 2019 | 349532 | 0.000009 | 0.000009 | 0.000000 | 0.000000 |
| `ES` | 2020 | 349608 | 0.001413 | 0.001413 | 0.000006 | 0.000000 |
| `ES` | 2021 | 353363 | 0.000003 | 0.000003 | 0.000000 | 0.000000 |
| `ES` | 2022 | 354119 | 0.000008 | 0.000008 | 0.000003 | 0.000000 |
| `ES` | 2023 | 353153 | 0.000263 | 0.000263 | 0.000000 | 0.000000 |
| `ES` | 2024 | 346858 | 0.000003 | 0.000003 | 0.000000 | 0.000000 |
| `ES` | 2025 | 344561 | 0.000012 | 0.000012 | 0.000000 | 0.000000 |
| `ES` | 2026 | 140639 | 0.000007 | 0.000007 | 0.000000 | 0.000000 |
| `NQ` | 2019 | 349845 | 0.000006 | 0.000006 | 0.000000 | 0.000000 |
| `NQ` | 2020 | 348929 | 0.001161 | 0.001161 | 0.000020 | 0.000000 |
| `NQ` | 2021 | 353393 | 0.000008 | 0.000008 | 0.000000 | 0.000000 |
| `NQ` | 2022 | 354112 | 0.000008 | 0.000008 | 0.000003 | 0.000000 |
| `NQ` | 2023 | 353358 | 0.000260 | 0.000260 | 0.000000 | 0.000000 |
| `NQ` | 2024 | 346992 | 0.000003 | 0.000003 | 0.000000 | 0.000000 |
| `NQ` | 2025 | 344529 | 0.000029 | 0.000029 | 0.000000 | 0.000000 |
| `NQ` | 2026 | 140610 | 0.000007 | 0.000007 | 0.000000 | 0.000000 |
| `RTY` | 2019 | 328841 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| `RTY` | 2020 | 338085 | 0.000524 | 0.000524 | 0.001248 | 0.000000 |
| `RTY` | 2021 | 339895 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| `RTY` | 2022 | 345162 | 0.000012 | 0.000012 | 0.000000 | 0.000000 |
| `RTY` | 2023 | 342436 | 0.000120 | 0.000120 | 0.000000 | 0.000000 |
| `RTY` | 2024 | 333540 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| `RTY` | 2025 | 333557 | 0.000012 | 0.000012 | 0.000009 | 0.000000 |
| `RTY` | 2026 | 138593 | 0.000007 | 0.000007 | 0.000000 | 0.000000 |

## Explicit Gap List

### Expected Exclusions

The 2018 cells are expected exclusions for all eight families and all three
symbols because the required `ohlcv_1m` and `bbo_1m` 2018 DatasetVersions are
`BLOCKED`. The root blocking dimension is the RTY 2018 sparse-history coverage
gap recorded in `2018_BLOCKED_DIAGNOSIS.md`; this campaign uses dataset-level
fallback for the feature materialization window, so ES/NQ 2018 feature cells are
also excluded rather than fabricating per-symbol acceptance.

Expected-excluded cell count: 24.

### Unexpected Gaps

None. Every non-2018 required family / symbol / year cell resolves to registered
FeatureVersions with value rows through the local feature registry.

## Downstream Consumption

- Label materialization phases must treat this matrix as the feature substrate
  availability map for 2019-2026 and must keep 2018 excluded unless a later
  owner changes the dataset acceptance lock.
- 2019 and 2026 cells are usable only with their warning context preserved:
  2019 carries accepted-with-warnings history metadata, and 2026 is partial
  year.
- A registered family cell is not a claim that all feature values are non-null.
  The null-like and flag rates above are the value-free quality context that
  downstream phases must carry forward.
- This matrix does not create or imply any profitability, tradability, paper,
  live, broker, order-routing, production, or capital-allocation claim.
