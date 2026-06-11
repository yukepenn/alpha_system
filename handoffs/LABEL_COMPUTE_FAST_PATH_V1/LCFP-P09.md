# LCFP-P09 Handoff

Phase: `LCFP-P09` - FUTSUB Reintegration Handoff + Closeout

Lane: `YELLOW`

This handoff does not mark the phase PASS. Ralph owns staging, validation ledger
updates, review routing, verdict parsing, PR creation, CI, merge gates, merge,
done-check, and any FUTSUB coordinator actions. Codex left changes unstaged and
did not create review or verdict artifacts.

## What Was Written

- `research/label_compute_fast_path_v1/closeout/CLOSEOUT.md` records a
  `COMPLETE` closeout verdict, the five acceptance status fields, parity
  evidence from P07, benchmark evidence from P08, local validation outcomes,
  and the recommended coordinator-owned `ACTIVE_CAMPAIGN.md` repoint back to
  FUTSUB.
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_REINTEGRATION_ON_FAST_LABELS.md`
  gives coordinator-only amendment, P16-P20 reset/rerun, resume, worktree
  cleanup, and preserve-don't-delete registry/value rules.
- `docs/label_compute_fast_path/README.md`,
  `docs/label_compute_fast_path/OVERVIEW.md`,
  `research/label_compute_fast_path_v1/README.md`, and `README.md` were updated
  as concise closeout snapshots.

## Closeout Verdict Basis

Verdict: `COMPLETE`, subject to Ralph-owned review/merge/done-check.

Basis:

- P07 parity report covers required value, `label_available_ts`, identity,
  roll-crossing guard, maintenance-crossing guard, same-bar policy, gap/quality
  flags, `HorizonOverlapMetadata`, and no-lookahead dimensions.
- P08 benchmark summary selects fast only for `fixed_base` (1.03x, requested
  workers 8) and `path` (10.23x, requested workers 8); it selects reference for
  `fixed_extended`, `close_out`, and `cost_adjusted` because reference remains
  faster.
- P06 integration report records bounded execute/checkpoint/registry/resolver
  evidence, including fail-closed preservation of existing reference-lineage
  rows.
- This phase executed no FUTSUB amendment, reset, resume, registry mutation, or
  value write.

## Validation

Requested validation:

- `git status --short`
  - Not run. The executor prompt explicitly forbids `git status`; Ralph owns
    git state inspection.
- `python tools/verify.py --smoke`
  - Passed, exit `0`.
  - Exact command:
    `env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES -u FRONTIER_DISABLE_AUTOMERGE -u FRONTIER_MOCK_PROVIDERS -u FRONTIER_SCHEDULER_MODE -u FRONTIER_RESUME_PHASE -u FRONTIER_NO_PROVIDER_REPLAY PYTHONPATH=src python tools/verify.py --smoke`
- `python tools/hooks/canary_runner.py`
  - Passed, exit `0`; all Frontier canaries passed.
  - Exact command:
    `env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES -u FRONTIER_DISABLE_AUTOMERGE -u FRONTIER_MOCK_PROVIDERS -u FRONTIER_SCHEDULER_MODE -u FRONTIER_RESUME_PHASE -u FRONTIER_NO_PROVIDER_REPLAY PYTHONPATH=src python tools/hooks/canary_runner.py`
- `test -f research/label_compute_fast_path_v1/closeout/CLOSEOUT.md`
  - Passed, exit `0`.
- `test -f handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_REINTEGRATION_ON_FAST_LABELS.md`
  - Passed, exit `0`.
- `git ls-files runs`
  - Passed, exit `0`; output was empty.
- `git ls-files '**/*.parquet' '**/*.sqlite'`
  - Passed, exit `0`; output was empty.
- `python tools/verify.py --all`
  - First run failed, exit `1`, in the inherited `ALPHA_DATA_ROOT`
    environment:
    `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`
    expected `RUN_ARTIFACTS` but resolved `ALPHA_DATA_ROOT`. This is the known
    environment-only cache-policy red when `ALPHA_DATA_ROOT` is exported.
  - Exact failed command:
    `env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES -u FRONTIER_DISABLE_AUTOMERGE -u FRONTIER_MOCK_PROVIDERS -u FRONTIER_SCHEDULER_MODE -u FRONTIER_RESUME_PHASE -u FRONTIER_NO_PROVIDER_REPLAY PYTHONPATH=src python tools/verify.py --all`
  - Clean rerun with `ALPHA_DATA_ROOT` unset passed, exit `0`:
    `3009 passed, 70 skipped in 49.64s`. The embedded status doctor reported
    `WARN` because this worktree has no LCFP run dir with `state.json`, but the
    full command exited `0`.
  - Exact clean command:
    `env -u ALPHA_DATA_ROOT -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES -u FRONTIER_DISABLE_AUTOMERGE -u FRONTIER_MOCK_PROVIDERS -u FRONTIER_SCHEDULER_MODE -u FRONTIER_RESUME_PHASE -u FRONTIER_NO_PROVIDER_REPLAY PYTHONPATH=src python tools/verify.py --all`

Additional read-only checks performed before writing:

- The prompt-named LCFP run artifact directory was not present in this worktree;
  no `runs/**` artifact was created.
- FUTSUB pause state was rechecked read-only:
  STOP present; `state.json` stale `RUNNING` at `FUTSUB-P19`; status counts
  `PASS=1`, `PASS_WITH_WARNINGS=18`, `PENDING=14`, `SPEC_READY=1`; P14 and P19
  worktree directories exist; cost-adjusted local-only value/checkpoint counts
  remain 181/181/181 plus `completed_units.jsonl`; local label registry file
  exists. No Parquet payload, registry row, or label value was opened.

## Files Changed For Ralph To Stage

Codex did not run `git status`, `git diff`, `git add`, `git commit`, or
`git push`. The list below is based on files intentionally edited or generated
by this executor turn:

- `README.md`
- `docs/label_compute_fast_path/README.md`
- `docs/label_compute_fast_path/OVERVIEW.md`
- `research/label_compute_fast_path_v1/README.md`
- `research/label_compute_fast_path_v1/closeout/CLOSEOUT.md`
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_REINTEGRATION_ON_FAST_LABELS.md`
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P09.md`

Executor staging status: none staged by Codex.

## Boundary Notes

- No live trading, paper trading, broker operation, order routing, production
  deployment, external provider call, PR, merge, review call, `review.md`, or
  `verdict.json` was performed or created by Codex.
- No `ACTIVE_CAMPAIGN.md`, FUTSUB campaign/spec file, `runs/**` state, source,
  test, registry, value-store, or label-semantics file was edited.
- The reintegration handoff is coordinator-only and preserves the reference
  label engine as the parity oracle forever.
