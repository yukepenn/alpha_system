# FeatureSpec Draft Form

Use this form to draft feature-layer `FeatureSpec` metadata after a governed
`FeatureRequest` exists. The source of truth is `../FEATURE_CONTRACTS.md`; this
form does not redefine that contract.

## Governance Binding

- `governance_feature_request_id`: `<freq_... approved FeatureRequest>`
- `alpha_spec_id`: `<aspec_... reference used by the governed request>`
- FeatureRequest gate decision reference:
- DuplicateExposureReport reference:

## Feature Identity

- Feature id:
- Family:
- Human-readable name:
- Purpose as substrate metadata:

## FeatureInputSpec

- Canonical input view names:
- Canonical input fields:
- DatasetVersion id references:
- Partition scope:

Do not include raw provider fields or local file paths.

## TransformSpec

- Transform name:
- Parameters:
- Required primitives:
- Expected missing-value behavior:

## WindowSpec

- Window kind:
- Window length:
- Causality:
- Offline-only:
- Anchor:

Live-feature contracts must be causal. Centered or future windows must be
offline-only and cannot feed live features.

## NormalizationSpec

- Normalization name:
- Parameters:
- Fit partition policy:
- Locked-test contamination metadata, if any:

## Availability

- Availability assumptions:
- `available_ts` derivation rule:
- Expected quality flags:

Every emitted FeatureValueRecord must carry `available_ts`.

## Version And Store Notes

- Expected FeatureVersion derivation inputs:
- FeatureSetSpec membership:
- FeatureStore registry notes:
- Deprecation or equivalence notes:

This draft does not materialize values and does not state that values exist.
