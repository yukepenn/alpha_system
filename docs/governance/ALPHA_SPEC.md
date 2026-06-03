# AlphaSpec Contract

`ARGOV-P03` defines `AlphaSpec`, the pre-registration record that must validate
before implementation work can be allowed for a registered research idea.

`AlphaSpec` is governance metadata only. It does not search for alpha, ingest
real data, compute factors, run diagnostics, approve implementation by itself,
create candidate status, add anything to a factor library, validate a result,
or imply profitability, tradability, paper readiness, live readiness, capital
allocation, production readiness, or deployment approval.

## Required Fields

Every `AlphaSpec` must include these fields from the campaign contract:

- `alpha_spec_id`
- `hypothesis_id`
- `target_instruments`
- `data_assumptions`
- `factor_inputs`
- `label_references`
- `exclusion_rules`
- `timestamp_assumptions`
- `cost_assumptions`
- `expected_failure_modes`
- `promotion_criteria`
- `created_by`
- `created_at`

`alpha_spec_id` must be a deterministic `aspec_...` governance ID generated
from the complete pre-registration content. `hypothesis_id` must be a
well-formed `HypothesisCard` reference, and each `label_references` entry must
be a well-formed `LabelSpec` reference. This phase records those references
only; it does not resolve or validate the referenced objects.

## Fail-Closed Behavior

Validation uses the ARGOV-P02 primitives for deterministic IDs, canonical JSON
serialization, and structured fail-closed validation. The validator rejects:

- non-mapping roots;
- missing or null required fields;
- fields with undeclared names;
- malformed governance IDs;
- `alpha_spec_id` values that do not match deterministic record content;
- empty strings, empty lists, or empty assumption mappings;
- vague substantive entries such as `TBD`, `unknown`, or `placeholder`;
- terse substantive rules and assumptions that do not describe the constraint;
- malformed or timezone-free `created_at` timestamps;
- content that cannot be serialized as strict canonical JSON.

Valid records can be round-tripped through canonical JSON with stable ordering
and without implicit defaults, field dropping, or type coercion.

## No-Code Gate

`validate_no_code_gate(...)` is the pure precondition for the
`REGISTERED -> IMPLEMENTATION_ALLOWED` transition. It blocks the transition when
there is no `AlphaSpec` or when the supplied `AlphaSpec` fails validation. It
returns the validated `AlphaSpec` when the precondition is satisfied.

The gate executes no implementation, reads no data, computes no factor values,
runs no study, creates no candidate status, and creates no factor-library entry.
Later phases add the remaining governance objects and checks that can also
block future lifecycle transitions.

## Template

Use `templates/governance/alpha_spec.template.yaml` as the human-readable
starting point for future pre-registration records. The template is not a
validated object until every placeholder is replaced with explicit,
substantive governance metadata and a deterministic `alpha_spec_id`.
