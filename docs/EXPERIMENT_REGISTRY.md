# Experiment Registry

The experiment registry hardening layer sits on top of the local SQLite metadata
registry. It does not add a second registry, a server, or an external tracker.
All durable experiment metadata continues to flow through the existing
`dataset_versions`, factor, label, strategy, run, artifact, and promotion tables.

SQLite files remain local-only artifacts. Tests that exercise registry behavior
use temporary databases.

## Hardened Run Records

`src/alpha_system/experiments/run_records.py` defines the hardened
`ExperimentRunRecord` model. It validates the reproducibility fields before a
row is inserted into an experiment run table:

- `run_id`
- `timestamp`
- `git_commit`
- `git_dirty`
- `code_hash`
- `config_hash`
- `data_version`
- `factor_versions`
- `label_versions`
- `engine_version`
- `parameters`
- `artifact_paths`
- `decision_status`
- `warnings`
- failed-step visibility for failed runs

The model writes through `src/alpha_system/experiments/registry.py`, preserving
the existing SQLite table contract. Category-specific requirements are enforced
for `factor_validation_runs`, `study_runs`, `grid_runs`, `ml_runs`, and
`backtest_runs`; for example, study/grid/ML runs require label versions, while
backtest rows can omit label versions when no label dependency exists.

## Table Coverage

The registry hardening tests exercise all required metadata tables against a
temporary database:

| Table | Coverage |
| --- | --- |
| `dataset_versions` | Dataset version row inserted. |
| `factor_registry` | Factor registry row inserted. |
| `factor_versions` | Factor version metadata inserted. |
| `factor_validation_runs` | Hardened run record inserted. |
| `label_versions` | Label version metadata inserted. |
| `study_runs` | Hardened run record inserted. |
| `strategy_registry` | Strategy registry row inserted. |
| `strategy_versions` | Strategy version metadata inserted. |
| `grid_runs` | Hardened grid and management-grid-compatible run rows inserted. |
| `ml_runs` | Hardened run record inserted. |
| `backtest_runs` | Hardened run record inserted. |
| `artifact_manifest` | Manifest entry inserted with path-policy metadata. |
| `promotion_decisions` | Review-backed promotion decision inserted. |

## Artifact Manifests

`src/alpha_system/experiments/artifact_manifest.py` provides
`ArtifactManifestEntry` and path-policy classification. Manifest entries support:

- `artifact_id`
- `run_id`
- `artifact_type`
- relative path
- content hash
- size in bytes when the file is available
- creation timestamp
- local-only status
- commit-eligible status
- warnings for not-commit-safe paths

The path policy distinguishes commit-eligible documentation/source/test paths
from local-only or forbidden generated paths. Absolute paths, parent-directory
traversal, synced Windows mount paths, generated DB files, generated Parquet/
Arrow/Feather files, logs, and full output directories are flagged.

## Failed Runs

`src/alpha_system/experiments/failure_records.py` records failed runs directly
in the relevant run table with:

- `decision_status="failed"`
- a visible failed-step payload in `status_message`
- a warning that the failed run was recorded visibly

`list_failed_runs` scans the experiment run tables and surfaces failed rows.
This prevents a failed run from being represented only as an absent success row.

## Promotion Traceability

`src/alpha_system/experiments/promotion.py` defines `PromotionDecision`.
Promotion decisions require:

- `candidate_id`
- `source_run_id`
- `review_status`
- reviewer identity or review artifact reference
- `decision_status`
- rationale
- artifact references
- timestamp

Approved or promoted decisions are rejected unless review metadata is present.
Recommendation states are represented separately and are not treated as approval.
The model also rejects candidate self-approval.

## Version References

`src/alpha_system/experiments/version_refs.py` validates structured references
for data, factor, label, and engine versions. Empty values, control characters,
and malformed tokens are rejected before metadata is written.

## CLI Status

`alpha registry status` remains read-only. It now reports:

- registry location and migration/table status,
- audit finding count,
- visible failed-run count,
- promotion approvals without review.

The command does not create a registry, mutate rows, run experiments, approve
candidates, or write artifacts.
