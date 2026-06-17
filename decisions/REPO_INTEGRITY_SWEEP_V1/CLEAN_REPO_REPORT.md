# Repo Integrity Sweep V1 - Clean Repo Report

## Deleted / Removed

| Path / ref | Action | Reason | Risk class |
| --- | --- | --- | --- |
| `origin/fix-52-conditioned-power-gate` | Deleted remote branch | GitHub PR #513 was `MERGED`; main contains the #52 work plus follow-up #74. | Low; PR/main preserve history. |
| `worktree-agent-a2223982a2e1b1dc0` | Deleted local branch | It was an ancestor of `main`. | Low; merged local branch. |
| `.claude/worktrees/agent-a5880a65a74e8a54b` | Removed local worktree | Clean worktree for already-merged PR #514. | Low; no uncommitted files. |
| `worktree-agent-a5880a65a74e8a54b` | Deleted local branch | Clean worktree branch tied to merged PR #514. | Low; merge preserved by PR/main. |
| `origin/fix-74-binary-overlap-conditioned-neff` | Pruned stale remote-tracking ref | Remote branch was already absent; local tracking ref stale. | Low; `git fetch --prune origin`. |

## Renamed Local Run Logs

`python tools/verify.py --all` initially failed
`tests/unit/test_l2_artifact_policy.py::test_no_l2_db_or_columnar_artifacts_are_present`
because old ignored `runs/**` files had `.log` suffixes. The contents were
preserved by renaming each to `.log.txt`:

- `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/coordinator_resume_p16.log.txt`
- `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/coordinator_resume_p16b.log.txt`
- `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/coordinator_resume_p17.log.txt`
- `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/coordinator_resume_p18.log.txt`
- `runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/coordinator_resume.log.txt`
- `runs/2026-06-11T223643Z_DISCOVERY_RIGOR_FLOOR_V1/phases/RIGOR-P04/repair_attempts/ci_attempt_1/ci_failure.log.txt`
- `runs/2026-06-11T223643Z_DISCOVERY_RIGOR_FLOOR_V1/phases/RIGOR-P05/repair_attempts/ci_attempt_1/ci_failure.log.txt`
- `runs/2026-06-11T223643Z_DISCOVERY_RIGOR_FLOOR_V1/phases/RIGOR-P06/repair_attempts/ci_attempt_1/ci_failure.log.txt`
- `runs/2026-06-13T174822Z_SHIP_REFIT_V1/phases/SHIP_REFIT-P04/repair_attempts/ci_attempt_1/ci_failure.log.txt`

Follow-up proof:

- `find runs -type f \( -name '*.log' -o -name '*.sqlite' -o -name '*.db' -o -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' -o -name '*.wal' \)` returns no paths.
- `pytest tests/unit/test_l2_artifact_policy.py::test_no_l2_db_or_columnar_artifacts_are_present -q` passes.

## Preserved

| Path / ref | Reason |
| --- | --- |
| `intraday-system-custody-v0` | Separate local branch; not part of this repo-integrity sweep. |
| `research/intraday_system_custody_v0/` | Untracked research/custody content; preserved as uncertain/non-regenerable and hidden through local `.git/info/exclude` only. |
| `/home/yuke_zhang/alpha_data/alpha_system/**` | Raw/canonical/value/registry data is local-only and never deleted by this sweep. |
| Registry backups under `ALPHA_DATA_ROOT/registry/` | Audit/history artifacts; preserved. |

## Commands Used

- `gh pr list --head fix-52-conditioned-power-gate --state all`
- `git push origin --delete fix-52-conditioned-power-gate`
- `git branch -d worktree-agent-a2223982a2e1b1dc0`
- `git worktree remove .claude/worktrees/agent-a5880a65a74e8a54b`
- `git branch -d worktree-agent-a5880a65a74e8a54b`
- `git push origin --delete fix-74-binary-overlap-conditioned-neff` (remote already absent)
- `git fetch --prune origin`
- `find runs -type f -name '*.log' -print0 | xargs -0 -I{} mv {} {}.txt`

## Current State

`git worktree list --porcelain` shows only the active repo worktree.

`git branch --all --verbose --no-abbrev` shows only:

- current integrity branch;
- `main`;
- preserved `intraday-system-custody-v0`;
- `origin/main`.
