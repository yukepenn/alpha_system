# Handoffs

Executor handoffs transfer context when work pauses, resumes, or changes owners.
They are commit-eligible and record scope completion, validation, artifacts,
known issues, and next-phase prerequisites. Run-local handoffs under
`runs/<RUN_ID>/phases/<PHASE_ID>/handoff.md` are **not** committed.

## Layout convention

Every campaign's phase handoffs live under `handoffs/<CAMPAIGN_ID>/<PHASE_ID>.md`.
**New campaigns: always write under `handoffs/<CAMPAIGN_ID>/`.**

### Campaign handoff directories (index)

- `handoffs/ALPHA_SYSTEM_V1/` — `ASV1-P00.md` … `ASV1-P29.md` (P17 never produced),
  `ASV1-HYGIENE.md`, plus bootstrap/repair handoffs.
- `handoffs/ALPHA_DATA_FOUNDATION_V1/` — `DATA-P00.md` … `DATA-P24.md`, plus the ADF1
  data / backfill / Databento / post-closeout handoffs (`ADF1_*.md`).
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/` — `ARGOV-P00.md` … `ARGOV-P19.md`.
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/` — RT-MVP phase handoffs.
- `handoffs/ALPHA_AGENT_FACTORY_MVP/` — AGENT phase handoffs.
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/` — FLF phase handoffs.
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/` — FUTCORE phase handoffs.
- `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/` — FCFP phase handoffs.
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/` — FUTSUB phase handoffs (in-flight).

The ALPHA_SYSTEM_V1 phase handoffs (and the ADF1 `ADF1_*` handoffs) were relocated
from flat top-level into these subdirectories on 2026-06-05 via `git mv`
(content and history preserved); the campaign-contract path references were updated
to match.

## Top-level (cross-cutting, not a single campaign's phase series)

- `PRE_FEATURE_REPO_CONSOLIDATION_V1.md`, `PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1.md`,
  `POST_RUNTIME_FEATURE_LABEL_STORAGE_AND_SEED_PACKS_V1.md`,
  `WF2_PARALLEL_DAG_SCHEDULER_MVP.md` — repo-wide / cross-cutting records.
- `000-template.md` — the handoff template.

> `FUTSUB-P04.md` and `FUTSUB-P12.md` were relocated from the flat top level into
> `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/` via `git mv` (content and
> history preserved), matching the `handoffs/<CAMPAIGN_ID>/` convention the campaign
> specs reference.

## Template

Use `000-template.md` as the starting point for a new handoff.
