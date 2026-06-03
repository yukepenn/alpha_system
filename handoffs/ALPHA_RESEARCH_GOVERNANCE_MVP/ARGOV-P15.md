# ARGOV-P15 Handoff - Governance Registry Integration

## Summary

Implemented `alpha_system.governance.registry` as a local SQLite-backed
governance registry using the existing `alpha_system.core.registry` persistence
contract. The module uses `init_registry`, `connect_registry`, and
`resolve_registry_path`, then ensures schema-only governance tables inside the
local registry database:

- `governance_objects` for immutable validated object payloads keyed by typed
  governance ID.
- `governance_lifecycle_states` for immutable ID-to-lifecycle-state associations
  used by state lookup.

No new database technology was introduced. No core registry migration was added;
the governance module registers its schema through the existing local registry
connection contract when `GovernanceRegistry` or `init_governance_registry` is
used.

The registry persists and resolves these validated governance records:

- `HypothesisCard`
- `AlphaSpec`
- `FeatureRequest`
- `LabelSpec`
- `StudySpec`
- `TrialLedgerRecord`
- `EvidenceBundle`
- `RejectedIdeaRecord`
- `PromotionDecision`
- `ReviewerVerdict`
- `NegativeControlResult`

Read paths return validated objects by typed ID through `get_object(...)` or full
registry entries through `get(...)`. `list_by_lifecycle_state(...)` resolves
validated entries by MVP lifecycle state with optional object-kind narrowing.
Missing records, malformed payload JSON, object-kind mismatches, lifecycle-state
mismatches, ID mismatches, and content-hash mismatches fail closed with
structured `GovernanceValidationError` issues.

## Gate Preservation

The registry does not expose a state-transition, force-promote, self-approve, or
ledger-rewrite API. Object rows are immutable: repeated writes are idempotent
only when object kind, payload, and content hash match exactly; conflicting
writes fail closed with `governance_record_rewrite_blocked`.

`ReviewerVerdict` writes require `PromotionGateContext` and validate the existing
`EVIDENCE_READY -> REVIEWED` promotion-gate path, including reviewer identity
and role independence.

`PromotionDecision` writes require `PromotionGateContext` and validate the
existing `REVIEWED -> decision.next_state` promotion-gate path, including
reviewer-verdict linkage plus the evidence/trial-ledger blocks for
`CANDIDATE`/`VALIDATED` where applicable.

The registry persists governance metadata only. It does not compute factors or
labels, run diagnostics, ingest real data, operate brokers, route orders, grant
live approval, allocate capital, or assert alpha/profitability/tradability.

## Temp-DB Test Approach

Added `tests/integration/governance/test_registry_integration.py`. The tests
create SQLite registries only under pytest `tmp_path`, persist synthetic
validated governance objects, resolve records by typed ID and lifecycle state,
exercise missing/malformed read errors, and assert that reviewer/promotion writes
require the existing gate context.

No database is created under `metadata/` by the tests. The final metadata audit
returned empty output.

## README Snapshot

Updated `README.md` to reflect that `ARGOV-P15` completed executor deliverables
for Ralph validation and independent review, that
`alpha_system.governance.registry` and
`docs/governance/REGISTRY_INTEGRATION.md` are durable governance machinery, that
the active/next planned phase is `ARGOV-P16 - Governance CLI and Validation
Tools`, and that the safety boundaries are unchanged.

## Staged Files

Exact files to stage explicitly:

- `README.md`
- `docs/governance/REGISTRY_INTEGRATION.md`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P15.md`
- `src/alpha_system/governance/registry.py`
- `tests/integration/governance/test_registry_integration.py`

No `runs/**` path is included.

## Validation Results

Spec-requested validation:

- `git status --short` - passed before handoff/staging with only allowed ARGOV-P15
  paths:

```text
 M README.md
 M src/alpha_system/governance/registry.py
?? docs/governance/REGISTRY_INTEGRATION.md
?? tests/integration/governance/
```

- `python tools/verify.py --smoke` - passed with exit 0 and no output.

- `python -m pytest tests/unit/governance -q` - passed:

```text
466 passed in 0.30s
```

- `python -m pytest tests/integration/governance -q` - passed:

```text
4 passed in 0.98s
```

- `test -f docs/governance/REGISTRY_INTEGRATION.md` - passed with exit 0 and no
  output.

- `find metadata -type f ! -name README.md ! -name .gitkeep -print` - passed
  with empty output after tests.

- `git ls-files runs` - passed with empty output.

Additional local validation:

- `python -m pytest tests/integration/governance/test_registry_integration.py -q`
  - passed:

```text
4 passed in 0.94s
```

- `python -m ruff format src/alpha_system/governance/registry.py tests/integration/governance/test_registry_integration.py`
  - passed; initial run reformatted both files and the final run reported:

```text
2 files left unchanged
```

- `python -m ruff check src/alpha_system/governance/registry.py tests/integration/governance/test_registry_integration.py`
  - initially found import ordering plus `UP040`; both were repaired.

- `python -m ruff check src/alpha_system/governance/registry.py tests/integration/governance/test_registry_integration.py`
  - passed after repair:

```text
All checks passed!
```

- `git diff --check` - passed with exit 0 and no output.

Skipped checks: none of the spec-requested executor validation commands were
skipped. Claude review, reviewer execution, `review.md`, and `verdict.json` were
not run or created by Codex because the executor prompt reserves review and
verdict handling for Ralph and the independent reviewer.

## Artifact Policy

- `find metadata -type f ! -name README.md ! -name .gitkeep -print` returned
  empty output after tests.
- `git ls-files runs` returned empty output.
- No SQLite, DB, DB journal, WAL, raw/canonical/factor/label/cache data, Parquet,
  Arrow, Feather, log, cache, model binary, generated report bundle, credential,
  or heavy artifact is staged.
- No `runs/**` path is staged.
- No run-local `review.md`, `verdict.json`, `checks.json`, or repair artifact was
  created by Codex.

## Staging Discipline

Explicit staging only. `git add .`, `git add -A`, force push, PR creation, merge,
reviewer invocation, and destructive cleanup were not used. No commit was created
by Codex in this executor step.

Post-staging validation:

- `git diff --cached --name-only` - passed after explicit staging with exactly
  this curated set:

```text
README.md
docs/governance/REGISTRY_INTEGRATION.md
handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P15.md
src/alpha_system/governance/registry.py
tests/integration/governance/test_registry_integration.py
```

- `git diff --cached --check` - passed with exit 0 and no output.

- `git diff --cached --name-only | rg '^runs/'` - passed with no matches. `rg`
  returned exit 1 because no staged path matched `runs/`.

- `git diff --cached --name-only | rg '(^data/(raw|canonical|factors|labels|cache)/|^metadata/|^artifacts/|\.(sqlite|sqlite3|db|db-journal|wal|parquet|arrow|feather|pkl|joblib|onnx|npy|log)$)'`
  - passed with no matches. `rg` returned exit 1 because no staged path matched
  forbidden artifact patterns.

## Scope Confirmation

No broker, live, paper, order-routing, production deployment, real-data
ingestion, alpha search, factor computation, label materialization, strategy
optimization, portfolio allocation, alpha/profitability/tradability claim, live
approval claim, capital allocation claim, or production-readiness claim was
introduced.
