# Agent Factory Dry Run

`alpha_system.agent_factory.dry_run.harness` is a bounded, local-only harness
for proving Agent Factory machinery on synthetic fixture refs. It routes exactly
one `ResearchTask` once through the MVP role order:

1. Research Director scopes one tiny bounded task.
2. Hypothesis Scout drafts three `AlphaSpec` draft refs and surfaces prior
   rejected-idea memory.
3. AlphaSpec Critic rejects or revises most drafts and forwards one synthetic
   survivor ref.
4. Data Contract Auditor checks the synthetic DatasetVersion / FeaturePack /
   LabelPack refs through the resolver surface.
5. Feature Engineer and Label Engineer reference one approved seed input each.
6. Diagnostics Runner adapts a bound synthetic runtime result through
   `runtime_bridge`.
7. No-Lookahead Auditor records a PASS integrity gate over summary refs only.
8. Statistical Reviewer issues `REJECT`.
9. Librarian proposes rejected-idea and research memory records after the
   reviewer verdict.

The dry run is not alpha evidence. An `EvidenceDraft` is not a candidate, and a
`ReferenceCandidateHandoff` is not Reference validation. The most advanced
forward state reachable by the synthetic survivor is
`REFERENCE_HANDOFF_RECORDED`; terminal states are `REJECTED`, `INCONCLUSIVE`,
and `BLOCKED`. Promotion states, strategy states, paper/live states,
profitability/tradability states, and autonomous-runner states remain
unreachable.

The harness consumes existing Agent Factory contracts:

- role declarations and permission matrix entries;
- separation-of-duties wiring and concrete rule checks;
- `ResearchQueue` / `ResearchTask` budget and review requirements;
- registered `ToolInvocationRecord` contracts where the shared tool registry
  exposes the role tool surface;
- `AgentDecisionRecord`, `AgentHandoff`, and value-free `AgentToolResult`;
- `RejectedIdeaMemoryRecord` and `ResearchMemoryRecord`;
- `runtime_bridge.adapt_runtime_tool_result`.

It does not edit or duplicate runtime, governance, registry, feature, label, or
data primitives. It does not instantiate an autonomous agent, start a
continuous research loop, run alpha search, materialize feature or label
values, read provider files, call external providers, call broker APIs, route
orders, create a PR, merge, or promote any factor.

When the synthetic DatasetVersion resolver cannot resolve the fixture, the
harness returns a structured `BLOCKED` report instead of crashing or claiming
success. The default path uses a tiny in-process synthetic resolver and produces
only ids, refs, statuses, summaries, rejection reasons, gates, and limitations.
