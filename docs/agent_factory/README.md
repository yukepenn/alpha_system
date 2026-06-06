# Agent Factory Documentation

`docs/agent_factory/` is the durable documentation root for the
`ALPHA_AGENT_FACTORY_MVP` campaign.

The Agent Factory is the controlled AI research-team contract layer over the
completed governance, Feature/Label, and Research Runtime stack. In this MVP it
defines contracts only: role boundaries, permissions, tool contracts, research
queue rules, separation of duties, records, memory, prompt assets, runtime
bridge rules, and bounded dry-run protocols. It does not instantiate an
autonomous agent, start a continuous research runner, search for alpha, promote
a factor, validate a strategy, or introduce broker, live, paper, order, or
account scope.

The docs in this tree must keep the campaign posture explicit:

- Agents are constrained workers, not autonomous traders.
- Agent Factory drives existing runtime, governance, and registry primitives; it
  does not duplicate or edit them.
- Agent-facing outputs are structured and value-free; they do not embed raw or
  heavy data.
- Dry-run success is not alpha evidence, an `EvidenceDraft` is not a candidate,
  and a `ReferenceCandidateHandoff` is not Reference validation.
- The human owns risk, capital, paper, live, and broker judgment.

## Current Docs

- `README.md` - this entry point for the Agent Factory docs tree.
- `OVERVIEW.md` - concise contracts-only overview, lifecycle states,
  prohibited MVP states, and preflight gates.

## Planned Docs

Later phases are expected to add focused docs for:

- entry contract and preflight gates;
- package skeleton and naming;
- role contracts and role registry;
- permission matrix and tool access policy;
- structured tool contracts and value-free outputs;
- research queue and work-item contracts;
- separation-of-duties enforcement;
- agent handoff, decision, tool-invocation, audit, prompt-version, role-version,
  and permission-version records;
- rejected-idea memory and research memory;
- prompt and skill assets;
- runtime tool integration bridge;
- operator guide and Core Alpha Pilot readiness;
- bounded non-alpha dry-run and seed-pack/synthetic dry-run;
- Workflow 2 DAG integration and final acceptance audit.

Each added document should state its contract boundary, identify consumed
runtime/governance/registry primitives, and avoid alpha, tradability,
profitability, strategy, portfolio, paper, live, broker, production, or
deployment claims.
