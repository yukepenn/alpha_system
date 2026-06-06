# Agent Factory Overview

`ALPHA_AGENT_FACTORY_MVP` defines the controlled AI research-team contract layer
that drives the existing Research Runtime, governance objects, and accepted
DatasetVersion registry through sanctioned APIs. It is local-first and
contracts-only.

This phase creates documentation only. It adds no `agent_factory` package, no
runtime bridge, no role implementation, no provider access, no data access, and
no autonomous process.

## Contract Layer

The campaign will specify how constrained research workers interact with the
existing stack:

- role contracts define each worker's purpose, allowed inputs, tools, outputs,
  decisions, forbidden actions, handoff format, and independence requirements;
- permission contracts default-deny tool, data, write, review, promotion, human
  approval, and Red-lane access;
- tool contracts adapt runtime/governance/registry results into structured,
  value-free agent-facing outputs;
- queue contracts bound each research task and variant budget;
- separation-of-duties contracts prevent self-review and self-promotion;
- record and memory contracts keep decisions, handoffs, rejected ideas, and
  audit history visible.

The Agent Factory consumes `RuntimeToolResult` / `RuntimeRunSummary`, the
`alpha runtime` CLI surface, governance contracts such as `AlphaSpec` and
`StudySpec`, and `resolve_dataset_version`. It does not compute diagnostics
directly, bypass the runtime, read raw provider files, or write registries
directly outside sanctioned tool APIs.

## Lifecycle States

The contracts are expected to model a bounded research lifecycle:

```text
RESEARCH_TASK_QUEUED
DIRECTOR_SCOPED
HYPOTHESIS_DRAFTED
ALPHASPEC_DRAFTED
ALPHASPEC_CRITIQUED
ALPHASPEC_REVISION_REQUESTED
ALPHASPEC_REJECTED
DATA_CONTRACT_AUDITED
INPUTS_BLOCKED
IMPLEMENTATION_SCOPED
DIAGNOSTICS_REQUESTED
DIAGNOSTICS_COMPLETE
NO_LOOKAHEAD_AUDITED
STATISTICAL_REVIEW_PASS
STATISTICAL_REVIEW_WATCH
STATISTICAL_REVIEW_REJECT
STATISTICAL_REVIEW_INCONCLUSIVE
EVIDENCE_DRAFT_RECORDED
REFERENCE_HANDOFF_RECORDED
LIBRARIAN_MEMORY_RECORDED
REJECTED
INCONCLUSIVE
BLOCKED
```

`REFERENCE_HANDOFF_RECORDED` is the most advanced forward state any MVP dry-run
survivor may reach. That state is still not Reference validation and not factor
promotion.

## Prohibited MVP States

The following states are not reachable in this MVP:

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

If a phase introduces one of these states as an executable transition, or makes
a claim equivalent to one of them, that is outside this campaign's contract.

## Preflight Gates

`AGENT-P01` is expected to encode four preflight gates as contracts:

- a real seed FeaturePack and LabelPack exist locally;
- Research Runtime real-data smoke has passed with
  `real_dataset_version_smoke_ran: true`;
- `FEATURE_LABEL_PARQUET_SINK_V1` status is checked, and large-scale
  value-consuming studies are blocked until it lands or a human explicitly
  approves;
- `SESSION_LABEL_GUARD_FIX_V1` status is checked, and session-context features
  (`rth_flag`, `eth_flag`, `session_minute`) are blocked until the guard issue
  is fixed.

These gates do not authorize alpha search, factor promotion, strategy
validation, provider calls, or broker/live/paper/order/account behavior.
