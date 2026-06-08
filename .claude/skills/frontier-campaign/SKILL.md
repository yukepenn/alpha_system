---
description: "Create or refine a Frontier campaign contract (GOAL, PHASE_PLAN, campaign.yaml, ACCEPTANCE, RISK_REGISTER, RUNBOOK)."
---

Read:

- `CRITICAL.md`
- `AGENTS.md`
- `frontier.yaml`
- `ACTIVE_CAMPAIGN.md`
- existing `campaigns/`
- `docs/ARCHITECTURE.md`

For current campaign/phase status, run `just status-doctor` (or read
`runs/<run_id>/state.json`). Do not read `PROJECT_STATUS.md` / `PROGRESS.md` for
live status; they are historical and lag the running campaign.

Write:

- `campaigns/<CAMPAIGN_ID>/GOAL.md`
- `campaigns/<CAMPAIGN_ID>/PHASE_PLAN.md`
- `campaigns/<CAMPAIGN_ID>/campaign.yaml`
- `campaigns/<CAMPAIGN_ID>/ACCEPTANCE.md`
- `campaigns/<CAMPAIGN_ID>/RISK_REGISTER.md`
- `campaigns/<CAMPAIGN_ID>/RUNBOOK.md`

Rules:

- Every phase must have id, lane, dependencies, purpose, scope, non-goals, expected files, forbidden changes, validation, artifact policy, done criteria, handoff requirement, review requirement, and auto-merge eligibility.
- Default to Workflow 2 strict autonomous execution when the campaign is well-scoped.
- Green and yellow phases should be auto-merge eligible only when policy gates pass.
- Red phases require scoped authorization and should not be handled ad hoc.
