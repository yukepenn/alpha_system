# Model Routing

Use role aliases from `frontier.yaml` instead of scattering concrete model names through prompts.

Provider CLI routing:

- Claude spec/review calls use `claude -p <prompt>`.
- Codex execution/repair calls use `codex exec --sandbox workspace-write <prompt>`.
- Claude semantic phase and campaign done-checks also use `claude -p <prompt>`.
- `FRONTIER_MOCK_PROVIDERS=1` replaces provider calls with deterministic local output.

Environment overrides:

```bash
FRONTIER_MOCK_PROVIDERS=1
FRONTIER_PROVIDER_TIMEOUT_SECONDS=1800
FRONTIER_CLAUDE_CMD=claude
FRONTIER_CODEX_CMD=codex
FRONTIER_CODEX_SANDBOX=workspace-write
```

GitHub routing is separate from provider routing and uses only the local `gh` CLI for PR, CI, branch protection, and merge operations.

Update `frontier.yaml` when concrete model or provider policy changes.
