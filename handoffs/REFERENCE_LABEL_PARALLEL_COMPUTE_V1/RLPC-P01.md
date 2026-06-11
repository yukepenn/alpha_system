# RLPC-P01 Handoff

Campaign: `REFERENCE_LABEL_PARALLEL_COMPUTE_V1`
Phase: `RLPC-P01` - Reference-Engine Unit-Parallel Worker Path
Lane: YELLOW

## Summary

Implemented the reference-engine label worker orchestration path in
`src/alpha_system/features/scaleout/driver.py`. Reference label scaleout now
allows explicit worker parallelism for default-executor label configs, dispatches
disjoint runnable units through a spawn `ProcessPoolExecutor`, and keeps label
registry registration serial in the parent process in deterministic unit order.
The parent appends the checkpoint ledger only after successful registration,
matching the existing v1 worker contract.

The worker entrypoint computes and writes reference label values only. It returns
a value-free manifest/output object and does not open or write the label
registry. The parent reconstructs records from the Parquet value handle when
needed and registers with `LabelRegistry.register_materialized_label` using the
existing reference producer metadata.

Updated `src/alpha_system/cli/scaleout.py` help text so
`alpha scaleout label-pack --engine reference --workers N` is documented as an
explicit opt-in policy. Default workers remain 1 through the existing
`ALPHA_LABEL_CPU_WORKERS` then `ALPHA_CPU_WORKERS` convention.

Added synthetic unit tests under
`tests/unit/reference_label_parallel_compute/` for deterministic parent
registration order, per-unit failure retryability, worker-plan caps/defaults,
checkpoint-after-registration ordering, parent-only registration structure, and
reference worker thread caps.

Updated the root README snapshot for RLPC-P01.

## File List

Commit-eligible files created or modified:

- `src/alpha_system/features/scaleout/driver.py`
- `src/alpha_system/cli/scaleout.py`
- `tests/unit/reference_label_parallel_compute/test_reference_worker_parallelism.py`
- `README.md`
- `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/RLPC-P01.md`

Local-only file created:

- `runs/2026-06-11T015152Z_REFERENCE_LABEL_PARALLEL_COMPUTE_V1/phases/RLPC-P01/handoff.md`

No review artifacts, `review.md`, `verdict.json`, PR, merge, or PASS marker were
created by the executor.

## Git / Artifact Evidence

`git status --short` was not run because the executor prompt explicitly forbids
`git status`. This conflicts with the generated spec validation list; the safety
override was followed and this exception is recorded here.

No `git add`, `git commit`, `git push`, `git status`, or `git diff` command was
run by the executor. The executor did not stage anything.

`git ls-files runs` was run and produced no output.

No forbidden label oracle path was edited:

- `src/alpha_system/labels/engine.py`
- `src/alpha_system/labels/families/**`
- `src/alpha_system/labels/roll_guard.py`
- `src/alpha_system/labels/version.py`

No data, value, SQLite, Parquet, Arrow, Feather, log, cache, secret, broker,
live, execution, portfolio, strategy, backtest, or FUTSUB run/worktree path was
modified.

## Validation Results

- `python tools/frontier/status_doctor.py` - WARN, not blocking for executor:
  active campaign pointer is `REFERENCE_LABEL_PARALLEL_COMPUTE_V1`; no live run
  dir with `state.json` was found for this campaign; hooksPath warning reported.
- `PYTHONPATH=src python -m pytest tests/unit/reference_label_parallel_compute -q`
  - PASS, `6 passed`.
- `PYTHONPATH=src python -m pytest tests/unit/feature_compute_fast_path/test_scaleout_worker_parallelism.py -q`
  - PASS, `5 passed`.
- `env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES PYTHONPATH=src python tools/verify.py --smoke`
  - PASS, exit code 0 with no output.
- `PYTHONPATH=src python tools/hooks/canary_runner.py` - PASS, all Frontier
  canaries passed.
- `git ls-files runs` - PASS, output empty.
- `git status --short` - NOT RUN. Reason: explicit executor prompt forbids
  `git status`.

## Residual Risks

RLPC-P02 still owns exact workers=1 vs workers>1 equivalence, interruption
resume, and single-writer audit coverage. RLPC-P03 still owns real-data bounded
benchmarking and release decision. This phase did not run real data, benchmark,
paper/live/broker operations, or production deployment.

The reference worker compute helper uses private reference-engine validation and
write helpers to avoid editing the reference engine while supporting multi-input
label units. This preserves the oracle files byte-for-byte from the executor's
edits, but RLPC-P02 should exercise exact equivalence across worker counts.

## Scope Notes

Edits were limited to the generated spec's allowed source, CLI, test, README,
and handoff paths plus the required run-local handoff. The paused FUTSUB run,
registry rows, checkpoints, materialized values, and worktree were not touched.
