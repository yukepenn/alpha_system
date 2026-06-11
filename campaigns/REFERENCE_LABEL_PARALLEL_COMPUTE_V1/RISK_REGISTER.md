# REFERENCE_LABEL_PARALLEL_COMPUTE_V1 — Risk Register

| # | Risk | Likelihood | Impact | Mitigation / Gate |
|---|------|-----------|--------|-------------------|
| R1 | Concurrent SQLite registry writes (BUSY/corruption) | Low (by design) | Critical | Workers structurally cannot write the registry (no handle in the entrypoint); parent-only serial registration; RLPC-P02 single-writer audit + canary-style guard test. |
| R2 | Nondeterminism between serial and parallel output (ordering, caches, float state) | Medium | Critical | Spawn context (clean module state per worker); registration in deterministic unit order; RLPC-P02 exact-equality gate over records/ids/hashes/registry rows/guards/available_ts — any diff is BLOCKED, never a tolerance. |
| R3 | Checkpoint ledger corruption or unit loss under interruption | Medium | High | Checkpoint appended by parent only AFTER successful registration (v1 contract); RLPC-P02 kill-between-units resume test (no dupes, no holes, ledger↔registry 1:1). |
| R4 | Serial registration becomes the bottleneck (speedup ceiling < 3x) | Medium | Medium | RLPC-P03 component timings disclose compute vs registration; honest NOT_RELEASED path; backlog §6 option 2 (cost-kernel vectorization) is the recorded escalation, not a gate weakening. |
| R5 | Memory pressure: N reference workers × panel frames | Medium | Medium | Per-worker thread caps (=2); peak RSS reported per benchmark cell; worker plan caps at min(requested, cores, runnable units). |
| R6 | Scope creep into label math "while we're in there" | Low | Critical | `labels/engine.py`, `labels/families/**`, `roll_guard.py`, `version.py` are forbidden_paths; reviewer must verify the diff is orchestration-only. |
| R7 | Accidental mutation of the paused FUTSUB run (checkpoints, registry rows, worktree) | Low | High | FUTSUB run dir is runs/** (never staged); P00 records pause state read-only; only RLPC-P04 touches FUTSUB *contract files*; resume surgery is coordinator-owned, post-campaign. |
| R8 | Benchmark gamed or unrepresentative (tiny units, no roll/session edge cases) | Low | High | Self-validating slice requirement (roll event + session/maintenance gap or widen/fail); >=8 runnable units; real driver invocation required (stubbed timing = failure); reviewer checks the slice definition. |
| R9 | Default behavior change for existing callers | Low | High | Default workers stays 1 everywhere; parallelism is explicit opt-in (`--workers N` / `ALPHA_LABEL_CPU_WORKERS`); regression tests assert the workers=1 path is byte-identical to pre-campaign behavior. |
| R10 | CI redness from polars/duckdb-optional environments | Medium | Low | Synthetic fixtures + importorskip pattern consistent with existing scaleout tests; real-data checks skip cleanly with reason when the data root is absent. |

Standing rule: any gate failure stops the phase BLOCKED. Gates are never
weakened, tolerances never added, tests never narrowed to pass.
