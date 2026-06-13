# SSRL-P01 Handoff

## Scope Completed

- Added additive governance ID kinds and prefixes for `MechanismCard` (`mech_`)
  and `SetupSpec` (`setup_`) without altering existing kinds or prefixes.
- Added `MechanismCard` as a pure governance contract with required fields for
  source, rationale, expected mechanism/direction, horizon, session, required
  features, required labels, cost sensitivity, variant budget, duplicate
  exposure notes, and a first-class `stamp` field.
- Added `SetupSpec` as a pure governance contract with required fields for
  entry context, separate event trigger, regime filter, confirmation,
  invalidation, stop, target, hold time, horizon, governed path-label binding,
  allowed variants, forbidden post-hoc changes, mechanism link, and a first-class
  `stamp` field.
- Both contracts are content-addressed over required component fields excluding
  their ID fields, validate fail-closed, and round-trip through canonical
  governance serialization.
- `stamp` defaults to and validates as `EXPLORATORY`; no promotion logic or
  promotion eligibility was added.
- `SetupSpec.mechanism_id` validates as a `MechanismCard` governance ID, and
  `SetupSpec.path_label` validates as a governed `LabelSpec` ID.
- `SetupSpec.event_trigger` is a required field distinct from `entry_context`;
  validation rejects missing triggers, object aliases, canonical duplicate
  content, and explicit derivation from `entry_context`.
- Added focused tests for required fields, type validation, vague-text
  rejection, deterministic content addressing, ID change on component changes,
  canonical round trips, EXPLORATORY stamp behavior, mechanism linkage, and
  context-vs-trigger separation.
- Updated the compact README current snapshot for the new governance contracts
  and the next `SSRL-P02` phase.

## Files Changed

- `src/alpha_system/governance/ids.py`
- `src/alpha_system/governance/__init__.py`
- `src/alpha_system/governance/mechanism_card.py`
- `src/alpha_system/governance/setup_spec.py`
- `tests/unit/governance/test_ids.py`
- `tests/unit/governance/test_mechanism_card.py`
- `tests/unit/governance/test_setup_spec.py`
- `README.md`
- `handoffs/STRATEGY_SHAPED_RESEARCH_LANE_V0/SSRL-P01.md`

## Validation

- `PYTHONPATH=src python -m pytest tests -k "setup_spec or mechanism_card" -q`
  passed: `102 passed, 2 skipped, 3424 deselected in 1.42s`.
- `PYTHONPATH=src python -m ruff check src/alpha_system/governance/ids.py src/alpha_system/governance/__init__.py src/alpha_system/governance/mechanism_card.py src/alpha_system/governance/setup_spec.py tests/unit/governance/test_ids.py tests/unit/governance/test_mechanism_card.py tests/unit/governance/test_setup_spec.py`
  passed: `All checks passed!`.
- `PYTHONPATH=src python tools/verify.py --smoke` passed with no output.
- `PYTHONPATH=src python tools/hooks/canary_runner.py` passed; all Frontier
  canaries passed, including planted fake alpha, true-alpha pair,
  forbidden second PnL truth, forbidden scope drift, and governance random target.
- `git ls-files runs` passed and printed nothing.
- `PYTHONPATH=src python -c "import importlib.util, sys; offenders=[m for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]; sys.exit('numpy/pandas/polars must NOT import: '+','.join(offenders)) if offenders else None"`
  passed and printed nothing.
- `PYTHONPATH=src python -m pytest tests/unit/governance/test_ids.py -q`
  passed: `10 passed in 0.01s`.

## Skipped Checks

- `git diff --name-only -- src/alpha_system/strategies/templates.py src/alpha_system/research`
  was not run because the executor prompt explicitly forbids running `git diff`.
  No edits were made to `src/alpha_system/strategies/templates.py` or
  `src/alpha_system/research/**`.
- `python tools/verify.py --all` was not run. The required targeted tests,
  smoke check, canaries, run-artifact check, dependency absence check, and
  ID-registry test passed; no failing shared-governance behavior appeared that
  required broadening to the full suite.

## Invariants

- Single-factor engine/template/research paths were not edited.
- No `AlphaSpec`, `StudySpec`, or `HypothesisCard` duplication was introduced;
  the new contracts link to existing governed IDs where needed.
- No executable probe, compiler, runtime, diagnostics, backtest, management,
  portfolio, broker, live, L2, data, or simulation code was added or edited.
- No new dependency was added; numpy, pandas, and polars remain unimportable in
  the checked environment.
- No second PnL/value truth was introduced.
- No live trading, paper trading, broker operation, order routing, deployment,
  PR creation, merge, staging, commit, push, reviewer call, `review.md`, or
  `verdict.json` was performed by this executor.
- The referenced run-local phase directory was not present in this worktree, and
  no run-local artifacts were written.
