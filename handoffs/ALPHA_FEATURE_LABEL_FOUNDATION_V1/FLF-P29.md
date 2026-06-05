# FLF-P29 Handoff - Docs, Templates, and Agent Guide

## Summary

Implemented the FLF-P29 documentation-only scope for the Feature/Label
Foundation.

This phase adds:

- a durable researcher guide under `docs/feature_label_foundation/guide/`;
- a concise AI-agent operating guide at
  `docs/feature_label_foundation/AGENT_GUIDE.md`;
- researcher-facing FeatureRequest, FeatureSpec, and LabelSpec forms under
  `docs/feature_label_foundation/templates/`;
- reusable YAML templates under `templates/feature_label/`;
- a compact README snapshot update for the post-FLF-P29 repository state.

The docs point to existing Feature/Label and governance contract pages instead
of duplicating those contracts. The templates reference governed `freq_`,
`lspec_`, `aspec_`, and StudySpec handles and do not define alternate
governance schemas or id prefixes.

## Staging / Curated File List

Staged by Codex: none. The executor prompt explicitly prohibited `git add`,
`git commit`, `git push`, `git status`, and `git diff`; all changes are left
unstaged for Ralph.

Curated commit-eligible files for Ralph to stage explicitly by path:

- `docs/feature_label_foundation/guide/README.md`
- `docs/feature_label_foundation/guide/dataset_entry.md`
- `docs/feature_label_foundation/guide/request_to_study.md`
- `docs/feature_label_foundation/guide/safety_semantics.md`
- `docs/feature_label_foundation/AGENT_GUIDE.md`
- `docs/feature_label_foundation/templates/README.md`
- `docs/feature_label_foundation/templates/feature_request.md`
- `docs/feature_label_foundation/templates/feature_spec.md`
- `docs/feature_label_foundation/templates/label_spec.md`
- `templates/feature_label/README.md`
- `templates/feature_label/feature_request.template.yaml`
- `templates/feature_label/feature_spec.template.yaml`
- `templates/feature_label/label_spec.template.yaml`
- `README.md`
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P29.md`

No review artifacts were created by Codex because the executor prompt forbade
calling Claude, running reviewer, and creating `review.md` or `verdict.json`.
GREEN review, if any, remains Ralph-owned.

## Validation

- `git status --short` - skipped; explicitly forbidden by the executor prompt.
- `test -f docs/feature_label_foundation/AGENT_GUIDE.md` - passed.
- `test -f README.md` - passed.
- `ls docs/feature_label_foundation/guide` - passed; listed
  `README.md`, `dataset_entry.md`, `request_to_study.md`, and
  `safety_semantics.md`.
- `ls docs/feature_label_foundation/templates` - passed; listed
  `README.md`, `feature_request.md`, `feature_spec.md`, and `label_spec.md`.
- `ls templates/feature_label` - passed; listed `README.md`,
  `feature_request.template.yaml`, `feature_spec.template.yaml`, and
  `label_spec.template.yaml`.
- `python tools/verify.py --smoke` - passed with no output.
- `git ls-files runs` - passed; empty output.
- No-claims / scope heuristic scan:
  `grep -REn -i "alpha[- ]?validated|profitable|tradable|production[- ]?ready|live[- ]?ready|strategy[- ]?ready" docs/feature_label_foundation/guide docs/feature_label_foundation/AGENT_GUIDE.md docs/feature_label_foundation/templates templates/feature_label README.md | grep -vi "future\|non-MVP\|not\b\|never\|prohibited" || echo "no unsupported alpha/tradability/readiness claim found in authored docs"` -
  passed with `no unsupported alpha/tradability/readiness claim found in
  authored docs`.
- Artifact audit:
  `git ls-files | grep -E '\.(parquet|arrow|feather|dbn|zst|sqlite|sqlite3|db|wal|log)$' | grep -v '^tests/fixtures/' || echo "no committed heavy/db/log artifacts"` -
  passed with `no committed heavy/db/log artifacts`.
- `git diff --cached --name-only` - skipped because the executor prompt
  explicitly forbade `git diff`. Codex performed no staging, so there is no
  Codex-staged set to inspect.

## Artifact Policy

- No `runs/**` path was created for commit eligibility or staged by Codex.
- `git ls-files runs` returned empty output.
- The run-local phase directory remains local-only; Codex did not create
  run-local `handoff.md`, `review.md`, `verdict.json`, checks, or repair
  artifacts.
- No raw, canonical, factor, feature-value, label-value, provider-response,
  parquet, arrow, feather, DBN, Zstd, SQLite, local registry, log, cache, model,
  report bundle, or heavy artifact was added for commit eligibility.
- The YAML files under `templates/feature_label/` are placeholder templates
  only. They contain no real ids, no real data, no provider responses, and no
  materialized feature or label values.

## README Snapshot

README snapshot policy was applied compactly. `README.md` now reflects that,
after this phase merges, campaign progress is `FLF-P00` through `FLF-P29`,
the durable Feature/Label researcher guide, agent guide, and request templates
exist, and the next phase is FLF-P30 End-to-End Feature/Label Dry Run. It adds
no run details, local artifact paths, duplicated handoff content, provider
activity, trading behavior, or result claims.

## DAG / Scope

- FLF-P29 DAG metadata was treated as parallel-safe in merge group
  `diagnostics_and_packaging`, with disjoint commit-eligible docs/templates
  paths.
- The only shared-root file edited was the compact `README.md` snapshot.
- `ACTIVE_CAMPAIGN.md` was not edited.
- `docs/AI_AGENT_GUIDE.md` and `docs/CLI_REFERENCE.md` were not edited.
- No `src/**`, `tests/**`, shared feature/label core, or governance module was
  edited.
- Serial merge ordering, PR creation, CI waiting, merge-gate evaluation,
  review, verdict parsing, and done-check remain Ralph-owned.

## Forbidden Scope Confirmation

- No live trading, paper trading, broker operation, account operation, order
  routing, production deployment, PR creation, merge, or destructive cleanup was
  performed.
- No Databento, IBKR, external provider, raw-provider, or broker client was
  imported or called.
- No raw provider file, provider response, local data-root file, materialized
  feature value, materialized label value, local registry DB, report bundle,
  cache, log, or heavy artifact was added.
- Docs and templates preserve accepted-DatasetVersion-only framing, canonical
  `from_mapping` loader consumption, `available_ts` and `label_available_ts`
  requirements, no-label-as-feature rules, no future/centered live-window
  rules, BBO missingness flagging, dense-grid no-trade semantics, and
  local-only FeatureStore/LabelStore posture.
- No alpha, profitability, tradability, strategy, backtest, portfolio, broker,
  paper, live, order-routing, deployment, promotion, or readiness claim was
  introduced.
