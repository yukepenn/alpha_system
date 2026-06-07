# FUTCORE-P13 Data Contract Audit

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
Phase: `FUTCORE-P13`
Audit type: value-free accepted-AlphaSpec to locked input-pack mapping
Recorded on: 2026-06-07

This audit maps the 10 `accept-for-StudySpec` AlphaSpecs from `FUTCORE-P12` to
the DatasetVersion, FeaturePack, and LabelPack references locked by
`FUTCORE-P03`. It records ids, names, family membership, registry references,
hashes, schema versions, and point-in-time availability metadata only. It does
not read raw provider files, canonical data files, Parquet rows, feature values,
label values, provider responses, or arbitrary data paths.

The availability decision is intentionally pack-based. A primitive that exists
in source code, or is derivable from bars in principle, is marked `AVAILABLE`
only when it resolves through the locked `FUTCORE-P03` FeaturePack or LabelPack
metadata with a valid `available_ts` or `label_available_ts` window.

## Source Set

The accepted set is taken from
`research/futures_core_alpha_pilot_v1/alpha_specs/BUDGET_AUDIT.md`.

| Family | AlphaSpec id | Source draft | Declared horizon / context |
| --- | --- | --- | --- |
| `cross_market` | `aspec_0ebd90cecfd475607685b445` | `cross_market/FUTCORE-P07_cross_market_01_nq_leads_es_completed_bar_context.json` | NQ completed-bar context for later ES decision; primary `5m`. |
| `cross_market` | `aspec_8d9e272e4b78eedcd27f0bec` | `cross_market/FUTCORE-P07_cross_market_05_nq_beta_residual_vs_es_rty_basket.json` | NQ beta residual versus ES/RTY basket; primary `10m`. |
| `cross_market` | `aspec_a41dcccac5552de945aba825` | `cross_market/FUTCORE-P07_cross_market_10_rty_catchup_rotation_context.json` | RTY catch-up rotation context; primary `15m`. |
| `cross_market` | `aspec_fa4895a43a80d4eef0a607a4` | `cross_market/FUTCORE-P07_cross_market_14_nq_es_divergence_context.json` | NQ/ES completed-bar divergence context; primary `30m`. |
| `vwap_session` | `aspec_b40aee52d4399dd5b855a6ed` | `vwap_session/FUTCORE-P08_vwap_session_01.md` | RTH running-VWAP reclaim; primary matrix `5m`, `10m`, `15m`, `30m`. |
| `vwap_session` | `aspec_43cd6c154bca2fcc419eee83` | `vwap_session/FUTCORE-P08_vwap_session_07.md` | RTH open versus completed ETH VWAP; primary matrix `5m`, `10m`, `15m`, `30m`. |
| `regime` | `aspec_eb962fc197eaf3955c5e4711` | `regime/FUTCORE-P09_regime_01.md` | Trendiness, volatility, and range-compression gate; primary matrix begins at `5m`. |
| `liquidity_pa` | `aspec_df2d040e45564c259ef3de6d` | `liquidity_pa/FUTCORE-P10_liquidity_pa_02.md` | Sweep close-back-inside; primary matrix `5m`, `10m`, `15m`, `30m`. |
| `liquidity_pa` | `aspec_39ffc190cfbfa6ba0b1a2a25` | `liquidity_pa/FUTCORE-P10_liquidity_pa_06.md` | Failed-breakout reversal; primary matrix `5m`, `10m`, `15m`, `30m`. |
| `bbo_tradability` | `aspec_1284e49b083df11eeb0481ea` | `bbo_tradability/FUTCORE-P11_bbo_tradability_01.md` | Spread-zscore plus top-book depth confirmation overlay; primary matrix `5m`, `10m`, `15m`, `30m`. |

## Resolution Surfaces

Resolution used sanctioned registry and governance surfaces only:

- `alpha_system.data.foundation.version_registry.resolve_dataset_version`
- `alpha_system.cli.feature._feature_records` using the local feature registry
  in read-only mode
- `alpha_system.cli.label._label_records` using the local label registry in
  read-only mode
- `alpha_system.runtime.input_resolver.FeatureLabelPackResolver`
- `alpha_system.governance.study_input_pack.validate_study_input_pack`

Registry inventory:

| Surface | Resolved locked records | Result |
| --- | ---: | --- |
| DatasetVersion | 1 | `dsv_databento_ohlcv_05404069799decb0`; symbols `ES`, `NQ`, `RTY`; 1 minute `TRADES`. |
| FeaturePack | 8 | All records bind to `dsv_databento_ohlcv_05404069799decb0`, `development_partition`, and `value_store_format=dual`. |
| LabelPack | 3 | `fwd_ret_5m`, `fwd_ret_10m`, and `fwd_ret_30m` bind to the locked DatasetVersion and partition. |
| Runtime pack resolver | 8 feature handles / 3 label handles | Handles resolved by explicit local registry facades; all availability windows are non-empty and ordered. |
| StudyInputPack validation | 10 | One value-free `StudyInputPack` shape validated for each accepted AlphaSpec using locked feature request ids, label spec ids, and DatasetVersion scope. |

## Locked FeaturePack Metadata

All feature rows below are `AVAILABLE`: they resolve through the locked
FeaturePack and carry valid, non-empty `available_ts` windows.

| Feature primitive | FeatureVersion id | FeatureRequest id | Pack set/version | `value_content_hash` | `value_schema_version` | `available_ts` validity |
| --- | --- | --- | --- | --- | --- | --- |
| `base_ohlcv_log_returns` | `fver_7ac2429f12ce6f7d494b7c0ab968446f2455da51863ebe471ddd8a224b6fa9f9` | `freq_658fe17db11d23540e4ed17d` | `fset_es_ohlcv_session_smoke` / `v1_log_returns` | `sha256:5958b475409b9275c5982935de6d3487d2c01fe6845f31eee5781b3f1f0d812a` | `alpha_system.features.materialization.v1` | valid: `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` |
| `base_ohlcv_range_position` | `fver_862f9b2d36e10b58d362afffe69c72cfc4231e562d96e1cb923aca649c1b2f5d` | `freq_e44777a9b6c5685aed764c32` | `fset_es_ohlcv_session_smoke` / `v1_range_position` | `sha256:7056759e0577f5a3f57426944f48602bf6f5589d7d79597270e7db543aa8dc73` | `alpha_system.features.materialization.v1` | valid: `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` |
| `base_ohlcv_returns` | `fver_a6390d478bc31576bce270eadb93f8adfe215833ab403aba2e69af53e120eb8a` | `freq_7644d195221963a725953a50` | `fset_es_ohlcv_session_smoke` / `v1_returns` | `sha256:0a8d29b9284d85e5306d76e0482ce6925c8384e9bb28247dc9564be02360ed90` | `alpha_system.features.materialization.v1` | valid: `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` |
| `base_ohlcv_rolling_range` | `fver_74ba4d642ce7b24dbdc06bc5bd16ce9c05bae3def8052056c439b3b6cdbc9169` | `freq_cd75d0b4aa48ba48c04e970b` | `fset_es_ohlcv_session_smoke` / `v1_rolling_range` | `sha256:c9e133ed324b2b2ea168fa2b2672e99050161c91e34ea919f82eae2be2f96077` | `alpha_system.features.materialization.v1` | valid: `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` |
| `base_ohlcv_rolling_volatility` | `fver_18b5841a0d7f2fd7b86e5d650a21742190c1517dacc40dbb90854a1188191147` | `freq_af690f30c36a7bbd12b6d730` | `fset_es_ohlcv_session_smoke` / `v1_rolling_volatility` | `sha256:1ad59e668cbed859460cb3dc672293cfc03f55d600d185477b46cfe1e9c1ec67` | `alpha_system.features.materialization.v1` | valid: `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` |
| `base_ohlcv_rth_flag` | `fver_acbfa7833cb2a07338a91abe750c934d9e9922477ad96e3ea3e0c001970573f9` | `freq_67991722245329f35c0fa612` | `fset_es_session_ctx_smoke` / `v1_rth_flag` | `sha256:29a64bad4966f696b1c18e72432ef2e5e00fff9ed767b6cd968493a7d4a6fa79` | `alpha_system.features.materialization.v1` | valid: `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` |
| `base_ohlcv_session_minute` | `fver_fd739ad918a557d2f4ca45d54c9ea700cc0168ad9c6fec90151d87479bf1b858` | `freq_f7d4e9c2f4c60c5c25f15ce2` | `fset_es_session_ctx_smoke` / `v1_session_minute` | `sha256:94430bbd52270daf8a7e043c9a0e1c45b98e1f84b0f9ff0439d7119ddb3ef0ad` | `alpha_system.features.materialization.v1` | valid: `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` |
| `base_ohlcv_volume_zscore` | `fver_759ee1b9da77fefb78aa5440b3de66dd217922ac576241858960cf1e8cef8a91` | `freq_c74b47e119cb7095e86dc709` | `fset_es_ohlcv_session_smoke` / `v1_volume_zscore` | `sha256:5c4ff7e2cbcbe4165a25c654d01466937c74b52560a53193f9c422256c84bbdf` | `alpha_system.features.materialization.v1` | valid: `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` |

## Locked LabelPack Metadata

All label rows below are `AVAILABLE`: they resolve through the locked LabelPack
and carry valid, non-empty `label_available_ts` windows.

| Label primitive | LabelVersion id | LabelSpec id | `value_content_hash` | `value_schema_version` | `label_available_ts` validity |
| --- | --- | --- | --- | --- | --- |
| `fwd_ret_5m` | `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` | `lspec_cd6523694c850c9943b2067e` | `sha256:abb5f53c7ede5f359a79541b237d71d44e79304ebbb6333a101a3c0588e32a9f` | `alpha_system.labels.materialization.v1` | valid: `2024-01-02T00:06:05+00:00` to `2024-01-09T00:00:05+00:00` |
| `fwd_ret_10m` | `lver_4170332f366d6945a37cfe8980395626c393b40c2e1c36944ffb784b88cc7941` | `lspec_15c26c4368bb432b0b0dc6e9` | `sha256:d691193911a2f72a821da02846dbc3bab377ad810b67b0761de72b83bbac1489` | `alpha_system.labels.materialization.v1` | valid: `2024-01-02T00:11:05+00:00` to `2024-01-09T00:00:05+00:00` |
| `fwd_ret_30m` | `lver_69c9900cbac5e679f8d97d350e30f493f30a498eb3d47463e6ab9995f1c0310a` | `lspec_65ba5b5c9b4fa37e0e42b6ef` | `sha256:d691193911a2f72a821da02846dbc3bab377ad810b67b0761de72b83bbac1489` | `alpha_system.labels.materialization.v1` | valid: `2024-01-02T00:31:05+00:00` to `2024-01-09T00:00:05+00:00` |

## Status Key

| Status | Meaning in this audit |
| --- | --- |
| `AVAILABLE` | Primitive resolves through the locked pack and has required PIT availability metadata. |
| `MISSING` | Primitive is required by an accepted AlphaSpec but has no registry-resolved locked pack reference in `FUTCORE-P03`. |
| `AVAILABLE_BUT_NEEDS_REVIEW` | The reference exists by sanctioned handle, but a downstream no-lookahead, symbol coverage, partition, stale-id, or alignment concern remains. |

## Primitive Reference Index

| Ref | Required primitive or primitive group | Type / family | Status | Resolved ref or unavailable reason |
| --- | --- | --- | --- | --- |
| `D1` | ES/NQ/RTY 1 minute OHLCV DatasetVersion anchor | DatasetVersion | `AVAILABLE_BUT_NEEDS_REVIEW` | DatasetVersion `dsv_databento_ohlcv_05404069799decb0` resolves for `ES`, `NQ`, `RTY`; P03 records no `coverage_report_hash`, so symbol-level row coverage remains a downstream observation. |
| `F1` | `base_ohlcv_rth_flag` | FeaturePack / session context | `AVAILABLE_BUT_NEEDS_REVIEW` | P03 primitive available as `fver_acbfa7833cb2a07338a91abe750c934d9e9922477ad96e3ea3e0c001970573f9`; accepted source drafts cite stale `fver_c365f971...`, so P14 must bind the P03 id. |
| `F2` | `base_ohlcv_session_minute` | FeaturePack / session context | `AVAILABLE_BUT_NEEDS_REVIEW` | P03 primitive available as `fver_fd739ad918a557d2f4ca45d54c9ea700cc0168ad9c6fec90151d87479bf1b858`; accepted source drafts cite stale `fver_17dfce...`, so P14 must bind the P03 id. |
| `F3` | `base_ohlcv_returns` | FeaturePack / base OHLCV | `AVAILABLE` | `fver_a6390d478bc31576bce270eadb93f8adfe215833ab403aba2e69af53e120eb8a`; valid `available_ts`. |
| `F4` | `base_ohlcv_log_returns` | FeaturePack / base OHLCV | `AVAILABLE` | `fver_7ac2429f12ce6f7d494b7c0ab968446f2455da51863ebe471ddd8a224b6fa9f9`; valid `available_ts`. |
| `F5` | `base_ohlcv_rolling_volatility` | FeaturePack / base OHLCV | `AVAILABLE` | `fver_18b5841a0d7f2fd7b86e5d650a21742190c1517dacc40dbb90854a1188191147`; valid `available_ts`. |
| `F6` | `base_ohlcv_rolling_range` | FeaturePack / base OHLCV | `AVAILABLE` | `fver_74ba4d642ce7b24dbdc06bc5bd16ce9c05bae3def8052056c439b3b6cdbc9169`; valid `available_ts`. |
| `F7` | `base_ohlcv_range_position` | FeaturePack / base OHLCV | `AVAILABLE` | `fver_862f9b2d36e10b58d362afffe69c72cfc4231e562d96e1cb923aca649c1b2f5d`; valid `available_ts`. |
| `F8` | `base_ohlcv_volume_zscore` | FeaturePack / volume overlay | `AVAILABLE` | `fver_759ee1b9da77fefb78aa5440b3de66dd217922ac576241858960cf1e8cef8a91`; valid `available_ts`; overlay-only. |
| `L5` | `fwd_ret_5m` | LabelPack / fixed horizon | `AVAILABLE` | `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395`; valid `label_available_ts`. |
| `L10` | `fwd_ret_10m` | LabelPack / fixed horizon | `AVAILABLE` | `lver_4170332f366d6945a37cfe8980395626c393b40c2e1c36944ffb784b88cc7941`; valid `label_available_ts`. |
| `L30` | `fwd_ret_30m` | LabelPack / fixed horizon | `AVAILABLE` | `lver_69c9900cbac5e679f8d97d350e30f493f30a498eb3d47463e6ab9995f1c0310a`; valid `label_available_ts`. |
| `G1` | `fwd_ret_15m` | LabelPack / fixed horizon | `MISSING` | Required by the campaign primary horizon matrix and by `aspec_a41dcccac5552de945aba825`; no locked LabelPack member resolves. |
| `G2` | VWAP/session feature binding: running VWAP, completed ETH/anchored VWAP, distance-to-VWAP, opening-range context | FeaturePack / VWAP-session | `MISSING` | Required by accepted VWAP/session AlphaSpecs; no locked FeaturePack member resolves these primitives. |
| `G3` | Cross-market derived-state binding: beta residual, ES/RTY basket residual, relative-rank/catch-up, pair divergence/agreement state | FeaturePack / cross-market | `MISSING` | Required by three accepted cross-market AlphaSpecs beyond the simple NQ-to-ES completed-bar context; no locked FeaturePack member resolves these derived states. |
| `G4` | Additional base-OHLCV derived-state binding: trendiness, ATR, fixed prior-range/compression boundaries, sweep/breakout/failure trigger flags | FeaturePack / regime and liquidity-PA | `MISSING` | Some base inputs resolve (`F3` through `F8`), but these accepted regime/liquidity primitives are not separately registered in the locked FeaturePack. |
| `G5` | BBO top-book confirmation binding: spread, spread ticks, spread zscore, top-book depth, wide-spread, low-depth, missing-BBO, bad-quote flags | FeaturePack / BBO | `MISSING` | Required by `aspec_1284e49b083df11eeb0481ea`; no BBO DatasetVersion or BBO FeaturePack member is locked in P03. |

## Accepted AlphaSpec Coverage Mapping

| AlphaSpec id | Family | Available locked refs | Missing refs | Mapping status | Notes |
| --- | --- | --- | --- | --- | --- |
| `aspec_0ebd90cecfd475607685b445` | `cross_market` | `D1`, `F1`, `F2`, `L5` | none | `AVAILABLE_BUT_NEEDS_REVIEW` | Primitive set resolves by name, but source draft feature-version ids are stale relative to P03 and cross-instrument alignment remains a P16/P23 concern. |
| `aspec_8d9e272e4b78eedcd27f0bec` | `cross_market` | `D1`, `F1`, `F2`, `F3`, `F4`, `L10` | `G3` | `MISSING` | Primary `10m` label resolves. Beta/residual basket state itself does not resolve as a locked FeaturePack primitive. |
| `aspec_a41dcccac5552de945aba825` | `cross_market` | `D1`, `F1`, `F2`, `F3`, `F4` | `G1`, `G3` | `MISSING` | Primary `15m` label and RTY catch-up/relative-rank state do not resolve in the locked packs. |
| `aspec_fa4895a43a80d4eef0a607a4` | `cross_market` | `D1`, `F1`, `F2`, `F3`, `F4`, `L30` | `G3` | `MISSING` | Primary `30m` label resolves. Pair divergence/agreement state does not resolve as a locked FeaturePack primitive. |
| `aspec_b40aee52d4399dd5b855a6ed` | `vwap_session` | `D1`, `F1`, `F2`, `F3`, `F6`, `F7`, `F8`, `L5`, `L10`, `L30` | `G1`, `G2` | `MISSING` | `5m`, `10m`, and `30m` labels resolve; `15m`, running VWAP, distance-to-VWAP, and opening-range bindings do not. |
| `aspec_43cd6c154bca2fcc419eee83` | `vwap_session` | `D1`, `F1`, `F2`, `F3`, `F6`, `F7`, `F8`, `L5`, `L10`, `L30` | `G1`, `G2` | `MISSING` | Completed ETH VWAP / active RTH VWAP context is not a locked FeaturePack primitive; `15m` label remains missing. |
| `aspec_eb962fc197eaf3955c5e4711` | `regime` | `D1`, `F1`, `F2`, `F3`, `F5`, `F6`, `L5`, `L10`, `L30` | `G1`, `G4` | `MISSING` | Rolling volatility, rolling range, and returns resolve; trendiness and `15m` label do not. |
| `aspec_df2d040e45564c259ef3de6d` | `liquidity_pa` | `D1`, `F1`, `F2`, `F3`, `F6`, `F7`, `F8`, `L5`, `L10`, `L30` | `G1`, `G4` | `MISSING` | Rolling range, returns, range position, and volume zscore resolve; ATR and fixed reference/trigger bindings do not. |
| `aspec_39ffc190cfbfa6ba0b1a2a25` | `liquidity_pa` | `D1`, `F1`, `F2`, `F3`, `F6`, `F7`, `F8`, `L5`, `L10`, `L30` | `G1`, `G4` | `MISSING` | Same locked base feature coverage as the sweep spec; failed-breakout/fixed-boundary trigger binding and `15m` label are missing. |
| `aspec_1284e49b083df11eeb0481ea` | `bbo_tradability` | `D1`, `F1`, `F2`, `L5`, `L10`, `L30` | `G1`, `G5` | `MISSING` | Label matrix resolves except `15m`. BBO quote and top-book confirmation features do not resolve in P03. |

## Cross-Instrument Availability Flags

The DatasetVersion and all locked FeaturePack/LabelPack records bind to the
same `dsv_databento_ohlcv_05404069799decb0` and `development_partition`.
DatasetVersion metadata resolves the universe as `ES`, `NQ`, and `RTY`; this
audit does not inspect value rows to prove symbol-level row counts.

| AlphaSpec id | Instruments declared | Registry-bound availability | Forward flag |
| --- | --- | --- | --- |
| `aspec_0ebd90cecfd475607685b445` | `NQ`, `ES` | DatasetVersion universe includes both instruments; required locked session features and `5m` label bind to the same DatasetVersion. | P16/P23 must check completed-bar alignment, late/stale rows, and stale source-draft feature ids. |
| `aspec_8d9e272e4b78eedcd27f0bec` | `NQ`, `ES`, `RTY` | DatasetVersion universe includes all three; `10m` label resolves. | P16/P23 must check cross-instrument missingness and point-in-time beta/residual construction; P15 must resolve or defer `G3`. |
| `aspec_a41dcccac5552de945aba825` | `RTY`, `ES`, `NQ` | DatasetVersion universe includes all three; no `15m` label resolves. | P14/P15 must resolve or defer `G1` and `G3`; P16/P23 must check ES/NQ agreement and RTY decision timing. |
| `aspec_fa4895a43a80d4eef0a607a4` | `NQ`, `ES` | DatasetVersion universe includes both instruments; `30m` label resolves. | P16/P23 must check divergence construction by `available_ts`; P15 must resolve or defer `G3`. |

## Consolidated Gap Outcome

The minimal P15 gap list is recorded in
`research/futures_core_alpha_pilot_v1/audits/data_contract/gap_list.md`.
It contains exactly five grouped budget items:

1. `fwd_ret_15m` LabelPack binding.
2. VWAP/session FeaturePack binding.
3. Cross-market derived-state FeaturePack binding.
4. Additional base-OHLCV derived-state FeaturePack binding for regime and
   liquidity/PA.
5. BBO top-book confirmation FeaturePack binding.

`fwd_ret_10m` and `fwd_ret_30m` are not P15 gaps in this audit because they
resolve in the P03 locked LabelPack with valid `label_available_ts` metadata.

## Binding Drift Notes For P14

The accepted AlphaSpec source drafts consistently cite stale session
FeatureVersion ids (`fver_c365f971...` and `fver_17dfce...`). P03 locks the same
primitive names under `fver_acbfa783...` and `fver_fd739ad...`. This is not a
missing primitive because registry resolution by primitive name succeeds, but
P14 StudySpecs must bind the P03 ids, not the stale draft ids.

Several accepted source drafts also say the locked pack exposes only the `5m`
label. P03 locks `5m`, `10m`, and `30m`. P14 should bind the P03 `10m` and
`30m` LabelSpec ids where those horizons are used, and should not treat `15m`
as available unless P15 resolves that gap or P14 explicitly defers the horizon.

## Boundary Confirmation

No consumed primitive under `src/alpha_system/**` was edited. No FeatureRequest
or LabelSpec was created. No raw provider data, canonical data, feature values,
label values, Parquet/Arrow/Feather files, SQLite/DB files, provider responses,
run-local artifacts, diagnostics, StudySpecs, reviews, verdicts, PRs, merges,
or staging operations were created by this audit.
