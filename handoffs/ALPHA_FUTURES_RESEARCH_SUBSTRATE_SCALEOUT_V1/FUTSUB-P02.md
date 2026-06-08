# FUTSUB-P02 Executor Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P02` - DatasetVersion Inventory and Acceptance-Lock Contract  
Executor: Codex  
Lane: Yellow

## Status

Executor implementation scope is complete for the code, CLI, config, docs,
tests, README snapshot, and value-free inventory summary. This handoff does not
mark the phase PASS.

Local registry persistence was attempted through the new sanctioned CLI path
and is blocked in this executor environment because the DatasetVersion registry
opened as read-only:

```text
dataset acceptance error: could not persist DatasetVersion acceptance lock: dsv_databento_bbo_22c49fbf57cceea6: attempt to write a readonly database
```

Ralph or an unsandboxed local operator must rerun the persist command with a
writable `$ALPHA_DATA_ROOT/registry/datasets.sqlite` before downstream phases
can treat the acceptance-lock as persisted.

No live trading, paper trading, broker operation, order routing, provider call,
raw provider read, feature/label materialization, diagnostics run, PR creation,
merge, reviewer call, `review.md`, or `verdict.json` was performed by Codex.

## Scope Completed

- Added DatasetVersion acceptance-lock states:
  `ACCEPTED`, `ACCEPTED_WITH_WARNINGS`, `BLOCKED`.
- Added coverage-driven verdict logic that fails closed when required coverage
  evidence is missing; missing evidence cannot produce `ACCEPTED`.
- Added exact DatasetVersion registry inventory for the FUTSUB-P02 Databento
  matrix through `resolve_dataset_version` and local registry metadata only.
- Added local registry persistence helpers that attach the lock to
  `dataset_versions.metadata_json` and `artifact_manifest` through sanctioned
  code paths when the registry is writable.
- Added read-only CLI:
  `alpha registry dataset-acceptance inventory` and
  `alpha registry dataset-acceptance show`.
- Added write CLI:
  `alpha data accept-datasets`.
- Added the value-free acceptance policy, contract doc, unit tests, synthetic
  fixture policy, README snapshot, and value-free summary.

## Inventory Result

Read-only inventory command:

```bash
PYTHONPATH=src python -m alpha_system.cli registry dataset-acceptance inventory --registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --config configs/data/dataset_acceptance/futsub_p02_policy.json --summary-out research/futures_substrate_scaleout_v1/dataset_acceptance/acceptance_summary.md --json
```

Result:

- Expected schema/year matrix complete: `yes`.
- In-scope Databento DatasetVersions inventoried: `27`.
- `ACCEPTED`: `0`.
- `ACCEPTED_WITH_WARNINGS`: `0`.
- `BLOCKED`: `27`.
- Blocking reason count per version: `5`.

The all-`BLOCKED` result is intentional for the evidence currently persisted in
the registry: schema, symbol, year/date-range, exact resolver, and continuous
provenance metadata are available, but row-count/expected-bar sanity, gap
coverage, required-field presence, missingness/quality-flag evidence, and
roll-boundary metadata are not persisted as coverage evidence.

## Files Created Or Modified

Codex staged no files. Ralph stage candidates for this phase, by explicit path:

| Path | Outcome |
| --- | --- |
| `src/alpha_system/data/foundation/datasets.py` | Added acceptance-lock model, verdict logic, inventory, summary rendering, and local registry persistence helpers. |
| `src/alpha_system/cli/registry.py` | Added read-only DatasetVersion acceptance inventory/show commands. |
| `src/alpha_system/cli/data.py` | Added `data accept-datasets` persistence command. |
| `configs/data/dataset_acceptance/futsub_p02_policy.json` | Added FUTSUB-P02 value-free acceptance policy. |
| `docs/futures_substrate_scaleout/DATASET_ACCEPTANCE.md` | Added acceptance-lock contract documentation. |
| `research/futures_substrate_scaleout_v1/dataset_acceptance/acceptance_summary.md` | Added value-free read-only inventory summary. |
| `tests/unit/futures_substrate_scaleout/test_dataset_acceptance.py` | Added coverage verdict, state mapping, fail-closed, persistence, and no-network tests. |
| `tests/fixtures/futures_substrate_scaleout/dataset_acceptance/policy_minimal.json` | Added tiny synthetic test policy. |
| `tests/fixtures/futures_substrate_scaleout/dataset_acceptance/README.md` | Documented fixture locality and synthetic status. |
| `README.md` | Updated compact campaign snapshot for `FUTSUB-P02` and next phase `FUTSUB-P03`. |
| `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P02.md` | Created this commit-eligible handoff. |

No `reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P02/**`
artifact was created by Codex because the executor prompt explicitly forbids
calling the reviewer, creating `review.md`, creating `verdict.json`, or marking
the phase PASS. Ralph owns Yellow-lane review routing.

## Git And Artifact Hygiene

- `git status --short`: not run. The executor prompt explicitly forbids
  `git status`; Ralph owns working-tree and staging hygiene.
- `git diff`, `git add`, `git commit`, `git push`, force push: not run.
- `git diff --cached --name-only`: not run. The executor prompt forbids
  `git diff`, and Codex staged no files.
- Staging: Codex performed no staging, so no `runs/` path, forbidden data path,
  DB/cache/log/heavy artifact, or `ACTIVE_CAMPAIGN.md` was staged by Codex.
- `git ls-files runs`: passed with empty output.
- `git ls-files '**/*.parquet' '**/*.arrow' '**/*.feather' '**/*.sqlite' '**/*.db' '**/*.dbn' '**/*.zst'`:
  passed with empty output.
- The run-local phase directory was created for local audit:
  `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P02`.
  It contains no files at handoff time.
- No value artifact, heavy artifact, local DB, provider response, secret,
  credential, raw data, canonical data, feature value, label value, or
  roll-calendar data was created in the repository.

## Validation

Commands run from the provided WSL2 worktree root:

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP` | PASS; STOP absent. |
| `git status --short` | Not run; forbidden by executor safety override in the prompt. |
| `PYTHONPATH=src python -m alpha_system.cli registry dataset-acceptance inventory --registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --config configs/data/dataset_acceptance/futsub_p02_policy.json --json` | PASS; 27 in-scope locks computed; expected matrix complete; all 27 `BLOCKED`. |
| `PYTHONPATH=src python -m alpha_system.cli data accept-datasets --registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --config configs/data/dataset_acceptance/futsub_p02_policy.json --summary-out research/futures_substrate_scaleout_v1/dataset_acceptance/acceptance_summary.md --json` | BLOCKED; exit code `2`; SQLite reported `attempt to write a readonly database`. |
| `PYTHONPATH=src python -m alpha_system.cli registry dataset-acceptance inventory --registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --config configs/data/dataset_acceptance/futsub_p02_policy.json --summary-out research/futures_substrate_scaleout_v1/dataset_acceptance/acceptance_summary.md --json` | PASS; generated read-only value-free summary. |
| `python -m pytest tests/unit/futures_substrate_scaleout/test_dataset_acceptance.py -q` | PASS; `3 passed`. |
| `python tools/verify.py --smoke` | PASS; exit code `0`; no output. |
| `python tools/verify.py --lint` | ENV-ONLY SKIP; exit code `0`; output: `ruff is not installed; run pip install -e ".[dev]" to enable lint. Skipping.` |
| `python tools/verify.py --typecheck` | PASS; exit code `0`; ran `/home/yuke_zhang/.venvs/alpha_system_research/bin/python -m compileall -q src tests tools`. |
| `python -m py_compile src/alpha_system/data/foundation/datasets.py src/alpha_system/cli/registry.py src/alpha_system/cli/data.py` | PASS; exit code `0`; no output. |
| `python tools/verify.py --test` | FAIL; exit code `1`; `4 failed, 2843 passed in 48.50s`. Failures: `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture` expected a list and received a tuple; `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture` expected a list and received a tuple; `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline` found `ohlcv_rows` empty; `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only` expected `RuntimeCacheStorageKind.RUN_ARTIFACTS` and received `RuntimeCacheStorageKind.ALPHA_DATA_ROOT`. These match the failures documented in the FUTSUB-P01 handoff and were not repaired because they are outside this phase scope. |
| `python tools/hooks/canary_runner.py` | PASS; output ended with `All Frontier canaries passed.` |
| `test -f research/futures_substrate_scaleout_v1/dataset_acceptance/acceptance_summary.md` | PASS; exit code `0`; no output. |
| `test -f docs/futures_substrate_scaleout/DATASET_ACCEPTANCE.md` | PASS; exit code `0`; no output. |
| `git ls-files runs` | PASS; exit code `0`; output empty. |
| `git ls-files '**/*.parquet' '**/*.arrow' '**/*.feather' '**/*.sqlite' '**/*.db' '**/*.dbn' '**/*.zst'` | PASS; exit code `0`; output empty. |

## Boundary Confirmation

No forbidden modules were edited. No external provider/network call, re-pull,
raw-provider read, materialized feature/label value, diagnostics run,
StudySpec lock, alpha ideation, broker/live/paper/order/deployment action, PR,
merge, review artifact, local SQLite/Parquet/heavy artifact commit candidate,
or `ACTIVE_CAMPAIGN.md` edit was performed by Codex.
