# FUTSUB-P12 Executor Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P12`  
Lane: Yellow  
Executor: Codex

## Intended Commit File List

All changes were left unstaged per executor instructions. Ralph owns staging and
commit.

- `README.md`
- `src/alpha_system/data/foundation/canonical_loader.py`
- `src/alpha_system/features/families/bbo/family.py`
- `src/alpha_system/features/scaleout/driver.py`
- `src/alpha_system/features/scaleout/__init__.py`
- `tests/unit/futures_substrate_scaleout/features/test_bbo_tradability_scaleout.py`
- `tests/unit/futures_substrate_scaleout/scaleout/test_bbo_tradability_scaleout_driver.py`
- `research/futures_substrate_scaleout_v1/feature_packs/bbo_tradability_top_book/coverage_summary.md`
- `handoffs/FUTSUB-P12.md`

Existing config confirmed present and consumed:

- `configs/features/scaleout/bbo_tradability_top_book.json`

## Implementation Summary

- Added `bbo_tradability_top_book` support on the existing FUTSUB-P06
  `UnitExecutor` seam.
- Added a canonical BBO Parquet loader that reads only already-canonical local
  `bbo_1m` partitions and preserves BBO quality flags.
- Added symbol/partition `input_scope` support to existing BBO feature
  definitions so P12 FeatureVersion previews are scoped by DatasetVersion,
  symbol, year, partition, and feature-set version. No BBO formula changed.
- Bound P12 config labels to existing governed BBO primitives: mid, spread,
  spread ticks, spread z-score, top-book depth/imbalance, missing/bad/wide/low
  flags, and `microprice_proxy -> microprice`.
- Reused the sanctioned scaleout/materialization path: acceptance-lock gate,
  canonical BBO loader, `materialize_features`, Parquet value-store format, and
  `FeatureStore.register_materialized_feature`.
- Added explicit BBO proxy metadata: BBO-1m is a time-sampled and
  forward-filled tradability proxy only; passive-fill, queue-priority, impact,
  intra-minute path, and execution-truth claims are forbidden.
- Added focused synthetic tests for P12 dry-run identity, BBO `available_ts`
  discipline, missingness surfacing, proxy guardrails, and driver dispatch.
- Updated README snapshot and wrote value-free P12 coverage evidence.

The generated spec file path from the prompt was absent in this checkout, and
the provided run phase directory was also absent. Execution used the prompt
contract, campaign phase plan, and predecessor handoff patterns without
broadening scope.

## Materialization Result

The full-window dry-run preview succeeded:

- Rollout: `full-window`
- Accepted units: `24`
- Bounded-real year: `2024`
- Bounded-real units: `3`
- Planned units: `24`
- Failed preview units: `0`
- FeatureVersion preview count: `264` ids (`24` units x `11` governed BBO
  primitives)
- 2018 blocked `bbo_1m` DatasetVersion excluded by the acceptance summary.
- 2019 and 2026 retained `ACCEPTED_WITH_WARNINGS` metadata.
- Per-symbol/year coverage and bounded-real FeatureVersion previews are recorded
  value-free in
  `research/futures_substrate_scaleout_v1/feature_packs/bbo_tradability_top_book/coverage_summary.md`.

The bounded-then-full execute command was attempted but did not write values:

```bash
PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/bbo_tradability_top_book.json --rollout bounded-then-full --execute --alpha-data-root "$ALPHA_DATA_ROOT" --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --json
```

Outcome:

```text
scaleout command error: [Errno 30] Read-only file system: '/home/yuke_zhang/alpha_data/alpha_system/materialization'
```

Because this executor sandbox cannot write the local materialization area, the
real bounded-real and full-window Parquet writes, checkpoint markers, registry
rows, content hashes, and materialized `available_ts` min/max are not available
from this run. The P12 executor verifies required registry fields
(`value_store_format`, `parquet_path`, `value_content_hash`,
`value_schema_version`, `dataset_version_id`, `feature_version_id`) after a
successful execute, but no real registry rows were written here.

## DatasetVersions Previewed

Each listed year covers `ES`, `NQ`, and `RTY`; all units consume `bbo_1m`.

| Year | DatasetVersion | Acceptance state |
| ---: | --- | --- |
| 2019 | `dsv_databento_bbo_f91f510a8d6fa87b` | `ACCEPTED_WITH_WARNINGS` |
| 2020 | `dsv_databento_bbo_af9511d169b0aead` | `ACCEPTED` |
| 2021 | `dsv_databento_bbo_d5cb08f949e7ff28` | `ACCEPTED` |
| 2022 | `dsv_databento_bbo_7b5595d5030462ab` | `ACCEPTED` |
| 2023 | `dsv_databento_bbo_8772e3b47aa5fb98` | `ACCEPTED` |
| 2024 | `dsv_databento_bbo_f9e1d70a04d9dae4` | `ACCEPTED` |
| 2025 | `dsv_databento_bbo_35d4417c086be53f` | `ACCEPTED` |
| 2026 | `dsv_databento_bbo_22c49fbf57cceea6` | `ACCEPTED_WITH_WARNINGS` |

## Validation

- `test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP && test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P12/STOP`
  - Passed; STOP absent.
- `PYTHONPATH=src python -m compileall -q src/alpha_system/data/foundation/canonical_loader.py src/alpha_system/features/scaleout tests/unit/futures_substrate_scaleout/features/test_bbo_tradability_scaleout.py tests/unit/futures_substrate_scaleout/scaleout/test_bbo_tradability_scaleout_driver.py`
  - Passed.
- `PYTHONPATH=src python -m compileall -q src/alpha_system/features/families/bbo/family.py src/alpha_system/features/scaleout tests/unit/futures_substrate_scaleout/features/test_bbo_tradability_scaleout.py tests/unit/futures_substrate_scaleout/scaleout/test_bbo_tradability_scaleout_driver.py`
  - Passed.
- `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/bbo_tradability_top_book.json --rollout full-window --summary-out research/futures_substrate_scaleout_v1/feature_packs/bbo_tradability_top_book/coverage_summary.md --json`
  - Passed; produced `24` planned units, `0` failed units.
- `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/bbo_tradability_top_book.json --rollout bounded-then-full --execute --alpha-data-root "$ALPHA_DATA_ROOT" --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --json`
  - Failed before writes with read-only local materialization area as shown
    above.
- `python tools/verify.py --smoke`
  - Passed.
- `PYTHONPATH=src python -m pytest tests/unit/futures_substrate_scaleout/features/test_bbo_tradability_scaleout.py -q`
  - Passed: `2 passed`.
- `PYTHONPATH=src python -m pytest tests/unit/futures_substrate_scaleout/scaleout -q`
  - Passed: `11 passed`.
- `PYTHONPATH=src python -m pytest tests/unit/features/families/bbo/test_bbo_family.py -q`
  - Passed: `8 passed`.
- `python tools/hooks/canary_runner.py`
  - Passed: all Frontier canaries passed.
- `test -f configs/features/scaleout/bbo_tradability_top_book.json && test -f research/futures_substrate_scaleout_v1/feature_packs/bbo_tradability_top_book/coverage_summary.md`
  - Passed.
- `git ls-files runs`
  - Passed; output empty.
- `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'`
  - Passed; output empty.

Commands intentionally not run by Codex due to the explicit executor override:

- `git status --short`
- `git diff`
- `git diff --cached --name-only`
- `git add`
- `git commit`
- `git push`
- any PR, merge, reviewer, verdict, or PASS-marking command

## Artifact And Safety Notes

- No `runs/**` path, run-local handoff, review artifact, or verdict artifact
  was created by Codex.
- No `review.md`, `verdict.json`, PR, merge, live, paper, broker, order, or
  deployment action was performed.
- No feature values, Parquet files, SQLite registries, provider responses, raw
  data, canonical data, roll-calendar data, checkpoint markers, registry
  backups, secrets, credentials, caches, or logs were written into the
  repository.
- BBO outputs are documented as research substrate tradability proxies only,
  not profitability evidence, passive-fill evidence, queue evidence, impact
  evidence, or execution truth.
- Phase is not marked PASS by this executor.
