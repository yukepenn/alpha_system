# Sync Frontier Template Final Runs Optional Doctor Repair Handoff

## Branch

`sync/frontier-template-final`

## Commit

Planned commit: `sync(frontier): make local run dir optional`

## Files Changed

- `tools/frontier/bootstrap.py`
- `tests/test_bootstrap.py`
- `handoffs/ALPHA_SYSTEM_V1/SYNC_FRONTIER_TEMPLATE_FINAL_RUNS_OPTIONAL_DOCTOR_REPAIR.md`

## Scope Completed

- Removed `runs` from the bootstrap doctor hard-required path list.
- Kept `runs/` as local-only runtime state: missing `runs/` now emits an informational note and does not fail doctor.
- Added tests proving doctor returns success with `runs/` absent and does not create `runs/`.
- Added a regression test proving missing required paths still fail without reporting `runs` as required.
- Left artifact policy, CI, branch protection, review, and merge gate configuration unchanged.

## Validation Run

Passed:

- `python -m pytest tests/test_bootstrap.py`
- `python -m pytest`
- `python tools/hooks/canary_runner.py`
- `python tools/verify.py --artifacts`
- `python tools/verify.py --all`
- `rm -rf runs`
- `python tools/frontier/bootstrap.py doctor`
- `grep -RIn 'name,state,conclusion' tools tests || true`
- `grep -RIn 'require_branch_protection: false\|allow_unprotected_green_merge: true' tools tests frontier.yaml || true`
- `git ls-files runs .frontier/upgrade_reports`

## Clean Checkout Note

`git clone --depth 1 --branch sync/frontier-template-final https://github.com/yukepenn/alpha_system.git /tmp/alpha_ci_check || true` succeeded, but the remote branch was stale before this local commit. The cloned `tools/frontier/bootstrap.py` still hard-required `runs`, so the local working tree was used for the manual clean-check doctor validation.

## Non-Runs

No `runs/` files, `.frontier/upgrade_reports/` files, raw data, caches, broker calls, live trading, paper trading, PR creation, merge, or deployment operation was introduced.

## Review Focus

- Confirm `runs/` is no longer a hard bootstrap doctor requirement.
- Confirm doctor does not create `runs/`.
- Confirm branch protection and unprotected merge controls remain unchanged.
