# LCFP-P05 Handoff

Phase: `LCFP-P05` - Fast Path Labels (MFE/MAE/Target-Before-Stop/Triple-Barrier)

Lane: `YELLOW`

## Status

code_status: implemented

parity_status: synthetic parity checks pass for MFE, MAE,
target-before-stop, and triple-barrier path labels on the kernelized P02
guarded-panel scan cases. This is not a benchmark result and does not claim
fast-label-path acceptance for production materialization.

Ralph owns staging, commit, review routing, verdict parsing, PR, CI, merge
gate, merge, and done-check. Codex left changes unstaged.

## Implemented

- Added `src/alpha_system/labels/fast/path.py` with the governed
  `build_path_label_pack(...)` surface for `mfe`, `mae`,
  `target_before_stop`, and `triple_barrier`.
- Extended `FastLabelMaterializer` to admit path definitions while preserving
  reference-derived `label_version_id`s.
- Added P02 terminal-model dispatch for path labels. The pack uses a guarded
  fixed-horizon terminal whose minutes equal governed `horizon_steps`; scans
  are bounded to the retained terminal row, and roll/maintenance crossing
  drops are inherited from the shared terminal path.
- Added synthetic fixtures and parity tests covering target-first, stop-first,
  same-bar ambiguity, forced same-bar policy variants, timeout, session-gap
  no-trade source rows, roll crossing, and maintenance crossing.
- Added durable docs and value-free parity evidence.

## Kernel / Fallback Table

| Label | Implemented route | Safe fallback | Reason |
| --- | --- | --- | --- |
| `mfe` | P02 guarded panel scan kernel | Reference path family | Exact max favorable return over retained future trade rows. |
| `mae` | P02 guarded panel scan kernel | Reference path family | Exact min adverse return over retained future trade rows. |
| `target_before_stop` | P02 guarded first-touch scan kernel | Reference path family | Exact target/stop ordering with `SameBarBarrierPolicy`. |
| `triple_barrier` | P02 guarded first-touch scan kernel | Reference path family | Exact target/stop/horizon/ambiguous outcome mapping. |

Fallback is documented and implemented for unsupported panel/terminal proof
boundaries. The materializer path created in this phase uses the P02 guarded
terminal model; callers that cannot satisfy that boundary must route through
the reference family rather than widening tolerances or changing semantics.

## Files Changed

Commit-eligible changed files:

- `README.md`
- `docs/label_compute_fast_path/OVERVIEW.md`
- `docs/label_compute_fast_path/PATH_LABEL_PACKS.md`
- `docs/label_compute_fast_path/README.md`
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P05.md`
- `research/label_compute_fast_path_v1/README.md`
- `research/label_compute_fast_path_v1/parity/LCFP-P05.md`
- `src/alpha_system/labels/fast/__init__.py`
- `src/alpha_system/labels/fast/materializer.py`
- `src/alpha_system/labels/fast/panel.py`
- `src/alpha_system/labels/fast/path.py`
- `tests/fixtures/label_compute_fast_path/path_labels.py`
- `tests/unit/label_compute_fast_path/test_path_label_pack.py`

No run-local `handoff.md`, `review.md`, or `verdict.json` was created.

## Parity Coverage

- 4 governed path labels covered: `mfe`, `mae`, `target_before_stop`,
  `triple_barrier`.
- 7 P05 tests pass.
- Fixture cases covered: target-first, stop-first, same-bar ambiguous,
  same-bar `target_first`, same-bar `stop_first`, timeout, no-trade
  session-gap source, roll crossing, and maintenance crossing.
- Exact parity asserted for `label_available_ts`, `label_spec_id`,
  `label_version_id`, event sets, and quality flags on reference-vs-fast scan
  cases.
- Exact P02 terminal guard disposition asserted for roll and maintenance
  crossing rows before value emission.

Documented tolerance:

- Path float values use `abs=1e-12, rel=1e-12` because the reference path
  family computes from `Decimal` input-view rows while the fast path consumes a
  float shared panel. Timestamp, identity, event-set, guard-disposition, and
  quality-flag checks remain exact.

## Validation

- `git status --short`
  - Not run. The executor prompt explicitly forbids `git status`; Ralph owns
    git state inspection.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m compileall -q src/alpha_system/labels/fast tests/unit/label_compute_fast_path tests/fixtures/label_compute_fast_path`
  - PASS, exit 0.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/test_path_label_pack.py -q`
  - PASS, `7 passed in 0.38s` on the final rerun.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/ -q`
  - PASS, `22 passed in 0.76s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/feature_compute_fast_path/test_fixed_horizon_label_pack.py -q`
  - PASS, `4 passed in 1.65s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`
  - PASS, `12 passed in 0.17s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/test_fast_path_artifact_policy.py -q`
  - PASS, `2 passed in 0.24s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python tools/verify.py --smoke`
  - PASS, exit 0.
- `git ls-files runs`
  - PASS, returned empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite'`
  - PASS, returned empty output.
- `git ls-files --modified --others --exclude-standard`
  - Used as the changed-file inventory because `git status` is forbidden.
  - Reported only the commit-eligible files listed above.

Additional non-required check:

- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m ruff check ...`
  - Not available in this venv: `No module named ruff`. A read-only long-line
    scan found no lines over 100 characters after formatting.

No `git add`, `git commit`, `git push`, `git diff`, reviewer call, PR creation,
merge, `review.md`, or `verdict.json` was performed by Codex.

## Residuals

- Fresh Claude review artifacts are required by the Yellow lane, but Codex did
  not create them because the executor prompt explicitly delegates review,
  verdict, PR, CI, merge gate, merge, and done-check to Ralph.
- This phase does not wire CLI targeting, checkpointing, workers, registry
  writes, or resolver smoke; those remain LCFP-P06 scope.
- This phase does not run real data, materialize values, or benchmark speed;
  those remain LCFP-P08 scope.
