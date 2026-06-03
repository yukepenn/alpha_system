# ASV1-P22 Handoff - Experiment Registry Hardening

## Status

Implemented the local-first experiment registry hardening layer. Codex did not
run Claude, reviewer, verdict parsing, PR creation, merge, broker/live/paper
scope, order routing, deployment, or PASS marking.

## Registry Hardening Summary

ASV1-P22 adds hardened experiment modules under `src/alpha_system/experiments/`
that reuse the existing SQLite metadata registry and `experiments.registry`
insert/read foundation. No registry migration or second registry implementation
was introduced.

Durable modules added:

- `run_records.py` - canonical hardened run-record model and required-field
  enforcement.
- `artifact_manifest.py` - manifest entry schema, hash/size capture, and
  path-policy classification.
- `reproducibility.py` - reproducibility metadata assembly and completeness
  checks.
- `promotion.py` - review-backed promotion-decision model.
- `audit.py` - read-only registry audit with structured findings.
- `failure_records.py` - failed-run recording and surfacing.
- `version_refs.py` - structured data/factor/label/engine version references.

`alpha registry status` remains read-only and now surfaces audit finding count,
visible failed-run count, and promotion approvals without review.

## Table Coverage Matrix

| Table | ASV1-P22 coverage |
| --- | --- |
| `dataset_versions` | Temp-DB integration test inserts and counts a dataset version. |
| `factor_registry` | Temp-DB integration test inserts and counts a factor registry row. |
| `factor_versions` | Temp-DB integration test inserts and counts factor version metadata. |
| `factor_validation_runs` | Hardened run record inserted through the shared run-record model. |
| `label_versions` | Temp-DB integration test inserts and counts label version metadata. |
| `study_runs` | Hardened run record inserted and audited. |
| `strategy_registry` | Temp-DB integration test inserts and counts a strategy registry row. |
| `strategy_versions` | Temp-DB integration test inserts and counts strategy version metadata. |
| `grid_runs` | Hardened run record inserted for grid and management-grid-compatible coverage. |
| `ml_runs` | Hardened run record inserted. |
| `backtest_runs` | Hardened run record inserted. |
| `artifact_manifest` | Manifest entry inserted with path-policy metadata. |
| `promotion_decisions` | Review-backed promotion decision inserted and audit-tested. |

## Run-Record Field Coverage

`ExperimentRunRecord` validates:

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
- failed-step visibility for failed rows

Category-specific requirements are enforced for the existing experiment run
tables. Study/grid/ML rows require label versions; factor-validation and
backtest rows allow empty label versions when no label dependency is required.
Duplicate run IDs continue to fail deterministically through SQLite primary-key
constraints.

## Artifact Manifest Summary

`ArtifactManifestEntry` supports artifact id, run id, artifact type, relative
path, content hash, size when available, created timestamp, local-only status,
commit-eligible status, and warnings. Path classification flags absolute paths,
parent traversal, Windows synced mounts, generated DB files, generated Parquet/
Arrow/Feather/log files, and full output directories.

## Failed-Run Visibility Summary

`record_failed_run` writes failed runs into the relevant run table with
`decision_status="failed"`, a structured failed-step payload, and a visible
warning. `list_failed_runs` surfaces failures across experiment run tables.
The audit also detects failed rows that lack failed-step, warning, or status
detail.

## Promotion Traceability Summary

`PromotionDecision` requires candidate id, source run id, review status,
reviewer identity or review artifact reference, decision status, rationale,
artifact references, and timestamp. Approval-like decisions without review
metadata are rejected. Recommendation states remain distinct from approval, and
self-approval is rejected.

## Reproducibility Audit Summary

The read-only registry audit detects:

- missing git commit,
- missing code hash,
- missing config hash,
- missing data version,
- missing required factor versions,
- missing required label versions,
- missing artifact references,
- forbidden artifact paths,
- not-commit-safe manifest paths without warning,
- promotion approval without review,
- hidden failed-run patterns.

Audit output is structured and non-mutating. A clean audit is metadata hygiene
evidence only; it does not make research, profitability, robustness, or
tradability claims.

## Files Changed And Staged

Source:

- `src/alpha_system/experiments/run_records.py`
- `src/alpha_system/experiments/artifact_manifest.py`
- `src/alpha_system/experiments/reproducibility.py`
- `src/alpha_system/experiments/promotion.py`
- `src/alpha_system/experiments/audit.py`
- `src/alpha_system/experiments/failure_records.py`
- `src/alpha_system/experiments/version_refs.py`
- `src/alpha_system/cli/registry.py`

Docs:

- `docs/EXPERIMENT_REGISTRY.md`
- `docs/REPRODUCIBILITY_AUDIT.md`
- `README.md`

Tests:

- `tests/unit/test_run_record_required_fields.py`
- `tests/unit/test_failed_run_recording.py`
- `tests/unit/test_failure_records_visible.py`
- `tests/unit/test_artifact_manifest_schema.py`
- `tests/unit/test_artifact_manifest_hash_size.py`
- `tests/unit/test_artifact_path_policy.py`
- `tests/unit/test_promotion_requires_review.py`
- `tests/unit/test_promotion_decision_schema.py`
- `tests/unit/test_version_refs.py`
- `tests/integration/test_registry_audit_missing_hashes.py`
- `tests/integration/test_registry_audit_missing_versions.py`
- `tests/integration/test_registry_audit_forbidden_artifacts.py`
- `tests/integration/test_registry_all_tables_exercised.py`
- `tests/integration/test_duplicate_run_behavior.py`

Handoff:

- `handoffs/ASV1-P22.md`

These files are intended to be staged explicitly by path. No `runs/` path is
included.

## Validation Results

Passed:

- `python -m pytest tests/unit tests/integration` - PASS, 466 passed.
- `python -m pytest tests/unit/experiments || true` - PASS, 4 passed.
- `python -m pytest tests/unit/test_run_record_required_fields.py tests/unit/test_failed_run_recording.py tests/unit/test_artifact_manifest_schema.py` - PASS, 7 passed.
- `python -m pytest tests/integration/test_registry_audit_missing_hashes.py tests/integration/test_registry_audit_missing_versions.py tests/integration/test_no_committed_sqlite.py` - PASS, 4 passed after the audit coverage update.
- `python -m pytest tests/integration/test_registry_audit_missing_hashes.py tests/integration/test_registry_audit_missing_versions.py tests/integration/test_registry_audit_forbidden_artifacts.py` - PASS, 4 passed.
- `PYTHONPATH=src python -m alpha_system.cli registry status --help` - PASS.
- `python -m compileall src` - PASS.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` - PASS, no output.
- `find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true` - PASS, no output.
- `find . -path ./tests/fixtures -prune -o -type f -name "*.parquet" -print` - PASS, no output.
- `find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print` - PASS, no output.
- `git ls-files runs` - PASS, no output.

Command exceptions / unavailable tools:

- `python -m alpha_system.cli registry status --help` - failed in the plain
  shell with `/usr/bin/python: Error while finding module specification for
  'alpha_system.cli' (ModuleNotFoundError: No module named 'alpha_system')`.
  The repo is source-layout and not installed in this shell; the same module
  command succeeds with `PYTHONPATH=src`, and pytest uses `pythonpath = ["src"]`
  from `pyproject.toml`.
- `python -m ruff check src tests || true` - ruff unavailable:
  `/usr/bin/python: No module named ruff`.
- `python -m mypy src || true` - mypy unavailable:
  `/usr/bin/python: No module named mypy`.

## Artifact Policy Confirmation

- No local DB was committed or intended to be staged.
- No generated artifacts were committed or intended to be staged.
- No `runs/**` path was staged or intended to be staged.
- SQLite tests use `tmp_path` databases only.
- Artifact, metadata, Parquet, and SQLite scans produced no forbidden output.
- `git ls-files runs` returned empty.

## Safety Confirmations

- No broker, live, paper, order-routing, deployment, or production execution
  behavior was introduced.
- No alpha, profitability, robustness, or tradability claims were introduced.
- Promotion requires review; recommendation remains distinct from approval.
- Failed runs stay visible through failed-step metadata and audit findings.
- `alpha registry status` remains read-only.
- README snapshot was updated compactly for ASV1-P22 complete / ASV1-P23 next
  with unchanged safety boundaries.

## Known Limitations

- The exact plain `python -m alpha_system.cli registry status --help` command
  requires the package to be installed or `PYTHONPATH=src` in this shell.
- The hardening layer adapts to the existing ASV1-P05 schema. Additional
  manifest and promotion details are stored in existing JSON metadata/status
  fields rather than new columns because registry migrations were outside the
  allowed path list.
- The audit can detect observable hidden-failure patterns in registry rows. It
  cannot detect work that was never recorded anywhere.

## Recommended Review Focus

Review should focus on required-field enforcement, category-specific
factor/label version requirements, failed-run visibility, artifact path-policy
classification, audit finding completeness, promotion review-trail enforcement,
recommendation-versus-approval behavior, read-only CLI status behavior, temp-DB
test discipline, README compactness, artifact policy, and absence of
broker/live/paper scope or unsupported claim language.
