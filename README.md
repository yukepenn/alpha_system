# alpha_system

This repository uses Frontier Harness Generic `3.0.0` with profile `trading_research`.

Start with:

```bash
python tools/verify.py --smoke
python tools/frontier/bootstrap.py doctor
python tools/frontier/ralph_driver.py run --campaign-id G005_WORKFLOW2_TOY
```

Project work should be organized through campaigns, specs, handoffs, reviews, decisions, and run ledgers.
