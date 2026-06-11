# RLPC-P03 Handoff

Campaign: `REFERENCE_LABEL_PARALLEL_COMPUTE_V1`  
Phase: `RLPC-P03` - Bounded Real Benchmark + Release Gate (workers 1/2/4/8)  
Lane: YELLOW

## Summary

Built `tools/reference_label_parallel_compute/benchmark_reference_parallel.py`,
a bounded real benchmark harness for the reference-label unit-parallel path. The
harness calls the real `alpha_system.features.scaleout.driver.run_scaleout`
entrypoint with `engine="reference"` and workers 1/2/4/8. It does not replace
or mock label compute. It wraps the existing driver compute/register functions
only to measure elapsed component timings, then calls the originals.

The harness enforces an isolated benchmark namespace, rejects production
registry/value roots, selects a self-validating real `cost_adjusted` slice,
requires persisted accepted DatasetVersion locks, reads canonical inputs only,
and writes benchmark values/registries/checkpoints only under the local-only
benchmark namespace.

The measured release decision is `NOT_RELEASED`: requested workers=8 reached
2.14x versus workers=1 on the same 9-unit grid, below the 3.0x release gate.
The diagnosis is serial registration ceiling: workers=8 spent 90.097791 s in
serial parent registration out of 247.888112 s total.

## Slice Definition

- Config: `configs/labels/scaleout/cost_adjusted.json`
- Family: `cost_adjusted`
- Symbols: `ES`
- Years: `2024`
- Horizons: `1m, 3m, 5m, 10m, 15m, 30m, 60m, 120m, 240m`
- Label ids: `cost_adjusted_fwd_ret, spread_adjusted_fwd_ret`
- Runnable units: `9`
- Unit ids: `mbu_241290fd96424d08c7ee773b, mbu_4f8f521212eedfd0804d73a5, mbu_69c6ee8585dd5dc0476f779d, mbu_b70c477529b368187ee4a57d, mbu_ecb023cde3ef706eab250e67, mbu_fd84ba6176164534fa2e14a5, mbu_ab9e7f433e7ce9f42ea7e5e0, mbu_683bf98b5b2027c72bbd8540, mbu_bb2fb852c02a243ad3773d4d`
- OHLCV DatasetVersion: `dsv_databento_ohlcv_05404069799decb0`
- BBO DatasetVersion: `dsv_databento_bbo_f9e1d70a04d9dae4`
- Canonical OHLCV rows inspected for self-validation: `346858`
- Analytic CME roll events in selected year: `4`
- Roll event dates: `2024-03-07, 2024-06-13, 2024-09-12, 2024-12-12`
- Session/maintenance gaps observed from canonical timestamps: `471`
- Max timestamp gap minutes: `4381`
- Raw contract/id transitions observed in canonical rows: `0`
- Initial ES/2024 slice widened: `false`

Roll self-validation uses the configured analytic CME equity-index quarterly
roll calendar because the canonical front-continuous rows keep stable
`contract_id` / `instrument_id` identifiers. Session/maintenance gaps are
measured directly from canonical OHLCV timestamp deltas.

## Benchmark Invocation

Command run:

```bash
ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system \
POLARS_MAX_THREADS=2 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 NUMEXPR_MAX_THREADS=2 \
PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python \
  -m tools.reference_label_parallel_compute.benchmark_reference_parallel \
  --workers 1 2 4 8
```

Output:

```text
wrote research/reference_label_parallel_compute_v1/benchmark/benchmark_summary.md
Release decision: NOT_RELEASED
```

Namespace pattern: `$ALPHA_DATA_ROOT/rlpc_p03_benchmark_<UTCSTAMP>/workers_N`.
Actual local-only namespace name: `rlpc_p03_benchmark_20260611T032628Z`. The
handoff and committed summary do not include label values, canonical rows,
SQLite content, Parquet payloads, or provider responses.

## Results

| Requested | Effective | Driver Plan Threads/Worker | Elapsed (s) | Units/s | Speedup vs 1 | Worker Compute (s) | Serial Registration (s) | Overhead (s) | Peak RSS MiB | Registry Delta | Completed | Label Versions | Rows | Determinism |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | 16 | 530.998623 | 0.0169 | 1.00 | 526.587762 | 3.515340 | 0.895521 | 3496.10 | 18 | 9 | 18 | 6243444 | PASS |
| 2 | 2 | 8 | 389.293969 | 0.0231 | 1.36 | 303.147023 | 86.077229 | 0.069717 | 3682.13 | 18 | 9 | 18 | 6243444 | PASS |
| 4 | 4 | 4 | 289.894526 | 0.0310 | 1.83 | 203.654499 | 86.172520 | 0.067508 | 3690.77 | 18 | 9 | 18 | 6243444 | PASS |
| 8 | 8 | 2 | 247.888112 | 0.0363 | 2.14 | 157.706309 | 90.097791 | 0.084013 | 3690.77 | 18 | 9 | 18 | 6243444 | PASS |

Determinism spot-check versus workers=1 passed for every swept cell:
order-normalized completed record sets, `label_version_id`s, content hashes, and
row counts all matched.

Production label registry write confirmation: production row delta was `0`.
Each benchmark cell used its own isolated benchmark `labels.sqlite` and ended
with 18 benchmark registry rows.

## Files For Ralph To Stage

The executor staged no files and ran no staging commands. Ralph should stage
only these commit-eligible paths:

- `tools/reference_label_parallel_compute/__init__.py`
- `tools/reference_label_parallel_compute/benchmark_reference_parallel.py`
- `tests/unit/reference_label_parallel_compute/test_benchmark_reference_parallel.py`
- `research/reference_label_parallel_compute_v1/benchmark/benchmark_summary.md`
- `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/RLPC-P03.md`
- `README.md`

Do not stage `__pycache__/`, `.pytest_cache/`, anything under `$ALPHA_DATA_ROOT`,
or anything under `runs/`.

## Validation Results

- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/reference_label_parallel_compute -q` - PASS: `19 passed, 1 skipped in 6.24s`. The skip is the pre-existing optional RLPC-P02 real-slice spot-check.
- `test -f research/reference_label_parquet 2>/dev/null; test -f research/reference_label_parallel_compute_v1/benchmark/benchmark_summary.md` - PASS, exit code 0.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python tools/verify.py --smoke` - PASS, exit code 0 with no output.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python tools/hooks/canary_runner.py` - PASS: all Frontier canaries passed.
- `git ls-files runs` - PASS, output empty.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m tools.reference_label_parallel_compute.benchmark_reference_parallel --help` - PASS; documented flags are `--workers`, `--out`, `--alpha-data-root`, `--dataset-registry`, `--canonical-root`, `--benchmark-namespace`, and `--config`.

Additional artifact checks:

- `find research/reference_label_parallel_compute_v1/benchmark -type f \( -name '*.parquet' -o -name '*.sqlite' -o -name '*.db' -o -name '*.arrow' -o -name '*.feather' -o -name '*.log' \) -print` - PASS, output empty.
- `find tools/reference_label_parallel_compute tests/unit/reference_label_parallel_compute research/reference_label_parallel_compute_v1/benchmark -type f \( -name '*.sqlite' -o -name '*.db' -o -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' -o -name '*.log' -o -name '*.dbn' -o -name '*.zst' \) -print` - PASS, output empty.

Not run:

- `git status --short` - NOT RUN because the executor prompt explicitly forbids
  `git status`.
- `git diff`, `git add`, `git commit`, `git push` - NOT RUN by executor.
- Claude review, reviewer, `review.md`, `verdict.json`, PR creation, merge, and
  PASS marking - NOT RUN by executor; Ralph owns these stages.

## Scope / Artifact Notes

No forbidden source paths were edited:

- `src/alpha_system/labels/engine.py`
- `src/alpha_system/labels/families/**`
- `src/alpha_system/labels/roll_guard.py`
- `src/alpha_system/labels/version.py`
- `src/alpha_system/features/scaleout/driver.py`
- `src/alpha_system/cli/scaleout.py`

No paused FUTSUB run directory, worktree, checkpoint, registry row, or value path
was touched. Benchmark values, manifests, and benchmark-scoped registries remain
local-only under `$ALPHA_DATA_ROOT/rlpc_p03_benchmark_20260611T032628Z/**`.

No live trading, paper trading, broker operations, order routing, production
deployment, destructive cleanup, PR creation, merge, or external provider call
was performed.
