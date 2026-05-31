# Model Routing

Use role aliases from `frontier.yaml` instead of scattering model names through prompts.

| Role | Default model | Use |
| --- | --- | --- |
| `chatgpt_strategist` | `gpt-5.5-thinking` | strategy, campaign design, post-run review |
| `codex_executor` | `gpt-5.5` | implementation and repair |
| `codex_fast_subagent` | `gpt-5.4-mini` | small exploration and mechanical edits |
| `claude_architect` | `claude-opus-4-8` | specs, architecture, ADRs |
| `claude_reviewer` | `claude-opus-4-8` | review and done-check |
| `claude_verifier` | `claude-sonnet-4-6` | repo map, verifier, audit |

Update `frontier.yaml` when the concrete model changes.
