# ASV1-P00A Workflow2 Ledger-Only Runner Handoff

## Branch

`feat/ASV1-P00A-workflow2-ledger`

## Commit

`ASV1-P00A: implement ledger-only workflow2 runner`

## Files Changed

* `tools/frontier/ralph_driver.py`
* `tests/test_ralph_driver.py`
* `handoffs/ALPHA_SYSTEM_V1/ASV1-P00A_WORKFLOW2_LEDGER_ONLY_RUNNER.md`

## Scope Completed

Implemented dedicated ledger-only Workflow2 support for `ALPHA_SYSTEM_V1`.

The runner now:

* validates the required campaign contract files exist,
* reads `GOAL.md`, `PHASE_PLAN.md`, and `campaign.yaml`,
* parses `ASV1-P00` through `ASV1-P29` from `PHASE_PLAN.md`,
* cross-checks parsed phase name, lane, and dependencies against `campaign.yaml`,
* creates `runs/<timestamp>_ALPHA_SYSTEM_V1/`,
* writes `RUN_GOAL.md`, `PHASE_PLAN.md`, `state.json`, `events.jsonl`, `progress.txt`, `costs.jsonl`, `RUN_SUMMARY.md`, and `STOP`,
* leaves every parsed phase as `PENDING` with `execution_mode: ledger_only`,
* records zero provider cost and safety flags showing no provider, network, GitHub, PR, merge, deployment, broker, live trading, or paper trading operation occurred,
* handles resume by inspecting/refreshing ledger state and never executing phase bodies.

The existing `G005_WORKFLOW2_TOY` deterministic local execution path is unchanged in behavior and still completes.

## Validation Run

Passed:

* `python -m pytest`
* `python -m compileall tools`
* `just frontier-doctor`
* `just verify-canaries`
* `python tools/frontier/ralph_driver.py run --campaign-id G005_WORKFLOW2_TOY`
* `rm -rf docs/toy_workflow2`
* `rm -rf runs/*G005_WORKFLOW2_TOY*`
* `python tools/frontier/ralph_driver.py run --campaign-id ALPHA_SYSTEM_V1`
* required `latest_run` file checks for `state.json`, `events.jsonl`, `RUN_SUMMARY.md`, and `STOP`
* required Python state assertion: `ALPHA_SYSTEM_V1 ledger-only state OK 30`
* `just frontier-run-campaign ALPHA_SYSTEM_V1`
* `python tools/verify.py --artifacts`

Generated `G005_WORKFLOW2_TOY` docs/runs and generated `ALPHA_SYSTEM_V1` runs were removed before commit so run evidence is not committed as durable source.

## Non-Runs

No phase implementation was executed for `ALPHA_SYSTEM_V1`.

The driver did not call Claude, Codex, OpenAI, Anthropic, GitHub, IBKR, network providers, broker systems, live trading, paper trading, PR creation, or merge operations.

## Risks And Caveats

This is intentionally not a real Ralph execution loop. It only creates durable ledger state and safety artifacts.

The campaign parser fails on malformed or inconsistent campaign files instead of guessing. This is deliberate, but a future campaign contract format change may require updating the parser.

`STOP` is written by default for ledger-only runs. On resume, an existing `STOP` marks the run as `STOPPED` and refreshes the summary without execution.

## Review Focus

* Confirm `G005_WORKFLOW2_TOY` behavior remains unchanged.
* Confirm `ALPHA_SYSTEM_V1` state shape matches the requested ledger-only schema.
* Confirm parsed phase metadata matches the campaign contract and all phase statuses remain `PENDING`.
* Confirm no provider, network, GitHub, PR, merge, broker, live trading, or paper trading path was introduced.

## Next Recommended Step

Review this ledger-only runner, then use it as the readiness baseline before implementing provider-wired Ralph phase selection, spec generation, execution, review, PR, and merge gates in later scoped work.
