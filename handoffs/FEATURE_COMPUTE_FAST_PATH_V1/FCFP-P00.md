# FCFP-P00 Handoff

Summary: Bootstrapped the `FEATURE_COMPUTE_FAST_PATH_V1` campaign pointer and
documentation scaffold, confirmed the campaign phase/lanes match the phase plan,
and kept run/value/heavy artifacts out of commit-eligible paths.

## Files For Ralph To Stage

Codex did not stage files because the executor prompt explicitly prohibited
`git add`, `git commit`, `git push`, `git status`, and `git diff`. Ralph should
stage only these commit-eligible paths:

- `ACTIVE_CAMPAIGN.md`
- `README.md`
- `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/campaign.yaml`
- `docs/feature_compute_fast_path/README.md`
- `docs/feature_compute_fast_path/OVERVIEW.md`
- `research/feature_compute_fast_path_v1/README.md`
- `research/feature_compute_fast_path_v1/.gitkeep`
- `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P00.md`

## Git Status

`git status --short` was not run. The executor prompt explicitly prohibited
`git status`; changes were left unstaged for Ralph.

## Scope Completed

- Confirmed the 6-file campaign bundle exists:
  `GOAL.md`, `PHASE_PLAN.md`, `campaign.yaml`, `ACCEPTANCE.md`,
  `RISK_REGISTER.md`, and `RUNBOOK.md`.
- Updated `campaign.yaml` so phase `allowed_paths` no longer include `runs/**`;
  `runs/**` remains only in local-only / never-commit policy sections.
- Added the fast-path docs index under `docs/feature_compute_fast_path/`.
- Added the value-free evidence skeleton under
  `research/feature_compute_fast_path_v1/`.
- Refreshed the root `ACTIVE_CAMPAIGN.md` pointer for
  `FEATURE_COMPUTE_FAST_PATH_V1`, with `Next phase: FCFP-P01`.
- Updated the root `README.md` snapshot to show `1/16` phases complete, `FCFP-P01`
  next, the new docs/evidence skeleton, and unchanged safety boundaries.
- Confirmed no campaign-local
  `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/ACTIVE_CAMPAIGN.md` exists.

No source code, tests, registry paths, value stores, data paths, run artifacts,
review artifacts, `review.md`, or `verdict.json` were created or edited.

## Validation Results

- `test ! -f runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/STOP`: PASS.
- `test ! -f runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/phases/FCFP-P00/STOP`: PASS.
- `git status --short`: SKIPPED. Executor prompt forbids `git status`.
- `test -f campaigns/FEATURE_COMPUTE_FAST_PATH_V1/GOAL.md`: PASS.
- `test -f campaigns/FEATURE_COMPUTE_FAST_PATH_V1/PHASE_PLAN.md`: PASS.
- `test -f campaigns/FEATURE_COMPUTE_FAST_PATH_V1/campaign.yaml`: PASS.
- `test -f campaigns/FEATURE_COMPUTE_FAST_PATH_V1/ACCEPTANCE.md`: PASS.
- `test -f campaigns/FEATURE_COMPUTE_FAST_PATH_V1/RISK_REGISTER.md`: PASS.
- `test -f campaigns/FEATURE_COMPUTE_FAST_PATH_V1/RUNBOOK.md`: PASS.
- `test '!' -f campaigns/FEATURE_COMPUTE_FAST_PATH_V1/ACTIVE_CAMPAIGN.md`: PASS.
- `test -f ACTIVE_CAMPAIGN.md`: PASS.
- `grep -q "FEATURE_COMPUTE_FAST_PATH_V1" ACTIVE_CAMPAIGN.md`: PASS.
- `test -f docs/feature_compute_fast_path/README.md`: PASS.
- `test -f docs/feature_compute_fast_path/OVERVIEW.md`: PASS.
- `test -f research/feature_compute_fast_path_v1/README.md`: PASS.
- `test -f research/feature_compute_fast_path_v1/.gitkeep`: PASS.
- `test -f handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P00.md`: PASS.
- `python -c "import yaml; yaml.safe_load(open('campaigns/FEATURE_COMPUTE_FAST_PATH_V1/campaign.yaml'))"`:
  PASS, no output.
- Campaign phase consistency script: PASS.
  Output:

  ```text
  campaign.yaml parses; 16 phases FCFP-P00..FCFP-P15; lanes match PHASE_PLAN.md; no runs/** in phase allowed_paths
  ```

- `python tools/verify.py --smoke`: PASS, no output.
- `git ls-files runs`: PASS, empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.db' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst'`:
  PASS, empty output.

## README Snapshot

The root README now records `FEATURE_COMPUTE_FAST_PATH_V1` as the active campaign,
`1/16` phases complete after `FCFP-P00`, and `FCFP-P01` as the active/next phase.
It lists the new docs index and value-free evidence skeleton, and states that no
engine modules, parity harness, CLI commands, registry writes, benchmarks, feature
values, or label values were added in this phase.

Safety boundaries remain unchanged: the reference engine stays the oracle;
resolver exact-id semantics and official serial registry writes are unchanged;
the campaign remains Green/Yellow only with no Red scope; `runs/**`, raw/canonical
data, values, local SQLite, provider responses, and heavy artifacts remain
local-only; no profitability or tradability claim is made.

## Skipped Checks

- `git status --short` was skipped because the executor prompt explicitly forbade
  running `git status`.
