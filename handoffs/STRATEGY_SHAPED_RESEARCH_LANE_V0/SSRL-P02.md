# SSRL-P02 Handoff

## Scope Delivered

- Added the additive `CONTEXT_TRIGGER_CONDITIONAL_TEMPLATE` strategy template
  with `build_context_trigger_conditional_spec` and
  `evaluate_context_trigger_conditional`.
- Kept `SINGLE_FACTOR_THRESHOLD_TEMPLATE`, `build_single_factor_threshold_spec`,
  `evaluate_single_factor_threshold`, and `_require_threshold_template`
  source-hash unchanged.
- Added `src/alpha_system/research/conditional_probe.py`, compiling a validated
  `SetupSpec` into a context-factor predicate plus separate trigger-factor
  predicate, then scoring the trigger only inside the selected context bucket.
- Probe outcomes come only from materialized path-label rows using the existing
  path outcome fields consumed by `target_before_stop_probability` and
  `post_event_mfe_mae`; no PnL, backtest, management, or fast-path bridge was
  added.
- Every readout is stamped `EXPLORATORY`, has `promotion_eligible: false`,
  carries fixed geometry from the bound setup/path-label declaration, a
  VariantLedger/family-budget binding, a surrogate-FDR `ZERO_PASS_MET` gate, and
  a per-factor IC MDE/power statement.
- Added a fail-closed EXPLORATORY promotion guard in governance and wired it into
  the promotion gate for trusted transition contexts.
- Added the dedicated `forbidden_exploratory_promotion` canary and runner
  registration; the canary exits non-zero if the guard does not raise the
  `exploratory_artifact_refused` issue.
- Added focused tests, a compact conditional-probe contract doc, and the README
  campaign snapshot update for SSRL-P02.
- Repair attempt 1: regenerated the generated system map so the new
  `forbidden_exploratory_promotion` canary is listed under
  `docs/SYSTEM_MAP.md`.

## Files Changed

- `README.md`
- `docs/strategy_shaped_lane/CONDITIONAL_PROBE.md`
- `docs/SYSTEM_MAP.md`
- `evals/canaries/forbidden_exploratory_promotion/README.md`
- `src/alpha_system/strategies/templates.py`
- `src/alpha_system/research/conditional_probe.py`
- `src/alpha_system/research/diagnostics.py`
- `src/alpha_system/governance/promotion.py`
- `src/alpha_system/governance/promotion_gate.py`
- `tools/hooks/canary_runner.py`
- `tests/unit/strategies/test_conditional_template.py`
- `tests/unit/research/test_setup_probe.py`
- `tests/unit/governance/test_exploratory_refusal.py`
- `handoffs/STRATEGY_SHAPED_RESEARCH_LANE_V0/SSRL-P02.md`

## Validation

- `PYTHONPATH=src python -m pytest tests -k "conditional or setup_probe or exploratory or templates" -q`
  passed: `17 passed, 2 skipped, 3520 deselected`.
- `PYTHONPATH=src python tools/verify.py --smoke` passed with no output.
- `PYTHONPATH=src python tools/hooks/canary_runner.py` passed; all Frontier
  canaries passed, including `PASS forbidden_exploratory_promotion`.
- `PYTHONPATH=src python -c "import importlib.util,sys; bad=[m for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]; sys.exit('forbidden dependency importable: '+','.join(bad) if bad else 0)"`
  passed with no output.
- `grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path)|from +(alpha_system\.)?(backtest|management|fast_path)" src/alpha_system/research && echo "FORBIDDEN IMPORT FOUND" && exit 1 || echo "no forbidden research->sim imports"`
  passed and printed `no forbidden research->sim imports`.
- `git ls-files runs` passed and printed nothing.
- `PYTHONPATH=src python -m ruff check src/alpha_system/strategies/templates.py src/alpha_system/research/conditional_probe.py src/alpha_system/research/diagnostics.py src/alpha_system/governance/promotion.py src/alpha_system/governance/promotion_gate.py tools/hooks/canary_runner.py tests/unit/strategies/test_conditional_template.py tests/unit/research/test_setup_probe.py tests/unit/governance/test_exploratory_refusal.py`
  passed: `All checks passed!`.
- Repair validation: `just system-map` passed and rewrote
  `docs/SYSTEM_MAP.md`.
- Repair validation: `python tools/frontier/system_map.py --check` passed and
  printed `docs/SYSTEM_MAP.md is current.`
- Repair validation: `PYTHONPATH=src python -m pytest tests/tools/test_system_map.py -q`
  passed: `2 passed`.
- Repair validation: raw `just ci-parity` no longer failed on the stale system
  map, but later failed on
  `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`
  because this shell exports
  `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system`.
- Repair validation: `env -u ALPHA_DATA_ROOT PYTHONPATH=src python -m pytest tests/unit/runtime/test_cache_policy.py -q`
  passed: `12 passed`.
- Repair validation: `env -u ALPHA_DATA_ROOT -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES just ci-parity`
  passed: `3459 passed, 80 skipped`.
- Repair validation: `just verify-canaries` passed; all Frontier canaries
  passed, including `PASS forbidden_exploratory_promotion`.
- Repair audit: `git diff -- src/alpha_system/strategies/templates.py` showed
  the conditional template added after the existing single-factor functions, with
  no deletions.

## Skipped Checks

- `python tools/verify.py --all` was not run. The phase-required targeted tests,
  smoke, canaries, dependency absence, import-boundary guard, run-artifact guard,
  clean `ci-parity`, and focused lint passed, and no broad shared failure signal
  appeared.
- No reviewer, `review.md`, `verdict.json`, PR, staging, commit, push, merge, live
  trading, paper trading, broker operation, order routing, or deployment action
  was performed by this executor.

## Required Confirmations

- Single-factor path byte-unchanged: confirmed by the fixed source hash over
  `SINGLE_FACTOR_THRESHOLD_TEMPLATE`, `build_single_factor_threshold_spec`,
  `evaluate_single_factor_threshold`, and `_require_threshold_template`.
- `research/` imports no `backtest`, `management`, or `fast_path` package: the
  requested grep check passed.
- EXPLORATORY-refusal canary passes and fails if bypassed: runner output includes
  `PASS forbidden_exploratory_promotion`; the canary exits `1` if the guard does
  not raise `exploratory_artifact_refused`.
- Surrogate-FDR zero-pass and per-factor power are attached to every readout:
  asserted by `tests/unit/research/test_setup_probe.py`.
- Run artifacts remain local-only: `git ls-files runs` printed nothing, and no
  run-local handoff/review/verdict artifact was created.
