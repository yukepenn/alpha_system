# RT-P21 Handoff - Small Real FLF DatasetVersion Runtime Smoke

## Scope Completed

- Added `src/alpha_system/runtime/smoke.py`, a local-only smoke driver that resolves an accepted local DatasetVersion, Feature/Label handles, Tier 0 diagnostics, `double_cost` cost stress, no-lookahead audit, `EvidenceDraft`, `RuntimeToolResult`, and `RuntimeRunSummary`.
- Added `tests/integration/runtime/test_smoke.py` for CI-safe absent-data behavior and a dependency-injected resolved-input smoke path.
- Added `docs/research_runtime/REAL_SMOKE.md` with the exact operator command and warning behavior.
- Updated `README.md` with the RT-P21 snapshot and unchanged safety boundaries.

## Files For Ralph To Stage Explicitly

- `src/alpha_system/runtime/smoke.py`
- `tests/integration/runtime/test_smoke.py`
- `docs/research_runtime/REAL_SMOKE.md`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P21.md`

No files were staged by Codex. `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P21/**` is reviewer-owned and was not created.

## Git Status

`git status --short`: skipped. The executor prompt explicitly forbids Codex from running `git status`.

`git diff --cached --name-only`: skipped. The executor prompt forbids `git diff`; Codex also performed no staging.

## Validation And Execution

- `test -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP && printf 'STOP present\n' || printf 'STOP absent\n'` -> pass, output `STOP absent`.
- `python -m py_compile src/alpha_system/runtime/smoke.py` -> pass.
- `python -c "import alpha_system.runtime.smoke"` -> fail in this shell: `ModuleNotFoundError: No module named 'alpha_system'`. The repository uses `src` layout and the bare shell does not have `src` on `PYTHONPATH`.
- `PYTHONPATH=src python -c "import alpha_system.runtime.smoke"` -> pass.
- `python tools/verify.py --smoke` -> pass.
- `python -m pytest tests/integration/runtime/test_smoke.py -q` -> initial failure on missing explicit `StudySpec.locked_test_policy` string metadata; repaired and re-run passed.
- `python -m pytest tests/integration/runtime -q` -> pass, `3 passed`.
- `test -f docs/research_runtime/REAL_SMOKE.md` -> pass.
- `PYTHONPATH=src python -m alpha_system.runtime.smoke` -> pass with runtime output status `PASS_WITH_WARNINGS`; local real smoke did not run because `ALPHA_DATA_ROOT` is not set in this runner.

Broader `python tools/verify.py --all` and `python tools/hooks/canary_runner.py` were not run because this phase added a scoped orchestration module, tests, and docs, and did not edit shared primitive behavior.

## Artifact Audit

- `git ls-files runs` -> pass, no output.
- `find data -type f ! -name README.md ! -name .gitkeep -print` -> pass, no output.
- `find artifacts -type f -size +1M -print` -> pass, no output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` -> pass, no output.
- `git ls-files | grep -E '\.(sqlite|sqlite3|db|db-journal|wal|parquet|arrow|feather|dbn|zst|pkl|pickle|joblib|onnx|npy|npz|log)$' | grep -v '^tests/fixtures/' || echo "no committed heavy/db/log artifacts"` -> pass, output `no committed heavy/db/log artifacts`.

No `runs/**` path, raw/canonical/feature/label/runtime values, provider response, DB, cache, log, or heavy artifact was intentionally created as a commit-eligible output.

## Smoke Outcome

This runner recorded a truthful `PASS_WITH_WARNINGS`: `ALPHA_DATA_ROOT` is not set, so no local accepted DatasetVersion registry or Feature/Label handles were available. The smoke CLI exited successfully and reported the exact operator command:

```bash
ALPHA_DATA_ROOT=/abs/local/alpha_data ALPHA_DATASET_VERSION_ID=dsv_... ALPHA_FEATURE_PACK_REFS=fver_... ALPHA_LABEL_PACK_REFS=lver_... python -m alpha_system.runtime.smoke
```

The integration test also exercises the resolved path with dependency-injected local DatasetVersion and Feature/Label handles, proving the orchestration reaches `EVIDENCE_DRAFT_READY`, includes `double_cost`, and emits value-free tool/run summaries without provider imports or raw/heavy data references.

## Caveats

- The bare import command from the generated spec is environment-dependent in this `src` layout; it passes when `src` is on `PYTHONPATH`, as pytest and the supplemental import check demonstrate.
- Codex did not call Claude, did not run reviewer, did not create review artifacts, did not create a verdict, did not create a PR, did not merge, and did not mark the phase PASS.
