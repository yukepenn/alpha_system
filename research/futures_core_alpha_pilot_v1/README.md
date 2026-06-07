# Futures Core Alpha Pilot Research Evidence

`research/futures_core_alpha_pilot_v1/` is the commit-eligible, value-free
research evidence root for `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`.

This tree starts as scaffolding in `FUTCORE-P00`. Later phases may add
AlphaSpec drafts and critiques, StudySpecs, diagnostics reports, cost/session/
regime/no-lookahead summaries, TrialLedger and RejectedIdeaLedger records,
EvidenceDrafts, reviewer verdict references, promotion decisions, and downstream
handoffs when their phase specs authorize those artifacts.

## Artifact Rules

- Store only value-free research evidence: ids, references, summaries,
  decisions, limitations, warnings, and review links.
- Do not store raw market data, canonical data, provider responses, materialized
  feature values, materialized label values, per-row diagnostics, Parquet, Arrow,
  Feather, DBN, Zstd, SQLite, DB files, logs, caches, secrets, or credentials.
- Do not copy run-local artifacts from `runs/**` into this tree unless a later
  phase explicitly creates a value-free commit-eligible summary.
- Keep report language conservative and consistent with
  `docs/RESEARCH_INTERPRETATION_POLICY.md`.

## Current Contents

- `README.md` - this evidence-tree contract.
- `.gitkeep` - placeholder so the evidence root exists before later phases
  populate it.
