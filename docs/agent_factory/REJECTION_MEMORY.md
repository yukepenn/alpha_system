# Agent Factory Rejected-Idea and Research Memory

`alpha_system.agent_factory.memory.models` defines passive, value-free memory
contracts for rejected ideas and research outcomes. The module keeps failed and
rejected ideas visible, supports deterministic duplicate checks, and surfaces
prior rejection reasons before a future draft can be accepted.

This is a contract layer only. It does not instantiate an autonomous agent,
start a continuous research runner, search for alpha, promote a factor, write a
registry, call a provider, read raw data, or make alpha, tradability,
profitability, strategy, paper, live, broker, order, deployment, or production
claims.

## Model

- `RejectedIdeaMemoryRecord` stores one visible rejected or failed idea memory
  row: deterministic `idea_key`, full `idea_fingerprint`, status,
  optional `alpha_spec_id`, originating role, linked governance graveyard
  `rejected_id` refs, rejection reasons, linked decision/handoff/tool/spec refs,
  next required gate, summary, and limitations.
- `ResearchMemoryRecord` stores one value-free research memory entry: idea key,
  fingerprint, status, originating role, prior-outcome summary, linked
  `AgentDecisionRecord` / `AgentHandoff` / `ToolInvocationRecord` ids, spec
  refs, related rejected-memory refs, next required gate, and limitations.
- `DuplicateIdeaReport` is the pure duplicate-check result. It carries the
  matched memory refs, matched graveyard refs, surfaced rejection reasons, and
  next required gate.

All three records carry ids, refs, statuses, summaries, and reasons only. They
reject bytes, mutable payloads, dataframe/array objects, raw/provider markers,
embedded value markers, raw/canonical/cache/metadata paths, and heavy artifact
suffixes such as parquet, arrow, feather, dbn, zst, SQLite/DB, WAL, numpy,
pickle, joblib, ONNX, and logs.

## Governance Graveyard Boundary

Memory consumes the governance graveyard by import:

```text
alpha_system.governance.rejected_idea.RejectedIdeaRecord
alpha_system.governance.rejected_idea.ResearchGraveyardLedger
```

It does not redefine those contracts and does not edit
`alpha_system.governance`. A memory row stores graveyard `rejected_id` refs and
short rejection reasons; the source graveyard remains the authoritative
append-only ledger for `RejectedIdeaRecord` details and reconsideration links.

`ensure_rejected_ideas_visible(memory_records, graveyard)` fails closed when a
graveyard rejection has no corresponding visible memory row, or when memory
points at an unknown graveyard record. This prevents hidden or dropped rejected
ideas.

## Duplicate Avoidance

`idea_key(candidate)` and `idea_fingerprint(candidate)` canonicalize a
value-free idea summary and hash it deterministically. They accept a short
string or a mapping of string fields. They reject raw/heavy markers, bytes,
dataframes, arrays, and non-string payload values.

`detect_duplicate_idea(candidate, memory_records, graveyard)` is pure
in-memory logic. It performs no I/O, network access, filesystem access, DB
write, registry write, or provider call. It checks:

- deterministic idea-key matches in `RejectedIdeaMemoryRecord`;
- linked graveyard records for matched memory rows;
- candidate governance idea refs (`aspec_*` or `hyp_*`) already present in
  `ResearchGraveyardLedger`; and
- candidate governance refs listed as duplicate links in the graveyard.

When a duplicate or prior rejection is found, the report surfaces the prior
rejection reasons before a new draft can proceed.

## Prior-Rejection Surfacing

`prior_rejection_reasons(known_idea_key, memory_records, graveyard)` returns
the recorded rejection reasons for a known deterministic idea key. The result
is value-free text from memory plus summarized governance reason-category notes
by ref. A future Hypothesis Scout can be shown why an idea was previously
rejected without embedding raw data, diagnostics payloads, reports, or feature
and label values.

## Not a Library or Registry

This memory model is not a FactorLibrary, AlphaBook, registry writer,
promotion surface, diagnostics runner, or research scheduler. Recording an
idea as rejected, failed, duplicate, inconclusive, watched, blocked, or
reference-handoff-recorded is not evidence that an alpha exists and is not
factor promotion, candidate validation, strategy validation, tradability
evidence, or approval for paper/live/broker/order activity.
