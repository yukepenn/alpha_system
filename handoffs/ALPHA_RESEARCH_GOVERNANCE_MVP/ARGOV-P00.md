# ARGOV-P00 Handoff — Governance Campaign Bootstrap

## Summary

Created the governance documentation root for `ALPHA_RESEARCH_GOVERNANCE_MVP`:

- `docs/governance/README.md` introduces the admissibility and evidence-governance layer, hard governance rules, governance object list, lifecycle summary, prohibited future-only state names, and campaign contract pointers.
- `docs/governance/GOVERNANCE_OVERVIEW.md` summarizes the admissibility protocol, object families, lifecycle states from `DRAFT` through `VALIDATED`, blocked transitions, prohibited MVP state names, and the evidence-governance posture.
- `README.md` was refreshed as a compact repository snapshot for the governance campaign, including current campaign progress, active phase, next phase, newly added docs, and unchanged safety boundaries.
- `ACTIVE_CAMPAIGN.md` continues to point to `ALPHA_RESEARCH_GOVERNANCE_MVP` and records the active run/phase without recording a phase PASS verdict.

No campaign contract files were rewritten.

## Staged Files

Actual staged files:

- none; `git diff --cached --name-only` returned empty after the staging attempt failed.

The explicit staging command attempted was:

```bash
git add ACTIVE_CAMPAIGN.md README.md docs/governance/README.md docs/governance/GOVERNANCE_OVERVIEW.md handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P00.md
```

It failed with:

```text
fatal: Unable to create '/home/yuke_zhang/projects/alpha_system/.git/index.lock': Read-only file system
```

Intended commit-eligible files for staging:

- `ACTIVE_CAMPAIGN.md`
- `README.md`
- `docs/governance/README.md`
- `docs/governance/GOVERNANCE_OVERVIEW.md`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P00.md`

No `runs/**` path is staged.

## Validation Results

- `git status --short` — succeeded. Output showed only commit-eligible allowed paths:
  - `M ACTIVE_CAMPAIGN.md`
  - `M README.md`
  - `?? docs/governance/`
  - `?? handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/`
- `test -f ACTIVE_CAMPAIGN.md` — succeeded.
- `test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/GOAL.md` — succeeded.
- `test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/PHASE_PLAN.md` — succeeded.
- `test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/campaign.yaml` — succeeded.
- `test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/ACCEPTANCE.md` — succeeded.
- `test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/RISK_REGISTER.md` — succeeded.
- `test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/RUNBOOK.md` — succeeded.
- `test ! -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/ACTIVE_CAMPAIGN.md` — succeeded.
- `test -f docs/governance/README.md` — succeeded.
- `test -f docs/governance/GOVERNANCE_OVERVIEW.md` — succeeded.
- `test -f README.md` — succeeded.
- `test -f handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P00.md` — succeeded.
- `grep -q "ALPHA_RESEARCH_GOVERNANCE_MVP" ACTIVE_CAMPAIGN.md` — succeeded.
- `python tools/verify.py --smoke` — succeeded.
- `git ls-files runs` — succeeded with empty output.

Optional safe artifact audits:

- `find data -type f ! -name README.md ! -name ".gitkeep" -print` — succeeded with empty output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` — succeeded with empty output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` — succeeded with empty output.

Contract consistency check:

- `python - <<'PY' ...` confirming `campaign.yaml` and `PHASE_PLAN.md` agree for `ARGOV-P00` on ID, phase name, YELLOW lane, and no dependencies — succeeded with output: `ARGOV-P00 campaign.yaml and PHASE_PLAN.md consistency confirmed`.

Skipped checks: none.

## Artifact Policy

- `git ls-files runs` returned empty.
- `git diff --cached --name-only` returned empty after the failed staging attempt, so no `runs/**` path was staged.
- No raw data, canonical data, factor data, label data, cache data, local DB file, log, heavy artifact, or Parquet artifact was staged.
- `runs/<run_id>/phases/ARGOV-P00/handoff.md` was not created or staged.
- No `review.md` or `verdict.json` was created.

## Staging Discipline

- Explicit staging only.
- Explicit staging was attempted with only the five intended commit-eligible paths, but the repository metadata directory was read-only in this session and `.git/index.lock` could not be created.
- `git add .` was not used.
- `git add -A` was not used.
- No force push was performed.
- No commit was created because staging was blocked by the read-only `.git` filesystem.

## Scope Confirmation

- No `src/**` source was added or modified.
- No `tests/**` files were added or modified.
- No configs, templates, or CLI surfaces were added.
- No broker, live, paper, order-routing, real-data-ingestion, alpha-search, L2-replay, ML/DL, optimization, or portfolio-allocation scope was added.
- No alpha, profitability, tradability, or production-readiness claims were added.

## Contract Consistency Note

The campaign contract bundle is present under `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/`. For `ARGOV-P00`, `campaign.yaml` and `PHASE_PLAN.md` agree on phase ID, phase name, YELLOW lane, and no dependencies. The generated phase spec applies the more conservative artifact rule for this executor run by treating `runs/**` as local-only and including the root `README.md` snapshot as commit-eligible.
