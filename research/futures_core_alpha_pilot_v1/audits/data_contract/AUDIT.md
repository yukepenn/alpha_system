# FUTCORE-P13 Data Contract Audit

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P13`  
Audit type: value-free accepted-AlphaSpec to locked input-pack mapping  
Recorded on: 2026-06-07

This audit maps the 10 `accept-for-StudySpec` AlphaSpecs from `FUTCORE-P12` to
the DatasetVersion, FeaturePack, and LabelPack references locked by
`FUTCORE-P03`. It records ids, names, families, registry refs, and point-in-time
availability metadata only. It does not read value files, raw provider files,
Parquet rows, SQLite contents outside sanctioned registry APIs, or arbitrary
data paths.

The availability decision is intentionally pack-based. A primitive name that
exists in source code but is not registered in the locked `FUTCORE-P03`
FeaturePack or LabelPack is not marked `AVAILABLE` for this phase.

## Source Set

The accepted set is taken from
`research/futures_core_alpha_pilot_v1/alpha_specs/BUDGET_AUDIT.md`.

| Family | AlphaSpec id | Source draft | Accepted horizon/session context |
| --- | --- | --- | --- |
| `cross_market` | `aspec_0ebd90cecfd475607685b445` | `cross_market/FUTCORE-P07_cross_market_01_nq_leads_es_completed_bar_context.json` | NQ completed-bar context for later ES decision; primary `5m`; RTH/RTH_with_ETH_context plus diagnostic thin-session views. |
| `cross_market` | `aspec_8d9e272e4b78eedcd27f0bec` | `cross_market/FUTCORE-P07_cross_market_05_nq_beta_residual_vs_es_rty_basket.json` | NQ residual versus ES/RTY basket; primary `10m`; cross-instrument completed-bar alignment. |
| `cross_market` | `aspec_a41dcccac5552de945aba825` | `cross_market/FUTCORE-P07_cross_market_10_rty_catchup_rotation_context.json` | RTY catch-up rotation context; primary `15m`; cross-instrument completed-bar alignment. |
| `cross_market` | `aspec_fa4895a43a80d4eef0a607a4` | `cross_market/FUTCORE-P07_cross_market_14_nq_es_divergence_context.json` | NQ/ES divergence context; primary `30m`; cross-instrument completed-bar alignment. |
| `vwap_session` | `aspec_b40aee52d4399dd5b855a6ed` | `vwap_session/FUTCORE-P08_vwap_session_01.md` | RTH reclaim of running VWAP; primary matrix `5m`, `10m`, `15m`, `30m`; RTH primary with thin-session diagnostics. |
| `vwap_session` | `aspec_43cd6c154bca2fcc419eee83` | `vwap_session/FUTCORE-P08_vwap_session_07.md` | RTH open versus completed ETH VWAP context; primary matrix `5m`, `10m`, `15m`, `30m`. |
| `regime` | `aspec_eb962fc197eaf3955c5e4711` | `regime/FUTCORE-P09_regime_01.md` | Trend/volatility/range regime gate; starts with `5m`, later primary matrix needs `10m`, `15m`, `30m` labels. |
| `liquidity_pa` | `aspec_df2d040e45564c259ef3de6d` | `liquidity_pa/FUTCORE-P10_liquidity_pa_02.md` | Close-back-inside after sweep; primary matrix `5m`, `10m`, `15m`, `30m`; fixed reference levels by completed bars. |
| `liquidity_pa` | `aspec_39ffc190cfbfa6ba0b1a2a25` | `liquidity_pa/FUTCORE-P10_liquidity_pa_06.md` | Failed-breakout reversal context; primary matrix `5m`, `10m`, `15m`, `30m`; fixed reference levels by completed bars. |
| `bbo_tradability` | `aspec_1284e49b083df11eeb0481ea` | `bbo_tradability/FUTCORE-P11_bbo_tradability_01.md` | Spread-zscore plus top-book depth confirmation overlay; primary matrix `5m`, `10m`, `15m`, `30m`; BBO as confirmation/risk-control only. |

## Locked Pack Resolution

Resolution was performed by sanctioned registry and resolver surfaces:

- `alpha_system.data.foundation.version_registry.resolve_dataset_version(...)`
- `alpha_system.runtime.input_resolver.FeatureLabelPackResolver`
- `alpha_system.governance.study_input_pack.validate_study_input_pack`
- registry readers used by the existing feature and label CLI modules

Registry inventory:

| Surface | Resolved locked records | Notes |
| --- | ---: | --- |
| DatasetVersion | 1 | `dsv_databento_ohlcv_05404069799decb0`; source `dsrc_databento_historical`; symbols `ES`, `NQ`, `RTY`; 1 minute `TRADES`. |
| FeaturePack | 2 | `base_ohlcv_rth_flag`, `base_ohlcv_session_minute`; both `REGISTERED`, `development_partition`, `value_store_format=dual`. |
| LabelPack | 1 | `fwd_ret_5m`; `REGISTERED`, `development_partition`, `value_store_format=dual`. |
| StudyInputPack validation | 10 | One value-free pack shape validates for each accepted AlphaSpec using the locked feature request ids and label spec id. |

Resolved point-in-time metadata:

| Primitive | Type | Resolved ref | PIT metadata |
| --- | --- | --- | --- |
| `base_ohlcv_rth_flag` | Feature | `fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f`; `freq_67991722245329f35c0fa612`; `fset_es_session_ctx_smoke/v1_rth_flag` | `available_ts` first `2024-01-02T00:01:05+00:00`, last `2024-01-09T00:00:05+00:00`. |
| `base_ohlcv_session_minute` | Feature | `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978`; `freq_76147d2e3318292d48004696`; `fset_es_session_ctx_smoke/v1_session_minute` | `available_ts` first `2024-01-02T00:01:05+00:00`, last `2024-01-09T00:00:05+00:00`. |
| `fwd_ret_5m` | Label | `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395`; `lspec_cd6523694c850c9943b2067e` | `label_available_ts` first `2024-01-02T00:06:05+00:00`, last `2024-01-09T00:00:05+00:00`. |

## Status Key

| Status | Meaning in this audit |
| --- | --- |
| `AVAILABLE` | Primitive resolves through the locked `FUTCORE-P03` pack and carries the required PIT availability metadata. |
| `MISSING` | Primitive is required by an accepted AlphaSpec but has no registry-resolved locked pack reference in `FUTCORE-P03`. |
| `AVAILABLE_BUT_NEEDS_REVIEW` | The reference exists by sanctioned handle, but a downstream no-lookahead, symbol-coverage, duplicate-exposure, or partition concern remains. |

## Primitive Reference Index

| Ref | Required primitive or primitive group | Type / family | Status | Resolved ref or unavailable reason |
| --- | --- | --- | --- | --- |
| `D1` | Canonical ES/NQ/RTY OHLCV 1 minute bars with bar `available_ts` | Data reference, not FeaturePack | `AVAILABLE_BUT_NEEDS_REVIEW` | DatasetVersion `dsv_databento_ohlcv_05404069799decb0` resolves. `coverage_report_hash` was `null` in P03 and symbol-level coverage remains a downstream audit concern. |
| `F1` | `base_ohlcv_rth_flag` | FeaturePack, session context | `AVAILABLE` | `fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f`; has non-empty `available_ts` window. |
| `F2` | `base_ohlcv_session_minute` | FeaturePack, session context | `AVAILABLE` | `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978`; has non-empty `available_ts` window. |
| `L1` | `fwd_ret_5m` | LabelPack, fixed horizon | `AVAILABLE` | `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395`; has non-empty `label_available_ts` window. |
| `G1` | `fwd_ret_10m` | LabelPack, fixed horizon | `MISSING` | Fixed-horizon label name exists in code, but no locked LabelPack record or LabelVersion resolves in P03. |
| `G2` | `fwd_ret_15m` | LabelPack, fixed horizon | `MISSING` | Required by the campaign primary horizon policy and accepted `15m` AlphaSpec, but no locked LabelPack record resolves; the inspected fixed-horizon label enum does not expose a `fwd_ret_15m` name. |
| `G3` | `fwd_ret_30m` | LabelPack, fixed horizon | `MISSING` | Fixed-horizon label name exists in code, but no locked LabelPack record or LabelVersion resolves in P03. |
| `G4` | Causal OHLCV derived features: `VWAP`, `ANCHORED_VWAP`, `DISTANCE_TO_VWAP`, `OPENING_RANGE`, `RETURNS`, `ROLLING_VOLATILITY`, `ROLLING_RANGE`, `ATR`, `RANGE_POSITION`, `TRENDINESS`, `VOLUME_ZSCORE`, plus fixed prior/compression range levels derived from completed OHLCV bars | FeaturePack, OHLCV/session/PA/regime | `MISSING` | These feature names or constructions are declared by accepted AlphaSpecs, but the locked FeaturePack resolves only `base_ohlcv_rth_flag` and `base_ohlcv_session_minute`. |
| `G5` | BBO confirmation features: `SPREAD`, `SPREAD_TICKS`, `SPREAD_ZSCORE`, `TOP_BOOK_DEPTH`, `WIDE_SPREAD_FLAG`, `LOW_DEPTH_FLAG`, `MISSING_BBO_FLAG`, `BAD_QUOTE_FLAG` | FeaturePack, BBO tradability / confirmation | `MISSING` | BBO feature names exist in code, but no BBO DatasetVersion/FeaturePack member is locked by P03. The accepted BBO spec remains confirmation/risk-control only. |

## Accepted AlphaSpec Mapping

| AlphaSpec id | Required primitive refs | Mapping status | Notes |
| --- | --- | --- | --- |
| `aspec_0ebd90cecfd475607685b445` | `D1`, `F1`, `F2`, `L1` | `AVAILABLE_BUT_NEEDS_REVIEW` | Core 5m NQ-to-ES lead/lag inputs resolve by reference. Cross-instrument late/missing/stale input exclusion remains a no-lookahead review item. |
| `aspec_8d9e272e4b78eedcd27f0bec` | `D1`, `F1`, `F2`, `L1`, `G1`, `G4` | `MISSING` | Accepted primary horizon is `10m`; P12 routed `10m` label binding to P13/P15. Residual/basket construction has no locked derived FeaturePack binding. |
| `aspec_a41dcccac5552de945aba825` | `D1`, `F1`, `F2`, `L1`, `G2`, `G4` | `MISSING` | Accepted primary horizon is `15m`; no locked or inspected fixed-horizon `15m` label primitive exists. Rotation/catch-up construction has no locked derived FeaturePack binding. |
| `aspec_fa4895a43a80d4eef0a607a4` | `D1`, `F1`, `F2`, `L1`, `G3`, `G4` | `MISSING` | Accepted primary horizon is `30m`; P12 routed `30m` label binding to P13/P15. Divergence construction has no locked derived FeaturePack binding. |
| `aspec_b40aee52d4399dd5b855a6ed` | `D1`, `F1`, `F2`, `L1`, `G1`, `G2`, `G3`, `G4` | `MISSING` | RTH running-VWAP reclaim requires VWAP, distance-to-VWAP, and opening-range features not present in the locked FeaturePack; only 5m label is locked. |
| `aspec_43cd6c154bca2fcc419eee83` | `D1`, `F1`, `F2`, `L1`, `G1`, `G2`, `G3`, `G4` | `MISSING` | Completed ETH VWAP and active RTH VWAP context require anchored/running VWAP derived FeaturePack binding; only 5m label is locked. |
| `aspec_eb962fc197eaf3955c5e4711` | `D1`, `F1`, `F2`, `L1`, `G1`, `G2`, `G3`, `G4` | `MISSING` | Regime gate requires trendiness, rolling volatility, rolling range, and returns as causal derived features not present in the locked FeaturePack. |
| `aspec_df2d040e45564c259ef3de6d` | `D1`, `F1`, `F2`, `L1`, `G1`, `G2`, `G3`, `G4` | `MISSING` | Sweep close-back-inside requires rolling range, ATR, returns, range position, optional volume z-score, and fixed reference levels by completed bars; no derived pack binding exists. |
| `aspec_39ffc190cfbfa6ba0b1a2a25` | `D1`, `F1`, `F2`, `L1`, `G1`, `G2`, `G3`, `G4` | `MISSING` | Failed-breakout reversal has the same derived OHLCV/reference-level FeaturePack gap as the accepted sweep spec. |
| `aspec_1284e49b083df11eeb0481ea` | `D1`, `F1`, `F2`, `L1`, `G1`, `G2`, `G3`, `G5` | `MISSING` | BBO spread/depth confirmation requires BBO FeaturePack and BBO input binding not locked in P03; only session features and 5m label resolve. |

## Gap Outcome

The minimal P15 gap list is recorded in `gap_list.md`. It contains five request
budget items, matching but not exceeding the campaign cap
`research_budget_policy.max_new_feature_or_label_requests: 5`.

This audit does not authorize implementing all five. It records the smallest
bounded list that preserves the accepted AlphaSpec obligations. `FUTCORE-P15`
may choose a smaller no-op or partial path only if downstream StudySpecs are
explicitly constrained to the locked 5m label plus already available session
features.

## Duplicate Exposure And Availability Notes

- Cross-market accepted records still need cross-instrument `available_ts`
  alignment, missingness by instrument, and stale-input handling review.
- The locked feature set id is `fset_es_session_ctx_smoke`; symbol-level
  coverage for ES/NQ/RTY is registry-bound but not value-inspected here.
- The DatasetVersion resolver returned no coverage report hash in P03; this is
  carried forward as an availability review note, not repaired in P13.
- The locked partition is `development_partition`; validation, locked-test, or
  shadow partitions require separate pack locks.
- BBO confirmation remains a research-only overlay. No tradability, fill,
  broker, paper/live, or production claim is made by mapping its missing pack
  binding.

## Boundary Confirmation

No consumed primitive under `src/alpha_system/**` was edited. No FeatureRequest
or LabelSpec was created. No raw provider data, canonical data, feature values,
label values, Parquet/Arrow/Feather files, SQLite/DB files, provider responses,
run-local artifacts, diagnostics, StudySpecs, reviews, verdicts, PRs, merges,
or staging operations were created by this audit.
