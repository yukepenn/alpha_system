# P090500_PACK_OVERWRITE_GUARD Handoff

Branch: `wf1/pack-overwrite-guard`

Commit: this commit (`P090500 guard registered feature pack rewrites`)

## Scope Completed

- Added registry-aware feature pack integrity helpers in
  `src/alpha_system/features/pack_integrity.py`.
- Added read-only `FeatureRegistry` APIs to list REGISTERED Parquet-backed
  feature rows and resolve REGISTERED rows by normalized `parquet_path`.
- Added fail-closed pre-write superset checks before feature Parquet
  replacement. No `--allow-shrink` or equivalent escape hatch was added.
- Added post-registration reconciliation that reloads the Parquet bytes,
  verifies every REGISTERED fver for the path exists on disk, and verifies each
  registry `value_content_hash` matches the actual file content hash.
- Added read-only `alpha scaleout pack-audit` / `run_pack_audit` reporting
  `clean`, `stale-registry`, and `benign-extra` classes with counts and ids only.
- Added synthetic tests for subset refusal, superset write allowance, tamper
  reconciliation failure, and pack-audit classification/CLI JSON output.

## Write Sites Guarded

- `src/alpha_system/features/fast/materializer.py::_write_records`
  - Guards the fast feature pack `values.parquet` writer before
    `write_parquet_values(...)` can replace an existing pack file.
- `src/alpha_system/features/engine/materialization.py::_write_records_idempotently`
  - Guards the reference feature Parquet writer before
    `write_parquet_values(...)` can replace any registered feature path.
- `src/alpha_system/features/fast/materializer.py::PackMaterializer.register_pack`
  - Reconciles registered fvers for the written path after normal fast-pack
    registration.
- `src/alpha_system/features/scaleout/driver.py::_materialize_unit_per_feature`
  - Reconciles after reference/per-feature scaleout materialization and
    registration.
- `src/alpha_system/features/scaleout/driver.py::_register_v1_worker_output`
  - Reconciles after the serial V1 worker-output registration path, including
    existing-record refreshes and fresh declarations. Intermediate one-feature
    fresh registrations skip the materializer-level reconciliation and rely on
    the final unit-level reconciliation after the whole registered path is
    updated.

Label writers were not changed: this phase contract is feature-registry/fver
specific and the incident path is feature pack materialization.

## Files Changed

- `specs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P090500_PACK_OVERWRITE_GUARD-registry-aware-write-once.md`
- `src/alpha_system/cli/scaleout.py`
- `src/alpha_system/features/engine/materialization.py`
- `src/alpha_system/features/fast/materializer.py`
- `src/alpha_system/features/pack_integrity.py`
- `src/alpha_system/features/registry.py`
- `src/alpha_system/features/scaleout/driver.py`
- `tests/unit/features/test_pack_overwrite_guard.py`
- `handoffs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P090500_PACK_OVERWRITE_GUARD.md`

## Validation Run

- `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features/test_pack_overwrite_guard.py -q`
  - PASS: `3 passed`
- `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout tests/unit/features -q`
  - PASS: `281 passed`
- `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python tools/verify.py --smoke`
  - PASS
- `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python tools/hooks/canary_runner.py`
  - PASS: all Frontier canaries passed
- `PYTHONPATH=$PWD/src PATH=$HOME/.venvs/alpha_system_ci/bin:$PATH just ci-parity`
  - PASS: `3304 passed, 78 skipped`
- `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python tools/verify.py --artifacts`
  - PASS
- `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python tools/verify.py --boundaries`
  - PASS
- `git ls-files runs`
  - PASS: empty
- Forbidden local artifact scan for `*.sqlite`, `*.db`, `*.parquet`, `*.arrow`,
  `*.feather`, and `*.log`
  - PASS: empty

## Non-Passing / Caveats

- `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python tools/verify.py --all`
  failed after `3383 passed, 1 skipped` on two pre-existing integration
  assertions in the research venv:
  - `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`
  - `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`
- Both failures are tuple-vs-list equality assertions when optional
  `duckdb`/`polars` dependencies are available in the research venv. The same
  integration tests pass under the requested CI parity venv.
- `ruff` is not installed in either `~/.venvs/alpha_system_research` or
  `~/.venvs/alpha_system_ci`; no ruff lint run was available.

## Risks / Caveats

- `pack-audit` computes hashes from Parquet row payloads and reports ids/counts
  only; it does not print values.
- The feature registry path comparison normalizes paths before equality checks.
- Deprecated feature rows are intentionally ignored by the guard and audit.

## Review Request Focus

- Confirm the guarded write-site list covers the feature-side paths that can
  replace a registered `parquet_path`.
- Confirm final V1 scaleout reconciliation happens after all existing/fresh
  registry updates, not mid-refresh.
- Confirm `pack-audit` status semantics match repair needs:
  `stale-registry` for missing registered ids or hash mismatch,
  `benign-extra` for unregistered ids present on disk with registered hashes
  matching, and `clean` for exact match.

## Next Recommended Step

Fresh adversarial review for this Yellow phase, then run
`alpha scaleout pack-audit --alpha-data-root <root> --json` after any repair
re-materialization before declaring the damaged pack paths complete.
