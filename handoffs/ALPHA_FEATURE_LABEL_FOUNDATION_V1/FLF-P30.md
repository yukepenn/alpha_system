# FLF-P30 Handoff - End-to-End Feature/Label Dry Run

## Summary

Implemented the FLF-P30 local-only end-to-end Feature/Label dry-run scope.

This phase adds a CI-safe integration test that exercises the existing
Feature/Label substrate from governed `FeatureRequest` and `LabelSpec` handles
through feature and label materialization, FeatureRegistry metadata, feature
quality and coverage reports, label leakage and availability audit, StudySpec
Input Pack validation, and the FLF-P28 CLI dry-run surfaces.

No production source, governance module, substrate contract, store, registry,
engine, or schema was edited. The dry run uses a tiny synthetic
Databento-shaped accepted DatasetVersion fixture by default and writes
materialized feature/label values only under pytest temporary
`ALPHA_DATA_ROOT`.

## Staging / Curated File List

Codex staged no files. The executor prompt explicitly prohibited `git add`,
`git commit`, `git push`, `git status`, and `git diff`; all changes are left
unstaged for Ralph.

`git status --short`: not run; explicitly forbidden by the executor prompt.

Exact staged files by Codex:

- none

Curated files for Ralph to stage explicitly by path:

- `docs/feature_label_foundation/E2E_DRY_RUN.md`
- `tests/integration/feature_label/test_e2e_dryrun.py`
- `README.md`
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P30.md`

Do not stage `runs/**` or generated cache files. Local `__pycache__` files may
exist from pytest/py_compile and are not commit-eligible.

## Validation Results

- `git status --short`: not run; explicitly forbidden by the executor prompt.
- STOP check:
  `test -f runs/2026-06-05T131433Z_ALPHA_FEATURE_LABEL_FOUNDATION_V1/STOP` -
  passed; no STOP file present.
- `git ls-files runs`: passed; output empty.
- `test -f docs/feature_label_foundation/E2E_DRY_RUN.md`: passed.
- `python -m pytest tests/integration/feature_label/test_e2e_dryrun.py -q`:
  passed, `1 passed`.
- `python -m pytest tests/integration/feature_label -q`: passed, `2 passed`.
- `python -m ruff check tests/integration/feature_label/test_e2e_dryrun.py`:
  passed.
- `python tools/verify.py --smoke`: passed with no output.
- `find data -type f ! -name README.md ! -name .gitkeep -print`: passed;
  output empty.
- `find metadata -type f ! -name README.md ! -name .gitkeep -print`: passed;
  output empty.
- `find artifacts -type f -size +1M -print`: passed; output empty.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print`: passed;
  output empty.
- `python tools/hooks/canary_runner.py`: passed; all Frontier canaries passed.
- Optional real local DatasetVersion command
  `alpha feature dry-run --dataset dsv_databento_ohlcv_<hex> --small --local-only`:
  skipped because `ALPHA_DATA_ROOT` is unset in this executor environment and no
  local accepted DatasetVersion id/registry was supplied. The synthetic fixture
  path is the documented fallback.
- `git diff --cached --name-only`: not run; `git diff` is explicitly forbidden
  and Codex staged nothing.

## Dry-Run Coverage

The integration test asserts:

- Feature lifecycle observation advances through `REQUESTED`, `SPEC_DRAFTED`,
  `SPEC_VALIDATED`, `IMPLEMENTATION_ALLOWED`, materialization, quality/coverage
  report consumption, registration, and `READY_FOR_STUDY` input-pack readiness.
- Label lifecycle observation advances through `LABEL_REQUESTED`,
  `LABEL_SPEC_DRAFTED`, `LABEL_SPEC_VALIDATED`, `MATERIALIZATION_ALLOWED`,
  materialization, leakage audit, and `READY_FOR_STUDY`.
- Every feature value carries timezone-aware `available_ts` at or after
  `event_ts`.
- Every label value carries timezone-aware `label_available_ts` at or after
  `horizon_end_ts`.
- The label leakage guard and registered-label audit are clean for safe live
  feature references; no label-as-feature path is admitted.
- BBO missingness and quarantine are surfaced as `missing_bbo` and
  `bbo_quarantined`, and quote-derived feature values on those rows are `None`
  rather than silently forward-filled.
- The dense-grid no-trade fixture row carries `has_trade=false`,
  `synthetic=true`, `quality_flags=("no_trade",)`, and zero volume.
- The StudySpec Input Pack validates against existing `FeatureRequest`,
  `LabelSpec`, `AlphaSpec`, and `StudySpec` contracts without modifying the
  StudySpec schema.
- Prohibited MVP lifecycle states remain outside feature and label registry
  lifecycle enums.

The feature coverage report is consumed and records the existing fail-closed
`SESSION_COVERAGE_UNRESOLVED` warning for scalar feature values that do not
embed a session identifier. The dry-run summary documents this as a substrate
coverage-report warning, not as research evidence or production readiness.

## Artifact Policy Confirmation

- Codex staged nothing and ran no commit, push, PR, merge, reviewer, or verdict
  operation.
- No `runs/` path is in the curated commit-eligible file list.
- `git ls-files runs` returned empty output.
- No raw, canonical, factor, feature-value, label-value, provider-response,
  parquet, arrow, feather, DBN, Zstd, SQLite, local registry, log, model,
  report-bundle, data, DB, or heavy artifact is in the curated file list.
- Feature and label values created by tests were written only under pytest
  temporary `ALPHA_DATA_ROOT`, outside the repository tree.
- The durable dry-run documentation is row-free and contains no raw rows,
  feature values, label values, provider responses, registry contents, or local
  artifact paths.

## DAG / Scope Confirmation

- FLF-P30 DAG metadata was treated as run-alone:
  `parallel_safe=false`, `must_run_alone=true`, merge group `closeout`, serial
  merge queue.
- `ACTIVE_CAMPAIGN.md` was not edited.
- No `src/**` file was edited.
- Governance modules were consumed, not edited:
  `feature_request`, `duplicate_exposure`, `label_spec`,
  `label_leakage_guard`, `study_spec`, and `study_input_pack`.
- Dataset consumption resolves accepted DatasetVersions through the sanctioned
  registry path and canonical mapping loaders in the existing substrate.
- No external Databento or IBKR provider call, provider client import, data
  pull, raw-provider file read, broker/live/paper/order-routing/account scope,
  strategy/backtest/portfolio scope, production deployment, or destructive
  operation was performed or added.
- No alpha, profitability, tradability, promotion, broker-readiness,
  paper-readiness, live-readiness, or production-readiness claim was introduced.

## README Snapshot

`README.md` was updated per the FLF-P30 snapshot policy: progress through
FLF-P30, active FLF-P30 / next FLF-P31 closeout, the new
`docs/feature_label_foundation/E2E_DRY_RUN.md` summary and
`tests/integration/feature_label/test_e2e_dryrun.py`, and unchanged safety
boundaries. The update does not include generated run details, local artifact
paths, alpha claims, broker/live/paper/deployment behavior, or duplicated
handoff content.

## Review Status

This YELLOW phase still requires fresh independent Claude review by Ralph's
review step. Codex did not call Claude, run reviewer, create `review.md`,
create `verdict.json`, mark the phase PASS, create a PR, merge, stage, commit,
or push, per executor instructions.
