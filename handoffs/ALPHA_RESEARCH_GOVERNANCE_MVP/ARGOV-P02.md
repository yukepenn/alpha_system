# ARGOV-P02 Handoff — Governance IDs, Serialization, and Validation Primitives

## Summary

Delivered shared governance primitives only:

- `alpha_system.governance.ids` defines canonical governance ID kinds and prefixes from
  `docs/governance/NAMING.md`, deterministic ID generation, typed parsing, and ID
  validation.
- `alpha_system.governance.serialization` defines canonical JSON serialization,
  deserialization, and SHA-256 content hashing over the canonical form.
- `alpha_system.governance.validation` defines structured validation issues, a structured
  validation error, required-field checks, declared-type checks, unknown-field rejection,
  and a minimal `validate_schema(...)` helper.
- `docs/governance/PRIMITIVES.md` documents the deterministic and fail-closed primitive
  contract.
- Focused governance unit tests cover deterministic IDs, malformed ID rejection,
  deterministic serialization and hashing, duplicate-key rejection, required-field
  rejection, type rejection, and unknown-field rejection.

No tiny fixtures were needed.

## Public Primitive Contract

### IDs

Governance IDs use `<prefix>_<24-lowercase-hex-token>`.

The accepted prefixes are `hyp`, `aspec`, `freq`, `lspec`, `sspec`, `trial`, `evb`,
`rej`, `prom`, `rver`, `nctrl`, and `abook`, matching `docs/governance/NAMING.md`.

`generate_governance_id(kind, components)` is deterministic for identical canonical
object kind and logical component mapping. It uses canonical serialization and SHA-256; it
does not use wall-clock time, random entropy, filesystem state, broker state, or external
state.

`parse_governance_id(...)` and `validate_governance_id(...)` reject malformed IDs,
unknown prefixes, wrong expected prefixes, and wrong expected kinds with
`GovernanceIdError`, which carries a structured `GovernanceIdIssue`.

### Serialization And Hashing

`canonical_serialize(...)` emits deterministic JSON with sorted keys, compact separators,
ASCII output, and finite numbers only. It accepts strict JSON-compatible values and rejects
values that cannot round-trip faithfully as JSON, including non-string mapping keys and
sets.

`deserialize(...)` rejects non-string input, malformed JSON, and duplicate JSON keys.
`deserialize(canonical_serialize(x))` reproduces the logical JSON value.

`content_hash(...)` hashes the canonical serialized form with SHA-256. Field reordering
does not change the hash. Logical content changes do change the hash.

### Validation

Validation fails closed. Missing required fields, null required fields, invalid declared
types, non-mapping roots, invalid schema declarations, and undeclared fields when an
allowed-field set is supplied raise `GovernanceValidationError` with structured
`ValidationIssue` entries.

Valid mappings are returned unchanged. The validation primitives do not coerce values, add
implicit defaults, accept `bool` as `int`, or drop undeclared fields.

## Staged Files

Exact staged files after explicit staging:

- `README.md`
- `docs/governance/PRIMITIVES.md`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P02.md`
- `src/alpha_system/governance/__init__.py`
- `src/alpha_system/governance/ids.py`
- `src/alpha_system/governance/serialization.py`
- `src/alpha_system/governance/validation.py`
- `tests/unit/governance/test_ids.py`
- `tests/unit/governance/test_serialization.py`
- `tests/unit/governance/test_validation.py`

No `runs/**` path is staged.

## Validation Results

- `git status --short` — succeeded before handoff/staging. Output showed only allowed
  ARGOV-P02 paths:

```text
 M README.md
 M src/alpha_system/governance/__init__.py
 M src/alpha_system/governance/ids.py
 M src/alpha_system/governance/serialization.py
 M src/alpha_system/governance/validation.py
?? docs/governance/PRIMITIVES.md
?? tests/unit/governance/test_ids.py
?? tests/unit/governance/test_serialization.py
?? tests/unit/governance/test_validation.py
```

- `python -m pytest tests/unit/governance -q` — passed:

```text
...........................                                              [100%]
27 passed in 0.04s
```

- `python tools/verify.py --smoke` — passed with exit 0 and no output.
- `git ls-files runs` — passed with empty output.
- `find data -type f ! -name README.md ! -name ".gitkeep" -print` — passed with
  empty output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` — passed with
  empty output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` — passed with
  empty output.

Skipped checks: none.

## Artifact Policy

- `git ls-files runs` returned empty.
- `git diff --cached --name-only` contains no `runs/` path.
- The `data`, `metadata`, and Parquet audits returned empty output.
- No forbidden data, raw/canonical/factor/label/cache data, local DB, DB journal, WAL,
  Parquet, Arrow, Feather, pickle, model binary, log, cache, heavy artifact, or run
  artifact is staged.
- No run-local `handoff.md`, `review.md`, `verdict.json`, `checks.json`, or
  `repair_attempts/` artifact was created or staged.

## Staging Discipline

- Explicit staging only.
- The staged set was built with explicit file paths.
- `git add .` was not used.
- `git add -A` was not used.
- No force push was performed.
- No PR was created.
- No merge was performed.

## Scope Confirmation

- No specific governance object schema or behavior was added.
- No persistence, registry integration, state machine, gate, CLI, report builder, or
  template was added.
- No unrelated `src/alpha_system` subpackage was modified.
- No tests outside `tests/unit/governance/` were added, removed, skipped, weakened, or
  relaxed.
- No broker, live, paper, order-routing, production-deployment, real-data-ingestion,
  alpha-search, L2 replay, ML/DL, strategy-optimization, or portfolio-allocation scope was
  introduced.
- No alpha, profitability, tradability, paper-readiness, live-readiness, broker-readiness,
  capital-allocation, or production-readiness claim was introduced.

## Review Boundary

No Claude review was run by Codex. No `review.md` or `verdict.json` was created. Ralph owns
validation orchestration, independent review routing, verdict parsing, PR creation, CI,
merge gates, semantic done-checks, and phase PASS marking.
