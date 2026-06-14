# IVL-P01 Handoff - Intake Validator + alpha idea validate

Campaign: `ALPHA_IDEA_TO_VERDICT_LOOP_V0`  
Phase: `IVL-P01`  
Executor: Codex  
Date: 2026-06-14

## Scope Delivered

- Added `src/alpha_system/governance/idea_draft.py`.
  - New `IdeaDraft` intake-only wrapper validates `study_kind` as `main_effect` or
    `context_not_equal_trigger`.
  - `study_kind` and lineage live only on `IdeaDraft`.
  - `build_idea_validation_bundle()` mints/validates a HypothesisCard parent, always mints an
    AlphaSpec trunk via `generate_alpha_spec_id` + `validate_alpha_spec`, emits an EXPLORATORY
    MechanismCard via `create_mechanism_card`, and emits SetupSpec only for
    `context_not_equal_trigger`.
- Added `src/alpha_system/cli/idea.py` and registered it in `src/alpha_system/cli/main.py`.
  - `alpha idea validate <idea.yaml>` emits JSON for `idea_draft`, `hypothesis_card`,
    `alpha_spec`, `mechanism_card`, and optional `setup_spec`.
  - Governance/domain validation errors are wrapped to exit `2` with structured JSON issues.
- Added `src/alpha_system/governance/track_a_migration.py`.
  - Migrates all eight legacy Track-A cards to canonical value-free records.
  - Preserves legacy slug lineage as `MechanismCard.source = "track_a:<slug>"`.
  - Mints fresh canonical `mech_<24-hex>` ids.
  - Derives AlphaSpec `lspec_` label-reference IDs from legacy label names without creating
    LabelSpec objects or materializing labels.
- Added explicit Track-A gap metadata at
  `research/idea_to_verdict_loop_v0/track_a_migration_governance.json`.
  - Supplies explicit `cost_sensitivity`, `variant_budget`, `duplicate_exposure`, and
    `primary_horizon` per card.
  - The mapper fails closed when any of these are missing.
- Wrote value-free migrated records under `research/idea_to_verdict_loop_v0/migrated_cards/*.json`
  and a value-free front-door fixture at
  `research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml`.
- Added tests:
  - `tests/unit/governance/test_idea_draft.py`
  - `tests/unit/governance/test_track_a_migration.py`
  - `tests/unit/cli/test_idea_cli.py`
- Updated `README.md` with the compact IVL-P01 snapshot and unchanged safety boundaries.

## Track-A Parity Result

`tests/unit/governance/test_track_a_migration.py` asserts the canonical-vs-card map for all eight
legacy cards:

- `hypothesis.economic_rationale -> MechanismCard.rationale`
- `hypothesis.statement -> MechanismCard.expected_mechanism`
- `expected_sign -> MechanismCard.expected_direction`
- explicit `primary_horizon` selected from `expected_horizon[]`
- `expected_session -> MechanismCard.session`
- `required_features.existing[] -> MechanismCard.required_features` and AlphaSpec `factor_inputs`
- `required_labels.existing[] -> MechanismCard.required_labels` and deterministic AlphaSpec
  `label_references`
- `data_dependency.class/detail`, lookahead, and orthogonality material preserved in AlphaSpec
  assumptions, exclusions, failure modes, and criteria.

Source-grounded partition follows the IVL-P00 ADR/schema map: `existing_substrate=2`,
`derivable_from_exchange_calendar=4`, `needs_paid_data=2`. The generated prompt text still says
five derivable calendar cards; the current legacy JSON and ADR/schema map explicitly identify
`open_close_auction_flow` as `existing_substrate`, so the implementation preserves that source truth
and routes it as `existing_substrate_record_not_selected`. `day_of_week_effect` is the live exemplar.

`fomc_drift` and `cpi_surprise_reversion` migrate as `record_only_red_deferred`; they are not tested.

## Fail-Closed Gap Behavior

Covered by unit and CLI parametrized tests:

- Missing `MechanismCard.source` -> validation exits/fails closed.
- Missing `MechanismCard.cost_sensitivity` -> validation exits/fails closed.
- Missing `MechanismCard.variant_budget` -> validation exits/fails closed.
- Missing `MechanismCard.duplicate_exposure` -> validation exits/fails closed.
- Missing Track-A migration metadata for `primary_horizon`, `cost_sensitivity`, `variant_budget`,
  or `duplicate_exposure` -> migration fails closed.

No placeholder or silent default is used for these fields.

## Schema And Legacy-Card Boundary

- Executor did not edit:
  - `src/alpha_system/governance/alpha_spec.py`
  - `src/alpha_system/governance/mechanism_card.py`
  - `src/alpha_system/governance/setup_spec.py`
  - `research/differentiated_substrate_v1/cards/*.json`
- `rg -n "study_kind" src/alpha_system/governance/mechanism_card.py src/alpha_system/governance/setup_spec.py src/alpha_system/governance/alpha_spec.py || true` returned no matches.
- The requested `git diff` checks were not run because the executor prompt explicitly forbade
  `git diff`. The phase was implemented without staging or committing.

## Validation

Passed:

```bash
PYTHONPATH=src python -m pytest \
  tests/unit/governance/test_idea_draft.py \
  tests/unit/governance/test_track_a_migration.py \
  tests/unit/cli/test_idea_cli.py -q
# 23 passed
```

```bash
PYTHONPATH=src python -m pytest tests \
  -k "idea or idea_draft or mechanism_card or setup_spec or alpha_spec or track_a or migration" -q
# 222 passed, 2 skipped, 3426 deselected
```

```bash
python -c "import importlib,sys; [sys.exit('numpy/pandas must NOT import') for m in ('numpy','pandas') if importlib.util.find_spec(m)]"
# passed
```

```bash
python tools/verify.py --smoke
# passed
```

```bash
python tools/hooks/canary_runner.py
# all Frontier canaries passed
```

```bash
PYTHONPATH=src python -m alpha_system.cli.main idea --help
# exited 0 and showed the idea validate subcommand
```

Note: `python -m alpha_system.cli.main ...` prints a pre-existing `RuntimeWarning` because
`alpha_system.cli.__init__` imports `alpha_system.cli.main` before module execution. The command
exits `0`.

```bash
PYTHONPATH=src python -m alpha_system.cli.main idea validate \
  research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml \
  >/tmp/ivl_p01_idea_validate.json && \
python -c "import json; p=json.load(open('/tmp/ivl_p01_idea_validate.json')); assert p['alpha_spec']['alpha_spec_id'].startswith('aspec_'); assert p['mechanism_card']['stamp']=='EXPLORATORY'; print('front_door_validate_ok')"
# front_door_validate_ok
```

```bash
git ls-files runs
# empty
```

```bash
python tools/verify.py --artifacts
# passed
```

```bash
python tools/verify.py --boundaries
# passed
```

Additional pre-flight:

```bash
python tools/frontier/status_doctor.py
# WARN: no run dir with state.json found for ALPHA_IDEA_TO_VERDICT_LOOP_V0; no live run to reconcile
```

The prompted run artifact directory
`runs/2026-06-14T200245Z_ALPHA_IDEA_TO_VERDICT_LOOP_V0/phases/IVL-P01` was absent in this checkout.
No STOP file was present at the prompted run root.

Not run:

- `git diff --cached --name-only` and other `git diff` checks: explicitly forbidden by the executor
  prompt.
- `python tools/verify.py --all`: not required for this executor phase; closeout/reviewer concern.
- Review, verdict, PR, merge, staging, commit, push: explicitly driver-owned and not performed.

## Files For Driver Staging

- `src/alpha_system/governance/idea_draft.py`
- `src/alpha_system/governance/track_a_migration.py`
- `src/alpha_system/cli/idea.py`
- `src/alpha_system/cli/main.py`
- `research/idea_to_verdict_loop_v0/track_a_migration_governance.json`
- `research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml`
- `research/idea_to_verdict_loop_v0/migrated_cards/cpi_surprise_reversion.json`
- `research/idea_to_verdict_loop_v0/migrated_cards/day_of_week_effect.json`
- `research/idea_to_verdict_loop_v0/migrated_cards/fomc_drift.json`
- `research/idea_to_verdict_loop_v0/migrated_cards/month_end_flow.json`
- `research/idea_to_verdict_loop_v0/migrated_cards/month_end_rebalance_flow.json`
- `research/idea_to_verdict_loop_v0/migrated_cards/open_close_auction_flow.json`
- `research/idea_to_verdict_loop_v0/migrated_cards/opex_pinning.json`
- `research/idea_to_verdict_loop_v0/migrated_cards/roll_week_flow.json`
- `tests/unit/governance/test_idea_draft.py`
- `tests/unit/governance/test_track_a_migration.py`
- `tests/unit/cli/test_idea_cli.py`
- `README.md`
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P01.md`

No `runs/` path was staged or committed by the executor.
