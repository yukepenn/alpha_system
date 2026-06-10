# LCFP-P04 Handoff

Phase: `LCFP-P04` - Fast Session / Maintenance / Cost Labels

Lane: `YELLOW`

## Status

code_status: implemented

parity_status: synthetic parity checks pass for session-close,
maintenance-flat, cost-adjusted forward return, and spread-adjusted forward
return. This is not a benchmark result and does not claim fast-label-path
acceptance for production materialization.

Ralph owns staging, commit, review routing, verdict parsing, PR, CI, merge
gate, merge, and done-check. Codex left changes unstaged.

## Implemented

- Added `src/alpha_system/labels/fast/session_maintenance.py` with the governed
  `build_session_maintenance_label_pack(...)` surface for `session_close` and
  `maintenance_flat`.
- Added `src/alpha_system/labels/fast/cost_adjusted.py` with the governed
  `build_cost_adjusted_label_pack(...)` surface for `cost_adjusted_fwd_ret`
  and `spread_adjusted_fwd_ret`.
- Extended `FastLabelMaterializer` to admit fixed-family close-out definitions
  and cost-adjusted definitions while preserving reference-derived
  `label_version_id`s.
- Close-out labels reuse the LCFP-P02 shared panel and terminal-index model for
  session and maintenance terminals.
- Cost-adjusted labels compute exact BBO-horizon records from the shared panel
  and apply `alpha_system.backtest.costs` primitives read-only:
  `CostInput`, `SpreadCost`, and `BpsCost`.
- Added synthetic parity fixtures/tests covering normal rows, roll-drop rows,
  session-gap rows, a maintenance-crossing cost window, terminal BBO gaps, and
  entry BBO missingness.
- Added durable docs and value-free parity evidence.

## Files Changed

Commit-eligible changed files:

- `README.md`
- `docs/label_compute_fast_path/OVERVIEW.md`
- `docs/label_compute_fast_path/README.md`
- `docs/label_compute_fast_path/SESSION_MAINTENANCE_COST_PACKS.md`
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P04.md`
- `research/label_compute_fast_path_v1/README.md`
- `research/label_compute_fast_path_v1/parity/LCFP-P04.md`
- `src/alpha_system/labels/fast/__init__.py`
- `src/alpha_system/labels/fast/cost_adjusted.py`
- `src/alpha_system/labels/fast/materializer.py`
- `src/alpha_system/labels/fast/session_maintenance.py`
- `tests/fixtures/label_compute_fast_path/session_cost_labels.py`
- `tests/unit/label_compute_fast_path/test_session_maintenance_cost_pack.py`

No run-local `handoff.md`, `review.md`, or `verdict.json` was created.

## Parity Coverage

- `session_close`: normal retained rows, post-session no-terminal rows, and
  roll-crossing rows dropped by the shared roll guard.
- `maintenance_flat`: normal retained maintenance-boundary rows and
  roll-crossing rows dropped by the shared roll guard.
- `spread_adjusted_fwd_ret` / `cost_adjusted_fwd_ret`: normal BBO rows,
  terminal BBO missingness, entry BBO missingness, and a window crossing the
  daily maintenance break. The fast behavior matches the reference
  cost-adjusted family for the crossing case.
- Exact parity asserted for `label_available_ts`, `label_spec_id`,
  `label_version_id`, event sets, and quality flags.

Documented tolerance:

- Cost-adjusted value comparison uses `abs=1e-12, rel=1e-12` because the
  reference path computes from `Decimal` input-view rows while the fast path
  consumes a Polars float panel before reconstructing Decimal cost inputs for
  the sanctioned `backtest.costs` primitives. Timestamp, identity, event-set,
  and flag parity remain exact.

## Cost Truth Boundary

`src/alpha_system/backtest/costs.py` was consumed read-only and not edited.
The fast cost branch does not duplicate cost arithmetic; it delegates spread
and bps cost calculations to `SpreadCost`, `BpsCost`, and `CostInput`.
BBO spread remains a proxy input only; no execution-quality claim is made.

## Validation

- `git status --short`
  - Not run. The executor prompt explicitly forbids `git status`; Ralph owns
    git state inspection.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m compileall -q src/alpha_system/labels/fast tests/unit/label_compute_fast_path tests/fixtures/label_compute_fast_path`
  - PASS, exit 0.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/test_session_maintenance_cost_pack.py -q`
  - PASS, `3 passed in 0.33s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/ -q`
  - PASS, `15 passed in 0.69s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/feature_compute_fast_path/test_fixed_horizon_label_pack.py -q`
  - PASS, `4 passed in 1.66s`.
- `/home/yuke_zhang/.venvs/alpha_system_research/bin/python tools/verify.py --smoke`
  - PASS, exit 0.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`
  - PASS, `12 passed in 0.15s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/test_fast_path_artifact_policy.py -q`
  - PASS, `2 passed in 0.27s`.
- `git ls-files runs`
  - PASS, returned empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite'`
  - PASS, returned empty output.
- `git ls-files --modified --others --exclude-standard`
  - Used as the changed-file inventory because `git status` is forbidden.
  - Reported only the commit-eligible files listed above.

No `git add`, `git commit`, `git push`, `git diff`, reviewer call, PR creation,
merge, `review.md`, or `verdict.json` was performed by Codex.

## Additive Extension Points

- P06 can consume the new pack builders through `alpha_system.labels.fast`.
- The materializer now dispatches fast supported definitions by family while
  preserving the existing fixed-minute behavior and metadata fields used by P03.
- P05 path-label work remains separate; no path-label kernels or tests were
  added here.

## Residual Risks

- The cost-adjusted fast path supports the existing `backtest.costs` half-spread
  and full-spread profiles. A governed `custom_fraction` cost-model contract
  would fail closed until a sanctioned cost primitive exists for that profile.
- Cost-adjusted roll/maintenance behavior intentionally follows the reference
  `cost_adjusted` family. The added maintenance-crossing fixture documents that
  retained-record behavior rather than imposing fixed-horizon roll/maintenance
  drops on the cost family.
