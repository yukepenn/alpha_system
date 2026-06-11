# RLPC-P02 Handoff

Campaign: `REFERENCE_LABEL_PARALLEL_COMPUTE_V1`
Phase: `RLPC-P02` - Determinism, Single-Writer, and Interruption-Resume Gate
Lane: YELLOW

## Summary

Implemented the RLPC-P02 synthetic correctness gate for the reference-label
unit-parallel worker path.

The new test suite runs a synthetic fixed-horizon plus cost-adjusted-shaped
label grid through `run_scaleout` at workers=1 and workers=4. The workers=4
path uses the real spawn `ProcessPoolExecutor` stage with a picklable synthetic
reference worker output, then exercises the real parent-side serial registry
writer, label registry, checkpoint ledger, and resume checks. Equality is exact
via canonical serialization with root-path normalization only; there are no
tolerances, rounding knobs, or known-diff allowlists.

Interruption coverage includes a worker failure followed by resume and a parent
abort after completed checkpoint append between serial registrations. The
assertions cover duplicate-free completed checkpoints, no holes in registered
units, final registry/data-root snapshot equality to an uninterrupted run, and
completed checkpoint rows 1:1 with registered units.

Single-writer coverage includes a registry-open audit around the real worker
entrypoint, a canary proving `labels.sqlite` opens fail loudly, and a source/
signature guard that fails if the worker entrypoint grows registry-writer
symbols.

## Files Changed

Commit-eligible files created or modified:

- `src/alpha_system/features/scaleout/driver.py`
- `tests/unit/reference_label_parallel_compute/test_determinism_resume_single_writer.py`
- `research/reference_label_parallel_compute_v1/determinism/RLPC-P02_SYNTHETIC_DETERMINISM.md`
- `README.md`
- `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/RLPC-P02.md`

No run-local handoff, `review.md`, `verdict.json`, PR, merge, or PASS marker was
created by the executor.

## Driver Touches

`driver.py` was touched for two orchestration-only reasons:

- Added `REFERENCE_LABEL_WORKER_ENTRYPOINT`, a default alias to the existing
  `_reference_label_worker_compute_entrypoint`, so tests can submit a picklable
  synthetic worker through the real spawn pool without changing production
  behavior.
- Preserved the optional `horizon` field in `_record_from_payload`. The ledger
  already writes `horizon`; dropping it during rehydration made cost-adjusted
  completed checkpoints rehydrate as default-horizon units, causing registry
  truth checks to miss and append duplicate completed checkpoint rows on resume.

No label math, label families, roll guard, label versioning, CLI flags, default
worker policy, broker/live/execution path, or data artifact path was edited.

## Validation Results

- `python -m pytest tests/unit/reference_label_parallel_compute -q` - PASS:
  `12 passed, 1 skipped in 6.14s`. Skip reason: optional real-slice spot-check
  requires local real data, optional dependencies, and an explicitly isolated
  namespace; the synthetic gate is authoritative in CI.
- `python -m pytest tests/unit/feature_compute_fast_path/test_scaleout_worker_parallelism.py -q`
  - PASS: `5 passed in 0.25s`.
- `python tools/verify.py --smoke` - PASS, exit code 0 with no output.
- `python tools/hooks/canary_runner.py` - PASS: all Frontier canaries passed.
- `git ls-files runs` - PASS, output empty.
- `git status --short` - NOT RUN. Reason: the executor prompt explicitly
  forbids `git status`; this safety override conflicts with the generated spec
  validation list. No staging command was run by the executor.

Additional exploratory check:

- `PYTHONPATH=src python - <<'PY' import polars ... PY` - FAILED with
  `ModuleNotFoundError: No module named 'polars'`. This is why the optional
  real-slice spot-check was not run locally.

## Artifact Evidence

No `git add`, `git commit`, `git push`, `git status`, or `git diff` command was
run by the executor. The executor did not stage anything.

`git ls-files runs` returned no tracked run paths.

Filesystem sanity check found no `*.sqlite`, `*.db`, `*.parquet`, `*.arrow`,
`*.feather`, or `*.log` artifacts in the worktree outside `.git`. The pytest run
created ignored `__pycache__` files under `tests/unit/reference_label_parallel_compute/`;
they are local cache artifacts and are not part of the changed-file list.

The value-free determinism evidence under
`research/reference_label_parallel_compute_v1/determinism/` contains counts,
coverage dimensions, and booleans only; it stores no label values, Parquet,
SQLite, logs, provider responses, or run artifacts.

## Optional Real-Slice Spot-Check

Skipped. The local executor environment does not have `polars` installed, and no
explicit isolated real-data namespace was provided. No `$ALPHA_DATA_ROOT`
production registry, paused FUTSUB run directory, paused FUTSUB worktree,
checkpoint, or materialized value path was read or written for this phase.

## Residual Risks

The synthetic worker output is intentionally value-free and does not benchmark
or validate real Parquet contents. RLPC-P03 still owns the bounded real-data
benchmark and release decision. This phase makes no speedup, alpha,
profitability, tradability, paper/live, broker, or production deployment claim.
