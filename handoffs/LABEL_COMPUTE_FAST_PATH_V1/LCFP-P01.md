# LCFP-P01 Handoff - Label Engine Inventory + Baseline Benchmark

## Status

- code_status: reference benchmark harness added under
  `tools/label_compute_fast_path/`; no production label or registry code was
  modified.
- artifact_status: value-free inventory and bounded baseline benchmark summary
  written under `research/label_compute_fast_path_v1/`.

No review artifacts, verdict files, PR, merge, staging, or commit were created
by the executor.

## Changed Files

- `README.md`
- `docs/label_compute_fast_path/README.md`
- `docs/label_compute_fast_path/OVERVIEW.md`
- `research/label_compute_fast_path_v1/README.md`
- `research/label_compute_fast_path_v1/inventory/inventory.md`
- `research/label_compute_fast_path_v1/baseline/baseline_benchmark_summary.md`
- `tools/label_compute_fast_path/__init__.py`
- `tools/label_compute_fast_path/baseline_benchmark.py`
- `tests/unit/label_compute_fast_path/test_baseline_benchmark.py`
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P01.md`

## Inventory

`research/label_compute_fast_path_v1/inventory/inventory.md` covers:

- Reference dispatch in `src/alpha_system/labels/engine.py`.
- Fixed-horizon, extended-horizon, session-close, maintenance-flat, cost-adjusted,
  spread-adjusted, path, and event label families under
  `src/alpha_system/labels/families/**`.
- Per-family inputs, terminal semantics, quality or gap behavior, availability
  rules, overlap metadata, and per-row hot-loop locations.
- Existing `src/alpha_system/labels/fast/**` surface from FCFP-P10:
  `FastLabelMaterializer`, `FastLabelPack`,
  `build_fixed_horizon_label_pack`, and `LabelPanelFrameRequest`.
- The disclosed stale fast-label enum defect, including the stale
  `governance_gap_note` in `labels/fast/fixed_horizon.py`, recorded only as
  LCFP-P03 repair input.
- FUTSUB P16-P20 label config needs, including the paused P19 state from
  `handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_PAUSE_STATE.md`.
- `RollCrossPolicy`, `LabelAvailabilityPolicy`, `HorizonOverlapMetadata`,
  registry/store write and resolve schema, serial-write requirements, and the
  existing parity harness in
  `tests/unit/feature_compute_fast_path/parity_harness.py`.

The inventory is value-free: it includes paths, symbols, counts, and contract
descriptions only.

## Baseline Benchmark

Summary artifact:
`research/label_compute_fast_path_v1/baseline/baseline_benchmark_summary.md`.

Command used:

```bash
ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m tools.label_compute_fast_path.baseline_benchmark --format json
```

Timing mode: compute-only. The harness loads bounded canonical OHLCV/BBO inputs
read-only and calls the real reference family compute functions. It does not
call `materialize_labels`, instantiate `LabelRegistry`, write Parquet, write
SQLite, or create scratch outputs.

No production registry write occurred. The production label registry path under
`$ALPHA_DATA_ROOT` was not opened for write, and FUTSUB run state, label values,
registry rows, and worktrees were not touched.

Bounded slice:

- Symbol: `ES`
- Year: `2024`
- Window: `2024-06-01T00:00:00+00:00` through
  `2024-07-01T00:00:00+00:00`
- OHLCV dataset_version_id: `dsv_databento_ohlcv_05404069799decb0`
- BBO dataset_version_id: `dsv_databento_bbo_f9e1d70a04d9dae4`
- OHLCV rows loaded: `26,304`
- BBO rows loaded: `26,304`
- Roll events in slice: `1`
- Maintenance/session gap rows in slice: `48`

Measured reference baseline:

| Family bucket | Definitions | Rows processed | Elapsed seconds | Rows/sec | Extrapolation basis rows | Estimated seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fixed_base | 6 | 157,824 | 4.505292 | 35,030.81 | 79,200,000 | 2,260.87 |
| fixed_extended | 3 | 78,912 | 2.096966 | 37,631.52 | 39,600,000 | 1,052.31 |
| close_out | 2 | 52,608 | 1.517126 | 34,676.09 | 26,400,000 | 761.33 |
| cost_adjusted | 18 | 473,472 | 5.508200 | 85,957.67 | 237,600,000 | 2,764.15 |
| path | 28 | 736,512 | 66.302128 | 11,108.42 | 369,600,000 | 33,272.05 |

Full-window runtime rows are extrapolations only. The reference engine was not
timed on a full window.

## Validation

- `git status --short`: not run. The executor prompt explicitly prohibited
  `git status`; Ralph owns authoritative worktree/staging inspection.
- `python tools/verify.py --smoke`: passed.
- `test -f research/label_compute_fast_path_v1/inventory/inventory.md`:
  passed.
- `test -f research/label_compute_fast_path_v1/baseline/baseline_benchmark_summary.md`:
  passed.
- `git ls-files runs`: passed; returned empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite'`: passed; returned empty output.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/ -q`:
  passed, `2 passed in 0.11s`.

The run artifact directory named in the executor prompt was not present in this
worktree, and no `runs/**` files were created by this executor step.

## Reviewer And P02 Notes

- `labels/fast` currently covers only fixed-horizon pack construction and still
  has the disclosed stale-enum/coverage note; this phase inventoried it and did
  not repair it.
- Fixed-horizon reference code has direct roll and maintenance guard behavior.
  Cost-adjusted and path family code does not call `roll_guard.py` directly in
  the inspected implementation; P02 should make the shared guard contract
  explicit instead of assuming every family already shares one code path.
- Path labels carry same-bar ambiguity through `SameBarBarrierPolicy`; P02 and
  later parity work should treat this as a first-class parity dimension.
- `LabelAvailabilityPolicy` is derived from family, horizon, terminal mode,
  delay, and calendar version; later packs need exact `label_available_ts`
  parity, not value-only parity.
- Default `python` is sufficient for `tools/verify.py --smoke`. The benchmark
  used the existing research virtualenv because canonical data loading requires
  optional data dependencies.
