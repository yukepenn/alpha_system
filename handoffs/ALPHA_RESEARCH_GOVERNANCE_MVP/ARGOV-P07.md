# ARGOV-P07 Handoff — StudySpec and Study Budget Protocol

## Summary

Implemented the `StudySpec` governance contract in
`alpha_system.governance.study_spec` using ARGOV-P02 typed IDs, canonical
serialization, deterministic round trips, and fail-closed structured
validation.

Implemented the study-budget protocol as pure accounting metadata:
`evaluate_variant_budget(...)` and `check_variant_budget(...)` compare a
declared positive integer `variant_budget` with an observed variant count and
return explicit `RESPECTED` or `OVERRUN` metadata. The helper performs no IO,
runs no variants, and never treats an overrun as clean.

Implemented the diagnostics gate:
`validate_diagnostics_gate(...)` / `assert_diagnostics_allowed(...)` block
`IMPLEMENTED -> DIAGNOSTICS_ALLOWED` unless a valid `StudySpec` is present.
Missing or invalid input raises `GovernanceValidationError`; there is no
permissive boolean result to coerce into allowed.

This phase added governance protocol metadata, tests, a tiny synthetic fixture,
docs, a template, and the README snapshot only. It did not run diagnostics,
studies, backtests, or variant searches; did not compute factors, labels, or
metrics; did not ingest real data; did not touch broker/live/paper/order-routing
scope; and did not introduce alpha, profitability, tradability, candidate,
validated, factor-library, or production-readiness claims.

## StudySpec Contract

`StudySpec` carries all campaign-required fields:

- `study_spec_id`
- `alpha_spec_id`
- `label_spec_id`
- `dataset_scope`
- `split_protocol`
- `metrics`
- `cost_assumptions`
- `variant_budget`
- `locked_test_policy`
- `negative_controls`
- `stopping_rules`

`study_spec_id` is a deterministic `sspec_...` content ID generated from the
remaining fields. `alpha_spec_id` must be a well-formed `aspec_...` ID and
`label_spec_id` must be a well-formed `lspec_...` ID. This phase validates ID
shape/kind only; registry existence checks remain later scope.

Validation is fail-closed:

- missing, null, empty, unknown, malformed, or non-serializable fields raise
  `GovernanceValidationError` with structured issues;
- `study_spec_id` must match deterministic `StudySpec` content;
- metadata mappings must be non-empty and explicit;
- `metrics`, `negative_controls`, and `stopping_rules` must be non-empty lists
  of explicit strings;
- `variant_budget` must be an exact positive integer cap.

Serialization round trips deterministically through the ARGOV-P02 canonical
serialization primitive.

## Study Budget

The budget protocol requires `variant_budget` to be declared before diagnostics.
Absent, null, non-positive, boolean, string, float, or otherwise unbounded
budgets fail closed.

Budget accounting returns `StudyBudgetCheck` metadata:

- `status`: `RESPECTED` or `OVERRUN`
- `respected`
- `overrun`
- `variants_remaining`
- `overrun_by`

Observed counts at or below the cap are `RESPECTED`; counts above the cap are
`OVERRUN` with `overrun_by` set to the excess count. This is accounting only and
does not execute a study or mutate a ledger.

## Locked Test And Negative Controls

`locked_test_policy` is mandatory, non-empty, and must include an explicit
policy string declaring OOS or locked-test handling. Empty policies or mappings
without any declared policy string fail closed.

`negative_controls` is mandatory and non-empty. The template and fixture declare
random-target, permuted-label, future-shift, and optimistic-fill controls. The
catalog and harness remain later ARGOV-P13/P14 scope; this phase only declares
the required controls.

## Diagnostics Gate

`validate_diagnostics_gate(...)` evaluates only:

```text
IMPLEMENTED -> DIAGNOSTICS_ALLOWED
```

It raises `GovernanceValidationError` when the `StudySpec` is missing, invalid,
or when another transition is passed. The block cannot be coerced to allowed
because the API returns a validated `StudySpec` or raises.

## README Snapshot

`README.md` now reflects `ARGOV-P07` executor deliverables: `StudySpec`,
study-budget overrun accounting, the no-StudySpec-no-diagnostics gate,
`docs/governance/STUDY_SPEC.md`, `docs/governance/STUDY_BUDGET.md`, and
`templates/governance/study_spec.template.yaml`. It also identifies
`ARGOV-P08 — TrialLedger and Variant Accounting` as the next planned phase and
reaffirms unchanged safety boundaries.

## Staged Files

Exact staged files after explicit staging:

- `README.md`
- `docs/governance/README.md`
- `docs/governance/STUDY_BUDGET.md`
- `docs/governance/STUDY_SPEC.md`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P07.md`
- `src/alpha_system/governance/__init__.py`
- `src/alpha_system/governance/study_spec.py`
- `templates/governance/README.md`
- `templates/governance/study_spec.template.yaml`
- `tests/fixtures/governance/README.md`
- `tests/fixtures/governance/study_spec_valid.json`
- `tests/unit/governance/test_study_budget.py`
- `tests/unit/governance/test_study_spec.py`

No `runs/**` path is staged.

## Validation Results

Spec-requested validation:

- `git status --short` — passed before staging. Output showed only allowed
  ARGOV-P07 paths:

```text
 M README.md
 M docs/governance/README.md
 M src/alpha_system/governance/__init__.py
 M src/alpha_system/governance/study_spec.py
 M templates/governance/README.md
 M tests/fixtures/governance/README.md
?? docs/governance/STUDY_BUDGET.md
?? docs/governance/STUDY_SPEC.md
?? templates/governance/study_spec.template.yaml
?? tests/fixtures/governance/study_spec_valid.json
?? tests/unit/governance/test_study_budget.py
?? tests/unit/governance/test_study_spec.py
```

- `python tools/verify.py --smoke` — passed with exit 0 and no output.

- `python -m pytest tests/unit/governance/test_study_spec.py -q` — passed:

```text
.............................................                            [100%]
45 passed in 0.03s
```

- `python -m pytest tests/unit/governance/test_study_budget.py -q` — passed:

```text
...........                                                              [100%]
11 passed in 0.01s
```

- `python -m pytest tests/unit/governance -q` — passed:

```text
........................................................................ [ 43%]
........................................................................ [ 86%]
......................                                                   [100%]
166 passed in 0.10s
```

- `test -f docs/governance/STUDY_SPEC.md` — passed with exit 0 and no output.
- `test -f docs/governance/STUDY_BUDGET.md` — passed with exit 0 and no output.
- `test -f templates/governance/study_spec.template.yaml` — passed with exit 0
  and no output.
- `git ls-files runs` — passed with empty output.

Additional local inspection:

- `git diff --check` — passed with exit 0 and no output.
- `python -m compileall -q src/alpha_system/governance/study_spec.py` — passed
  with exit 0 and no output.
- `find data -type f ! -name README.md ! -name .gitkeep -print` — passed with
  empty output.
- `find metadata -type f ! -name README.md ! -name .gitkeep -print` — passed
  with empty output.
- `find . -name '*.parquet' -not -path './tests/fixtures/*' -print` — passed
  with empty output.

Skipped checks: none of the spec-requested validation commands were skipped.
Claude review, reviewer execution, `review.md`, and `verdict.json` were not run
or created by Codex because the executor prompt explicitly reserves review and
verdict handling for Ralph and the independent reviewer.

## Artifact Policy

- `git ls-files runs` returned empty.
- `git diff --cached --name-only` contains no `runs/` path after explicit
  staging.
- The `data`, `metadata`, and Parquet audits returned empty output.
- No forbidden data, raw/canonical/factor/label/cache data, local DB, DB
  journal, WAL, Parquet, Arrow, Feather, log, cache, model binary, heavy
  artifact, or run artifact is staged.
- No run-local `handoff.md` under
  `runs/2026-06-03T135209Z_ALPHA_RESEARCH_GOVERNANCE_MVP/phases/ARGOV-P07/`
  was created or staged.
- No run-local `review.md`, `verdict.json`, `checks.json`, or
  `repair_attempts/` artifact was created or staged by Codex.

## Staging Discipline

- Explicit staging only.
- The staged set was built with explicit file paths.
- `git add .` was not used.
- `git add -A` was not used.
- No force push was performed.
- No commit was created by Codex in this executor step.
- No PR was created.
- No merge was performed.

## Scope Confirmation

- No diagnostics, studies, backtests, variant searches, factor computations,
  label computations, metric computations, real data ingestion, strategy
  optimization, portfolio allocation, candidate/library/promotion path, CLI,
  registry persistence, PR creation, or merge scope was introduced.
- No edits were made to `src/alpha_system/execution/broker/**`,
  `src/alpha_system/execution/live/**`, `src/alpha_system/execution/paper/**`,
  `src/alpha_system/execution/order_router*`, `src/alpha_system/broker/**`,
  `src/alpha_system/live/**`, data roots, metadata DB paths, or artifact roots.
- Tests were added only under authorized governance paths. Existing tests were
  not weakened, skipped, deleted, or relaxed.
- Fixtures are tiny synthetic governance metadata only; they are not real market
  data, computed label values, computed factor values, diagnostics output,
  research evidence, or alpha evidence.
