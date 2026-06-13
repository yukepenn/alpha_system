# SHIP_REFIT-P03 Executor Handoff

## Scope Delivered

- Added pure-Python IC power reporting in
  `src/alpha_system/runtime/diagnostics/power.py`:
  `SE(IC) ~= 1 / sqrt(N_eff - 1)` and
  `MDE(|IC|) = z_multiple * SE(IC)` with default `z = 1.96`.
- Attached additive detection-power blocks to
  `src/alpha_system/governance/detection_statistic.py` and surrogate
  `gate_outcome` serialization without changing the detection threshold,
  detection decision, surrogate-FDR zero-pass criterion, constant-factor
  exclusion, or seed mapping.
- Extended `DiagnosticsReport` with an optional value-free
  `power_statement` block and surfaced stacked plus per-declared-factor power
  reporting in factor diagnostics.
- Updated `src/alpha_system/runtime/diagnostics/splits/n_eff.py` so
  purge/embargo gaps reduce rows before the overlap discount while preserving
  `n_eff <= rows`, `rows_are_not_independent_samples`, and
  `statistical_validity_claim: False`.
- Added focused tests for MDE/SE math, edge cases, monotonicity, purge/embargo
  N_eff reduction, DETECTED/NOT_DETECTED power surfaces, per-factor reporting,
  and diagnostics report serialization.
- Recorded the value-free A-vs-B settler result in
  `research/ship_refit_v1/SHIP_REFIT-P03_SETTLER_NULL.md` and updated the
  compact README snapshot.

## Settler Result Of Record

Coordinator settler, 2026-06-13: A-vs-B conditional re-score returned NULL.
Conditional uplift collapsed to approximately `1e-6` at full power across the
substrate-scale observation range (`39M` to `66M` observations), cross-validated
byte-exact against `research/regimes.py`.

Bounded consequence: P03 stayed scoped to MDE/power/N_eff rigor. No
interaction/gating detector was added. The distinct stacking-blindness lesson is
addressed only by reporting power per declared factor in addition to the stacked
aggregate.

## Validation

- `PYTHONPATH=src python -m pytest tests -k "n_eff or mde or power or detection or split" -q`
  - Passed: `50 passed, 2 skipped, 3369 deselected`.
- `python -c "import importlib,sys; [sys.exit('numpy/pandas/polars must NOT be present') for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]"`
  - Passed: no output.
- `python tools/hooks/canary_runner.py`
  - Passed: all Frontier canaries passed, including `planted_fake_alpha`,
    `true_alpha_detection_detect_strong`, and `true_alpha_detection_no_detect_weak`.
- `python tools/verify.py --smoke`
  - Passed: no output.
- `python tools/verify.py --all`
  - Initial executor environment run failed one known environment-sensitive test:
    `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`
    saw exported `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system` and
    selected `RuntimeCacheStorageKind.ALPHA_DATA_ROOT` instead of the default
    run-artifact cache root.
  - Clean-shell rerun command: `env -u ALPHA_DATA_ROOT python tools/verify.py --all`.
  - Passed: `3341 passed, 80 skipped`.
  - Status doctor emitted WARN only because this worktree has no live
    `state.json` run dir for `SHIP_REFIT_V1`; runtime contract was consistent.
- `git ls-files runs`
  - Passed: empty output.
- Final forbidden suffix scan for `*.parquet`, `*.arrow`, `*.feather`,
  `*.sqlite`, `*.db`, `*.dbn`, and `*.zst`
  - Passed: empty output.

## Artifact And Safety Notes

- No `git add`, `git commit`, `git push`, `git status`, or `git diff` command was
  run by the executor. Changes are left unstaged for Ralph.
- No `runs/` path was staged or committed by the executor; `git ls-files runs`
  returned empty.
- The prompt-named run-local phase directory
  `runs/2026-06-13T174822Z_SHIP_REFIT_V1/phases/SHIP_REFIT-P03` was not present
  in this worktree. No run-local handoff, `review.md`, or `verdict.json` was
  created.
- No live trading, paper trading, broker operation, order routing, deployment,
  PR creation, merge, reviewer call, or Claude call was performed.
- No numpy, pandas, or polars dependency was introduced.

## Commit-Eligible Paths Touched

- `README.md`
- `src/alpha_system/governance/detection_statistic.py`
- `src/alpha_system/governance/surrogate_run.py`
- `src/alpha_system/runtime/diagnostics/factor/runtime.py`
- `src/alpha_system/runtime/diagnostics/power.py`
- `src/alpha_system/runtime/diagnostics/report.py`
- `src/alpha_system/runtime/diagnostics/splits/n_eff.py`
- `tests/unit/governance/test_detection_power.py`
- `tests/unit/governance/test_surrogate_run.py`
- `tests/unit/futures_substrate_scaleout/test_n_eff_reporting.py`
- `tests/unit/runtime/diagnostics/factor/test_factor_runtime.py`
- `tests/unit/runtime/diagnostics/test_power.py`
- `tests/unit/runtime/diagnostics/test_report.py`
- `research/ship_refit_v1/SHIP_REFIT-P03_SETTLER_NULL.md`
- `handoffs/SHIP_REFIT_V1/SHIP_REFIT-P03.md`
