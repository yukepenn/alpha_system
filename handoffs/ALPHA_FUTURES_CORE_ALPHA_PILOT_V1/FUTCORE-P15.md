# FUTCORE-P15 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P15` - Minimal Missing FeatureRequest / LabelSpec Additions, If Needed  
Executor: Codex GPT-5.5  
Lane: Yellow  
Status: executor work complete; Ralph review, authoritative staging, commit, PR, CI, merge, and done-check remain pending

## Decision

Decision recorded: **Minimal additions**.

The P13 gap list was not empty, and P14 StudySpecs still carry `P15-G1` through
`P15-G5`. A strict no-op was therefore not available. The corrected P15 outcome
adds exactly one missing LabelSpec (`fwd_ret_15m`) and four FeatureRequest
records for the feature binding gaps. `fwd_ret_10m` and `fwd_ret_30m` are not
P15 additions because P13/P14 record them as locked P03/P13 LabelPack members
with valid `label_available_ts` metadata.

## Primitive Mapping

| P13 gap | Governed record | Governance id | Implementation outcome |
| --- | --- | --- | --- |
| `P15-G1` | `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json` | `lspec_8ea5c33463a47d467963d216` | `fwd_ret_15m` is supported in the fixed-horizon label family; tests cover exact terminal rows and `label_available_ts`. |
| `P15-G2` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g2_vwap_session.json` | `freq_c2a4bc747eb9a0602327de2d` | Existing OHLCV family code covers running VWAP, anchored VWAP, distance-to-VWAP, and opening-range context with current-row `available_ts`. |
| `P15-G3` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g3_cross_market_derived_state.json` | `freq_54d8ae828e0bf68c675734cb` | Existing cross-market family code covers residual, spread, divergence/agreement, and rotation-state primitives with as-of `available_ts` alignment. |
| `P15-G4` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g4_causal_ohlcv_derived.json` | `freq_65e52467c10ca7dbc01e39bb` | Existing OHLCV and structure families cover trendiness, ATR, prior-boundary, compression, sweep, and failed-breakout state with causal windows. |
| `P15-G5` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g5_bbo_top_book_confirmation.json` | `freq_9593f8957b283031a62447bf` | Existing BBO family code covers spread, spread ticks, spread zscore, top-book depth, wide/low-depth flags, missing-BBO flag, and bad-quote flag without quote filling. |

## Files Written, Updated, Or Removed

Codex staged no files. The user override explicitly forbade Codex from running
`git add`, `git commit`, `git push`, `git status`, or `git diff`.

Staged files by Codex:

- None.

Commit-eligible files for Ralph explicit staging:

- `research/futures_core_alpha_pilot_v1/feature_requests/DECISION.md`
- `research/futures_core_alpha_pilot_v1/feature_requests/p15_g2_vwap_session.json`
- `research/futures_core_alpha_pilot_v1/feature_requests/p15_g3_cross_market_derived_state.json`
- `research/futures_core_alpha_pilot_v1/feature_requests/p15_g4_causal_ohlcv_derived.json`
- `research/futures_core_alpha_pilot_v1/feature_requests/p15_g5_bbo_top_book_confirmation.json`
- `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json`
- `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_10m.json` (deleted; non-gap P15 artifact)
- `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_30m.json` (deleted; non-gap P15 artifact)
- `src/alpha_system/labels/families/fixed_horizon/family.py`
- `tests/unit/features/test_futcore_p15_primitive_requests.py`
- `tests/unit/labels/families/fixed_horizon/test_fixed_horizon_family.py`
- `docs/futures_core_alpha_pilot/PRIMITIVE_ADDITIONS.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P15.md`

No `runs/**` path should be staged.

## Validation Run By Codex

```bash
test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP
```

Result: exit code `0`; no active run-level STOP file was present.

```bash
test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P15/STOP
```

Result: exit code `0`; no active phase-level STOP file was present.

```bash
PYTHONPATH=src python - <<'PY'
... validate P15 FeatureRequest and LabelSpec JSON records ...
PY
```

Result: exit code `0`; output:

```text
feature_requests 4
label_specs ['fwd_ret_15m.json']
governance_validation ok
```

```bash
test -f research/futures_core_alpha_pilot_v1/feature_requests/DECISION.md
```

Result: exit code `0`.

```bash
test ! -e research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_10m.json
test ! -e research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_30m.json
```

Result: both commands exited `0`; the non-gap P15 label files are absent.

```bash
PYTHONPATH=src pytest tests/unit/features/test_futcore_p15_primitive_requests.py tests/unit/labels/families/fixed_horizon/test_fixed_horizon_family.py
```

Result: exit code `0`; `15 passed in 0.19s`.

Earlier targeted feature test run:

```bash
PYTHONPATH=src pytest tests/unit/features/test_futcore_p15_primitive_requests.py
```

First result: exit code `1`; two failures due to a deterministic ID mismatch in
`p15_g4_causal_ohlcv_derived.json` after the record content was corrected. The
record was repaired, and the rerun exited `0` with `5 passed in 0.11s`.

```bash
PYTHONPATH=src pytest tests/unit/labels/families/fixed_horizon/test_fixed_horizon_family.py
```

Result: exit code `0`; `10 passed in 0.22s`.

```bash
python tools/verify.py --smoke
```

Result: exit code `0`; no stdout.

```bash
python tools/verify.py --all
```

Result: exit code `1`; verifier ran compileall and pytest, with
`4 failed, 2840 passed in 46.50s`.

Failures observed:

- `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`
  - assertion expected a list, actual was a tuple containing the expected row.
- `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`
  - assertion expected a list, actual was a tuple containing the expected row.
- `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`
  - expected non-empty OHLCV JSONL rows, actual parsed rows were empty.
- `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`
  - expected `RUN_ARTIFACTS`, actual resolved storage kind was `ALPHA_DATA_ROOT`
    at `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/runtime/cache/derived_summaries`.

These failures are outside the P15 allowed edit surface. Codex did not edit
`src/alpha_system/data/**`, `src/alpha_system/runtime/**`, or the failing
integration fixtures.

```bash
python tools/hooks/canary_runner.py
```

Result: exit code `0`; all Frontier canaries passed.

```bash
git ls-files runs
```

Result: exit code `0`; empty output.

```bash
git ls-files '**/*.parquet' '**/*.sqlite'
```

Result: exit code `0`; empty output.

```bash
git ls-files '**/*.dbn' '**/*.zst' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.wal' '**/*.log'
```

Result: exit code `0`; empty output.

```bash
test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P15/review.md
test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P15/verdict.json
test ! -e reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P15
```

Result: all commands exited `0`; Codex created no review, verdict, or
commit-eligible review artifact.

Supplemental attempted listing:

```bash
find reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P15 -maxdepth 2 -type f -print
```

Result: exit code `1`; the directory does not exist. This is expected because
the user explicitly forbade reviewer execution and review artifact creation.

Validation intentionally not run by Codex:

- `git status --short`: not run because the user explicitly forbade
  `git status`.
- `git diff --cached --name-only`: not run because the user explicitly forbade
  `git diff`, and Codex staged nothing.
- Any `git add`, `git commit`, or `git push`: not run because the user
  explicitly forbade staging and committing.
- Fresh Yellow-lane Claude review: not run because the user explicitly forbade
  calling Claude or running reviewer.
- `review.md` and `verdict.json`: not created because the user explicitly
  forbade creating them. Ralph owns reviewer artifacts and verdict parsing.

## Artifact And Boundary Confirmation

- `git ls-files runs` returned empty.
- Tracked Parquet, SQLite, DBN, Zst, Arrow, Feather, DB, WAL, and log globs
  returned empty.
- No raw/canonical market data, provider responses, materialized feature values,
  materialized label values, heavy artifacts, local DB/registry files, logs,
  caches, secrets, or credentials were added.
- No live trading, paper trading, broker/order call, account operation,
  deployment, PR creation, merge, reviewer call, review artifact, or verdict
  action was performed.
- The work remains research-only and value-free. It makes no alpha,
  profitability, tradability, production, broker, paper/live, or
  capital-allocation claim.
