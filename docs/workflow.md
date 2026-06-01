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

ASV1-P00B wires the local minimum viable ALPHA_SYSTEM_V1 conductor:
`frontier-run-campaign` is campaign-loop mode, while `frontier-run-next`
or `FRONTIER_MAX_PHASES=1` runs one safe smoke/debug phase.

ASV1-P00B also fixes the initial GitHub Actions CI bootstrap issue by
installing minimal Python test dependencies and skipping pytest only when
Python tests are genuinely absent.
