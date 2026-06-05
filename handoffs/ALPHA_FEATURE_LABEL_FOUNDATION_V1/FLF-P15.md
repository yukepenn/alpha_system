# FLF-P15 Handoff — Feature Quality and Coverage Reports

## Change Summary

Implemented the FLF-P15 descriptive evidence layer for registered feature
values.

The phase adds:

- `alpha_system.features.reports.FeatureQualityReport`, an immutable report over
  FLF-P14 `FeatureRegistryRecord` metadata and local FLF-P13 materialized JSONL
  values. It records null / NaN-like rates, constant-output detection,
  `missing_bbo` / `bbo_quarantined` exposure, `available_ts` defects, registry
  span consistency, and duplicate / equivalent exposure status with separate
  `blocking` and `non_blocking` finding partitions.
- `alpha_system.features.reports.FeatureCoverageReport`, an immutable coverage
  report by symbol, session, and partition. It maps partition semantics to
  development / validation / locked-test-candidate roles, blocks undocumented
  expected coverage gaps, and records documented gaps as non-blocking evidence.
- `alpha_system.reports.feature_card.FeatureCard`, a plain-text / structured
  renderer for quality, coverage, and duplicate / equivalent exposure evidence.
  The renderer validates output through the existing prohibited-claim checker.
- Focused synthetic unit tests for fail-closed `available_ts`, undocumented
  coverage gaps, missing-BBO exposure, equivalent exposure visibility, and card
  claim-language exclusions.
- Durable docs at `docs/feature_label_foundation/FEATURE_REPORTS.md` and a
  compact README snapshot update marking FLF-P15 complete after merge.

No feature values, report bundles, local registries, DBs, raw/canonical data, or
provider artifacts were created for commit.

## Staging / Curated File List

Staged by Codex: none. The executor prompt explicitly prohibited `git add`,
`git commit`, `git push`, `git status`, and `git diff`; all changes are left
unstaged for Ralph.

Curated files for Ralph to stage by explicit path:

- `src/alpha_system/features/reports.py`
- `src/alpha_system/reports/feature_card.py`
- `tests/unit/features/test_feature_reports.py`
- `tests/unit/reports/test_feature_card.py`
- `docs/feature_label_foundation/FEATURE_REPORTS.md`
- `README.md`
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P15.md`

No review artifacts were created by Codex because the executor prompt explicitly
forbade calling Claude, running reviewer, and creating `review.md` or
`verdict.json`. YELLOW review remains Ralph-owned.

## Validation Results

- `git status --short`: not run; explicitly forbidden by executor prompt.
- `python -c "import alpha_system.features.reports"`: failed with
  `ModuleNotFoundError: No module named 'alpha_system'` because bare
  `python -c` does not put `src/` on `PYTHONPATH` in this checkout.
- `python -c "import alpha_system.reports.feature_card"`: failed with
  `ModuleNotFoundError: No module named 'alpha_system'` for the same bare
  `python -c` environment reason.
- `PYTHONPATH=src python -c "import alpha_system.features.reports"`: passed.
- `PYTHONPATH=src python -c "import alpha_system.reports.feature_card"`: passed.
- `python tools/verify.py --smoke`: passed.
- `python -m pytest tests/unit/features/test_feature_reports.py tests/unit/reports/test_feature_card.py -q`:
  passed, 4 tests.
- `python -m pytest tests/unit/features tests/unit/reports -q`: passed, 102 tests.
- `test -f docs/feature_label_foundation/FEATURE_REPORTS.md`: passed.
- `python tools/hooks/canary_runner.py`: passed; all Frontier canaries passed.
- `git ls-files runs`: passed; output empty.
- `PYTHONPATH=src python -m ruff check src/alpha_system/features/reports.py src/alpha_system/reports/feature_card.py tests/unit/features/test_feature_reports.py tests/unit/reports/test_feature_card.py`:
  passed.
- `find . -path './.git' -prune -o \( -name '*.sqlite' -o -name '*.sqlite3' -o -name '*.db' -o -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' -o -name '*.dbn' -o -name '*.zst' -o -name '*.wal' -o -name '*.journal' \) -print`:
  passed; output empty.

## Artifact Policy Confirmation

- No `runs/**` files were created, staged, or committed by Codex.
- The run-local `runs/<run_id>/phases/FLF-P15/handoff.md`, `review.md`,
  `verdict.json`, checks, and repair artifacts were not created by Codex.
- `git ls-files runs` returned empty.
- No DB, SQLite, WAL, journal, parquet, arrow, feather, `.dbn`, `.zst`, raw,
  canonical, cache, log, provider-response, feature-value, label-value, report
  bundle, or heavy artifact path is in the curated file list.
- Local artifact scan for common forbidden data/DB/heavy suffixes returned
  empty.
- `git diff --cached --name-only` was not run because the executor prompt
  forbade `git diff`; Codex performed no staging, so there is no Codex-staged
  set to inspect.
- Explicit staging only is confirmed for the Ralph driver: the curated file list
  above contains no `runs/` path.

## DAG / Scope Confirmation

- FLF-P15 is `parallel_safe=false`, `must_run_alone=true`, merge group
  `feature_integration`; this phase was treated as run-alone.
- `ACTIVE_CAMPAIGN.md` was not edited.
- No governance modules, FeatureStore / FeatureRegistry core modules,
  feature-family modules, materialization engine code, labels, CLI, consumption
  layers, or forbidden paths were edited.
- Governance objects and guards were consumed, not duplicated:
  `FeatureRegistryRecord`, `FeatureSpec`, `FeatureVersion`,
  `FeatureValueRecord` JSON payloads, `FeatureLineageRecord`,
  `DuplicateExposureReport`, and `EquivalentFeatureGroup` are consumed from the
  existing feature/governance modules.
- Reports read only local materialized JSONL values under `ALPHA_DATA_ROOT` (or
  an explicitly supplied local root in tests). They do not read raw provider
  files, parquet/arrow/feather/dbn/zst files, provider responses, or raw
  canonical data, and they do not re-materialize values.
- No external provider call, broker/live/paper/order/account behavior, PR
  creation, merge, deployment, destructive cleanup, or reviewer invocation was
  performed.
- No alpha, profitability, tradability, IC, strategy, backtest, portfolio,
  broker, live, paper, deployment, or production-readiness claim was introduced.

## Review Status

Fresh Claude Opus review is required for this YELLOW phase, but Codex did not
call Claude or create review artifacts because the executor prompt forbade those
actions. Ralph owns the review, verdict parsing, staging, commit, PR, CI, merge
gate, and semantic done-check.
