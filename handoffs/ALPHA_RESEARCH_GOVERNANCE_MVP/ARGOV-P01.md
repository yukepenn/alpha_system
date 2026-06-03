# ARGOV-P01 Handoff — Governance Package Skeleton and Canonical Naming

## Summary

Created the governance skeleton for `ALPHA_RESEARCH_GOVERNANCE_MVP`:

- Added an importable `alpha_system.governance` package with skeleton placeholder
  modules for IDs, serialization, validation, governance object families, canaries,
  registry, unsupported-claim guard, and reporting.
- Added `tests/unit/governance/test_package_skeleton.py`, an import smoke test for
  the governance package and documented placeholder modules.
- Added documented placeholder roots under `configs/governance/` and
  `templates/governance/`.
- Added `docs/governance/NAMING.md`, fixing the canonical object names from
  `campaign.yaml`, ID prefixes, module names, test names, docs/config/template
  naming, directory roots, and commit-eligible vs local-only artifact split.
- Updated `README.md` with the ARGOV-P01 snapshot and unchanged safety boundaries.

`tests/unit/governance/__init__.py` was not added because the existing `tests/unit/`
tree does not use package-style test directories.

## Naming Contract Snapshot

`docs/governance/NAMING.md` fixes these object names exactly as listed in
`campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/campaign.yaml`:

- `HypothesisCard`
- `AlphaSpec`
- `FeatureRequest`
- `LabelSpec`
- `StudySpec`
- `TrialLedgerRecord`
- `EvidenceBundle`
- `RejectedIdeaRecord`
- `PromotionDecision`
- `ReviewerVerdict`
- `NegativeControlResult`
- `AlphaBookRecord`

Canonical ID prefixes are `hyp`, `aspec`, `freq`, `lspec`, `sspec`, `trial`, `evb`,
`rej`, `prom`, `rver`, `nctrl`, and `abook`. The token format and any generation
behavior remain explicitly deferred to `ARGOV-P02`.

## Staged Files

Exact staged files after explicit staging:

- `README.md`
- `configs/governance/README.md`
- `docs/governance/NAMING.md`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P01.md`
- `src/alpha_system/governance/__init__.py`
- `src/alpha_system/governance/alpha_spec.py`
- `src/alpha_system/governance/canaries/__init__.py`
- `src/alpha_system/governance/claims.py`
- `src/alpha_system/governance/evidence_bundle.py`
- `src/alpha_system/governance/feature_request.py`
- `src/alpha_system/governance/hypothesis_card.py`
- `src/alpha_system/governance/ids.py`
- `src/alpha_system/governance/label_spec.py`
- `src/alpha_system/governance/promotion.py`
- `src/alpha_system/governance/registry.py`
- `src/alpha_system/governance/rejected_idea.py`
- `src/alpha_system/governance/report.py`
- `src/alpha_system/governance/reviewer_verdict.py`
- `src/alpha_system/governance/serialization.py`
- `src/alpha_system/governance/study_spec.py`
- `src/alpha_system/governance/trial_ledger.py`
- `src/alpha_system/governance/validation.py`
- `templates/governance/README.md`
- `tests/unit/governance/test_package_skeleton.py`

No `runs/**` path is staged.

## Validation Results

- `git status --short` — succeeded. Before staging, output showed only allowed
  ARGOV-P01 paths:
  - `M README.md`
  - `?? configs/governance/`
  - `?? docs/governance/NAMING.md`
  - `?? src/alpha_system/governance/`
  - `?? templates/`
  - `?? tests/unit/governance/`
- `python -c "import alpha_system.governance"` — failed in this executor shell with
  `ModuleNotFoundError: No module named 'alpha_system'`. The bare `/usr/bin/python`
  environment does not have the repository `src/` layout on `sys.path`, and
  `alpha-system` is not installed in the local interpreter. This is an environment
  import-path issue, not a package skeleton import failure.
- `PYTHONPATH=src python -c "import alpha_system.governance"` — succeeded. This
  confirms the package skeleton imports cleanly when the repo `src/` layout is on
  `sys.path`.
- `python tools/verify.py --smoke` — succeeded with exit 0.
- `python -m pytest tests/unit/governance -q` — succeeded:

```text
.                                                                        [100%]
1 passed in 0.01s
```

- `test -f docs/governance/NAMING.md` — succeeded.
- `test -f src/alpha_system/governance/__init__.py` — succeeded.
- `test -d configs/governance` — succeeded.
- `test -d templates/governance` — succeeded.
- `git ls-files runs` — succeeded with empty output.
- `find data -type f ! -name README.md ! -name ".gitkeep" -print` — succeeded with
  empty output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` — succeeded
  with empty output.
- `find artifacts -type f -size +1M -print` — succeeded with empty output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` — succeeded
  with empty output.
- `python tools/hooks/canary_runner.py` — succeeded:

```text
PASS forbidden_git_add_dot
PASS policy_doc_mentions_forbidden_command
PASS forbidden_test_tamper
PASS forbidden_secret
PASS forbidden_large_binary
PASS forbidden_destructive_op
PASS forbidden_boundary_import
PASS forbidden_raw_data_commit
PASS forbidden_cache_data_commit
PASS forbidden_local_artifacts
PASS forbidden_scope_drift
PASS generated_scaffold_allowed
All Frontier canaries passed.
```

Skipped checks: none. The exact bare import command was run and failed for the
environment reason recorded above.

## Artifact Policy

- `git ls-files runs` returned empty.
- `git diff --cached --name-only` contains no `runs/` path.
- Local artifact audits for `data`, `metadata`, oversized files under `artifacts`,
  and Parquet files outside `tests/fixtures` returned empty output.
- Generated `__pycache__` directories created by the import/test checks under the new
  governance paths were removed before staging.
- No raw data, canonical data, factor data, label data, cache data, local DB file,
  log, heavy artifact, Parquet, Arrow, Feather, model binary, or run artifact was
  staged.
- No run-local `handoff.md`, `review.md`, `verdict.json`, `checks.json`, or
  `repair_attempts/` artifact was created or staged.

## Staging Discipline

- Explicit staging only.
- The staged set was built with explicit file paths.
- `git add .` was not used.
- `git add -A` was not used.
- No force push was performed.
- No PR was created.
- No merge was performed.

## Scope Confirmation

- No object logic was introduced.
- No ID generation, serialization behavior, validation behavior, hashing, or
  fail-closed logic was introduced.
- No object fields or classes were defined.
- No registry or persistence integration was introduced.
- No CLI, report builder, template content beyond documented placeholder roots, or
  canary harness was introduced.
- No unrelated `src/alpha_system` subpackage was modified.
- No tests outside `tests/unit/governance/` were added, removed, skipped, weakened,
  or relaxed.
- No broker, live, paper, order-routing, real-data-ingestion, alpha-search,
  production deployment, L2 replay, ML/DL expansion, strategy optimization, or
  portfolio allocation scope was introduced.
- No alpha, profitability, tradability, paper-readiness, live-readiness,
  broker-readiness, capital-allocation, or production-readiness claim was introduced.

## Review Boundary

No Claude review was run by Codex. No `review.md` or `verdict.json` was created.
Ralph owns validation orchestration, independent review routing, verdict parsing,
PR creation, CI, merge gates, semantic done-checks, and phase PASS marking.
