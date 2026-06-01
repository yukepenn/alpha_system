# ASV1-P00B Provider-Wired Workflow2 Conductor and CI Fix Handoff

## Branch

`feat/ASV1-P00B-provider-wired-workflow2`

## Commit

Planned commit: `ASV1-P00B: implement provider-wired workflow2 conductor and CI fix`

## Files Changed

- `.github/workflows/frontier-ci.yml`
- `PROJECT_STATUS.md`
- `docs/workflow.md`
- `justfile`
- `tests/test_ralph_driver.py`
- `tools/frontier/ralph_driver.py`
- `tools/verify.py`
- `handoffs/ALPHA_SYSTEM_V1/ASV1-P00B_PROVIDER_WIRED_WORKFLOW2_MINIMUM_VIABLE_CONDUCTOR_AND_CI_FIX.md`

## Scope Completed

- Added ALPHA_SYSTEM_V1 provider-wired Workflow 2 conductor mode with Claude spec generation, Codex execution, validation, Claude review, conservative verdict parsing, one bounded repair attempt, run artifacts, STOP handling, and resume support.
- Preserved ALPHA_SYSTEM_V1 ledger-only mode and G005 toy Workflow 2 behavior.
- Implemented `FRONTIER_MOCK_PROVIDERS=1` deterministic mock-provider mode for safe local tests and smoke runs.
- Updated just recipes so `frontier-run-campaign` is aggressive campaign-loop mode, while `frontier-run-next` and `FRONTIER_MAX_PHASES=1` run one phase.
- Fixed `frontier-ci` fresh-runner pytest dependency failure and safe no-tests handling.

## Validation Run

- `python -m compileall tools tests` passed.
- `python -m pytest` passed.
- `python tools/verify.py --test` passed.
- `python tools/verify.py --ci` passed.
- `just frontier-doctor` passed.
- `just verify-canaries` passed.
- `FRONTIER_MOCK_PROVIDERS=1 python tools/frontier/ralph_driver.py run --campaign-id ALPHA_SYSTEM_V1 --provider-wired --max-phases 1` passed.
- Required state assertion for the one-phase mock run passed with 30 parsed phases and exactly one `PASS`.
- `FRONTIER_MAX_PHASES=2 just frontier-run-campaign-mock ALPHA_SYSTEM_V1` passed.
- `python tools/verify.py --artifacts` passed.

## Non-Runs

- Real provider-wired phase execution was not run during validation because this phase only requires safe mock-provider execution before commit.
- No PR creation, CI polling, merge gate automation, auto-merge, deployment, broker operation, paper trading, live trading, or IBKR action was run.

## Risks Or Caveats

- Real provider mode shells out to local `claude -p` and `codex exec --sandbox workspace-write`; it depends on those CLIs being configured in the execution environment.
- Budget and time stop gates are not yet enforced beyond phase-count limits and the hard STOP/BLOCKED/validation/review gates.
- CI/PR creation and auto-merge remain intentionally unimplemented.

## Review Request Focus

- Check the provider-wired state transitions, STOP semantics, and max-phase precedence.
- Check that CI no-tests handling skips only genuinely absent tests and does not mask real pytest failures.
- Check that no broker/live/paper/IBKR or merge automation behavior was introduced.

## Next Recommended Step

Run CI on the pushed branch, then review whether ASV1-P00C should add real budget/time accounting and PR/CI gate stubs before any auto-merge integration.
