# DATA-P18 Handoff — Dataset Partition Plan and Locked-Test Metadata

## Scope Executed

Implemented `DatasetPartitionPlan` in
`src/alpha_system/data/foundation/datasets.py` as a frozen, fail-closed
data-admissibility descriptor with exactly these fields:

- `plan_id`
- `development_partition`
- `validation_partition`
- `locked_test_candidate`
- `latest_shadow_candidate`
- `contamination_metadata_rules`

The package namespace now re-exports `DatasetPartitionPlan`,
`REQUIRED_DATASET_PARTITION_PLAN_FIELDS`,
`CONTAMINATION_METADATA_RULE_FIELDS`, and
`require_governance_metadata_for_locked_partition_use`.

## Encoded Partition Windows

The canonical fixed windows are encoded and validated:

- `development_partition`: `2018-01-01` through `2022-12-31`
- `validation_partition`: `2023-01-01` through `2024-12-31`
- `locked_test_candidate`: `2025-01-01` through `as_of_run`
- `latest_shadow_candidate`: optional; when present, it must be explicitly
  rolling and optional, with explicit start/end bounds.

The fixed windows are ordered and non-overlapping. The locked-test candidate is
held out by construction and starts strictly after the validation window.

## Contamination Metadata Rules

`contamination_metadata_rules` is structured and validated. It requires:

- data QA coverage inspection across partitions to be allowed;
- held-out partition IDs to be explicit;
- locked partition use to require Governance metadata;
- locked partition use to require contamination metadata;
- alpha research without Governance metadata to be rejected;
- the plan to imply no research approval.

Malformed, loose, missing, or weakened rule mappings raise
`DataFoundationValidationError`.

## Locked-Test Guard Behavior

`require_governance_metadata_for_locked_partition_use(...)` provides the
testable guard:

- coverage QA purposes are allowed across plan partitions without Governance
  contamination metadata;
- development and validation partitions are not treated as locked by this guard;
- non-QA use of `locked_test_candidate` or `latest_shadow_candidate` fails
  closed unless substantive Governance contamination metadata is supplied;
- missing, empty, vague, non-mapping, or null metadata is rejected.

The guard records the prerequisite rule only. It does not create Governance
metadata, authorize locked-partition use, or imply research approval.

## Tests And Docs

Added `tests/unit/data/test_dataset_partition_plan.py` covering exact fields,
canonical date encoding, missing/extra/blank input rejection, malformed and
non-canonical partition bounds, loose partition field rejection, optional
latest-shadow validation, non-enforcing contamination rule rejection, QA
coverage inspection allowance, and locked-partition use rejection without
Governance metadata.

Added `docs/data_foundation/PARTITION_PLAN.md` and updated
`docs/data_foundation/README.md` plus the root `README.md` snapshot for DATA-P18
and next phase DATA-P19.

## Explicit Staged File Set

Final explicit staged set:

- `README.md`
- `docs/data_foundation/PARTITION_PLAN.md`
- `docs/data_foundation/README.md`
- `handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P18.md`
- `src/alpha_system/data/foundation/__init__.py`
- `src/alpha_system/data/foundation/datasets.py`
- `tests/unit/data/test_dataset_partition_plan.py`

No `runs/` path is staged.

## Validation Results

- `git status --short` — passed; final staged set contains only allowed DATA-P18
  files listed above.
- `python tools/verify.py --smoke` — passed with no output.
- `python -m pytest tests/unit/data/test_dataset_partition_plan.py -q` —
  passed: `7 passed in 0.04s`.
- `python -m pytest tests/unit/data -q` — passed: `310 passed in 0.22s`.
- `test -f docs/data_foundation/PARTITION_PLAN.md` — passed.
- `git ls-files runs` — passed with empty output.
- `find data -type f ! -name README.md ! -name .gitkeep -print` — passed with
  empty output.
- `find metadata -type f ! -name README.md ! -name .gitkeep -print` — passed
  with empty output.
- `find . -name '*.parquet' -not -path './tests/fixtures/*' -print` — passed
  with empty output.
- `git diff --cached --name-only` — passed; output matches the explicit staged
  file set above.

No required or supplementary checks were skipped.

## Artifact And Safety Confirmation

`runs/**` remains local-only; no run-local handoff, review, verdict, or repair
artifact was staged. No raw data, canonical data, factor data, label data,
cache data, provider response, account artifact, SQLite/DB/journal/WAL file,
Parquet/Arrow/Feather file, log, cache, model artifact, heavy artifact, or
secret was created or staged.

No alpha research, factor research, label research, strategy work,
locked-partition use, Governance metadata attachment, broker operation, live
trading, paper trading, order routing, account access, real-data pull,
deployment, PR creation, merge, reviewer invocation, `review.md`, `verdict.json`,
or unsupported alpha/profitability/tradability/production-readiness claim was
introduced.

This handoff does not mark DATA-P18 PASS. Ralph owns validation orchestration,
review, verdict parsing, done-check, PR, CI, and merge gates.
