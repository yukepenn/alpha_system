---
description: Adversarial cross-provider review of Codex implementation against spec.
---

Inputs:

- `AGENTS.md`
- `frontier.yaml`
- active spec
- git diff
- handoff
- validation output
- changed files

Outputs:

- `reviews/<CAMPAIGN_ID>/<PHASE_ID>-review.md`
- `reviews/<CAMPAIGN_ID>/<PHASE_ID>-verdict.json`

Verdicts:

- `PASS`
- `PASS_WITH_WARNINGS`
- `REWORK`
- `BLOCKED`

Always check:

- scope match
- hidden coupling
- missing done criteria
- test weakening
- test gaming
- artifact violations
- boundary violations
- future maintainability
- whether a fresh future agent can inherit safely
