# FCFP-P10 Handoff

Summary: Implemented the V1 `fixed_horizon` label pack under
`src/alpha_system/labels/fast/`, added full governed-label synthetic parity and
registration coverage, wrote the value-free parity report, updated docs /
README, and left all changes unstaged for Ralph.

## Files For Ralph To Stage

Codex did not run `git add`, `git commit`, `git push`, `git status`, or
`git diff` because the executor prompt explicitly prohibited those actions.
Ralph should stage only these commit-eligible paths:

- `src/alpha_system/labels/fast/__init__.py`
- `src/alpha_system/labels/fast/fixed_horizon.py`
- `src/alpha_system/labels/fast/materializer.py`
- `tests/unit/feature_compute_fast_path/parity_harness.py`
- `tests/unit/feature_compute_fast_path/test_fixed_horizon_label_pack.py`
- `tests/fixtures/feature_compute_fast_path/README.md`
- `tests/fixtures/feature_compute_fast_path/fixed_horizon_label.py`
- `research/feature_compute_fast_path_v1/label_packs/fixed_horizon_parity.md`
- `docs/feature_compute_fast_path/README.md`
- `README.md`
- `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P10.md`

No `runs/**` path, review artifact, verdict artifact, value artifact, SQLite
file, Parquet file, or heavy artifact is included in this list.

## Scope Completed

- Added `FastLabelMaterializer`, `FastLabelPack`, and
  `FastLabelDeclaration` under `src/alpha_system/labels/fast/`.
- Added the governed `fixed_horizon` label pack for exactly the current
  `FixedHorizonLabelName` set:
  `fwd_ret_{1,3,5,10,15,30}m` and
  `mid_fwd_ret_{1,3,5,10,30}m`.
- Built one shared OHLCV+BBO Polars price panel with `price_basis`, row-level
  trade/BBO guard columns, and cached symbol-year loading through the sanctioned
  canonical OHLCV/BBO readers.
- Computed all governed horizons from that shared prepared panel, excluding
  trailing rows without an exact terminal event exactly as the reference does.
- Preserved `label_available_ts = max(terminal.available_ts,
  LabelSpec.availability_time)` and exact quality-flag behavior.
- Recorded value-free N_eff and horizon-overlap metadata per label.
- Materialized test outputs through `LabelMaterializationPlan` /
  `LabelMaterializationResult` and registered each label with
  `LabelRegistry.register_materialized_label` under the serial registry lock.
- Recorded `producer_engine_id =
  alpha_system.labels.fast.pack_materializer.v1` and `value_schema_version =
  alpha_system.labels.fast.values.v1` in the value-store wrapper and label
  lineage.
- Added the tiny synthetic fixture and parity/materialization/cache tests.
- Added a value-free fixed-horizon parity report and updated durable docs /
  README snapshot.

## Parity Results

Fixture: `tests/fixtures/feature_compute_fast_path/fixed_horizon_label.py`  
Shared panel: 36 synthetic OHLCV rows and 36 synthetic BBO rows.  
Tolerance: exact for all labels; no floating-point tolerance was needed.

| Label | Basis | Horizon | N_eff | Null / gap rows | Value | `label_available_ts` | Flags / guards | `label_version_id` |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |
| `fwd_ret_1m` | close | 1m | 35 | 4 | exact | exact | exact | exact |
| `fwd_ret_3m` | close | 3m | 33 | 4 | exact | exact | exact | exact |
| `fwd_ret_5m` | close | 5m | 31 | 3 | exact | exact | exact | exact |
| `fwd_ret_10m` | close | 10m | 26 | 2 | exact | exact | exact | exact |
| `fwd_ret_15m` | close | 15m | 21 | 2 | exact | exact | exact | exact |
| `fwd_ret_30m` | close | 30m | 6 | 2 | exact | exact | exact | exact |
| `mid_fwd_ret_1m` | mid | 1m | 35 | 4 | exact | exact | exact | exact |
| `mid_fwd_ret_3m` | mid | 3m | 33 | 4 | exact | exact | exact | exact |
| `mid_fwd_ret_5m` | mid | 5m | 31 | 3 | exact | exact | exact | exact |
| `mid_fwd_ret_10m` | mid | 10m | 26 | 2 | exact | exact | exact | exact |
| `mid_fwd_ret_30m` | mid | 30m | 6 | 2 | exact | exact | exact | exact |

Additional parity confirmations:

- Trade guards matched the reference for `source_not_trade`,
  `horizon_not_trade`, `no_trade`, `roll_splice_boundary`, and
  `maintenance_crossing` quality flags.
- Midprice guards matched the reference for `bbo_gap`, `source_bbo_gap`,
  `horizon_bbo_gap`, `missing_bbo`, and `bbo_quarantined`.
- Horizon terminal exclusion matched the reference: `N_eff = 36 -
  horizon_minutes` for every governed label.
- Horizon-overlap metadata was present and positive for every same-basis label.
- Fast declarations reused `LabelVersion.derive(LabelContractSpec)` identities;
  no V1-specific `label_version_id` was minted.

## Governance Gap

The reference-governed fixed-horizon set currently stops at 30m. FUTSUB
narrative horizons beyond the current enum, including 60m/120m/240m, remain a
governance gap. This phase did not create new `LabelSpec`s, horizons, labels, or
label identities.

## Validation Results

- STOP check:
  `test ! -f runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/STOP && printf 'NO_STOP\n' || { printf 'STOP_PRESENT\n'; sed -n '1,120p' runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/STOP; }`
  produced:
  ```text
  NO_STOP
  ```
- Run phase directory probe:
  `find runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/phases/FCFP-P10 -maxdepth 2 -type f -print | sort`
  exited 1 because the phase directory was absent:
  ```text
  find: 'runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/phases/FCFP-P10': No such file or directory
  ```
- `git status --short`: skipped. The executor prompt forbids `git status`.
- `python tools/verify.py --smoke`: completed with exit code 0 and no output.
- `python -m pytest tests/unit/feature_compute_fast_path/ -q`:
  ```text
  ....................                                                     [100%]
  20 passed in 1.46s
  ```
- `python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`:
  ```text
  ............                                                             [100%]
  12 passed in 0.16s
  ```
- `python tools/hooks/canary_runner.py`:
  ```text
  PASS forbidden_git_add_dot
  PASS policy_doc_mentions_forbidden_command
  PASS forbidden_test_tamper
  PASS forbidden_secret
  PASS forbidden_large_binary
  PASS forbidden_destructive_op
  PASS forbidden_boundary_import
  PASS forbidden_raw_data_commit
  PASS forbidden_stray_raw_suffix
  PASS forbidden_stray_dbn_suffix
  PASS forbidden_cache_data_commit
  PASS forbidden_local_artifacts
  PASS forbidden_scope_drift
  PASS generated_scaffold_allowed
  PASS governance_future_shift
  PASS governance_permuted_labels
  PASS governance_optimistic_fill
  All Frontier canaries passed.
  ```
- `test -f research/feature_compute_fast_path_v1/label_packs/fixed_horizon_parity.md`:
  completed with exit code 0 and no output.
- `git ls-files runs`: completed with exit code 0 and no output.
- `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'`:
  completed with exit code 0 and no output.
- Extra compile check:
  `python -m compileall -q src/alpha_system/labels/fast tests/unit/feature_compute_fast_path tests/fixtures/feature_compute_fast_path/fixed_horizon_label.py`
  completed with exit code 0 and no output.
- Extra targeted label-fast boundary scan:
  `rg -n "\.parquet|read_parquet|pyarrow|databento|ib_insync" src/alpha_system/labels/fast | cat`
  completed with exit code 0 and no output.
- Extra ruff checks were attempted but ruff is not installed in this
  environment:
  ```text
  /home/yuke_zhang/.venvs/alpha_system_research/bin/python: No module named ruff
  ```

Polars was available in this environment; no Polars-absent skip occurred for the
P10 parity tests.

## Artifact And Boundary Confirmation

- Codex left all changes unstaged for Ralph.
- Codex did not write a run-local handoff under `runs/**`.
- Codex did not create `review.md`, `verdict.json`, review artifacts, a PR, or a
  merge.
- No Parquet, SQLite, DB, Arrow, Feather, DBN, Zstd, raw/canonical data,
  provider response, feature value, label value, log, cache, or model artifact
  is listed for staging.
- Reference engine files were consumed read-only:
  `src/alpha_system/labels/families/fixed_horizon/family.py`,
  `src/alpha_system/labels/version.py`, `src/alpha_system/labels/engine.py`,
  and `src/alpha_system/labels/registry.py` were not edited.
- Resolver exact-id semantics, the existing label materialization plan contract,
  and `LabelRegistry` registration checks were not weakened or bypassed.
- No live trading, paper trading, broker operation, order routing, external
  provider call, production deployment, destructive cleanup, profitability
  claim, or tradability claim was made.

Ralph owns staging, cached-diff audit, commit, review routing, verdict parsing,
PR, CI, merge gate, merge, and phase done-check.
