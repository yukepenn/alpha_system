# FeatureRequest Contract

`ARGOV-P05` defines `FeatureRequest`, the governance record for proposed
feature or factor inputs before any implementation work.

`FeatureRequest` is metadata only. It does not compute factor values, ingest real
data, add a factor-library entry, grant candidate status, or permit
implementation. Approval metadata on the object is not a lifecycle transition.

## Required Fields

Every `FeatureRequest` must include these fields from the campaign contract:

- `feature_request_id`
- `alpha_spec_id`
- `requested_inputs`
- `formula_sketch`
- `availability_assumptions`
- `duplicate_or_equivalent_exposure_notes`
- `data_requirements`
- `approval_status`

`feature_request_id` is a deterministic `freq_...` governance ID generated from
the remaining required fields. `alpha_spec_id` must be a well-formed `aspec_...`
governance ID.

## Fail-Closed Validation

Validation uses the shared ARGOV-P02 primitives:

- `governance/ids.py` for typed deterministic IDs;
- `governance/serialization.py` for canonical JSON round trips;
- `governance/validation.py` for structured validation errors.

Missing, null, empty, unknown, malformed, or non-serializable fields raise
`GovernanceValidationError`. Required collection and mapping fields must contain
explicit metadata. The validator does not coerce types, drop unknown fields, or
silently fill in clean duplicate-exposure notes.

`approval_status` is constrained to:

- `PENDING`
- `BLOCKED_DUPLICATE`
- `NEEDS_REVIEW`
- `APPROVED`

The only constructor default is `PENDING`. The object never auto-advances to
`APPROVED`. A request with a blocking duplicate finding cannot validate as
`APPROVED`, and a request whose registry check was unavailable cannot validate
as `APPROVED`.

## Duplicate-Exposure Notes

`duplicate_or_equivalent_exposure_notes` must be populated with structured
metadata from the duplicate-exposure guard:

- `guard: duplicate_exposure`
- `checked: true`
- `registry_status`
- `registry_entries_checked`
- `findings`
- `summary`

This prevents an unchecked request from being treated as clean. A registry check
may produce no findings, warning findings, blocking findings, or an unavailable
registry status, but the notes must make that state explicit.

## Boundary

A `FeatureRequest` only records requested inputs and duplicate-exposure guard
metadata. It is not implementation permission, validation status, evidence, a
factor registration, or a trading decision.
