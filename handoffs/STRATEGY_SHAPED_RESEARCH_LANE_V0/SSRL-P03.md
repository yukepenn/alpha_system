# SSRL-P03 Handoff

## Scope Delivered

- Added `src/alpha_system/research/first_light.py`, a small additive evidence
  helper that declares the first-light `MechanismCard` and `SetupSpec`, compiles
  the setup through the unchanged SSRL-P02 conditional probe, and records the
  de-stack read through the unchanged single-factor threshold template.
- Declared the first-light idea as:
  - `entry_context.factor_id`: `liquidity_structure_range_contraction`
  - `event_trigger.factor_id`: `liquidity_structure_failed_high_breakout_flag`
  - `target.path_outcome`: `target_before_stop`
  - `hold_time.max_minutes`: `120`
  - `path_label`: `lspec_9b1d49df8ff366677cb6f7bd`
  - `variant_id`: `baseline_range_contraction_failed_high_breakout`
  - `family_id`: `ssrl_p03_first_light_range_contraction_failed_high_breakout`
  - `stamp`: `EXPLORATORY`
- Wrote commit-eligible first-light declaration/evidence artifacts:
  - `research/strategy_shaped_lane_v0/first_light/mechanism_card.json`
  - `research/strategy_shaped_lane_v0/first_light/setup_spec.json`
  - `research/strategy_shaped_lane_v0/first_light/EVIDENCE.json`
- Real slice status: `INCONCLUSIVE` / `DATA_GAP`. The executor could see
  matching manifest files for the context factor, trigger factor, and 120m path
  label under `ALPHA_DATA_ROOT`, but no sanctioned Parquet reader module
  (`duckdb`, `pyarrow`, `numpy`, `pandas`, `polars`) was importable. No row
  values were fabricated.
- Recorded the de-stack diagnostic as value-free evidence through the existing
  single-factor engine:
  - factor reference: `vwap_session.factor_session_minute`
  - isolated IC read: `0.068`
  - observation count: `6862`
  - power MDE: `0.023662594516346006`
  - artifact: `research/strategy_shaped_lane_v0/de_stack/EVIDENCE.json`
- Added focused synthetic-fixture tests covering declaration validation,
  conditional-probe execution, static JSON validation, de-stack single-factor
  engine shape, and EXPLORATORY promotion refusal.
- Added `docs/strategy_shaped_lane/FIRST_LIGHT.md` and updated `README.md` with
  the compact P03 snapshot and unchanged boundaries.

## Files Changed

- `README.md`
- `docs/strategy_shaped_lane/FIRST_LIGHT.md`
- `handoffs/STRATEGY_SHAPED_RESEARCH_LANE_V0/SSRL-P03.md`
- `research/strategy_shaped_lane_v0/de_stack/EVIDENCE.json`
- `research/strategy_shaped_lane_v0/first_light/EVIDENCE.json`
- `research/strategy_shaped_lane_v0/first_light/mechanism_card.json`
- `research/strategy_shaped_lane_v0/first_light/setup_spec.json`
- `src/alpha_system/research/first_light.py`
- `tests/unit/research/test_first_light.py`

## Validation

- `PYTHONPATH=src python -m pytest tests -k "first_light or conditional or exploratory" -q`
  passed: `15 passed, 2 skipped, 3528 deselected`.
- `PYTHONPATH=src python -m ruff check src/alpha_system/research/first_light.py tests/unit/research/test_first_light.py`
  passed: `All checks passed!`.
- `PYTHONPATH=src python tools/verify.py --smoke` passed with no output.
- `PYTHONPATH=src python tools/hooks/canary_runner.py` passed; all Frontier
  canaries passed, including `PASS forbidden_exploratory_promotion`.
- `PYTHONPATH=src python -c "import importlib.util,sys; bad=[m for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]; sys.exit('forbidden dependency importable: '+','.join(bad) if bad else 0)"`
  passed with no output.
- `grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path)|from +(alpha_system\.)?(backtest|management|fast_path)" src/alpha_system/research && echo "FORBIDDEN IMPORT FOUND" && exit 1 || echo "no forbidden research->sim imports"`
  passed and printed `no forbidden research->sim imports`.
- `grep -rEin 'pnl|profit|tradab|sharpe|return on|expected value|\$|alpha (found|exists)' research/strategy_shaped_lane_v0 && echo "REVIEW: possible claim/PnL language" || echo "no PnL/claim tokens in evidence"`
  passed and printed `no PnL/claim tokens in evidence`.
- `git ls-files runs` passed and printed nothing.
- `sha256sum src/alpha_system/strategies/templates.py src/alpha_system/research/conditional_probe.py`
  recorded:
  - `e3afc86ef3d61b4990c9fc1df86c9e4ec7fcfa92040333741d1e6af891d959bd  src/alpha_system/strategies/templates.py`
  - `58ce73100dd732d8178b2d1af53b375cc0b79204f11a9a07c1a498d980b8b95e  src/alpha_system/research/conditional_probe.py`

## Skipped Checks

- `git diff -- src/alpha_system/strategies/templates.py` was not run because the
  executor prompt explicitly forbids `git diff`. I did not edit
  `src/alpha_system/strategies/templates.py` or
  `src/alpha_system/research/conditional_probe.py`; hashes are recorded above
  for driver/reviewer comparison.
- The spec's double-quoted evidence grep form was also run and produced a false
  `REVIEW` result because the shell consumed the backslash before `$`, making
  grep match line ends. The corrected escaped scan above passed.
- `python tools/verify.py --all` was not run. This phase added a bounded
  research helper, evidence artifacts, docs, README snapshot, and focused tests;
  it did not modify shared governance, diagnostics, strategy templates, or the
  P02 compiler.

## Required Confirmations

- `entry_context` and `event_trigger` are separate fields and read two different
  factors: `liquidity_structure_range_contraction` vs
  `liquidity_structure_failed_high_breakout_flag`.
- The first-light output is `EXPLORATORY`-stamped, `promotion_eligible: false`,
  variant-ledgered under the family budget, and the promotion guard still
  refuses it; the focused test and `forbidden_exploratory_promotion` canary pass.
- Outcomes are bound to materialized path labels only; no `backtest`,
  `management`, or `fast_path` import exists under `src/alpha_system/research`.
- Surrogate-FDR and power statements are attached to both first-light and
  de-stack readouts. First-light is blocked as `DATA_GAP` with `n_eff: 0`;
  de-stack records `zero-pass-met` and `n_eff: 6862`.
- The de-stack read uses the existing `single_factor_threshold` template and
  records `engine_changed: false`.
- Evidence under `research/strategy_shaped_lane_v0` contains no PnL token,
  promotion claim, or profitability/tradability language per the corrected grep
  scan.
- No reviewer, `review.md`, `verdict.json`, PR, staging, commit, push, merge,
  live trading, paper trading, broker operation, order routing, deployment, or
  destructive cleanup was performed by this executor.
