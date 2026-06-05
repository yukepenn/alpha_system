# Handoffs

Executor handoffs transfer context when work pauses, resumes, or changes owners.
They are commit-eligible and record scope completion, validation, artifacts,
known issues, and next-phase prerequisites. Run-local handoffs under
`runs/<RUN_ID>/phases/<PHASE_ID>/handoff.md` are **not** committed.

## Layout convention

Every campaign's phase handoffs live under `handoffs/<CAMPAIGN_ID>/<PHASE_ID>.md`:

- `handoffs/ALPHA_SYSTEM_V1/` — `ASV1-P00.md` … `ASV1-P29.md` (P17 was never produced),
  `ASV1-HYGIENE.md`, plus the bootstrap/repair handoffs.
- `handoffs/ALPHA_DATA_FOUNDATION_V1/` — `DATA-P00.md` … `DATA-P24.md`, plus the ADF1
  data / backfill / Databento / post-closeout handoffs (`ADF1_*.md`).
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/` — `ARGOV-P00.md` … `ARGOV-P19.md`.

The ALPHA_SYSTEM_V1 phase handoffs (and the ADF1 `ADF1_*` handoffs) were relocated
from flat top-level into these subdirectories on 2026-06-05 via `git mv`
(content and history preserved); the campaign-contract path references were updated
to match. **New campaigns: always write under `handoffs/<CAMPAIGN_ID>/`.**

## Top-level (cross-cutting, not a single campaign's phase series)

- `PRE_FEATURE_REPO_CONSOLIDATION_V1.md` — repo-wide pre-Feature/Label consolidation record.
- `000-template.md` — the handoff template.

## Template

Use `000-template.md` as the starting point for a new handoff.
