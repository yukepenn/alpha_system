# ARGOV-P05 Handoff — FeatureRequest and Duplicate Exposure Guard

## Summary

Implemented the `FeatureRequest` governance contract in
`alpha_system.governance.feature_request` using ARGOV-P02 IDs, canonical
serialization, and fail-closed structured validation.

Implemented the read-only duplicate/equivalent exposure guard in
`alpha_system.governance.duplicate_exposure`. The guard consumes an injected
registry reader or read-only registry path, returns structured duplicate or
equivalent findings, and can populate `FeatureRequest` duplicate-exposure notes.

This phase added only governance protocol metadata, tests, tiny synthetic
fixtures, and docs. It did not compute factor values, materialize data, mutate
the factor registry, grant implementation permission, or add candidate/library
status.

## FeatureRequest Contract

`FeatureRequest` carries all campaign-required fields:

- `feature_request_id`
- `alpha_spec_id`
- `requested_inputs`
- `formula_sketch`
- `availability_assumptions`
- `duplicate_or_equivalent_exposure_notes`
- `data_requirements`
- `approval_status`

Validation is fail-closed:

- missing, null, empty, unknown, malformed, or non-serializable fields raise
  `GovernanceValidationError` with structured issues;
- `feature_request_id` must be a deterministic content-bound `freq_...` ID;
- `alpha_spec_id` must be a well-formed `aspec_...` reference;
- duplicate-exposure notes must identify the `duplicate_exposure` guard, set
  `checked: true`, include registry status, entry count, findings, and summary;
- `approval_status` is constrained to `PENDING`, `BLOCKED_DUPLICATE`,
  `NEEDS_REVIEW`, or `APPROVED`;
- `create_feature_request(...)` defaults only to `PENDING`;
- no path auto-advances to `APPROVED`;
- blocking duplicate findings and unavailable registry checks cannot validate as
  `APPROVED`.

`FeatureRequest` implies no implementation permission, validation status,
candidate status, factor-library entry, trading action, or research result.

## Duplicate-Exposure Guard

The guard exposes:

- `check_duplicate_exposure(feature_request, registry_reader) -> ExposureCheckResult`
- `find_duplicate_exposures(feature_request, registry_reader) -> tuple[ExposureFinding, ...]`
- `apply_duplicate_exposure_notes(feature_request, result) -> FeatureRequest`
- `check_and_update_feature_request(feature_request, registry_reader) -> FeatureRequest`

Each `ExposureFinding` has:

- `kind`: `DUPLICATE` or `EQUIVALENT`
- `severity`: `BLOCKING` or `WARNING`
- `matched_registry_reference`
- `rationale`

Registry interaction is read-only:

- tests inject a synthetic read-only spy via `read_factor_versions()`;
- iterable and callable registry readers are accepted;
- registry paths are opened through the existing registry connection helper with
  `read_only=True`;
- the guard does not call `register_factor_spec`,
  `record_factor_validation_run`, `record_promotion_decision`, or any other
  mutating registry path;
- unavailable readers degrade to `registry_status: UNAVAILABLE` without
  crashing and without producing a clean claim.

Duplicate matches are blocking. Equivalent operation/input/window matches are
warnings. Empty registries return no findings with `registry_status: EMPTY`.

## Docs And README

Added:

- `docs/governance/FEATURE_REQUEST.md`
- `docs/governance/DUPLICATE_EXPOSURE.md`

Updated `README.md` with a compact ARGOV-P05 snapshot, ARGOV-P06 as next, the
new durable modules/docs, and unchanged safety boundaries. The README does not
record a phase PASS verdict and does not include run-local artifact paths or
alpha/profitability/tradability claims.

## Staged Files

Exact staged files after explicit staging:

- `README.md`
- `docs/governance/DUPLICATE_EXPOSURE.md`
- `docs/governance/FEATURE_REQUEST.md`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P05.md`
- `src/alpha_system/governance/__init__.py`
- `src/alpha_system/governance/duplicate_exposure.py`
- `src/alpha_system/governance/feature_request.py`
- `tests/fixtures/governance/README.md`
- `tests/fixtures/governance/duplicate_exposure_registry.json`
- `tests/fixtures/governance/feature_request_valid.json`
- `tests/unit/governance/test_duplicate_exposure.py`
- `tests/unit/governance/test_feature_request.py`
- `tests/unit/governance/test_package_skeleton.py`

No `runs/**` path is staged.

## Validation Results

Final spec-requested validation:

- `git status --short` — passed before staging. Output showed only allowed
  ARGOV-P05 paths:

```text
 M README.md
 M src/alpha_system/governance/__init__.py
 M src/alpha_system/governance/feature_request.py
 M tests/unit/governance/test_package_skeleton.py
?? docs/governance/DUPLICATE_EXPOSURE.md
?? docs/governance/FEATURE_REQUEST.md
?? src/alpha_system/governance/duplicate_exposure.py
?? tests/fixtures/governance/README.md
?? tests/fixtures/governance/duplicate_exposure_registry.json
?? tests/fixtures/governance/feature_request_valid.json
?? tests/unit/governance/test_duplicate_exposure.py
?? tests/unit/governance/test_feature_request.py
```

- `python tools/verify.py --smoke` — passed with exit 0 and no output.

- `python -m pytest tests/unit/governance/test_feature_request.py -q` —
  passed:

```text
......................                                                   [100%]
22 passed in 0.02s
```

- `python -m pytest tests/unit/governance/test_duplicate_exposure.py -q` —
  passed:

```text
....                                                                     [100%]
4 passed in 0.02s
```

- `python -m pytest tests/unit/governance -q` — passed:

```text
........................................................................ [ 83%]
..............                                                           [100%]
86 passed in 0.08s
```

- `test -f docs/governance/FEATURE_REQUEST.md` — passed with exit 0 and no
  output.
- `test -f docs/governance/DUPLICATE_EXPOSURE.md` — passed with exit 0 and no
  output.
- `git ls-files runs` — passed with empty output.
- `find data -type f ! -name README.md ! -name ".gitkeep" -print` — passed
  with empty output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` —
  passed with empty output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` — passed
  with empty output.

Interim checks:

- An initial focused duplicate-exposure test run failed because the unavailable
  registry summary text did not contain the expected explicit word
  "unavailable". The summary was updated, and the final rerun above passed.
- A bare diagnostic `python - <<'PY' ...` import failed with
  `ModuleNotFoundError: No module named 'alpha_system'` because the local shell
  does not install the package or add `src` to `sys.path`. The same diagnostic
  with `PYTHONPATH=src` passed and produced a deterministic `freq_...` ID.

Skipped checks: none of the spec-requested commands were skipped.

## Artifact Policy

- `git ls-files runs` returned empty.
- `git diff --cached --name-only` contains no `runs/` path after explicit
  staging.
- The `data`, `metadata`, and Parquet audits returned empty output.
- No forbidden data, raw/canonical/factor/label/cache data, local DB, DB
  journal, WAL, Parquet, Arrow, Feather, log, cache, model binary, heavy
  artifact, or run artifact is staged.
- No run-local `handoff.md` under
  `runs/2026-06-03T135209Z_ALPHA_RESEARCH_GOVERNANCE_MVP/phases/ARGOV-P05/`
  was created or staged.
- No run-local `review.md`, `verdict.json`, `checks.json`, or
  `repair_attempts/` artifact was created or staged by Codex.

## Staging Discipline

- Explicit staging only.
- The staged set was built with explicit file paths.
- `git add .` was not used.
- `git add -A` was not used.
- No force push was performed.
- No PR was created.
- No merge was performed.

## Scope Confirmation

- No edits were made to `src/alpha_system/factors/**`.
- No factor registry mutation, factor registration, validation recording, or
  promotion recording path was called or added.
- No broker, live, paper, order-routing, production-deployment,
  real-data-ingestion, alpha-search, factor-computation, label materialization,
  diagnostics, backtest, strategy optimization, portfolio allocation, CLI, report
  template, or promotion-gate scope was introduced.
- Tests were added only under authorized governance paths. Existing tests were
  not weakened, skipped, deleted, or relaxed.
- Fixtures are tiny synthetic governance metadata only; they are not real market
  data, computed factor values, research evidence, or alpha evidence.
- No alpha, profitability, tradability, paper-readiness, live-readiness,
  broker-readiness, capital-allocation, production-readiness,
  deployment-readiness, candidate-status, or factor-library-entry claim was
  introduced.

## Review Boundary

No Claude review was run by Codex. No `review.md` or `verdict.json` was created.
Ralph owns validation orchestration, independent review routing, verdict
parsing, PR creation, CI, merge gates, semantic done-checks, and phase PASS
marking.
