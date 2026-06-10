# LCFP-P02 Handoff

## Status

- `code_status`: implemented
- `fast_label_path_v1_status`: shared contract only; no benchmark or performance
  claim
- `execute_status`: not applicable; this phase writes no label values
- `registry_status`: no registry writes
- `artifact_status`: value-free code/docs/tests only; no tracked `runs/`,
  Parquet, or SQLite artifacts found by the requested audits

The run-local artifact directory named in the executor prompt was not present in
this worktree when checked. No run-local `handoff.md`, `review.md`, or
`verdict.json` was created.

## Built

LCFP-P02 adds the shared contract substrate in `alpha_system.labels.fast`:

- `build_shared_label_panel(...)` builds one immutable wide
  `SharedLabelPanel` per symbol-year from OHLCV plus optional BBO rows. Rows
  carry trade price, high/low, BBO proxy columns, BBO presence/missingness
  flags, spread/cost inputs, session segment ids, an ex-ante analytic roll
  calendar, and maintenance windows.
- `TerminalRequest`, `TerminalKind`, `resolve_terminal_indices(...)`, and
  `TerminalIndexModel` compute terminal indices once per panel for
  fixed-horizon, session-close, maintenance-flat, and roll-truncation terminals.
- `TerminalResolution` records source index, retained terminal index when any,
  requested/effective terminal timestamps, `drop` / `truncate` / `flag` /
  `invalid` disposition, guard reason, roll policy, and value-free quality
  flags.
- Roll semantics call the existing `evaluate_roll_guard(...)` using the
  ex-ante calendar and default `RollCrossPolicy.DROP`. Maintenance crossing is
  evaluated before roll crossing, matching the reference fixed-horizon family.
- `derive_label_available_ts(...)` mirrors the governed
  `LabelAvailabilityPolicy` derivation by family. Fixed-horizon tests compare
  it directly against the reference family.
- `quality_metadata_for_resolution(...)` standardizes gap and quality flags:
  `insufficient_window`, `input_gap`, `session_reset`,
  `maintenance_crossing`, and BBO gap/missingness flags.

The public P03/P04/P05 consumption surface is:

- `SharedLabelPanel` / `SharedLabelPanelRow`
- `build_shared_label_panel(...)`
- `TerminalKind`, `TerminalRequest`, `TerminalIndexModel`,
  `TerminalResolution`, `TerminalGuardDisposition`
- `resolve_terminal_indices(...)`
- `LabelAvailabilityFamily`, `derive_label_available_ts(...)`
- `LabelQualityMetadata`, `quality_metadata_for_resolution(...)`

This phase does not compute family pack values and does not derive or mutate
`label_version_id`.

## Files Created Or Modified

- `README.md`
- `docs/label_compute_fast_path/OVERVIEW.md`
- `docs/label_compute_fast_path/PANEL_TERMINAL_CONTRACT.md`
- `docs/label_compute_fast_path/README.md`
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P02.md`
- `src/alpha_system/labels/fast/__init__.py`
- `src/alpha_system/labels/fast/panel.py`
- `tests/fixtures/label_compute_fast_path/synthetic_panel.py`
- `tests/unit/label_compute_fast_path/test_shared_label_panel_contract.py`

## Validation

- `git status --short`: not run. The executor prompt explicitly forbids
  `git status`; the Ralph driver owns git state inspection.
- `PYTHONPATH=src python tools/verify.py --smoke`: PASS, exit 0.
- `PYTHONPATH=src python -m pytest tests/unit/label_compute_fast_path/ -q`:
  PASS, `9 passed in 0.12s`.
- `PYTHONPATH=src python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`:
  PASS, `12 passed in 0.16s`.
- `PYTHONPATH=src python -m pytest tests/unit/test_fast_path_artifact_policy.py -q`:
  PASS, `2 passed in 0.21s`.
- `git ls-files runs`: PASS, returned empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite'`: PASS, returned empty output.

No `git add`, `git commit`, `git push`, `git diff`, reviewer call, PR creation,
merge, `review.md`, or `verdict.json` was performed by the executor.

## Residuals

- The known pre-existing
  `tests/unit/feature_compute_fast_path/test_fixed_horizon_label_pack.py` RED
  with Polars installed remains P03 scope. This phase did not edit or repair
  that test.
- The new contract is value-free. Family-specific value producers remain P03
  fixed/extended horizons, P04 session/maintenance/cost, and P05 path labels.
- Roll truncation retains a terminal only when the existing roll guard returns
  `truncate` and the panel has an exact same-contract row at the effective roll
  boundary timestamp. Otherwise the resolution fails closed as an insufficient
  terminal window.
