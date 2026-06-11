# Core Pilot StudySpec Re-lock Contract

`FUTSUB-P27` re-issues only the Core Pilot StudySpec dataset-scope locks needed to open the bounded rerun gate for `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. The original accepted Core Pilot artifacts under `research/futures_core_alpha_pilot_v1/**` remain read-only inputs.

## What Is Held Fixed

For each re-locked StudySpec, these fields are copied from the original Core Pilot StudySpec without tuning or reinterpretation:

- `alpha_spec_id`
- top-level `label_spec_id`
- `split_protocol`
- `metrics`
- `cost_assumptions`
- `variant_budget`
- `locked_test_policy`
- `negative_controls`
- `stopping_rules`

The re-lock does not create new AlphaSpecs or LabelSpecs, does not edit accepted study parameters, and does not change promotion state.

## What Is Re-issued

Only `dataset_scope` is re-issued. The new scope binds the existing study to current full-substrate registry identities:

- accepted or accepted-with-warnings `dsv_...` DatasetVersions for 2019-2026;
- current exact `fver_...` FeatureVersion locks;
- current exact `lver_...` LabelVersion locks;
- StudyInputPack reference lists derived from those locks;
- old StudySpec to new StudySpec provenance.

Re-lock JSON is produced through `alpha_system.governance.study_spec.create_study_spec` and validates through `StudySpec.from_mapping`. The runtime smoke resolves the committed locks through `FeatureLabelPackResolver.resolve_feature_packs` and `resolve_label_packs`, and feature locks are also checked with `validate_feature_locks`.

## Why Originals Are Not Edited

The Core Pilot lesson is binding: AlphaSpec factor-input FeatureVersion IDs are provenance but are hashed into `alpha_spec_id`. Editing original AlphaSpecs, LabelSpecs, or StudySpecs in place would cascade identifiers and blur the audit trail. P27 therefore writes new value-free rerun artifacts under `research/futures_substrate_scaleout_v1/rerun/` and records the original-to-new mapping.

## Gap Policy

Resolver semantics remain exact-id and fail-closed. A materialized feature that is not governed by the StudySpec lock is invisible. A lock whose current registry record fails the runtime resolver is not substituted by family, feature name, feature set, or fuzzy matching.

P27 records two named gaps instead of fabricating locks:

- `regime`: current `liquidity_structure_range_contraction` records fail closed with `label_as_feature_input` on `session_label` role metadata.
- `bbo_tradability`: current `bbo_tradability_spread_zscore` records fail closed with `label_as_feature_input` on `session_label` role metadata.

P28 may rerun only prior-INCONCLUSIVE studies that have committed re-locked StudySpecs: the two VWAP/session studies and the two liquidity/PA studies. The cross-market prior-REJECT specs are re-locked as an audit baseline only.

## Safety Boundaries

This contract is research-only and value-free. It authorizes no paper trading, live trading, broker operation, order routing, deployment, capital allocation, alpha ideation, parameter tuning, registry mutation, value materialization, or profitability/tradability claim. Values, registries, manifests, Parquet files, SQLite files, and resolver scratch files stay local-only under `ALPHA_DATA_ROOT` or `/tmp`.
