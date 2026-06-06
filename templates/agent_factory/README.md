# Agent Factory Templates

This directory is the planned root for reusable Agent Factory templates.
AGENT-P02 creates only this index so later phases can add assets into stable
paths without changing shared roots.

Planned layout:

```text
templates/agent_factory/
  README.md
  roles/
    <role>.md
  prompts/
    README.md
    <prompt_name>.md
  research_task.template.yaml
  agent_handoff.template.md
```

The planned `roles/` and `prompts/` directories are populated by later phases.
The planned `research_task.template.yaml` and `agent_handoff.template.md` files
are also added by later phases. This phase does not create per-role templates,
prompt files, task templates, or handoff templates.

Templates are contracts and operator assets only. They do not instantiate an
agent, start a runner, perform alpha search, access data, call external
providers, or authorize broker, paper, live, order, account, deployment, or
production behavior.
