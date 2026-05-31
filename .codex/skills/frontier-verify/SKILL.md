---
name: frontier-verify
description: Verify that a Frontier change is ready for review and records required checks.
---
# frontier-verify

Use this skill to verify that a change is ready for review.

## Checklist

- Scope matches the active campaign or spec.
- Validation commands were run and recorded.
- Generated artifacts are intentional.
- No secrets, credentials, or machine-local paths were added.
- Human review requirements for profile `trading_research` are satisfied.
- Lane-specific checks in `frontier.yaml` are recorded.
- Canary checks are run for yellow and red lanes when configured.
