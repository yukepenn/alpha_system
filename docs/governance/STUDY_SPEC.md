# StudySpec Contract

`ARGOV-P07` defines `StudySpec`, the governance record that must exist before
diagnostics may be allowed.

`StudySpec` is protocol metadata only. It declares how a future study is allowed
to be run: dataset scope, split protocol, metrics, cost assumptions, variant
budget, locked-test policy, required negative controls, and stopping rules. It
does not run diagnostics, compute factors, materialize labels, ingest real data,
assert that diagnostics passed, or make any alpha, profitability, tradability,
candidate, library-entry, or production-readiness claim.

## Required Fields

Every `StudySpec` must include these fields:

- `study_spec_id`
- `alpha_spec_id`
- `label_spec_id`
- `dataset_scope`
- `split_protocol`
- `metrics`
- `cost_assumptions`
- `variant_budget`
- `locked_test_policy`
- `negative_controls`
- `stopping_rules`

`study_spec_id` is a deterministic `sspec_...` governance ID generated from the
remaining fields. `alpha_spec_id` must be a well-formed `aspec_...` ID, and
`label_spec_id` must be a well-formed `lspec_...` ID. This phase validates ID
shape and kind; registry existence checks are later scope.

## Fail-Closed Validation

Validation uses the shared ARGOV-P02 primitives:

- `governance/ids.py` for typed deterministic IDs;
- `governance/serialization.py` for canonical JSON round trips;
- `governance/validation.py` for structured validation errors.

Missing, null, empty, unknown, malformed, or non-serializable fields raise
`GovernanceValidationError`. The validator does not coerce types, drop unknown
fields, infer defaults, or silently accept an unbounded study.

`dataset_scope`, `split_protocol`, `cost_assumptions`, and
`locked_test_policy` must be non-empty explicit mappings. `metrics`,
`negative_controls`, and `stopping_rules` must be non-empty lists of explicit
strings.

`variant_budget` must be an exact positive integer cap. Strings such as
`unbounded` or `unlimited`, booleans, nulls, zero, and negative values fail
closed.

`locked_test_policy` must explicitly declare OOS or locked-test handling before
diagnostics. The field is consumed by later ledger and promotion phases; this
phase only requires the declaration.

`negative_controls` declares the controls a later study must run, such as random
target, permuted labels, future-shift, and optimistic-fill controls. The
catalog and harness are later phases.

## Diagnostics Gate

`validate_diagnostics_gate(...)` and `assert_diagnostics_allowed(...)` enforce:

```text
IMPLEMENTED -> DIAGNOSTICS_ALLOWED requires a valid StudySpec
```

Passing `None`, an invalid mapping, or a different transition raises
`GovernanceValidationError`. There is no permissive boolean result to coerce
into allowed.

## Round Trip

`StudySpec.to_canonical_json()` serializes through the canonical governance JSON
primitive. `StudySpec.from_canonical_json(...)` deserializes and validates the
payload again. Reordered mappings must round-trip to the same canonical content.
