# FLF-P26 Handoff - Small Real Databento DatasetVersion Dry Run

## Summary

Implemented the FLF-P26 bounded accepted-DatasetVersion dry-run surface.

This phase adds a provider-neutral helper under `alpha_system.features.engine`
that resolves one accepted DatasetVersion through the existing consumption
adapter, validates supplied canonical mappings through the canonical loaders,
and delegates value production to the existing feature and label engines. The
helper returns only a row-free summary: counts, symbol/session coverage,
partition, quality/coverage status, BBO missingness, synthetic no-trade counts,
blocking flags, and local-output-root booleans. It does not read provider files,
call providers, import provider clients, register values, or write inside the
repository.

The real local Databento operator run was not performed in this executor
workspace because no real local Databento DatasetVersion id, registry evidence,
or canonical row slice was supplied. The durable dry-run doc records that
truthfully as `PASS_WITH_WARNINGS` and includes the exact operator command. The
CI-safe integration test creates a temporary accepted synthetic DatasetVersion
registry entry and materializes a bounded feature/label sample under a temporary
`ALPHA_DATA_ROOT`.

## Staging / Curated File List

Codex staged no files. The executor prompt explicitly prohibited `git add`,
`git commit`, `git push`, `git status`, and `git diff`; all changes are left
unstaged for Ralph.

`git status --short`: not run; explicitly forbidden by the executor prompt.

Exact staged files by Codex:

- none

Curated files for Ralph to stage by explicit path:

- `src/alpha_system/features/engine/dataset_version_dry_run.py`
- `src/alpha_system/features/engine/__init__.py`
- `tests/integration/feature_label/test_small_databento_dataset_version_dryrun.py`
- `docs/feature_label_foundation/DRY_RUN_DATABENTO.md`
- `README.md`
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P26.md`

No `runs/` path is commit-eligible for this phase.

## Validation Results

- `git status --short`: not run; explicitly forbidden by the executor prompt.
- `python -m pytest tests/integration/feature_label -q`: passed, `1 passed`.
- `python -m ruff check src/alpha_system/features/engine/dataset_version_dry_run.py src/alpha_system/features/engine/__init__.py tests/integration/feature_label/test_small_databento_dataset_version_dryrun.py`: passed.
- `python tools/verify.py --smoke`: passed.
- `test -f docs/feature_label_foundation/DRY_RUN_DATABENTO.md`: passed.
- `git ls-files runs`: passed; output empty.
- `find data -type f ! -name README.md ! -name ".gitkeep" -print`: passed; output empty.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print`: passed; output empty.
- `find artifacts -type f -size +1M -print`: passed; output empty.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print`: passed; output empty.
- `grep -REn "\.dbn|\.zst|read_parquet|pyarrow|databento|ib_insync|\.feather" src/alpha_system/features src/alpha_system/labels 2>/dev/null | grep -v "from_mapping\|resolve_dataset_version" || echo "no direct provider/file readers found in feature/label code"`: passed, `no direct provider/file readers found in feature/label code`.
- Real local operator command `alpha feature dry-run --dataset dsv_databento_ohlcv_<hex> --small --local-only`: not run; no real local DatasetVersion id, registry evidence, or canonical row slice was supplied to this executor workspace.
- `git diff --cached --name-only`: not run; `git diff` is explicitly forbidden and Codex staged nothing.

## Artifact Policy Confirmation

- Codex staged nothing and ran no commit, push, PR, merge, reviewer, or verdict
  operation.
- No `runs/` path is in the curated commit-eligible file list.
- `git ls-files runs` returned empty output.
- No data, DB, SQLite, WAL, journal, parquet, arrow, feather, `.dbn`, `.zst`,
  log, cache, provider-response, materialized feature-value, materialized
  label-value, model, report-bundle, raw, canonical, factor, or label artifact
  is in the curated file list.
- Feature and label values created by the integration test were written only
  under pytest's temporary `ALPHA_DATA_ROOT`, outside the repository.
- The committed dry-run documentation is row-free and contains no raw rows,
  feature values, label values, provider responses, local registry contents, or
  local artifact paths.

## Scope / Safety Confirmation

- DAG metadata observed: `parallel_safe: false`, `must_run_alone: true`,
  `merge_group: diagnostics_and_packaging`.
- `ACTIVE_CAMPAIGN.md` was not written.
- No governance module was edited; governance objects are consumed through the
  existing FeatureRequest, LabelSpec, duplicate-exposure, label-leakage, and
  partition gates.
- The helper consumes only one accepted DatasetVersion handle at a time and uses
  canonical mapping loaders before materialization.
- The integration test uses `development_partition`; no locked-test partition
  use was introduced.
- Every feature value is produced by the existing feature engine with
  `available_ts`; every label value is produced by the existing label engine
  with `label_available_ts`.
- BBO missingness is surfaced in the row-free summary; synthetic dense-grid
  no-trade rows are validated and counted without being treated as trade bars.
- No external provider call, provider client import, raw-provider file read,
  broker/live/paper/order-routing/account scope, strategy/backtest/portfolio
  scope, production deployment, or destructive operation was introduced.
- No alpha, profitability, tradability, production-readiness, or prohibited MVP
  lifecycle claim was introduced.

## README Snapshot

`README.md` was updated per the FLF-P26 snapshot policy: progress through
FLF-P26, next phase FLF-P27, follow-on FLF-P28 and FLF-P30/FLF-P31 closeout,
the new dry-run doc and engine helper, and unchanged safety boundaries. The
update does not include generated run details, local artifact paths, alpha
claims, broker/live/paper/deployment behavior, or duplicated handoff content.

## Review Status

This YELLOW phase still requires fresh independent Claude review by Ralph's
review step. Codex did not call Claude, run reviewer, create `review.md`, create
`verdict.json`, mark the phase PASS, create a PR, merge, stage, commit, or push,
per executor instructions.
