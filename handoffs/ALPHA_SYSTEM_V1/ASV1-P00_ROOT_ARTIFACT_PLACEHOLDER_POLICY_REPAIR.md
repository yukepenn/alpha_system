# ASV1-P00 Root Artifact Placeholder Policy Repair Handoff

## Branch

`sync/frontier-root-artifact-placeholders`

## Commit

Planned commit: `sync(frontier): allow root artifact placeholders`

## Template Source

- `../frontier_harness_template` `main`
- Verified local `main` matches `origin/main`: `9f9a6d02fa2ab563949241eeba28be93958d1aaf`

## Files Changed

- `.gitignore`
- `frontier.yaml`
- `tests/test_canaries.py`
- `tests/test_frontier_config.py`
- `tests/test_git_utils.py`
- `tests/test_hooks.py`
- `tools/hooks/canary_runner.py`
- `handoffs/ALPHA_SYSTEM_V1/ASV1-P00_ROOT_ARTIFACT_PLACEHOLDER_POLICY_REPAIR.md`

## Scope Completed

- Synced the template artifact policy fix that explicitly allows root-level artifact placeholders.
- `frontier.yaml` now allows `artifacts/README.md`, `artifacts/.gitkeep`, and nested artifact placeholders while retaining `artifacts/**` forbids for real payloads.
- `.gitignore` now unignores root-level `artifacts/README.md` and `artifacts/.gitkeep`.
- Tests and canaries now cover root-level artifact placeholders and representative blocked artifact payloads.
- Left `require_branch_protection: true` and `allow_unprotected_green_merge: false` unchanged.
- Did not modify `campaigns/ALPHA_SYSTEM_V1`.

## Validation Run

Passed:

- `python -m pytest`
- `python tools/hooks/canary_runner.py`
- `python tools/verify.py --artifacts`
- `python tools/verify.py --all`
- Artifact placeholder policy smoke script from the repair request.
- `grep -RIn 'name,state,conclusion' tools tests || true`
- `grep -RIn 'require_branch_protection: false\|allow_unprotected_green_merge: true' tools tests frontier.yaml || true`
- `grep -RIn 'git add \.\|git add -A' tools tests || true`
- `git ls-files runs .frontier/upgrade_reports`

Notes:

- `python tools/verify.py --all` reported the repo's existing lint and typecheck scaffold notices, then passed pytest.
- The final grep and tracked-run-artifact checks returned no output.

## Non-Runs

No `runs/` files, `.frontier/upgrade_reports/` files, raw data, caches, databases, model artifacts, logs, heavy payloads, broker calls, live trading, paper trading, PR creation, merge, or deployment operation was introduced.

## Review Focus

- Confirm root-level artifact placeholders are allowed only as placeholders.
- Confirm real artifact payloads remain blocked, including pickle, joblib, parquet, run, and upgrade-report paths.
- Confirm branch protection and unprotected merge controls remain unchanged.
