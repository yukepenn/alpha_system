# Architecture

Document the structure and key design choices for `alpha_system`.

## Harness Spine

```text
campaigns/
specs/
handoffs/
reviews/
runs/
frontier.yaml
AGENTS.md
CLAUDE.md
```

The harness is a repo-native operating layer. It should support project work without owning business logic.
