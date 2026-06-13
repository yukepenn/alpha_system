# FUTSUB Kill-Shot Resume Handoff

Campaign closed by: `DISCOVERY_RIGOR_FLOOR_V1`
Paused run: `2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
Boundary: FUTSUB is stopped before P28; this phase does not touch the run.

This is coordinator-only. Do not execute these steps from a phase executor.
Do not inspect Track A metrics before Track-B registration is complete.

## RELOCK_V2 AMENDMENT (2026-06-13 — overrides V1-era narrative below)

This handoff predates `P110000_RELOCK_V2` (PR #405), which rotated all 10
StudySpec ids and forced a substrate re-materialization. The kill-shot runs the
**V2** content-addressed objects. The original step narrative (V1 Track-B
registration as the closing action; "4560-lock" audits) is SUPERSEDED:

- **Track-B (step 4)**: V2 pooled hypotheses are ALREADY registered pre-metric
  against the V2 anchor `sspec_f6cbd88caa0445f0f56d81fd` —
  `poolhyp_d3b3d986369b525618a1caa0` (cross_symbol) +
  `poolhyp_0755f59753552574a8092624` (cross_horizon),
  `registered_before_metrics: true` (live registry
  `~/alpha_data/alpha_system/futsub_killshot_track_b/`). The
  2026-06-12T05:06:10Z V1 records are immutable history, NOT execution contracts.
- **Audits (steps 6/7)**: use the V2 re-runs —
  `variant_reconciliation/FUTSUB_KILL_SHOT_variant_reconciliation_v2.md` (PASS)
  and `substrate_invariant/FUTSUB_KILL_SHOT_substrate_invariant_audit_v2.md`
  (GREEN; V2 corpus 4112 handles → 1168 distinct fver + 96 lver, all REGISTERED).
- **Caveat-carry (step 3)**: ADD the `bbo_tradability_spread_ticks` all-null
  substrate caveat (24 excluded bbo sub-configs in the Row 6 V2 calibration) to
  the operator context, alongside R-037 and BBO-proxy.
- **P28 surgery + run id**: use the FULL run id
  `2026-06-07T235209Z_...` (two stale same-suffix runs exist — DUPLICATE RUN-ID
  HAZARD). P28 BLOCKED→PENDING: reduce to the canonical 14-key set (matches
  P29–P33), DROP the 10 runtime keys (`branch`, `*_at`, `current_stage`,
  `last_completed_stage`, `completed_stages`, `suppress_active_pointer`,
  `wave_id`, `worktree_path`), keep `dependencies=["FUTSUB-P27"]`. STOP present,
  RUN.lock absent, heartbeat pid 998997 dead. Prune stale `futsub-p28` worktree
  (29fab84, ancestor of main).

## Ordered Resume Steps

1. Confirm the rigor-floor closeout has been merged and reviewed by Ralph.

   ```bash
   python tools/frontier/status_doctor.py
   test -f research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md
   test -f docs/discovery_rigor_floor/TRACK_B_PREREGISTRATION_TEMPLATE.md
   ```

2. Read the fail-closed readiness checklist and stop unless every
   `PENDING-coordinator` row is closed by the steps below.

   ```bash
   sed -n '1,220p' research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md
   ```

3. Carry the caveat register into the kill-shot operator context before STOP
   removal: R-037 `contract_id` caveat and BBO-proxy regime limits. These
   caveats travel with verdict interpretation and are not tradability claims.

4. Complete Track-B pre-registration before any Track A metric marker exists.
   Fill one cross-symbol and one cross-horizon payload from
   `docs/discovery_rigor_floor/TRACK_B_PREREGISTRATION_TEMPLATE.md` or the two
   draft JSON templates under `research/discovery_rigor_floor_v1/track_b/`.
   Register the filled payloads with the live schema:

   ```bash
   mkdir -p /home/yuke_zhang/alpha_data/alpha_system/futsub_killshot_track_b
   : > /home/yuke_zhang/alpha_data/alpha_system/futsub_killshot_track_b/pooled_hypotheses.jsonl
   : > /home/yuke_zhang/alpha_data/alpha_system/futsub_killshot_track_b/pooled_variant_ledger.jsonl
   alpha governance register-pooled-hypothesis /home/yuke_zhang/alpha_data/alpha_system/futsub_killshot_track_b/cross_symbol_pooled_hypothesis.json --registry-path /home/yuke_zhang/alpha_data/alpha_system/futsub_killshot_track_b/pooled_hypotheses.jsonl --variant-ledger-path /home/yuke_zhang/alpha_data/alpha_system/futsub_killshot_track_b/pooled_variant_ledger.jsonl --metrics-started-marker runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P28/track_a_metrics_started.json
   alpha governance register-pooled-hypothesis /home/yuke_zhang/alpha_data/alpha_system/futsub_killshot_track_b/cross_horizon_pooled_hypothesis.json --registry-path /home/yuke_zhang/alpha_data/alpha_system/futsub_killshot_track_b/pooled_hypotheses.jsonl --variant-ledger-path /home/yuke_zhang/alpha_data/alpha_system/futsub_killshot_track_b/pooled_variant_ledger.jsonl --metrics-started-marker runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P28/track_a_metrics_started.json
   alpha governance pooled-hypotheses list --registry-path /home/yuke_zhang/alpha_data/alpha_system/futsub_killshot_track_b/pooled_hypotheses.jsonl --json
   ```

   Required closeout: `track_b_minimum_satisfied()` is true for at least one
   registered `cross_symbol` and one registered `cross_horizon` record over the
   kill-shot study set. Draft templates alone do not satisfy this step.

5. Run the real-data surrogate calibration required by compass v4.4 section
   7.2 before FUTSUB-P28. The accepted report must declare K, state the
   false-pass bound (`zero passes in K bounds false-pass rate at about 3/K at
   95%`; `K>=60` for about 5%), use dependence-preserving nulls
   (session/trade-date-block shuffling minimum plus at least one block-bootstrap
   configuration), and be per-family. Any shuffled pass is a
   `LEAKAGE_BLOCKED` diagnosis first. The current RIGOR-P05 synthetic
   `K=2` report does not satisfy this step.

6. Emit the VariantLedger reconciliation audit over the six rerun candidates:
   every kill-shot study invocation must be matched to the intended
   `VariantLedgerRecord`, including the Track-B pooled entries from step 4.
   The artifact must be value-free: study ids, variant ids, ledger ids,
   matched/unmatched status, and issue codes only.

7. Emit the read-only substrate-invariant audit over the live registries. It
   must prove: no constant-valued flag columns, at least two session values per
   trading day, role-marker WARN documented, and zero locks referencing
   `DEPRECATED` records. The artifact must be value-free.

8. Re-check the readiness checklist against live evidence. Do not proceed while
   any item is `PENDING-coordinator`.

   ```bash
   python -m pytest tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py tests/unit/discovery_rigor_floor/test_rigor_p03_sealed_holdout_declaration.py tests/unit/discovery_rigor_floor/test_pooled_track_b_readiness.py -q
   python tools/hooks/canary_runner.py
   python tools/verify.py --smoke
   ```

9. Repoint `ACTIVE_CAMPAIGN.md` to FUTSUB. This is coordinator-owned; phase
   branches do not do it.

10. Remove the boundary STOP and stale `RUN.lock` only after PID-checking the
    lock owner. Do not delete a live lock.

    ```bash
    python - <<'PY'
from pathlib import Path
import json
run = Path("runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1")
lock = run / "RUN.lock"
if lock.exists():
    payload = json.loads(lock.read_text(encoding="utf-8"))
    print(payload)
else:
    print("no RUN.lock")
PY
    # Only after confirming the printed PID is not a live process:
    rm -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/RUN.lock
    rm runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP
    ```

11. Resume FUTSUB. P28 selection follows from the recorded run state.

    ```bash
    just frontier-resume-run 2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
    ```

## Non-Actions In RIGOR-P07

RIGOR-P07 does not repoint `ACTIVE_CAMPAIGN.md`, remove STOP, delete locks,
register Track B, run real-data surrogate calibration, inspect Track A metrics,
touch FUTSUB registries/values/worktrees, create PRs, merge, paper trade, live
trade, route orders, or deploy.
