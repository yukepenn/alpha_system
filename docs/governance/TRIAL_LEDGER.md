# TrialLedger

`ARGOV-P08` adds `TrialLedgerRecord` metadata for recording research attempts
and variant accounting. The ledger is governance machinery only. It records what
was attempted, including failed and abandoned attempts, and it does not run
studies, backtests, diagnostics, factor computations, label computations, or any
market-data workflow.

The invariant installed by this phase is:

```text
No TrialLedger -> no promotion.
```

A `COMPLETED` status only means the attempt produced an outcome record. It is not
a quality judgment and does not imply alpha validity, profitability,
tradability, candidate status, validation, factor-library eligibility, or
production readiness.

## Record Fields

`TrialLedgerRecord` carries exactly these fields:

| Field | Meaning |
| --- | --- |
| `trial_id` | Deterministic `TrialLedgerRecord` governance ID with the `trial` prefix, generated from all non-ID content fields. |
| `alpha_spec_id` | Valid `AlphaSpec` ID with the `aspec` prefix. |
| `study_spec_id` | Valid `StudySpec` ID with the `sspec` prefix. |
| `run_id` | Opaque diagnostics or study run reference. It is not a filesystem path and must not point into `runs/**`. |
| `variant_id` | Explicit variant identifier within the study. |
| `status` | Closed `TrialStatus` enum: `PLANNED`, `RUNNING`, `COMPLETED`, `FAILED`, or `ABANDONED`. |
| `parameters` | Non-empty mapping of explicit trial parameters. |
| `metrics_summary` | Explicit mapping of summary metrics. It may be empty for failed or abandoned attempts; metrics are not fabricated. |
| `failure_reason` | Required and substantive for `FAILED` or `ABANDONED`; empty or null for non-failed statuses. |
| `oos_touched_flag` | Strict boolean recording out-of-sample contact metadata. |
| `locked_test_contamination_flag` | Strict boolean recording locked-test contamination metadata. |
| `code_hash` | Lowercase SHA-256 content hash string. |
| `config_hash` | Lowercase SHA-256 content hash string. |

Validation is fail-closed. Missing fields, unknown fields, malformed governance
IDs, non-substantive parameters, invalid status values, non-boolean
contamination flags, invalid hashes, non-canonical values, and mismatched
deterministic IDs raise `GovernanceValidationError`.

## Serialization

`TrialLedgerRecord.to_dict()` returns a strict JSON-compatible representation in
the campaign-required field order. `to_canonical_json()` uses the shared
canonical serialization primitive, and `from_canonical_json()` deserializes then
validates the record. The `trial_id` is recomputed during validation and must
match the record content.

## Failed-Run Visibility

Failed and abandoned attempts are first-class records. The status enum includes
`FAILED` and `ABANDONED`, and those statuses require a substantive
`failure_reason`. Empty `metrics_summary` is allowed for these outcomes so the
ledger can record the attempt without fabricating metrics.

The accounting API has no parameter or default that excludes failed or abandoned
records. Every matching record for a `study_spec_id` contributes to:

- `attempt_count`
- `variant_attempt_count`
- `variant_counts`
- `status_counts`
- failed and abandoned counts

An empty matching ledger for a study raises a validation error instead of
returning a clean zero-count summary.

## Variant Accounting

`account_trial_ledger(records, study_spec_id=..., variant_budget=...)` validates
each supplied record, selects records for the requested `study_spec_id`, and
returns `TrialLedgerAccounting` metadata.

The accounting result includes:

- all attempt counts for the study;
- distinct observed variant IDs and per-variant attempt counts;
- closed status counts;
- failed and abandoned counts;
- OOS-touched and locked-test contamination counts;
- a `StudyBudgetCheck` from `evaluate_variant_budget(...)`.

The observed-variant budget check uses the existing `StudySpec` budget
accounting rather than re-implementing the budget rules. The helper is metadata
only and does not execute variants or enforce a promotion decision.

## Contamination Flags

`oos_touched_flag` and `locked_test_contamination_flag` are strict booleans on
each record. Accounting surfaces both counts and `any_*` flags so later
promotion-gate phases can block on recorded OOS contact or locked-test
contamination. The TrialLedger phase records the metadata; it does not decide
promotion eligibility.
