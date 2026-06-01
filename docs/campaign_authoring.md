# Campaign Authoring

Campaigns are durable goal contracts. Create them under `campaigns/<CAMPAIGN_ID>/`.

Each campaign should include:

- `GOAL.md`
- `PHASE_PLAN.md`
- `campaign.yaml`
- `ACCEPTANCE.md`
- `RISK_REGISTER.md`
- `RUNBOOK.md`

Each phase should define:

- id
- lane
- dependencies
- purpose
- scope
- non-goals
- expected files
- forbidden changes
- validation
- artifact policy
- done criteria
- handoff requirement
- review requirement
- merge eligibility
- whether no-diff completion is acceptable for docs/check-only phases

Generic harness behavior belongs in harness files. Project-specific behavior belongs in `frontier.yaml`, campaign files, project skill files, profile config, source, configs, and project tests.

Workflow2 done-checks compare the phase spec, changed files, handoff, validation, review, verdict, `AGENTS.md`, `frontier.yaml`, and campaign requirements. Write campaign acceptance criteria concretely enough that the semantic done-check can distinguish done from incomplete.
