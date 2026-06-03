# Negative Controls

`ARGOV-P13` defines the governance negative-control catalog and the
`NegativeControlResult` record. `ARGOV-P14` adds a tiny executable synthetic
harness for the `future_shift`, `permuted_labels`, and `optimistic_fill`
controls. The catalog and harness do not ingest real data, compute factors,
materialize labels, run real studies, route orders, or make any alpha,
profitability, tradability, capital-allocation, live-readiness, or
production-readiness claim.

Negative controls validate guard behavior only. A passing negative control means
the relevant guard rejected or flagged a known-bad injected fault. It never means
the underlying research idea is valid.

## Catalog

The canonical source of truth lives in `alpha_system.governance.canaries`.
`StudySpec.negative_controls` should reference these `canary_type` strings by
name, and `EvidenceBundle.negative_control_results` should record corresponding
`NegativeControlResult` dictionaries after a future harness executes them.

| Canary type | Guard family | Injected fault | Expected failure |
| --- | --- | --- | --- |
| `random_target` | `statistical_sanity` | Replace the target with random noise so any admissible-looking signal is known-bad. | `guard_rejects_or_flags_random_target_signal` |
| `permuted_labels` | `label_integrity` | Permute labels away from their original examples so label alignment is known-bad. | `guard_rejects_or_flags_permuted_label_signal` |
| `future_shift` | `no_lookahead` | Shift future information into the feature or label path so lookahead is known-bad. | `guard_rejects_or_flags_future_shift_lookahead` |
| `optimistic_fill` | `execution_assumption` | Use an unrealistically favorable fill assumption so execution-cost handling is known-bad. | `guard_rejects_or_flags_optimistic_fill_assumption` |

`future_shift` explicitly catalogs no-lookahead coverage for R-011. All entries
share the R-010 fail-closed expectation: a correct guard must reject or flag the
injected fault.

## NegativeControlResult

`NegativeControlResult` carries exactly these fields:

- `canary_id`
- `canary_type`
- `expected_failure`
- `observed_result`
- `pass_fail`
- `related_study_or_evidence`
- `notes`

`canary_id` is a deterministic `nctrl_...` governance ID generated from all
non-ID fields. `canary_type` is constrained to the catalogued values:
`random_target`, `permuted_labels`, `future_shift`, and `optimistic_fill`.
`expected_failure` must match the catalog entry for the selected `canary_type`.
`related_study_or_evidence` must reference a `StudySpec` or `EvidenceBundle`
governance ID.

Validation is fail-closed. Missing fields, null fields, unknown fields, invalid
types, uncatalogued canary types, mismatched expected failures, malformed IDs,
non-substantive text, non-canonical values, and inconsistent `pass_fail`
semantics raise `GovernanceValidationError`.

## Pass And Fail Semantics

`pass_fail` uses the closed vocabulary `PASS` or `FAIL`.

`PASS` means the observed result matched the catalogued `expected_failure`: the
guard caught the injected known-bad fault. `FAIL` means the observed result did
not match the expected failure: the control is recorded as a failed guard check.

The validator does not silently convert a mismatch into a pass. A result whose
`observed_result` differs from `expected_failure` is valid only when
`pass_fail` is `FAIL`.

## Canary Harness

The executable harness lives in
`alpha_system.governance.canaries.harness` and is documented in
`docs/governance/CANARY_HARNESS.md`.

The harness runs three ARGOV-P14 synthetic dry-run canaries:

- `future_shift` invokes the label-leakage guard's availability-time check and
  expects `guard_rejects_or_flags_future_shift_lookahead`.
- `permuted_labels` invokes the label-leakage guard's forbidden-feature-overlap
  check and expects `guard_rejects_or_flags_permuted_label_signal`.
- `optimistic_fill` invokes execution-assumption guards and expects
  `guard_rejects_or_flags_optimistic_fill_assumption`.

`random_target` remains catalogued but is not executable in ARGOV-P14.

`tools/hooks/canary_runner.py` runs these governance canaries alongside the
existing Frontier safety canaries. A governance canary passes only when the guard
catches the injected fault; a missed fault is recorded as `FAIL`, never silently
treated as success.
