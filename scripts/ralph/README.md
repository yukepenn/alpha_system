# Ralph Scripts

Run the built-in smoke campaign:

```bash
scripts/ralph/ralph.sh --campaign-id G005_WORKFLOW2_TOY
```

Preferred just recipes:

```bash
just frontier-run-campaign <campaign>
just frontier-run-next <campaign>
just frontier-run-campaign-mock <campaign>
just frontier-run-next-mock <campaign>
just frontier-run-campaign-ledger <campaign>
just frontier-run-overnight <campaign>
just frontier-resume <run_id>
just frontier-heartbeat <run_id>
```

`frontier-run-campaign` runs campaign-loop mode. `frontier-run-next` or `FRONTIER_MAX_PHASES=1` runs one phase for smoke/debug.

The local Ralph driver is provider-wired and safe by default. Green/yellow auto-merge can run for real when `frontier.yaml`, CI, verdicts, artifact policy, branch protection, and `gh` auth all pass. Red lane requires `FRONTIER_RED_AUTHORIZED=1` plus matching scope.
