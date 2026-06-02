# Factor Registry

`ASV1-P09` defines the factor governance spine only. It validates
specifications, dependencies, lifecycle gates, deterministic hashes, and local
SQLite registry records. It does not compute factor values, materialize a factor
store, generate labels, or make any alpha/tradability claim.

## FactorSpec Fields

Every `FactorSpec` must contain:

```text
factor_id
name
version
owner
description
input_fields
parameters
frequency
warmup_bars
session_reset
availability_lag
factor_type
evaluation_type
code_hash
config_hash
status
created_at
validation_artifact_path
```

`factor_id` is a stable lower-case identifier. `version` is the factor version
token. `input_fields` is a non-empty list of declared inputs with `name`,
`domain`, and `source_field`. Supported domains are `bar`, `quote`, `trade`,
`l2`, and `factor`. `parameters` is a JSON mapping. `availability_lag` is a
non-negative number of seconds. `warmup_bars` is a non-negative integer.
`session_reset` is a boolean.

## Lifecycle

The lifecycle states are:

```text
draft -> candidate -> validated -> approved -> deprecated
```

Allowed transitions are:

```text
draft -> candidate
draft -> deprecated
candidate -> validated
candidate -> deprecated
validated -> approved
validated -> deprecated
approved -> deprecated
```

`candidate` requires a `validation_artifact_path`. `validated` requires a
validation artifact reference and a recorded reviewed validation status in
`factor_validation_runs`. `approved` requires a review-backed promotion decision
in `promotion_decisions` with reviewer metadata. Automatic or unreviewed
approval is rejected. `deprecated` factors remain queryable so old research
records can be reproduced.

Draft factor values are not permanently materialized into the long-term factor
store by default. This phase represents that policy in lifecycle helpers and
tests; it does not implement a materialization command or factor store.

## Dependencies

Factor inputs must be declared up front. A factor implementation may only use
declared input names or declared `source_field` values. Raw ad hoc fields are
rejected by validation. Label-like fields are also rejected as factor inputs,
including fields such as `forward_return_1m`, `mfe`, `mae`,
`target_before_stop`, `stop_before_target`, and names containing `label`.

This keeps future-looking labels out of factor inputs and preserves the
factor/label boundary.

## Hashes

`code_hash` is a SHA-256 hash over the supplied code path manifest when
`alpha factor validate --code-path` is used. Without a code path, validation
checks that the recorded hash is a lowercase SHA-256 digest.

`config_hash` is a SHA-256 hash of the FactorSpec config with the
self-referential `config_hash` field excluded. The hash includes the recorded
`code_hash`, parameters, lifecycle status, dependency declarations, and other
spec fields.

## Registry Behavior

The factor registry uses the ASV1-P05 SQLite tables:

```text
factor_registry
factor_versions
factor_validation_runs
promotion_decisions
```

`factor_registry` stores factor identity and current lifecycle status.
`factor_versions` stores versioned code/config hashes, parameters, artifact
references, and decision status. `(factor_id, factor_version)` is unique.
Duplicate version registration is rejected.

Reviewed validation evidence is read from `factor_validation_runs`. Approval
evidence is read from `promotion_decisions`. Deprecated records are not deleted
or hidden; they remain queryable.

Registry writes from `alpha factor validate` must target temp/local SQLite paths
outside the repository. No registry database under `metadata/` is created or
committed by this phase.

## CLI

Help:

```bash
python -m alpha_system.cli factor validate --help
```

Example validation:

```bash
PYTHONPATH=src python -m alpha_system.cli factor validate \
  configs/factors/examples/valid_draft_factor.json \
  --registry-path /tmp/alpha_system/example_factor_registry.sqlite3 \
  --summary-out /tmp/alpha_system/example_factor_summary.json
```

Inputs:

```text
spec_path
--registry-path
--code-path
--validation-artifact-path
--summary-out
--used-field
--json
```

The command prints a small summary. If `--summary-out` is supplied, it writes a
small JSON or Markdown summary to a local-only path. If `--registry-path` is
supplied for a valid draft or candidate spec, the command writes a temp/local
registry entry. It does not compute factor values, write Parquet/Arrow/Feather,
write into repo-local `data/`, create a committed SQLite database, or implement
`alpha factor materialize`.
