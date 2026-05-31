# G005 Acceptance

Acceptance criteria:

- `python tools/frontier/ralph_driver.py run --campaign-id G005_WORKFLOW2_TOY` completes locally without provider, network, GitHub, browser, merge, deployment, or trading calls.
- The driver creates `docs/toy_workflow2/phase_a.md`.
- The driver creates `docs/toy_workflow2/phase_b.md`.
- The driver creates `docs/toy_workflow2/summary.md`.
- The run directory contains `RUN_GOAL.md`, `PHASE_PLAN.md`, `state.json`, `events.jsonl`, `progress.txt`, `RUN_SUMMARY.md`, and `STOP`.
- Each of the three phase directories contains `spec.md`, `handoff.md`, `review.md`, and `verdict.json`.
- If a `STOP` file exists before the next phase starts, the driver records a stopped run and preserves completed phase artifacts.
