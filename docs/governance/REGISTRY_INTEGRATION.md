# Governance Registry Integration

`alpha_system.governance.registry` persists validated governance metadata in the
existing local SQLite metadata registry. It is protocol machinery only. It does
not ingest data, compute factor or label values, run diagnostics, route orders,
approve live use, or make market claims.

## Persistence Contract

The governance registry uses `alpha_system.core.registry.init_registry` and
`connect_registry` for the existing local persistence layer. When
`GovernanceRegistry` or `init_governance_registry` opens a database, it ensures
two schema-only governance tables inside that local SQLite registry:

| Table | Purpose |
| --- | --- |
| `governance_objects` | Immutable validated object payloads keyed by typed governance ID. |
| `governance_lifecycle_states` | Immutable ID-to-lifecycle-state associations for state lookup. |

Each object write validates through the object's existing fail-closed validator
before any row is inserted. The stored payload is canonical governance JSON, and
the stored content hash is recomputed on read. Existing object rows are
idempotent only when kind, payload, and hash match exactly; conflicting writes
fail closed instead of rewriting ledger history.

Supported object families are:

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

## ID And State Lookup

`GovernanceRegistry.save(...)` persists a validated object under a declared MVP
lifecycle state. `get(...)` and `get_object(...)` load by typed governance ID and
return a revalidated object. `list_by_lifecycle_state(...)` resolves objects
recorded under a lifecycle state, optionally narrowed by governance object kind.

Reads fail closed with `GovernanceValidationError` for missing records, malformed
JSON, object-kind mismatches, lifecycle-state mismatches, ID/content mismatches,
and content-hash mismatches. The registry does not silently coerce partial rows
into objects.

## Gate Preservation

The registry does not expose a state-transition, force-promote, self-approve, or
ledger-rewrite API. It persists records and state associations only after the
same validators and gate logic used by the in-memory governance contracts pass.

Two write paths require the existing promotion gate context:

- `ReviewerVerdict` writes require `PromotionGateContext` and validate
  `EVIDENCE_READY -> REVIEWED`, including reviewer identity and role
  independence.
- `PromotionDecision` writes require `PromotionGateContext` and validate
  `REVIEWED -> decision.next_state`, including reviewer-verdict linkage and the
  candidate/validated evidence and trial-ledger blocks where applicable.

This preserves the established blocks for missing evidence, missing trial
ledger records, failed-run omission, unrecorded locked-test contamination,
self-review, and prohibited MVP states.

## Temp-DB Tests

Integration tests live in `tests/integration/governance/test_registry_integration.py`.
They create a SQLite registry only under pytest `tmp_path`, persist synthetic
validated governance objects, resolve them by ID and lifecycle state, and assert
that invalid writes and malformed rows fail closed.

No test writes a database under `metadata/` or another commit-eligible path.

## No-DB-Commit Policy

SQLite registries are local-only runtime artifacts. Do not stage or commit
`metadata/*.sqlite`, `*.sqlite3`, `*.db`, journal files, WAL files, or any
database produced while exercising the governance registry. Commit only source,
tests, docs, and handoffs authorized by the active phase spec.
