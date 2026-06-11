# N_eff / Overlap-Aware Sample Reporting

`FUTSUB-P25` adds value-free effective-sample-size reporting for overlapping
label diagnostics. The runtime surface is additive and opt-in:

- estimator and hooks:
  `alpha_system.runtime.diagnostics.splits.n_eff`
- label report integration:
  `build_label_diagnostics_report(..., n_eff_overlap_metadata=...,
  walk_forward_metadata=...)`
- report payload block:
  `label_n_eff_report`

Calls that omit the N_eff request keep the prior label diagnostics payload.

## Estimator

Required caller-supplied metadata:

- `horizon_bars`, `horizon_minutes`, or `horizon_seconds`
- `sampling_cadence_bars`, `sampling_cadence_minutes`, or
  `sampling_cadence_seconds`
- `discount_factor` or an accepted overlap-factor alias

The metadata is supplied by the caller from LabelPack registry metadata or the
committed horizon-overlap context. The estimator does not read registries,
materialize labels, or infer missing overlap factors.

Formula:

```text
implied_discount_factor = max(1, horizon / sampling_cadence)
n_eff = floor(rows / discount_factor), bounded to [0, rows]
```

For `rows > 0`, the lower bound is one effective sample after discounting. For
`rows == 0`, `n_eff == 0`.

The supplied `discount_factor` must be at least the
`implied_discount_factor`. If it is missing, non-positive, not finite, uses
incompatible units, or understates the horizon/cadence overlap, the runtime
fails closed with `NEffSampleReportingError` or a visible label diagnostics
reason code `n_eff_overlap_metadata_unavailable`.

Conservatism direction:

- `n_eff` is never greater than raw `rows`.
- Overlapping horizons discount rows by the explicit overlap factor.
- Extended horizons such as 60m, 120m, and 240m therefore receive stronger
  discounts than 5m or 30m horizons at the same sampling cadence.
- The estimator may understate the effective count for irregular calendars or
  nonuniform sampling; it must not overstate it by treating raw rows as
  independent samples.

This is a reporting input only. It is not a significance test, correction
engine, promotion rule, DSR/PBO/PSR implementation, contamination ledger, or
portfolio walk-forward method.

## Report Block Contract

When requested, label diagnostics add:

```text
label_n_eff_report:
  rows: int
  n_eff: int
  rows_are_not_independent_samples: true
  overlap_metadata:
    horizon: number
    horizon_unit: bars|minutes|seconds
    sampling_cadence: number
    sampling_cadence_unit: bars|minutes|seconds
    discount_factor: number
    implied_discount_factor: number
    overlap_fraction: number
    metadata_source: string
  estimator_formula: string
  conservatism_direction: string
  statistical_validity_claim: false
  session_day_aggregation:
    session_fields: comma-delimited configured field names
    trade_date_fields: comma-delimited configured field names
    observation_count: int
    session_unit_count: int
    trade_date_unit_count: int
    session_trade_date_unit_count: int
    missing_session_count: int
    missing_trade_date_count: int
  walk_forward_fold_n_eff:
    - split_id: string
      half_life_protocol: STRUCTURAL|MEDIUM|FAST when present
      purge_gap: int|null
      embargo_gap: int|null
      train:
        rows: int
        n_eff: int
        rows_are_not_independent_samples: true
        overlap_metadata: same shape as above
      validation:
        rows: int
        n_eff: int
        rows_are_not_independent_samples: true
        overlap_metadata: same shape as above
```

The block is value-free. It carries counts, field names, protocol names, and
metadata only.

## Session / Day Hooks

`build_session_day_aggregation` groups caller-supplied observations by existing
fields only. Defaults:

- session fields: `session_label`, `session`, `session_segment`
- trade-date fields: `trade_date`, `trade_date_id`

The hook reports unit counts and missing-field counts. It does not derive a
session or trade date from timestamps and does not introduce a new session
calendar.

## Walk-Forward Fold Attachment

`attach_n_eff_to_walk_forward_metadata` consumes the P24
`WalkForwardSplitPlan.to_dict()` shape or an equivalent iterable of fold
mappings. It reads:

- `config.half_life_protocol` when present
- each fold `split_id`
- each fold `train_indices` and `validation_indices` lengths
- each fold `purge_gap` and `embargo_gap`

It does not change split construction, purge/embargo semantics, protocol
defaults, or fail-closed behavior. It attaches train and validation rows/N_eff
counts beside the P24 fold identity fields for downstream Validation Governance.

## Validation Governance Handoff

Downstream consumers should treat `label_n_eff_report` as the N_eff + fold
metadata contract:

- use `rows` only as raw observation count;
- use `n_eff` as the overlap-aware reporting input;
- require `rows_are_not_independent_samples == true`;
- require explicit `overlap_metadata`;
- preserve `session_day_aggregation` unit counts;
- preserve `walk_forward_fold_n_eff` when walk-forward context is supplied;
- fail closed when N_eff is requested and metadata is missing or inconsistent.

Full multiple-testing control, locked-test contamination policy, promotion
eligibility, and DSR/PBO/PSR remain deferred to
`ALPHA_VALIDATION_GOVERNANCE_V1`.
