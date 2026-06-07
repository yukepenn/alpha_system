# FUTCORE-P14 StudySpec Index

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P14`  
Artifact type: value-free Approved StudySpec Pack

This index maps the 10 `FUTCORE-P12` accepted AlphaSpecs to exactly one governance `StudySpec` each. The canonical JSON pack is `study_specs.json`; every object validates with `alpha_system.governance.study_spec.validate_study_spec` and carries a matching handle-only `StudyInputPack` shape.

## Traceability Map

| AlphaSpec id | StudySpec id | Family | Source | P13 mapping | P15 gaps carried | Variant budget |
| --- | --- | --- | --- | --- | --- | ---: |
| `aspec_0ebd90cecfd475607685b445` | `sspec_ac883ec0b962f4ae4f25e190` | `cross_market` | `research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_01_nq_leads_es_completed_bar_context.json` | `AVAILABLE_BUT_NEEDS_REVIEW` | none for locked 5m baseline | `4` |
| `aspec_8d9e272e4b78eedcd27f0bec` | `sspec_16f6de31387d8289d0fbb394` | `cross_market` | `research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_05_nq_beta_residual_vs_es_rty_basket.json` | `MISSING` | P15-G1, P15-G4 | `4` |
| `aspec_a41dcccac5552de945aba825` | `sspec_fc7b0408e59a83f2e69714d3` | `cross_market` | `research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_10_rty_catchup_rotation_context.json` | `MISSING` | P15-G2, P15-G4 | `4` |
| `aspec_fa4895a43a80d4eef0a607a4` | `sspec_6fe5fa12b333d19ea95915d2` | `cross_market` | `research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_14_nq_es_divergence_context.json` | `MISSING` | P15-G3, P15-G4 | `4` |
| `aspec_b40aee52d4399dd5b855a6ed` | `sspec_ab3cbb830a2cede5485de19b` | `vwap_session` | `research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_01.md` | `MISSING` | P15-G1, P15-G2, P15-G3, P15-G4 | `4` |
| `aspec_43cd6c154bca2fcc419eee83` | `sspec_8b8037013e7b3c14fd5b2844` | `vwap_session` | `research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_07.md` | `MISSING` | P15-G1, P15-G2, P15-G3, P15-G4 | `4` |
| `aspec_eb962fc197eaf3955c5e4711` | `sspec_28e943d62d4b2eb29a8c445f` | `regime` | `research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_01.md` | `MISSING` | P15-G1, P15-G2, P15-G3, P15-G4 | `4` |
| `aspec_df2d040e45564c259ef3de6d` | `sspec_b4f5d27095d4f419c078bbcc` | `liquidity_pa` | `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_02.md` | `MISSING` | P15-G1, P15-G2, P15-G3, P15-G4 | `4` |
| `aspec_39ffc190cfbfa6ba0b1a2a25` | `sspec_62f0ef13ec4f47c2f8c1c784` | `liquidity_pa` | `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_06.md` | `MISSING` | P15-G1, P15-G2, P15-G3, P15-G4 | `4` |
| `aspec_1284e49b083df11eeb0481ea` | `sspec_98d73578b6891eefe52eece5` | `bbo_tradability` | `research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/FUTCORE-P11_bbo_tradability_01.md` | `MISSING` | P15-G1, P15-G2, P15-G3, P15-G5 | `4` |

## Pack Binding

- DatasetVersion: `dsv_databento_ohlcv_05404069799decb0`; manifest hash `abbf9ebbecfe97f2c4b31900d9ae44421549e08a65e90ec64e235a958c1d2d31`; code hash `87fb8de7760c3635fb883948971bc12ee21ed64562713975bb20028ae3f92139`; config hash `206bc27869bcedfde89e483828534c5778bb72cf7e66b69a9d3304c7e7f03b5b`; quality report hash `7e46966bdc6921a0bb338097fa82ec94fcdf401e1913d81b288052bd6c9c66b4`.
- FeaturePack refs: `fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f` hash `sha256:58c42ab7515299d64ea4f90348290e88e3510849b3f31490a22f5a56638c7705`; `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978` hash `sha256:d953e7f4bd32998b0fc5d3db7e28b968dc25bf0896bc491b8fb5ba6442fc8278`.
- LabelPack ref: `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` / LabelSpec `lspec_cd6523694c850c9943b2067e` hash `sha256:abb5f53c7ede5f359a79541b237d71d44e79304ebbb6333a101a3c0588e32a9f`.
- Parquet side is the required research-scale side of the P03 lock; this pack records ids/hashes only and embeds no value rows.

## Family Budget Reconciliation

| Family | Required budget | StudySpecs | Share | Verdict |
| --- | ---: | ---: | ---: | --- |
| `cross_market` | 40% | 4 | 40% | PASS |
| `vwap_session` | 20% | 2 | 20% | PASS |
| `regime` | 15% | 1 | 10% | PASS with P12 integer-rounding note |
| `liquidity_pa` | 15% | 2 | 20% | PASS with P12 integer-rounding note |
| `bbo_tradability` | 10% | 1 | 10% | PASS |
| **Total** | 100% | **10** | **100%** | PASS; cap `<=10` held |

Each StudySpec declares `variant_budget: 4`; the two predeclared axes in each payload define at most four parameter combinations. Sessions, horizons, instruments, and cost profiles are fixed diagnostic/reporting slices and do not expand the variant grid.

## Boundary Notes

- `5m` binds to the locked `fwd_ret_5m` LabelPack reference. `10m`, `15m`, and `30m` remain pending `P15-G1`, `P15-G2`, and `P15-G3` before diagnostics may consume those labels.
- Derived OHLCV and BBO bindings remain pending `P15-G4` and `P15-G5` where listed. This pack does not implement them.
- `zero_cost` is diagnostic-only and cannot support a continuation, survivor, `WATCH`, or `CANDIDATE_RESEARCH` basis.
- `1m` is sampling-only and `1m`/`3m` are execution-fragile diagnostics only with stricter cost, spread, liquidity, and timestamp gates.
- No diagnostics, feature/label values, market rows, costs, returns, signals, promotions, broker/live/paper/order behavior, review artifact, verdict, PR, merge, or staging action is recorded here.
