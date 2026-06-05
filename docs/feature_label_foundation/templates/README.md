# Feature/Label Request Templates

These researcher-facing templates help authors request governed feature and
label substrate objects. They consume the existing governance contracts; they do
not replace or redefine those contracts.

Authoritative contracts:

- `../../governance/FEATURE_REQUEST.md`
- `../../governance/LABEL_SPEC.md`
- `../../governance/STUDY_SPEC.md`
- `../../governance/ALPHA_SPEC.md`
- `../FEATURE_REQUEST_GATE.md`
- `../FEATURE_CONTRACTS.md`
- `../LABEL_CONTRACTS.md`

Reusable YAML versions live under `../../../templates/feature_label/`.

## Template Set

- `feature_request.md` - request a governed `FeatureRequest` with a `freq_`
  handle and duplicate-exposure guard notes.
- `feature_spec.md` - draft feature-layer `FeatureSpec` metadata bound to an
  approved `freq_` handle.
- `label_spec.md` - draft or request a governed `LabelSpec` with an `lspec_`
  handle and leakage metadata.

## Guardrails

Use placeholders until the corresponding governance object exists. Do not use
these templates to:

- bypass governance validators;
- create alternate id prefixes;
- infer approval or lifecycle transitions;
- copy FeatureRequest or LabelSpec schemas into StudySpec inputs;
- request raw-provider access or local data-root reads;
- request materialized value commits;
- make research-result, trading, broker, paper, live, order-routing, or
  deployment claims.
