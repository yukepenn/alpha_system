> **COORDINATOR AUTHORIZATION (2026-06-11T11:10Z)** — per review F1/F2:
> the locked-test update to guarded semantics in
> tests/unit/label_compute_fast_path/test_path_label_pack.py is AUTHORIZED
> (preserve parity assertions + drop-mechanism proof; no assertion deleted or
> weakened), and the labels/fast/path.py parity edit is AUTHORIZED (fast must
> match newly-guarded reference exactly). Basis: R-036/R-037 + campaign P20
> scope ("reuse the shared roll/maintenance guard wiring"). Full text in the
> run-local spec.md Coordinator Authorization section.

# FUTSUB-P20 Executor Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P20`  
Family: `path`  
Executor: Codex  
Date: `2026-06-11`

## Ralph Staging List

Executor left all changes unstaged. If Ralph stages this phase, stage only these
commit-eligible paths:

- `README.md`
- `configs/labels/scaleout/path.json`
- `research/futures_substrate_scaleout_v1/label_packs/path/coverage_summary.md`
- `research/futures_substrate_scaleout_v1/label_packs/path/coverage_matrix.json`
- `src/alpha_system/features/scaleout/driver.py`
- `src/alpha_system/labels/families/path/family.py`
- `src/alpha_system/labels/fast/path.py`
- `tests/unit/label_compute_fast_path/test_path_label_pack.py`
- `tests/unit/futures_substrate_scaleout/labels/test_path_scaleout.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P20.md`

`src/alpha_system/labels/fast/path.py` is included because P20 is mandated to
use the V1 fast path, and that file is the in-scope V1 path kernel where the
full-window roll/maintenance guard repair was required. Without that repair the
official P20 engine path would keep measuring path windows across guarded
boundaries. Repair attempt 1 explicitly routed review findings F1/F2 for this
bounded phase, authorizing the already-reviewed `src/alpha_system/labels/fast/path.py`
edit and the narrow LCFP regression update in
`tests/unit/label_compute_fast_path/test_path_label_pack.py`; no campaign policy
file was changed by the executor.

No `runs/**`, Parquet, SQLite, DB, Arrow, Feather, DBN, ZST, log, cache, or
provider payload was staged or committed by the executor.

## Scope Completed

- Reused the official scaleout label-mode dispatch with `--engine v1`.
- Reused the existing governed path family definitions: `mfe`, `mae`,
  `target_before_stop`, and `triple_barrier`; no new variants, parameter
  sweeps, or tuning were added.
- Wired path materialization scope (`symbol`, `partition_id`,
  `dataset_version_id`, window, and horizon) into path label identity so
  dry-run preview, execution, registry records, and resolver locks use the same
  partition-scoped label-version ids.
- Applied the shared FUTSUB-P16 roll-splice and maintenance-crossing terminal
  guard to the full path window before MFE/MAE excursion or barrier-touch
  measurement in both the reference path family and the V1 fast path.
- Materialized and registered the accepted path grid: `168` units,
  `672` label versions, ES/NQ/RTY, years 2019-2026, horizons
  `5m/10m/15m/30m/60m/120m/240m`.
- Preserved checkpoint/restart discipline. The full-grid run skipped the seven
  bounded real `ES`/`2024` units from checkpoint + registry truth and completed
  the remaining `161` units.

## Materialization Commands

Dry-run identity preview:

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system ALPHA_LABEL_CPU_WORKERS=8 POLARS_MAX_THREADS=2 OMP_NUM_THREADS=2 RAYON_NUM_THREADS=2 NUMBA_NUM_THREADS=2 /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/path.json --dry-run --rollout full-window --engine v1 --workers 8 --dataset-registry /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite --summary-out /tmp/futsub_p20_path_dry_run_summary.md
```

Outcome: exit `0`; accepted `168`, bounded `21`, planned `168`, failed `0`;
requested workers `8`; dry-run effective workers `1`; estimate
`92,400,000` rows / `924.0` seconds. A follow-up identity preview confirmed
distinct per-symbol path label-version ids for representative `5m`, `30m`, and
`240m` horizons across ES/NQ/RTY.

Bounded real validation:

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system ALPHA_LABEL_CPU_WORKERS=8 POLARS_MAX_THREADS=2 OMP_NUM_THREADS=2 RAYON_NUM_THREADS=2 NUMBA_NUM_THREADS=2 /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/path.json --execute --rollout full-window --symbols ES --years 2024 --engine v1 --workers 8 --dataset-registry /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite --summary-out /tmp/futsub_p20_path_es2024_bounded_summary.md --json
```

Outcome: exit `0`; accepted `7`, completed `7`, skipped `0`, failed `0`;
requested workers `8`; effective workers reduced to `7` runnable units;
threads per worker `2`. Registry messages confirmed worker compute was
registered by the serial writer.

Full accepted-window execution:

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system ALPHA_LABEL_CPU_WORKERS=8 POLARS_MAX_THREADS=2 OMP_NUM_THREADS=2 RAYON_NUM_THREADS=2 NUMBA_NUM_THREADS=2 /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/path.json --execute --rollout full-window --engine v1 --workers 8 --dataset-registry /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite --summary-out /tmp/futsub_p20_path_full_scaleout_summary.md
```

Outcome: exit `0`; accepted `168`, bounded `21`, planned `0`, completed `161`,
skipped `7`, failed `0`; requested workers `8`; effective workers `8`; threads
per worker `2`. The `planned=0` value reflects checkpoint + registry truth at
the final reporting point, not missing scope. The only stderr seen during
worker startup was repeated Python `runpy` warnings from child interpreters.

Registration stayed parent-only serial. Worker-computed units were registered
with messages of the form `worker compute registered by serial writer`.

## Path Variant Definitions

Definitions come from the existing governed path family and the FUTSUB-P05
horizon plan:

- `mfe`: maximum favorable excursion over the guarded forward real-trade-bar
  window; `label_available_ts` is the guarded window end.
- `mae`: maximum adverse excursion over the guarded forward real-trade-bar
  window; `label_available_ts` is the guarded window end.
- `target_before_stop`: governed `target_return=0.02`,
  `stop_return=-0.02`, `direction=long`, `price_field=close`,
  `same_bar_policy=ambiguous`; `label_available_ts` is first barrier touch or,
  if no barrier is touched, the guarded window end.
- `triple_barrier`: upper/lower/time barrier outcome using the same governed
  target/stop/direction/price/same-bar settings; `label_available_ts` is first
  barrier touch or, if no barrier is touched, the guarded window end.

Horizons: `5m`, `10m`, `15m`, `30m`, `60m`, `120m`, `240m`.

## Feasibility / Coverage Accounting

Current registry + checkpoint truth:

- Current completed units: `168`.
- Current label versions: `672`.
- Remaining units: `0`.
- Failed units: `0`.
- Flagged infeasible units: `0`.
- Unique local Parquet value files: `168` under `ALPHA_DATA_ROOT`.
- Accepted-state units: `ACCEPTED=126`, `ACCEPTED_WITH_WARNINGS=42`.
- `2018` excluded as `BLOCKED`; reference:
  `research/futures_substrate_scaleout_v1/dataset_acceptance/2018_BLOCKED_DIAGNOSIS.md`.

Value-free aggregate scan of current outputs:

- Metadata-column rows scanned across all four variants: `200,973,356`.
- Rows by variant: `mfe=50,243,339`, `mae=50,243,339`,
  `target_before_stop=50,243,339`, `triple_barrier=50,243,339`.
- `label_available_ts` null rows: `0`.
- Guard-flagged emitted rows: `0`.
- Max rows in one label version: `347,309`, below the configured per-label row
  budget `550,000`.
- All-variant metadata row count remained below the configured aggregate path
  evaluation budget `415,800,000`.

No R-021 infeasible units were required. Machine-reviewable per
symbol-year-variant-horizon rows, N_eff / overlap metadata, and per-unit guard
counts are in
`research/futures_substrate_scaleout_v1/label_packs/path/coverage_matrix.json`.
The compact human summary is in
`research/futures_substrate_scaleout_v1/label_packs/path/coverage_summary.md`.

N_eff is conservatively reported as `floor(row_count / horizon_steps)` at
one-minute sampling; rows are not claimed independent.

## Guard / Identity / Registry Evidence

- Shared FUTSUB-P16 roll-splice and maintenance-crossing guard wiring is reused
  through `_guarded_forward_terminal`; no forked guard policy was introduced.
- Full path windows are contract-scoped on `series_id+contract_id+event_ts`;
  a path scan is dropped if the guarded terminal crosses a contract segment,
  roll-splice guard, or maintenance break.
- Guard policy is `drop`. Dropped guard windows are not emitted as label rows.
  The materialized outputs have zero emitted roll/maintenance guard-flag rows.
- Value-free dropped-window counts are recorded by symbol/year/horizon in
  `coverage_matrix.json` and summarized by symbol-year in
  `coverage_summary.md`.
- Required registry fields were present for every current label version:
  `value_store_format`, `parquet_path`, `value_content_hash`,
  `value_schema_version`, `dataset_version_id`, `label_version_id`.
- `value_store_format=parquet` for all `672` current label versions.
- `producer_engine_id=alpha_system.labels.fast.pack_materializer.v1` for all
  current label versions.
- `value_schema_version=alpha_system.labels.fast.values.v1` for all current
  label versions.
- `label_version_id` does not encode `producer_engine_id`.

## Validation

Run:

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python tools/verify.py --smoke
```

Outcome: exit `0`.

Run:

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout/labels/test_path_scaleout.py -q
```

Outcome: exit `0`; `3 passed in 0.20s`.

Run:

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python tools/hooks/canary_runner.py
```

Outcome: exit `0`; all Frontier canaries passed.

Run:

```bash
test -f configs/labels/scaleout/path.json && test -d research/futures_substrate_scaleout_v1/label_packs/path
```

Outcome: exit `0`.

Run:

```bash
PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m json.tool configs/labels/scaleout/path.json >/tmp/futsub_p20_path_config_json.out
PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m json.tool research/futures_substrate_scaleout_v1/label_packs/path/coverage_matrix.json >/tmp/futsub_p20_path_coverage_json.out
```

Outcome: both commands exited `0`.

Run:

```bash
PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m compileall -q src/alpha_system/labels/families/path/family.py src/alpha_system/labels/fast/path.py src/alpha_system/features/scaleout/driver.py tests/unit/futures_substrate_scaleout/labels/test_path_scaleout.py
```

Outcome: exit `0`.

Run:

```bash
grep -n "importorskip" tests/unit/futures_substrate_scaleout/labels/test_path_scaleout.py
grep -rn "polars\|value_store\|seed_pack\|data.storage" tests/unit/futures_substrate_scaleout/labels/test_path_scaleout.py
```

Outcome: exit `0`; both greps matched line `7`:
`pytest.importorskip("polars")`.

Run:

```bash
git ls-files runs
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'
```

Outcome: both commands returned empty output.

Repair attempt 1 reran the review-requested path surfaces after updating the
stale LCFP regression expectation:

```bash
PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/test_path_label_pack.py::test_mfe_record_set_matches_guarded_reference_across_gaps_and_roll_windows -q
```

Outcome: exit `0`; `2 passed in 0.25s`.

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/test_path_label_pack.py -q
```

Outcome: exit `0`; `9 passed in 0.42s`.

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/labels/families/path/ -q
```

Outcome: exit `0`; `6 passed in 0.13s`.

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/no_lookahead/label_fast_path/ -q
```

Outcome: exit `0`; `2 passed in 0.84s`.

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout/labels/test_path_scaleout.py -q
```

Outcome: exit `0`; `3 passed in 0.21s`.

```bash
PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/ tests/unit/labels/families/path/ tests/no_lookahead/label_fast_path/ tests/unit/futures_substrate_scaleout/labels/test_path_scaleout.py -q
```

Outcome: exit `1`; `5 failed, 64 passed in 3.57s`. The P20 path scopes passed.
The remaining failures are five fast-label residuals: two campaign-level
parity-matrix tests fail while enumerating `_cost_adjusted_cases()`, and three
are cost-adjusted pack tests. They are not path-family test failures:

- `tests/unit/label_compute_fast_path/test_parity_matrix_suite.py::test_campaign_level_parity_matrix_covers_every_fast_label_family_and_dimension`
- `tests/unit/label_compute_fast_path/test_parity_matrix_suite.py::test_required_guard_and_missingness_cases_are_exercised_by_the_matrix`
- `tests/unit/label_compute_fast_path/test_session_maintenance_cost_pack.py::test_cost_adjusted_pack_matches_reference_and_preserves_bbo_gap_flags`
- `tests/unit/label_compute_fast_path/test_session_maintenance_cost_pack.py::test_cost_adjusted_maintenance_crossing_window_matches_reference_behavior`
- `tests/unit/label_compute_fast_path/test_session_maintenance_cost_pack.py::test_cost_adjusted_matches_reference_on_misaligned_bbo_timestamps`

```bash
env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python tools/verify.py --all
```

Outcome: exit `1`; `9 failed, 3125 passed, 1 skipped in 57.49s`. P20 path tests
passed inside the run. Failures were the same five fast-label residuals listed
above plus:

- `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`
- `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`
- `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`
- `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only` (`ALPHA_DATA_ROOT` resolved the cache root to `alpha_data_root`)

`verify.py --all` also ran status doctor, which warned that no live run dir was
present and local hooks were not armed (`core.hooksPath` was the shared root
hooks path rather than `.githooks`), then ran canaries successfully.

Repair attempt 2, done-check baseline triage:

```bash
mktemp -d /tmp/futsub_p20_main_baseline.XXXXXX
```

Outcome: exit `0`; created `/tmp/futsub_p20_main_baseline.LSXPLG`.

```bash
git archive bed5893 --output=/tmp/futsub_p20_main_bed5893.tar
tar -xf /tmp/futsub_p20_main_bed5893.tar -C /tmp/futsub_p20_main_baseline.LSXPLG
```

Outcome: both commands exited `0`. `bed5893` is
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P19: Cost-Adjusted
LabelPack Scaleout (#352)`.

```bash
env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES PYTHONPATH=/tmp/futsub_p20_main_baseline.LSXPLG/src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/test_parity_matrix_suite.py tests/unit/label_compute_fast_path/test_session_maintenance_cost_pack.py -q
```

Outcome on clean `bed5893`: exit `1`; `5 failed, 10 passed in 2.03s`.
Failed tests were exactly:

- `tests/unit/label_compute_fast_path/test_parity_matrix_suite.py::test_campaign_level_parity_matrix_covers_every_fast_label_family_and_dimension`
- `tests/unit/label_compute_fast_path/test_parity_matrix_suite.py::test_required_guard_and_missingness_cases_are_exercised_by_the_matrix`
- `tests/unit/label_compute_fast_path/test_session_maintenance_cost_pack.py::test_cost_adjusted_pack_matches_reference_and_preserves_bbo_gap_flags`
- `tests/unit/label_compute_fast_path/test_session_maintenance_cost_pack.py::test_cost_adjusted_maintenance_crossing_window_matches_reference_behavior`
- `tests/unit/label_compute_fast_path/test_session_maintenance_cost_pack.py::test_cost_adjusted_matches_reference_on_misaligned_bbo_timestamps`

The two parity-matrix failures entered through `_cost_adjusted_cases()`, with
assertions failing on cost-adjusted reference/fast quality-flag parity before
the matrix reached path cases. This proves the five fast-label residuals
pre-exist FUTSUB-P20 on clean main and are not introduced by the P20 path
repair.

```bash
env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/test_parity_matrix_suite.py tests/unit/label_compute_fast_path/test_session_maintenance_cost_pack.py -q
```

Outcome on the FUTSUB-P20 branch: exit `1`; `5 failed, 10 passed in 1.79s`,
with the same five failed tests listed above.

```bash
env -u ALPHA_DATA_ROOT -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only -q
```

Outcome: exit `0`; `1 passed in 0.05s`. This confirms the
`test_cache_policy` red in `verify.py --all` matches the known `ALPHA_DATA_ROOT`
environment-only pattern.

Final repair audit:

```bash
git status --short
```

Outcome: exit `0`; unstaged/untracked phase files only:
`README.md`, `configs/labels/scaleout/path.json`,
`src/alpha_system/features/scaleout/driver.py`,
`src/alpha_system/labels/families/path/family.py`,
`src/alpha_system/labels/fast/path.py`,
`tests/unit/label_compute_fast_path/test_path_label_pack.py`,
`handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P20.md`,
`research/futures_substrate_scaleout_v1/label_packs/path/`, and
`tests/unit/futures_substrate_scaleout/labels/test_path_scaleout.py`.

```bash
git diff --cached --name-only
```

Outcome: exit `0`; empty output, no staged files.

```bash
grep -n "importorskip" tests/unit/futures_substrate_scaleout/labels/test_path_scaleout.py tests/unit/label_compute_fast_path/test_path_label_pack.py
grep -rn "polars\|value_store\|seed_pack\|data.storage" tests/unit/futures_substrate_scaleout/labels/test_path_scaleout.py tests/unit/label_compute_fast_path/test_path_label_pack.py
```

Outcome: exit `0`; both greps found `pytest.importorskip("polars")` at
`test_path_scaleout.py:7` and at the existing function-level guards in
`test_path_label_pack.py` (`50`, `114`, `159`, `196`, `297`).

```bash
git ls-files runs
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'
```

Outcome: exit `0`; both commands returned empty output.

Not run by executor repair attempts:

- Reviewer / Claude / `review.md` / `verdict.json`: not run or created per
  executor instructions.

## Test Hygiene

- New/modified test files:
  `tests/unit/futures_substrate_scaleout/labels/test_path_scaleout.py`.
- `tests/unit/label_compute_fast_path/test_path_label_pack.py` was modified
  during repair attempt 1 to align the LCFP regression with the guarded path
  reference semantics while preserving fast/reference parity assertions.
- Both files import/exercise the polars-backed fast label path and carry
  `pytest.importorskip("polars")` where required (`test_path_scaleout.py` at
  module level; the existing fast-path regression test at function level).
- Pre-handoff grep checks for `importorskip` and data-layer terms were run and
  are recorded above.
- No path-family enum was extended, so no existing family governance /
  parametrized tests required generalization.
- No test assertions were weakened, skipped, or relaxed.

## Local-Only Artifacts

- Materialized path label values, manifests, checkpoints, and
  `registry/labels.sqlite` updates are local-only under
  `/home/yuke_zhang/alpha_data/alpha_system`.
- Command summaries and aggregate scratch outputs were written under `/tmp`.
- The run artifact directory named in the executor prompt was not present in
  this sandboxed worktree; no run-local
  `runs/<run_id>/phases/FUTSUB-P20/handoff.md` was created.

## Executor Boundary

- Did not call Claude.
- Did not run reviewer.
- Did not create `review.md`.
- Did not create `verdict.json`.
- Did not create a PR.
- Did not merge.
- Did not mark the phase PASS.
- Did not run `git add`, `git commit`, or `git push`; read-only git audit
  commands were run during the repair attempt and are recorded above.
- Did not stage or commit anything under `runs/`.
