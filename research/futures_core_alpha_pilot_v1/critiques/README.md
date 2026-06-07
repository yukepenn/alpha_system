# AlphaSpec Critique Index

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P12`  
Critic role: `AlphaSpec Critic:FUTCORE-P12`

This directory contains independent, value-free critique records for the
`FUTCORE-P07` through `FUTCORE-P11` AlphaSpec draft batches. The records critique
specification quality, duplicate exposure, no-lookahead routing, and budget fit
only. They do not implement, diagnose, promote, or make alpha, profitability,
tradability, paper/live, production, broker, or capital-allocation claims.

## Decision Counts

| Family | Drafts critiqued | Accept-for-StudySpec | Revise | Reject |
| --- | ---: | ---: | ---: | ---: |
| `cross_market` | 16 | 4 | 9 | 3 |
| `vwap_session` | 8 | 2 | 4 | 2 |
| `regime` | 6 | 1 | 4 | 1 |
| `liquidity_pa` | 6 | 2 | 4 | 0 |
| `bbo_tradability` | 4 | 1 | 3 | 0 |
| **Total** | **40** | **10** | **24** | **6** |

## Accepted Drafts

| Family | Accepted draft id | Critique record |
| --- | --- | --- |
| `cross_market` | `aspec_0ebd90cecfd475607685b445` | `cross_market/FUTCORE-P07_cross_market_01_nq_leads_es_completed_bar_context_critique.md` |
| `cross_market` | `aspec_8d9e272e4b78eedcd27f0bec` | `cross_market/FUTCORE-P07_cross_market_05_nq_beta_residual_vs_es_rty_basket_critique.md` |
| `cross_market` | `aspec_a41dcccac5552de945aba825` | `cross_market/FUTCORE-P07_cross_market_10_rty_catchup_rotation_context_critique.md` |
| `cross_market` | `aspec_fa4895a43a80d4eef0a607a4` | `cross_market/FUTCORE-P07_cross_market_14_nq_es_divergence_context_critique.md` |
| `vwap_session` | `aspec_b40aee52d4399dd5b855a6ed` | `vwap_session/FUTCORE-P08_vwap_session_01_critique.md` |
| `vwap_session` | `aspec_43cd6c154bca2fcc419eee83` | `vwap_session/FUTCORE-P08_vwap_session_07_critique.md` |
| `regime` | `aspec_eb962fc197eaf3955c5e4711` | `regime/FUTCORE-P09_regime_01_critique.md` |
| `liquidity_pa` | `aspec_df2d040e45564c259ef3de6d` | `liquidity_pa/FUTCORE-P10_liquidity_pa_02_critique.md` |
| `liquidity_pa` | `aspec_39ffc190cfbfa6ba0b1a2a25` | `liquidity_pa/FUTCORE-P10_liquidity_pa_06_critique.md` |
| `bbo_tradability` | `aspec_1284e49b083df11eeb0481ea` | `bbo_tradability/FUTCORE-P11_bbo_tradability_01_critique.md` |

All accepted records preserve the downstream routing flags for no-lookahead,
input-pack, BBO binding, and label binding audits. Acceptance here means
`accept-for-StudySpec` only; it is not a diagnostic result or promotion.
