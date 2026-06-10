# LCFP-P07 Handoff

Phase: `LCFP-P07` - Parity / No-Lookahead / Guard Test Suite

Lane: `YELLOW`

## Status

code_status: implemented

parity_status: consolidated synthetic parity, no-lookahead, and guard checks
pass locally in the research venv with Polars installed. This is not a
benchmark result and does not claim fast-label-path acceptance for production
materialization.

Ralph owns staging, commit, review routing, verdict parsing, PR, CI, merge
gate, merge, and done-check. Codex left changes unstaged.

## Files Changed

Commit-eligible changed files:

- `README.md`
- `docs/label_compute_fast_path/OVERVIEW.md`
- `docs/label_compute_fast_path/README.md`
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P07.md`
- `research/label_compute_fast_path_v1/README.md`
- `research/label_compute_fast_path_v1/parity/parity_report.md`
- `tests/no_lookahead/label_fast_path/__init__.py`
- `tests/no_lookahead/label_fast_path/test_fast_label_available_ts.py`
- `tests/unit/feature_compute_fast_path/parity_harness.py`
- `tests/unit/label_compute_fast_path/test_parity_matrix_suite.py`

No run-local `handoff.md`, `review.md`, or `verdict.json` was created.

## Implementation Summary

- Extended the existing parity harness with `LabelParityStats` and
  `assert_and_summarize_label_records_match(...)`. The original assertion
  behavior remains intact; the new helper adds value-free record counts,
  null/flag counts, and numeric diff summaries.
- Added the campaign-level P07 parity matrix suite covering fixed/extended
  horizons, session-close, maintenance-flat, cost-adjusted labels, and path
  labels using the P03/P04/P05 synthetic fixtures.
- Added direct roll-policy terminal-disposition parity against
  `evaluate_roll_guard(...)` for DROP/TRUNCATE/FLAG/INVALID.
- Added fast-label no-lookahead tests under the new allowed subtree
  `tests/no_lookahead/label_fast_path/`.
- Added `parity_report.md` with value-free family-by-dimension coverage,
  case counts, tolerances, optional-dependency behavior, and residual-gap
  status.

## Parity Matrix Summary

Local value-free aggregate counts from the P07 matrix:

| Family | Labels | Compared records | Null records | Flagged records | Max abs diff | Max median abs diff |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fixed_horizon | 14 | 8074 | 36 | 36 | 0 | 0 |
| session_maintenance | 2 | 6 | 0 | 0 | 0 | 0 |
| cost_adjusted | 2 | 10 | 6 | 6 | 0 | 0 |
| path | 4 | 52 | 6 | 22 | 0 | 0 |

Required dimensions covered:

- value parity;
- exact `label_available_ts`;
- exact `horizon_end_ts`;
- exact `label_spec_id` and `label_version_id`;
- exact quality flags;
- roll-crossing guard cases, including policy modes;
- maintenance-crossing guard cases;
- session-gap/no-trade cases;
- BBO missingness cases;
- same-bar path barrier policy variants;
- barrier-never-touched timeout;
- fixed-horizon `HorizonOverlapMetadata` preservation.

## Tolerances

- Fixed-horizon and session/maintenance labels: exact value parity.
- Cost-adjusted labels: `abs=1e-12, rel=1e-12`. Justification: the reference
  path computes from `Decimal` BBO input-view rows while the fast path consumes
  a float shared panel before applying the sanctioned cost primitives. Observed
  max and median abs diff in the P07 synthetic suite are both 0.
- Path labels: `abs=1e-12, rel=1e-12`. Justification: the reference path family
  computes from `Decimal` OHLCV input-view rows while the fast path consumes a
  float shared panel. Boolean barrier outputs, timestamps, identity, event
  sets, quality flags, and guard dispositions remain exact. Observed max and
  median abs diff in the P07 synthetic suite are both 0.

No tolerance was added to hide a known divergence.

## Fast-Path Defects

No fast-path source defect was found by the consolidated suite. No files under
`src/alpha_system/labels/fast/**` were changed in this phase.

## Optional Dependency Behavior

The consolidated fast-label tests use `pytest.importorskip("polars")` because
the fast label materializer uses the optional Polars dependency. In this
research venv Polars is installed, so the tests executed real synthetic parity
checks. In environments without Polars, the tests skip visibly rather than
falling back to a weakened assertion path.

## Validation

- `git status --short`
  - Not run. The executor prompt explicitly forbids `git status`; Ralph owns
    git state inspection.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/test_parity_matrix_suite.py tests/no_lookahead/label_fast_path/ -q`
  - First run failed: `1 failed, 10 passed` due to a test-loop unpacking bug in
    the new no-lookahead test. Fixed in
    `tests/no_lookahead/label_fast_path/test_fast_label_available_ts.py`.
  - Final rerun passed: `11 passed in 2.41s`.
- `python -m compileall -q tests/no_lookahead/label_fast_path tests/unit/label_compute_fast_path/test_parity_matrix_suite.py tests/unit/feature_compute_fast_path/parity_harness.py`
  - PASS, exit 0.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/ -q`
  - PASS, `37 passed in 2.85s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/feature_compute_fast_path/test_fixed_horizon_label_pack.py -q`
  - PASS, `4 passed in 1.69s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/no_lookahead/label_fast_path/ -q`
  - PASS, `2 passed in 0.84s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`
  - PASS, `12 passed in 0.15s`.
- `/home/yuke_zhang/.venvs/alpha_system_research/bin/python tools/verify.py --smoke`
  - PASS, exit 0 with no output.
- `test -f research/label_compute_fast_path_v1/parity/parity_report.md`
  - PASS, exit 0.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/test_fast_path_artifact_policy.py -q`
  - PASS, `2 passed in 0.29s`.
- `git ls-files runs`
  - PASS, returned empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite'`
  - PASS, returned empty output.

Additional value-free stats helper:

- Imported the new P07 matrix helpers in a read-only Python snippet to compute
  the aggregate counts recorded in `parity_report.md`. No label values were
  written.

## Artifact / Boundary Notes

- No `runs/**` path was created or modified by Codex in this phase.
- The prompt named
  `runs/2026-06-10T102615Z_LABEL_COMPUTE_FAST_PATH_V1/phases/LCFP-P07`, but
  that run artifact directory was not present in this worktree.
- STOP checks before execution/validation/handoff reported clear.
- No `git add`, `git commit`, `git push`, `git diff`, reviewer call, PR
  creation, merge, `review.md`, or `verdict.json` was performed by Codex.
- No reference-engine, roll-guard, availability-policy, registry, store, CLI,
  broker/live/order, cost-accounting, or existing `tests/no_lookahead/**`
  outside `label_fast_path/` files were edited.
