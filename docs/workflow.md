# Workflow

Document how work moves from campaign planning through implementation, review, and handoff.

## Workflow 1

Human-gated phase loop:

```text
strategy -> spec -> human approval -> Codex execution -> handoff -> Claude review -> human merge or repair
```

## Workflow 2

Ralph strict autonomous campaign loop scaffold:

```text
campaign -> phase spec -> execute -> checks -> handoff -> review -> repair or merge gate -> done-check -> next phase
```

Generated Workflow 2 code does not perform real provider calls or merges until explicitly implemented.
