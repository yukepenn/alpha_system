# FUTSUB Resume On Parallel Reference Handoff

Campaign: `REFERENCE_LABEL_PARALLEL_COMPUTE_V1`  
Target paused campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Target run id: `2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Target phase: `FUTSUB-P19`

## Measured Outcome

RLPC-P03 ended `NOT_RELEASED`. The bounded real benchmark at
`research/reference_label_parallel_compute_v1/benchmark/benchmark_summary.md`
measured the reference-worker path at 2.14x with requested workers=8 on the same
9-unit `cost_adjusted` ES/2024 grid, below the 3.0x release gate. Determinism
spot-checks passed at every worker count and the production registry row delta
was 0.

FUTSUB-P19 therefore resumes on the unchanged serial reference policy:
`--engine reference`, default workers=1. The opt-in parallel path exists
(`--workers N` / `ALPHA_LABEL_CPU_WORKERS`) but is not production policy for
FUTSUB.

The preserved pause evidence is
`handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/FUTSUB_PAUSE_STATE.md`. It records
the active STOP, preserved P19 worktree, preserved registry and value state, and
the coordinator pause estimate of approximately 134/216 full-window
`cost_adjusted` cells checkpointed. Treat those checkpoints as durable; only the
remaining approximately 82/216 full-window cells should recompute. The honest
serial expectation for the remainder is about 70 minutes; do not claim a
parallel speedup for this resume.

## Coordinator Resume Steps

These steps are for the coordinator after RLPC-P04 is reviewed and merged. This
handoff describes them; RLPC-P04 did not execute them.

1. Repoint the root campaign pointer to FUTSUB:

   ```bash
   printf '%s\n' 'ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1' > ACTIVE_CAMPAIGN.md
   ```

   This is coordinator-owned and must not be part of the RLPC-P04 phase diff.

2. Back up the paused FUTSUB run state before any state surgery:

   ```bash
   RUN_ID=2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
   RUN_DIR="runs/${RUN_ID}"
   TS="$(date -u +%Y%m%dT%H%M%SZ)"
   cp "${RUN_DIR}/state.json" "${RUN_DIR}/state.json.pre-rlpc-p19-reset.${TS}.bak"
   ```

3. Archive the old FUTSUB-P19 phase artifact directory so regenerated prompts
   and specs cannot reuse stale RLPC-era instructions:

   ```bash
   PHASE_DIR="${RUN_DIR}/phases/FUTSUB-P19"
   if [ -d "${PHASE_DIR}" ]; then
     mv "${PHASE_DIR}" "${RUN_DIR}/phases/FUTSUB-P19.pre-rlpc-reset.${TS}"
   fi
   ```

4. Reset the FUTSUB-P19 ledger entry in `${RUN_DIR}/state.json` to a clean
   pending phase. Use an audited JSON edit that preserves all other phases and
   run-level metadata, and for the `FUTSUB-P19` phase sets `status` to
   `PENDING` and removes stale in-flight fields such as `current_stage`,
   `completed_stages`, `last_completed_stage`, `status_reason`, `resume_stage`,
   `provider_limit`, `branch`, `worktree_path`, `commit_sha`, `pr`, `pr_url`,
   and `merged`. Then set run-level `status` to `RUNNING`,
   `current_phase_id` to `FUTSUB-P19`, `current_stage` to `spec`, and
   `stop_requested` to `false`.

   Log the rationale in `${RUN_DIR}/progress.txt`, for example:

   ```bash
   printf '%s\n' \
     "$(date -u +%Y-%m-%dT%H:%M:%SZ) Coordinator reset FUTSUB-P19 to PENDING after RLPC-P03 NOT_RELEASED; regenerated spec must inherit unchanged serial reference policy." \
     >> "${RUN_DIR}/progress.txt"
   ```

5. Remove the run STOP file only when ready to resume:

   ```bash
   rm "${RUN_DIR}/STOP"
   ```

6. Clear a stale run lock only after checking the PID is not live:

   ```bash
   if [ -f "${RUN_DIR}/RUN.lock" ]; then
     cat "${RUN_DIR}/RUN.lock"
     # Inspect the PID recorded in the lock. Remove the lock only if the PID is
     # absent, no longer running, or belongs to an unrelated dead process.
   fi
   ```

7. Resume FUTSUB as a coordinator background task with the watchdog re-armed:

   ```bash
   just frontier-resume-run 2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
   ```

   The regenerated FUTSUB-P19 spec should continue from checkpoint and registry
   truth. It should not delete preserved values, clear checkpoints, force a full
   recompute, or opt into reference workers >1 unless a later reviewed campaign
   changes policy.

## Resume Gotchas

- Stage-scoped resume uses the stage name `ci` when resuming CI gates.
- Use `FRONTIER_ALLOW_RESUME_HEAD_MISMATCH=1` only after manually confirming
  the branch head diff is exactly the reviewed files and no unreviewed files are
  present.
- Do not resume with `--no-provider-replay` for a pre-PR or pre-CI phase body;
  the deterministic no-provider path is for later gate stages.
- If the current FUTSUB state disagrees with this handoff, stop and inspect
  `${RUN_DIR}/state.json`, `${RUN_DIR}/progress.txt`, and the archived P19 phase
  directory before changing anything.
