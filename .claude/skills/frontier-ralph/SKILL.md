---
description: Advance the Frontier Ralph strict loop by reading run state and performing the next state-machine action.
---

Read:

- `AGENTS.md`
- `frontier.yaml`
- `ACTIVE_CAMPAIGN.md`
- `campaigns/<ID>/*`
- `runs/<RUN_ID>/state.json`
- `runs/<RUN_ID>/progress.txt`
- `runs/<RUN_ID>/prd.json`

Actions:

- load campaign
- select next phase
- generate phase spec
- interpret review verdict
- decide repair, checkpoint, or block
- perform semantic done-check
- update state, progress, and events
- write `RUN_SUMMARY.md`

Do not chat casually. Advance state.

Generated Ralph tooling is a scaffold until provider integrations and merge gates are implemented for this project.
