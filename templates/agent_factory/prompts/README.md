# Agent Factory Prompt Assets

This directory is the source-of-truth index for AGENT-P19 prompt and skill
templates. These files are templates only: they do not register Claude Code
subagents, instantiate autonomous agents, start a continuous research runner,
run tools, read data, call providers, or authorize broker, paper, live, order,
deployment, strategy, portfolio, factor-promotion, or alpha-search behavior.

## Naming Policy

Prompt files use stable `snake_case.md` names that match the MVP `AgentRole`
`role_id`. A prompt is consumable by later phases only when it is listed in
this index. New prompt assets must be added under this directory and indexed in
the same change; do not scatter operating prompts outside
`templates/agent_factory/prompts/`.

The older reserved `templates/agent_factory/roles/<role>.md` files are
role-phase templates. AGENT-P19 prompt assets live here and are the durable
source of truth for future role operating prompts.

## Shared Boundaries

Every prompt in this directory restates these campaign boundaries:

- Drive existing runtime, governance, registry, queue, records, and memory
  primitives through sanctioned Agent Factory tool contracts; never duplicate
  or edit those primitives.
- Resolve dataset inputs only through `resolve_dataset_version`; roles without
  that callable tool must consume a value-free Data Contract Auditor handoff.
- Read refs, ids, summaries, decisions, verdicts, and structured tool results
  only. Do not read raw provider data, runtime values, local value stores, or
  heavy artifacts.
- Make no external provider calls and perform no Databento, IBKR, broker,
  paper, live, account, order, deployment, strategy, portfolio, or production
  operation.
- Produce structured, value-free `AgentToolResult`-shaped outputs only.
- Preserve separation of duties: no self-review, no self-promotion, a
  diagnostics runner cannot promote, a reviewer cannot review its own work, and
  the Librarian needs an independent reviewer verdict before memory recording.
- The human owns risk, capital, live, and final judgment.

## Indexed Prompts

| Role | Prompt path | One-line purpose |
| --- | --- | --- |
| `research_director` | `templates/agent_factory/prompts/research_director.md` | Scope one bounded ResearchTask, assign roles, and set budgets within queue policy. |
| `hypothesis_scout` | `templates/agent_factory/prompts/hypothesis_scout.md` | Draft 3-5 value-free AlphaSpec draft refs for one scoped ResearchTask. |
| `alpha_spec_critic` | `templates/agent_factory/prompts/alpha_spec_critic.md` | Independently critique, reject, or request revision on AlphaSpec draft refs. |
| `data_contract_auditor` | `templates/agent_factory/prompts/data_contract_auditor.md` | Verify accepted DatasetVersion and seed-pack availability through registry tools. |
| `feature_engineer` | `templates/agent_factory/prompts/feature_engineer.md` | Reference approved seed features or draft one bounded FeatureRequest ref. |
| `label_engineer` | `templates/agent_factory/prompts/label_engineer.md` | Reference approved seed labels or draft one bounded LabelSpec ref. |
| `no_lookahead_auditor` | `templates/agent_factory/prompts/no_lookahead_auditor.md` | Audit runtime summary refs for point-in-time and label-leakage integrity. |
| `diagnostics_runner` | `templates/agent_factory/prompts/diagnostics_runner.md` | Request runtime diagnostics for one bound AlphaSpec and StudySpec within budget. |
| `statistical_reviewer` | `templates/agent_factory/prompts/statistical_reviewer.md` | Issue an independent PASS, REJECT, WATCH, or INCONCLUSIVE evidence verdict. |
| `librarian` | `templates/agent_factory/prompts/librarian.md` | Record decisions, rejected ideas, and memory updates after an independent verdict. |
