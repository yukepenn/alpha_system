# Reproducibility Audit

The reproducibility audit is a read-only inspection of the local SQLite metadata
registry. It is a hardening check, not a claim that an experiment result is
correct, profitable, robust, or tradable.

## What The Audit Checks

`src/alpha_system/experiments/audit.py` returns structured findings for:

- missing `git_commit`,
- missing `code_hash`,
- missing `config_hash`,
- missing `data_version`,
- missing factor versions where the run category requires them,
- missing label versions where the run category requires them,
- missing artifact references,
- forbidden artifact paths,
- not-commit-safe manifest paths without warnings,
- approved promotion decisions without review metadata,
- failed rows that lack visible failed-step or warning metadata.

The audit also reports missing required registry tables.

## Artifact Path Findings

Artifact path policy is intentionally conservative. The audit flags paths that
would create commit or reproducibility risk, including:

- absolute paths,
- parent-directory traversal,
- Windows synced mount paths under `/mnt/c`, `/mnt/d`, or `/mnt/e`,
- OneDrive, Dropbox, or Google Drive paths,
- generated SQLite/DB/journal/WAL files,
- generated Parquet, Arrow, Feather, or log files,
- full grid output or full trade log directories.

Local-only paths can be valid registry references, but they must remain out of
git and carry not-commit-safe warnings when recorded in the artifact manifest.

## Failed-Run Findings

Failed runs should be visible in normal run tables. A failed row should include
a failed-step payload, a status message, or warnings. A failed row without those
details produces a `hidden_failed_run` finding because reviewers cannot tell
where the failure occurred.

The audit cannot detect work that was never recorded anywhere. It detects
observable hidden-failure patterns in the registry rows it can inspect.

## Promotion Findings

Approved or promoted decisions must include a review trail. The audit flags
promotion rows where an approval-like status lacks reviewer metadata, review
artifact metadata, review status, or rationale.

Recommendation is distinct from approval. A recommendation row does not promote
a candidate by itself.

## Interpreting Output

A clean audit means the inspected registry rows satisfy the metadata and path
policy checks implemented for this phase. It does not validate research quality,
execution truth, no-lookahead semantics, or candidate suitability by itself.

Findings are structured with:

- `code`,
- `table_name`,
- `record_id`,
- `severity`,
- `message`,
- optional `details`.

The intended workflow is to use the audit output as review evidence alongside
tests, handoffs, and semantic review. SQLite databases and generated artifacts
remain local-only and must not be committed.
