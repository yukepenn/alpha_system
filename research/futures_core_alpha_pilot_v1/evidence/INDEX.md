# FUTCORE-P27 Evidence Artifact Index

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
Phase: `FUTCORE-P27`
Artifact type: value-free EvidenceDraft, FactorCard draft, and ReferenceCandidateHandoff index for P26/P25 survivors

## Boundary

These artifacts package existing evidence by id, path, and content hash only. They do not rerun diagnostics, rescore ideas, assign promotion decisions, perform Reference validation, create paper/live readiness, or make profitability or capital claims.

Every survivor artifact is labeled `candidate-for-later-review`, `not validated`, and `not tradable`. This is a conservative handoff label for future review input only.

## Survivor Derivation

- TrialLedger source: `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/trial_ledger.json` / `50ff07aee4b4580b8ecbcd877fe1c51e3fc46f1672164b69b246cdf965f677d2`
- RejectedIdeaLedger source: `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/rejected_idea_ledger.json` / `3959b0253258f15bcdb5f37260a90f3dcf7b45e6022716fa343a4297bfe9c00d`
- P25 statistical reviewer record: `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/statistical/FUTCORE-P25.md` / `5e4327c69741456c25faae6a48a717c9d5e6b3793f7f8ed45b2d730aabecbe63`
- Survivor count: `6` unique StudySpecs with P25 `INCONCLUSIVE` verdict artifacts recorded in P26.

## Artifact Table

| StudySpec | AlphaSpec | Family | P25 judgement | Trial count | Duplicate hint | Linked rejected ids | EvidenceDraft | FactorCard draft | ReferenceCandidateHandoff |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| `sspec_69c22ec5847395ac8e81b5b6` | `aspec_b40aee52d4399dd5b855a6ed` | `vwap_session` | `INCONCLUSIVE` | 1 | `vwap-reclaim-reject` | `rej_7107e99008c6a7aaf7d2d5b4` | `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/evidence_draft_sspec_69c22ec5847395ac8e81b5b6.json` | `research/futures_core_alpha_pilot_v1/evidence/factor_cards/factor_card_sspec_69c22ec5847395ac8e81b5b6.json` | `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_69c22ec5847395ac8e81b5b6.json` |
| `sspec_aff70fcbc4b7ff226fcc8149` | `aspec_43cd6c154bca2fcc419eee83` | `vwap_session` | `INCONCLUSIVE` | 1 | `vwap-rth-open-eth` | `none exact` | `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/evidence_draft_sspec_aff70fcbc4b7ff226fcc8149.json` | `research/futures_core_alpha_pilot_v1/evidence/factor_cards/factor_card_sspec_aff70fcbc4b7ff226fcc8149.json` | `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_aff70fcbc4b7ff226fcc8149.json` |
| `sspec_267cc052e37668339c38d179` | `aspec_eb962fc197eaf3955c5e4711` | `regime` | `INCONCLUSIVE` | 4 | `regime-trend-vol-range` | `none exact` | `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/evidence_draft_sspec_267cc052e37668339c38d179.json` | `research/futures_core_alpha_pilot_v1/evidence/factor_cards/factor_card_sspec_267cc052e37668339c38d179.json` | `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_267cc052e37668339c38d179.json` |
| `sspec_27bf1262b0bd23d27191cc86` | `aspec_df2d040e45564c259ef3de6d` | `liquidity_pa` | `INCONCLUSIVE` | 1 | `pa-sweep-closeback` | `none exact` | `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/evidence_draft_sspec_27bf1262b0bd23d27191cc86.json` | `research/futures_core_alpha_pilot_v1/evidence/factor_cards/factor_card_sspec_27bf1262b0bd23d27191cc86.json` | `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_27bf1262b0bd23d27191cc86.json` |
| `sspec_02c400a561891171a33c0c66` | `aspec_39ffc190cfbfa6ba0b1a2a25` | `liquidity_pa` | `INCONCLUSIVE` | 1 | `pa-failed-breakout` | `none exact` | `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/evidence_draft_sspec_02c400a561891171a33c0c66.json` | `research/futures_core_alpha_pilot_v1/evidence/factor_cards/factor_card_sspec_02c400a561891171a33c0c66.json` | `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_02c400a561891171a33c0c66.json` |
| `sspec_9f6f741192a4b534f06e51c0` | `aspec_1284e49b083df11eeb0481ea` | `bbo_tradability` | `INCONCLUSIVE` | 4 | `bbo-spread-depth-confirmation` | `none exact` | `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/evidence_draft_sspec_9f6f741192a4b534f06e51c0.json` | `research/futures_core_alpha_pilot_v1/evidence/factor_cards/factor_card_sspec_9f6f741192a4b534f06e51c0.json` | `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_9f6f741192a4b534f06e51c0.json` |

## Runtime Surface Consumption

- `alpha_system.runtime.evidence.draft.EvidenceDraft` validated each EvidenceDraft runtime object.
- `alpha_system.runtime.handoff.reference.ReferenceCandidateHandoff` validated each handoff runtime object.
- `alpha_system.governance.evidence_bundle.create_evidence_bundle` validated governance evidence input payloads.

## Artifact Policy

The evidence directory contains JSON and Markdown references only. It contains no raw provider data, feature values, label values, row-level diagnostics, Parquet, Arrow, Feather, DBN, Zstd, SQLite, DB files, model binaries, logs, caches, secrets, run-local files, reviewer artifacts, PR state, or merge state.
