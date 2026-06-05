# Handoffs

Executor handoffs transfer context when work pauses, resumes, or changes owners.
They are commit-eligible and record scope completion, validation, artifacts,
known issues, and next-phase prerequisites. Run-local handoffs under
`runs/<RUN_ID>/phases/<PHASE_ID>/handoff.md` are **not** committed.

## Layout convention (current vs historical)

Two layouts coexist on purpose:

- **`ALPHA_SYSTEM_V1` (the first campaign) uses flat top-level paths** —
  `handoffs/ASV1-P00.md` … `handoffs/ASV1-P29.md` (plus `ASV1-HYGIENE.md`). These
  paths are **frozen historical evidence**: the campaign contract
  `campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md` references them by exact path, so they
  are deliberately **not** relocated. (`handoffs/ALPHA_SYSTEM_V1/` separately holds
  that campaign's bootstrap/repair handoffs.)
- **Every later and future campaign uses a per-campaign subdirectory** —
  `handoffs/<CAMPAIGN_ID>/<PHASE_ID>.md`:
  - `handoffs/ALPHA_DATA_FOUNDATION_V1/` — `DATA-P00.md` … `DATA-P24.md`.
  - `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/` — `ARGOV-P00.md` … `ARGOV-P19.md`.

**New campaigns: write under `handoffs/<CAMPAIGN_ID>/`. Do not add new flat
top-level phase handoffs.**

## Cross-campaign / task handoffs (top level)

- `ADF1_DATABENTO_ES_NQ_RTY_OHLCV_BBO_DEEP_HISTORY.md` — Databento Phase B (primary deep-history).
- `ADF1_LOCAL_RESEARCH_DATA_BACKFILL.md`, `ADF1_FULL_RESEARCH_DATA_BACKFILL.md` — IBKR backfill tasks.
- `ADF1_POST_CLOSEOUT_AUDIT_AND_CONSOLIDATION.md` — earlier post-closeout consolidation.
- `PRE_FEATURE_REPO_CONSOLIDATION_V1.md` — pre-Feature/Label consolidation (this pass).

## Template

Use `000-template.md` as the starting point for a new handoff.
