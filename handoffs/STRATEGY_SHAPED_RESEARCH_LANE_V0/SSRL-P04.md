# SSRL-P04 Handoff

## Scope Delivered

- Added `src/alpha_system/governance/trusted_handoff.py`, an additive trusted-rerun
  gap scaffold for EXPLORATORY strategy-shaped probe artifacts.
- The scaffold consumes a mapping shaped like the SSRL-P02/P03 artifacts:
  top-level or nested `stamp: EXPLORATORY`, optional `setup_spec`,
  optional `mechanism_card`, and optional partial trusted-lane candidate specs
  under `trusted_lane_specs`.
- The scaffold validates nested `SetupSpec` and `MechanismCard` declarations
  when present, reads the existing trusted-lane required-field constants, and
  emits a `TrustedHandoffGapReport`.
- The report output is:
  - `schema`: `alpha_system.governance.trusted_handoff_gap_report.v1`
  - `status`: `TRUSTED_RERUN_GAPS_ONLY`
  - `stamp`: `EXPLORATORY`
  - `promotion_eligible`: `false`
  - `promotion_evidence`: `false`
  - `trusted_rerun_required`: `true`
  - source provenance identifiers from the probe
  - one gap object each for `AlphaSpec`, `StudySpec`, `FeatureRequest`, and
    `LabelSpec`
  - a checklist for authoring the trusted rerun separately
- For the P03 first-light artifact, the emitted missing trusted-lane fields are:
  - `AlphaSpec`: `alpha_spec_id`, `hypothesis_id`, `target_instruments`,
    `data_assumptions`, `factor_inputs`, `label_references`,
    `exclusion_rules`, `timestamp_assumptions`, `cost_assumptions`,
    `expected_failure_modes`, `promotion_criteria`, `created_by`,
    `created_at`
  - `StudySpec`: `study_spec_id`, `alpha_spec_id`, `label_spec_id`,
    `dataset_scope`, `split_protocol`, `metrics`, `cost_assumptions`,
    `variant_budget`, `locked_test_policy`, `negative_controls`,
    `stopping_rules`
  - `FeatureRequest`: `feature_request_id`, `alpha_spec_id`,
    `requested_inputs`, `formula_sketch`, `availability_assumptions`,
    `duplicate_or_equivalent_exposure_notes`, `data_requirements`,
    `approval_status`
  - `LabelSpec`: `label_spec_id`, `horizon`, `path_rules`, `cost_model`,
    `target_stop_rules`, `availability_time`, `forbidden_feature_overlap`,
    `leakage_checks`
- Added focused tests for expected gap emission, EXPLORATORY stamp preservation,
  non-mutation, no lifecycle-state creation, partial candidate gap reporting, and
  promotion-path refusal with `EXPLORATORY_PROMOTION_REFUSAL_CODE`.
- Added `docs/strategy_shaped_lane/AI_RESEARCHER_HAPPY_PATH.md`.
- Added `docs/strategy_shaped_lane/PA_GRAMMAR_SUBSTRATE_V1.md`.
- Added
  `research/strategy_shaped_lane_v0/trusted_handoff/EXAMPLE_GAP_REPORT.json`,
  generated from the P03 first-light EXPLORATORY artifact.
- Updated existing strategy-shaped docs to keep scanner-sensitive no-claim
  boundary language value-free.
- Updated `README.md` with the P04 snapshot and final-planned-phase status.

## Checklist Emitted

1. Author an `AlphaSpec` with pre-registered hypothesis, instruments, inputs,
   label references, assumptions, exclusions, failure modes, and promotion
   criteria.
2. Author `FeatureRequest` metadata for context and trigger inputs, including
   availability assumptions and duplicate or equivalent exposure notes.
3. Author a `LabelSpec` for the trusted path-label binding, including horizon,
   path rules, target/stop rules, availability time, and leakage checks.
4. Author a `StudySpec` linking `AlphaSpec` and `LabelSpec` with dataset scope,
   split protocol, metrics, assumptions, variant budget, locked-test policy,
   negative controls, and stopping rules.
5. Run the trusted rerun separately; this EXPLORATORY handoff is only a gap
   report.

## Files Changed

- `README.md`
- `docs/strategy_shaped_lane/AI_RESEARCHER_HAPPY_PATH.md`
- `docs/strategy_shaped_lane/CONDITIONAL_PROBE.md`
- `docs/strategy_shaped_lane/PA_GRAMMAR_SUBSTRATE_V1.md`
- `docs/strategy_shaped_lane/REUSE_MAP.md`
- `docs/strategy_shaped_lane/V0_SCOPE.md`
- `handoffs/STRATEGY_SHAPED_RESEARCH_LANE_V0/SSRL-P04.md`
- `research/strategy_shaped_lane_v0/trusted_handoff/EXAMPLE_GAP_REPORT.json`
- `src/alpha_system/governance/__init__.py`
- `src/alpha_system/governance/trusted_handoff.py`
- `tests/unit/governance/test_trusted_handoff.py`

## Validation

- `PYTHONPATH=src python -m ruff check src/alpha_system/governance/trusted_handoff.py tests/unit/governance/test_trusted_handoff.py`
  passed: `All checks passed!`.
- `PYTHONPATH=src python -m pytest tests/unit/governance/test_trusted_handoff.py -q`
  passed: `5 passed`.
- `PYTHONPATH=src python -m pytest tests -k "handoff or promotion_refusal or exploratory" -q`
  passed: `35 passed, 2 skipped, 3517 deselected`.
- `PYTHONPATH=src python tools/verify.py --smoke` passed with no output.
- `PYTHONPATH=src python tools/hooks/canary_runner.py` passed; all Frontier
  canaries passed, including `forbidden_exploratory_promotion`,
  `forbidden_second_pnl_truth`, `planted_fake_alpha`, and true-alpha pair
  canaries.
- `PYTHONPATH=src python -c "import importlib.util,sys; bad=[m for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]; sys.exit('forbidden dependency importable: '+','.join(bad) if bad else 0)"`
  passed with no output.
- `grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path)|from +(alpha_system\.)?(backtest|management|fast_path)" src/alpha_system/research && echo "FORBIDDEN IMPORT FOUND" && exit 1 || echo "no forbidden research->sim imports"`
  passed and printed `no forbidden research->sim imports`.
- `sha256sum src/alpha_system/strategies/templates.py src/alpha_system/research/conditional_probe.py`
  recorded:
  - `e3afc86ef3d61b4990c9fc1df86c9e4ec7fcfa92040333741d1e6af891d959bd  src/alpha_system/strategies/templates.py`
  - `58ce73100dd732d8178b2d1af53b375cc0b79204f11a9a07c1a498d980b8b95e  src/alpha_system/research/conditional_probe.py`
- `grep -rEin 'pnl|profit|tradab|sharpe|return on|expected value|\$|alpha (found|exists)' research/strategy_shaped_lane_v0 docs/strategy_shaped_lane && echo "REVIEW: possible claim/PnL language" || echo "no PnL/claim tokens in artifacts"`
  passed and printed `no PnL/claim tokens in artifacts`.
- `git ls-files runs` passed and printed nothing.
- `env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES PYTHONPATH=src python tools/verify.py --all`
  failed once on
  `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`
  because ambient `ALPHA_DATA_ROOT` was exported and the cache policy selected
  `alpha_data_root`; this matches the known environment-sensitive closeout
  issue.
- `env -u ALPHA_DATA_ROOT -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES PYTHONPATH=src python tools/verify.py --all`
  passed: `3474 passed, 80 skipped` in `88.81s`; canaries also passed in that
  verify run.

## Skipped Or Adjusted Checks

- `git diff -- src/alpha_system/strategies/templates.py` was not run because the
  executor prompt explicitly forbids `git diff`. I did not edit
  `src/alpha_system/strategies/templates.py` or
  `src/alpha_system/research/conditional_probe.py`; hashes are recorded above
  and match the P03 handoff.
- The spec's double-quoted claim-scan form was not used because `\$` is passed
  to grep as the ERE line-end anchor in that form, producing a false hit on
  every line. The corrected single-quoted equivalent passed.

## Required Confirmations

- The scaffold emits trusted-rerun gaps without promoting and without stripping
  the `EXPLORATORY` stamp.
- The handoff/gap artifact is still refused by
  `reject_exploratory_promotion_artifact(s)` and `assert_promotion_gate` with
  `EXPLORATORY_PROMOTION_REFUSAL_CODE`.
- The single-factor path and SSRL-P02 compiler are byte-unchanged by this phase;
  hashes are recorded above and no edits were made to those files.
- `research/` imports no `backtest`, `management`, or `fast_path`, and the
  scaffold computes no outcome or PnL value.
- The happy-path doc and `PA_GRAMMAR_SUBSTRATE_V1` naming note are present and
  carry no profitability/tradability claim.
- The commit-eligible docs/research artifacts contain no PnL value or
  profitability/tradability claim per the corrected scanner.
- No trusted rerun, PA grammar pack, new probe/capability logic, live/paper
  trading, broker operation, order routing, deployment, PR, merge, review,
  `review.md`, or `verdict.json` was created by this executor.
- No `runs/` path was created, staged, or committed by this executor. The
  referenced run phase directory and generated spec file were absent in this
  checkout; execution used the full prompt spec as the contract and created only
  the commit-eligible handoff above.
