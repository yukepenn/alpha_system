# Governance Integration: StudySpec Input Packs

`StudyInputPack` is an additive governance helper for packaging the handles a
future `StudySpec` references. It lives in
`alpha_system.governance.study_input_pack` and bundles:

- `feature_request_ids`: one or more `freq_` FeatureRequest handles.
- `label_spec_ids`: one or more `lspec_` LabelSpec handles.
- `alpha_spec_id`: one `aspec_` AlphaSpec handle.
- `dataset_scope`: the same kind of substantive, canonically serializable
  mapping expected by `StudySpec.dataset_scope`.

The pack is an input bundle only. It does not create a `StudySpec`, does not
run diagnostics, does not produce evidence, and does not change any lifecycle
state.

## Governance Reuse

The helper consumes existing governance APIs. ID handles are validated through
`alpha_system.governance.ids`, and callers that have resolved governance records
can ask the helper to validate them through the public `FeatureRequest`,
`LabelSpec`, `AlphaSpec`, and `StudySpec` validators.

The helper does not edit `StudySpec`, `FeatureRequest`, `LabelSpec`,
`AlphaSpec`, registries, promotion modules, duplicate-exposure guards, or label
leakage guards. It adds no field to `StudySpec` and does not introduce a
parallel study or experiment schema.

## Validation Posture

A pack fails closed when:

- a handle is malformed, unknown-prefix, or has the wrong expected prefix;
- a feature-request or label-spec handle list is empty;
- a feature-request or label-spec handle list contains duplicates;
- `dataset_scope` is empty, vague, null, or not canonical JSON-compatible.

`StudyInputPack` is immutable and hashable. Its public serialization uses the
same canonical JSON primitive used by the rest of governance.

## No-Claims Boundary

A pack is not a study result, not a diagnostic summary, not market evidence,
and not a promotion decision. It is only a deterministic list of governed input
references and dataset-scope metadata.

Per `docs/RESEARCH_INTERPRETATION_POLICY.md`, fixture templates and local
metadata must not be interpreted as alpha, profitability, robustness,
tradability, approval, production readiness, paper-trading readiness, live-use
readiness, broker execution readiness, or order-routing safety.

This phase adds no provider access, no raw or canonical data reads, no
materialized feature or label values, no strategy, no backtest, no portfolio
workflow, and no broker, paper, live, deployment, or order-routing behavior.
