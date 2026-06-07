# Agent Factory Guide

`ALPHA_AGENT_FACTORY_MVP` defines constrained research workers, not autonomous
traders. The Agent Factory drives the existing `runtime.*`, `governance.*`, and
registry primitives through sanctioned contracts and never duplicates or edits
those primitives. This campaign does not instantiate an autonomous agent, does
not create a continuous research runner, does not search for alpha, and does not
promote a factor.

## Contract Map

The contract layer is a chain of value-free gates and records. Each link keeps
authority narrow and passes ids, refs, statuses, summaries, blockers, and next
gates only.

```text
[Entry contract + preflight gates]
  -> [Research queue / work item]
  -> [Role model + registry]
  -> [Permission matrix]
  -> [Tool contract registry + AgentToolResult]
  -> [Runtime bridge]
  -> [Separation-of-duties enforcement]
  -> [Agent records]
  -> [Rejected-idea / research memory]
  -> [Bounded non-alpha dry-run]
```

Component references:

- Entry contract and preflight gates: [PREFLIGHT_GATES.md](PREFLIGHT_GATES.md).
- Research queue and work item: [RESEARCH_QUEUE.md](RESEARCH_QUEUE.md).
- Role model and registry: [ROLES.md](ROLES.md).
- Permission matrix: [PERMISSIONS.md](PERMISSIONS.md).
- Tool contract registry and `AgentToolResult`: [TOOLS.md](TOOLS.md).
- Runtime bridge: the AGENT-P21 bridge adapts the existing Research Runtime
  surface described by [TOOLS.md](TOOLS.md) and
  [../research_runtime/CLI.md](../research_runtime/CLI.md); this guide does not
  implement or run it.
- Separation-of-duties enforcement:
  [SEPARATION_OF_DUTIES.md](SEPARATION_OF_DUTIES.md).
- Agent records and handoffs: [HANDOFFS.md](HANDOFFS.md).
- Rejected-idea and research memory: [REJECTION_MEMORY.md](REJECTION_MEMORY.md).
- Bounded non-alpha dry-run: planned for AGENT-P22 and AGENT-P23; until those
  phases land, this is a target harness, not an available runner.

The important invariant is that the Agent Factory consumes the existing
Research Runtime, governance objects, accepted DatasetVersion registry,
FeaturePack and LabelPack refs, and rejected-idea ledger by reference. The
contracts do not read raw provider files, materialize feature or label values,
write registries directly, bypass `AlphaSpec` / `StudySpec`, or replace runtime
diagnostics.

## Lifecycle

The agent-research lifecycle the contracts enforce is:

```text
RESEARCH_TASK_QUEUED -> DIRECTOR_SCOPED -> HYPOTHESIS_DRAFTED -> ALPHASPEC_DRAFTED -> ALPHASPEC_CRITIQUED (-> ALPHASPEC_REVISION_REQUESTED / ALPHASPEC_REJECTED) -> DATA_CONTRACT_AUDITED (-> INPUTS_BLOCKED) -> IMPLEMENTATION_SCOPED -> DIAGNOSTICS_REQUESTED -> DIAGNOSTICS_COMPLETE -> NO_LOOKAHEAD_AUDITED -> STATISTICAL_REVIEW_{PASS|WATCH|REJECT|INCONCLUSIVE} -> EVIDENCE_DRAFT_RECORDED -> REFERENCE_HANDOFF_RECORDED -> LIBRARIAN_MEMORY_RECORDED
```

Terminal states are:

```text
REJECTED
INCONCLUSIVE
BLOCKED
```

`REFERENCE_HANDOFF_RECORDED` is the most advanced forward state any dry-run
survivor may reach. That state is still only a recorded handoff inside the
Agent Factory boundary; it is not Reference validation, factor promotion, or
permission to use the result outside the governed research process.

The following MVP states are unreachable by any defined transition:

```text
ALPHA_VALIDATED
FACTOR_PROMOTED
STRATEGY_READY
PORTFOLIO_READY
CANDIDATE_PROMOTED
LIVE_READY
PAPER_READY
PROFITABLE
TRADABLE
PRODUCTION_READY
AUTONOMOUS_RESEARCH_RUNNING
```

If a future phase needs any of those concepts, it needs separate authorization,
separate evidence standards, and its own reviewed governance gates.

## Separation Of Duties

The separation rules are deliberately plain:

- A generator cannot approve the artifact it generated.
- An implementer cannot review the work it implemented.
- A Diagnostics Runner can request runtime diagnostics but cannot promote.
- A reviewer is not the implementer for the work under review.
- A Librarian cannot write a registry or memory path unless an independent
  reviewer verdict ref exists.
- The human owns risk, capital, live-use, and any external operating judgment.

These rules are enforced fail-closed by the separation layer and described in
[SEPARATION_OF_DUTIES.md](SEPARATION_OF_DUTIES.md). They reduce routine human
interaction by making boundaries machine-checkable, not by weakening any gate.
