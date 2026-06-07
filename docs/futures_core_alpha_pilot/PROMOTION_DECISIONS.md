# Promotion Decisions

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P28`

P28 records one bounded PromotionDecision for each of the 10 accepted
StudySpecs carried into the evidence gate.

| Outcome | Count |
| --- | ---: |
| `REJECT` | 4 |
| `INCONCLUSIVE` | 6 |
| `WATCH` | 0 |
| `CANDIDATE_RESEARCH` | 0 |
| `WATCH` + `CANDIDATE_RESEARCH` | 0 |

The campaign cap for `WATCH` + `CANDIDATE_RESEARCH` is `2`; the recorded count
is `0`. No survivor is assigned `WATCH` or `CANDIDATE_RESEARCH` because all six
independent P25 Statistical Reviewer verdicts are `INCONCLUSIVE`.

## Decision Table

| StudySpec | Family | Decision | Primary provenance |
| --- | --- | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | `cross_market` | `REJECT` | P26 `trial_b4e25da7c409809fc1cb54b7` and `rej_c27b447c282967db390ff10d` |
| `sspec_c671fbeeb143512cbc03bc5b` | `cross_market` | `REJECT` | P26 `trial_587d6da288aa8ff2ca25fa37` and `rej_9ed40aaf995f1f70f5f94cdf` |
| `sspec_90b28233d828128664588a9a` | `cross_market` | `REJECT` | P26 `trial_bdbfa08dcf63fe1fe8e5921d` and `rej_20d88b59ce09f47d364fd529` |
| `sspec_7c8fb13628843890c171b122` | `cross_market` | `REJECT` | P26 `trial_1fc87c34cf31d8055d3d224d` and `rej_fa471f1ddeaa066dc4a95feb` |
| `sspec_69c22ec5847395ac8e81b5b6` | `vwap_session` | `INCONCLUSIVE` | P25 `reviewer_verdict_sspec_69c22ec5847395ac8e81b5b6.json`; P27 `evidence_draft_sspec_69c22ec5847395ac8e81b5b6.json` |
| `sspec_aff70fcbc4b7ff226fcc8149` | `vwap_session` | `INCONCLUSIVE` | P25 `reviewer_verdict_sspec_aff70fcbc4b7ff226fcc8149.json`; P27 `evidence_draft_sspec_aff70fcbc4b7ff226fcc8149.json` |
| `sspec_267cc052e37668339c38d179` | `regime` | `INCONCLUSIVE` | P25 `reviewer_verdict_sspec_267cc052e37668339c38d179.json`; P27 `evidence_draft_sspec_267cc052e37668339c38d179.json` |
| `sspec_27bf1262b0bd23d27191cc86` | `liquidity_pa` | `INCONCLUSIVE` | P25 `reviewer_verdict_sspec_27bf1262b0bd23d27191cc86.json`; P27 `evidence_draft_sspec_27bf1262b0bd23d27191cc86.json` |
| `sspec_02c400a561891171a33c0c66` | `liquidity_pa` | `INCONCLUSIVE` | P25 `reviewer_verdict_sspec_02c400a561891171a33c0c66.json`; P27 `evidence_draft_sspec_02c400a561891171a33c0c66.json` |
| `sspec_9f6f741192a4b534f06e51c0` | `bbo_tradability` | `INCONCLUSIVE` | P25 `reviewer_verdict_sspec_9f6f741192a4b534f06e51c0.json`; P27 `evidence_draft_sspec_9f6f741192a4b534f06e51c0.json` |

The authoritative machine-readable records live under
`research/futures_core_alpha_pilot_v1/promotion/`.

These records are research evidence only. They are not Reference validation and
are not paper, live, broker, production, capital, tradability, or return
decisions.
