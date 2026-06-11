# DISCOVERY_RIGOR_FLOOR_V1 — Runbook

## Preconditions

- FUTSUB run `2026-06-07T235209Z_...` is boundary-gated: STOP written
  automatically on FUTSUB-P27 merge (before P28, the kill-shot rerun). Its
  run dir, registries, values, and worktrees are DATA — untouched by this
  campaign. FUTSUB resumes only after RIGOR-P07 merges (coordinator).
- `ACTIVE_CAMPAIGN.md` points to this campaign (coordinator repoints at
  launch, NOT at bundle merge).
- Research venv `~/.venvs/alpha_system_research`;
  `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system`.

## Launch (coordinator, at the FUTSUB P27/P28 boundary)

```bash
python -c "import yaml; yaml.safe_load(open('campaigns/DISCOVERY_RIGOR_FLOOR_V1/campaign.yaml'))"
just frontier-plan DISCOVERY_RIGOR_FLOOR_V1
# repoint ACTIVE_CAMPAIGN.md to this campaign (coordinator-owned), then:
just frontier-run-parallel DISCOVERY_RIGOR_FLOOR_V1 2
```

Monitor exception-only (events high-signal filter + 3-signal stall check +
driver liveness). Codex service tier is `fast` (frontier.yaml); effort xhigh.

## STOP / resume

STOP file: `runs/<run_id>/STOP`. Failed/stopped resumes write a fresh STOP —
remove before resuming. Stale `RUN.lock`: PID-check (the `"pid"` field, not
timestamp digits) then delete. Stage-scoped resume uses stage name `ci`;
`FRONTIER_ALLOW_RESUME_HEAD_MISMATCH=1` only after manually diffing heads.
**After any platform-level merge mid-campaign, rebase or remove stale phase
worktrees before resuming (P19 lesson — resume REUSES existing worktrees).**

## Phase-specific notes

- RIGOR-P01/P02/P03 serialize (all touch promotion_gate.py).
- RIGOR-P05 surrogate runs: isolated `$ALPHA_DATA_ROOT/rigor_p05_surrogate_*`
  namespaces; production registries never the target; if local real data is
  absent, the synthetic calibration must still be CI-green and the real-data
  calibration becomes a coordinator runbook step before kill-shot resume.
- Historical Core Pilot dirs are forbidden_paths everywhere; annotations go
  to `research/futures_core_alpha_pilot_v1/verdict_annotations/` (new dir).

## After campaign completion (coordinator, NOT a phase)

1. Read `handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md`.
2. Complete Track-B pooled-hypothesis registration from the template —
   BEFORE inspecting any Track A metric.
3. Run real-data surrogate calibration if not done in-campaign; verify the
   zero-pass threshold holds (any pass → LEAKAGE_BLOCKED diagnosis first).
4. Verify KILL_SHOT_READINESS.md items against live evidence.
5. Repoint `ACTIVE_CAMPAIGN.md` to FUTSUB; `rm` the boundary STOP; clear
   stale RUN.lock; `just frontier-resume-run 2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
   (background + watchdog). P28 kill-shot follows.

## Hard rules (inherited)

Explicit staging only; never commit runs//values/SQLite/Parquet; no force
push; historical evidence append-only; gates fail-closed with bypass
canaries; research-only language — no alpha/profitability/tradability claims.
