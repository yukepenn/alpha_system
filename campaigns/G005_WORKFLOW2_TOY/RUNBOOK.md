# G005 Runbook

Run the toy campaign:

```bash
python tools/frontier/ralph_driver.py run --campaign-id G005_WORKFLOW2_TOY
```

Or with `just`:

```bash
just frontier-run-campaign G005_WORKFLOW2_TOY
```

Inspect a run:

```bash
just frontier-summary <run_id>
just frontier-tail <run_id>
```

Request a safe stop before the next phase:

```bash
just frontier-stop <run_id>
```

Resume a stopped toy run:

```bash
just frontier-resume <run_id>
```

The resume command removes the run's `STOP` file only for this deterministic toy campaign, then continues pending phases. Completed phases are not re-executed.
