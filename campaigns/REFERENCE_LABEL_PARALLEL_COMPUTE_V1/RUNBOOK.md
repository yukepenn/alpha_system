# REFERENCE_LABEL_PARALLEL_COMPUTE_V1 — Runbook

## Preconditions

- FUTSUB run `2026-06-07T235209Z_...` is STOPPED (STOP file present, written
  2026-06-11T01:45Z); its checkpoints, registry rows, values, and P19 worktree
  are preserved and are DATA for this campaign — do not touch except where
  RLPC-P04 amends FUTSUB *contract files*.
- `ACTIVE_CAMPAIGN.md` points to this campaign (coordinator-owned).
- Research venv: `~/.venvs/alpha_system_research`; data root via
  `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system`.

## Launch (coordinator)

```bash
# validate the contract
python -c "import yaml; yaml.safe_load(open('campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/campaign.yaml'))"
just frontier-plan REFERENCE_LABEL_PARALLEL_COMPUTE_V1

# live run (serial chain; dag_wave for harness consistency)
just frontier-run-parallel REFERENCE_LABEL_PARALLEL_COMPUTE_V1 2
```

Monitor exception-only: watch `runs/<run_id>/events.jsonl` for
MERGE/BLOCKED/STOP/VERDICT, plus driver liveness and a stall watchdog.
Validation per phase: `python tools/verify.py --smoke`, targeted pytest dirs,
`python tools/hooks/canary_runner.py` (see phase `checks`).

## STOP / resume

STOP file: `runs/<run_id>/STOP`. Failed/stopped resumes write a fresh STOP —
remove it before resuming. Stale `RUN.lock`: PID-check, then delete. Resume:
`just frontier-resume-run <run_id>`; stage-scoped resume uses stage name `ci`
(not `ci_wait`); `FRONTIER_ALLOW_RESUME_HEAD_MISMATCH=1` only after manually
diffing the new head against the reviewed head.

## Benchmark phase (RLPC-P03) specifics

- Bounded slice only; the reference engine is NEVER timed on a full window.
- Isolated benchmark data-root namespace (pattern:
  `$ALPHA_DATA_ROOT/rlpc_p03_benchmark_<UTCSTAMP>/...`); production registry
  untouched.
- Sweep `--workers 1 2 4 8`; thread caps per worker
  (`POLARS_MAX_THREADS=2 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
  NUMEXPR_MAX_THREADS=2`).
- Commit only the value-free `benchmark_summary.md`.

## After campaign completion (coordinator, NOT a phase)

1. Read `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/FUTSUB_RESUME_ON_PARALLEL_REFERENCE.md`.
2. Repoint `ACTIVE_CAMPAIGN.md` back to
   `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`.
3. FUTSUB state surgery per the handoff: backup `state.json`, reset
   `FUTSUB-P19` to clean PENDING (archive the old phase dir), log rationale in
   `progress.txt`.
4. `rm runs/2026-06-07T235209Z_.../STOP`, clear stale `RUN.lock` if the PID is
   dead, then
   `just frontier-resume-run 2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
   as a coordinator background task with the watchdog re-armed.
5. P19 regenerates its spec under the amended ENGINE POLICY
   (`--engine reference --workers 8` if released) and recomputes only the
   remaining full-window cells (~82/216; checkpoints durable).

## Hard rules (inherited)

Explicit staging only; never commit `runs/**`/values/SQLite/Parquet; no force
push; reference engine is the oracle and is not edited in this campaign; no
alpha/profitability claims; lessons → project-skill at closeout if earned.
