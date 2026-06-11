# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer selects
`REFERENCE_LABEL_PARALLEL_COMPUTE_V1`. This Workflow 2 campaign removes a
reference-label throughput blocker by adding and validating unit-level worker
parallelism around the unchanged reference label engine.

RLPC-P02 adds the synthetic correctness gate for the reference-engine
unit-parallel worker path. The committed tests prove exact workers=1 vs
workers=4 equivalence on a fixed-horizon plus cost-adjusted-shaped grid,
interruption/resume safety, completed-checkpoint to registry 1:1 coverage, and
single-writer worker isolation. Default workers remain 1; after RLPC-P02
merges, the active next phase is RLPC-P03, the bounded real benchmark and
release gate.

Durable artifacts in this campaign snapshot:

- `campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/` - campaign contract bundle.
- `research/reference_label_parallel_compute_v1/` - value-free evidence
  root, including the RLPC-P02 synthetic determinism evidence note.
- `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/FUTSUB_PAUSE_STATE.md` -
  committed record of the stopped FUTSUB-P19 pause state and preservation
  boundary.
- `tests/unit/reference_label_parallel_compute/` - synthetic structural,
  determinism, resume, single-writer audit, and canary tests for the reference
  worker path.
- `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/RLPC-P02.md` - executor handoff
  for the determinism/resume/single-writer gate.

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

The per-row reference label engine remains the correctness oracle. RLPC-P02 does
not edit the reference engine, label families, roll guard, label versioning, or
any data artifact. Registry writes remain parent-only and serial; RLPC-P02 only
preserves ledger unit horizon metadata during resume so cost-adjusted checkpoint
truth rehydrates to the same unit identity. Later phases must preserve exact
identity, serial registry writes, roll/maintenance guards, and
`label_available_ts` no-lookahead behavior.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

This campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Workflow 2 orchestration, validation routing, review,
staging, commit, PR, CI, merge, and done-check actions are owned by Ralph.
