# LabelSpec Contract

`ARGOV-P06` defines `LabelSpec`, the governance record for an explicit label
definition before any downstream study can use it.

`LabelSpec` is protocol metadata only. It describes a label horizon, path rules,
cost assumptions, target/stop rule metadata, availability time, and leakage
constraints. It does not materialize labels, compute label values, ingest real
data, assert label quality, assert predictive value, or make any alpha,
profitability, tradability, candidate, library-entry, or production-readiness
claim.

## Required Fields

Every `LabelSpec` must include the campaign-required fields:

- `label_spec_id`
- `horizon`
- `path_rules`
- `cost_model`
- `target_stop_rules`
- `availability_time`
- `forbidden_feature_overlap`
- `leakage_checks`

`label_spec_id` is a deterministic `lspec_...` governance ID generated from the
content fields. If `alpha_spec_id` is present, it is included in the content ID
and must be a well-formed `aspec_...` governance ID.

## Fail-Closed Validation

Validation uses the shared ARGOV-P02 primitives:

- `governance/ids.py` for typed deterministic IDs;
- `governance/serialization.py` for canonical JSON round trips;
- `governance/validation.py` for structured validation errors.

Missing, null, empty, unknown, malformed, or non-serializable fields raise
`GovernanceValidationError`. The validator does not coerce types, drop unknown
fields, or infer a clean leakage state.

`horizon` must be explicit. `availability_time` must be a timezone-aware
ISO-8601 timestamp so the label-leakage guard can compare feature information
times without ambiguity.

The metadata mappings `path_rules`, `cost_model`, `target_stop_rules`, and
`forbidden_feature_overlap` must be non-empty and explicit. Nested null, empty,
or placeholder values fail validation.

`leakage_checks` must be non-empty and must include:

- `label_as_feature`
- `availability_time`

These declarations are required because the object is not allowed to silently
omit either the label-as-feature guard or the no-lookahead availability-time
guard.

## Forbidden Feature Overlap

`forbidden_feature_overlap` declares references that cannot appear as requested
features for this label. The guard treats declared label references, aliases,
and transforms as blocking overlap when feature metadata matches them.

Examples of synthetic metadata keys are:

- `label_reference`
- `aliases`
- `transforms`

The structure is governance metadata only. It is not a computed label, not a
factor value, and not evidence that a label is useful.

## Round Trip

`LabelSpec.to_canonical_json()` serializes through the canonical governance JSON
primitive. `LabelSpec.from_canonical_json(...)` deserializes and validates the
payload again. Reordered mappings must round-trip to the same canonical content.
