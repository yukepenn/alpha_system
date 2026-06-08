# FUTSUB-P08 Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P08` - VWAP / Session Auction FeaturePack Scaleout  
Executor: Codex  
Lane: Yellow

## Status

Executor implementation scope is complete for the VWAP / session-auction
scaleout config, scaleout driver family dispatch, value-free coverage summary,
focused synthetic test, README snapshot, and this handoff. This handoff does
not mark the phase PASS.

Bounded-real materialization was attempted and is blocked in this executor
environment because `$ALPHA_DATA_ROOT` is outside the writable sandbox roots:

```text
scaleout command error: [Errno 30] Read-only file system: '/home/yuke_zhang/alpha_data/alpha_system/materialization'
```

No full-window materialization was run after that bounded-real environment
block. No Parquet values, SQLite registry rows, checkpoint markers, review
artifacts, `review.md`, `verdict.json`, PR, merge, live trading, paper trading,
broker operation, order routing, provider call, or raw-provider read was
performed by Codex.

## Scope Completed

- Extended the FUTSUB-P06 scaleout driver through its family executor seam for
  `vwap_session_auction`.
- Bound the P08 config labels to existing governed OHLCV family definitions:
  `running_vwap -> vwap`, `anchored_eth_vwap -> anchored_vwap` with `ETH`
  anchor, `distance_to_vwap -> distance_to_vwap`, `opening_range`,
  `overnight_range`, and `rth_open_context -> session_minute`.
- Added explicit value-free anchor/leakage metadata to
  `configs/features/scaleout/vwap_session_auction.json`.
- The P08 executor uses the sanctioned accepted-context loader,
  `materialize_features`, Parquet value store, and
  `FeatureStore.register_materialized_feature`; it does not hand-write registry
  records.
- The executor registers each materialized feature only after Parquet write
  evidence exists and verifies required registry fields through the existing
  registry round-trip helper.
- Added a tiny synthetic unit test proving running VWAP and anchored ETH VWAP
  use current-row `available_ts` state rather than final-session aggregates.
- Generated value-free full-window coverage evidence for the planned accepted
  window.

No family-code repair under `src/alpha_system/features/families/ohlcv/**` or
`src/alpha_system/features/families/session/**` was required.

## Executor Staging

Codex staged no files. The explicit staged file list from Codex is empty.

Ralph stage candidates, by explicit path:

- `src/alpha_system/features/scaleout/__init__.py`
- `src/alpha_system/features/scaleout/driver.py`
- `configs/features/scaleout/vwap_session_auction.json`
- `research/futures_substrate_scaleout_v1/feature_packs/vwap_session_auction/coverage_summary.md`
- `tests/unit/futures_substrate_scaleout/features/test_vwap_session_scaleout.py`
- `README.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P08.md`

## Rollout Result

Dry-run full-window preview:

- accepted VWAP/session-auction units: `24`
- planned units: `24`
- failed dry-run units: `0`
- symbols: `ES`, `NQ`, `RTY`
- years: `2019` through `2026`
- 2018 excluded because `ohlcv_1m` is `BLOCKED`
- 2019 and 2026 retain `ACCEPTED_WITH_WARNINGS`
- 2026 partial window end: `2026-06-01T00:00:00+00:00`

Bounded-real execute:

- command attempted:
  `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/vwap_session_auction.json --rollout bounded-real --execute --alpha-data-root "$ALPHA_DATA_ROOT" --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --json`
- result: ENV BLOCKED; exit code `2`; read-only filesystem at
  `$ALPHA_DATA_ROOT/materialization`.
- full-window execute: not run because bounded-real did not complete.

Because execution was blocked before value writes, actual Parquet paths,
`value_content_hash` values, materialized row counts, observed `available_ts`
min/max, registry rows, and checkpoint completion markers are unavailable from
this executor run. The driver verifies `value_store_format`, `parquet_path`,
`value_content_hash`, `value_schema_version`, `dataset_version_id`, and
`feature_version_id` when execution succeeds.

## DatasetVersions

Planned full-window input DatasetVersions:

| Year | `ohlcv_1m` state | DatasetVersion |
| ---: | --- | --- |
| 2019 | `ACCEPTED_WITH_WARNINGS` | `dsv_databento_ohlcv_a483cc0cc282474b` |
| 2020 | `ACCEPTED` | `dsv_databento_ohlcv_bac95e92f1bb1850` |
| 2021 | `ACCEPTED` | `dsv_databento_ohlcv_8aeb50fb409fc691` |
| 2022 | `ACCEPTED` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` |
| 2023 | `ACCEPTED` | `dsv_databento_ohlcv_ec144f9a02a64774` |
| 2024 | `ACCEPTED` | `dsv_databento_ohlcv_05404069799decb0` |
| 2025 | `ACCEPTED` | `dsv_databento_ohlcv_35ffead770498acd` |
| 2026 | `ACCEPTED_WITH_WARNINGS` | `dsv_databento_ohlcv_a0342ee6a412622b` |

Each planned year is one unit per symbol: `ES`, `NQ`, and `RTY`.

## Running-Vs-Final Discipline

The P08 config and driver record the following value-free discipline:

- running VWAP and distance-to-VWAP are expanding point-in-time calculations at
  each row `available_ts`;
- anchored ETH VWAP starts from the ETH anchor and carries forward only source
  rows already available at the output `available_ts`;
- final-session VWAP, full-session value area, and closing-auction aggregates
  are forbidden as intraday inputs;
- the synthetic test asserts early rows do not equal the final session/anchor
  VWAP when later rows change the final aggregate.

## Validation

Commands run from the provided WSL2 worktree root:

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP` | PASS; STOP absent. |
| `test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P08/STOP` | PASS; phase STOP absent. |
| `python -m py_compile src/alpha_system/features/scaleout/__init__.py src/alpha_system/features/scaleout/driver.py tests/unit/futures_substrate_scaleout/features/test_vwap_session_scaleout.py` | PASS. |
| `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/vwap_session_auction.json --rollout full-window --summary-out research/futures_substrate_scaleout_v1/feature_packs/vwap_session_auction/coverage_summary.md --json` | PASS; dry-run summary reported `24` planned, `0` failed. |
| `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/vwap_session_auction.json --rollout bounded-real --execute --alpha-data-root "$ALPHA_DATA_ROOT" --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --json` | ENV BLOCKED; exit code `2`; read-only filesystem at `$ALPHA_DATA_ROOT/materialization`. |
| `python tools/verify.py --smoke` | PASS; exit code `0`. |
| `PYTHONPATH=src python -m pytest tests/unit/futures_substrate_scaleout/features/test_vwap_session_scaleout.py -q` | PASS; `3 passed`. |
| `python tools/hooks/canary_runner.py` | PASS; all Frontier canaries passed. |
| `test -f configs/features/scaleout/vwap_session_auction.json` | PASS. |
| `test -f research/futures_substrate_scaleout_v1/feature_packs/vwap_session_auction/coverage_summary.md` | PASS. |
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
backup, secret, credential, cache, or log file was created as a commit candidate
by Codex.

The attempted bounded-real execute did not write local-only values because the
configured `$ALPHA_DATA_ROOT` is read-only to this executor. Codex did not stage
anything, so no staged set exists from the executor side.
