# Agent Factory Acceptance Audit

## Audit Verdict

`COMPLETE_WITH_WARNINGS`

The audit covers the six `campaign.yaml` acceptance gates and the
cross-cutting checklist from `ACCEPTANCE.md`. The campaign satisfies the
contracts-only MVP acceptance surface with warnings for the P23 synthetic dry
run fallback and the open future blockers `FEATURE_LABEL_PARQUET_SINK_V1` and
`SESSION_LABEL_GUARD_FIX_V1`. This document does not self-approve `AGENT-P25`
or replace the required fresh YELLOW-lane review.

## Gate Audit

| Gate | Coverage | Audit status |
| --- | --- | --- |
| `bootstrap_and_entry` | `AGENT-P00`, `AGENT-P01`, `AGENT-P02` | `PASS` |
| `core_contracts` | `AGENT-P03`, `AGENT-P04`, `AGENT-P05`, `AGENT-P06` | `PASS` |
| `agent_roles` | `AGENT-P07` - `AGENT-P15` | `PASS` |
| `enforcement_and_records` | `AGENT-P16`, `AGENT-P17`, `AGENT-P18` | `PASS` |
| `assets_and_bridge` | `AGENT-P19`, `AGENT-P20`, `AGENT-P21` | `PASS` |
| `dry_run_and_closeout` | `AGENT-P22`, `AGENT-P23`, `AGENT-P24`, `AGENT-P25` | `PASS_WITH_WARNINGS` |

The gate mapping in `campaign.yaml` covers all 26 phases exactly once:
`AGENT-P00` through `AGENT-P25`.

## Cross-Cutting Checklist

| Check | Audit finding |
| --- | --- |
| Contracts-only posture | Held. The campaign defines contracts, records, docs, templates, a runtime adapter, and a bounded dry-run harness. It does not instantiate autonomous agents or start a continuous research runner. |
| Existing primitives consumed, not duplicated | Held. The Agent Factory consumes existing `runtime.*`, `governance.*`, `research.*`, `experiments.*`, `backtest.*`, `features.*`, `labels.*`, and `data.foundation.*` primitives through refs and adapters; it does not edit consumed primitive packages in closeout. |
| Entry contract and preflight gates | Held with warnings. `entry_contract` encodes seed FeaturePack/LabelPack markers, runtime real-smoke status, `FEATURE_LABEL_PARQUET_SINK_V1`, and `SESSION_LABEL_GUARD_FIX_V1`; missing local seed registries degrade to `PREFLIGHT_WARN`, and explicit unsatisfied blockers fail closed. |
| Permission matrix | Held. The matrix is default-deny/fail-closed and has explicit entries for Research Director, Hypothesis Scout, AlphaSpec Critic, Data Contract Auditor, Feature Engineer, Label Engineer, No-Lookahead Auditor, Diagnostics Runner, Statistical Reviewer, and Librarian. |
| Separation of duties | Held. Code checks block generator self-approval, implementer self-review, diagnostics-runner promotion, non-independent reviewers, missing matrix coverage, weakened human/red-lane markers, and Librarian write paths without reviewer verdict refs. |
| Structured value-free outputs | Held. `AgentToolResult` is the agent-facing result envelope and carries ids, refs, summaries, statuses, limitations, blockers, and next gates. It rejects raw/heavy payloads and provider/value material. |
| Provider and data boundary | Held. Agent Factory code is local-first and accepted-DatasetVersion-only. It does not read raw provider files, call Databento, call IBKR, or bypass `resolve_dataset_version` for runtime bridge admissibility. |
| Failed and rejected ideas visible | Held. Rejected-idea and research memory consume governance graveyard primitives by ref, surface prior rejection reasons, avoid duplicate ideas, and preserve rejected/blocked/inconclusive outcomes. |
| Prohibited MVP states unreachable | Held. The dry-run forward path tops out at `REFERENCE_HANDOFF_RECORDED`; terminal states are `REJECTED`, `INCONCLUSIVE`, and `BLOCKED`. Prohibited alpha, promotion, strategy, portfolio, paper/live, profitability, tradability, production, and autonomous-runner states remain non-outcomes. |
| Runtime bridge | Held. `runtime_bridge` adapts `RuntimeToolResult` / `RuntimeRunSummary` into value-free `AgentToolResult` records and resolves DatasetVersion inputs through `resolve_dataset_version`, admitting only `VERSIONED` and `READY_FOR_RESEARCH`. |
| Dry-run interpretation | Held with warning. The P23 integration dry run recorded `PASS_WITH_WARNINGS` because local seed registries were unavailable and synthetic fallback was used. The dry run proves contract routing only, not alpha. |
| DAG metadata | Held. Parallel-safe role and asset phases are disjoint, closeout phases run alone, the serial merge queue is recorded, and phase branches do not write `ACTIVE_CAMPAIGN.md`. |
| Artifact policy | Held pending coordinator staged-set audit. `git ls-files runs` is expected to remain empty; data, metadata, DB, cache, log, and heavy artifacts are not part of the closeout artifacts. The executor did not stage files. |

## Per-Gate Detail

### `bootstrap_and_entry`

`AGENT-P00` through `AGENT-P02` establish the campaign files, Agent Factory
package root, docs root, templates root, and entry contract. The entry contract
returns structured `PREFLIGHT_PASS`, `PREFLIGHT_WARN`, or
`PREFLIGHT_BLOCKED`; it performs marker/config checks only and does not open
registries, read market data, call a provider, or instantiate an agent.

### `core_contracts`

`AGENT-P03` through `AGENT-P06` add the role model and registry, permission
model and matrix, tool contracts and `AgentToolResult`, and finite research
queue contracts. Unknown roles/tools fail closed. Work items are bounded by
declared DatasetVersion refs, FeaturePack/LabelPack refs, finite budgets,
review requirements, blockers, and next gates.

### `agent_roles`

`AGENT-P07` through `AGENT-P15` add all ten MVP role contracts in disjoint
files. Each role declares inputs, tools, outputs, allowed decisions, forbidden
actions, handoff format, reviewer-independence constraints, and failure modes.
No role can grant itself raw data access, external provider access, promotion,
paper/live/broker/order scope, or production authority.

### `enforcement_and_records`

`AGENT-P16` through `AGENT-P18` add fail-closed separation-of-duties checks,
passive records, handoffs, audit logs, version refs, and rejected-idea/research
memory. Records and memory store ids, refs, statuses, summaries, warnings, and
reasons only; they do not write registries directly or hide failed ideas.

### `assets_and_bridge`

`AGENT-P19` through `AGENT-P21` add prompt/operator/readiness docs and the
runtime bridge. The bridge is the single Agent Factory adapter for existing
runtime outputs. It imports runtime contracts, does not reimplement
diagnostics, and blocks unresolved or inadmissible DatasetVersions.

### `dry_run_and_closeout`

`AGENT-P22` through `AGENT-P25` add the bounded dry-run harness, integration
dry-run results, DAG plan, acceptance audit, and closeout. The dry run routes
one synthetic task through the MVP role order and records rejection memory. It
does not promote, validate, or approve a candidate. `AGENT-P23` is the source
of the gate warning because the runner had no local seed registries.

## No-Claims Interpretation

This audit preserves the campaign interpretation policy:

- A dry-run success is not alpha.
- An agent-drafted `AlphaSpec` is not implementation approval.
- A runtime diagnostic PASS is not factor promotion.
- An `EvidenceDraft` is not a candidate.
- A `ReferenceCandidateHandoff` is not Reference validation.
- Validated research is not paper/live approval.

`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` remains a separate, separately authorized
next campaign. The Agent Factory closeout provides readiness of the controlled
contract layer only.
