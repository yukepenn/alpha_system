# FUTCORE-P14 StudySpec Index

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P14`  
Artifact type: value-free Approved StudySpec Pack

This index maps the 10 `FUTCORE-P12` accepted AlphaSpecs to exactly one governance `StudySpec` each. The canonical JSON pack is `study_specs.json`, and each StudySpec is also materialized as an individual `sspec_*.json` file for handle-level consumption. Every object validates with `alpha_system.governance.study_spec.validate_study_spec`.

## Traceability Map

| AlphaSpec id | StudySpec id | Family | Source | P13 mapping | P15 gaps carried | Variant budget |
| --- | --- | --- | --- | --- | --- | ---: |
| `aspec_0ebd90cecfd475607685b445` | `sspec_dde3e64667fe158f9bad527d` | `cross_market` | `research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_01_nq_leads_es_completed_bar_context.json` | `AVAILABLE_BUT_NEEDS_REVIEW` | no P15 gap for locked 5m baseline | `4` |
| `aspec_8d9e272e4b78eedcd27f0bec` | `sspec_c671fbeeb143512cbc03bc5b` | `cross_market` | `research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_05_nq_beta_residual_vs_es_rty_basket.json` | `MISSING` | P15-G3 | `4` |
| `aspec_a41dcccac5552de945aba825` | `sspec_90b28233d828128664588a9a` | `cross_market` | `research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_10_rty_catchup_rotation_context.json` | `MISSING` | P15-G1, P15-G3 | `4` |
| `aspec_fa4895a43a80d4eef0a607a4` | `sspec_7c8fb13628843890c171b122` | `cross_market` | `research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_14_nq_es_divergence_context.json` | `MISSING` | P15-G3 | `4` |
| `aspec_b40aee52d4399dd5b855a6ed` | `sspec_69c22ec5847395ac8e81b5b6` | `vwap_session` | `research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_01.md` | `MISSING` | P15-G1, P15-G2 | `4` |
| `aspec_43cd6c154bca2fcc419eee83` | `sspec_aff70fcbc4b7ff226fcc8149` | `vwap_session` | `research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_07.md` | `MISSING` | P15-G1, P15-G2 | `4` |
| `aspec_eb962fc197eaf3955c5e4711` | `sspec_267cc052e37668339c38d179` | `regime` | `research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_01.md` | `MISSING` | P15-G1, P15-G4 | `4` |
| `aspec_df2d040e45564c259ef3de6d` | `sspec_27bf1262b0bd23d27191cc86` | `liquidity_pa` | `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_02.md` | `MISSING` | P15-G1, P15-G4 | `4` |
| `aspec_39ffc190cfbfa6ba0b1a2a25` | `sspec_02c400a561891171a33c0c66` | `liquidity_pa` | `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_06.md` | `MISSING` | P15-G1, P15-G4 | `4` |
| `aspec_1284e49b083df11eeb0481ea` | `sspec_9f6f741192a4b534f06e51c0` | `bbo_tradability` | `research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/FUTCORE-P11_bbo_tradability_01.md` | `MISSING` | P15-G1, P15-G5 | `4` |

## Pack Binding

- DatasetVersion: `dsv_databento_ohlcv_05404069799decb0`; manifest hash `abbf9ebbecfe97f2c4b31900d9ae44421549e08a65e90ec64e235a958c1d2d31`; code hash `87fb8de7760c3635fb883948971bc12ee21ed64562713975bb20028ae3f92139`; config hash `206bc27869bcedfde89e483828534c5778bb72cf7e66b69a9d3304c7e7f03b5b`; quality report hash `7e46966bdc6921a0bb338097fa82ec94fcdf401e1913d81b288052bd6c9c66b4`.
- FeaturePack refs are bound by P13 availability mapping from the P03 lock, including session context (`F1`, `F2`) and the required base OHLCV primitives (`F3` through `F8`) where each accepted AlphaSpec needs them. Each reference records the FeatureVersion id, FeatureRequest id, value-content hash, schema version, and available_ts window.
- LabelPack refs: `5m` `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` / `lspec_cd6523694c850c9943b2067e`; `10m` `lver_4170332f366d6945a37cfe8980395626c393b40c2e1c36944ffb784b88cc7941` / `lspec_15c26c4368bb432b0b0dc6e9`; `30m` `lver_69c9900cbac5e679f8d97d350e30f493f30a498eb3d47463e6ab9995f1c0310a` / `lspec_65ba5b5c9b4fa37e0e42b6ef`.
- `15m` remains pending `P15-G1`. `10m` and `30m` are not P15 gaps because P03/P13 resolve them with valid label_available_ts metadata.
- Parquet is the required research-scale side of the P03 lock; this pack records ids/hashes only and embeds no value rows or storage files.

## Family Budget Reconciliation

| Family | Required budget | StudySpecs | Share | Reconciliation |
| --- | ---: | ---: | ---: | --- |
| `cross_market` | 40% | 4 | 40% | Aligned with the P12 accepted allocation. |
| `vwap_session` | 20% | 2 | 20% | Aligned with the P12 accepted allocation. |
| `regime` | 15% | 1 | 10% | Matches the P12 integer-rounding note. |
| `liquidity_pa` | 15% | 2 | 20% | Matches the P12 integer-rounding note. |
| `bbo_tradability` | 10% | 1 | 10% | Aligned with the P12 accepted allocation. |
| **Total** | 100% | **10** | **100%** | Approved cap `<=10` is held. |

Each StudySpec declares `variant_budget: 4`; the two predeclared axes in each payload define at most four parameter combinations. Sessions, horizons, instruments, and cost profiles are fixed diagnostic/reporting slices and do not expand the variant grid.

## Boundary Notes

- Required sessions: `full_session`, `RTH_only`, `ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, `RTH`, `post_RTH`, and `RTH_with_ETH_context`.
- Primary horizons: `5m`, `10m`, `15m`, and `30m`; `1m` is sampling-only and `1m`/`3m` are execution-fragile diagnostics only with stricter cost, spread, liquidity, and timestamp gates.
- Cost profiles are `zero_cost`, `base`, `stress_1`, `stress_2`, and `double_cost`; thin-session penalties apply to `ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, and `post_RTH` on non-zero profiles.
- `zero_cost` is diagnostic-only contrast and cannot support any favorable continuation or survivor basis.
- No modeled holding period may cross the exchange daily maintenance or trade-date break.
- No diagnostics, feature/label values, market rows, costs, returns, signals, broker/live/paper/order behavior, review artifact, verdict, PR, merge, staging action, or phase approval is recorded here.
