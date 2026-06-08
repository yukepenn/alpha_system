# FUTSUB-P07 Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P07` - Session / Calendar / Maintenance FeaturePack Scaleout  
Executor: Codex  
Lane: Yellow

## Status

Executor implementation scope is complete for the session scaleout config,
session unit-executor dispatch, point-in-time session metadata guard repair,
symbol-scoped session FeatureVersion identity repair, value-free coverage
summary, focused tests, README snapshot, and this handoff.

Bounded-real materialization was attempted and is blocked in this executor
environment because `$ALPHA_DATA_ROOT` is outside the writable sandbox roots:

```text
scaleout command error: [Errno 30] Read-only file system: '/home/yuke_zhang/alpha_data/alpha_system/materialization'
```

No full-window materialization was run after that bounded-real environment
block. No live trading, paper trading, broker operation, order routing,
provider call, raw-provider read, runtime diagnostics, PR creation, merge,
reviewer call, `review.md`, or `verdict.json` was performed by Codex. This
handoff does not mark the phase PASS.

## Scope Completed

- Added the P07 session/calendar/maintenance scaleout config with the governed
  existing session family features:
  `session_id`, `minutes_from_rth_open`, `minutes_to_rth_close`,
  `rth_segment_flag`, `eth_segment_flag`, `day_of_week`, `bars_to_roll`,
  `minutes_to_roll`, `minutes_to_expiration`, and `halt_status_flag`.
- Extended the FUTSUB-P06 scaleout driver through the sanctioned family
  dispatch / unit-executor seam for `session_calendar_maintenance`.
- Multi-input units now plan one `family x symbol x year` unit and require every
  configured input schema/year lock before execution. The session family uses
  `ohlcv_dense_research_grid` as the primary materialization input while also
  requiring the paired `ohlcv_1m` lock.
- Added `ScaleoutInputDataset` evidence to unit records and ledgers while
  preserving single-input P06 identity payloads.
- Added a session family `input_view_name` parameter so P07 contracts can bind
  `dense_grid_ohlcv` explicitly without changing default session behavior.
- Added explicit point-in-time metadata availability guards:
  row-specific expiration/status metadata with an explicit metadata
  availability timestamp later than the row `available_ts` fails closed.
- Added symbol/partition `input_scope` to P07 session FeatureSpecs so ES/NQ/RTY
  do not share FeatureVersion ids for the same yearly DatasetVersion pair.
- Tightened feature registry round-trip verification to require Parquet,
  `parquet_path`, `value_content_hash`, and `value_schema_version` when
  execution succeeds.
- Generated value-free coverage evidence for the full accepted dry-run window.

## Executor Staging

Codex staged no files. The explicit staged file set from Codex is empty.

Ralph stage candidates, by explicit path:

- `src/alpha_system/features/families/session/family.py`
- `src/alpha_system/features/scaleout/__init__.py`
- `src/alpha_system/features/scaleout/driver.py`
- `configs/features/scaleout/session_calendar_maintenance.json`
- `research/futures_substrate_scaleout_v1/feature_packs/session_calendar_maintenance/coverage_summary.md`
- `tests/unit/futures_substrate_scaleout/features/test_session_scaleout.py`
- `tests/unit/futures_substrate_scaleout/scaleout/test_session_scaleout_driver.py`
- `README.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P07.md`

No review artifacts were created by Codex. Ralph owns Yellow-lane review
routing and any review files under
`reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P07/**`.

## Rollout Result

Dry-run bounded-real preview:

- accepted session units: `24`
- bounded-real units: `3` (`2024 x ES/NQ/RTY`)
- planned bounded-real units: `3`
- failed dry-run units: `0`
- write-free identity preview confirmed symbol-scoped FeatureVersion ids.

Dry-run full-window preview:

- planned accepted units: `24`
- symbols: `ES`, `NQ`, `RTY`
- years: `2019` through `2026`
- 2018 excluded because `ohlcv_1m` is `BLOCKED`; the accepted dense-grid 2018
  DatasetVersion is not sufficient because P07 requires every configured input
  schema/year to be executable.
- primary materialization schema: `ohlcv_dense_research_grid`
- paired lock schema: `ohlcv_1m`
- 2026 partial window end: `2026-06-01T00:00:00+00:00`

Bounded-real execute:

- command attempted:
  `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/session_calendar_maintenance.json --rollout bounded-real --execute --alpha-data-root "$ALPHA_DATA_ROOT" --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --json`
- result: ENV BLOCKED; exit code `2`; read-only filesystem at
  `$ALPHA_DATA_ROOT/materialization`.
- full-window execute: not run because bounded-real did not complete.

Because execution was blocked before value writes, actual Parquet paths,
`value_content_hash` values, value row counts, registry rows, available-ts
min/max from materialized values, and real checkpoint completion markers are not
available from this executor run. The driver verifies those registry fields when
execution succeeds, and the synthetic seam test verifies restart skip behavior
from completed unit markers.

## DatasetVersions

Planned full-window input DatasetVersions:

| Year | `ohlcv_1m` | `ohlcv_dense_research_grid` |
| ---: | --- | --- |
| 2019 | `dsv_databento_ohlcv_a483cc0cc282474b` (`ACCEPTED_WITH_WARNINGS`) | `dsv_databento_ohlcv_dense_2019_v1` (`ACCEPTED`) |
| 2020 | `dsv_databento_ohlcv_bac95e92f1bb1850` (`ACCEPTED`) | `dsv_databento_ohlcv_dense_2020_v1` (`ACCEPTED`) |
| 2021 | `dsv_databento_ohlcv_8aeb50fb409fc691` (`ACCEPTED`) | `dsv_databento_ohlcv_dense_2021_v1` (`ACCEPTED`) |
| 2022 | `dsv_databento_ohlcv_dc7c86c813fe0dfe` (`ACCEPTED`) | `dsv_databento_ohlcv_dense_2022_v1` (`ACCEPTED`) |
| 2023 | `dsv_databento_ohlcv_ec144f9a02a64774` (`ACCEPTED`) | `dsv_databento_ohlcv_dense_2023_v1` (`ACCEPTED`) |
| 2024 | `dsv_databento_ohlcv_05404069799decb0` (`ACCEPTED`) | `dsv_databento_ohlcv_dense_2024_v1` (`ACCEPTED`) |
| 2025 | `dsv_databento_ohlcv_35ffead770498acd` (`ACCEPTED`) | `dsv_databento_ohlcv_dense_2025_v1` (`ACCEPTED`) |
| 2026 | `dsv_databento_ohlcv_a0342ee6a412622b` (`ACCEPTED_WITH_WARNINGS`) | `dsv_databento_ohlcv_dense_2026_v1` (`ACCEPTED_WITH_WARNINGS`) |

## Validation

Commands run from the provided WSL2 worktree root:

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP` | PASS; STOP absent. |
| `test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P07/STOP` | PASS; STOP absent. |
| `python -m py_compile src/alpha_system/features/scaleout/__init__.py src/alpha_system/features/scaleout/driver.py src/alpha_system/features/families/session/family.py tests/unit/futures_substrate_scaleout/features/test_session_scaleout.py tests/unit/futures_substrate_scaleout/scaleout/test_session_scaleout_driver.py` | PASS. |
| `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/session_calendar_maintenance.json --rollout full-window --summary-out research/futures_substrate_scaleout_v1/feature_packs/session_calendar_maintenance/coverage_summary.md --json` | PASS; generated value-free full-window summary with `24` planned units and `0` failed units. |
| `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/session_calendar_maintenance.json --rollout bounded-real --json` | PASS; dry-run preview reported `24` accepted units, `3` bounded units, `3` planned, `0` failed. |
| `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/session_calendar_maintenance.json --rollout bounded-real --execute --alpha-data-root "$ALPHA_DATA_ROOT" --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --json` | ENV BLOCKED; exit code `2`; read-only filesystem at `$ALPHA_DATA_ROOT/materialization`. |
| `python tools/verify.py --smoke` | PASS. |
| `python -m pytest tests/unit/futures_substrate_scaleout/features/test_session_scaleout.py -q` | PASS; `3 passed`. |
| `python -m pytest tests/unit/futures_substrate_scaleout/scaleout/test_session_scaleout_driver.py -q` | PASS; `2 passed`. |
| `python tools/hooks/canary_runner.py` | PASS; all Frontier canaries passed. |
| `test -f configs/features/scaleout/session_calendar_maintenance.json` | PASS. |
| `test -f research/futures_substrate_scaleout_v1/feature_packs/session_calendar_maintenance/coverage_summary.md` | PASS. |
| `git ls-files runs` | PASS; output empty. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'` | PASS; output empty. |

Commands intentionally not run by Codex due to the explicit executor override:

- `git status --short`
- `git diff`
- `git diff --cached --name-only`
- `git add`
- `git commit`
- `git push`
- any PR, merge, reviewer, verdict, or PASS-marking command

## Artifact Boundary

No `runs/**` path, run-local handoff, review artifact, verdict artifact,
Parquet, Arrow, Feather, DB, SQLite, DBN, Zstd, provider response, raw data,
canonical data, feature value, label value, local checkpoint marker, registry
backup, secret, credential, cache, or log file was created as a commit
candidate by Codex.

The attempted bounded-real execute did not write local-only values because the
configured `$ALPHA_DATA_ROOT` is read-only to this executor. Codex did not stage
anything, so no staged set exists from the executor side.
