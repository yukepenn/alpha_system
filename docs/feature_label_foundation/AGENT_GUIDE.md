# Feature/Label Foundation Agent Guide

Use this guide when an AI agent consumes the Feature/Label Foundation substrate.
It is intentionally short. For detailed researcher context, use `guide/`.

## Hard Rules

- Consume accepted DatasetVersions only.
- Resolve DatasetVersions through the Feature/Label consumption adapter, which
  wraps `resolve_dataset_version`.
- Reconstruct rows through canonical `from_mapping` loaders only.
- Use existing governance objects; do not define alternate FeatureRequest,
  LabelSpec, StudySpec, AlphaSpec, duplicate-exposure, or leakage schemas.
- Do not read raw provider files, provider responses, parquet, arrow, feather,
  DBN, Zstd, local registry DBs, or local data-root files directly.
- Do not call Databento, IBKR, brokers, live systems, paper systems, order
  routers, account APIs, or deployment tooling.
- Do not create strategy, backtest, portfolio, alpha-search, or trading scope.
- Do not make alpha, profitability, tradability, promotion, broker, paper,
  live, order-routing, deployment, or readiness claims.

## Required References

- Entry contract: `ENTRY_CONTRACT_CONSUMPTION.md`
- Dense-grid and BBO semantics: `DENSE_GRID_AND_BBO_SEMANTICS.md`
- Feature request gate: `FEATURE_REQUEST_GATE.md`
- Feature contracts: `FEATURE_CONTRACTS.md`
- Feature store and reports: `FEATURE_STORE.md`, `FEATURE_REPORTS.md`
- Label contracts: `LABEL_CONTRACTS.md`
- Label store and leakage audit: `LABEL_STORE.md`,
  `LABEL_LEAKAGE_AUDIT.md`
- StudySpec input packs: `governance_integration.md`
- Researcher guide: `guide/README.md`
- Templates: `templates/` and `../../templates/feature_label/`

## Consumption Flow

1. Start from a DatasetVersion id that is expected to be accepted.
2. Resolve it through `resolve_accepted_dataset_version(...)`.
3. Load rows through `CanonicalBarRecord.from_mapping`,
   `CanonicalBBORecord.from_mapping`, or `DenseGridBarRecord.from_mapping`.
4. For features, require an approved `freq_` FeatureRequest and a valid
   FeatureSpec with an explicit `available_ts` rule.
5. For labels, require a valid `lspec_` LabelSpec and a label contract with an
   explicit `label_available_ts` rule.
6. Preserve BBO quality flags and dense-grid no-trade markers.
7. Reference FeatureVersion and LabelVersion metadata through local-only stores.
8. Pass governed handles to a StudySpec input pack; do not copy governance
   schemas into the pack.

## Fail Closed

Stop and report the blocker when:

- the DatasetVersion is missing or not admissible;
- any row lacks required availability timestamps;
- a feature request lacks checked duplicate-exposure metadata;
- a FeatureSpec uses a centered or future window as a live feature;
- a label can be reached as a live feature;
- BBO missingness would be filled or hidden;
- a dense-grid no-trade row would be treated as a trade bar;
- a workflow asks to commit values, DBs, caches, logs, report bundles, provider
  payloads, or local data-root artifacts;
- a request asks for broker, paper, live, order, account, external provider,
  PR, merge, or deployment activity outside the phase authorization.

## Output Discipline

Docs and templates may be committed under the phase allowed paths. Runtime
state under `runs/**`, raw/canonical data, feature values, label values, local
registries, heavy artifacts, logs, and caches remain local-only.
