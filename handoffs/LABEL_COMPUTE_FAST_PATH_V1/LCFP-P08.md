# LCFP-P08 Handoff

Phase: `LCFP-P08` - Benchmark + Production Readiness Gate

Lane: `YELLOW`

This handoff does not mark the phase PASS. Ralph owns staging, validation
ledger updates, review routing, verdict parsing, PR, CI, merge gate, merge, and
done-check. Codex left changes unstaged and did not create review or verdict
artifacts.

## Status

- `code_status`: implemented.
- `benchmark_status`: `COMPLETE` from the bounded real-data benchmark payload.
- `registry_status`: main label registry was backed up before the benchmark;
  benchmark writes used isolated local scratch roots under `ALPHA_DATA_ROOT`.
- `artifact_status`: value-free committed summary/docs/handoff only; label
  values, Parquet payloads, local benchmark registries, and scratch outputs
  remain local-only under `ALPHA_DATA_ROOT`.

## Registry Backup

- Backup path:
  `/home/yuke_zhang/alpha_data/alpha_system/registry/labels.sqlite.bak_lcfp_20260610T183107Z`
- Backup command was executed before the benchmark entrypoint touched any label
  registry.

## Benchmark Run

Command:

```bash
ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m tools.label_compute_fast_path.benchmark_gate --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system --format json
```

Result:

- Exit code: `0`
- Payload status: `COMPLETE`
- Generated summary:
  `research/label_compute_fast_path_v1/benchmark/benchmark_summary.md`
- Local-only scratch root name:
  `lcfp_p08_benchmark_20260610T183231Z`
- Reference timing was bounded only; no full-window reference timing occurred.

## Slice Self-Validation

- Symbol/year: `ES` / `2024`
- Window: `2024-06-01T00:00:00+00:00` to
  `2024-07-01T00:00:00+00:00`
- OHLCV DatasetVersion: `dsv_databento_ohlcv_05404069799decb0`
- BBO DatasetVersion: `dsv_databento_bbo_f9e1d70a04d9dae4`
- OHLCV rows: `26304`
- BBO rows: `26304`
- Contract-roll events asserted: `1`
- Session/maintenance gaps asserted: `48`

## Per-Family Headline Results

| Family | Selected Engine | Requested Workers | Effective Workers | Best Speedup | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| `fixed_base` | `fast` | 8 | 6 | 1.03x | Fast compute narrowly beat the bounded reference rerun. |
| `fixed_extended` | `reference` | n/a | n/a | 0.55x | Reference remains faster; component timings are documented in the summary. |
| `close_out` | `reference` | n/a | n/a | 0.40x | Reference remains faster; component timings are documented in the summary. |
| `cost_adjusted` | `reference` | n/a | n/a | 0.72x | Reference remains faster; component timings are documented in the summary. |
| `path` | `fast` | 8 | 7 | 10.23x | Path family cleared the material-speedup gate. |

Aggregate selected worker policy:

- Status: `SELECTED`
- Requested workers: `8`
- Effective workers observed at selection: `8`
- Thread controls: `POLARS_MAX_THREADS=2`, `OMP_NUM_THREADS=2`,
  `RAYON_NUM_THREADS=2`, `NUMBA_NUM_THREADS=2`

## Parity And Resolver Outcomes

All worker cells completed parity and strict resolver smoke on the same bounded
slice.

| Family | Worker Counts | Resolver Smoke | Parity |
| --- | --- | --- | --- |
| `fixed_base` | 1 / 2 / 4 / 8 | `PASS 6/6` for each cell | `PASS` for each cell |
| `fixed_extended` | 1 / 2 / 4 / 8 | `PASS 3/3` for each cell | `PASS` for each cell |
| `close_out` | 1 / 2 / 4 / 8 | `PASS 2/2` for each cell | `PASS` for each cell |
| `cost_adjusted` | 1 / 2 / 4 / 8 | `PASS 18/18` for each cell | `PASS` for each cell |
| `path` | 1 / 2 / 4 / 8 | `PASS 28/28` for each cell | `PASS` for each cell |

Worker reductions recorded in the summary:

- `fixed_base` requested `8` reduced to `6` runnable units.
- `fixed_extended` requested `4` and `8` reduced to `3` runnable units.
- `close_out` requested `4` and `8` reduced to `2` runnable units.
- `path` requested `8` reduced to `7` runnable units.

## Validation

Requested validation:

- `git status --short`
  - Not run. The executor prompt explicitly forbids `git status`; Ralph owns
    git state inspection.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python tools/verify.py --smoke`
  - Passed, exit `0`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/ -q`
  - Passed: `58 passed in 2.69s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/feature_compute_fast_path/test_fixed_horizon_label_pack.py -q`
  - Passed: `4 passed in 1.71s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`
  - Passed: `12 passed in 0.17s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/test_fast_path_artifact_policy.py -q`
  - Passed: `2 passed in 0.22s`.
- `test -f research/label_compute_fast_path_v1/benchmark/benchmark_summary.md`
  - Passed.
- `git ls-files runs`
  - Passed: empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite'`
  - Passed: empty output.

Additional focused check:

- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/test_benchmark_gate.py -q`
  - Passed: `11 passed in 0.19s`.

## Files Changed For Ralph To Stage

Codex did not run `git status`, `git diff`, `git add`, `git commit`, or
`git push`. The list below is based on files intentionally edited or generated
by this executor turn:

- `README.md`
- `docs/label_compute_fast_path/README.md`
- `docs/label_compute_fast_path/OVERVIEW.md`
- `research/label_compute_fast_path_v1/README.md`
- `research/label_compute_fast_path_v1/benchmark/benchmark_summary.md`
- `tools/label_compute_fast_path/benchmark_gate.py`
- `tests/unit/label_compute_fast_path/test_benchmark_gate.py`
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P08.md`

Executor staging status: none staged by Codex.

## Boundary Notes

- No live trading, paper trading, broker operation, order routing, production
  deployment, external provider call, PR, merge, review call, `review.md`, or
  `verdict.json` was performed or created by Codex.
- No `runs/**` path was edited or staged by Codex. The run artifact directory
  named in the prompt was not present in this worktree.
- No reference-engine semantics, label identity, roll guard,
  maintenance-crossing behavior, `label_available_ts`, resolver exact-id
  semantics, or cost/accounting math was changed.
