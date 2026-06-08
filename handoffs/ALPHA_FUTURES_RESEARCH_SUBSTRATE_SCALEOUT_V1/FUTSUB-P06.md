# FUTSUB-P06 Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P06` - Scaleout Materialization Driver + Base OHLCV FeaturePack Scaleout  
Executor: Codex  
Lane: Yellow

## Status

Executor implementation scope is complete for the reusable FeaturePack scaleout
driver, CLI, base OHLCV planning, restart ledger behavior, value-free docs,
value-free summaries, tests, README snapshot, and this handoff. This handoff
does not mark the phase PASS.

Bounded-real materialization was attempted first and is blocked in this executor
environment because `$ALPHA_DATA_ROOT` is outside the writable sandbox roots:

```text
scaleout command error: [Errno 30] Read-only file system: '/home/yuke_zhang/alpha_data/alpha_system/materialization'
```

No full-window materialization was run after that bounded-real environment
block. No live trading, paper trading, broker operation, order routing,
provider call, raw-provider read, runtime diagnostics, PR creation, merge,
reviewer call, `review.md`, or `verdict.json` was performed by Codex.

## Scope Completed

- Added `alpha_system.features.scaleout` with a generic, config-driven
  `family x schema x symbol x accepted-year` driver.
- Added `alpha scaleout feature-pack` with dry-run default and explicit
  `--execute` mode.
- Driver planning reads the P05 FeaturePack config plus the value-free P02
  acceptance summary. Execution requires exact persisted DatasetVersion
  acceptance locks and fails closed on missing, blocked, or mismatched locks.
- Driver execution reuses the existing governed seed-pack path, sanctioned
  canonical loader, Parquet value store, and
  `FeatureStore.register_materialized_feature`.
- Base OHLCV scaleout uses Parquet-only research-scale values.
- Added local-only restart ledger/checkpoint behavior under `ALPHA_DATA_ROOT`;
  completed units are skipped, and incomplete completion evidence fails closed.
- Fixed Base OHLCV materialized feature identity so symbol/partition scope is a
  deterministic computational input, avoiding ES/NQ/RTY feature-version
  collisions for the same yearly DatasetVersion.
- Updated the FeaturePack DatasetVersion inventory annotations to match the
  current P02 `20 ACCEPTED` / `5 ACCEPTED_WITH_WARNINGS` / `2 BLOCKED`
  value-free acceptance summary.
- Added value-free driver and base OHLCV summaries.

## Executor Staging

Codex staged no files. The explicit staged file set from Codex is empty.

Ralph stage candidates, by explicit path:

- `src/alpha_system/features/scaleout/__init__.py`
- `src/alpha_system/features/scaleout/driver.py`
- `src/alpha_system/features/families/ohlcv/family.py`
- `src/alpha_system/cli/scaleout.py`
- `src/alpha_system/cli/main.py`
- `src/alpha_system/cli/seed_pack.py`
- `configs/features/scaleout/dataset_version_inventory.json`
- `docs/futures_substrate_scaleout/SCALEOUT_DRIVER.md`
- `research/futures_substrate_scaleout_v1/feature_packs/base_ohlcv/coverage_summary.md`
- `research/futures_substrate_scaleout_v1/scaleout_driver/driver_summary.md`
- `tests/unit/futures_substrate_scaleout/scaleout/test_scaleout_driver.py`
- `tests/unit/futures_substrate_scaleout/features/test_base_ohlcv_scaleout_identity.py`
- `README.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P06.md`

No review artifacts were created by Codex. Ralph owns Yellow-lane review
routing and any review files under
`reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P06/**`.

## Rollout Result

Dry-run bounded-real preview:

- accepted base OHLCV units: `24`
- bounded-real units: `3` (`2024 x ES/NQ/RTY`)
- planned bounded-real units: `3`
- failed dry-run units: `0`
- write-free identity preview confirmed symbol-scoped FeatureVersion ids.

Bounded-real execute:

- command attempted:
  `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/base_ohlcv.json --rollout bounded-real --execute --alpha-data-root "$ALPHA_DATA_ROOT" --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --json`
- result: blocked before value materialization by read-only
  `$ALPHA_DATA_ROOT/materialization` in this sandbox.
- full-window execute: not run because bounded-real did not complete.

## 2018 Handling

The phase uses the fallback authorized by the spec. Per-symbol 2018 eligibility
would require broadening acceptance semantics beyond this phase's driver scope,
so base OHLCV scaleout excludes the blocked 2018 `ohlcv_1m` DatasetVersion at
the DatasetVersion level. The existing value-free diagnosis remains at
`research/futures_substrate_scaleout_v1/dataset_acceptance/2018_BLOCKED_DIAGNOSIS.md`.

Full accepted base OHLCV planning window is therefore 2019 through 2026 for
ES/NQ/RTY:

- 2019: `ACCEPTED_WITH_WARNINGS`
- 2020 through 2025: `ACCEPTED`
- 2026: `ACCEPTED_WITH_WARNINGS` partial-year window through
  `2026-06-01T00:00:00+00:00`

## Validation

Commands run from the provided WSL2 worktree root:

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP && test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P06/STOP` | PASS; STOP absent. |
| `python -m py_compile src/alpha_system/features/scaleout/__init__.py src/alpha_system/features/scaleout/driver.py src/alpha_system/cli/scaleout.py src/alpha_system/cli/main.py tests/unit/futures_substrate_scaleout/scaleout/test_scaleout_driver.py` | PASS. |
| `python -m py_compile src/alpha_system/features/families/ohlcv/family.py src/alpha_system/cli/seed_pack.py src/alpha_system/features/scaleout/driver.py` | PASS. |
| `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/base_ohlcv.json --rollout bounded-real --json` | PASS; dry-run preview reported `24` accepted units, `3` bounded units, `3` planned, `0` failed. |
| `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/base_ohlcv.json --rollout full-window --summary-out research/futures_substrate_scaleout_v1/feature_packs/base_ohlcv/coverage_summary.md --json` | PASS; generated value-free full-window summary. |
| `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/base_ohlcv.json --rollout bounded-real --summary-out research/futures_substrate_scaleout_v1/scaleout_driver/driver_summary.md --json` | PASS; generated value-free bounded-real summary. |
| `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/base_ohlcv.json --rollout bounded-real --execute --alpha-data-root "$ALPHA_DATA_ROOT" --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --json` | ENV BLOCKED; exit code `2`; read-only filesystem at `$ALPHA_DATA_ROOT/materialization`. |
| `python -c "import alpha_system.features, alpha_system.core.value_store, alpha_system.data.foundation.canonical_loader"` | PASS. |
| `python tools/verify.py --smoke` | PASS. |
| `python tools/verify.py --lint` | ENV-ONLY SKIP; exit code `0`; `ruff is not installed; run pip install -e ".[dev]" to enable lint. Skipping.` |
| `python tools/verify.py --typecheck` | PASS; compileall over `src`, `tests`, and `tools`. |
| `python -m pytest tests/unit/futures_substrate_scaleout/scaleout -q` | PASS; `2 passed`. |
| `python -m pytest tests/unit/futures_substrate_scaleout/features -q` | PASS; `1 passed`. |
| `python -m pytest tests/unit/cli/test_feature_cli.py tests/unit/features/families/ohlcv/test_ohlcv_family.py -q` | PASS; `19 passed`. |
| JSON parse check for `configs/features/scaleout/dataset_version_inventory.json` and `configs/features/scaleout/base_ohlcv.json` | PASS. |
| `python tools/hooks/canary_runner.py` | PASS; all Frontier canaries passed. |
| `git ls-files runs` | PASS; output empty. |
| `git ls-files '**/*.parquet' '**/*.arrow' '**/*.feather' '**/*.sqlite' '**/*.db' '**/*.dbn' '**/*.zst'` | PASS; output empty. |

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
