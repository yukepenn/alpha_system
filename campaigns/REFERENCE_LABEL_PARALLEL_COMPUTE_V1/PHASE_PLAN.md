# REFERENCE_LABEL_PARALLEL_COMPUTE_V1 — Phase Plan

Serial chain (each phase depends on the previous): P00 → P01 → P02 → P03 → P04.
All phases `must_run_alone`; merge queue serial. Lanes: P00 GREEN, P01–P04
YELLOW (fresh Claude review).

### RLPC-P00 — Campaign Bootstrap + FUTSUB Pause-State Record (GREEN)

Land the bundle + evidence skeleton; record the FUTSUB-P19 pause truthfully
(STOP 2026-06-11T01:45Z mid full-window pass, ~134/216 cost_adjusted cells
durably checkpointed, registry/values/worktree preserved). No code, no
registry/value writes, no deletion.

### RLPC-P01 — Reference-Engine Unit-Parallel Worker Path (YELLOW)

`driver.py`: reference worker entrypoint running the UNCHANGED per-unit
reference pipeline inside the existing spawn ProcessPoolExecutor; loosen the
`engine == v1` parallel gate; serial parent-side registration in unit order +
checkpoint-after-registration (mirror the v1 contract). `cli/scaleout.py`:
honor `--workers` with `--engine reference` (default stays 1). Per-worker
thread caps (=2). Synthetic-fixture unit tests mirroring
`test_scaleout_worker_parallelism.py`: serial-order registration, per-unit
retryability, worker-plan caps, parent-only registry writes,
checkpoint-after-registration ordering.

### RLPC-P02 — Determinism, Single-Writer, Interruption-Resume Gate (YELLOW)

workers=1 vs workers=4 on a synthetic multi-family grid → IDENTICAL records,
label_version_ids, content hashes, registry rows/lineage, guard outcomes,
label_available_ts (no tolerances; any diff = BLOCKED). Kill-between-units →
resume with no duplicates/holes; ledger rows 1:1 with registered units.
Single-writer audit + canary-style guard test (fails if workers ever write the
registry). Optional bounded real-slice spot-check when local data exists; CI
skips cleanly.

### RLPC-P03 — Bounded Real Benchmark + Release Gate (YELLOW, resource_class materialization_registry)

Real bounded self-validating cost_adjusted grid (>=8 runnable units, contains
a roll event + session/maintenance gap), isolated benchmark data root, sweep
workers 1/2/4/8. Report units/sec, speedup vs workers=1, component timings
(worker compute vs serial registration), RSS, registry delta, determinism
spot-check. Release policy: workers=8 if >=3.0x, else NOT_RELEASED + honest
component-timing diagnosis. Reference never timed full-window; production
registry never targeted.

### RLPC-P04 — FUTSUB Amendment + Resume Handoff + Backlog Closeout (YELLOW)

Amend FUTSUB ENGINE POLICY (P19 + future reference-family label work) to the
MEASURED released policy (or record NOT_RELEASED honestly and change nothing).
Update backlog §6 (option 1 delivered/blocked; option 2 stays). Write
`FUTSUB_RESUME_ON_PARALLEL_REFERENCE.md` with exact coordinator resume steps
(repoint ACTIVE_CAMPAIGN, clear STOP, P19 → clean PENDING state surgery,
resume run; checkpointed cells durable). Lessons to project-skill if earned.

## Expected outcome

P19's remaining ~82 cells: ~70 min serial → ~10–15 min at 6–7x; any future
full-window reference-family pass: ~3h → ~30 min.
