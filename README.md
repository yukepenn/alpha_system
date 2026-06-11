# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer selects
`REFERENCE_LABEL_PARALLEL_COMPUTE_V1`. This Workflow 2 campaign removes a
reference-label throughput blocker by adding and validating unit-level worker
parallelism around the unchanged reference label engine in later phases.

RLPC-P00 is the bootstrap phase. It confirms the six-file campaign bundle,
creates the value-free evidence root, and records the paused FUTSUB-P19 state
without changing run state, registry state, label values, source code, tools, or
tests. After RLPC-P00 merges, the active next phase is RLPC-P01.

Durable artifacts introduced by this phase:

- `campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/` - campaign contract bundle.
- `research/reference_label_parallel_compute_v1/` - value-free evidence
  skeleton for later determinism and benchmark reports.
- `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/FUTSUB_PAUSE_STATE.md` -
  committed record of the stopped FUTSUB-P19 pause state and preservation
  boundary.
- `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/RLPC-P00.md` - executor handoff
  for this bootstrap phase.

The committed campaign pointer and README are snapshots. For authoritative
in-flight Workflow 2 state, use `python tools/frontier/status_doctor.py` or the
run-local state owned by Ralph.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Campaign bundle: `campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/`
- Value-free research evidence root:
  `research/reference_label_parallel_compute_v1/`
- Commit-eligible handoffs:
  `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
production deployment, account operations, capital allocation, or autonomous
trading behavior.

The per-row reference label engine remains the correctness oracle. RLPC-P00 does
not edit the reference engine, label families, registry code, scaleout driver,
CLI, tests, or any data artifact. Later phases must preserve exact identity,
serial registry writes, roll/maintenance guards, and `label_available_ts`
no-lookahead behavior.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

This campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Workflow 2 orchestration, validation routing, review,
staging, commit, PR, CI, merge, and done-check actions are owned by Ralph.
