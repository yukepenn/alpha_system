# Ralph Scripts

Run the deterministic local Workflow 2 toy campaign:

```bash
scripts/ralph/ralph.sh --campaign-id G005_WORKFLOW2_TOY
```

Run another scaffolded Workflow 2 campaign ledger:

```bash
scripts/ralph/ralph.sh --campaign-id CAMPAIGN_ID
```

Resume a scaffolded run:

```bash
scripts/ralph/ralph.sh resume --run-id RUN_ID
```

This is a local driver and strict-loop scaffold, not a production autonomous driver.
