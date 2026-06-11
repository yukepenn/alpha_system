# FUTSUB-P24 Handoff

Phase: `FUTSUB-P24` - Purged / Embargo Walk-Forward Runtime Wiring  
Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Date: 2026-06-11  
Executor: Codex

## Scope Completed

- Added `runtime/diagnostics/splits/walk_forward.py`, a thin runtime callable
  path over `alpha_system.experiments.splits.walk_forward_splits`,
  `apply_purge_embargo`, and `assert_chronological_split`.
- Added bounded, overridable `STRUCTURAL` / `MEDIUM` / `FAST` protocol metadata
  through `DiagnosticsHalfLifeProtocol` and `WalkForwardSplitConfig`.
- Wired opt-in `walk_forward_config` into factor diagnostics. Existing callers
  that omit the config keep the prior behavior; requested split failures become
  visible `walk_forward_split_unavailable` inconclusive reports with no unsplit
  fallback.
- Exposed value-free per-fold metadata using canonical `SplitWindow.to_dict()`
  shape for downstream P25 / Validation Governance consumption.
- Added focused tests for canonical fold metadata, fail-closed too-small input,
  factor-runtime metadata, and factor-runtime inconclusive state.
- Added value-free P24 documentation and wiring smoke evidence.

`src/alpha_system/experiments/splits.py` was consumed, not edited.

## Explicit Non-Scope

No N_eff engine, DSR, PBO, PSR, multiple-testing correction, contamination
ledger, portfolio-level walk-forward, alpha ideation, promotion logic,
profitability/tradability claim, broker path, paper/live path, production
deployment, review artifact, verdict artifact, PR, merge, staging, or commit was
created by the executor.

## Files For Ralph To Stage

- `README.md`
- `docs/futures_substrate_scaleout/README.md`
- `docs/futures_substrate_scaleout/WALK_FORWARD_WIRING.md`
- `research/futures_substrate_scaleout_v1/wiring/walk_forward_wiring_smoke.md`
- `src/alpha_system/runtime/diagnostics/__init__.py`
- `src/alpha_system/runtime/diagnostics/contracts.py`
- `src/alpha_system/runtime/diagnostics/factor/runtime.py`
- `src/alpha_system/runtime/diagnostics/splits/__init__.py`
- `src/alpha_system/runtime/diagnostics/splits/walk_forward.py`
- `tests/unit/runtime/diagnostics/test_contracts.py`
- `tests/unit/futures_substrate_scaleout/test_walk_forward_wiring.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P24.md`

No `runs/` path should be staged.

## Validation

| Command | Outcome |
| --- | --- |
| `python -m pytest tests/unit/futures_substrate_scaleout/test_walk_forward_wiring.py -q` | PASS, `4 passed` |
| `PYTHONPATH=src python -m pytest tests/unit/runtime/diagnostics/test_contracts.py tests/unit/runtime/diagnostics/factor/test_factor_runtime.py tests/unit/runtime/diagnostics/splits/test_splits.py tests/unit/futures_substrate_scaleout/test_walk_forward_wiring.py -q` | PASS, `24 passed` |
| `PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system python tools/verify.py --smoke` | PASS, exit 0, no output |
| `PYTHONPATH=src python tools/hooks/canary_runner.py` | PASS, all Frontier canaries passed |
| `env -u ALPHA_DATA_ROOT PYTHONPATH=src python tools/verify.py --all` | PASS, `3080 passed, 73 skipped`; status doctor reported WARN because no run-local `state.json` exists in this worktree |
| `PYTHONPATH=src ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system python tools/verify.py --all` | FAIL as known ambient-env case: `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only` expects run-artifact storage for the explicit run-root case, but exported `ALPHA_DATA_ROOT` redirects the cache policy to `alpha_data_root`; suite otherwise reached `3079 passed, 73 skipped` and canaries passed |
| `PYTHONPATH=src python tools/verify.py --lint` | FAIL repo-wide on pre-existing formatting/lint backlog outside P24 scope (`1579 errors`) |
| `python -m ruff format --check <P24 Python paths>` | PASS, `7 files already formatted` |
| `python -m ruff check <P24 Python paths>` | PASS, `All checks passed!` |
| `for path in README.md docs/futures_substrate_scaleout/README.md docs/futures_substrate_scaleout/WALK_FORWARD_WIRING.md research/futures_substrate_scaleout_v1/wiring/walk_forward_wiring_smoke.md src/alpha_system/runtime/diagnostics/splits/walk_forward.py tests/unit/futures_substrate_scaleout/test_walk_forward_wiring.py handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P24.md; do test -f "$path" || exit 1; done` | PASS, exit 0, no output |
| `find . ... <heavy/local artifact suffixes> -print` excluding `.git`, caches, and `__pycache__` | PASS, empty output |
| `find reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1 -maxdepth 2 -type f -name '*FUTSUB-P24*' -print` | PASS, empty output |
| `test ! -e runs` | PASS, exit 0, no output |

## Repair Attempt

Bounded repair for review findings B1/B2:

- Moved the commit-eligible handoff to the campaign-declared path:
  `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P24.md`.
- Moved the focused wiring test to the campaign-declared check path:
  `tests/unit/futures_substrate_scaleout/test_walk_forward_wiring.py`.
- Updated the README snapshot, smoke report pointer, staged-file list,
  validation table, and file-existence check to remove the stale flat handoff
  and runtime-test paths.

Repair validation rerun on 2026-06-11:

| Command | Outcome |
| --- | --- |
| `python -m pytest tests/unit/futures_substrate_scaleout/test_walk_forward_wiring.py -q` | PASS, `4 passed` |
| `PYTHONPATH=src python -m pytest tests/unit/runtime/diagnostics/test_contracts.py tests/unit/runtime/diagnostics/factor/test_factor_runtime.py tests/unit/runtime/diagnostics/splits/test_splits.py tests/unit/futures_substrate_scaleout/test_walk_forward_wiring.py -q` | PASS, `24 passed` |
| `python tools/verify.py --smoke` | PASS, exit 0, no output |
| `test -f research/futures_substrate_scaleout_v1/wiring/walk_forward_wiring_smoke.md` | PASS, exit 0, no output |
| `git ls-files runs` | PASS, empty output |
| `python tools/hooks/canary_runner.py` | PASS, all Frontier canaries passed |

## Artifact Policy Confirmation

- No `runs/` directory was present in this worktree at execution time, so the
  prompt-provided run-local spec / STOP directory could not be read.
- No run-local `handoff.md`, `review.md`, `verdict.json`, `checks.json`, or
  repair-attempt artifact was created.
- No feature value, label value, raw/canonical data, provider payload, Parquet,
  Arrow, Feather, SQLite/DB, DBN/ZST, model artifact, cache, log, secret, or
  local data artifact was created.
- The initial executor left changes unstaged for Ralph. This bounded repair ran
  read-only git inspection commands only and did not run `git add`, `git commit`,
  or `git push`.

## Review Notes

Yellow-lane review remains Ralph-owned. The executor did not call Claude, run a
reviewer, create `review.md`, create `verdict.json`, create a PR, merge, or mark
the phase PASS.
