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

Ralph tooling is provider-wired and live for this project: `tools/frontier/`
implements the provider config/adapters, DAG-wave scheduler, merge gate, verdict
parser, and the strict driver loop (`ralph_driver.py`), and has driven real
multi-phase Workflow 2 campaigns end to end. Treat it as production automation,
not a scaffold; respect its STOP/resume semantics and merge gates.
