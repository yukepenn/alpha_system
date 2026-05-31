# Runbook

## Commands

Record commands needed to validate or operate this campaign.

Default commands:

```bash
python tools/verify.py --all
python tools/hooks/canary_runner.py
python tools/frontier/ralph_driver.py run --campaign-id 000-template
```

## Rollback

Record rollback or recovery steps when applicable.
