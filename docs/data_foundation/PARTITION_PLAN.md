# DATA-P18 Dataset Partition Plan and Locked-Test Metadata

`DatasetPartitionPlan` is the data-foundation descriptor for partitioning a
versioned canonical dataset. It defines the canonical development, validation,
locked-test candidate, and optional latest-shadow candidate windows, and it
records the structured locked-test contamination metadata rules.

The plan is a data-admissibility object only. It does not imply research
approval, alpha value, tradability, broker readiness, paper trading, live
trading, or production readiness. It does not permit locked-partition use.

## Required Fields

`DatasetPartitionPlan` has exactly these fields:

- `plan_id`
- `development_partition`
- `validation_partition`
- `locked_test_candidate`
- `latest_shadow_candidate`
- `contamination_metadata_rules`

Construction is fail-closed. Missing fields, extra fields, blank or malformed
`plan_id`, malformed partition mappings, loose partition fields, non-canonical
fixed partition dates, malformed date bounds, reversed latest-shadow bounds, and
non-enforcing contamination rules raise `DataFoundationValidationError`.

## Canonical Windows

The DATA-P18 canonical windows are pinned to the campaign contract:

| Partition | Start | End | Notes |
| --- | --- | --- | --- |
| `development_partition` | `2018-01-01` | `2022-12-31` | Development window. |
| `validation_partition` | `2023-01-01` | `2024-12-31` | Validation window. |
| `locked_test_candidate` | `2025-01-01` | `as_of_run` | Held-out locked-test candidate. |
| `latest_shadow_candidate` | `rolling_recent` or explicit date | `as_of_run` or explicit date | Optional rolling recent candidate. |

The fixed development, validation, and locked-test candidate windows must remain
ordered and non-overlapping. The locked-test candidate starts strictly after the
validation window. The latest-shadow candidate is optional and must be explicitly
marked as rolling and optional when present.

## Contamination Metadata Rules

The plan stores these structured rules in `contamination_metadata_rules`:

- `data_qa_coverage_inspection_allowed` must be `True`.
- `locked_partition_ids` must identify the held-out locked-test and
  latest-shadow candidate partitions.
- `locked_partition_use_requires_governance_metadata` must be `True`.
- `locked_partition_use_requires_contamination_metadata` must be `True`.
- `alpha_research_without_governance_metadata` must be `REJECT`.
- `implies_research_approval` must be `False`.

These fields are validated as policy values, not as prose. A malformed or
weakened rule set fails closed.

## Locked-Test Guard

`require_governance_metadata_for_locked_partition_use(...)` is the testable
guard for the locked-partition rule:

- coverage QA purposes may inspect coverage across plan partitions;
- non-QA use of `locked_test_candidate` or `latest_shadow_candidate` requires
  substantive Governance contamination metadata;
- missing, empty, vague, or non-mapping Governance metadata raises
  `DataFoundationValidationError`;
- development and validation partitions are not treated as locked by this
  specific guard.

The guard expresses the requirement that locked-partition use must create
Governance contamination metadata. It does not create Governance metadata, grant
research approval, or authorize locked-test research.

## Scope Boundaries

DATA-P18 does not pull, parse, canonicalize, version, inspect, or write real
market data. It does not perform alpha research, factor research, label
research, strategy work, broker operations, paper trading, live trading, order
routing, account access, deployment, or production operation.

Raw provider responses, canonical data, local DB files, logs, caches, heavy
artifacts, and `runs/**` remain local-only and must not be committed.
