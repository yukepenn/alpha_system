# ASV1-P09 Handoff

## Phase

- Phase ID: `ASV1-P09`
- Phase name: FactorSpec, Factor Registry, and Lifecycle
- Campaign: `ALPHA_SYSTEM_V1`
- Lane: Yellow
- Branch: `auto/alpha_system_v1/asv1-p09-factorspec-factor-registry-and-lifecycle`
- Base commit observed by Codex: `a726575`
- Run directory: `runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/phases/ASV1-P09` (local-only)

## Scope Completed

Implemented the scoped factor governance layer:

- validated `FactorSpec` contract with all required fields;
- declared factor input/dependency validation;
- lifecycle state parsing, legal transitions, and review/materialization gates;
- SQLite registry helpers over the ASV1-P05 tables;
- review-gated validation and promotion checks;
- `alpha factor validate` CLI registration and behavior;
- tiny synthetic example specs;
- factor registry documentation;
- required unit and integration coverage.

No factor computation engine, factor materialization command, factor values,
labels, signals, strategies, broker/paper/live code, order routing, deployment,
reviewer call, PR creation, merge, or PASS marking was introduced.

## FactorSpec Field Mapping

`src/alpha_system/factors/spec.py` defines and validates:

```text
factor_id -> lower-case stable identifier
name -> non-empty display name
version -> version token
owner -> non-empty owner string
description -> non-empty description
input_fields -> non-empty declared input list
parameters -> JSON mapping
frequency -> FactorFrequency enum
warmup_bars -> non-negative integer
session_reset -> boolean
availability_lag -> non-negative seconds as timedelta
factor_type -> FactorType enum
evaluation_type -> FactorEvaluationType enum
code_hash -> lowercase SHA-256 digest
config_hash -> lowercase SHA-256 digest
status -> FactorStatus lifecycle state
created_at -> ISO-8601 datetime normalized to UTC
validation_artifact_path -> string/null artifact reference with artifact-policy checks
```

`config_hash` is computed from the config with the self-referential
`config_hash` field excluded. `code_hash` can be verified against one or more
caller-provided code paths.

## Lifecycle And Materialization Rules

States represented:

```text
draft
candidate
validated
approved
deprecated
```

Legal transitions:

```text
draft -> candidate
draft -> deprecated
candidate -> validated
candidate -> deprecated
validated -> approved
validated -> deprecated
approved -> deprecated
```

Illegal transitions such as `draft -> approved` and `candidate -> approved`
are rejected. `candidate`, `validated`, and `approved` require a validation
artifact reference. `validated` requires reviewed validation evidence in the
registry. `approved` requires a review-backed promotion decision in
`promotion_decisions`. Draft long-term factor-value materialization is blocked
by default; this phase does not implement a materialization path.

## Registry Behavior

Implemented in `src/alpha_system/factors/registry.py` against the ASV1-P05
schema:

```text
factor_registry
factor_versions
factor_validation_runs
promotion_decisions
```

`register_factor_spec` upserts `factor_registry` identity/status metadata and
inserts unique `(factor_id, factor_version)` rows in `factor_versions`.
Duplicate versions are rejected. Deprecated factor versions remain queryable
through `get_factor_version`.

Reviewed validation evidence is matched through `factor_validation_runs`
using `factor_versions_json`, code/config hashes, a reviewed decision status,
and a validation artifact reference. Approved status is accepted only when a
matching `promotion_decisions` row has an accepted/approved review status,
non-empty reviewer, non-empty rationale, and `metadata_json.review_backed`.

The CLI writes registry rows only for valid `draft` or `candidate` specs and
only to temp/local SQLite paths outside the repository.

## CLI Behavior

Introduced:

```bash
alpha factor validate
```

Module usage when source is importable:

```bash
PYTHONPATH=src python -m alpha_system.cli factor validate --help
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

`--registry-path` defaults to `/tmp/alpha_system/factor_registry.sqlite3`.
Tests pass temp paths. `--summary-out` writes only small JSON/Markdown
summaries to local-only allowed paths. The command does not compute factor
values, write Parquet/Arrow/Feather, create a committed registry DB, or write
into repo-local `data/`.

## Files Changed

Commit-eligible files changed:

```text
configs/factors/examples/invalid_label_input_factor.json
configs/factors/examples/valid_candidate_factor.json
configs/factors/examples/valid_draft_factor.json
docs/FACTOR_REGISTRY.md
handoffs/ASV1-P09.md
src/alpha_system/cli/factor.py
src/alpha_system/cli/main.py
src/alpha_system/factors/dependency_spec.py
src/alpha_system/factors/lifecycle.py
src/alpha_system/factors/registry.py
src/alpha_system/factors/spec.py
src/alpha_system/factors/validation.py
tests/integration/test_factor_no_output_artifacts.py
tests/integration/test_factor_registry_tempdb.py
tests/integration/test_factor_validate_cli.py
tests/unit/test_factor_dependency_validation.py
tests/unit/test_factor_hashes.py
tests/unit/test_factor_lifecycle.py
tests/unit/test_factor_lifecycle_transitions.py
tests/unit/test_factor_promotion_requires_review.py
tests/unit/test_factor_spec_fields.py
```

These same paths were staged explicitly after validation. `git add .`,
`git add -A`, force push, PR creation, merge, reviewer execution, `review.md`,
and `verdict.json` were not used.

## Validation Results

Commands run by Codex:

```text
test -e runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/STOP
PASS - exit 1; no STOP file was active.

python -m pytest tests/unit/test_factor_spec_fields.py tests/unit/test_factor_lifecycle.py tests/unit/test_factor_lifecycle_transitions.py tests/unit/test_factor_dependency_validation.py tests/unit/test_factor_hashes.py tests/unit/test_factor_promotion_requires_review.py tests/integration/test_factor_registry_tempdb.py tests/integration/test_factor_validate_cli.py tests/integration/test_factor_no_output_artifacts.py
PASS - 58 passed.

python -m pytest tests/unit tests/integration
PASS - 154 passed.

python -m alpha_system.cli factor validate --help
FAIL - exit 1; `/usr/bin/python: Error while finding module specification for
'alpha_system.cli' (ModuleNotFoundError: No module named 'alpha_system')`.
Reason: this source-layout checkout is not installed into the host interpreter,
matching the known ASV1-P05/ASV1-P08 environment limitation.

PYTHONPATH=src python -m alpha_system.cli factor validate --help
PASS - exit 0; factor validate help printed with the expected arguments.

alpha factor validate --help || true
NON-BLOCKING - exit 0 due to `|| true`; console script is not installed in
this shell (`alpha: command not found`).

python -m compileall src
PASS - exit 0.

python -m ruff check src tests || true
UNAVAILABLE - exit 0 due to `|| true`; `/usr/bin/python: No module named ruff`.

python -m mypy src || true
UNAVAILABLE - exit 0 due to `|| true`; `/usr/bin/python: No module named mypy`.

git diff --check
PASS - exit 0.

find data/factors -type f ! -name README.md ! -name .gitkeep -print
PASS - exit 0; returned empty.

find metadata -type f ! -name README.md ! -name .gitkeep -print
PASS - exit 0; returned empty.

find . -path './tests/fixtures/*' -prune -o -type f \( -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' \) -print
PASS - exit 0; returned empty.

find . -type f \( -name '*.sqlite' -o -name '*.sqlite3' -o -name '*.db' -o -name '*.db-journal' -o -name '*.wal' \) -print
PASS - exit 0; returned empty.

git ls-files runs
PASS - exit 0; returned empty.

git diff --cached --name-only
PASS - exit 0; returned exactly the staged files listed in Files Changed.

git diff --cached --name-only | rg '^runs/'
PASS - exit 1; returned empty, so no runs path is staged.

git diff --cached --name-only | rg '(^data/|^metadata/|^artifacts/|\.parquet$|\.arrow$|\.feather$|\.sqlite$|\.sqlite3$|\.db$|\.db-journal$|\.wal$|\.log$|__pycache__|\.pyc$|\.pkl$|\.pickle$|\.joblib$|\.onnx$|\.npy$|\.npz$)'
PASS - exit 1; returned empty, so no forbidden artifact/cache/heavy path is staged.

git diff --cached --check
PASS - exit 0; returned empty.
```

## Artifact Policy Confirmation

- Commit-eligible allowed paths are separated from local-only `runs/**`.
- No `runs/**` path was staged or committed.
- `git ls-files runs` returned empty.
- No computed factor output, factor Parquet, Arrow, Feather, local factor
  store, local registry DB, journal, WAL, raw data, canonical data, label data,
  cache, log, model artifact, or heavy artifact was created in the repo tree,
  staged, or committed.
- No SQLite/DB file was created under `metadata/`.
- No broker, paper trading, live trading, order routing, or production
  execution scope was introduced.
- No alpha, profitability, robustness, tradability, or production-readiness
  claim was introduced.
- No tests were weakened, skipped, xfailed, or visibly gated for tests.

## Relevant Risk Status

- R-015 Candidate promotion without review: mitigated by lifecycle validation,
  registry promotion-decision checks, and promotion tests.
- R-001 Lookahead leakage: mitigated in this phase by availability lag,
  session reset, and dependency/label boundary validation.
- R-005 Factor/label misalignment: mitigated by rejecting label-like fields
  and `label` domains as factor inputs.
- R-014 Alpha/tradability overclaiming: mitigated; docs/configs/CLI summaries
  make no such claim and state the limit explicitly.
- R-018 SQLite schema drift: mitigated by using the ASV1-P05 tables directly
  and temp-DB integration tests.
- R-037 CLI writes to local-only paths during tests: mitigated by temp-path
  CLI tests and clean repo artifact audits.
- R-038 Generated SQLite DB committed: mitigated by temp DB use and DB-file
  audits returning empty.
- R-039 Generated Parquet committed: mitigated by no factor output path and
  Parquet/Arrow/Feather audits returning empty.

## Known Limitations And Review Focus

- The raw `python -m alpha_system.cli factor validate --help` command fails
  until the source-layout package is installed or `PYTHONPATH=src` is provided.
  The introduced command help works when the source tree is importable.
- YAML FactorSpec parsing is intentionally not implemented; JSON examples and
  JSON CLI parsing avoid adding a new dependency in this phase.
- Registry validation represents reviewed evidence and promotion decisions; it
  does not perform the semantic review itself.

Review should focus on lifecycle gate correctness, the approval/promotion
evidence matching, dependency and label-leakage rejection, ASV1-P05 schema
alignment, and artifact-policy boundaries.

## Next Step

Ralph should run formal handoff validation, route the required Yellow-lane
Claude review, parse the verdict, and continue the Workflow 2 gate sequence.
