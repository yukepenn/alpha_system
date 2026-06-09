# FCFP-P13 Handoff - Benchmark Gate

## Outcome

Status: `BLOCKED_PARITY`

The bounded-real benchmark was wired to the real canonical loaders, real
reference runners, and real V1 fast-pack runners. The December 2024 ES/NQ/RTY
slice self-validation passed, but the benchmark failed closed during real-data
parity confirmation before speedup or full-window runtime estimates were
reported.

The commit-eligible value-free summary is:

```text
research/feature_compute_fast_path_v1/benchmark/benchmark_summary.md
```

No feature values, label values, market prices, Parquet, SQLite, or row-level
outputs were written to the repository.

## Benchmark Window

- `ALPHA_DATA_ROOT`: `/home/yuke_zhang/alpha_data/alpha_system`
- Window: `2024-12-01T00:00:00+00:00` to `2025-01-01T00:00:00+00:00`
- Symbols: `ES`, `NQ`, `RTY`
- Primary single-symbol packs: `ES`
- OHLCV DatasetVersion: `dsv_databento_ohlcv_05404069799decb0`
- Dense OHLCV DatasetVersion: `dsv_databento_ohlcv_dense_2024_v1`
- BBO DatasetVersion: `dsv_databento_bbo_f9e1d70a04d9dae4`
- Slice row count across loaded inputs: `168794`
- Configured quarterly roll events in window: `1`
- Raw contract/id transitions observed in canonical rows: `0`
- Session gaps observed: `1304`

Note: the canonical continuous front rows keep stable `contract_id` /
`instrument_id` identifiers, so roll self-validation records the configured
quarterly CME roll calendar event and separately reports raw transition count.

## Parity Result

Real-data parity failed before speedup reporting:

```text
bbo_tradability/bbo_tradability_spread_zscore
fver_dddade60a238bed22a27e0bb3738253a0f8f7c88ce3a6de9f0fb51cb20b56bfb
quality_flags differ
```

Value-free diagnostic aggregate:

- Records compared: `28727`
- Key differences: `0`
- Flag differences: `24192`
- Reference flags on differing rows: `primitive_gap`, `zero_variance`
- V1 flags on differing rows: none
- Null/non-null value differences: `24192`
- Non-null numeric value differences: `4521`

This is not a tolerance issue: the reference emits zero-variance primitive gaps
while V1 emits non-null values without the corresponding quality flags. Per the
spec, no speedup or full-window runtime estimate is reported until parity passes.

One numeric tolerance was added for `base_ohlcv_rolling_volatility` after a
bounded-slice diagnostic found only floating reduction noise:

- Records compared: `28727`
- Key differences: `0`
- Flag differences: `0`
- Max absolute difference: `5.708324438136181e-17`
- Max relative difference: `2.00675290128409e-12`

## Report Fields

Required benchmark report fields were not reported because parity did not pass:

- `elapsed`: not reported
- `rows_per_sec`: not reported
- `canonical_reads_per_symbol_year`: not reported
- `output_features_or_labels_per_read`: not reported
- `full_accepted_window_runtime_estimate`: not reported
- `speedup_vs_reference`: not reported

The summary records the bounded window, symbols, row count, roll/gap
self-validation, and the parity blocker.

## Commands Run

Pre-flight / targeted checks:

```bash
PYTHONPATH=src $HOME/.venvs/alpha_system_research/bin/python -m py_compile tools/feature_compute_fast_path/benchmark_gate.py
```

Outcome: passed.

```bash
PYTHONPATH=src $HOME/.venvs/alpha_system_research/bin/python -m pytest tests/unit/feature_compute_fast_path/test_benchmark_gate.py -q
```

Outcome: `6 passed in 0.17s`.

Registry backup:

```bash
ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system bash -lc 'TS=$(date -u +%Y%m%dT%H%M%SZ); cp "$ALPHA_DATA_ROOT/registry/features.sqlite" "$ALPHA_DATA_ROOT/registry/features.sqlite.bak_fcfp_$TS"; printf "%s\n" "$ALPHA_DATA_ROOT/registry/features.sqlite.bak_fcfp_$TS"'
```

Outcome: created local-only backup
`/home/yuke_zhang/alpha_data/alpha_system/registry/features.sqlite.bak_fcfp_20260609T012717Z`.

Benchmark:

```bash
ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system PYTHONPATH=src $HOME/.venvs/alpha_system_research/bin/python tools/feature_compute_fast_path/benchmark_gate.py
```

Outcome: the command was rerun during bounded repair. Earlier attempts exposed
benchmark wiring issues in real Polars frame construction (`infer_schema_length`
for label/feature frames and `quality_flags` list typing), which were fixed in
the harness. A later attempt exposed the documented
`base_ohlcv_rolling_volatility` floating reduction tolerance described above.
The final run was nonzero by design after real-data parity failed on
`bbo_tradability_spread_zscore` quality flags. The command wrote
`research/feature_compute_fast_path_v1/benchmark/benchmark_summary.md` with
status `BLOCKED_PARITY` before re-raising the parity error.

Required validation:

```bash
git status --short
```

Outcome: not run. The executor prompt explicitly forbade all `git status`
commands. This is not an environment failure.

```bash
PATH="$HOME/.venvs/alpha_system_research/bin:$PATH" PYTHONPATH=src python tools/verify.py --smoke
```

Outcome: passed.

```bash
test -f research/feature_compute_fast_path_v1/benchmark/benchmark_summary.md
```

Outcome: passed.

```bash
git ls-files runs
```

Outcome: passed, empty output.

```bash
git ls-files '**/*.parquet' '**/*.sqlite'
```

Outcome: passed, empty output.

Supporting validation:

```bash
PATH="$HOME/.venvs/alpha_system_research/bin:$PATH" PYTHONPATH=src python -m pytest tests/unit/feature_compute_fast_path/ -q
```

Outcome: `33 passed in 2.24s`.

```bash
PATH="$HOME/.venvs/alpha_system_research/bin:$PATH" PYTHONPATH=src python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q
```

Outcome: `12 passed in 0.16s`.

```bash
PATH="$HOME/.venvs/alpha_system_research/bin:$PATH" PYTHONPATH=src python tools/hooks/canary_runner.py
```

Outcome: all Frontier canaries passed.

## Staging

The executor did not run `git add`, `git commit`, `git push`, `git status`, or
`git diff`. No files were staged by the executor.

Suggested explicit stage list for Ralph, subject to Ralph artifact audit:

```text
README.md
docs/feature_compute_fast_path/BENCHMARK_GATE.md
docs/feature_compute_fast_path/README.md
handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P13.md
research/feature_compute_fast_path_v1/benchmark/benchmark_summary.md
tests/unit/feature_compute_fast_path/test_benchmark_gate.py
tools/feature_compute_fast_path/__init__.py
tools/feature_compute_fast_path/benchmark_gate.py
```

No `runs/**` path should be staged. No review, verdict, PR, merge, or PASS
artifact was created by the executor.

## Next Step

Repair the governed V1 BBO spread z-score parity issue before rerunning P13.
The benchmark gate should remain blocked until the real bounded slice passes
value, availability, quality flag, and version identity parity.
