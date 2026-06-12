# Evidence-Accrual Requeue Scan

`alpha governance requeue-scan` is a deterministic, manual scan for
INCONCLUSIVE verdict evidence annotated with `reason_code == UNDERPOWERED`.
It does not change verdicts, annotations, ledgers, registries, schedules, or
promotion outcomes.

## Declared Materiality Rule

The rule lives in `src/alpha_system/governance/requeue.py`:

- `MATERIALITY_MIN_ACCRUED_MONTHS = 6`
- `MATERIALITY_MIN_POWER_DELTA = 0.25`
- `REQUEUE_REASON = "UNDERPOWERED_EVIDENCE_ACCRUAL"`

A row is eligible only when both conditions are true:

1. current accepted data months minus verdict-time accepted data months is at
   least 6 months;
2. new planning-prior power estimate minus prior planning-prior power estimate
   is at least 0.25.

Eligibility is queue metadata only. It is not a PASS, not a promotion
criterion, and not evidence that a hypothesis is tradable or profitable.

## Planning Heuristic

The power estimate is a planning-only heuristic:

```text
t ~= SR_prior * sqrt(years_of_accepted_data)
```

When `n_eff` and `observation_count` metadata are present, years are scaled by
`n_eff / observation_count`. When that metadata is absent, the scan uses
calendar accepted-data years and marks the row `N_EFF_METADATA_ABSENT`.

The estimator is isolated in `alpha_system.governance.requeue`. It must never
be imported by `promotion_gate.py` or used by any promotion gate.

## Input Contract

The scan reads JSON files or directories supplied by the caller:

- `--verdicts`: reviewer verdict JSON files or directories, read-only.
- `--annotations`: additive verdict annotation JSON files or directories,
  read-only.
- `--acceptance-evidence`: a JSON file declaring current accepted data months
  for UNDERPOWERED candidates.

UNDERPOWERED candidates must include explicit requeue planning metadata:

```json
{
  "reason_code": "UNDERPOWERED",
  "study_spec_id": "sspec_example",
  "original_verdict_path": "synthetic/reviewer_verdicts/example.json",
  "requeue_scan": {
    "accepted_data_months_at_verdict": 12,
    "sr_prior": 0.5,
    "n_eff_at_verdict": 120,
    "observation_count_at_verdict": 240
  }
}
```

Acceptance evidence is keyed by `study_spec_id`, `original_verdict_ref`, or
`original_verdict_path`:

```json
{
  "schema": "discovery_rigor_floor.dataset_acceptance_evidence.v1",
  "accepted_data": [
    {
      "study_spec_id": "sspec_example",
      "accepted_data_months": 30,
      "n_eff": 600,
      "observation_count": 600
    }
  ]
}
```

Missing or malformed input fails closed. A successful scan exits 0 even when
no rows are eligible.

## Output

Stdout contains a value-free eligibility table plus the emitted
`RequeuedVerdictRecord` JSON. With `--out`, the record JSON is also written to
the caller-supplied path. The command never writes to production ledgers or
registries.

Synthetic fixture example:

| study_spec_id | original_verdict_ref | prior_power_estimate | new_power_estimate | data_accrued_months | eligible | requeue_reason | metadata_status |
|---|---|---:|---:|---:|---|---|---|
| sspec_requeue_eligible | synthetic/reviewer_verdicts/reviewer_verdict_sspec_requeue_eligible.json | 0.353553 | 0.790569 | 18 | true | UNDERPOWERED_EVIDENCE_ACCRUAL | N_EFF_METADATA_USED |
| sspec_requeue_not_eligible | synthetic/reviewer_verdicts/reviewer_verdict_sspec_requeue_not_eligible.json | 0.300000 | 0.335410 | 3 | false | UNDERPOWERED_EVIDENCE_ACCRUAL | N_EFF_METADATA_ABSENT |

## Cadence

There is no daemon, scheduler, cron, watcher, or auto-rerun path. The
coordinator runs the scan manually post-campaign and after material
dataset-acceptance events, using an explicit acceptance-evidence file for the
current accepted-data picture. Any eligible row is a deterministic retest-queue
signal for human/coordinator action; it does not execute the retest.
