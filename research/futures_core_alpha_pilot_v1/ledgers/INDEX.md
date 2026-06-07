# FUTCORE-P26 Ledger Index

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P26`  
Artifact type: value-free TrialLedger and RejectedIdeaLedger index

This index records ledger structure and reconciliation by reference only. The
records under this directory were constructed through
`create_trial_ledger_record` and `create_rejected_idea_record`, then validated
with `validate_trial_ledger_record` and `validate_rejected_idea_record`. The
RejectedIdea aggregate was serialized through `ResearchGraveyardLedger`.

No diagnostics were run or rerun. No promotion, watcher/candidate state,
FactorCard, EvidenceDraft, broker/live/paper/order/deployment action, reviewer
artifact, PR, merge, staging action, or phase PASS is recorded here.

## Ledger Files

- TrialLedger aggregate: `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/trial_ledger.json`
- TrialLedger records: `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/*.json`
- RejectedIdeaLedger aggregate: `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/rejected_idea_ledger.json`
- RejectedIdea records: `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/*.json`

## Completeness Counts

| Population | Count | Reconciliation |
| --- | ---: | --- |
| AlphaSpec drafts in `research/futures_core_alpha_pilot_v1/alpha_specs/**` | 40 | Matches 40 P12 critique files. |
| AlphaSpecs accepted for StudySpec | 10 | Matches `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md`. |
| P12 non-accepted AlphaSpecs recorded in RejectedIdeaLedger | 30 | `revise` plus `reject` critique decisions, one record each. |
| Accepted StudySpecs rejected before P25 verdict review | 4 | P16 cross-market rejected-source set, one record each. |
| P25 reviewer-rejected ideas | 0 | P25 verdict set contains 6 `INCONCLUSIVE` judgements and no rejected verdict. |
| RejectedIdeaLedger records | 34 | 30 P12 non-accepted plus 4 P16 diagnostic rejections. |
| TrialLedger records | 16 | 8 study-level pre-grid attempts plus 8 explicit variant-cell attempts. |
| Declared StudySpec variant slots | 40 | 10 StudySpecs x `variant_budget: 4`; P24 records no over-budget execution. |
| P24 explicit observed variant cells | 8 | 4 P18 regime cells plus 4 P20 BBO cells. |
| AlphaSpecs with P25 `INCONCLUSIVE` reviewer verdict and no rejection record | 6 | All six are carried to later evidence/promotion phases without P26 promotion. |

The union of P12 non-accepted AlphaSpecs and StudySpec-bound accepted AlphaSpecs
accounts for all 40 AlphaSpec drafts. TrialLedger records cover every
StudySpec-bound accepted idea; RejectedIdeaLedger records cover every P12
non-accepted idea and every accepted StudySpec rejected before P25. No P25
verdict adds a reviewer-rejected idea in this phase.

## Trial Status Counts

| Status | Count |
| --- | ---: |
| `ABANDONED` | 4 |
| `COMPLETED` | 4 |
| `FAILED` | 8 |

## Trial Family Counts

| Family | Trial records |
| --- | ---: |
| `bbo_tradability` | 4 |
| `cross_market` | 4 |
| `liquidity_pa` | 2 |
| `regime` | 4 |
| `vwap_session` | 2 |

## Rejection Counts

| Reason category | Count |
| --- | ---: |
| `duplicate` | 30 |
| `failed_diagnostics` | 4 |

| Source decision/event | Count |
| --- | ---: |
| `P16_REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | 4 |
| `reject` | 6 |
| `revise` | 24 |

| Family | Rejection records |
| --- | ---: |
| `bbo_tradability` | 3 |
| `cross_market` | 16 |
| `liquidity_pa` | 4 |
| `regime` | 5 |
| `vwap_session` | 6 |

## TrialLedger Records

| TrialLedger id | StudySpec | AlphaSpec | Family | Variant id | Status | Record path |
| --- | --- | --- | --- | --- | --- | --- |
| `trial_2c32c84a140e6e99f67f5aa8` | `sspec_9f6f741192a4b534f06e51c0` | `aspec_1284e49b083df11eeb0481ea` | `bbo_tradability` | `bbo_low_depth_flag_exclusion_long_predeclared_trailing` | `ABANDONED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_2c32c84a140e6e99f67f5aa8.json` |
| `trial_4ee4909066d85d4abcdfaa42` | `sspec_9f6f741192a4b534f06e51c0` | `aspec_1284e49b083df11eeb0481ea` | `bbo_tradability` | `bbo_low_depth_flag_exclusion_short_predeclared_trailing` | `ABANDONED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_4ee4909066d85d4abcdfaa42.json` |
| `trial_3a61fa6378614054674171ec` | `sspec_9f6f741192a4b534f06e51c0` | `aspec_1284e49b083df11eeb0481ea` | `bbo_tradability` | `bbo_minimum_depth_filter_long_predeclared_trailing` | `ABANDONED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_3a61fa6378614054674171ec.json` |
| `trial_2ae03a839098b6ff741b2f84` | `sspec_9f6f741192a4b534f06e51c0` | `aspec_1284e49b083df11eeb0481ea` | `bbo_tradability` | `bbo_minimum_depth_filter_short_predeclared_trailing` | `ABANDONED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_2ae03a839098b6ff741b2f84.json` |
| `trial_1fc87c34cf31d8055d3d224d` | `sspec_7c8fb13628843890c171b122` | `aspec_fa4895a43a80d4eef0a607a4` | `cross_market` | `study_level_pregrid_cross_market_missingness` | `FAILED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_1fc87c34cf31d8055d3d224d.json` |
| `trial_bdbfa08dcf63fe1fe8e5921d` | `sspec_90b28233d828128664588a9a` | `aspec_a41dcccac5552de945aba825` | `cross_market` | `study_level_pregrid_cross_market_missingness` | `FAILED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_bdbfa08dcf63fe1fe8e5921d.json` |
| `trial_587d6da288aa8ff2ca25fa37` | `sspec_c671fbeeb143512cbc03bc5b` | `aspec_8d9e272e4b78eedcd27f0bec` | `cross_market` | `study_level_pregrid_cross_market_missingness` | `FAILED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_587d6da288aa8ff2ca25fa37.json` |
| `trial_b4e25da7c409809fc1cb54b7` | `sspec_dde3e64667fe158f9bad527d` | `aspec_0ebd90cecfd475607685b445` | `cross_market` | `study_level_pregrid_cross_market_missingness` | `FAILED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_b4e25da7c409809fc1cb54b7.json` |
| `trial_45df4e0c5999da63a57ff9b2` | `sspec_02c400a561891171a33c0c66` | `aspec_39ffc190cfbfa6ba0b1a2a25` | `liquidity_pa` | `study_level_pregrid_liquidity_trigger_binding` | `COMPLETED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_45df4e0c5999da63a57ff9b2.json` |
| `trial_666433ac863d5adb1368a3d1` | `sspec_27bf1262b0bd23d27191cc86` | `aspec_df2d040e45564c259ef3de6d` | `liquidity_pa` | `study_level_pregrid_liquidity_trigger_binding` | `COMPLETED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_666433ac863d5adb1368a3d1.json` |
| `trial_58fdb5456d910efccdd95b7b` | `sspec_267cc052e37668339c38d179` | `aspec_eb962fc197eaf3955c5e4711` | `regime` | `regime_momentum_active_long_predeclared_trailing` | `FAILED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_58fdb5456d910efccdd95b7b.json` |
| `trial_94781614f100a2aa0878aae4` | `sspec_267cc052e37668339c38d179` | `aspec_eb962fc197eaf3955c5e4711` | `regime` | `regime_momentum_active_short_predeclared_trailing` | `FAILED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_94781614f100a2aa0878aae4.json` |
| `trial_fce335815b1bda26eb898aed` | `sspec_267cc052e37668339c38d179` | `aspec_eb962fc197eaf3955c5e4711` | `regime` | `regime_reversion_active_long_predeclared_trailing` | `FAILED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_fce335815b1bda26eb898aed.json` |
| `trial_13c98257a704ce5641a51626` | `sspec_267cc052e37668339c38d179` | `aspec_eb962fc197eaf3955c5e4711` | `regime` | `regime_reversion_active_short_predeclared_trailing` | `FAILED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_13c98257a704ce5641a51626.json` |
| `trial_fffbb48dc4111caeabcc55c9` | `sspec_69c22ec5847395ac8e81b5b6` | `aspec_b40aee52d4399dd5b855a6ed` | `vwap_session` | `study_level_pregrid_vwap_feature_binding` | `COMPLETED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_fffbb48dc4111caeabcc55c9.json` |
| `trial_3b8f60dd0f4793288360159e` | `sspec_aff70fcbc4b7ff226fcc8149` | `aspec_43cd6c154bca2fcc419eee83` | `vwap_session` | `study_level_pregrid_vwap_feature_binding` | `COMPLETED` | `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/trial_3b8f60dd0f4793288360159e.json` |

## RejectedIdeaLedger Records

| RejectedIdea id | AlphaSpec | Family | Reason category | Source decision/event | Duplicate-exposure group hint | Record path |
| --- | --- | --- | --- | --- | --- | --- |
| `rej_3f230dd99e4378773d549458` | `aspec_857ea832d75aa4fc23b376d6` | `bbo_tradability` | `duplicate` | `revise` | `bbo-depth-imbalance` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_3f230dd99e4378773d549458.json` |
| `rej_1b16a258b6e3bdf8f844ff1b` | `aspec_89fa98eb6439f131de4151cb` | `bbo_tradability` | `duplicate` | `revise` | `bbo-quote-quality-quarantine` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_1b16a258b6e3bdf8f844ff1b.json` |
| `rej_a0475fcf4c9aa26eb43e503d` | `aspec_cfb2aad22b43bc23391a7806` | `bbo_tradability` | `duplicate` | `revise` | `bbo-microprice-imbalance` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_a0475fcf4c9aa26eb43e503d.json` |
| `rej_06647e1d25ff8b1fbed873b1` | `aspec_0cc1c674fbe038809819be79` | `cross_market` | `duplicate` | `revise` | `cm-pair-residual-divergence` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_06647e1d25ff8b1fbed873b1.json` |
| `rej_c27b447c282967db390ff10d` | `aspec_0ebd90cecfd475607685b445` | `cross_market` | `failed_diagnostics` | `P16_REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | `cm-lead-lag-pair` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_c27b447c282967db390ff10d.json` |
| `rej_af5723443be70254b18dbfef` | `aspec_4d5ebc78dc8269d8b8d2ca20` | `cross_market` | `duplicate` | `reject` | `cm-broad-rotation` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_af5723443be70254b18dbfef.json` |
| `rej_af75aeaef690e7c6bed5ffac` | `aspec_4fee1276b9f37cb75bd7be48` | `cross_market` | `duplicate` | `revise` | `cm-rty-residual-catchup` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_af75aeaef690e7c6bed5ffac.json` |
| `rej_09a5984328920eb6569e65e4` | `aspec_532c35c3e7571acf8c8f40d1` | `cross_market` | `duplicate` | `revise` | `cm-small-cap-risk` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_09a5984328920eb6569e65e4.json` |
| `rej_ba018932c70418dd1c62cc73` | `aspec_59b646fde9d11179bc4c0444` | `cross_market` | `duplicate` | `revise` | `cm-confirmation-triad` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_ba018932c70418dd1c62cc73.json` |
| `rej_79fb93c524e01205571be326` | `aspec_677bf829db3937be87e8fff4` | `cross_market` | `duplicate` | `revise` | `cm-nq-rotation` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_79fb93c524e01205571be326.json` |
| `rej_e0a173b02edb0e71d249725f` | `aspec_6fa402d0ecaaa3491c6a52cd` | `cross_market` | `duplicate` | `revise` | `cm-rty-nonconfirmation` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_e0a173b02edb0e71d249725f.json` |
| `rej_9ed40aaf995f1f70f5f94cdf` | `aspec_8d9e272e4b78eedcd27f0bec` | `cross_market` | `failed_diagnostics` | `P16_REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | `cm-beta-residual` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_9ed40aaf995f1f70f5f94cdf.json` |
| `rej_279ba6379332d9f899780922` | `aspec_a3a0979f1cb8d95982605a5c` | `cross_market` | `duplicate` | `reject` | `cm-broad-confirmation` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_279ba6379332d9f899780922.json` |
| `rej_20d88b59ce09f47d364fd529` | `aspec_a41dcccac5552de945aba825` | `cross_market` | `failed_diagnostics` | `P16_REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | `cm-rty-rotation` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_20d88b59ce09f47d364fd529.json` |
| `rej_637bd1497ff024f9a212faa3` | `aspec_a98c25c5b437e0906320ac56` | `cross_market` | `duplicate` | `revise` | `cm-lead-lag-rty` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_637bd1497ff024f9a212faa3.json` |
| `rej_f1aa6cbbba90096cbe920125` | `aspec_b2243f2aa448902d9d99d386` | `cross_market` | `duplicate` | `revise` | `cm-rank-turnover` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_f1aa6cbbba90096cbe920125.json` |
| `rej_74bd9f3de2307470f9a9205e` | `aspec_bd439bada940f95f45288535` | `cross_market` | `duplicate` | `revise` | `cm-beta-residual` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_74bd9f3de2307470f9a9205e.json` |
| `rej_57e5257eb6c885c6254cf45e` | `aspec_c6a0645fbad79e0a263737a6` | `cross_market` | `duplicate` | `reject` | `cm-lead-lag-triad` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_57e5257eb6c885c6254cf45e.json` |
| `rej_fa471f1ddeaa066dc4a95feb` | `aspec_fa4895a43a80d4eef0a607a4` | `cross_market` | `failed_diagnostics` | `P16_REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | `cm-pair-divergence` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_fa471f1ddeaa066dc4a95feb.json` |
| `rej_a8832777786ac88bbe434900` | `aspec_1c1cfee8bedf55ced10a391e` | `liquidity_pa` | `duplicate` | `revise` | `pa-prior-range-sweep-parent` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_a8832777786ac88bbe434900.json` |
| `rej_cf1b3dcfd7a25f222ef38522` | `aspec_55c1351d04054c943c2c3721` | `liquidity_pa` | `duplicate` | `revise` | `pa-compression-breakout` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_cf1b3dcfd7a25f222ef38522.json` |
| `rej_8c41a68d8e95409fb821be78` | `aspec_928e60d5096d2383a25f66c6` | `liquidity_pa` | `duplicate` | `revise` | `pa-wick-sweep` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_8c41a68d8e95409fb821be78.json` |
| `rej_a047b6106811559925518ea4` | `aspec_bc9bbcd07669384e51b1661f` | `liquidity_pa` | `duplicate` | `revise` | `pa-sweep-displacement` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_a047b6106811559925518ea4.json` |
| `rej_9f8dd7ff8159f5b50645721e` | `aspec_7db3a23e98ca7ff99b1805c6` | `regime` | `duplicate` | `revise` | `regime-vol-expansion` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_9f8dd7ff8159f5b50645721e.json` |
| `rej_932d2686b8670d5f21a2a4ca` | `aspec_ad998ced05be1a90c92bee1e` | `regime` | `duplicate` | `reject` | `regime-vwap-distance` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_932d2686b8670d5f21a2a4ca.json` |
| `rej_b6525bbd50dcd3c0618596d9` | `aspec_d26b7959b12be5b53f969067` | `regime` | `duplicate` | `revise` | `regime-compression-release` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_b6525bbd50dcd3c0618596d9.json` |
| `rej_af9540c3abafe6b474cb4256` | `aspec_edc47c5593bcaaf6d2d8c42b` | `regime` | `duplicate` | `revise` | `regime-eth-rth-session` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_af9540c3abafe6b474cb4256.json` |
| `rej_47e465bbe40d78562f0705d8` | `aspec_f2de85c342e1bc2018297ff7` | `regime` | `duplicate` | `revise` | `regime-session-transition` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_47e465bbe40d78562f0705d8.json` |
| `rej_720b132bcff3939fbf54b81e` | `aspec_497f906c7b8f8ed80b64f42b` | `vwap_session` | `duplicate` | `revise` | `vwap-gap-open` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_720b132bcff3939fbf54b81e.json` |
| `rej_5c5d0ffd83e6fef6b7b7b42a` | `aspec_4a0e170d68918d3c787db230` | `vwap_session` | `duplicate` | `revise` | `vwap-opening-range-confluence` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_5c5d0ffd83e6fef6b7b7b42a.json` |
| `rej_0175c1657e62c90cc2266540` | `aspec_5abca2fa010fc9e7174e0d7d` | `vwap_session` | `duplicate` | `reject` | `vwap-transition-distance` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_0175c1657e62c90cc2266540.json` |
| `rej_39942b4314a2d73d6b2d6806` | `aspec_668088ee803855ce3e5617e6` | `vwap_session` | `duplicate` | `reject` | `vwap-distance-baseline` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_39942b4314a2d73d6b2d6806.json` |
| `rej_7107e99008c6a7aaf7d2d5b4` | `aspec_8c9bc3ea6722e507f02b94de` | `vwap_session` | `duplicate` | `revise` | `vwap-reclaim-reject` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_7107e99008c6a7aaf7d2d5b4.json` |
| `rej_edeac064bfc49a96e4a561e4` | `aspec_ee701ec09d58e30b746c8e06` | `vwap_session` | `duplicate` | `revise` | `vwap-overnight-level` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_edeac064bfc49a96e4a561e4.json` |

## Evidence References

- StudySpec pack: `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md`
- Critiques and duplicate-exposure hints: `research/futures_core_alpha_pilot_v1/critiques/README.md` and `research/futures_core_alpha_pilot_v1/critiques/**/*.md`
- Diagnostics reports: `research/futures_core_alpha_pilot_v1/diagnostics_reports/**`
- Cost consolidation: `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md`
- Session/horizon/regime matrix: `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md`
- No-lookahead audit: `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`
- Variant-budget audit: `research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md`
- Statistical reviewer verdicts: `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md`

## Boundary Confirmation

- Records are value-free: ids, statuses, categories, counts, hash references,
  duplicate-exposure hints, and repo-relative evidence paths only.
- No raw/canonical market data, feature values, label values, signal values,
  provider responses, Parquet/Arrow/Feather payloads, SQLite/DB files, logs,
  caches, model binaries, secrets, or credentials are embedded.
- No `runs/**` artifact is referenced as a commit-eligible ledger artifact.
- No consumed primitive under `src/alpha_system/**` was edited by this ledger.
