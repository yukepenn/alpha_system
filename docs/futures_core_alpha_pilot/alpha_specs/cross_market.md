# Cross-Market AlphaSpec Family Index

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P07`  
Family: cross-market / relative value  
Drafter role: `Hypothesis Scout`

This index summarizes the value-free cross-market AlphaSpec draft batch.
The canonical draft payloads live under
`research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/`.
No diagnostics, market values, feature values, label values, approval,
implementation, or promotion decision is recorded here.

## Batch Bounds

- Draft count: `16`.
- P05 quota: minimum `12`, target `16`, maximum `16`.
- Family budget: `40%` of the 40-draft pilot cap.
- Universe: `ES`, `NQ`, `RTY` only.
- Cost model: `cmv_futcore_pilot_three_layer_session_stress_v1` with
  `zero_cost`, `base`, `stress_1`, `stress_2`, and `double_cost`;
  `zero_cost` is diagnostic-only and never a criterion basis.
- Required family diagnostics are declared in each payload: timestamp
  alignment, cross-market missingness, stale/late input handling,
  lead/lag or residual/rank/confirmation convention, and duplicate exposure.

## Draft Index

| # | File | AlphaSpec id | Hypothesis id | Sub-theme | Instruments | Primary horizon |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | `FUTCORE-P07_cross_market_01_nq_leads_es_completed_bar_context.json` | `aspec_0ebd90cecfd475607685b445` | `hyp_133f3df4e0c44c13675a71cb` | lead-lag | NQ, ES | 5m |
| 2 | `FUTCORE-P07_cross_market_02_es_leads_rty_completed_bar_context.json` | `aspec_a98c25c5b437e0906320ac56` | `hyp_631772a66d1d7c866576e56a` | lead-lag | ES, RTY | 5m |
| 3 | `FUTCORE-P07_cross_market_03_rty_leads_nq_risk_context.json` | `aspec_532c35c3e7571acf8c8f40d1` | `hyp_89ec34153cac980877ff49dd` | lead-lag | RTY, NQ | 5m |
| 4 | `FUTCORE-P07_cross_market_04_triad_lead_lag_cascade_context.json` | `aspec_c6a0645fbad79e0a263737a6` | `hyp_3e8f5c6ee360f239c768554f` | lead-lag | ES, NQ, RTY | 5m |
| 5 | `FUTCORE-P07_cross_market_05_nq_beta_residual_vs_es_rty_basket.json` | `aspec_8d9e272e4b78eedcd27f0bec` | `hyp_84b6642dd4b662f4e374282d` | beta-residual | NQ, ES, RTY | 10m |
| 6 | `FUTCORE-P07_cross_market_06_es_beta_residual_vs_nq_rty_basket.json` | `aspec_bd439bada940f95f45288535` | `hyp_fb6d890680faa487320da2d4` | beta-residual | ES, NQ, RTY | 10m |
| 7 | `FUTCORE-P07_cross_market_07_rty_beta_residual_vs_es_nq_basket.json` | `aspec_4fee1276b9f37cb75bd7be48` | `hyp_7b73717684ea50392f84dd9a` | beta-residual | RTY, ES, NQ | 10m |
| 8 | `FUTCORE-P07_cross_market_08_es_nq_pair_spread_beta_residual.json` | `aspec_0cc1c674fbe038809819be79` | `hyp_6b1fb5d7c43f19ff45606dec` | beta-residual | ES, NQ | 10m |
| 9 | `FUTCORE-P07_cross_market_09_nq_leadership_rotation_rank_context.json` | `aspec_677bf829db3937be87e8fff4` | `hyp_7d8821f081972f4a645c7f86` | rotation | NQ, ES, RTY | 15m |
| 10 | `FUTCORE-P07_cross_market_10_rty_catchup_rotation_context.json` | `aspec_a41dcccac5552de945aba825` | `hyp_7682ec9c4cfa0a2b54996d7d` | rotation | RTY, ES, NQ | 15m |
| 11 | `FUTCORE-P07_cross_market_11_defensive_rotation_between_es_nq_rty.json` | `aspec_4d5ebc78dc8269d8b8d2ca20` | `hyp_299450622ffc8a3c7cd6e580` | rotation | ES, NQ, RTY | 15m |
| 12 | `FUTCORE-P07_cross_market_12_triad_relative_strength_rank_turnover.json` | `aspec_b2243f2aa448902d9d99d386` | `hyp_2f91837e870b2c40fd63225e` | rotation | ES, NQ, RTY | 15m |
| 13 | `FUTCORE-P07_cross_market_13_es_nq_agreement_rty_confirmation_context.json` | `aspec_59b646fde9d11179bc4c0444` | `hyp_7e152c98cb6daa317c542adb` | confirmation-divergence | ES, NQ, RTY | 30m |
| 14 | `FUTCORE-P07_cross_market_14_nq_es_divergence_context.json` | `aspec_fa4895a43a80d4eef0a607a4` | `hyp_e5f43b3eda732aa7aae76b4b` | confirmation-divergence | NQ, ES | 30m |
| 15 | `FUTCORE-P07_cross_market_15_rty_nonconfirmation_broad_market_context.json` | `aspec_6fa402d0ecaaa3491c6a52cd` | `hyp_b5b940f3d90f1db7ea7967e7` | confirmation-divergence | RTY, ES, NQ | 30m |
| 16 | `FUTCORE-P07_cross_market_16_triad_dispersion_confirmation_context.json` | `aspec_a3a0979f1cb8d95982605a5c` | `hyp_4bc1d657a35b4ca65fcea388` | confirmation-divergence | ES, NQ, RTY | 30m |

## Review Notes For FUTCORE-P12

- The locked label pack exposes `lspec_cd6523694c850c9943b2067e` for the
  5m label. Drafts whose primary horizon is `10m`, `15m`, or `30m` declare
  a P13/P15 label audit gap rather than inventing LabelSpec ids.
- The broad triad drafts intentionally expose possible duplicate family
  exposure so the AlphaSpec Critic can accept, narrow, reject, or request
  revision without role ambiguity.
- These drafts remain research evidence only and do not claim profitability,
  tradability, paper/live readiness, production readiness, or capital fitness.
