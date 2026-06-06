# ALPHA_AGENT_FACTORY_MVP Risk Register

## Purpose

This register records the campaign-specific risks for the **Agent Factory MVP**: the
**controlled AI Alpha Research Team contract layer** that sits over the completed
Governance + Feature/Label + Research Runtime stack (`ALPHA_RESEARCH_GOVERNANCE_MVP`,
`ALPHA_DATA_FOUNDATION_V1`, `ALPHA_FEATURE_LABEL_FOUNDATION_V1` 32/32 COMPLETE_WITH_WARNINGS,
`ALPHA_RESEARCH_RUNTIME_MVP` 27/27 COMPLETE_WITH_WARNINGS, and
`POST_RUNTIME_FEATURE_LABEL_STORAGE_AND_SEED_PACKS_V1`). This campaign defines, as **contracts
only**, the agent role model, the fail-closed permission matrix, the agent-facing tool
contracts, the bounded research queue, separation-of-duties enforcement, agent/decision/handoff
records, rejected-idea memory, prompt assets, a runtime tool integration bridge, and a bounded
non-alpha dry-run harness — by **driving existing primitives**
(`alpha_system.runtime.tool_results.RuntimeToolResult` / `RuntimeRunSummary`,
`alpha_system.cli.runtime`, `alpha_system.governance.*`,
`alpha_system.data.foundation.version_registry.resolve_dataset_version`,
`alpha_system.cli.seed_pack`), never re-implementing or editing them. The new package is
`src/alpha_system/agent_factory/` (`roles/`, `permissions/`, `tools/`, `queue/`, `separation/`,
`records/`, `memory/`, `runtime_bridge.py`, `dry_run/`, `entry_contract.py`).

This campaign is a **contract layer only**. It instantiates **no** autonomous agent, starts
**no** continuous research runner, conducts **no** alpha search, promotes **no** factor,
validates **no** strategy, calls **no** Databento/IBKR provider, and introduces **no**
order/account/paper/live/broker scope. There are **26 phases** (`AGENT-P00` … `AGENT-P25`):
`AGENT-P00` is GREEN, every other phase is YELLOW, and there are **no RED-lane phases**. Most
risks here are therefore about **contract discipline, separation of duties, permission/tool
fail-closedness, runtime/governance/registry reuse, dry-run scope honesty, memory visibility,
parallel-DAG correctness, and artifact discipline** — the Agent Factory drifting into alpha
search, instantiating an autonomous agent, bypassing the runtime or the `DatasetVersion`
boundary, overclaiming a dry-run, hiding a rejected idea, or committing forbidden values —
rather than market risk.

The framing is stated explicitly and must hold everywhere:

```text
The Agent Factory defines constrained workers, not autonomous traders.
An agent dry-run success is not alpha. An agent-drafted AlphaSpec is not implementation approval.
A runtime diagnostic PASS is not factor promotion. An EvidenceDraft is not a candidate.
A ReferenceCandidateHandoff is not Reference validation. Validated research is not paper/live approval.
```

Every "Blocking condition" below is a hard STOP/merge-block that Ralph must enforce through the
serial merge queue, and most map directly to the `merge_policy.global_blockers` and
`stop_conditions` lists in `campaign.yaml`.

## Severity Scale

* **S1 Critical** — instantiates an autonomous agent or continuous research runner, exposes
  forbidden trading/broker/order/account/alpha-search/factor-promotion scope, automates a
  risk/capital/live decision reserved for the human, reads raw provider data, calls an external
  provider, makes an unsupported alpha/tradability/profitability claim, or commits forbidden
  raw/canonical/value/heavy/DB artifacts; the campaign cannot be accepted.
* **S2 High** — materially weakens a separation-of-duties or permission/tool fail-closed
  boundary, the runtime/governance/registry-reuse boundary, the structured value-free tool
  contract, the rejected-idea/memory visibility, the preflight blocker gates, or a
  parallel-DAG/merge-queue invariant.
* **S3 Medium** — local correctness, clarity, or build-balance issue with contained impact.
* **S4 Low** — cosmetic or documentation-only issue.

## Likelihood Scale

* **L1 Rare** — unlikely given current controls.
* **L2 Possible** — plausible without explicit attention.
* **L3 Likely** — expected if not actively prevented.

## Risk Status Values

* **Open** — active and monitored.
* **Mitigated** — controls in place; residual risk accepted.
* **Closed** — no longer applicable.

## Risk Table Summary

| ID | Risk | Severity | Likelihood | Status | Related phases |
| -- | ---- | -------- | ---------- | ------ | -------------- |
| R-001 | Agent Factory becomes alpha search | S1 | L2 | Open | AGENT-P06, AGENT-P07, AGENT-P13, AGENT-P22, AGENT-P25 |
| R-002 | Agent bypasses Runtime | S1 | L2 | Open | AGENT-P05, AGENT-P13, AGENT-P21 |
| R-003 | Agent reads raw provider data | S1 | L2 | Open | AGENT-P01, AGENT-P10, AGENT-P21 |
| R-004 | Tool permissions too broad | S2 | L2 | Open | AGENT-P04, AGENT-P16 |
| R-005 | Agent self-review | S2 | L2 | Open | AGENT-P04, AGENT-P09, AGENT-P16 |
| R-006 | Agent self-promotion | S2 | L2 | Open | AGENT-P04, AGENT-P16 |
| R-007 | Role prompts ambiguous | S3 | L2 | Open | AGENT-P07, AGENT-P19 |
| R-008 | Tool outputs unstructured | S2 | L2 | Open | AGENT-P05, AGENT-P21 |
| R-009 | Rejected ideas not recorded | S2 | L2 | Open | AGENT-P18 |
| R-010 | Duplicate ideas re-generated | S2 | L2 | Open | AGENT-P18 |
| R-011 | Agent dry-run misread as alpha evidence | S1 | L2 | Open | AGENT-P22, AGENT-P23 |
| R-012 | Large-scale study runs before Parquet sink | S1 | L2 | Open | AGENT-P01 |
| R-013 | Session-context features used before guard fix | S2 | L2 | Open | AGENT-P01, AGENT-P12 |
| R-014 | Feature/Label packs not resolved (accepted-DatasetVersion bypassed) | S1 | L2 | Open | AGENT-P10, AGENT-P11 |
| R-015 | RuntimeToolResult not parsed safely | S2 | L2 | Open | AGENT-P05, AGENT-P13, AGENT-P21 |
| R-016 | Human approval bypassed for risk/capital | S1 | L2 | Open | AGENT-P04, AGENT-P16 |
| R-017 | Broker/live/paper scope creep | S1 | L2 | Open | AGENT-P04, AGENT-P25 |
| R-018 | Memory records become a dumping ground | S2 | L2 | Open | AGENT-P18 |
| R-019 | Agent docs scatter across repo | S3 | L2 | Open | AGENT-P19, AGENT-P20 |
| R-020 | DAG metadata wrong / parallel conflict | S2 | L2 | Open | AGENT-P24 |
| R-021 | Agent Factory blocks Core Alpha Pilot with overbuilding | S2 | L2 | Open | AGENT-P25 |
| R-022 | Agent Factory underbuilds and agents still write ad hoc scripts | S2 | L2 | Open | AGENT-P25 |
| R-023 | Statistical Reviewer lacks independence | S2 | L2 | Open | AGENT-P04, AGENT-P16 |
| R-024 | Librarian updates registry without verdict | S2 | L2 | Open | AGENT-P04, AGENT-P16 |
| R-025 | Tool contract drift from runtime implementation | S2 | L2 | Open | AGENT-P05, AGENT-P13, AGENT-P21 |

---

# Detailed Risk Entries

## R-001 — Agent Factory becomes alpha search

### Description
The contract layer drifts from "define constrained roles that scope one bounded `ResearchTask`
at a time" into broad, undirected alpha discovery — a role or the dry-run harness enumerates
hypotheses over all data, sweeps factor families, mines variants without a `VariantBudget`,
ranks candidates, or stands up a continuous unattended research runner — turning the Agent
Factory into an unbounded search engine and a de facto autonomous trader.

### Impact
The campaign exceeds its charter (it is **not** Core Alpha Pilot, **not** the Agent Research
Runner, **not** a Factor Library), re-creating an unbounded search and the overfit machine the
MVP is explicitly designed to prevent, and inviting prohibited lifecycle states
(`FACTOR_PROMOTED`, `AUTONOMOUS_RESEARCH_RUNNING`). S1.

### Likelihood
L2 — once role contracts and the dry-run harness exist, "just generate a few more hypotheses"
or "loop the queue" is a natural slide unless the single-task-bounded `ResearchQueue`/`VariantBudget`
and the `agent_factory_not_alpha_search` / `contracts_only_no_agent_instantiation` controls are
hard limits.

### Detection
* `agent_policy`: `autonomous_alpha_search_allowed: false`, `continuous_research_runner_allowed:
  false`; `risk_controls.agent_factory_not_alpha_search` (`no_broad_alpha_discovery`,
  `no_continuous_autonomous_runner`, `no_factor_promotion`) via scope audit + import audit +
  Claude review.
* AGENT-P06 `ResearchQueue`/`ResearchTask` is single-task-bounded with a `VariantBudget`/
  `ComputeBudget`; AGENT-P22 dry-run harness routes one bounded task end-to-end with no loop.
* `merge_policy.global_blockers`: `factor promotion or alpha search scope introduced`,
  `autonomous agent instantiated or continuous research loop introduced`; `stop_conditions`:
  `factor promotion or alpha search scope introduced`, `autonomous agent instantiated`.
* Claude Opus review of AGENT-P06/P07/P13/P22 scope and the AGENT-P25 semantic done-check.

### Mitigation
The queue scopes exactly one bounded task with bounded variants; no role and no harness loops or
searches; `autonomous_alpha_search_allowed` / `continuous_research_runner_allowed` are false;
prohibited MVP lifecycle states are unreachable; the most advanced forward state any dry-run
survivor reaches is `REFERENCE_HANDOFF_RECORDED`.

### Owner
Codex (single-task-bounded queue + non-looping harness) / Claude Opus (scope review) / Ralph
(scope/stop enforcement + merge gating).

### Related Phases
AGENT-P06, AGENT-P07, AGENT-P13, AGENT-P22, AGENT-P25.

### Blocking Condition
Broad alpha search, factor promotion, candidate-promotion scope, or a continuous autonomous
research runner appears, or a role/harness runs outside its single bounded `ResearchTask` budget.

---

## R-002 — Agent bypasses Runtime

### Description
`agent_factory` code performs diagnostics, cost stress, or no-lookahead checks directly —
re-computing them in a role, a tool, or the bridge — instead of invoking the Research Runtime
through its agent-facing structured outputs
(`alpha_system.runtime.tool_results.RuntimeToolResult` / `RuntimeRunSummary` and the
`alpha_system.cli.runtime` surface), bypassing the runtime input resolver and tool surface.

### Impact
The single sanctioned diagnostics boundary is broken: agents compute evidence outside the
fail-closed, no-lookahead-audited runtime, so every result inherits ungoverned logic and the
runtime's guarantees no longer hold for what the Agent Factory produces. S1.

### Likelihood
L2 — re-implementing a "quick" diagnostic inside a role or the bridge is a tempting shortcut
unless the only sanctioned path is the runtime tool surface and runtime-bypass is fail-closed.

### Detection
* `runtime_integration_policy`: `runtime_tool_use_required: true`, `runtime_consumed_not_edited:
  true`; `tool_policy.drives_existing_runtime_and_governance_tools_not_duplicates: true`;
  `risk_controls.runtime_consumed_not_bypassed` (`tools_call_runtime_tool_results_and_resolve_dataset_version`,
  `no_runtime_input_resolver_bypass`) via source-path audit + import audit + Claude review.
* AGENT-P05 Diagnostics Runner tool contract requires the runtime tool surface; AGENT-P13 role
  may not bypass the runtime; AGENT-P21 bridge is the only module importing the runtime tool
  surface and never re-implements diagnostics.
* `merge_policy.global_blockers`: `runtime bypassed instead of called via tool contract`;
  `stop_conditions`: `runtime bypassed`.
* Claude Opus review of AGENT-P13/P21 runtime integration semantics.

### Mitigation
All diagnostics flow through `RuntimeToolResult` / `RuntimeRunSummary` (and `alpha runtime`); the
Diagnostics Runner requests runtime diagnostics within budget and never alters specs or bypasses
the resolver; the bridge imports the runtime and never re-implements it; runtime bypass is
fail-closed and merge-blocking.

### Owner
Codex (runtime-tool-bound roles + bridge) / Claude Opus (runtime-boundary review).

### Related Phases
AGENT-P05, AGENT-P13, AGENT-P21.

### Blocking Condition
Any `agent_factory` code computes diagnostics/cost/no-lookahead directly instead of invoking the
runtime tool surface, or bypasses the runtime input resolver.

---

## R-003 — Agent reads raw provider data

### Description
`agent_factory` code reads raw provider files directly (`.dbn`, `.zst`, parquet, arrow, feather,
or any Databento/IBKR response) instead of consuming canonical records
(`CanonicalBarRecord` / `CanonicalBBORecord` / `DenseGridBarRecord`) from an accepted
`DatasetVersion`, or it calls an external Databento/IBKR API.

### Impact
The Agent Factory consumes provider artifacts and possible lookahead that canonical gating and
the runtime exist to remove, and (if an API is called) introduces external, network, and cost
scope the local-only campaign forbids — the most direct raw-bypass failure mode for an agent
layer. S1.

### Likelihood
L2 — raw provider files are already local and convenient, so a shortcut into them (or a
"convenience" provider call) is plausible without an explicit forbidden-path guard and import
audit.

### Detection
* `data_access_policy`: `raw_provider_access_forbidden: true`, `external_provider_calls_forbidden:
  true`, `canonical_records_only` limited to the three canonical record types;
  `risk_controls.no_raw_provider_access` + `risk_controls.no_external_provider_calls` via
  source-path audit, import audit, and CI-configuration audit.
* Every phase's `forbidden_paths` blocks `data/raw/**`, `data/canonical/**`, `**/*.dbn`,
  `**/*.zst`, `**/*.parquet`, `**/*.arrow`, `**/*.feather`; the AGENT-P10 Data Contract Auditor
  uses registry tools only; the AGENT-P21 bridge resolves inputs via `resolve_dataset_version`
  and never opens raw files.
* `merge_policy.global_blockers`: `raw provider data read by agent_factory code`, `external
  provider call attempted`; `stop_conditions`: `raw provider data read by agent_factory code`,
  `external Databento or IBKR API call attempted`.
* Claude Opus review of AGENT-P01/P10/P21 input access.

### Mitigation
`agent_factory` consumes only canonical records resolved from accepted `DatasetVersions`; raw
provider files are forbidden paths; provider readers are never imported; no Databento/IBKR API is
called in this campaign; raw access or any external call is fail-closed and merge-blocking.

### Owner
Codex (registry/runtime-only access + import guards) / Claude Opus (boundary review) / Ralph
(external-call prevention + merge gating).

### Related Phases
AGENT-P01, AGENT-P10, AGENT-P21.

### Blocking Condition
Any `agent_factory` code reads a raw provider file (`.dbn`/`.zst`/parquet/arrow/feather) directly
or attempts an external Databento/IBKR API call.

---

## R-004 — Tool permissions too broad

### Description
The permission matrix grants a role wider access than its purpose requires — a default-allow
posture, a missing `ToolPermission`/`DataPermission`/`WritePermission`/`ReviewPermission`/
`PromotionPermission` entry, a role with no matrix entry at all, or `WritePermission`/
`PromotionPermission` granted where it should be denied — so an agent can reach tools, data, or
writes outside its mandate.

### Impact
Over-broad permissions defeat the fail-closed, default-deny boundary that keeps each role a
constrained worker, opening the door to self-review, self-promotion, direct registry writes, and
the overfit-machine failure modes the matrix exists to prevent. S2.

### Likelihood
L2 — a permissive default or a forgotten matrix entry is the path of least resistance when adding
a role unless every role is required to have explicit fail-closed entries.

### Detection
* `permissions_required` / `role_permissions_required`; `risk_controls.permission_matrix_required`
  (`every_role_has_tool_data_write_review_promotion_permissions`, `fail_closed_default_deny`) via
  permission-matrix tests + Claude review.
* AGENT-P04 `permissions/model.py` + `permissions/matrix.py` define a default-deny matrix with an
  explicit entry per roster role (`ToolPermission`/`DataPermission`/`WritePermission`/
  `ReviewPermission`/`PromotionPermission`/`HumanApprovalRequired`/`RedLaneRequired`); AGENT-P16
  wiring asserts every registered role has a matrix entry.
* `merge_policy.global_blockers`: `agent role without a permission-matrix entry`;
  `stop_conditions`: `role without permission matrix entry`.
* Claude Opus review of AGENT-P04/P16 matrix completeness and default-deny posture.

### Mitigation
The matrix is default-deny and fail-closed; every roster role has explicit permission entries;
no-raw-data, no-direct-registry-write, and human-approval/red-lane flags are asserted by tests; a
role without a matrix entry is fail-closed and merge-blocking.

### Owner
Codex (fail-closed matrix + per-role entries) / Claude Opus (permission-completeness review).

### Related Phases
AGENT-P04, AGENT-P16.

### Blocking Condition
The matrix is default-allow, omits a required permission entry, or any role exists without a
complete permission-matrix entry.

---

## R-005 — Agent self-review

### Description
A role both produces and approves the same artifact — the Hypothesis Scout approves its own
`AlphaSpec`, an implementer (Feature/Label Engineer) reviews its own work, or the Statistical
Reviewer reviews work it implemented — collapsing the generator/approver and implementer/reviewer
separation the campaign installs.

### Impact
Self-review removes the independent check that keeps agents from manufacturing convincing-but-false
evidence, directly enabling the overfit machine the separation-of-duties enforcement exists to
prevent. S2.

### Likelihood
L2 — wiring a role to both draft and approve is the simplest implementation and easy to ship
unless `generator_cannot_approve` / `implementer_cannot_review` are enforced in code and tested.

### Detection
* `agent_policy.self_review_forbidden: true`; `review_independence_policy.implementer_cannot_review:
  true`, `generator_cannot_approve: true`; `risk_controls.separation_of_duties_required`
  (`generator_cannot_approve`, `implementer_cannot_review`, `reviewer_is_not_implementer`) via
  separation-enforcement tests + Claude review.
* AGENT-P04 matrix denies self-approval/self-review per role; AGENT-P16 `separation/enforcement.py`
  proves each rule fails closed.
* `merge_policy.global_blockers`: `generator approves its own AlphaSpec`, `implementer reviews its
  own work`, `reviewer is the implementer`; `stop_conditions`: `self-review or self-promotion`.
* Claude Opus review of AGENT-P04/P16 separation rules.

### Mitigation
The matrix and separation enforcement forbid a role approving or reviewing its own output; the
AlphaSpec Critic and Statistical Reviewer are independent of the drafter/implementer; tests prove
each rule fails closed; any self-review is merge-blocking and routes to rework.

### Owner
Codex (separation enforcement + tests) / Claude Opus (independence review).

### Related Phases
AGENT-P04, AGENT-P09, AGENT-P16.

### Blocking Condition
A role approves or reviews an artifact it produced (generator approves its own AlphaSpec, or the
reviewer is the implementer).

---

## R-006 — Agent self-promotion

### Description
A role promotes its own result — the Diagnostics Runner promotes a runtime result, the Hypothesis
Scout promotes its own draft, or any role reaches a promotion state — instead of promotion being
reserved for a reviewer verdict plus the governance `PromotionGate` under a later,
separately-authorized campaign.

### Impact
Self-promotion lets an agent declare its own output a candidate, fabricating downstream confidence
and inviting the prohibited states `FACTOR_PROMOTED` / `CANDIDATE_PROMOTED` that the MVP forbids
entirely. S2.

### Likelihood
L2 — a runner or drafter "marking its result good" is a natural overstep unless
`diagnostics_runner_cannot_promote` and `self_promotion_forbidden` are enforced and promotion is
unreachable in this campaign.

### Detection
* `agent_policy.self_promotion_forbidden: true`;
  `review_independence_policy.diagnostics_runner_cannot_promote: true`;
  `risk_controls.separation_of_duties_required` (`diagnostics_runner_cannot_promote`) via
  separation-enforcement tests + Claude review.
* AGENT-P04 matrix denies `PromotionPermission` to non-promotion roles; AGENT-P16 enforcement
  proves runner≠promoter; no agent_lifecycle transition reaches a promotion/`FACTOR_PROMOTED`
  state.
* `merge_policy.global_blockers`: `diagnostics runner promotes`, `factor promotion or alpha search
  scope introduced`; `stop_conditions`: `self-review or self-promotion`, `factor promotion or
  alpha search scope introduced`.
* Claude Opus review of AGENT-P04/P16 promotion denial and the AGENT-P25 done-check.

### Mitigation
No role holds `PromotionPermission` in this campaign; the Diagnostics Runner may request
diagnostics but never promote; promotion belongs to a reviewer verdict + `PromotionGate` in a
later campaign; prohibited promotion states are unreachable; self-promotion is merge-blocking.

### Owner
Codex (promotion-denied matrix + enforcement) / Claude Opus (promotion-scope review).

### Related Phases
AGENT-P04, AGENT-P16.

### Blocking Condition
Any role promotes its own result, holds `PromotionPermission` in this campaign, or any promotion/
`FACTOR_PROMOTED`/`CANDIDATE_PROMOTED` state becomes reachable.

---

## R-007 — Role prompts ambiguous

### Description
A role contract or its prompt template states purpose, readable inputs, callable tools, producible
outputs, allowed/forbidden decisions, handoff format, or reviewer-independence rules ambiguously —
so a future agent operating the role could misread its mandate, exceed its permissions, or skip a
required handoff.

### Impact
Ambiguous role definitions weaken the constrained-worker model by leaving the boundary to
interpretation, increasing the chance a future agent oversteps its permissions or routes work
incorrectly. S3.

### Likelihood
L2 — prose role definitions and prompts drift toward vagueness without an explicit, structured
contract schema and a single indexed prompt source.

### Detection
* AGENT-P03 `roles/contracts.py` defines a structured `AgentRole` schema (purpose, inputs, tools,
  outputs, allowed/forbidden decisions, handoff format, reviewer-independence, failure modes);
  AGENT-P07..P15 role docs/tests assert each field is populated.
* AGENT-P19 `templates/agent_factory/prompts/**` provides per-role prompt templates with a
  source-of-truth `README.md` index (`risk_controls.agent_docs_indexed`); doc grep checks the
  index.
* Claude Opus review of AGENT-P07/P19 role-contract and prompt clarity (the `review_must_check`
  item "role prompts ambiguous").

### Mitigation
Every role uses the structured `AgentRole` contract schema with explicit fields; each prompt
template follows the schema and is registered in the indexed source-of-truth; review confirms
unambiguous purpose, permissions, and handoff format.

### Owner
Codex (structured role contracts + indexed prompts) / Claude Opus (clarity review).

### Related Phases
AGENT-P07, AGENT-P19.

### Blocking Condition
None on its own (S3, non-blocking); flagged in the AGENT-P07/P19 review and escalates to R-004 if
ambiguity widens an effective permission or to R-019 if prompts become unindexed/scattered.

---

## R-008 — Tool outputs unstructured

### Description
An agent-facing tool contract returns an unstructured or free-form output instead of the required
structured, value-free `AgentToolResult` (with `status`, `role`, `request_id`, `alpha_spec_id`,
`study_spec_id`, `dataset_version_id`, `feature_pack_refs`, `label_pack_refs`, `runtime_run_id`,
`diagnostics_summary`, `cost_summary`, `rejection_reasons`, `blocking_findings`,
`next_required_gate`, `artifacts`, `limitations`), or embeds raw/heavy data in a result.

### Impact
Unstructured or raw-bearing tool outputs break the agent-facing contract — a downstream agent
cannot reliably parse status, version ids, or the next gate — and risk leaking or committing raw/
heavy data, defeating both the tool contract and the artifact policy. S2.

### Likelihood
L2 — returning a free-form blob or "everything" is the simplest tool implementation unless the
`AgentToolResult` schema and the no-raw-data contract are required and tested.

### Detection
* `tool_policy`: `structured_outputs_required: true`, `raw_tool_output_forbidden: true`,
  `raw_data_in_tool_response_forbidden: true`; `risk_controls.structured_tool_outputs_required`
  (`all_tool_results_structured`, `no_raw_or_heavy_data_in_tool_results`) via tool-result tests +
  artifact policy checks + Claude review.
* AGENT-P05 `tools/results.py` `AgentToolResult` carries the structured fields and rejects raw/
  heavy payloads; AGENT-P21 bridge maps runtime outputs into the same value-free shape.
* `merge_policy.global_blockers`: `tool contract with unstructured output or embedded raw/heavy
  data`; `stop_conditions`: `tool result exposes raw or heavy data`.
* Claude Opus review of AGENT-P05/P21 tool-result contracts.

### Mitigation
All tools return the structured `AgentToolResult` with version ids, summaries, references, and the
next required gate, never raw or heavy data; the schema and no-raw-data rule are enforced by tests;
an unstructured or raw-bearing result is fail-closed and merge-blocking.

### Owner
Codex (structured value-free tool results) / Claude Opus (tool-contract review).

### Related Phases
AGENT-P05, AGENT-P21.

### Blocking Condition
An agent-facing tool returns an unstructured output or embeds raw/heavy data instead of a
structured, value-free `AgentToolResult`.

---

## R-009 — Rejected ideas not recorded

### Description
A rejected or failed idea is silently dropped or omitted instead of being recorded with a
`RejectedIdeaMemoryRecord` / `RejectionReasonRecord` (consuming `governance.rejected_idea` /
`ResearchGraveyardLedger`), so negative outcomes disappear from the agent memory the campaign
installs to keep failures visible.

### Impact
Hidden rejections bias the visible record toward survivors, manufacturing apparent success,
defeating the anti-overfit honesty of the Agent Factory, and feeding R-010 (the same idea is
re-generated because its rejection was never recorded). S2.

### Likelihood
L2 — dropping a disappointing idea is a natural temptation unless rejection recording is required
and the memory consumes the governance graveyard.

### Detection
* `memory_policy`: `rejected_ideas_visible: true`, `failed_runs_visible: true`,
  `consumes_governance_rejected_idea_and_graveyard: true`;
  `risk_controls.failed_and_rejected_ideas_visible` (`rejected_idea_memory_record_required`,
  `failed_runs_visible`) via memory tests + Claude review.
* AGENT-P18 `memory/models.py` `RejectedIdeaMemoryRecord` / `ResearchMemoryRecord` consume the
  governance graveyard; the AGENT-P22 dry-run records rejections via the Librarian; tests assert
  failures are recorded, not dropped.
* `merge_policy.global_blockers`: `failed or rejected idea hidden`; `stop_conditions`: `failed or
  rejected idea hidden`.
* Claude Opus review of AGENT-P18 rejection-memory semantics.

### Mitigation
Every rejected/failed idea produces a `RejectedIdeaMemoryRecord`/`RejectionReasonRecord` and is
surfaced; the memory consumes (does not duplicate) the governance graveyard; hiding a rejected/
failed idea is fail-closed and merge-blocking.

### Owner
Codex (rejection records consuming governance) / Claude Opus (visibility review).

### Related Phases
AGENT-P18.

### Blocking Condition
A rejected or failed idea is dropped or omitted instead of recorded with a
`RejectedIdeaMemoryRecord`/`RejectionReasonRecord` and surfaced.

---

## R-010 — Duplicate ideas re-generated

### Description
The Hypothesis Scout (or the dry-run harness) re-generates an idea that was already rejected,
because duplicate-idea avoidance and prior-rejection surfacing over the rejected-idea memory and
the governance `ResearchGraveyardLedger` are missing or weak.

### Impact
Duplicate churn wastes the bounded research budget and re-litigates settled rejections, edging the
team toward variant mining and the overfit machine the memory layer exists to prevent. S2.

### Likelihood
L2 — without explicit dedupe and prior-rejection surfacing, re-proposing a "fresh" idea that is
actually a known rejection is an easy, invisible repeat.

### Detection
* `memory_policy`: `duplicate_idea_avoidance_required: true`, `prior_rejection_reasons_surfaced:
  true`, `consumes_governance_rejected_idea_and_graveyard: true`; the Hypothesis Scout role
  (AGENT-P08) consults rejected-idea + library summaries before drafting.
* AGENT-P18 memory implements duplicate detection on synthetic fixtures and surfaces prior
  rejection reasons; tests assert a known rejection is detected and surfaced; the campaign also
  consumes `governance.duplicate_exposure`.
* `risk_controls.failed_and_rejected_ideas_visible` and the AGENT-P25 semantic done-check;
  duplicate churn is an anti-overfit failure mode the review checks.
* Claude Opus review of AGENT-P18 duplicate avoidance.

### Mitigation
The memory surfaces prior rejection reasons and detects duplicate ideas against the rejected-idea
memory and the governance graveyard before a new draft is accepted; duplicate avoidance is tested;
re-generating a known rejection is flagged.

### Owner
Codex (duplicate detection + prior-rejection surfacing) / Claude Opus (dedupe review).

### Related Phases
AGENT-P18.

### Blocking Condition
None on its own (S2, non-blocking); flagged in the AGENT-P18/P25 review when duplicate avoidance
or prior-rejection surfacing is absent, and escalates to R-001 if it normalizes variant mining.

---

## R-011 — Agent dry-run misread as alpha evidence

### Description
A seed-pack or synthetic dry-run outcome — or an `EvidenceDraft` or `ReferenceCandidateHandoff`
produced during the dry-run — is presented or recorded as alpha evidence, a validated candidate,
or tradability, conflating "the machinery works" with "the result is alpha."

### Impact
A dry-run that only proves role routing / tool contracts / permissions / handoffs / rejection
memory is misread as research evidence, overstating the Agent Factory's authority and corrupting
the chain into the future Core Alpha Pilot (a dry-run is **not** alpha; an `EvidenceDraft` is
**not** a candidate; a `ReferenceCandidateHandoff` is **not** Reference validation). S1.

### Likelihood
L2 — a clean dry-run PASS is easy to describe as if it found something unless the
not-alpha-evidence framing is enforced in contracts, tests, and docs.

### Detection
* `dry_run_policy`: `no_alpha_claims: true`, `does_not_prove_alpha: true`,
  `proves_role_routing_tools_permissions_handoffs_rejection_memory: true`;
  `runtime_integration_policy.seed_pack_dry_run_not_alpha_evidence: true`;
  `risk_controls.dry_run_not_evidence` (`seed_or_synthetic_dry_run_not_alpha_evidence`,
  `evidence_draft_not_candidate`, `reference_handoff_not_reference_validation`) via dry-run tests +
  doc grep + Claude review.
* AGENT-P22 `DRY_RUN.md` and AGENT-P23 `DRY_RUN_RESULTS.md` state explicitly the run is not alpha
  evidence; AGENT-P23 records a truthful `PASS_WITH_WARNINGS`.
* `merge_policy.global_blockers`: `seed-pack or synthetic dry-run treated as alpha evidence`,
  `EvidenceDraft treated as candidate`, `ReferenceCandidateHandoff treated as Reference
  validation`; matching `stop_conditions`.
* Claude Opus review of AGENT-P22/P23 dry-run wording and the AGENT-P25 done-check.

### Mitigation
Dry-run docs and contracts explicitly label the run as machinery-only and not alpha evidence; the
`EvidenceDraft` is a draft and the `ReferenceCandidateHandoff` is a handoff, never a candidate or
Reference validation; a dry-run-as-evidence claim is fail-closed and routes to rework.

### Owner
Codex (not-alpha-evidence labeling in dry-run + docs) / Claude Opus (scope-honesty review).

### Related Phases
AGENT-P22, AGENT-P23.

### Blocking Condition
A seed-pack/synthetic dry-run, an `EvidenceDraft`, or a `ReferenceCandidateHandoff` is presented or
recorded as alpha evidence, a candidate, tradability, or completed Reference validation.

---

## R-012 — Large-scale study runs before Parquet sink

### Description
A broad, multi-year, value-consuming study (a large feature/label scan) is attempted before
`FEATURE_LABEL_PARQUET_SINK_V1` lands or a human explicitly approves, despite ADR-0006 stating
the research-scale Parquet tier should land before any large-scale value-consuming Agent Factory
study (today values are the JSONL audit/small tier).

### Impact
A large-scale scan before the Parquet sink runs against an inadequate value tier — producing
heavy, possibly-committed outputs and an unreproducible study — and crosses a known future-blocker
the campaign encodes as a hard preflight gate. S1.

### Likelihood
L2 — once seed packs work end-to-end, "scale it up to all of 2024" is a tempting next step unless
the preflight gate and the `parquet_sink_blocker` scope blocker hold.

### Detection
* `future_blockers.FEATURE_LABEL_PARQUET_SINK_V1` (`enforced_as: preflight gate + hard scope
  blocker`; see `decisions/0006-feature-label-value-storage.md` / `docs/STRUCTURAL_BACKLOG.md`);
  `data_access_policy.large_scale_value_consuming_studies_blocked_until_parquet_sink: true`.
* AGENT-P01 `entry_contract` encodes the `FEATURE_LABEL_PARQUET_SINK_V1` status preflight gate and
  fails closed; `risk_controls.parquet_sink_blocker` via preflight gate tests + scope audit +
  Claude review.
* `merge_policy.global_blockers`: `large-scale value-consuming study before
  FEATURE_LABEL_PARQUET_SINK_V1`; `stop_conditions`: `large-scale value-consuming study before
  parquet sink`.
* Claude Opus review of AGENT-P01 preflight gate and any value-consuming scope.

### Mitigation
The entry contract gates on `FEATURE_LABEL_PARQUET_SINK_V1` status; Agent Factory MVP uses seed
packs and synthetic fixtures only for dry-run and designs tool contracts without broad scans; a
large-scale value-consuming study before the sink (absent explicit human approval) is fail-closed
and escalates.

### Owner
Codex (preflight gate + bounded scope) / Claude Opus (scope review) / Ralph (escalation).

### Related Phases
AGENT-P01.

### Blocking Condition
A broad/multi-year value-consuming study is attempted before `FEATURE_LABEL_PARQUET_SINK_V1` is
complete or explicitly human-approved.

---

## R-013 — Session-context features used before guard fix

### Description
Session-context features (`rth_flag` / `eth_flag` / `session_minute`, derived from the canonical
point-in-time field `session_label`) are used before `SESSION_LABEL_GUARD_FIX_V1`, even though the
runtime leakage guard `_reject_label_as_live_feature` in `runtime/input_resolver.py`
false-positives on `session_label` (a narrow guard over-match, not real leakage).

### Impact
Relying on session-context features before the guard fix either trips the runtime guard (blocking
the run) or, if worked around, risks bypassing a leakage guard the campaign must respect — a
deferred future-blocker the entry contract encodes as a hard preflight gate. S2.

### Likelihood
L2 — session/RTH/ETH features are attractive and easy to request unless the preflight gate and the
`session_label_guard_blocker` scope blocker hold them back.

### Detection
* `future_blockers.SESSION_LABEL_GUARD_FIX_V1` (`enforced_as: preflight gate + hard scope blocker
  for session-context features`);
  `data_access_policy` / scope blocker `session_context_features_blocked_until_SESSION_LABEL_GUARD_FIX_V1`.
* AGENT-P01 `entry_contract` encodes the `SESSION_LABEL_GUARD_FIX_V1` status preflight gate and
  fails closed; `risk_controls.session_label_guard_blocker` via preflight gate tests + scope audit
  + Claude review.
* `merge_policy.global_blockers`: `session-context feature used before session_label guard fix`;
  `stop_conditions`: `session-context feature used before guard fix`.
* Claude Opus review of AGENT-P01 preflight gate and any session-context feature scope.

### Mitigation
The entry contract gates on `SESSION_LABEL_GUARD_FIX_V1` status; Agent Factory must not rely on
`rth_flag`/`eth_flag`/`session_minute` until the guard is fixed or explicitly marked available; the
seed-pack features (`returns`/`log_returns`/`rolling_volatility`/`rolling_range`/`volume_zscore`/
`range_position`) are used instead; session-context use before the fix is fail-closed and routes to
rework.

### Owner
Codex (preflight gate + non-session seed features) / Claude Opus (scope review).

### Related Phases
AGENT-P01, AGENT-P12.

### Blocking Condition
A session-context (`session_label`-derived) feature (`rth_flag`/`eth_flag`/`session_minute`) is
used before `SESSION_LABEL_GUARD_FIX_V1`.

---

## R-014 — Feature/Label packs not resolved (accepted-DatasetVersion bypassed)

### Description
A role or tool produces feature/label inputs without resolving an **accepted** `DatasetVersion`
and its registered seed FeaturePack/LabelPack through the sanctioned
`alpha_system.data.foundation.version_registry.resolve_dataset_version` boundary — reading a
registry table directly, hard-coding a path, or accepting a non-admissible version state.

### Impact
The single sanctioned consumption boundary is broken: agents consume data that has not passed
quality/coverage/admissibility gating, so every downstream tool result, dry-run, and handoff
inherits ungated, possibly contaminated inputs. S1.

### Likelihood
L2 — convenience access to a known registry/path or pack is plausible in a role/tool unless the
only sanctioned API is enforced and admissibility (`VERSIONED`/`READY_FOR_RESEARCH`) is checked.

### Detection
* `data_access_policy`: `accepted_dataset_version_required: true`,
  `feature_label_pack_required_for_runtime: true`,
  `sanctioned_consumption_api: ...resolve_dataset_version`, admissible states `{VERSIONED,
  READY_FOR_RESEARCH}`; `risk_controls.accepted_dataset_version_required`
  (`resolve_dataset_version_only`, `admissible_states_versioned_or_ready_for_research`) via Data
  Contract Auditor tests + Claude review.
* AGENT-P10 Data Contract Auditor verifies DatasetVersion/FeaturePack/LabelPack availability and
  admissibility via registry tools only; AGENT-P11 Feature/Label Engineers reference approved seed
  packs; `forbidden_paths` block `data/**` edits.
* `merge_policy.global_blockers`: `accepted DatasetVersion bypassed`; `stop_conditions`: `accepted
  DatasetVersion bypassed`.
* Claude Opus review of AGENT-P10/P11 resolution semantics.

### Mitigation
`resolve_dataset_version` is the only resolution path; only `VERSIONED`/`READY_FOR_RESEARCH`
versions are admissible; the Data Contract Auditor resolves packs through registry tools without
raw access or registry writes; Databento and IBKR versions are never merged; bypass is fail-closed
and merge-blocking.

### Owner
Codex (registry-tool-bound resolution + admissibility checks) / Claude Opus (boundary review).

### Related Phases
AGENT-P10, AGENT-P11.

### Blocking Condition
Feature/Label inputs are produced without resolving an admissible `DatasetVersion` and its
registered packs through `resolve_dataset_version`.

---

## R-015 — RuntimeToolResult not parsed safely

### Description
The runtime bridge or the Diagnostics Runner consumes `RuntimeToolResult` / `RuntimeRunSummary`
unsafely — assuming fields are present, mishandling a `BLOCKED`/`REJECTED`/`INCONCLUSIVE`
outcome, dropping `blocking_findings`/`limitations`, or passing raw/heavy payloads through —
instead of mapping them defensively into a structured, value-free `AgentToolResult`.

### Impact
Unsafe parsing can crash on a missing field, silently swallow a runtime block/rejection (cross-links
R-009 / R-011), or let raw/heavy data flow into agent context (cross-links R-008), undermining the
agent-facing contract the bridge exists to provide. S2.

### Likelihood
L2 — "happy-path" parsing that assumes a successful result is the simplest implementation unless
the bridge is required to handle every runtime outcome and strip raw/heavy data.

### Detection
* `runtime_integration_policy.runtime_tool_result_contracts`
  (`...RuntimeToolResult`, `...RuntimeRunSummary`); `risk_controls.runtime_consumed_not_bypassed`
  and `risk_controls.structured_tool_outputs_required` via runtime-bridge tests + tool-result tests
  + Claude review.
* AGENT-P21 `runtime_bridge.py` maps every runtime status (including `BLOCKED`/`REJECTED`/
  `INCONCLUSIVE`) into a value-free `AgentToolResult`, preserving `blocking_findings`/`limitations`
  and embedding no raw/heavy data; AGENT-P13 Diagnostics Runner consumes the bridge output only.
* `merge_policy.global_blockers`: `tool contract with unstructured output or embedded raw/heavy
  data`; `stop_conditions`: `tool result exposes raw or heavy data`.
* Claude Opus review of AGENT-P21 parsing/adaptation and AGENT-P13 consumption.

### Mitigation
The bridge defensively maps all runtime outcomes into the structured `AgentToolResult`, preserves
blocking/limitation fields, and strips raw/heavy data; tests assert no raw/heavy payload and
correct handling of non-success outcomes; the Diagnostics Runner never parses runtime objects
directly.

### Owner
Codex (defensive bridge + outcome handling) / Claude Opus (bridge-contract review).

### Related Phases
AGENT-P05, AGENT-P13, AGENT-P21.

### Blocking Condition
The bridge/role consumes `RuntimeToolResult`/`RuntimeRunSummary` without handling every outcome
safely, drops blocking/limitation fields, or passes raw/heavy data into an `AgentToolResult`.

---

## R-016 — Human approval bypassed for risk/capital

### Description
An agent makes — or a contract permits an agent to make — a risk, capital, or live decision
reserved for the human, or a permission entry that should carry `HumanApprovalRequired` /
`RedLaneRequired` omits it, automating a judgment the human owns.

### Impact
Automating a risk/capital/live judgment crosses the campaign's hardest boundary — the human owns
risk/capital/live judgment — and is the gateway to broker/order/account scope; an agent that can
decide capital is no longer a constrained worker. S1.

### Likelihood
L2 — a "convenience" decision flag or a missing human-approval requirement is plausible unless the
matrix marks every such action `HumanApprovalRequired` and tests assert it.

### Detection
* `agent_policy.human_capital_judgment_required: true`; hard rule `human owns risk/capital/live
  judgment`; `agents_may_never` includes `touch capital allocation`;
  `risk_controls.human_capital_judgment_required` (`human_owns_risk_capital_live_judgment`,
  `human_approval_required_flag_respected`) via permission-matrix audit + Claude review.
* AGENT-P04 matrix carries `HumanApprovalRequired`/`RedLaneRequired` flags; AGENT-P16 enforcement
  asserts no role can take a human-reserved action without the flag.
* `merge_policy.global_blockers`: includes broker/order/account scope; `stop_conditions`: `capital
  or live judgment automated` (`stop_and_escalate`).
* Claude Opus review of AGENT-P04/P16 human-approval flags.

### Mitigation
Every risk/capital/live action is marked `HumanApprovalRequired` (or is simply absent from the MVP
scope); the matrix and enforcement prevent an agent from taking a human-reserved action; the human
owns risk/capital/live judgment; automation of such a judgment stops and escalates.

### Owner
Codex (human-approval flags + enforcement) / Claude Opus (human-judgment review) / Human (final
risk/capital/live authority).

### Related Phases
AGENT-P04, AGENT-P16.

### Blocking Condition
An agent makes (or a contract permits) a risk/capital/live decision reserved for the human, or a
human-reserved action lacks `HumanApprovalRequired`.

---

## R-017 — Broker/live/paper scope creep

### Description
Any broker, live-trading, paper-trading, order-routing, order-placement, account-trading, or
production-execution scope is introduced — code, dependency, config, or a role/permission — into
the local-only, broker-disabled Agent Factory contract layer.

### Impact
Broker/live/paper scope crosses the campaign's outermost boundary (broker disabled, no order/
account/paper/live scope), turning a contract layer into trading infrastructure and reaching the
prohibited states `LIVE_READY` / `PAPER_READY`; the campaign cannot be accepted. S1.

### Likelihood
L2 — aspirational "wire it to paper" or "add an order stub" impulses are plausible once roles and a
runtime bridge exist unless the broker/live/paper forbidden scope holds.

### Detection
* `project_profile`: `broker_live_trading_in_scope: false`, `paper_trading_in_scope: false`,
  `order_placement_in_scope: false`, `account_trading_in_scope: false`;
  `phase_defaults.forbidden_global_changes` includes broker integration / paper / live / order
  routing / order placement / account trading / production execution adapter;
  `agents_may_never` includes `create paper/live/broker/order code`.
* Every phase's `forbidden_paths` blocks `execution/broker/**`, `execution/live/**`,
  `execution/paper/**`, `execution/order_router*`, `broker/**`, `live/**`; `risk_controls.no_strategy_scope`
  and the AGENT-P25 acceptance audit/done-check.
* `merge_policy.global_blockers` (broker/order surface) and `stop_conditions`: `capital or live
  judgment automated` (`creates paper/live/broker/order code` → `stop_and_escalate`).
* Claude Opus review of AGENT-P04/P25 for any broker/live/paper/order/account surface.

### Mitigation
No broker/live/paper/order/account/production-execution scope is introduced; those paths are
forbidden in every phase; no role holds such permissions; the prohibited `LIVE_READY`/`PAPER_READY`
states are unreachable; any such scope stops and escalates.

### Owner
Codex (no broker/order surface) / Claude Opus (scope review) / Ralph (scope/stop enforcement).

### Related Phases
AGENT-P04, AGENT-P25.

### Blocking Condition
Any broker/live/paper/order-routing/order-placement/account-trading/production-execution scope is
introduced anywhere in the campaign.

---

## R-018 — Memory records become a dumping ground

### Description
The agent memory layer accumulates unstructured, un-typed, or value-bearing records instead of the
defined value-free record types (`AgentRunRecord`, `AgentDecisionRecord`, `AgentHandoff`,
`RejectedIdeaMemoryRecord`, `ResearchMemoryRecord`, `ToolInvocationRecord`, `AgentAuditLog`,
`AgentPromptVersion`, `AgentRoleVersion`, `AgentPermissionVersion`) — so memory becomes a
catch-all that embeds raw/heavy data or loses its structure.

### Impact
A dumping-ground memory cannot support duplicate avoidance or prior-rejection surfacing (cross-links
R-010), can embed raw/heavy values (cross-links R-008/R-026 artifact policy), and erodes the
versioned, auditable record contract the campaign installs. S2.

### Likelihood
L2 — "log everything" into a free-form memory is easy and tempting unless the record types are
strict, value-free contracts that consume (not duplicate) the governance graveyard.

### Detection
* `memory_policy.record_types` (the ten record types above), `no_full_factor_library_or_alphabook_yet:
  true`, `consumes_governance_rejected_idea_and_graveyard: true`;
  `risk_controls.failed_and_rejected_ideas_visible` + artifact policy checks.
* AGENT-P18 `memory/models.py` and AGENT-P17 `records/models.py` define typed, value-free record
  contracts; tests assert structure and no raw/heavy data; memory consumes the governance graveyard
  rather than re-defining it.
* `merge_policy.global_blockers`: `tool contract with unstructured output or embedded raw/heavy
  data`, artifact-policy blockers; `stop_conditions`: `raw or heavy data artifact staged`.
* Claude Opus review of AGENT-P17/P18 record structure and value-freeness.

### Mitigation
Memory and records use the defined typed, value-free contracts; they carry summaries, ids, and
references, never raw/heavy values; the memory consumes the governance graveyard; structure and
no-raw-data are tested; an unstructured/value-bearing memory record is fail-closed.

### Owner
Codex (typed value-free record/memory contracts) / Claude Opus (record-structure review).

### Related Phases
AGENT-P18.

### Blocking Condition
None on its own (S2, non-blocking); flagged in the AGENT-P18 review when memory records are
unstructured, and escalates to R-008 (raw/heavy data in a record) or the artifact-policy blockers
if values are embedded or staged.

---

## R-019 — Agent docs scatter across repo

### Description
Agent prompt/skill assets or `docs/agent_factory/**` documentation are scattered across the repo
without a single source-of-truth index — prompts placed outside
`templates/agent_factory/prompts/**`, docs duplicated across waves, or no `README.md` index — so
the durable agent assets become hard to find and drift.

### Impact
Scattered, unindexed prompts and docs erode the "durable, indexed assets" goal, increase the chance
of stale or conflicting role instructions (cross-links R-007), and make the operator guide and
readiness docs unreliable. S3.

### Likelihood
L2 — assets sprinkled near where they were written, without an enforced index, are a common
documentation failure unless a source-of-truth index is required.

### Detection
* `risk_controls.agent_docs_indexed` (`no_scattered_unindexed_agent_prompts`,
  `source_of_truth_index_present`) via docs index check + Claude review.
* AGENT-P19 `templates/agent_factory/prompts/README.md` is the prompt source-of-truth index;
  AGENT-P20 `docs/agent_factory/{GUIDE,OPERATOR,NEXT_CORE_ALPHA_PILOT_READINESS}.md` are the
  operator docs; AGENT-P02 `NAMING.md` sets the index policy; the two assets phases own disjoint
  paths.
* `merge_policy.global_blockers` (agent prompts scattered); `stop_conditions`: `agent prompts
  scattered`.
* Claude Opus review of AGENT-P19/P20 indexing and disjointness.

### Mitigation
All prompt templates live under `templates/agent_factory/prompts/**` with a `README.md`
source-of-truth index; docs live under `docs/agent_factory/**` per the naming policy; AGENT-P19 and
AGENT-P20 own disjoint paths; scattered/unindexed assets are flagged and route to rework.

### Owner
Codex (indexed prompts + docs) / Claude Opus (indexing/disjointness review).

### Related Phases
AGENT-P19, AGENT-P20.

### Blocking Condition
Agent prompt assets are scattered across the repo without a source-of-truth index (the
`agent prompts scattered` stop condition); otherwise flagged at AGENT-P19/P20 review.

---

## R-020 — DAG metadata wrong / parallel conflict

### Description
A phase declares incorrect or missing DAG metadata (`parallel_safe`, `must_run_alone`,
`allowed_paths`, `merge_group`, `dependencies`), or two phases in the same parallel wave write
overlapping `allowed_paths`, so the DAG wave scheduler parallelizes a run-alone phase, mis-orders
waves, or builds a wave with a path conflict (W1 role contracts AGENT-P07..P15; W3 assets
AGENT-P19/P20/P21).

### Impact
The scheduler builds an unsafe wave (e.g. a run-alone integration phase concurrent with a role
phase, or two role phases editing a shared `roles/__init__.py`), risking path/resource conflicts,
corrupt merges, or a phase branch writing `ACTIVE_CAMPAIGN.md` in parallel mode. S2.

### Likelihood
L2 — DAG metadata is easy to get subtly wrong, and the nine concurrent W1 role phases plus three
W3 assets phases can collide on a shared file unless `allowed_paths` are strictly disjoint and
shared modules are forbidden to parallel phases.

### Detection
* `workflow2`: `max_parallel_phases: 3`, `merge_queue: serial`, `update_active_campaign:
  coordinator_only`; requirements `run_frontier_plan_before_execution`,
  `run_parallel_mock_before_first_live_parallel_run`,
  `parallel_safe_phases_require_disjoint_allowed_paths`; default posture is run-alone
  (`default_parallel_safe: false`, `default_must_run_alone: true`).
* `risk_controls.dag_parallel_requires_allowed_paths`
  (`parallel_safe_phase_requires_disjoint_allowed_paths`,
  `no_global_coordinator_file_in_parallel_phase_allowed_paths`),
  `risk_controls.serial_merge_queue_required`, and `risk_controls.acceptance_gate_coverage_required`
  via plan-dag preview + dag_scheduler validation + campaign.yaml validation script; W1/W3 role and
  assets phases omit `runs/**` and never list `ACTIVE_CAMPAIGN.md`; role phases do not edit
  `roles/__init__.py` / `roles/registry.py`.
* `merge_policy.global_blockers` / `stop_conditions`: `parallel phase lacks allowed_paths`,
  `parallel wave has path/resource conflict`, `phase branch writes ACTIVE_CAMPAIGN.md in parallel
  mode`, `merge outside serial merge queue`, `PHASE_PLAN / campaign.yaml mismatch`.
* Claude Opus review of DAG metadata correctness and per-wave disjointness (an explicit
  `review_must_check` item) plus AGENT-P24 documentation.

### Mitigation
Parallel-safe phases (AGENT-P07..P15, AGENT-P19/P20/P21) declare disjoint `allowed_paths`,
`must_run_alone: false`, and no global/coordinator file; everything else runs alone by default;
`frontier-plan` and the parallel mock run before any live parallel run; the merge queue is serial;
PHASE_PLAN and campaign.yaml are kept in agreement; AGENT-P24 documents the exact plan.

### Owner
Ralph (DAG scheduler + plan/mock gating + serial merge) / Codex (additive disjoint writes) /
Claude Opus (DAG-metadata review).

### Related Phases
AGENT-P24.

### Blocking Condition
A parallel-safe phase lacks disjoint `allowed_paths`, two phases in a wave conflict on paths/
resources, a phase branch writes `ACTIVE_CAMPAIGN.md` in parallel mode, a merge occurs outside the
serial queue, or PHASE_PLAN and campaign.yaml DAG metadata disagree.

---

## R-021 — Agent Factory blocks Core Alpha Pilot with overbuilding

### Description
The contract layer is overbuilt — adding speculative roles, a continuous runner, a heavy
orchestration platform, premature promotion/strategy/portfolio machinery, or distributed compute —
beyond the bounded MVP, delaying and complicating the downstream
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` rather than enabling it.

### Impact
Overbuilding inflates the contract layer into infrastructure the Core Alpha Pilot does not need,
adds dependencies and scope, and risks reaching forbidden alpha-search / promotion / autonomous-runner
scope (cross-links R-001), pushing the actual pilot further out. S2.

### Likelihood
L2 — "build it all now so the pilot is easy" is a common over-engineering impulse once the role
model and runtime bridge exist.

### Detection
* `compute_policy`: `local_only: true`, `deterministic: true`, `no_distributed_compute_required:
  true`, `no_ray_cluster: true`, `no_ml_experiment_platform: true`,
  `heavy_dependencies_require_justification: true`; `agent_policy.optional_later_roles_not_mvp`
  enumerates roles explicitly out of scope.
* AGENT-P25 acceptance audit + semantic done-check and the
  `docs/agent_factory/NEXT_CORE_ALPHA_PILOT_READINESS.md` readiness doc (AGENT-P20) keep scope to
  what the pilot needs; `risk_controls.no_strategy_scope` blocks premature strategy/portfolio/ML
  scope.
* `merge_policy.global_blockers` (strategy/backtest/portfolio scope, autonomous agent/continuous
  runner) and the AGENT-P25 done-check guard against scope inflation.
* Claude Opus review of dependencies and scope across phases, focused on AGENT-P25 closeout.

### Mitigation
The MVP stays contracts-only, local-only, deterministic, and dependency-light; optional later roles
and platform scale are deferred to named follow-ups; the readiness doc records exactly what the
Core Alpha Pilot needs; overbuilding into forbidden scope is merge-blocking.

### Owner
Codex (bounded contracts) / Claude Opus (scope/dependency review) / ChatGPT (roadmap scoping and
Core-Alpha-Pilot framing).

### Related Phases
AGENT-P25.

### Blocking Condition
None on its own (S2, non-blocking); becomes blocking via R-001 (alpha-search/autonomous-runner
scope), the strategy/backtest/portfolio blockers, or R-026 (unjustified heavy dependencies) if
overbuilding crosses a forbidden scope.

---

## R-022 — Agent Factory underbuilds and agents still write ad hoc scripts

### Description
The contract layer is underbuilt — missing roles, an incomplete permission matrix or tool
registry, a non-functional runtime bridge, or a dry-run that does not exercise the full lifecycle —
so a future agent has no durable contract to operate through and falls back to ad hoc scripts that
bypass the runtime, governance, or registry.

### Impact
Underbuilding defeats the campaign's purpose: the future AI research team would improvise
runtime/governance/registry access under pressure (the exact overfit-machine conditions the Agent
Factory exists to prevent), and the Core Alpha Pilot would have to wire the team up from scratch. S2.

### Likelihood
L2 — shipping a partial contract layer that "looks done" is plausible unless the acceptance gates
require every role, the matrix, the tool registry, the bridge, and a full-lifecycle dry-run.

### Detection
* Acceptance gates require the full contract surface: `core_contracts` (role model + matrix + tool
  registry + queue), `agent_roles` (all ten roles), `enforcement_and_records` (separation + records
  + memory), `assets_and_bridge` (prompts + docs + bridge), `dry_run_and_closeout` (full-lifecycle
  dry-run + closeout); `acceptance_gate_coverage_required` ensures every phase is covered.
* AGENT-P22/P23 dry-run exercises the full lifecycle (Director → Scout → Critic → Data Contract
  Auditor → Feature/Label Engineer → Diagnostics Runner → No-Lookahead Auditor → Statistical
  Reviewer → Librarian); AGENT-P25 semantic done-check verifies completeness against the
  `success_definition`.
* `no_test_weakening` / `fake_completion_forbidden`; `stop_conditions`: `semantic done-check
  failed`.
* Claude Opus review of AGENT-P25 completeness against GOAL/PHASE_PLAN success criteria.

### Mitigation
The acceptance gates and the AGENT-P25 semantic done-check require every role, the fail-closed
matrix, the structured tool registry, the runtime bridge, and a full-lifecycle dry-run; fake
completion is forbidden; an incomplete contract layer records a truthful `BLOCKED` rather than a
false `COMPLETE`.

### Owner
Codex (complete contract surface + full-lifecycle dry-run) / Claude Opus (completeness/done-check) /
ChatGPT (roadmap framing for Core Alpha Pilot readiness).

### Related Phases
AGENT-P25.

### Blocking Condition
None on its own (S2, non-blocking); becomes blocking at AGENT-P25 if the semantic done-check fails
(missing roles, incomplete matrix/tool registry/bridge, or a dry-run that does not exercise the
full lifecycle), which records a truthful `BLOCKED`.

---

## R-023 — Statistical Reviewer lacks independence

### Description
The Statistical Reviewer role is wired such that it can review work it implemented — or its
permission entry permits implementation — so the independent PASS/REJECT/WATCH/INCONCLUSIVE verdict
on runtime evidence is not actually independent of the implementer.

### Impact
A non-independent reviewer can rubber-stamp the implementer's own result, defeating the independent
statistical check that protects the evidence chain and enabling the manufactured-evidence failure
mode (a specific, high-leverage case of R-005). S2.

### Likelihood
L2 — combining "implement" and "review" into one role or permission is an easy convenience unless
`statistical_reviewer_independent_of_implementer` is enforced and tested.

### Detection
* `review_independence_policy`: `implementer_cannot_review: true`,
  `statistical_reviewer_independent_of_implementer: true`,
  `reviewer_verdict_required_for_any_watch_or_candidate: true`;
  `risk_controls.separation_of_duties_required` (`reviewer_is_not_implementer`) via
  separation-enforcement tests + Claude review.
* AGENT-P04 matrix denies the Statistical Reviewer any implementation/`WritePermission` over the
  work it reviews; AGENT-P16 enforcement proves reviewer≠implementer; the AGENT-P14 role contract
  forbids reviewing its own implementation.
* `merge_policy.global_blockers`: `reviewer is the implementer`; `stop_conditions`: `self-review or
  self-promotion`.
* Claude Opus review of AGENT-P04/P16 reviewer-independence.

### Mitigation
The Statistical Reviewer holds review permissions only, never implementation over the work it
reviews; separation enforcement proves reviewer≠implementer; the allowed verdicts are PASS/REJECT/
WATCH/INCONCLUSIVE on evidence the role did not produce; a non-independent reviewer is
merge-blocking and routes to rework.

### Owner
Codex (reviewer-only permissions + enforcement) / Claude Opus (independence review).

### Related Phases
AGENT-P04, AGENT-P16.

### Blocking Condition
The Statistical Reviewer reviews work it implemented, or its permission entry permits
implementation over the work it reviews.

---

## R-024 — Librarian updates registry without verdict

### Description
The Librarian role writes a registry, promotes, or records a memory entry as a registry write
without a preceding reviewer verdict (and `PromotionGate`) — updating a FactorLibrary/registry
outside the sanctioned tool APIs or ahead of the required verdict.

### Impact
A Librarian that can write a registry without a verdict bypasses the `no reviewer verdict → no
factor library entry` hard rule, enabling silent promotion and a registry write outside governance
control. S2.

### Likelihood
L2 — letting the Librarian "just record it" into a registry is a convenience that skips the verdict
gate unless `librarian_cannot_update_registry_without_verdict` is enforced and tested.

### Detection
* `review_independence_policy.librarian_cannot_update_registry_without_verdict: true`;
  `agent_policy` hard rule `no reviewer verdict -> no factor library entry`; the Librarian's
  `forbidden: registry writes outside sanctioned tool APIs`;
  `risk_controls.separation_of_duties_required` (`librarian_cannot_write_registry_without_verdict`)
  via separation-enforcement tests + Claude review.
* AGENT-P04 matrix denies the Librarian direct registry writes/`PromotionPermission`; AGENT-P16
  enforcement proves a registry write requires a reviewer verdict; the AGENT-P15 role contract
  records proposed memory only after a verdict.
* `merge_policy.global_blockers`: `librarian updates a registry without a reviewer verdict`;
  `stop_conditions`: `librarian writes registry without verdict`.
* Claude Opus review of AGENT-P04/P16 Librarian permissions.

### Mitigation
The Librarian records decisions/rejections and proposes memory only after a reviewer verdict; it
holds no direct-registry-write or promotion permission; registry writes occur only through
sanctioned tool APIs after a verdict + `PromotionGate`; a verdict-less registry write is
merge-blocking and routes to rework.

### Owner
Codex (verdict-gated Librarian + enforcement) / Claude Opus (Librarian-permission review).

### Related Phases
AGENT-P04, AGENT-P16.

### Blocking Condition
The Librarian updates a registry or promotes without a reviewer verdict + `PromotionGate`, or
writes a registry outside the sanctioned tool APIs.

---

## R-025 — Tool contract drift from runtime implementation

### Description
The agent-facing tool contracts and the runtime bridge drift from the actual runtime
implementation — referencing fields, statuses, or CLI subcommands that
`RuntimeToolResult` / `RuntimeRunSummary` / `alpha runtime` no longer expose, or mis-mapping the
runtime's outputs — so a tool contract that imports cleanly silently mis-represents the runtime.

### Impact
Drift between the tool contracts and the real runtime produces tool results that misstate runtime
status/versions or break at call time, undermining the agent-facing contract the campaign prepares
for the Core Alpha Pilot, and tempting a re-implementation shortcut (cross-links R-002/R-026). S2.

### Likelihood
L2 — the runtime is consumed (not pinned in this campaign), so its contracts can evolve; a tool
contract written against an assumed shape drifts unless the bridge imports the real runtime
contracts and tests assert the mapping.

### Detection
* `runtime_integration_policy`: `runtime_tool_use_required: true`, `runtime_consumed_not_edited:
  true`, `runtime_tool_result_contracts` (the real dotted paths), `runtime_cli_surface:
  alpha_system.cli.runtime`; `risk_controls.runtime_consumed_not_bypassed`
  (`tools_call_runtime_tool_results_and_resolve_dataset_version`, `runtime_package_not_edited`) and
  `risk_controls.consume_not_duplicate` via source-path/import audit + Claude review.
* AGENT-P21 `runtime_bridge.py` imports the real `RuntimeToolResult`/`RuntimeRunSummary` and maps
  them; AGENT-P05/P13 tool contracts reference the real CLI surface; `python -c "import
  alpha_system.agent_factory.runtime_bridge"` and bridge tests catch drift; baseline dependency
  warnings are recorded if the runtime is not on `main`.
* `merge_policy.global_blockers`: `runtime bypassed instead of called via tool contract`, `duplicate
  of an existing governance/runtime/research/experiments/backtest primitive`; `stop_conditions`:
  `runtime bypassed`, `duplicate of existing primitive introduced`.
* Claude Opus review of AGENT-P21 mapping fidelity against the real runtime contracts.

### Mitigation
The bridge imports the real runtime tool-result contracts and maps them rather than re-defining
them; tool contracts reference the real CLI surface; tests assert the mapping against the imported
runtime; drift is caught at import/test time; the runtime is consumed and never edited or
duplicated.

### Owner
Codex (import-bound bridge + mapping tests) / Claude Opus (mapping-fidelity review).

### Related Phases
AGENT-P05, AGENT-P13, AGENT-P21.

### Blocking Condition
None on its own (S2, non-blocking); becomes blocking via R-002 (runtime bypassed) or R-026/the
duplicate-primitive blocker if drift is "fixed" by re-implementing or editing the runtime instead
of importing and mapping it.

---

## Blocking Risk Summary

The following are hard STOP/merge-block conditions (each maps to a `merge_policy.global_blockers`
entry, a `stop_conditions` entry, or a fail-closed gate):
**R-001, R-002, R-003, R-004, R-005, R-006, R-008, R-009, R-011, R-012, R-013, R-014, R-015,
R-016, R-017, R-020, R-023, R-024**. Any one of these makes the affected phase ineligible for merge
until resolved or truthfully blocked.

The remaining risks (**R-007, R-010, R-018, R-019, R-021, R-022, R-025**) are non-blocking on their
own (S2/S3) but are reviewed at their related phases and several escalate into a blocking condition
when they cross into a permission, separation, scope, duplication, or artifact violation (noted in
each entry).

## Risk Review Cadence

* **Per phase**: Claude Opus review checks the risks tied to that phase's Related Phases (the
  `review_must_check` list in `campaign.yaml` covers contracts-only / no-agent-instantiation,
  consume-not-duplicate, runtime-via-tool-contracts, accepted-DatasetVersion / no-raw-access,
  per-role permission entries, separation of duties, structured value-free tool outputs, preflight
  gates, parquet-sink and session-guard blockers, dry-run / EvidenceDraft / ReferenceCandidateHandoff
  scope honesty, rejected-idea visibility, DAG metadata, serial merge, artifact policy, no broker/
  live/paper scope, and no alpha/strategy claims).
* **Per gate**: each acceptance gate re-checks the blocking risks for its phases
  (`bootstrap_and_entry` → R-003/R-012/R-013/R-017; `core_contracts` → R-001/R-002/R-004/R-005/
  R-006/R-008/R-014/R-016/R-023/R-024; `agent_roles` → R-007/R-014/R-015; `enforcement_and_records`
  → R-004/R-005/R-006/R-009/R-010/R-016/R-018/R-023/R-024; `assets_and_bridge` → R-002/R-008/R-015/
  R-019/R-025; `dry_run_and_closeout` → R-001/R-011/R-020/R-021/R-022).
* **Per parallel wave**: before each live parallel run (W1 role contracts AGENT-P07..P15, W3 assets
  AGENT-P19/P20/P21), `run_frontier_plan_before_execution` and
  `run_parallel_mock_before_first_live_parallel_run` re-verify R-020 and serial-merge ordering.
* **Campaign closeout (AGENT-P25)**: the full register is reviewed in the acceptance audit and
  semantic done-check, including the no-claims/no-scope-creep audit (R-016/R-017), separation of
  duties (R-005/R-006/R-023/R-024), dry-run scope honesty (R-011), memory visibility (R-009/R-010/
  R-018), over/under-build balance (R-021/R-022), runtime/registry boundary (R-002/R-003/R-014/
  R-025), and `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` next-campaign readiness.

## Risk Ownership Summary

* **Ralph** — scope/stop enforcement, artifact policy + merge gating, DAG scheduler and serial
  merge queue, coordinator-only `ACTIVE_CAMPAIGN.md`, and external-call/broker prevention (primary
  on R-020; merge-gate enforcement of the scope/claims/broker blockers R-001/R-003/R-017 and the
  capital/live stop R-016).
* **Codex** — contracts-only construction (no agent instantiation, no duplication), the fail-closed
  permission matrix and separation enforcement, structured value-free tool contracts, the runtime
  bridge that imports and maps the runtime, accepted-DatasetVersion/canonical-only resolution, the
  preflight gates (parquet-sink, session-guard), typed value-free records and rejected-idea memory
  with duplicate avoidance, the bounded non-alpha dry-run, indexed prompts/docs, and local-only
  writes (R-001, R-002, R-004, R-005, R-006, R-007, R-008, R-009, R-010, R-011, R-012, R-013,
  R-014, R-015, R-018, R-019, R-023, R-024, R-025).
* **Claude Opus** — semantic review of the contracts-only / consume-not-duplicate boundary, the
  permission/separation/independence boundaries, the runtime/DatasetVersion/raw-access boundary,
  structured tool outputs, dry-run/EvidenceDraft/handoff scope honesty, the preflight blockers, DAG
  metadata, serial merge, claims/no-claims, and the final done-check (the semantic review side of
  every risk; primary on R-005, R-006, R-011, R-016, R-023, R-024).
* **ChatGPT** — roadmap framing and over/under-build balance against the downstream Core Alpha
  Pilot (R-021, R-022), scoping against premature platform/strategy build (R-001/R-021), and
  post-run reasoning.
* **Human (repo owner)** — direction and risk/capital/live judgment; this campaign is local-only
  with no RED-lane phases and no external provider calls, so no per-operation human authorization is
  required, but the human owns risk/capital/live judgment (R-016) and final acceptance of the
  contract layer.

---

*This file is a campaign contract describing the intended risks, controls, and boundaries of
ALPHA_AGENT_FACTORY_MVP; it instantiates no autonomous agent, runs no continuous research runner,
and makes no claim that any alpha is validated, tradable, profitable, robust, production-ready,
paper-ready, live-ready, or broker-ready, and no claim that any factor is promoted.*
