# IVL-P03 Handoff

Campaign: `ALPHA_IDEA_TO_VERDICT_LOOP_V0`  
Phase: `IVL-P03`  
Executor: Codex  
Date: 2026-06-14

## Scope Delivered

- Added `src/alpha_system/research_lane/slice_spec.py`, an immutable bounded
  fast-probe slice descriptor with fail-closed validation, `from_idea_payload`
  extraction, explicit feature/label inputs, governed pack refs or relative
  paths, instrument/session/data-version fields, and label-version mapping.
- Added `src/alpha_system/research_lane/fast_probe.py`, a generic
  `fast_probe(card, setup, slice_spec)` bridge outside `research/`.
- The bridge validates supplied feature/label pack refs via
  `FeatureLabelPackResolver`, loads already-materialized bounded rows only via
  `core.value_store.load_parquet_values`, maps value-store records to the
  governance row schema, and injects rows in memory into:
  `build_factor_diagnostics_run` for `main_effect`, and
  `evaluate_setup_conditional_probe` for `context_not_equal_trigger`.
- The context-not-equal-trigger path runs a bounded label-shuffle surrogate and
  passes the resulting counts into the unchanged conditional probe. The
  unchanged probe enforces `ZERO_PASS_MET`, family budget, and the >=2-class
  guard; the bridge does not bypass those checks.
- Added DATA_GAP fallback payloads for missing/unresolved data root, missing
  optional Parquet dependency, resolver failure, or unloadable/empty rows:
  `status=INCONCLUSIVE`, `issue_code=DATA_GAP`, `promotion_eligible=False`,
  `row_access.fabricated_values=False`.
- Updated `README.md` with a compact factual IVL-P03 snapshot and IVL-P04 next.

## Files Changed

- `src/alpha_system/research_lane/fast_probe.py`
- `src/alpha_system/research_lane/slice_spec.py`
- `tests/unit/research_lane/test_fast_probe.py`
- `tests/unit/research_lane/test_slice_spec.py`
- `README.md`
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P03.md`

No review, verdict, PR, staging, commit, push, merge, broker, paper, live,
deployment, materialization, scaleout-driver, registry write, or paid-data
operation was performed by the executor.

## Validation

- `python -m pytest tests -k "fast_probe or slice_spec or research_lane" -q`
  - PASS: `23 passed, 2 skipped, 3653 deselected`
- `python -m pytest tests/unit/research/test_research_no_value_engine.py -q`
  - PASS: `3 passed`
- `python tools/verify.py --boundaries`
  - PASS: exit 0
- `grep -rEn "import +(alpha_system\\.)?(backtest|management|fast_path|core\\.value_store)|from +(alpha_system\\.)?(backtest|management|fast_path|core\\.value_store)" src/alpha_system/research && echo "FORBIDDEN IMPORT FOUND" && exit 1 || echo "no forbidden research->sim imports"`
  - PASS: `no forbidden research->sim imports`
- `python tools/verify.py --smoke`
  - PASS: exit 0
- `python tools/hooks/canary_runner.py`
  - PASS: all Frontier canaries passed
- `python -c "import importlib,sys; [sys.exit('numpy/pandas must NOT import') for m in ('numpy','pandas') if importlib.util.find_spec(m)]"`
  - PASS: exit 0
- `git ls-files runs`
  - PASS: exit 0 with empty output
- `python -m ruff check src/alpha_system/research_lane/fast_probe.py src/alpha_system/research_lane/slice_spec.py tests/unit/research_lane/test_fast_probe.py tests/unit/research_lane/test_slice_spec.py`
  - PASS: `All checks passed!`

## Skipped Checks / Exceptions

- `git diff --cached --name-only` was not run because the executor prompt
  explicitly forbids `git diff`.
- `python tools/verify.py --artifacts` was not run because it invokes
  `git diff --cached` internally, which is explicitly forbidden for this
  executor run.
- `python tools/verify.py --all` was not run: it includes the artifact guard
  path above and broad full-suite validation was not required by the phase
  after the scoped bridge/tests remained green. Ralph owns any additional
  validation pass.
- YELLOW review artifacts under `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P03/**`
  were not created because the executor prompt explicitly forbids calling Claude,
  running reviewer, creating `review.md`, or creating `verdict.json`. Ralph owns
  review routing.

## Safety / Boundary Confirmation

- The bridge lives in `src/alpha_system/research_lane/`, not `src/alpha_system/research/`.
  The boundary test was run and passed; no value loader import was added under
  `research/`.
- `core/value_store.py`, `src/alpha_system/research/conditional_probe.py`,
  `src/alpha_system/research/first_light.py`,
  `src/alpha_system/runtime/diagnostics/factor/runtime.py`, and the stopped DK
  tool were not edited. The bridge only imports `load_parquet_values` into
  `research_lane/`.
- `promotion_eligible=False` is set on every bridge readout and DATA_GAP payload.
  The conditional probe's `ZERO_PASS_MET`, family-budget, and >=2-class gates are
  honored by passing real surrogate counts into the unchanged engine; tests assert
  a non-zero surrogate pass raises through the engine.
- DATA_GAP payloads fabricate no values and do not call scoring paths when the
  data root or optional Parquet dependency is unavailable.
- No materialization, recompute, scaleout-driver call, registry write, second
  loader, numpy/pandas import, paid-data sourcing, broker, paper, live, order,
  deployment, promotion, or downstream-module behavior was added or run.
- `git ls-files runs` is empty. No `runs/**`, data, Parquet, Arrow, Feather, DBN,
  ZST, SQLite, DB, cache, log, model, secret, or key artifact was intentionally
  created for commit eligibility.
- No staging was performed; all changes are left unstaged for Ralph. The README
  snapshot is compact, factual, and reaffirms unchanged safety boundaries.
