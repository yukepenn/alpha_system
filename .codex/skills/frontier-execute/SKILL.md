---
name: frontier-execute
description: Execute an active Frontier phase spec, run required checks, and produce a handoff.
---
# Frontier Execute Skill

You are the primary executor for a Frontier phase in `alpha_system`.

Read:

1. `AGENTS.md`
2. `frontier.yaml`
3. active campaign files
4. active phase spec
5. referenced handoffs and reviews

Execute exactly the spec.

Required:

- implement in scope
- write or update tests only when authorized
- run required checks
- write handoff
- commit curated files only
- never use `git add .`
- push branch

Stop if:

- spec is missing
- lane is unclear
- required command is impossible
- scope is contradictory
