# Reproducibility Principles

## Required Identity For Results

Every research result must be traceable through:

- git commit
- dirty-tree state
- code hash
- config hash
- data version
- factor version
- label version
- engine version
- run manifest

If a result cannot be connected to these identifiers, it is not complete for
review.

## Run Manifests

A run manifest should record the command, config path, resolved config hash,
code hash, git commit, dirty-tree summary, input data versions, factor
versions, label versions, engine version, runtime environment, output paths,
start time, end time, and status.

Failed runs must remain visible. Their manifests and handoff notes are part of
the audit trail.

## Hashing

Config hashes identify the resolved parameters used by a run. Code hashes
identify the implementation content used by a run. Data, factor, label, and
engine versions identify the semantic inputs. Hashing does not replace review,
but it makes review reproducible.

## Point-In-Time Reproduction

Reproduction must respect `available_ts` and `label_available_ts`. A reproduced
result that ignores timestamp availability is not equivalent to the original
research claim.

## Local-First Reproduction

The expected reproduction environment is local. Large inputs are local Parquet,
metadata is local SQLite, and reports are Markdown, CSV, or optional static
HTML. No S3 bucket, cloud object store, paid database, database server, workflow
server, MLflow server, or web UI is required for v1 reproduction.
