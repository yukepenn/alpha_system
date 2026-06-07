# FUTCORE-P28 PromotionDecision Index

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P28`  
Artifact type: value-free PromotionDecision index

## Boundary

This directory records one bounded PromotionDecision for each accepted
StudySpec carried into the evidence gate. The only assigned states are
`REJECT` and `INCONCLUSIVE`; no idea is assigned `WATCH` or
`CANDIDATE_RESEARCH`.

The records cite upstream artifacts by path only. They do not rerun
diagnostics, rescore ideas, perform Reference validation, create paper/live
readiness, or make broker, production, capital, tradability, or return claims.

## Gating Summary

| Item | Count |
| --- | ---: |
| Accepted StudySpecs covered | 10 |
| `REJECT` | 4 |
| `INCONCLUSIVE` | 6 |
| `WATCH` | 0 |
| `CANDIDATE_RESEARCH` | 0 |
| `WATCH` + `CANDIDATE_RESEARCH` | 0 |
| Maximum allowed `WATCH` + `CANDIDATE_RESEARCH` | 2 |

All six P27 survivors have independent P25 reviewer verdict artifacts, and all
six P25 verdicts are `INCONCLUSIVE` with watch/candidate budget impact `0`.
Because the independent reviewer did not support `WATCH` or
`CANDIDATE_RESEARCH`, P28 assigns each survivor `INCONCLUSIVE`.

The four non-survivor accepted StudySpecs are `REJECT` because P16 rejected
their cross-market diagnostic source before P25; P26 records their
failed-diagnostics RejectedIdeaLedger entries.

## Decision Table

| StudySpec | AlphaSpec | Family | Decision | Reviewer verdict ref | Ledger/evidence refs | Duplicate hint |
| --- | --- | --- | --- | --- | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | `aspec_0ebd90cecfd475607685b445` | `cross_market` | `REJECT` | not applicable: pre-P25 rejection | `trial_b4e25da7c409809fc1cb54b7`; `rej_c27b447c282967db390ff10d` | `cm-lead-lag-pair` |
| `sspec_c671fbeeb143512cbc03bc5b` | `aspec_8d9e272e4b78eedcd27f0bec` | `cross_market` | `REJECT` | not applicable: pre-P25 rejection | `trial_587d6da288aa8ff2ca25fa37`; `rej_9ed40aaf995f1f70f5f94cdf` | `cm-beta-residual` |
| `sspec_90b28233d828128664588a9a` | `aspec_a41dcccac5552de945aba825` | `cross_market` | `REJECT` | not applicable: pre-P25 rejection | `trial_bdbfa08dcf63fe1fe8e5921d`; `rej_20d88b59ce09f47d364fd529` | `cm-rty-rotation` |
| `sspec_7c8fb13628843890c171b122` | `aspec_fa4895a43a80d4eef0a607a4` | `cross_market` | `REJECT` | not applicable: pre-P25 rejection | `trial_1fc87c34cf31d8055d3d224d`; `rej_fa471f1ddeaa066dc4a95feb` | `cm-pair-divergence` |
| `sspec_69c22ec5847395ac8e81b5b6` | `aspec_b40aee52d4399dd5b855a6ed` | `vwap_session` | `INCONCLUSIVE` | `reviewer_verdict_sspec_69c22ec5847395ac8e81b5b6.json` | `trial_fffbb48dc4111caeabcc55c9`; `evidence_draft_sspec_69c22ec5847395ac8e81b5b6.json`; `rej_7107e99008c6a7aaf7d2d5b4` | `vwap-reclaim-reject` |
| `sspec_aff70fcbc4b7ff226fcc8149` | `aspec_43cd6c154bca2fcc419eee83` | `vwap_session` | `INCONCLUSIVE` | `reviewer_verdict_sspec_aff70fcbc4b7ff226fcc8149.json` | `trial_3b8f60dd0f4793288360159e`; `evidence_draft_sspec_aff70fcbc4b7ff226fcc8149.json` | `vwap-rth-open-eth` |
| `sspec_267cc052e37668339c38d179` | `aspec_eb962fc197eaf3955c5e4711` | `regime` | `INCONCLUSIVE` | `reviewer_verdict_sspec_267cc052e37668339c38d179.json` | `trial_94781614f100a2aa0878aae4`; `trial_13c98257a704ce5641a51626`; `trial_58fdb5456d910efccdd95b7b`; `trial_fce335815b1bda26eb898aed`; `evidence_draft_sspec_267cc052e37668339c38d179.json` | `regime-trend-vol-range` |
| `sspec_27bf1262b0bd23d27191cc86` | `aspec_df2d040e45564c259ef3de6d` | `liquidity_pa` | `INCONCLUSIVE` | `reviewer_verdict_sspec_27bf1262b0bd23d27191cc86.json` | `trial_666433ac863d5adb1368a3d1`; `evidence_draft_sspec_27bf1262b0bd23d27191cc86.json` | `pa-sweep-closeback` |
| `sspec_02c400a561891171a33c0c66` | `aspec_39ffc190cfbfa6ba0b1a2a25` | `liquidity_pa` | `INCONCLUSIVE` | `reviewer_verdict_sspec_02c400a561891171a33c0c66.json` | `trial_45df4e0c5999da63a57ff9b2`; `evidence_draft_sspec_02c400a561891171a33c0c66.json` | `pa-failed-breakout` |
| `sspec_9f6f741192a4b534f06e51c0` | `aspec_1284e49b083df11eeb0481ea` | `bbo_tradability` | `INCONCLUSIVE` | `reviewer_verdict_sspec_9f6f741192a4b534f06e51c0.json` | `trial_2ae03a839098b6ff741b2f84`; `trial_4ee4909066d85d4abcdfaa42`; `trial_3a61fa6378614054674171ec`; `trial_2c32c84a140e6e99f67f5aa8`; `evidence_draft_sspec_9f6f741192a4b534f06e51c0.json` | `bbo-spread-depth-confirmation` |

## Files

- Aggregate index: `research/futures_core_alpha_pilot_v1/promotion/decisions.json`
- Human-readable promotion table:
  `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`
- Per-idea decision records:
  `research/futures_core_alpha_pilot_v1/promotion/decisions/*.json`

## Artifact Policy

The promotion directory contains JSON and Markdown references only. It contains
no raw provider data, feature values, label values, row-level diagnostics,
Parquet, Arrow, Feather, DBN, Zstd, SQLite, DB files, model binaries, logs,
caches, secrets, run-local files, PR state, or merge state.
