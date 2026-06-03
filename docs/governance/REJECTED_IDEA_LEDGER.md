# RejectedIdeaLedger

`ARGOV-P10` adds `RejectedIdeaRecord` metadata and an append-only
`ResearchGraveyardLedger` for rejected, duplicate, leaky, weak, costly, failed,
or out-of-scope research ideas. The ledger is governance machinery only. It
does not run studies, compute factors or labels, ingest data, persist registry
state, make promotion decisions, or make market claims.

The invariant installed by this phase is:

```text
Rejected ideas are first-class records, not prose.
```

A rejected record is a durable audit entry. It does not mean the idea is
permanently banned. Future reconsideration must be explicit, linked, and
visible beside the original rejection.

## Record Fields

`RejectedIdeaRecord` carries exactly these required fields:

| Field | Meaning |
| --- | --- |
| `rejected_id` | Deterministic `RejectedIdeaRecord` governance ID with the `rej` prefix, generated from all non-ID content fields. |
| `alpha_spec_id_or_hypothesis_id` | Valid `AlphaSpec` ID with the `aspec` prefix or `HypothesisCard` ID with the `hyp` prefix. |
| `reason_category` | Closed rejection category from the set documented below. |
| `evidence_references` | Non-empty list of explicit evidence references, such as trial, evidence-bundle, diagnostic, review, or duplicate-check references. These are references only, not embedded evidence. |
| `duplicate_links` | Non-empty list of duplicate, equivalence, or duplicate-check references that make duplicate context visible. |
| `leakage_cost_weakness_notes` | Non-empty list of explicit notes recording leakage, cost, weakness, failed-diagnostic, scope, or other reviewer rationale. |
| `reviewer` | Explicit reviewer reference that records who accepted the rejection record. |
| `created_at` | UTC timestamp in `YYYY-MM-DDTHH:MM:SSZ` format. |

Validation is fail-closed. Missing fields, null fields, empty required lists,
empty or vague strings, malformed governance IDs, unknown fields, unknown reason
categories, invalid timestamps, non-canonical values, duplicate references, and
mismatched deterministic IDs raise `GovernanceValidationError`.

## Reason Categories

The allowed `reason_category` values are:

| Category | Semantics |
| --- | --- |
| `duplicate` | The idea duplicates, materially overlaps, or is equivalent to an existing hypothesis, AlphaSpec, or feature request. |
| `leakage` | The idea depends on lookahead, target leakage, locked-test contamination, or another inadmissible information path. |
| `weak_evidence` | The available evidence is incomplete, too weak, or fails to satisfy the campaign evidence standard. |
| `cost` | The expected implementation, compute, data, review, or maintenance cost is not justified under the current research budget. |
| `failed_diagnostics` | A referenced diagnostic, trial, negative control, or validation check failed or was abandoned. |
| `out_of_scope` | The idea is outside the approved campaign, data, market, instrument, or operational scope. |
| `other` | A reviewer-recorded reason that does not fit the other closed categories. |

Unknown categories fail closed instead of being coerced into `other`.

## Serialization

`RejectedIdeaRecord.to_dict()` returns a strict JSON-compatible representation
in the campaign-required field order. `to_canonical_json()` uses the shared
canonical serialization primitive, and `from_canonical_json()` deserializes then
validates the record. The `rejected_id` is regenerated during validation and
must match the record content.

## Research Graveyard Ledger

`ResearchGraveyardLedger` is an in-memory append-only abstraction. It supports:

- appending a validated rejected record;
- listing all rejected records in append order;
- looking up a rejected record by `rejected_id`;
- looking up rejected records by the referenced `AlphaSpec` or `HypothesisCard`;
- serializing a ledger snapshot through canonical JSON.

The ledger has no delete, remove, or overwrite API. Appending a second record
with the same `rejected_id` raises a validation error. This keeps failures and
rejections visible instead of allowing them to disappear through an update path.

The ledger does not persist to a registry or database. Later phases own any
registry integration.

## Explicit Reconsideration

Rejection is not a permanent ban. Reconsideration is modeled with
`RejectedIdeaReconsideration`, an explicit relationship carrying:

- the original `rejected_id`;
- the reconsidered `AlphaSpec` or `HypothesisCard` ID;
- a reconsideration note or pointer;
- rationale;
- reviewer;
- creation timestamp.

The ledger appends reconsideration links separately from rejected records. A
reconsideration link must point to an existing rejected record, and duplicate
links for the same rejected record fail closed. The original
`RejectedIdeaRecord` remains visible and unchanged; reconsideration is never an
in-place mutation or silent revival.

## Scope Boundary

This phase defines governance metadata only. It does not implement
`PromotionDecision`, the promotion-gate state machine, `EvidenceBundle`,
registry persistence, diagnostics execution, factor computation, real-data
ingestion, alpha search, broker operations, paper trading, live trading, order
routing, deployment behavior, or any alpha/profitability/tradability claim.
