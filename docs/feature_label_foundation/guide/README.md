# Feature/Label Foundation Researcher Guide

This guide is the durable entry point for researchers using the
Feature/Label Foundation substrate. It explains how to move from an accepted
DatasetVersion to governed feature and label references that a future
`StudySpec` can consume.

The source-of-truth contract docs remain in the surrounding
`docs/feature_label_foundation/` directory and in `docs/governance/`. This guide
links to those contracts instead of restating every field.

## Use This First

Read the pages in this order:

1. `dataset_entry.md` - the accepted-DatasetVersion entry contract and the
   only sanctioned loading path.
2. `request_to_study.md` - the FeatureRequest, FeatureSpec, LabelSpec,
   FeatureVersion, LabelVersion, and StudySpec input flow.
3. `safety_semantics.md` - no-lookahead, label availability, BBO missingness,
   dense-grid no-trade semantics, and local-only stores.

Use `../AGENT_GUIDE.md` when an AI agent needs a concise operating checklist.
Use `../templates/` for researcher-facing request forms and
`../../../templates/feature_label/` for reusable YAML templates.

## Operating Posture

The substrate consumes accepted DatasetVersions, creates governed feature and
label metadata, and records local-only materialization evidence. It does not
conduct alpha search, run strategies, run backtests, build portfolios, call
external providers, or operate broker, paper, live, account, order-routing, or
deployment systems.

The required framing is:

- A feature is not alpha.
- A label is not alpha.
- A FeatureStore is not a factor library.
- A materialized FeatureSet is not a promoted candidate.
- A diagnostic report is not a research verdict.
- `READY_FOR_STUDY` means a governed study may reference the substrate object;
  it is not a result claim.

## Authoritative Contract Links

- Entry contract:
  `../ENTRY_CONTRACT_CONSUMPTION.md` and
  `../../FEATURE_LABEL_FOUNDATION_ENTRY_CONTRACT.md`
- Canonical input views: `../INPUT_VIEWS.md`
- Dense-grid and BBO semantics: `../DENSE_GRID_AND_BBO_SEMANTICS.md`
- FeatureRequest gate: `../FEATURE_REQUEST_GATE.md`
- Feature contracts: `../FEATURE_CONTRACTS.md`
- Feature materialization and store: `../FEATURE_MATERIALIZATION.md` and
  `../FEATURE_STORE.md`
- Feature reports: `../FEATURE_REPORTS.md`
- Label contracts: `../LABEL_CONTRACTS.md`
- Label materialization, store, and leakage audit:
  `../LABEL_MATERIALIZATION.md`, `../LABEL_STORE.md`, and
  `../LABEL_LEAKAGE_AUDIT.md`
- StudySpec input packs: `../governance_integration.md`
- Governance source of truth:
  `../../governance/FEATURE_REQUEST.md`,
  `../../governance/LABEL_SPEC.md`,
  `../../governance/STUDY_SPEC.md`, and
  `../../governance/ALPHA_SPEC.md`

## Researcher Checklist

Before requesting or consuming substrate objects, confirm:

- the input is an accepted DatasetVersion resolved through the sanctioned
  adapter;
- canonical rows are reconstructed through `from_mapping` loaders, not raw
  provider files;
- every requested feature has a governed `freq_` FeatureRequest;
- every feature contract states an `available_ts` derivation rule;
- every requested label has a governed `lspec_` LabelSpec;
- every label contract states a `label_available_ts` derivation rule;
- no label value, alias, or version is reachable as a live feature;
- BBO missingness and dense-grid no-trade rows stay explicit;
- FeatureStore and LabelStore outputs remain local-only;
- a future `StudySpec` consumes handles, not copied schema definitions.
