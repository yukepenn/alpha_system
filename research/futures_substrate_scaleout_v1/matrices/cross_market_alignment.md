# FUTSUB-P26 Cross-Market Alignment Matrix

Value-free cross-market alignment matrix for `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` / `FUTSUB-P26`.

This matrix characterizes materialized lead-lag, residual, divergence/agreement, relative-strength, and catch-up/rotation states. It draws no predictive, relationship-strength, alpha, profitability, production, paper/live, broker, or order-routing conclusion.

## Method

- Registry input: `PYTHONPATH=src alpha feature list --alpha-data-root $ALPHA_DATA_ROOT --json`; aggregation resolved current records through the CLI registry helper `_feature_records(...)` in read-only mode.
- Value input: registered P13 `cross_market_alignment` Parquet-backed FeatureVersions filtered by exact `feature_version_id`.
- Session input: P07 session flags joined to the ES/NQ/RTY aligned panel by `available_ts`; strict-intersection survival is compared against ES/NQ/RTY per-instrument session grids.
- Availability check: each yearly aligned panel was joined by `event_ts` to registered ES, NQ, and RTY `base_ohlcv_log_returns`; the check counts panel rows missing at least one exact `event_ts` contributor and any panel `available_ts` earlier than a resolved contributor `available_ts`.

## Alignment Policy

The materialized substrate policy is `strict_intersection`. The fast pack still has an `asof` default in `src/alpha_system/features/fast/cross_market_panel.py`, but P14 scaleout guards require `alignment_policy=strict_intersection` for FUTSUB substrate materialization and reject `asof` for this path. No aggregate below is an `asof`-aligned substrate number.

## Session-Segment Coverage Note

The registered session flags used for the matrix collapsed the accepted cross-market panel rows into `ETH_NON_RTH`: `eth_segment_flag=1`, `rth_segment_flag=0`, and `halt_status_flag=null` for the checked cells. This matrix does not rederive RTH or maintenance-adjacent buckets from timestamps. The collapsed session split is recorded as substrate quality context for downstream consumers.

## State Coverage Matrix

Column definitions: `Non-null` is the share of rows whose state value is present; `Quality flags` is the share of rows carrying any materialized quality flag (`quality_flags_json != []`); `Cross-market gap` is the share carrying the named `cross_market_gap` flag. In this substrate pass, the materialized quality-flag rows are the `cross_market_gap` rows for the listed states, so the two rates are numerically identical while retaining distinct definitions.

| Year | Session | Scope | State | Feature | Rows | Non-null | Quality flags | Cross-market gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019 | `ETH_NON_RTH` | `ES:NQ:RTY` | `aligned_returns` | `cross_market_synchronized_returns` | 356040 | 0.878716 | 0.121284 | 0.121284 |
| 2019 | `ETH_NON_RTH` | `NQ-ES` | `basket_residual` | `cross_market_nq_minus_es_return_spread` | 356040 | 0.978907 | 0.021093 | 0.021093 |
| 2019 | `ETH_NON_RTH` | `RTY-ES` | `basket_residual` | `cross_market_rty_minus_es_return_spread` | 356040 | 0.878969 | 0.121031 | 0.121031 |
| 2019 | `ETH_NON_RTH` | `NQ/ES` | `beta_residual` | `cross_market_nq_es_rolling_beta_residual` | 356040 | 0.941344 | 0.058656 | 0.058656 |
| 2019 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 356040 | 0.615358 | 0.384642 | 0.384642 |
| 2019 | `ETH_NON_RTH` | `risk_off` | `catch_up_rotation` | `cross_market_risk_off_rotation_proxy` | 356040 | 0.878716 | 0.121284 | 0.121284 |
| 2019 | `ETH_NON_RTH` | `confirmation` | `divergence_agreement` | `cross_market_confirmation_flag` | 356040 | 0.878716 | 0.121284 | 0.121284 |
| 2019 | `ETH_NON_RTH` | `divergence` | `divergence_agreement` | `cross_market_divergence_flag` | 356040 | 0.878716 | 0.121284 | 0.121284 |
| 2019 | `ETH_NON_RTH` | `NQ/ES` | `lead_lag` | `cross_market_nq_es_rolling_correlation` | 356040 | 0.941344 | 0.058656 | 0.058656 |
| 2019 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 356040 | 0.615358 | 0.384642 | 0.384642 |
| 2019 | `ETH_NON_RTH` | `risk_on` | `relative_strength_rank` | `cross_market_risk_on_rotation_proxy` | 356040 | 0.878716 | 0.121284 | 0.121284 |
| 2020 | `ETH_NON_RTH` | `ES:NQ:RTY` | `aligned_returns` | `cross_market_synchronized_returns` | 357300 | 0.923767 | 0.076233 | 0.076233 |
| 2020 | `ETH_NON_RTH` | `NQ-ES` | `basket_residual` | `cross_market_nq_minus_es_return_spread` | 357300 | 0.973795 | 0.026205 | 0.026205 |
| 2020 | `ETH_NON_RTH` | `RTY-ES` | `basket_residual` | `cross_market_rty_minus_es_return_spread` | 357300 | 0.923997 | 0.076003 | 0.076003 |
| 2020 | `ETH_NON_RTH` | `NQ/ES` | `beta_residual` | `cross_market_nq_es_rolling_beta_residual` | 357300 | 0.954985 | 0.045015 | 0.045015 |
| 2020 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 357300 | 0.750837 | 0.249163 | 0.249163 |
| 2020 | `ETH_NON_RTH` | `risk_off` | `catch_up_rotation` | `cross_market_risk_off_rotation_proxy` | 357300 | 0.923767 | 0.076233 | 0.076233 |
| 2020 | `ETH_NON_RTH` | `confirmation` | `divergence_agreement` | `cross_market_confirmation_flag` | 357300 | 0.923767 | 0.076233 | 0.076233 |
| 2020 | `ETH_NON_RTH` | `divergence` | `divergence_agreement` | `cross_market_divergence_flag` | 357300 | 0.923767 | 0.076233 | 0.076233 |
| 2020 | `ETH_NON_RTH` | `NQ/ES` | `lead_lag` | `cross_market_nq_es_rolling_correlation` | 357300 | 0.954985 | 0.045015 | 0.045015 |
| 2020 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 357300 | 0.750792 | 0.249208 | 0.249208 |
| 2020 | `ETH_NON_RTH` | `risk_on` | `relative_strength_rank` | `cross_market_risk_on_rotation_proxy` | 357300 | 0.923767 | 0.076233 | 0.076233 |
| 2021 | `ETH_NON_RTH` | `ES:NQ:RTY` | `aligned_returns` | `cross_market_synchronized_returns` | 357420 | 0.921669 | 0.078331 | 0.078331 |
| 2021 | `ETH_NON_RTH` | `NQ-ES` | `basket_residual` | `cross_market_nq_minus_es_return_spread` | 357420 | 0.987561 | 0.012439 | 0.012439 |
| 2021 | `ETH_NON_RTH` | `RTY-ES` | `basket_residual` | `cross_market_rty_minus_es_return_spread` | 357420 | 0.921890 | 0.078110 | 0.078110 |
| 2021 | `ETH_NON_RTH` | `NQ/ES` | `beta_residual` | `cross_market_nq_es_rolling_beta_residual` | 357420 | 0.973409 | 0.026591 | 0.026591 |
| 2021 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 357420 | 0.716787 | 0.283213 | 0.283213 |
| 2021 | `ETH_NON_RTH` | `risk_off` | `catch_up_rotation` | `cross_market_risk_off_rotation_proxy` | 357420 | 0.921669 | 0.078331 | 0.078331 |
| 2021 | `ETH_NON_RTH` | `confirmation` | `divergence_agreement` | `cross_market_confirmation_flag` | 357420 | 0.921669 | 0.078331 | 0.078331 |
| 2021 | `ETH_NON_RTH` | `divergence` | `divergence_agreement` | `cross_market_divergence_flag` | 357420 | 0.921669 | 0.078331 | 0.078331 |
| 2021 | `ETH_NON_RTH` | `NQ/ES` | `lead_lag` | `cross_market_nq_es_rolling_correlation` | 357420 | 0.973409 | 0.026591 | 0.026591 |
| 2021 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 357420 | 0.716787 | 0.283213 | 0.283213 |
| 2021 | `ETH_NON_RTH` | `risk_on` | `relative_strength_rank` | `cross_market_risk_on_rotation_proxy` | 357420 | 0.921669 | 0.078331 | 0.078331 |
| 2022 | `ETH_NON_RTH` | `ES:NQ:RTY` | `aligned_returns` | `cross_market_synchronized_returns` | 356033 | 0.949811 | 0.050189 | 0.050189 |
| 2022 | `ETH_NON_RTH` | `NQ-ES` | `basket_residual` | `cross_market_nq_minus_es_return_spread` | 356033 | 0.994411 | 0.005589 | 0.005589 |
| 2022 | `ETH_NON_RTH` | `RTY-ES` | `basket_residual` | `cross_market_rty_minus_es_return_spread` | 356033 | 0.949873 | 0.050127 | 0.050127 |
| 2022 | `ETH_NON_RTH` | `NQ/ES` | `beta_residual` | `cross_market_nq_es_rolling_beta_residual` | 356033 | 0.991973 | 0.008027 | 0.008027 |
| 2022 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 356033 | 0.801667 | 0.198333 | 0.198333 |
| 2022 | `ETH_NON_RTH` | `risk_off` | `catch_up_rotation` | `cross_market_risk_off_rotation_proxy` | 356033 | 0.949811 | 0.050189 | 0.050189 |
| 2022 | `ETH_NON_RTH` | `confirmation` | `divergence_agreement` | `cross_market_confirmation_flag` | 356033 | 0.949811 | 0.050189 | 0.050189 |
| 2022 | `ETH_NON_RTH` | `divergence` | `divergence_agreement` | `cross_market_divergence_flag` | 356033 | 0.949811 | 0.050189 | 0.050189 |
| 2022 | `ETH_NON_RTH` | `NQ/ES` | `lead_lag` | `cross_market_nq_es_rolling_correlation` | 356033 | 0.991973 | 0.008027 | 0.008027 |
| 2022 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 356033 | 0.801667 | 0.198333 | 0.198333 |
| 2022 | `ETH_NON_RTH` | `risk_on` | `relative_strength_rank` | `cross_market_risk_on_rotation_proxy` | 356033 | 0.949811 | 0.050189 | 0.050189 |
| 2023 | `ETH_NON_RTH` | `ES:NQ:RTY` | `aligned_returns` | `cross_market_synchronized_returns` | 356040 | 0.936996 | 0.063004 | 0.063004 |
| 2023 | `ETH_NON_RTH` | `NQ-ES` | `basket_residual` | `cross_market_nq_minus_es_return_spread` | 356040 | 0.990698 | 0.009302 | 0.009302 |
| 2023 | `ETH_NON_RTH` | `RTY-ES` | `basket_residual` | `cross_market_rty_minus_es_return_spread` | 356040 | 0.937097 | 0.062903 | 0.062903 |
| 2023 | `ETH_NON_RTH` | `NQ/ES` | `beta_residual` | `cross_market_nq_es_rolling_beta_residual` | 356040 | 0.976376 | 0.023624 | 0.023624 |
| 2023 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 356040 | 0.764035 | 0.235965 | 0.235965 |
| 2023 | `ETH_NON_RTH` | `risk_off` | `catch_up_rotation` | `cross_market_risk_off_rotation_proxy` | 356040 | 0.936996 | 0.063004 | 0.063004 |
| 2023 | `ETH_NON_RTH` | `confirmation` | `divergence_agreement` | `cross_market_confirmation_flag` | 356040 | 0.936996 | 0.063004 | 0.063004 |
| 2023 | `ETH_NON_RTH` | `divergence` | `divergence_agreement` | `cross_market_divergence_flag` | 356040 | 0.936996 | 0.063004 | 0.063004 |
| 2023 | `ETH_NON_RTH` | `NQ/ES` | `lead_lag` | `cross_market_nq_es_rolling_correlation` | 356040 | 0.976376 | 0.023624 | 0.023624 |
| 2023 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 356040 | 0.764035 | 0.235965 | 0.235965 |
| 2023 | `ETH_NON_RTH` | `risk_on` | `relative_strength_rank` | `cross_market_risk_on_rotation_proxy` | 356040 | 0.936996 | 0.063004 | 0.063004 |
| 2024 | `ETH_NON_RTH` | `ES:NQ:RTY` | `aligned_returns` | `cross_market_synchronized_returns` | 347084 | 0.932103 | 0.067897 | 0.067897 |
| 2024 | `ETH_NON_RTH` | `NQ-ES` | `basket_residual` | `cross_market_nq_minus_es_return_spread` | 347084 | 0.998260 | 0.001740 | 0.001740 |
| 2024 | `ETH_NON_RTH` | `RTY-ES` | `basket_residual` | `cross_market_rty_minus_es_return_spread` | 347084 | 0.932270 | 0.067730 | 0.067730 |
| 2024 | `ETH_NON_RTH` | `NQ/ES` | `beta_residual` | `cross_market_nq_es_rolling_beta_residual` | 347084 | 0.985551 | 0.014449 | 0.014449 |
| 2024 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 347084 | 0.755056 | 0.244944 | 0.244944 |
| 2024 | `ETH_NON_RTH` | `risk_off` | `catch_up_rotation` | `cross_market_risk_off_rotation_proxy` | 347084 | 0.932103 | 0.067897 | 0.067897 |
| 2024 | `ETH_NON_RTH` | `confirmation` | `divergence_agreement` | `cross_market_confirmation_flag` | 347084 | 0.932103 | 0.067897 | 0.067897 |
| 2024 | `ETH_NON_RTH` | `divergence` | `divergence_agreement` | `cross_market_divergence_flag` | 347084 | 0.932103 | 0.067897 | 0.067897 |
| 2024 | `ETH_NON_RTH` | `NQ/ES` | `lead_lag` | `cross_market_nq_es_rolling_correlation` | 347084 | 0.985551 | 0.014449 | 0.014449 |
| 2024 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 347084 | 0.755056 | 0.244944 | 0.244944 |
| 2024 | `ETH_NON_RTH` | `risk_on` | `relative_strength_rank` | `cross_market_risk_on_rotation_proxy` | 347084 | 0.932103 | 0.067897 | 0.067897 |
| 2025 | `ETH_NON_RTH` | `ES:NQ:RTY` | `aligned_returns` | `cross_market_synchronized_returns` | 345700 | 0.941281 | 0.058719 | 0.058719 |
| 2025 | `ETH_NON_RTH` | `NQ-ES` | `basket_residual` | `cross_market_nq_minus_es_return_spread` | 345700 | 0.996109 | 0.003891 | 0.003891 |
| 2025 | `ETH_NON_RTH` | `RTY-ES` | `basket_residual` | `cross_market_rty_minus_es_return_spread` | 345700 | 0.941496 | 0.058504 | 0.058504 |
| 2025 | `ETH_NON_RTH` | `NQ/ES` | `beta_residual` | `cross_market_nq_es_rolling_beta_residual` | 345700 | 0.990648 | 0.009352 | 0.009352 |
| 2025 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 345700 | 0.779398 | 0.220602 | 0.220602 |
| 2025 | `ETH_NON_RTH` | `risk_off` | `catch_up_rotation` | `cross_market_risk_off_rotation_proxy` | 345700 | 0.941281 | 0.058719 | 0.058719 |
| 2025 | `ETH_NON_RTH` | `confirmation` | `divergence_agreement` | `cross_market_confirmation_flag` | 345700 | 0.941281 | 0.058719 | 0.058719 |
| 2025 | `ETH_NON_RTH` | `divergence` | `divergence_agreement` | `cross_market_divergence_flag` | 345700 | 0.941281 | 0.058719 | 0.058719 |
| 2025 | `ETH_NON_RTH` | `NQ/ES` | `lead_lag` | `cross_market_nq_es_rolling_correlation` | 345700 | 0.990648 | 0.009352 | 0.009352 |
| 2025 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 345700 | 0.779398 | 0.220602 | 0.220602 |
| 2025 | `ETH_NON_RTH` | `risk_on` | `relative_strength_rank` | `cross_market_risk_on_rotation_proxy` | 345700 | 0.941281 | 0.058719 | 0.058719 |
| 2026 | `ETH_NON_RTH` | `ES:NQ:RTY` | `aligned_returns` | `cross_market_synchronized_returns` | 140640 | 0.973549 | 0.026451 | 0.026451 |
| 2026 | `ETH_NON_RTH` | `NQ-ES` | `basket_residual` | `cross_market_nq_minus_es_return_spread` | 140640 | 0.999566 | 0.000434 | 0.000434 |
| 2026 | `ETH_NON_RTH` | `RTY-ES` | `basket_residual` | `cross_market_rty_minus_es_return_spread` | 140640 | 0.973642 | 0.026358 | 0.026358 |
| 2026 | `ETH_NON_RTH` | `NQ/ES` | `beta_residual` | `cross_market_nq_es_rolling_beta_residual` | 140640 | 0.997227 | 0.002773 | 0.002773 |
| 2026 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 140640 | 0.859748 | 0.140252 | 0.140252 |
| 2026 | `ETH_NON_RTH` | `risk_off` | `catch_up_rotation` | `cross_market_risk_off_rotation_proxy` | 140640 | 0.973549 | 0.026451 | 0.026451 |
| 2026 | `ETH_NON_RTH` | `confirmation` | `divergence_agreement` | `cross_market_confirmation_flag` | 140640 | 0.973549 | 0.026451 | 0.026451 |
| 2026 | `ETH_NON_RTH` | `divergence` | `divergence_agreement` | `cross_market_divergence_flag` | 140640 | 0.973549 | 0.026451 | 0.026451 |
| 2026 | `ETH_NON_RTH` | `NQ/ES` | `lead_lag` | `cross_market_nq_es_rolling_correlation` | 140640 | 0.997227 | 0.002773 | 0.002773 |
| 2026 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 140640 | 0.859748 | 0.140252 | 0.140252 |
| 2026 | `ETH_NON_RTH` | `risk_on` | `relative_strength_rank` | `cross_market_risk_on_rotation_proxy` | 140640 | 0.973549 | 0.026451 | 0.026451 |

## Strict-Intersection Survival

| Year | Session | Panel rows | ES grid | NQ grid | RTY grid | Survival vs min | Survival vs max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019 | `ETH_NON_RTH` | 356040 | 356040 | 356040 | 356040 | 1.000000 | 1.000000 |
| 2020 | `ETH_NON_RTH` | 357300 | 357300 | 357300 | 357300 | 1.000000 | 1.000000 |
| 2021 | `ETH_NON_RTH` | 357420 | 357420 | 357420 | 357420 | 1.000000 | 1.000000 |
| 2022 | `ETH_NON_RTH` | 356033 | 356040 | 356040 | 356033 | 1.000000 | 0.999980 |
| 2023 | `ETH_NON_RTH` | 356040 | 356040 | 356040 | 356040 | 1.000000 | 1.000000 |
| 2024 | `ETH_NON_RTH` | 347084 | 347085 | 347085 | 347084 | 1.000000 | 0.999997 |
| 2025 | `ETH_NON_RTH` | 345700 | 345705 | 345703 | 345700 | 1.000000 | 0.999986 |
| 2026 | `ETH_NON_RTH` | 140640 | 140640 | 140640 | 140640 | 1.000000 | 1.000000 |

## Availability Discipline Re-Verification

The contributor-gap column counts panel rows where at least one ES/NQ/RTY `base_ohlcv_log_returns` row did not resolve by exact `event_ts`. It is not a count of forward-filled rows, and it is not smoothed away; those rows remain availability context for downstream diagnostics.

| Year | Panel rows checked | Panel rows missing >=1 exact contributor | Panel available before contributor | Duplicate panel event_ts | Panel FeatureVersion |
| --- | --- | --- | --- | --- | --- |
| 2019 | 356040 | 27481 | 0 | 0 | `fver_ce1dda97cd91f4b20bcd49bf559e7438c552880355bd0c491a8fa5ba583b7662` |
| 2020 | 357300 | 19402 | 0 | 0 | `fver_c811e8bab0c98738a3825c4a6a232ef121a51df1fab00cc369151fe1c7b873ce` |
| 2021 | 357420 | 17643 | 0 | 0 | `fver_242ecff9a649e42320f9ed14d71f96333fe689f08ea48e561530c87645007488` |
| 2022 | 356033 | 10893 | 0 | 0 | `fver_d1df1621563daab1c61e4081c526c7c9421b59114c08b77cc6edabb17b2aae09` |
| 2023 | 356040 | 13800 | 0 | 0 | `fver_0ac6b9b142fc3244d8f1b03f24e77a591f516a2ad962ab12f7879918ce572c65` |
| 2024 | 347084 | 13711 | 0 | 0 | `fver_65bc052a7d8372b90322a2c69013d29317a5ea4e22cc94961fca784eb8d86b1a` |
| 2025 | 345700 | 12218 | 0 | 0 | `fver_a1e90307d723b4a49d687bf3896c6b8cbe1612050bb6a9a9c66c1ba0a97beaac` |
| 2026 | 140640 | 2059 | 0 | 0 | `fver_de52dc9917b23cfe98bc6e8018f9ae21503531f85e6ea7db5f27b4c660b39740` |

Result: the read-only all-row check found the exact `event_ts` contributor gaps listed above, zero panel rows whose `available_ts` preceded any resolved contributor `available_ts`, and zero duplicate panel `event_ts` in the registered `cross_market_synchronized_returns` panel rows. The nonzero contributor-gap counts are recorded as cross-market availability context, not estimated around or presented as filled substrate coverage.

## Thin Or Absent Coverage Context

Lowest non-null state/session cells. These are availability and state-coverage context only.

| Year | Session | Scope | State | Feature | Rows | Non-null | Gap rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 356040 | 0.615358 | 0.384642 |
| 2019 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 356040 | 0.615358 | 0.384642 |
| 2021 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 357420 | 0.716787 | 0.283213 |
| 2021 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 357420 | 0.716787 | 0.283213 |
| 2020 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 357300 | 0.750792 | 0.249208 |
| 2020 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 357300 | 0.750837 | 0.249163 |
| 2024 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 347084 | 0.755056 | 0.244944 |
| 2024 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 347084 | 0.755056 | 0.244944 |
| 2023 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 356040 | 0.764035 | 0.235965 |
| 2023 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 356040 | 0.764035 | 0.235965 |
| 2025 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 345700 | 0.779398 | 0.220602 |
| 2025 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 345700 | 0.779398 | 0.220602 |
| 2022 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 356033 | 0.801667 | 0.198333 |
| 2022 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 356033 | 0.801667 | 0.198333 |
| 2026 | `ETH_NON_RTH` | `RTY/ES` | `beta_residual` | `cross_market_rty_es_rolling_beta_residual` | 140640 | 0.859748 | 0.140252 |
| 2026 | `ETH_NON_RTH` | `RTY/ES` | `lead_lag` | `cross_market_rty_es_rolling_correlation` | 140640 | 0.859748 | 0.140252 |

## Registry Identities Used

Each row lists the exact cross-market FeatureVersions used for the matrix and the base-return FeatureVersions used for the availability-discipline check.

| Year | Partition | Panel DatasetVersion | Input DatasetVersions | Cross-market FeatureVersions | Base-return check FeatureVersions |
| --- | --- | --- | --- | --- | --- |
| 2019 | `ES_NQ_RTY_2019_full_year` | `dsv_databento_ohlcv_dense_2019_v1` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b:ACCEPTED_WITH_WARNINGS`<br>`ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2019_v1:ACCEPTED` | `fver_ce1dda97cd91f4b20bcd49bf559e7438c552880355bd0c491a8fa5ba583b7662`<br>`fver_cdf6c1963304c11b3c543c5715d91c25fe5e0e710a70a4b77a17fd91a430ba5e`<br>`fver_0473f9b25cf766d096fa2bc45aca0e39429a5fddd7329ade9ce6bd4f6a51e062`<br>`fver_06982c98991e937e440ab61466e2e6453ebd7e6e4814ce7b7a343169715082f9`<br>`fver_dccb437fb8611abc9cfa5af14ef378fc8e2c6f18b5da41cb925e36810d9998bb`<br>`fver_12b0a34b26bdec250c71b6657eb7a98740b517ff5efe3cb287e4a1ae3b2721cd`<br>`fver_70238176909b963087d7b910169dd4e05ff65abc64c20dfe9faa5b26a3d7bc29`<br>`fver_db22e6f82796c6817ff36743513a46342c06130c9c6f6799e5026752be25cae0`<br>`fver_c8e229f1b513fd5c7e797d3f0d56a33b67612440d14a876f5e92c96d0afc40c7`<br>`fver_3387ca49b318668fadc66317383219314ce6d72926aac427cd9e170e15f6ad78`<br>`fver_35e149a3c0575352bb914d61b5f62f009553c7af252165b3dff6599858b7e3f5` | `fver_f0cb850fbd61c91335b81585fb13d8824324c7c6fded2be237c24df3ed52e018`<br>`fver_7b2517b96a1af1d11352740ae1e203351991c76500fbd32a31983249b5a49202`<br>`fver_cc6f6bfa156f2a0cc9b2d95ec19c633bd63b92285914b226fa07c6135250b718` |
| 2020 | `ES_NQ_RTY_2020_full_year` | `dsv_databento_ohlcv_dense_2020_v1` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850:ACCEPTED`<br>`ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2020_v1:ACCEPTED` | `fver_c811e8bab0c98738a3825c4a6a232ef121a51df1fab00cc369151fe1c7b873ce`<br>`fver_4c73f552d26c18e98dd938db2e67bf62c206ecf1201f0aee3084419892d5c308`<br>`fver_b41a062ef18772e93a073edf657bf122f63193dafa4cb6c9c225166bb908bccf`<br>`fver_5bbaa5f845794a3b36bfa9c03cd0480f3526c3b62db4f23a4036b745fc2be93e`<br>`fver_9ae0ac7aca54d930c205cb07861b44081a4317e14e7904718fd555084110e190`<br>`fver_4f0c864258c40536e06b3fc00c7d7f151dabe9ec53a1a4e2fc36f74e32a2e72f`<br>`fver_f521f390d49edaffb8e910a618ce2ce86e70ebc8d4222e85a49b6fdfcbb3da4f`<br>`fver_53e1e9dfadadbfc7690b07bcbfdcbbddf71ebd3b25ae568fff3f410ca34b319e`<br>`fver_6d95462926f5a7716f863c2095da4f646c26d403ff784fe7dfead68eab8c6ade`<br>`fver_ac47a1d0e904922f4b6a14c31b45bbb5bf314e1c67685f9a38e4af0eb24a6bf5`<br>`fver_73fbe4baebd820a1a0dc11201e8806e02e573adacd35232c42ee026c67722dc8` | `fver_6d386235dac4815b9d2bc5dd95e973f7f66b30b794f9328c44646edc849b2039`<br>`fver_a329d3fe79dd6279af7ee68c8b45a2b7ec286599a1afead3b8dd2c546a11198e`<br>`fver_89afb53713fd8cb24fadac937b58653edc0ab568ef81b9dbe8732a0d66c06a43` |
| 2021 | `ES_NQ_RTY_2021_full_year` | `dsv_databento_ohlcv_dense_2021_v1` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691:ACCEPTED`<br>`ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2021_v1:ACCEPTED` | `fver_242ecff9a649e42320f9ed14d71f96333fe689f08ea48e561530c87645007488`<br>`fver_0d24cb347ef2a5ff36985de3fe2b64dcc94f1c179c3bb2a4b9441412f9f45160`<br>`fver_ce9ab5315ad0fbd139cb787ea834dc50387941ed6e3c0ba3d2750ac921607de1`<br>`fver_89c18a42b411a5864c3fd712344c3880009a3f907534faf33dc596c7ac097630`<br>`fver_fa65b620dff944b929bf1f6d1c3085eb0e9692b81d482b550f73f03924ad5895`<br>`fver_dd2d7aa1635ce3fd1abf9ffea9b44f87c2ccf3887212b2953d153249c61b7911`<br>`fver_45bd9b589b18ac0a01e381fe841b964ce7f0dfe003668abe7e371aa43a057d25`<br>`fver_afd55e5176585c054ec77b58d6ca52552acc91dae5737ed0330a22ec77da07a1`<br>`fver_516b6a92422436ed487e8335c6f0a5f06b227822d1116d5bbef32fe2839c67d3`<br>`fver_e5582c9fa6a4bf6edc52efd230f7281518aef37a8ecf2f97d97831b397409770`<br>`fver_38c1dcf180c1f3e7565900f3ae204c0a82ea4f908be9c55d284f85648c9d55a3` | `fver_7ac41f4913bdd1db5c785364fccccf6f08fb572bee99f5e2e16fd7bf6d7d1830`<br>`fver_aed1a47af3d80699ced20dd0443f972ed03882a0b4e72a2a039c0c2ecba14748`<br>`fver_a1ef06fbfe5a19d70ab71c3e46c970d20bbe81e4819d26ec4e483f228b21ec3f` |
| 2022 | `ES_NQ_RTY_2022_full_year` | `dsv_databento_ohlcv_dense_2022_v1` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe:ACCEPTED`<br>`ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2022_v1:ACCEPTED` | `fver_d1df1621563daab1c61e4081c526c7c9421b59114c08b77cc6edabb17b2aae09`<br>`fver_66d02fc1dec7ab6d159090307ae7fe7a52b8815fb34a058317f67360c5010122`<br>`fver_b0af1c3003206dc6827665c49e913a1113cc1750c1cd3fb4b4736daca62473b7`<br>`fver_ab4b77e25408f9c92e92800d84d39c36b2a60ee6c929c04c1e0eb4df910e30f1`<br>`fver_151d0de3d14749caac0990885f7e30802eceea0257d54a5fab39950a4328b4ab`<br>`fver_5b83a4f34dc41d933510c43f00f1e3bba58cf0cacaf3075306c1b5ee2b47377d`<br>`fver_ba317342f150b546dba99ad06c0a8fdacddc4aff1d76fb547c5ad8038f9dda21`<br>`fver_6e9f162df69914b86caebbe7b0a5fce3ae1e3736e9d7fdef05a7b7abf2432d31`<br>`fver_baa061929b1073c3a030eb915d0c30cfd6b17b04678c8ce435a46f09059f690a`<br>`fver_0079ad7ee379c480023542feda4f0fed1c15bb77a0ebd08d0b1a6e783d85f9a8`<br>`fver_42d3124e882abe6feb653a30cdd001dc05cd3bd035b68019d520209405d276fc` | `fver_2b450c32f2f3fb286afe5695ce6f47006ae839d938a6333bbf011dfcf767b755`<br>`fver_afd87f7b6488f127d030237cb48948284fdef5964a6017dd0dc786fb09dafea5`<br>`fver_1d8355c45f8a673eeb52d4bc8a507cf8e84bb7fc1a271318a51751a121013bff` |
| 2023 | `ES_NQ_RTY_2023_full_year` | `dsv_databento_ohlcv_dense_2023_v1` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774:ACCEPTED`<br>`ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2023_v1:ACCEPTED` | `fver_0ac6b9b142fc3244d8f1b03f24e77a591f516a2ad962ab12f7879918ce572c65`<br>`fver_880008517761355d78de79f2fc9b8a7d5d1a57e15d658db4091d849315036fd9`<br>`fver_15b1fdfc4dee470ab89e678d895ea7fc9e77d3337edd2feb904380eadc583026`<br>`fver_4b01771fd5a01427233a75ca92b4d94459721dd52c3fb3996a03b323ca00390a`<br>`fver_ff3c7a92fe68164a35b5b71f3cfe9ee1aa5b6f800f9d40a6bf616200316e5d9c`<br>`fver_b05c53750f379df97c54c7c393516165ef21cfa9d3056541cc156e5e05936127`<br>`fver_e4e4563e66d7c83856830a6b4306f371187ae4de6133ef74551ed8840c8ff146`<br>`fver_e3b57f97b24bbb5db317ef6915d12453b1721f1cf36dc4d8ab749cc6b9860f6d`<br>`fver_12387ca3f983295146576703c7fd1e9ba8e41489a261974c99a0adf01fd50127`<br>`fver_bf613fb110f19dbfbefedcae4f33491343f4582907a03e669e2531560a572ab6`<br>`fver_2e3781b0770228287a58e58856f0a58e95fab430c18ca89333f47b762333c54c` | `fver_7a3f6ce01ff40069ae4c91a6ad0bb31bb5aba856d0491b3ca09229b26389304b`<br>`fver_708a870303393692be6d07f3cf5030a48112e7316749999822cb904eec0c9e20`<br>`fver_d1150b7e74b2ac6f96158384ba91352ae9dd083b675add85df3cbb8350db126c` |
| 2024 | `ES_NQ_RTY_2024_full_year` | `dsv_databento_ohlcv_dense_2024_v1` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0:ACCEPTED`<br>`ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2024_v1:ACCEPTED` | `fver_65bc052a7d8372b90322a2c69013d29317a5ea4e22cc94961fca784eb8d86b1a`<br>`fver_6ae9a54d4cd0b08add3b635e2ec3fa4014625383fe9d7018d2d2a162a5c9ceda`<br>`fver_09e6ce6480f6c22aae71145ef115a573ac8cff09197d9eae71b509acee660fa3`<br>`fver_921a962a906efaadd2c7812610679dc987a76c95c5fb76b46ac82914a2cb999b`<br>`fver_693704d36430cf7ff842b57ec78d87f5be9e6692f19a81e3cda15fadf94529d1`<br>`fver_bacd82e2b2a873ca162859e15d22634bc7d350fd8d3cc3f9c418b449d37dc64c`<br>`fver_9ed797cf41de2d25c7add5ad1de37ff12e6df6fc7146ccdfdf84ba9197c54475`<br>`fver_b9d318eb8342a911c191d0622b869d17255702b3183351a0bb45fdeb0e0c31aa`<br>`fver_6e8aa35cc88f66165273f56c006e89dcb024e4ffb84dc7191731839c481c7b3e`<br>`fver_5f27368f8a583e5b2e19650eff63d2c6815bee9eccdf594eae2fcb5b8c0783d3`<br>`fver_c7124d0bc9192f838a763dd02a284a79dfbb8b032123a0033118d3e6b1c3af9e` | `fver_c179f00635ee5e96d8a9adafb4ffa5a856bc6fd1642d130e458e7bbbd56f56bf`<br>`fver_3215a58d2c8c92afa1c5748bb68771f957697e837625f5fced0907825fd839a3`<br>`fver_d62a761fae7bfbb1da27ce6295c437513c4324ec9bf5a4abbbbf8521995b7da2` |
| 2025 | `ES_NQ_RTY_2025_full_year` | `dsv_databento_ohlcv_dense_2025_v1` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd:ACCEPTED`<br>`ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2025_v1:ACCEPTED` | `fver_a1e90307d723b4a49d687bf3896c6b8cbe1612050bb6a9a9c66c1ba0a97beaac`<br>`fver_6bd1224fcb6cbde59f9051b9fcfb4bc19726bdad0ef9112a16180933580834c9`<br>`fver_dbeadec5ec721feb8684eb936c40e4b56331a93d7d073b45038b77122be57265`<br>`fver_e802c7a23d6a1625e7c0f68532f8c2840c0933ceda97b8efb454ddb86d1a342c`<br>`fver_d5344912cf14f01ef844e815df5e272680aae0a55e18e341d01755f38a56b956`<br>`fver_e2dee14fbe106e906f5219f02c2709531e829958a043122ca732e0d0e548aa4b`<br>`fver_26563f91497a55502d5d64228f5546c3bf26685ca6a54eccd25748fa2fd9cf36`<br>`fver_8df45bcfb8b0c4e092342145771fe0d4ec9a2f4465b80a715700f158cb96975f`<br>`fver_cab77998e46be8980c6586ad6dc877b454a0aceb77ae1f94caf6730fba1cc971`<br>`fver_eb4f292d02f27e5c878c9a9d47bec1c6878a42c8c58742eb14dfff98fb820368`<br>`fver_18c858795d98f4c079412fa77bf8467f893a7c2f46389413a75ff1fe71a753a7` | `fver_850309cd6522d7837f32d07bbb2a6316edb274c0162dbe69e273c33d83fe520d`<br>`fver_a42160651598041f72c9c1f6e114d1c95b268c5ab90c7595fd1af67dfb0672ab`<br>`fver_a3f90b568ba7ffed371c55be68556af7fde7a680b86149cf1b1674f8cfbeeeab` |
| 2026 | `ES_NQ_RTY_2026_full_year` | `dsv_databento_ohlcv_dense_2026_v1` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b:ACCEPTED_WITH_WARNINGS`<br>`ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2026_v1:ACCEPTED_WITH_WARNINGS` | `fver_de52dc9917b23cfe98bc6e8018f9ae21503531f85e6ea7db5f27b4c660b39740`<br>`fver_762882635b5c80ee4b6a7794a866e3a18ddc7d3fa0743f34f12a6679774cd191`<br>`fver_32c26edf742e5b1e1e954169d6934889d06d3fa9c790e0c33965f65c343cb76d`<br>`fver_9b8a8593cc3434881b6c875829272008a264bd525eeab807f5f2af4a87e03d2b`<br>`fver_fa06c761766848070692ad086c543f446c783ee3ef8d8b779b645f2a2d3e00a6`<br>`fver_7884f34c3c45a11cfe9b9353ba1da11646a414edac618b8b06aecd36eb2deecb`<br>`fver_37494c4fcb0dfbb1d6fc0c2da0b02057afa6559f60151ac08bd5e5fad2a0b101`<br>`fver_17569d992b6875b0ef36e5846f678d61af4e4b518129d6aa0806eeb93fb121d3`<br>`fver_f0e2c14a2e6fe78a0d6d6546e9c6ad0d4dbe7b36f517945a65fc0009a14cdf7c`<br>`fver_f7b490f2bb5992112d08b4bdccfa17ba77293998119fd5bc17d3834d312c4b79`<br>`fver_57a86805019963c6ebb97c0408afb2a68ec61a7f65a580b8cbf43ec80854f997` | `fver_73899c357f7dabfb8a27fc92e74acbe8ae15a955b36558a241c3d226027f711b`<br>`fver_d6fe27e42030b6288309459c90538bb5310f551cea93008dc6b933fba41c48a9`<br>`fver_b535ec2cd0f8a7e06eb7dd56629c2e1ed576bd735794397a2279927736fe5152` |

## Explicit Exclusions

- 2018 is expected-excluded because the required `ohlcv_1m` and dense-grid DatasetVersions are `BLOCKED` under the FUTSUB-P02 acceptance policy. The RTY-2018 sparse-history issue is the binding acceptance context, and ES/NQ 2018 panel values are not fabricated.
- 2019 and 2026 retain accepted-with-warnings context; 2026 is partial-year.

This matrix contains counts, rates, shares, state labels, and registry identities only. It contains no per-row feature values, prices, returns, provider payloads, local SQLite content, Parquet payloads, or `asof`-aligned aggregates.
