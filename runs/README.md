# Runs

Store command logs, validation transcripts, and operation notes that are useful for future review.

Workflow 2 run directories should use this shape:

```text
runs/<RUN_ID>/
├── RUN_GOAL.md
├── PHASE_PLAN.md
├── prd.json
├── progress.txt
├── state.json
├── events.jsonl
├── costs.jsonl
├── STOP
├── RUN_SUMMARY.md
└── phases/
```

`events.jsonl` and `costs.jsonl` are append-only ledgers.
