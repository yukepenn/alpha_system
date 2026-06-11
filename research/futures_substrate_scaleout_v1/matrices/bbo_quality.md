# FUTSUB-P26 BBO Quality Matrix

Value-free BBO quality matrix for `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` / `FUTSUB-P26`.

BBO-1m is a time-sampled + forward-filled tradability proxy. Nothing in this matrix is a passive-fill, queue-priority, intra-minute-impact, or execution-truth claim.

## Method

- Registry input: `PYTHONPATH=src alpha feature list --alpha-data-root $ALPHA_DATA_ROOT --json` to enumerate current registered FeatureVersions; aggregation resolved the same records through the CLI registry helper `_feature_records(...)` in read-only mode.
- Value input: registered Parquet-backed value handles for the P12 `bbo_tradability_top_book` FeaturePack; rows were filtered by exact `feature_version_id` before aggregation.
- Session input: registered P07 `session_calendar_maintenance` ETH/RTH/halt flags joined by `available_ts`. BBO quote `event_ts` is the sampled quote timestamp; `available_ts` is the minute-grid availability timestamp shared with session metadata.
- Spread bucket input: `bbo_tradability_spread`. The materialized `bbo_tradability_spread_ticks` field is recorded separately as a coverage field because it resolved all-null in this local substrate pass.

## Session-Segment Coverage Note

The materialized session flags resolved every accepted BBO row into `ETH_NON_RTH`: `eth_segment_flag=1`, `rth_segment_flag=0`, and `halt_status_flag=null` for the checked cells. This matrix does not rederive RTH, maintenance-adjacent, or other clock buckets from timestamps. Downstream consumers should treat the collapsed session split as diagnostics gating context and route any need for a finer session segmentation to the session substrate owner.

## Session Quality Matrix

| Symbol | Year | Session | Rows | Missing BBO | Bad Quote | Wide Spread | Low Depth | Top-book Available | Spread-ticks Available |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ES` | 2019 | `ETH_NON_RTH` | 349532 | 0.000009 | 0.000009 | 0.000000 | 0.000000 | 0.999991 | 0.000000 |
| `ES` | 2020 | `ETH_NON_RTH` | 349608 | 0.001413 | 0.001413 | 0.000006 | 0.000000 | 0.998587 | 0.000000 |
| `ES` | 2021 | `ETH_NON_RTH` | 353363 | 0.000003 | 0.000003 | 0.000000 | 0.000000 | 0.999997 | 0.000000 |
| `ES` | 2022 | `ETH_NON_RTH` | 354119 | 0.000008 | 0.000008 | 0.000003 | 0.000000 | 0.999992 | 0.000000 |
| `ES` | 2023 | `ETH_NON_RTH` | 353153 | 0.000263 | 0.000263 | 0.000000 | 0.000000 | 0.999737 | 0.000000 |
| `ES` | 2024 | `ETH_NON_RTH` | 346858 | 0.000003 | 0.000003 | 0.000000 | 0.000000 | 0.999997 | 0.000000 |
| `ES` | 2025 | `ETH_NON_RTH` | 344561 | 0.000012 | 0.000012 | 0.000000 | 0.000000 | 0.999988 | 0.000000 |
| `ES` | 2026 | `ETH_NON_RTH` | 140639 | 0.000007 | 0.000007 | 0.000000 | 0.000000 | 0.999993 | 0.000000 |
| `NQ` | 2019 | `ETH_NON_RTH` | 349845 | 0.000006 | 0.000006 | 0.000000 | 0.000000 | 0.999994 | 0.000000 |
| `NQ` | 2020 | `ETH_NON_RTH` | 348929 | 0.001161 | 0.001161 | 0.000020 | 0.000000 | 0.998839 | 0.000000 |
| `NQ` | 2021 | `ETH_NON_RTH` | 353393 | 0.000008 | 0.000008 | 0.000000 | 0.000000 | 0.999992 | 0.000000 |
| `NQ` | 2022 | `ETH_NON_RTH` | 354112 | 0.000008 | 0.000008 | 0.000003 | 0.000000 | 0.999992 | 0.000000 |
| `NQ` | 2023 | `ETH_NON_RTH` | 353358 | 0.000260 | 0.000260 | 0.000000 | 0.000000 | 0.999740 | 0.000000 |
| `NQ` | 2024 | `ETH_NON_RTH` | 346992 | 0.000003 | 0.000003 | 0.000000 | 0.000000 | 0.999997 | 0.000000 |
| `NQ` | 2025 | `ETH_NON_RTH` | 344529 | 0.000029 | 0.000029 | 0.000000 | 0.000000 | 0.999971 | 0.000000 |
| `NQ` | 2026 | `ETH_NON_RTH` | 140610 | 0.000007 | 0.000007 | 0.000000 | 0.000000 | 0.999993 | 0.000000 |
| `RTY` | 2019 | `ETH_NON_RTH` | 328841 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0.000000 |
| `RTY` | 2020 | `ETH_NON_RTH` | 338085 | 0.000524 | 0.000524 | 0.001248 | 0.000000 | 0.999476 | 0.000000 |
| `RTY` | 2021 | `ETH_NON_RTH` | 339895 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0.000000 |
| `RTY` | 2022 | `ETH_NON_RTH` | 345162 | 0.000012 | 0.000012 | 0.000000 | 0.000000 | 0.999988 | 0.000000 |
| `RTY` | 2023 | `ETH_NON_RTH` | 342436 | 0.000120 | 0.000120 | 0.000000 | 0.000000 | 0.999880 | 0.000000 |
| `RTY` | 2024 | `ETH_NON_RTH` | 333540 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0.000000 |
| `RTY` | 2025 | `ETH_NON_RTH` | 333557 | 0.000012 | 0.000012 | 0.000009 | 0.000000 | 0.999988 | 0.000000 |
| `RTY` | 2026 | `ETH_NON_RTH` | 138593 | 0.000007 | 0.000007 | 0.000000 | 0.000000 | 0.999993 | 0.000000 |

## Spread Bucket Occupancy

Shares are per symbol-year; each row is one session x spread bucket cell.

| Symbol | Year | Session | Spread bucket | Rows | Share of symbol-year |
| --- | --- | --- | --- | --- | --- |
| `ES` | 2019 | `ETH_NON_RTH` | `spread_0.25_0.50` | 3337 | 0.009547 |
| `ES` | 2019 | `ETH_NON_RTH` | `spread_0.50_1.00` | 5 | 0.000014 |
| `ES` | 2019 | `ETH_NON_RTH` | `spread_gt_1.00` | 1 | 0.000003 |
| `ES` | 2019 | `ETH_NON_RTH` | `spread_le_0.25` | 346186 | 0.990427 |
| `ES` | 2019 | `ETH_NON_RTH` | `spread_null` | 3 | 0.000009 |
| `ES` | 2020 | `ETH_NON_RTH` | `spread_0.25_0.50` | 28179 | 0.080602 |
| `ES` | 2020 | `ETH_NON_RTH` | `spread_0.50_1.00` | 2628 | 0.007517 |
| `ES` | 2020 | `ETH_NON_RTH` | `spread_gt_1.00` | 281 | 0.000804 |
| `ES` | 2020 | `ETH_NON_RTH` | `spread_le_0.25` | 318026 | 0.909665 |
| `ES` | 2020 | `ETH_NON_RTH` | `spread_null` | 494 | 0.001413 |
| `ES` | 2021 | `ETH_NON_RTH` | `spread_0.25_0.50` | 14952 | 0.042313 |
| `ES` | 2021 | `ETH_NON_RTH` | `spread_0.50_1.00` | 24 | 0.000068 |
| `ES` | 2021 | `ETH_NON_RTH` | `spread_gt_1.00` | 4 | 0.000011 |
| `ES` | 2021 | `ETH_NON_RTH` | `spread_le_0.25` | 338382 | 0.957605 |
| `ES` | 2021 | `ETH_NON_RTH` | `spread_null` | 1 | 0.000003 |
| `ES` | 2022 | `ETH_NON_RTH` | `spread_0.25_0.50` | 43575 | 0.123052 |
| `ES` | 2022 | `ETH_NON_RTH` | `spread_0.50_1.00` | 107 | 0.000302 |
| `ES` | 2022 | `ETH_NON_RTH` | `spread_gt_1.00` | 12 | 0.000034 |
| `ES` | 2022 | `ETH_NON_RTH` | `spread_le_0.25` | 310422 | 0.876604 |
| `ES` | 2022 | `ETH_NON_RTH` | `spread_null` | 3 | 0.000008 |
| `ES` | 2023 | `ETH_NON_RTH` | `spread_0.25_0.50` | 11509 | 0.032589 |
| `ES` | 2023 | `ETH_NON_RTH` | `spread_0.50_1.00` | 36 | 0.000102 |
| `ES` | 2023 | `ETH_NON_RTH` | `spread_gt_1.00` | 8 | 0.000023 |
| `ES` | 2023 | `ETH_NON_RTH` | `spread_le_0.25` | 341507 | 0.967023 |
| `ES` | 2023 | `ETH_NON_RTH` | `spread_null` | 93 | 0.000263 |
| `ES` | 2024 | `ETH_NON_RTH` | `spread_0.25_0.50` | 18311 | 0.052791 |
| `ES` | 2024 | `ETH_NON_RTH` | `spread_0.50_1.00` | 91 | 0.000262 |
| `ES` | 2024 | `ETH_NON_RTH` | `spread_gt_1.00` | 14 | 0.000040 |
| `ES` | 2024 | `ETH_NON_RTH` | `spread_le_0.25` | 328441 | 0.946903 |
| `ES` | 2024 | `ETH_NON_RTH` | `spread_null` | 1 | 0.000003 |
| `ES` | 2025 | `ETH_NON_RTH` | `spread_0.25_0.50` | 38633 | 0.112122 |
| `ES` | 2025 | `ETH_NON_RTH` | `spread_0.50_1.00` | 1111 | 0.003224 |
| `ES` | 2025 | `ETH_NON_RTH` | `spread_gt_1.00` | 81 | 0.000235 |
| `ES` | 2025 | `ETH_NON_RTH` | `spread_le_0.25` | 304732 | 0.884407 |
| `ES` | 2025 | `ETH_NON_RTH` | `spread_null` | 4 | 0.000012 |
| `ES` | 2026 | `ETH_NON_RTH` | `spread_0.25_0.50` | 19544 | 0.138966 |
| `ES` | 2026 | `ETH_NON_RTH` | `spread_0.50_1.00` | 79 | 0.000562 |
| `ES` | 2026 | `ETH_NON_RTH` | `spread_gt_1.00` | 15 | 0.000107 |
| `ES` | 2026 | `ETH_NON_RTH` | `spread_le_0.25` | 121000 | 0.860359 |
| `ES` | 2026 | `ETH_NON_RTH` | `spread_null` | 1 | 0.000007 |
| `NQ` | 2019 | `ETH_NON_RTH` | `spread_0.25_0.50` | 148578 | 0.424697 |
| `NQ` | 2019 | `ETH_NON_RTH` | `spread_0.50_1.00` | 7106 | 0.020312 |
| `NQ` | 2019 | `ETH_NON_RTH` | `spread_gt_1.00` | 508 | 0.001452 |
| `NQ` | 2019 | `ETH_NON_RTH` | `spread_le_0.25` | 193651 | 0.553534 |
| `NQ` | 2019 | `ETH_NON_RTH` | `spread_null` | 2 | 0.000006 |
| `NQ` | 2020 | `ETH_NON_RTH` | `spread_0.25_0.50` | 124832 | 0.357758 |
| `NQ` | 2020 | `ETH_NON_RTH` | `spread_0.50_1.00` | 120059 | 0.344079 |
| `NQ` | 2020 | `ETH_NON_RTH` | `spread_gt_1.00` | 53699 | 0.153897 |
| `NQ` | 2020 | `ETH_NON_RTH` | `spread_le_0.25` | 49934 | 0.143106 |
| `NQ` | 2020 | `ETH_NON_RTH` | `spread_null` | 405 | 0.001161 |
| `NQ` | 2021 | `ETH_NON_RTH` | `spread_0.25_0.50` | 167550 | 0.474118 |
| `NQ` | 2021 | `ETH_NON_RTH` | `spread_0.50_1.00` | 137142 | 0.388072 |
| `NQ` | 2021 | `ETH_NON_RTH` | `spread_gt_1.00` | 14059 | 0.039783 |
| `NQ` | 2021 | `ETH_NON_RTH` | `spread_le_0.25` | 34639 | 0.098018 |
| `NQ` | 2021 | `ETH_NON_RTH` | `spread_null` | 3 | 0.000008 |
| `NQ` | 2022 | `ETH_NON_RTH` | `spread_0.25_0.50` | 95324 | 0.269192 |
| `NQ` | 2022 | `ETH_NON_RTH` | `spread_0.50_1.00` | 213774 | 0.603690 |
| `NQ` | 2022 | `ETH_NON_RTH` | `spread_gt_1.00` | 36314 | 0.102549 |
| `NQ` | 2022 | `ETH_NON_RTH` | `spread_le_0.25` | 8697 | 0.024560 |
| `NQ` | 2022 | `ETH_NON_RTH` | `spread_null` | 3 | 0.000008 |
| `NQ` | 2023 | `ETH_NON_RTH` | `spread_0.25_0.50` | 212516 | 0.601418 |
| `NQ` | 2023 | `ETH_NON_RTH` | `spread_0.50_1.00` | 99052 | 0.280316 |
| `NQ` | 2023 | `ETH_NON_RTH` | `spread_gt_1.00` | 3250 | 0.009197 |
| `NQ` | 2023 | `ETH_NON_RTH` | `spread_le_0.25` | 38448 | 0.108807 |
| `NQ` | 2023 | `ETH_NON_RTH` | `spread_null` | 92 | 0.000260 |
| `NQ` | 2024 | `ETH_NON_RTH` | `spread_0.25_0.50` | 162494 | 0.468293 |
| `NQ` | 2024 | `ETH_NON_RTH` | `spread_0.50_1.00` | 142108 | 0.409543 |
| `NQ` | 2024 | `ETH_NON_RTH` | `spread_gt_1.00` | 21777 | 0.062759 |
| `NQ` | 2024 | `ETH_NON_RTH` | `spread_le_0.25` | 20612 | 0.059402 |
| `NQ` | 2024 | `ETH_NON_RTH` | `spread_null` | 1 | 0.000003 |
| `NQ` | 2025 | `ETH_NON_RTH` | `spread_0.25_0.50` | 99411 | 0.288542 |
| `NQ` | 2025 | `ETH_NON_RTH` | `spread_0.50_1.00` | 198504 | 0.576160 |
| `NQ` | 2025 | `ETH_NON_RTH` | `spread_gt_1.00` | 39736 | 0.115334 |
| `NQ` | 2025 | `ETH_NON_RTH` | `spread_le_0.25` | 6868 | 0.019934 |
| `NQ` | 2025 | `ETH_NON_RTH` | `spread_null` | 10 | 0.000029 |
| `NQ` | 2026 | `ETH_NON_RTH` | `spread_0.25_0.50` | 24887 | 0.176993 |
| `NQ` | 2026 | `ETH_NON_RTH` | `spread_0.50_1.00` | 89059 | 0.633376 |
| `NQ` | 2026 | `ETH_NON_RTH` | `spread_gt_1.00` | 25281 | 0.179795 |
| `NQ` | 2026 | `ETH_NON_RTH` | `spread_le_0.25` | 1382 | 0.009829 |
| `NQ` | 2026 | `ETH_NON_RTH` | `spread_null` | 1 | 0.000007 |
| `RTY` | 2019 | `ETH_NON_RTH` | `spread_0.25_0.50` | 8136 | 0.024741 |
| `RTY` | 2019 | `ETH_NON_RTH` | `spread_0.50_1.00` | 163 | 0.000496 |
| `RTY` | 2019 | `ETH_NON_RTH` | `spread_gt_1.00` | 8 | 0.000024 |
| `RTY` | 2019 | `ETH_NON_RTH` | `spread_le_0.25` | 320534 | 0.974739 |
| `RTY` | 2020 | `ETH_NON_RTH` | `spread_0.25_0.50` | 128856 | 0.381135 |
| `RTY` | 2020 | `ETH_NON_RTH` | `spread_0.50_1.00` | 12716 | 0.037612 |
| `RTY` | 2020 | `ETH_NON_RTH` | `spread_gt_1.00` | 1715 | 0.005073 |
| `RTY` | 2020 | `ETH_NON_RTH` | `spread_le_0.25` | 194621 | 0.575657 |
| `RTY` | 2020 | `ETH_NON_RTH` | `spread_null` | 177 | 0.000524 |
| `RTY` | 2021 | `ETH_NON_RTH` | `spread_0.25_0.50` | 148820 | 0.437841 |
| `RTY` | 2021 | `ETH_NON_RTH` | `spread_0.50_1.00` | 12684 | 0.037317 |
| `RTY` | 2021 | `ETH_NON_RTH` | `spread_gt_1.00` | 289 | 0.000850 |
| `RTY` | 2021 | `ETH_NON_RTH` | `spread_le_0.25` | 178102 | 0.523991 |
| `RTY` | 2022 | `ETH_NON_RTH` | `spread_0.25_0.50` | 101433 | 0.293871 |
| `RTY` | 2022 | `ETH_NON_RTH` | `spread_0.50_1.00` | 1985 | 0.005751 |
| `RTY` | 2022 | `ETH_NON_RTH` | `spread_gt_1.00` | 17 | 0.000049 |
| `RTY` | 2022 | `ETH_NON_RTH` | `spread_le_0.25` | 241723 | 0.700318 |
| `RTY` | 2022 | `ETH_NON_RTH` | `spread_null` | 4 | 0.000012 |
| `RTY` | 2023 | `ETH_NON_RTH` | `spread_0.25_0.50` | 13808 | 0.040323 |
| `RTY` | 2023 | `ETH_NON_RTH` | `spread_0.50_1.00` | 326 | 0.000952 |
| `RTY` | 2023 | `ETH_NON_RTH` | `spread_gt_1.00` | 25 | 0.000073 |
| `RTY` | 2023 | `ETH_NON_RTH` | `spread_le_0.25` | 328236 | 0.958532 |
| `RTY` | 2023 | `ETH_NON_RTH` | `spread_null` | 41 | 0.000120 |
| `RTY` | 2024 | `ETH_NON_RTH` | `spread_0.25_0.50` | 93474 | 0.280248 |
| `RTY` | 2024 | `ETH_NON_RTH` | `spread_0.50_1.00` | 1326 | 0.003976 |
| `RTY` | 2024 | `ETH_NON_RTH` | `spread_gt_1.00` | 60 | 0.000180 |
| `RTY` | 2024 | `ETH_NON_RTH` | `spread_le_0.25` | 238680 | 0.715596 |
| `RTY` | 2025 | `ETH_NON_RTH` | `spread_0.25_0.50` | 83202 | 0.249439 |
| `RTY` | 2025 | `ETH_NON_RTH` | `spread_0.50_1.00` | 3367 | 0.010094 |
| `RTY` | 2025 | `ETH_NON_RTH` | `spread_gt_1.00` | 331 | 0.000992 |
| `RTY` | 2025 | `ETH_NON_RTH` | `spread_le_0.25` | 246653 | 0.739463 |
| `RTY` | 2025 | `ETH_NON_RTH` | `spread_null` | 4 | 0.000012 |
| `RTY` | 2026 | `ETH_NON_RTH` | `spread_0.25_0.50` | 44450 | 0.320723 |
| `RTY` | 2026 | `ETH_NON_RTH` | `spread_0.50_1.00` | 1234 | 0.008904 |
| `RTY` | 2026 | `ETH_NON_RTH` | `spread_gt_1.00` | 121 | 0.000873 |
| `RTY` | 2026 | `ETH_NON_RTH` | `spread_le_0.25` | 92787 | 0.669493 |
| `RTY` | 2026 | `ETH_NON_RTH` | `spread_null` | 1 | 0.000007 |

## Quality-Regime Cells

Nonzero cells across the missingness, bad-quote, wide-spread, top-book availability, and low-depth dimensions.

| Symbol | Year | Session | Missing | Bad | Wide | Top-book avail | Low depth | Rows | Share of symbol-year |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ES` | 2019 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 349529 | 0.999991 |
| `ES` | 2019 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 3 | 0.000009 |
| `ES` | 2020 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 349112 | 0.998581 |
| `ES` | 2020 | `ETH_NON_RTH` | 0 | 0 | 1 | true | 0 | 2 | 0.000006 |
| `ES` | 2020 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 494 | 0.001413 |
| `ES` | 2021 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 353362 | 0.999997 |
| `ES` | 2021 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 1 | 0.000003 |
| `ES` | 2022 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 354115 | 0.999989 |
| `ES` | 2022 | `ETH_NON_RTH` | 0 | 0 | 1 | true | 0 | 1 | 0.000003 |
| `ES` | 2022 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 3 | 0.000008 |
| `ES` | 2023 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 353060 | 0.999737 |
| `ES` | 2023 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 93 | 0.000263 |
| `ES` | 2024 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 346857 | 0.999997 |
| `ES` | 2024 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 1 | 0.000003 |
| `ES` | 2025 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 344557 | 0.999988 |
| `ES` | 2025 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 4 | 0.000012 |
| `ES` | 2026 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 140638 | 0.999993 |
| `ES` | 2026 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 1 | 0.000007 |
| `NQ` | 2019 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 349843 | 0.999994 |
| `NQ` | 2019 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 2 | 0.000006 |
| `NQ` | 2020 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 348517 | 0.998819 |
| `NQ` | 2020 | `ETH_NON_RTH` | 0 | 0 | 1 | true | 0 | 7 | 0.000020 |
| `NQ` | 2020 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 405 | 0.001161 |
| `NQ` | 2021 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 353390 | 0.999992 |
| `NQ` | 2021 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 3 | 0.000008 |
| `NQ` | 2022 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 354108 | 0.999989 |
| `NQ` | 2022 | `ETH_NON_RTH` | 0 | 0 | 1 | true | 0 | 1 | 0.000003 |
| `NQ` | 2022 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 3 | 0.000008 |
| `NQ` | 2023 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 353266 | 0.999740 |
| `NQ` | 2023 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 92 | 0.000260 |
| `NQ` | 2024 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 346991 | 0.999997 |
| `NQ` | 2024 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 1 | 0.000003 |
| `NQ` | 2025 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 344519 | 0.999971 |
| `NQ` | 2025 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 10 | 0.000029 |
| `NQ` | 2026 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 140609 | 0.999993 |
| `NQ` | 2026 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 1 | 0.000007 |
| `RTY` | 2019 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 328841 | 1.000000 |
| `RTY` | 2020 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 337486 | 0.998228 |
| `RTY` | 2020 | `ETH_NON_RTH` | 0 | 0 | 1 | true | 0 | 422 | 0.001248 |
| `RTY` | 2020 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 177 | 0.000524 |
| `RTY` | 2021 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 339895 | 1.000000 |
| `RTY` | 2022 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 345158 | 0.999988 |
| `RTY` | 2022 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 4 | 0.000012 |
| `RTY` | 2023 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 342395 | 0.999880 |
| `RTY` | 2023 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 41 | 0.000120 |
| `RTY` | 2024 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 333540 | 1.000000 |
| `RTY` | 2025 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 333550 | 0.999979 |
| `RTY` | 2025 | `ETH_NON_RTH` | 0 | 0 | 1 | true | 0 | 3 | 0.000009 |
| `RTY` | 2025 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 4 | 0.000012 |
| `RTY` | 2026 | `ETH_NON_RTH` | 0 | 0 | 0 | true | 0 | 138592 | 0.999993 |
| `RTY` | 2026 | `ETH_NON_RTH` | 1 | 1 | 0 | false | 0 | 1 | 0.000007 |

## Worst-Cell Gating Context

These cells are diagnostics gating context for FUTSUB-P28 and downstream consumers. They are surfaced gaps or quality regimes, not smoothed inputs.

### `missing_bbo_rate`

| Symbol | Year | Session | Rows | Rate |
| --- | --- | --- | --- | --- |
| `ES` | 2020 | `ETH_NON_RTH` | 349608 | 0.001413 |
| `NQ` | 2020 | `ETH_NON_RTH` | 348929 | 0.001161 |
| `RTY` | 2020 | `ETH_NON_RTH` | 338085 | 0.000524 |
| `ES` | 2023 | `ETH_NON_RTH` | 353153 | 0.000263 |
| `NQ` | 2023 | `ETH_NON_RTH` | 353358 | 0.000260 |
| `RTY` | 2023 | `ETH_NON_RTH` | 342436 | 0.000120 |
| `NQ` | 2025 | `ETH_NON_RTH` | 344529 | 0.000029 |
| `RTY` | 2025 | `ETH_NON_RTH` | 333557 | 0.000012 |

### `bad_quote_rate`

| Symbol | Year | Session | Rows | Rate |
| --- | --- | --- | --- | --- |
| `ES` | 2020 | `ETH_NON_RTH` | 349608 | 0.001413 |
| `NQ` | 2020 | `ETH_NON_RTH` | 348929 | 0.001161 |
| `RTY` | 2020 | `ETH_NON_RTH` | 338085 | 0.000524 |
| `ES` | 2023 | `ETH_NON_RTH` | 353153 | 0.000263 |
| `NQ` | 2023 | `ETH_NON_RTH` | 353358 | 0.000260 |
| `RTY` | 2023 | `ETH_NON_RTH` | 342436 | 0.000120 |
| `NQ` | 2025 | `ETH_NON_RTH` | 344529 | 0.000029 |
| `RTY` | 2025 | `ETH_NON_RTH` | 333557 | 0.000012 |

### `wide_spread_rate`

| Symbol | Year | Session | Rows | Rate |
| --- | --- | --- | --- | --- |
| `RTY` | 2020 | `ETH_NON_RTH` | 338085 | 0.001248 |
| `NQ` | 2020 | `ETH_NON_RTH` | 348929 | 0.000020 |
| `RTY` | 2025 | `ETH_NON_RTH` | 333557 | 0.000009 |
| `ES` | 2020 | `ETH_NON_RTH` | 349608 | 0.000006 |
| `NQ` | 2022 | `ETH_NON_RTH` | 354112 | 0.000003 |
| `ES` | 2022 | `ETH_NON_RTH` | 354119 | 0.000003 |
| `NQ` | 2021 | `ETH_NON_RTH` | 353393 | 0.000000 |
| `ES` | 2021 | `ETH_NON_RTH` | 353363 | 0.000000 |

### `low_depth_rate`

| Symbol | Year | Session | Rows | Rate |
| --- | --- | --- | --- | --- |
| `ES` | 2022 | `ETH_NON_RTH` | 354119 | 0.000000 |
| `NQ` | 2022 | `ETH_NON_RTH` | 354112 | 0.000000 |
| `NQ` | 2021 | `ETH_NON_RTH` | 353393 | 0.000000 |
| `ES` | 2021 | `ETH_NON_RTH` | 353363 | 0.000000 |
| `NQ` | 2023 | `ETH_NON_RTH` | 353358 | 0.000000 |
| `ES` | 2023 | `ETH_NON_RTH` | 353153 | 0.000000 |
| `NQ` | 2019 | `ETH_NON_RTH` | 349845 | 0.000000 |
| `ES` | 2020 | `ETH_NON_RTH` | 349608 | 0.000000 |

## Registry Identities Used

Each row lists the exact registered FeatureVersions used for BBO aggregates plus session-segment joins.

| Symbol | Year | Rows | BBO DatasetVersion | Spread | Spread ticks | Top-book depth | Missing | Bad | Wide | Low | Session flags |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ES` | 2019 | 349532 | `dsv_databento_bbo_f91f510a8d6fa87b` | `fver_40f359f255662ce5285511d72d1c95e8b79955481a5200c068352da036833440` | `fver_7eb2c1d84e1b747fc92569ea5305b36f60d3dbcae493ef5adac302eb8bcd405c` | `fver_0faf50d4dd033c5a2fa737ae6646d1887745a3448b0aa3bab17396567a2e389f` | `fver_78d968a8bb123b26a96c42d66f2ecc16d7f9abb63e0508a520d16ba77640024a` | `fver_089ee9a7fad5e283764a0d58198115676e9a60096e7b66932f942cf66b7e8dce` | `fver_ea32b7301c445a7492d48f8fad6e80bd651647340dd8a48d7b5b94ebb668e9fd` | `fver_efec705eb36a859de89d8f196bb7ca8b0e70e90166aeae120e02d0a658cfe88c` | `fver_3fba1a0683bfc8c307f4ed662cf5ecb2fb703d7d50dc75bf2d7122dcfeade9b3`<br>`fver_8be217c4cdb47c0400a0d156aa622317755c59678ed7381246fb7fafba7b5131`<br>`fver_c1fcc5e05a7ee8086a8241c4f7a10de3aa51cd27570472762dff1917e7e08f17` |
| `ES` | 2020 | 349608 | `dsv_databento_bbo_af9511d169b0aead` | `fver_249f68a03093fa975ad0d2905cb9cfd20c4890465bc0ae3a6ab804ecf3af59ca` | `fver_6ac0780897a963a7997fc8b898d6ab8309a49da8c347f12e50ea460647de2f28` | `fver_ddc322750192491f230c9bcf7c17dcfa48b1600f67de3adfbc48b0d9240cfe25` | `fver_3c83838c9b1efbf3746887b83b8ccb3080322b0af21bb43c9084989aeb979ec4` | `fver_d62f8dc9b00140bbaaf3378f64f53e5b9485b2441f05b1f25f2b7e395697ebdb` | `fver_c8dbca5a4150f0437f98de767f6b082bf8c04f0f789d824b2a0dc00cea46cfc9` | `fver_f75128805419b7961f51d736539f5998a5194309c39607c3aab99ebf24f9e154` | `fver_d5dd3200e0400cb9aeb49b21259dee0047c4e8b56d4a43fab64345f14c8aff9b`<br>`fver_d6a4cd69f7b06182c7496394550938ea4ff130046c810c8d5b528f6142642fba`<br>`fver_2d4b03fd8246d9c343df84ad3315dc4c564bff807f8dd9bdcb809f09ac423704` |
| `ES` | 2021 | 353363 | `dsv_databento_bbo_d5cb08f949e7ff28` | `fver_956d2df73c8af315f2af31fd586e389b29048655d19bb46d87bd6ea9029b697f` | `fver_f3c5ce047c95aac0d8bd6deef0451e97ed92b87dfb7ba0337926f8f0805c2b0e` | `fver_e2792bf9c0c0b0630cd9bc91eed07f64edae26294141917d6c38e011c5a697e3` | `fver_b74805e36b760d4636fa6d756e8479d487f93289daf803676e4efad78b89cbbf` | `fver_a515ef2c7fe2016ed0f073ee40172e049244d19f2e0334cbb67c7a78faf1ce9b` | `fver_50a2d5af38f8bf73ca94dad638c551f5248a41bba0e1833693ea998f07e5217c` | `fver_28bd4156616ed2b13bc201acb7c7f5a7d7da5c12ca367dd2f8479657efbf26f5` | `fver_56ebc6becae4f421219d14cade3eb32670c422385336a0adb9e5dae70981acf2`<br>`fver_3c99a7515d1a720a2d8eeefc5f714ab51124393ee78488bf28cce4dc32841e28`<br>`fver_ec688c018dde606e884312ae96716cfeea09d37a22e11a82048b6f818cad8ade` |
| `ES` | 2022 | 354119 | `dsv_databento_bbo_7b5595d5030462ab` | `fver_e7c28ca29247bb3f50e75089e8b017ce743c0463a07c41eb191c4d691cad270e` | `fver_8ef6d437eaa45fe803dc17247b31cc9d0b81761e78232f38d3cc311a72cd084c` | `fver_2fad3d0b2d3c46deb0acba9fad9de420535e8b202ef1e422e8ae570bc2c9131b` | `fver_c9ac864efe44987cd987b8e3d20e1df156a981e6def499419f83ea3b8dcc9b18` | `fver_5a090e49fa3adb7bbab7389454ec8a2fe157b86ad9a29c8ec443390b4e82c8c8` | `fver_0570c122302ea0504e22fb7e8a128745556f13eb94b9d86c33dcfe36fe55ae20` | `fver_6977d39b267152eca4096146952594c6032ac6de93c52b590737b9cdded36688` | `fver_dfb98e1152d656b7ba5e9709b3fdbcc715437dba2a6d51ad4cad39a13ec7cdde`<br>`fver_6e216677aea8be97984ed69685ef183666eeec27492c37cded480e953b64fd62`<br>`fver_c0e4a0183e7d4671c2e0d7ed4bb3bba8cd7a9fdb287fff57d435944a832377ad` |
| `ES` | 2023 | 353153 | `dsv_databento_bbo_8772e3b47aa5fb98` | `fver_02c9091967c01b3fb2230093d1401a24ac45030b8aacd7717af40cff9fde5a2f` | `fver_9e391c824c6827838bce0dc4de23dfa7c1a819366a27330ce8102b9e9ac7f026` | `fver_98bf87e0b041b5c3fb5500c546f3821ec7a9ac01edec95c79e6fd82abfaf9972` | `fver_761bc0e3680069768f3f77f83caae31d3d210c1828db410e717f805d2c8b6c18` | `fver_e7144eff945da6a594d16fa3e23f8cc833a532626edd3cea8e86e6e331ef76fe` | `fver_50752a9648d866f2795b638a897ca6a045d425f7e80c1ebef0fb09ad969a1a0f` | `fver_fed6748c9353a53c164f770a23d8ed20f593aac69771c8fa3a17ce6f842b2c34` | `fver_fdf6ca4a40ddf61ba550122101763e7217c2ecd924c3f1e0428194fe5d4dec5c`<br>`fver_0ba53a1884c3c98f877adabdfcf6c9d962c1271666f15beb6368e104e51c3c2f`<br>`fver_5961839999584393265a3487fcd0ec513078758ca51afa8b12b07d04c20fe85a` |
| `ES` | 2024 | 346858 | `dsv_databento_bbo_f9e1d70a04d9dae4` | `fver_d4c2cd7edbe9a1a6f20bf93a0b1380c07edd8ef009a665e538093aad74b8859e` | `fver_fe6fcc0cd2f91ddadadc1e756ac94129e58fda7e4a9fb8286eaa9e7d970ac284` | `fver_aac3c66c35784079ea809e433c304e72fda34fd1a8cf344c8ba335df7c94737a` | `fver_b696f0b2399075ce36422b62458eff97386ec476e56c009014aab63834670cce` | `fver_8bc345c2b1d85250bb6b85754a5d4700b06c22bd056c5d91473ac10ff3899759` | `fver_3a162c4da024b6a81cbf997ba02d47b070bcc13f2f09884a104ee6053f3dc486` | `fver_88d2d46cb7ffc1c9cfff7c5a8cfd3a7553d54ac88360ddc5b869af16394233dd` | `fver_4f8e57f974e816a9c3c29c858618a27be587ea6dccdb539f6ad8ed344cb86082`<br>`fver_e4a726e194ef1ddda23d23d767fa44e1a33fdb9f76b8fb36ba437867ea6a1b77`<br>`fver_7675e4c7a909ef6a34b6860b5c4fb777651f48169249832cb4db72a42aca8e3a` |
| `ES` | 2025 | 344561 | `dsv_databento_bbo_35d4417c086be53f` | `fver_6d5342b281f310dc4b06ee2023794adab6047b1c702383d50096e50f6ae9c769` | `fver_1f83ac386a08ce609d691d484c6599b52207d4e877511dadcb230d557557081d` | `fver_e6624aa7df112d07d805d9998d01ba25d86e6a10154d6a46149c036958b37963` | `fver_d9f8550a8002b18e6084979216e1d7a1b044ecd06852ef4fda41edc6be8011cf` | `fver_2c79cead6c1996fb32e4d8aa99dddd255b67f2aaf44af9a734d53829dad9576f` | `fver_29da2dcd967071e8eb1b5d6f0618c33a9d80eec7894fcb6da1e9812a39d2cd31` | `fver_2d21e44075a170c4b905bac22ee9a87ff5f14117ae8f1606110151708552b382` | `fver_18d823a0051d5d2a95d1a6fcb4bbded6eb9e07363be33400582bea1cd4123e93`<br>`fver_ccf43e7d4168786ba2605024cbad78199b0c2d3a6f59259e49ad12f1e7dd460c`<br>`fver_c9789bad5fc9610b460f5cb5865b3f09268ef6e3c1ce961433cf0fd5dfd54c61` |
| `ES` | 2026 | 140639 | `dsv_databento_bbo_22c49fbf57cceea6` | `fver_1dd20ec10fab0d2c9562a041d08e62d2ce02161e6cfd47b2fe757a866cb07ad4` | `fver_3a730952000840b0fe4382f746dd001e9f8aacf0f121e37898ea03e12abe0819` | `fver_283104152fca542c267995c79d5ba6a51d6b1524be6be0a99435a0fb155df3e5` | `fver_6baf6084c1612db6c466a59e169ce2812fc2bf32d6f3a5b72faf37e171fcb0fe` | `fver_344029373b92954d93f2ef2077947fc5cc8562ed3475363185ae6ec48f035c8c` | `fver_0c8ba22ac3bf70b0fed90ceb0787ad992cddd42f881c281bccfcdb9d1537d384` | `fver_b2830836598768a9ef086b090749dcdf1dab441b43360c77427b3fc7ce30ec4d` | `fver_2713ab7701dfd7c531eee2950d226f6b8537862cd0f17b8ce15f5c6d44f1cb0e`<br>`fver_ea78d6cf82717127d6b705d0fc4a0b2b46921c32d3ae334d5a86065e24ed6650`<br>`fver_166a4b119c641c036928f5d7019e9d0c8842b1a090b3e52ba6ac3fbb0d537626` |
| `NQ` | 2019 | 349845 | `dsv_databento_bbo_f91f510a8d6fa87b` | `fver_6151541699811ea37d49e7f96ec6430ba6c8497664eb23c7c870d2605f54f219` | `fver_a61510feba9c3fe83aa35b9cfa477564cd6439acdb1c185274e24c0d3e1c00e7` | `fver_29e23aad48724196cedcc14482b3d97d7f996f6fee6e27bd96ab849e1ceafeb3` | `fver_c02bc884bf58a31e3f78fb85d25351aa0a2857eceddaf5531fd6325460ae51a8` | `fver_76d7445e2298986a0ebfbec85daf021ba566d4ff74c87603263ef82bcee0d888` | `fver_7d134fa0bd2cbf5fbe008f9af20f11a3cf5ba2e5b4e503d6560afb4f63d01023` | `fver_1b0f2b023ec92ea4b3d93bb34320648144ac34a5898d359ab79b27ec044a2184` | `fver_bfaf9042f6a6506832c51aa5263f9ae48708105c324acaae8956604dae1489ad`<br>`fver_62cb64337f13ed92f3abfe02fff289c5769d1f3d3d82d7f3d72befb2b1b784e1`<br>`fver_b4c4ddb000889566bd9d3e2bfeda3978fe9a05b1911c132481435e8996e1f095` |
| `NQ` | 2020 | 348929 | `dsv_databento_bbo_af9511d169b0aead` | `fver_a847de49cc3c41d6360b8cc39ceee246e15cbd1ad687bb11c350eb982a63ce02` | `fver_56d6fdf2befe66aadda7453762c3f8a6f138cf6a23c447d0c0a89f7c77b7888a` | `fver_531887042adfdf3d195aff70152adf0a43bb46d681598a01fced595be1cd044c` | `fver_34e53aa5b62723945470962ead2e677e1829f547700c64d4217fcac184ada2a6` | `fver_b63444f74631de2e3a3372bfd0a6fe4a64facc48c01dd7a1d4ba10263b508e9f` | `fver_36b3a22bb83f6a6eae2b5db7e2ab912474cbc70d1aeac7693c19743d4797c944` | `fver_ba9fc407e5ed9cd34bc5898be45de50c5f5cb9e3a23ba95959d456dea2d429f9` | `fver_9a29776a96f7967de5fd706e72f6957b0131b893df523792f3c6ed2f7191ef56`<br>`fver_773a2908c7cce9983111860531c460069ed62b2c4ede0a07bc5aacb86dd4a446`<br>`fver_f16e56fbb1601a4c787c399294ca12fdecbe72ef6ec7a01338751e5a49ae449e` |
| `NQ` | 2021 | 353393 | `dsv_databento_bbo_d5cb08f949e7ff28` | `fver_e323127e61889fa17045164a6ba1933fbfff3f245d821765cbb3b6df9b65f0ba` | `fver_c8cb17e23464f2affc4a720d955dfadcc64651790a03dbed43e79647f627bc75` | `fver_4c5254a9fa7faf3cd21e572982401e3bc4db80c88f708661bfb54d8fca9ac5b7` | `fver_cfa95f081cae667246c9cf2a5e37c1751add94a1a6599f551a299f1e72d7c33f` | `fver_bae8d6c2d79d11d78085d7605cef9b8224c9c701e7f167cb40087bb14890be85` | `fver_60d8883e7386466ec7108758d072908c72230a26a745907794e88348966cd7f7` | `fver_3edd1db72636f13ab82552e249f763c260ad2a42151f8181a34063198b23ddfa` | `fver_d3e7eeb9bdcabc720b619149ddfca52ab518454c7083dee24c295dba0bf67968`<br>`fver_4a79da17c0b34c7afac390945330c00ef6e31c3532c499933b5eca5a7d995ef9`<br>`fver_2c489d9da1dd8f763c0e076c6ff6e259d699ff4024379d8504223222d8026c96` |
| `NQ` | 2022 | 354112 | `dsv_databento_bbo_7b5595d5030462ab` | `fver_3560916a852c723ab06d99cb87f826fdc8e639aaef6c6201c7f9430139144977` | `fver_5b376810fad4fd715e28f0f70a948fb8a573137bb88fb4850de3a30a334c9ab9` | `fver_328b341786218d764259a08e83829984821c3f5fc92b273985281baaaf2ceded` | `fver_dc6ffab6912da94d27046a284c2303f9e72c7a3300bd59a2e40140e22433d6c2` | `fver_5d8d72c4906f3524e027aff78afd8c6012c85dd1ad077225b1f468c4c9151e16` | `fver_c6779259f3a88eebaea16cba26f8d96e9a4a90fe65b69294bb7341e283ec761a` | `fver_3a4c21576455f0cbda894b81a19ec688063160dce27bf273f492f3d42fe600e3` | `fver_7dbe2919a6fe54c02531bac0e81fc4747a88b5169a8af4da8e12edf9874d6355`<br>`fver_ad6038645170d06a0aeb91a47d8aa581ebdb539cdfaf36c6fde8f007d7cf1b42`<br>`fver_d68d6987a55485fe9d96d11f27b74ffcbefac6319a84be120fedb888c3c9987f` |
| `NQ` | 2023 | 353358 | `dsv_databento_bbo_8772e3b47aa5fb98` | `fver_21cb8ea330e79a2e52ca78262733fd83e363491c29a89cb236d7991e6f99259b` | `fver_510db655d76fad7edc75f44c3712f03043a58c7435fc198615ccd680983e2f3a` | `fver_6948dae45c929af57e661204f20a57670bc34d508f7be2d5a8943836cbca1fab` | `fver_4f7c086b9ea28ca100906b3c09c2cbef9037162d9ab30b891c395e0515a187b0` | `fver_cbb656412930f4890fdfe360151e1f3fa78999ef55a29a1be41506e7e5976bab` | `fver_75cd507bf855180c5c75cdf1f7c7e0a7ee17a563b1e1bf2abfcf98e81aad3863` | `fver_daa9059ac54b12f561dcb7b1eb81dd2ff7c96f4dbb56c68583d93b9e09c392df` | `fver_492772e197a8b11b78c5dee9e144b369475cf5f3acd30afdf701ebfecb6b1aa4`<br>`fver_77a0ec99c0311b3447b0fdf5ee09041a7a88f7ee60f8066f833ae3046ef0aaf8`<br>`fver_5f9087fb131e11773f5c65a0fc9925c423617785f39788491e930bcd4b8aec3f` |
| `NQ` | 2024 | 346992 | `dsv_databento_bbo_f9e1d70a04d9dae4` | `fver_7439eca390095664c91a1d55df523eb6685ed6867692fdee23bbf72c9697e3f5` | `fver_6ccf67910310b8e4b40e0ee9531107b996b4d0f0056e69b63e164bb056dd1213` | `fver_1c4961e4235038e374f34e510fc0591080e3467f89564fdd1a1cb944ce113496` | `fver_bfc08f2e84c7f133c95cd7a3ef78ac2f965662f00e44935a4f13c3b07ba48aed` | `fver_024ed7e353c75c3108667bc029050ca7d673389df98b67ee6415de624317a4af` | `fver_2380c0a86af332a677944eaff06b41b8279d4064a23794a63b3b1c792ad556a9` | `fver_e32fdf9814d3e2f365c661c53ba28da9ea4135fcbf9342527d28b1a868354ecc` | `fver_da46cb91020dcbda2e11a1c0fa9cc76e43a44bcacb4823a02228d61b24ce5437`<br>`fver_517550501fc9b6ceb27723aa04b775da4fe1dc2cfd977b3fcdb2a2f23e25aa8d`<br>`fver_cd37dee096036895ed8325254f0090b4cc6677ba33c13793b61bf0e7452b13f5` |
| `NQ` | 2025 | 344529 | `dsv_databento_bbo_35d4417c086be53f` | `fver_a3dab96e016e95ba1dba8235708706bdf8721aaa001b1418dab8af7d8eeba958` | `fver_2eb7fe18dd60153a75bbff69d89cbf38ca2ba41019de84bad63726d31ffb6a1b` | `fver_b8bde8e0abcc0df00e69392d188fa1e3ec16b1e128d17edd1f71e5cbc92c0f50` | `fver_2b23b0a2106802e7b8c691652d78abff1cf2eeca6f6d4883f07f5f1f8aa7afc6` | `fver_6d5e86837bd1b39a56d0713cef4e23eb5e4c10e69fdf4d57ad317cf5c9c9cb1f` | `fver_cb4b7b04c6c783d9340a4a56a50990c511aab7f3a2ee4ec9f5b026115ee6e810` | `fver_afe13932f76475c8da55088dd671be26378b3f3107909aa77c05669d7161f59f` | `fver_9970fb416f660d7f1627fd63f021caf3c2c194575b77fbe49e44f6d4121f45f0`<br>`fver_6ccee152c2711c53cdd8a2a12279258e05ce8b4baeed98cd657d8eeca6c26223`<br>`fver_f3c7e68362d0b24ee32afbb811055f06e425a3590486380bfe7d1a6435cd49be` |
| `NQ` | 2026 | 140610 | `dsv_databento_bbo_22c49fbf57cceea6` | `fver_ee075cb89c5d5dbd0f4e4ea02b2e00c649168d1711fe4c26109d37efe97303dd` | `fver_df2b9a46dc8d12371568cbd1527b68a4a0cb1a8da6229959ef5f02130dd1b55b` | `fver_e98858c7ad68849cba65cb2faaef6cd351cf6e276bce89b0ec04f5245dcdd973` | `fver_1762186829f144d8f0f688b01a3dee698ef7669812cb6686e1c0d3cd5162208b` | `fver_f7196da27acb257405a10c154653fe732d3e5cf33ed9ea1b97d85b2c3c659f23` | `fver_92e6efbbda9633be74f459de126c42d869fd1632512eb0c287037d541e5f89d1` | `fver_bcc4c7b2774a2c7c8bd31424b0f2d068e8e3f125b3f95e735e8b48af9e0a29f9` | `fver_c9fc55b9aa08e51104c8386badefae5e34879329d6b758ce769e4a34e5d5b033`<br>`fver_350d30c18ee3dd9a62cc44fb88f0a641672d20e6ec84908865e6a7ba2cbb340a`<br>`fver_b4d7aa5f5106a007b7c00fefa59108eb0ceef189238575d783560fd2ab000ebd` |
| `RTY` | 2019 | 328841 | `dsv_databento_bbo_f91f510a8d6fa87b` | `fver_a0b192cd32e6ea3fbb400dad76529a017d1ca6ea78b15917b3030ced6d54355b` | `fver_47be03db2549786eaf855c0cceac0651db37fd1891f16ce5e93dfe3c9e3473f2` | `fver_d83a337e6af8b1fdad1815d3417bd5fec04f144c3175d779cf77125546c63509` | `fver_5360822c9b065a44af5e68eb4445d21fcd433280c7000893e6797e1bcee7d38d` | `fver_1feb41b7f2f730123af210950c6e1759971ea97e13def7bd597b9eb983e31b6c` | `fver_b759115a857dade2839ab21b95baadaab9624ed6191e8708eff1b2c5572ac20c` | `fver_42805ade990bfa2a400211bdea850f0e539600a35f9ef6a75ad244897c087eeb` | `fver_95904d7cbdaf7132f3bb495915a5eb130b596b2eddeada9f24fdfce51b38b351`<br>`fver_baec394fb524f1db93ffa6aa62ee9d190218e687bc4e668f083e63c2540893df`<br>`fver_a6e99fb3c7545bf069a07ec31c220933dc0bb13e793398b3103d9257005d475e` |
| `RTY` | 2020 | 338085 | `dsv_databento_bbo_af9511d169b0aead` | `fver_8ad926bed675d91720cfb5a513fd7c77989e56afef1e7f2057aef6a92eccc391` | `fver_c9e21b98c145b27b7c9e542a668b7f0ae939f73aba8464be7a6305ea0f251488` | `fver_4b7d6e8cb9b6fc6fc35c3b61b06622dfa1025fa32e3d586bc824db08f5ad00c0` | `fver_d5225532141765b5430b22d577f11cc5b991accc52987f0234798d99cc90d7f7` | `fver_8725003989890f1073bc1c541dab82b27144b453945472d07a78b1d7e5c32ae6` | `fver_3a2887a9d1ee643b51626dafabd6ec71774ef977d85bc452d4393e8c20aa8b93` | `fver_cb6876002a759c0805bb73e2535dfd1d54b6284dd6b5183bc6ff7ade98451b04` | `fver_a778ef5dec589c8bb6fb07de82acd0ac27152527dc8d07d627442fd916fdc8a6`<br>`fver_6db54e27582bea005fec11e9778caa33150349bf4da9308e83165efe6aa0093e`<br>`fver_665817d33694b33c378df1cc0675c6e130814b8654b1e548f0a5547b4c00d8ba` |
| `RTY` | 2021 | 339895 | `dsv_databento_bbo_d5cb08f949e7ff28` | `fver_c8e198053406269483bcc3b0aed11e32607aeb1bc5e64adb5761669aa795d8e4` | `fver_b8d57caddd2a40f9f47e26ffb4114f0a480833217519e42868ed32c561f6c8dc` | `fver_7e763eb2cdf94ea0ea41c962d3b6b1bc2ff07d96c452c53f31bff6822bbc2a15` | `fver_672744d994715afac374c6bd0c325dcdadcfebee5d29354b2c0cccc87b22b1b5` | `fver_86a08c1b72aabbf4b063858705379574857cf777341da47bfd6a47216b2ce301` | `fver_e0be973ce508824fbb546842e459a86601f0983559b47cdcbbf3f0843209fada` | `fver_d4d9ccdbba81240ec38edbd8d8a25ab1d28c3b92d86dc9d8d9a536e70b820e94` | `fver_1f490c986e1daa30e63841f141f1c264249cf12453da953cb4b9700806d4d6b5`<br>`fver_650dce57be7d0b62b12444e81364808451e171f9e732e520d42a03cfc961891c`<br>`fver_1571bc8d3830a3c9f701b7335bb7b60f017109a2db9fd47ab26a074a9b27c5c8` |
| `RTY` | 2022 | 345162 | `dsv_databento_bbo_7b5595d5030462ab` | `fver_68b06b84fac4818710c5c020601179e6381c864ac7b7e2a7594b97e784f09b4f` | `fver_8bf5b497f2b265b57330ff5c9944d2de80106153c4581b3339e6d58043ffc1bb` | `fver_82e346b1497e2f7b7843a7b8dd6370e4788f9b885d5f5ad171e453579064bf5d` | `fver_d294638648f987d0a12b55fa384ec12a559fbb26ec9c4d35ac02b9c4f156269c` | `fver_53f7acc3c1edd357497586056f1d7e1d0f1874e67abfbf773450a3aa78fe2aa2` | `fver_44ebca6626963f0ff55cabed6ce7996a4ccfe9ea122c664636f16e8c26d9bcef` | `fver_ec7f20504a1202f621242016f8186f7dc9972f31e4ef211faff0f898d7de4f0c` | `fver_602bb49f32d051b29d79ad68c57cf21968375466013b366e2cceb715aa0cbb43`<br>`fver_9439b2ca5f6c8dc5299cf32d490079971c0a5ae22206b5cfab8073226e273f8f`<br>`fver_672ba7193c2d5027aff6760afcf98dbba5b103fbe8b4869b12327e22400c8159` |
| `RTY` | 2023 | 342436 | `dsv_databento_bbo_8772e3b47aa5fb98` | `fver_95164f39c0ff04ec9624ce07a6131211898c058eb06c59ed7793865e02350247` | `fver_901fad3c1a462526c649300e5a1d73b399ac07382440b66f6cff95ed70815f46` | `fver_e0236a32c84a50af66affac7f3f608655a6d8e300bf3851c199591482de78c4d` | `fver_58e0d0f305b7c1783a495d97b890e13e64fa60ef01d6e1dcbb0c69a86a30c252` | `fver_0cdddbf21c88391650c4346f96bbed29446c3b66623acabed57413ef93986bec` | `fver_fcaf7c1d10b8839d2b2a4fd4c6b8b9f2ca25383720b6140284f416dca5cba97e` | `fver_47193446855b0c58fbf4298bba3e435c9186b1d9fb392e6178c8d1bdf2d770c8` | `fver_4ad93b6aad1b680daef1f93caaa96742c837f008216eb1fd9105ef858ebbbfc1`<br>`fver_16f6a46292c183cb1bb4bf0239209f423bd7c736cca6c48b2ffa2d352c122696`<br>`fver_a4b90ce50e8d3d2eb1e62360b0b71784a9f2b880416c092e527ee2c274d8c6b9` |
| `RTY` | 2024 | 333540 | `dsv_databento_bbo_f9e1d70a04d9dae4` | `fver_ee12498a0dd96d1a94398a5ee469eca4c6783d7b400ef1edc5d9a762989cd46d` | `fver_391aed1ecec176fcf1b54b41562dc937b1946067f3b19811225cd48e2149068f` | `fver_21bb98c1823fb4d8a34906cc45e2cac19e0533af754dc3fc71ff019087870603` | `fver_15c604fac1031090750739065737e425e723f3a260d5b314a9fda56c7e49f363` | `fver_5476ec77f4237284d28e4764c0150100243d2933ce4e8fd166d9f81ad70acba7` | `fver_9cb271e01d0a85c376f9a4e2d8f8297d0c6e39a91fcb5b4ee6859a33b78fd0af` | `fver_dfb1495910d2c5ce5c599dfd34b1e8b5e172978ce73e4cff3060b52dd993e0b1` | `fver_0b8fdcb3e4f1bde5236ddc78e3a01694f36e4b4e39cde7beec3ba26d6326a215`<br>`fver_04fda2d17af939d9937c1170f8f9e6dc6bf1d0737cfbca0ba4378b8ce016ce30`<br>`fver_7582d067774eb595b70fabcb639cf6db34253daa45855ed57a56df59b2963e8a` |
| `RTY` | 2025 | 333557 | `dsv_databento_bbo_35d4417c086be53f` | `fver_d40e3e7df8244e0fa6d00463479eab603a39af722916823084837652a58020f9` | `fver_cecb9ebb814511b911078772db559252a29299dd71e95dbcf6663502e1e8b5e2` | `fver_093dce09a4f89904f322518329b3ae93eae8c261dcf84276cf0e55d6eb74763f` | `fver_20d228a7476838449530a2ba72e92fd75e3e3f9b09d808d10954fc4fa266c764` | `fver_b59a410e1866debd87d2d5cce7eb9980a2a53d8d6347ba9dd9e89cfc9a476551` | `fver_b2c28a26e367eec7972beb8b8a673dbd3268df2df3a8a33e144c6809b72531f1` | `fver_5c93f4f462f8df3d4f46872f99fb2cef1df86c997359023971c803b5afeddcb7` | `fver_ff16a78584ebf3bef90e71629f6969e8bff9b95a8daa695942d81b8045d66424`<br>`fver_127f8275f6bb00017ca13b5e4f11d29637f89c637bce625a156099760bd10678`<br>`fver_241c4770e6eede735638a699456a02af7102b21ef3bda0bd8c1601fbedf376e5` |
| `RTY` | 2026 | 138593 | `dsv_databento_bbo_22c49fbf57cceea6` | `fver_c7404972ffe30ae39ba6e7f8b4195e705a66b1a089412fe2daded7695a185e1c` | `fver_dac9d597c14908f870b01fc1b5e66b02a94c918e770e2dc8dff140d8a7c34228` | `fver_3ae2f5aa10bca33898b3419956561d227907bfdc3e0e865d50c731cb49725cb6` | `fver_4f3503c3cb5d32b8727ee7eb3e8aac0d53e2d5fa7a0e8d474cb5c91d15d07948` | `fver_0dab8bf3f28615b1e5a8553c58c04999218297279683ab29874c6fefdeea813b` | `fver_e248f89aeb375081ec815cf232fcb012dde0396d08a1b1f845c45d61758609a0` | `fver_93523a56c059fc982507052d5a7633fb5b7e20816876ae5b6296c73ff651b0f1` | `fver_cf7fd8ebe44aadf5197d40a62d7cfdd990f04cb560567b62b3aad0cc08756117`<br>`fver_bd798a42466e9929526b0b505a3e8e86c3bfdee1a6155eaacb9f0634bad8c849`<br>`fver_6a727c1c917098212656cc229690ec2a4fdc7438ba6913a28fe8446cf8459988` |

## Explicit Exclusions

- 2018 is expected-excluded for all ES/NQ/RTY BBO cells because the required `bbo_1m` DatasetVersion is `BLOCKED` under FUTSUB-P02 acceptance.
- 2019 and 2026 are retained with accepted-with-warnings context; 2026 is partial-year.

This matrix contains counts, rates, shares, bucket labels, and registry identities only. It contains no raw quotes, per-row feature values, price series, return series, provider payloads, local SQLite content, Parquet payloads, or execution-quality claim.
