# PromotionDecision Summary

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P28`

## Decision Boundary

P28 records bounded research-state outcomes for the 10 accepted StudySpecs that
entered the evidence gate. The allowed campaign states are `REJECT`,
`INCONCLUSIVE`, `WATCH`, and `CANDIDATE_RESEARCH`.

No idea is assigned `WATCH` or `CANDIDATE_RESEARCH` because no independent P25
Statistical Reviewer verdict supports either state. The resulting
`WATCH` + `CANDIDATE_RESEARCH` count is `0`, within the campaign cap of `2`.

These records are not Reference validation and are not paper, live, broker,
production, capital, tradability, or return decisions.

## Decisions

| StudySpec | AlphaSpec | Family | State | Rationale |
| --- | --- | --- | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | `aspec_0ebd90cecfd475607685b445` | `cross_market` | `REJECT` | P16 rejected the source before explicit variant-grid execution because required NQ and RTY legs were missing; P26 recorded failed diagnostics. |
| `sspec_c671fbeeb143512cbc03bc5b` | `aspec_8d9e272e4b78eedcd27f0bec` | `cross_market` | `REJECT` | P16 rejected the source before explicit variant-grid execution because required NQ and RTY legs were missing; P26 recorded failed diagnostics. |
| `sspec_90b28233d828128664588a9a` | `aspec_a41dcccac5552de945aba825` | `cross_market` | `REJECT` | P16 rejected the source before explicit variant-grid execution because required NQ and RTY legs were missing; P26 recorded failed diagnostics. |
| `sspec_7c8fb13628843890c171b122` | `aspec_fa4895a43a80d4eef0a607a4` | `cross_market` | `REJECT` | P16 rejected the source before explicit variant-grid execution because required NQ and RTY legs were missing; P26 recorded failed diagnostics. |
| `sspec_69c22ec5847395ac8e81b5b6` | `aspec_b40aee52d4399dd5b855a6ed` | `vwap_session` | `INCONCLUSIVE` | P25 remains inconclusive due unresolved VWAP/session FeaturePack binding, unresolved 15m label pack context, and carried P23 timing/label flags. |
| `sspec_aff70fcbc4b7ff226fcc8149` | `aspec_43cd6c154bca2fcc419eee83` | `vwap_session` | `INCONCLUSIVE` | P25 remains inconclusive due unresolved ETH VWAP / first-RTH running VWAP binding, unproven intraday final aggregate use, and carried P23 timing/label flags. |
| `sspec_267cc052e37668339c38d179` | `aspec_eb962fc197eaf3955c5e4711` | `regime` | `INCONCLUSIVE` | P25 remains inconclusive due missing locked trendiness and activation binding, rejected source probe arms in P22 context, and carried P23 timing/label flags. |
| `sspec_27bf1262b0bd23d27191cc86` | `aspec_df2d040e45564c259ef3de6d` | `liquidity_pa` | `INCONCLUSIVE` | P25 remains inconclusive due unresolved objective trigger counts without a locked structure FeaturePack, unresolved thin-session subsegments, and carried P23 timing/label flags. |
| `sspec_02c400a561891171a33c0c66` | `aspec_39ffc190cfbfa6ba0b1a2a25` | `liquidity_pa` | `INCONCLUSIVE` | P25 remains inconclusive due unresolved objective trigger counts without a locked structure FeaturePack, unresolved thin-session subsegments, and carried P23 timing/label flags. |
| `sspec_9f6f741192a4b534f06e51c0` | `aspec_1284e49b083df11eeb0481ea` | `bbo_tradability` | `INCONCLUSIVE` | P25 remains inconclusive because no locked BBO FeaturePack resolves, detailed RTH session cost cells are zero-fill or inconclusive, and P23 timing/label flags remain carried. |

## Provenance

- P25 reviewer verdicts:
  `research/futures_core_alpha_pilot_v1/reviewer_verdicts/**`
- P26 ledgers:
  `research/futures_core_alpha_pilot_v1/ledgers/**`
- P27 survivor evidence:
  `research/futures_core_alpha_pilot_v1/evidence/**`
- Promotion records:
  `research/futures_core_alpha_pilot_v1/promotion/decisions/*.json`
- Aggregate decision index:
  `research/futures_core_alpha_pilot_v1/promotion/decisions.json`
