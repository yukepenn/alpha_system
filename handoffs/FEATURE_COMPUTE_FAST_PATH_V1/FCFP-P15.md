# FCFP-P15 Handoff - Benchmark-Driven CPU Worker Parallelism

## Context

- Campaign: `FEATURE_COMPUTE_FAST_PATH_V1`
- Phase: `FCFP-P15`
- Lane: Yellow
- Executor staging: none
- Executor commits: none

The executor prompt explicitly forbade `git status`, `git diff`, `git add`,
`git commit`, `git push`, reviewer execution, review artifacts, PR creation,
merge, and PASS marking. Changes are left unstaged for Ralph.

The prompt-provided run artifact directory was absent in this checkout; there
is no `runs/` directory. No run-local handoff, review, or verdict artifact was
created.

## Files Changed

Executor-edited commit-eligible files:

```text
README.md
docs/feature_compute_fast_path/OVERVIEW.md
docs/feature_compute_fast_path/README.md
docs/feature_compute_fast_path/WORKER_PARALLELISM.md
handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P15.md
research/feature_compute_fast_path_v1/workers/worker_benchmark_summary.md
src/alpha_system/cli/scaleout.py
src/alpha_system/features/fast/__init__.py
src/alpha_system/features/fast/materializer.py
src/alpha_system/features/fast/worker.py
src/alpha_system/features/scaleout/__init__.py
src/alpha_system/features/scaleout/driver.py
src/alpha_system/labels/fast/materializer.py
tests/unit/feature_compute_fast_path/test_scaleout_worker_parallelism.py
tests/unit/futures_substrate_scaleout/features/test_cross_market_scaleout.py
tests/unit/futures_substrate_scaleout/scaleout/test_cross_market_scaleout_driver.py
tools/feature_compute_fast_path/worker_benchmark.py
```

## Scope Completed

- Added `--workers` and `ALPHA_CPU_WORKERS` with CLI precedence and default
  serial `1`.
- Added worker-plan reporting with explicit reductions for available cores,
  runnable units, and non-parallel surfaces.
- Added V1 worker compute orchestration using process workers for compute and a
  parent-only serial official registry writer.
- Moved V1 definition/request preparation into the parent process so workers do
  not open or write feature registries.
- Worker processes compute V1 values, write local Parquet, and write
  deterministic value-free manifests; parent rehydrates records from Parquet and
  registers via `PackMaterializer.register_pack` / `FeatureStore`.
- Added per-worker native thread pinning for `POLARS_MAX_THREADS`,
  `OMP_NUM_THREADS`, and `RAYON_NUM_THREADS`.
- Canonicalized feature and label record order before content hashing.
- Updated cross-market scaleout planning to one ES/NQ/RTY panel unit per year.
- Added worker-model docs, README snapshot, and a value-free worker benchmark
  runner.
- Added unit tests for worker control precedence, explicit caps, serial writer
  order, independent failed-unit handling, canonical hash order, and
  cross-market panel-level units.

## Benchmark Outcome

Registry backups created before benchmark attempts:

```text
/home/yuke_zhang/alpha_data/alpha_system/registry/features.sqlite.bak_fcfp_p15_20260609T055519Z
/home/yuke_zhang/alpha_data/alpha_system/registry/labels.sqlite.bak_fcfp_p15_20260609T055519Z
```

Benchmark local-only roots created:

```text
/home/yuke_zhang/alpha_data/alpha_system/fcfp_p15_worker_benchmark_20260609T055541Z
/home/yuke_zhang/alpha_data/alpha_system/fcfp_p15_worker_benchmark_20260609T060623Z
/home/yuke_zhang/alpha_data/alpha_system/fcfp_p15_worker_benchmark_20260609T061023Z
```

The real worker benchmark did not complete in this executor environment. A
value-free blocked summary was written at
`research/feature_compute_fast_path_v1/workers/worker_benchmark_summary.md`.

Chosen stable worker count: **not selected**.

Determinism/parity evidence:

- Synthetic/unit evidence passed for canonical feature hash order across record
  permutations.
- Synthetic/unit evidence passed for worker serial-writer ordering and failed
  unit isolation.
- Real `{1,2,4,8}` benchmark parity/resolver-smoke evidence was not produced;
  this remains a phase blocker for benchmark acceptance.

## Commands Run

```bash
python tools/frontier/status_doctor.py
```

Outcome: `VERDICT: WARN`; no run dir with `state.json` was present for
`FEATURE_COMPUTE_FAST_PATH_V1`; runtime contract was consistent.

```bash
python -m py_compile src/alpha_system/features/scaleout/driver.py src/alpha_system/cli/scaleout.py src/alpha_system/features/fast/worker.py src/alpha_system/features/fast/materializer.py src/alpha_system/labels/fast/materializer.py
```

Outcome: passed.

```bash
python -m pytest tests/unit/feature_compute_fast_path/test_scaleout_worker_parallelism.py tests/unit/futures_substrate_scaleout/features/test_cross_market_scaleout.py tests/unit/futures_substrate_scaleout/scaleout/test_cross_market_scaleout_driver.py -q
```

Outcome: `10 passed`.

```bash
python -m pytest tests/unit/futures_substrate_scaleout/ tests/unit/feature_compute_fast_path/ -q
```

Outcome: `99 passed`.

```bash
python tools/verify.py --smoke
```

Outcome: passed with exit code `0`.

```bash
python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q
```

Outcome: `12 passed`.

```bash
python tools/hooks/canary_runner.py
```

Outcome: all Frontier canaries passed.

```bash
test -f research/feature_compute_fast_path_v1/workers/worker_benchmark_summary.md
```

Outcome: passed with exit code `0`.

```bash
git ls-files runs
```

Outcome: empty.

```bash
git ls-files '**/*.parquet' '**/*.sqlite'
```

Outcome: empty.

Not run by executor due explicit prompt override:

```bash
git status --short
```

Outcome: not run; executor was forbidden to run `git status`.

## Artifact Discipline

- No `runs/**` path exists in this checkout.
- No run-local `handoff.md`, `review.md`, or `verdict.json` was created.
- `git ls-files runs` returned empty.
- `git ls-files '**/*.parquet' '**/*.sqlite'` returned empty.
- Benchmark values, local registries, checkpoints, manifests, and Parquet
  outputs remain under `ALPHA_DATA_ROOT` local-only roots listed above.

## Remaining Blocker — RESOLVED by coordinator

The executor's benchmark stall and parity gap were diagnosed and resolved by the
coordinator (the reviewer-sanctioned "coordinator runs the heavy real-data
benchmark unsandboxed" follow-up). Diagnosis found three root causes; the first
two are generic concurrency/validation fixes and the third re-derives the FLF-P05
request gate at registration time:

1. **Fork-after-threads deadlock (why the benchmark stalled even at workers=2).**
   `_compute_v1_stage_outputs_in_workers` used `ProcessPoolExecutor` with the
   Linux-default `fork` start method. The parent imports polars and runs canonical
   loads/job prep before forking, which initializes polars' Rayon thread pool;
   forked children inherit an inconsistent copy and deadlock on their first polars
   call. Fixed by using the `spawn` start method (`mp_context=get_context("spawn")`),
   which also makes the per-worker `POLARS_MAX_THREADS`/`OMP_NUM_THREADS`/
   `RAYON_NUM_THREADS` pins take effect (driver.py imports polars lazily, so the
   spawned child applies them before its fresh import).

2. **Invalid benchmark partition_id.** `_benchmark_units` built a partition_id with
   dots and a hyphen (`ES.2024-12.worker_benchmark`), which the data-foundation
   `_normalize_id` validator rejects, failing every benchmark unit. Fixed to a safe
   path token (`ES_2024_12_worker_benchmark`).

3. **Stale FLF-P05 request gate under parallelism.** The worker stage prepares every
   unit's duplicate-exposure request up front against the initial registry, but the
   single serial writer mutates the registry per unit, so a later unit's pre-computed
   request id no longer matched its spec (`checked FeatureRequest id must match
   FeatureSpec.feature_request_id` — only the first unit registered). Fixed by
   re-deriving the request gate against the LIVE registry at registration time and
   rebuilding the unit's plan with the fresh feature_set (the parallel path only;
   the serial executor is unchanged because it already registers each unit against
   the registry state it computed against). feature_version_id is content-addressed
   independent of registry state, so the worker's already-computed values register
   under the same identity and at the same Parquet output path.

**Completed benchmark result (real data, value-free summary committed):**
`{1,2,4,8}` workers all PASS — reference parity PASS, resolver-smoke PASS, and
byte-identical deterministic hashes across every worker count; effective workers
cap at the 3 runnable ES/NQ/RTY units, giving ~1.9x wall-clock vs single-process.
The fastest stable worker count is recorded in
`research/feature_compute_fast_path_v1/workers/worker_benchmark_summary.md`.

**Validation:** `tools/verify.py --smoke` PASS; canaries PASS; 150 FCFP+scaleout+
label unit tests PASS; `tests/no_lookahead/feature_label/test_synthetic_fail_closed.py`
12 PASS. No values/SQLite/heavy artifacts committed; benchmark roots and registry
backups stay local-only under `ALPHA_DATA_ROOT`.
