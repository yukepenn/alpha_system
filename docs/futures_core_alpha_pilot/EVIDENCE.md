# FUTCORE-P27 EvidenceDrafts And Reference Handoffs

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P27`  
Durable docs page for value-free survivor evidence packaging

P27 assembles the P25/P26 survivor evidence into one value-free artifact package
per survivor under `research/futures_core_alpha_pilot_v1/evidence/**`. The
artifacts cite upstream AlphaSpecs, StudySpecs, diagnostics, cost/thin-session
reports, matrix records, no-lookahead audits, variant-budget audits, P25
verdicts, TrialLedger records, and linked RejectedIdeaLedger records by id,
repo-relative path, and content hash.

The artifacts are candidate inputs for later review only. They are not
promotion decisions, Reference validation, paper/live readiness, broker
authorization, deployment evidence, profitability evidence, or capital guidance.

## Survivor Set

P27 derives survivors from the P26 TrialLedger plus the P25 statistical reviewer
verdict artifacts. The survivor set contains six unique StudySpecs, all with
P25 judgement `INCONCLUSIVE`.

| StudySpec | Family | P26 TrialLedger records | Duplicate hint | Linked RejectedIdea refs |
| --- | --- | ---: | --- | --- |
| `sspec_69c22ec5847395ac8e81b5b6` | `vwap_session` | 1 | `vwap-reclaim-reject` | `rej_7107e99008c6a7aaf7d2d5b4` |
| `sspec_aff70fcbc4b7ff226fcc8149` | `vwap_session` | 1 | `vwap-rth-open-eth` | none exact |
| `sspec_267cc052e37668339c38d179` | `regime` | 4 | `regime-trend-vol-range` | none exact |
| `sspec_27bf1262b0bd23d27191cc86` | `liquidity_pa` | 1 | `pa-sweep-closeback` | none exact |
| `sspec_02c400a561891171a33c0c66` | `liquidity_pa` | 1 | `pa-failed-breakout` | none exact |
| `sspec_9f6f741192a4b534f06e51c0` | `bbo_tradability` | 4 | `bbo-spread-depth-confirmation` | none exact |

## Artifact Index

- `research/futures_core_alpha_pilot_v1/evidence/survivors.json` records the
  survivor derivation and artifact paths.
- `research/futures_core_alpha_pilot_v1/evidence/INDEX.md` is the detailed
  evidence artifact index.
- `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/*.json`
  contains runtime-surface `EvidenceDraft` records.
- `research/futures_core_alpha_pilot_v1/evidence/factor_cards/*.json` contains
  FactorCard drafts for later review input.
- `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/*.json`
  contains runtime-surface `ReferenceCandidateHandoff` records.

## Runtime Surfaces

The EvidenceDraft objects were assembled through
`alpha_system.runtime.evidence.draft.EvidenceDraft` and governance evidence
bundle validation. The handoff objects were assembled through
`alpha_system.runtime.handoff.reference.ReferenceCandidateHandoff`.

All six P27 EvidenceDraft decisions remain `INCONCLUSIVE`, matching the P25
statistical reviewer judgement. P27 does not recast the evidence as ready,
validated, or promoted.

## Boundaries

The P27 artifacts are value-free: ids, hashes, statuses, references, summary
metadata, limitations, and conservative labels only. They contain no raw
provider payloads, row-level market values, feature values, label values,
runtime value tables, Parquet/Arrow/Feather payloads, DBN/Zstd files, SQLite or
DB files, run-local artifacts, logs, caches, secrets, model binaries, reviewer
artifacts, PR state, or merge state.
