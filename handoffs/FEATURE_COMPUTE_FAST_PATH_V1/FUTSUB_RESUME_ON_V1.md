# FUTSUB Resume On V1 Handoff

- Source campaign: `FEATURE_COMPUTE_FAST_PATH_V1`
- Target campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Status: coordinator handoff only
- Value policy: value-free instructions only. This document performs no state
  mutation, materialization, registry write, branch/worktree cleanup, campaign
  repoint, provider call, PR, merge, or review action.

## Decision

After `FEATURE_COMPUTE_FAST_PATH_V1` closes, resume FUTSUB on the V1 producer
path. The coordinator, not this phase branch, should repoint
`ACTIVE_CAMPAIGN.md` from `FEATURE_COMPUTE_FAST_PATH_V1` to
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`, reset the paused FUTSUB
integration phase, clear the STOP condition when ready, and let Ralph resume
from recorded FUTSUB state.

## FUTSUB Phases To Switch To V1

The following FUTSUB phases should materialize through the V1 producer path with
FCFP-P15 CPU worker parallelism:

| FUTSUB Phase | Scope | V1 Resume Direction |
| --- | --- | --- |
| `FUTSUB-P06` | Base OHLCV feature scaleout | Use the V1 `PackMaterializer` producer path, not the per-row reference engine. |
| `FUTSUB-P07` | Session / calendar / maintenance feature scaleout | Use V1 where the governed V1 pack covers the family; keep documented metadata deferrals with the reference oracle. |
| `FUTSUB-P08` | VWAP / session-auction feature scaleout | Use V1. |
| `FUTSUB-P09` | Regime / volatility / compression feature scaleout | Use V1. |
| `FUTSUB-P10` | Liquidity sweep / PA structure feature scaleout | Use V1. |
| `FUTSUB-P11` | Volume / activity feature scaleout | Use V1. |
| `FUTSUB-P12` | BBO tradability / top-book feature scaleout | Use V1. |
| `FUTSUB-P13` | Cross-market alignment feature scaleout | Use V1 as one ES/NQ/RTY aligned panel unit per year; do not split the panel across workers. |
| `FUTSUB-P14` | Feature registry integration, coverage audit, resolver smoke | Validate V1-produced feature output and fail closed on stale/unresolvable locks. |
| `FUTSUB-P16` | Governed fixed-horizon labels | Use V1 for the currently governed fixed-horizon labels. |
| `FUTSUB-P17` | Extended intraday labels | Use V1 only where governed label contracts exist; if contracts are missing, keep the governance gap explicit rather than minting new labels silently. |
| `FUTSUB-P18` | Session-close and maintenance-flat labels | Use V1 where governed label contracts and guards exist; otherwise record the gap. |
| `FUTSUB-P19` | Cost-adjusted labels | Use V1 where governed contracts exist and BBO/cost proxy semantics remain documented; no execution-truth claim. |
| `FUTSUB-P20` | Path labels | Use V1 only where governed label contracts and guards exist; no new label family should be invented by resume. |
| `FUTSUB-P22` | Label registry integration, coverage audit, resolver smoke | Validate V1-produced label output and fail closed on stale/unresolvable locks. |

V1 worker controls are:

- CLI: `--workers <N>`
- Environment fallback: `ALPHA_CPU_WORKERS=<N>`
- Stable default from FCFP-P15 benchmark evidence: requested workers `4`,
  effective workers capped by runnable unit count when lower.

Evidence:

- Default V1 producer integration:
  `research/feature_compute_fast_path_v1/integration/integration_report.md`
- Worker benchmark and stable worker count:
  `research/feature_compute_fast_path_v1/workers/worker_benchmark_summary.md`
- Benchmark parity and speed evidence:
  `research/feature_compute_fast_path_v1/benchmark/benchmark_summary.md`

## Reference Output Reconciliation

Use ADR-0007 and FCFP-P12 for all already-materialized FUTSUB reference outputs:

- Existing valid reference-engine outputs remain the parity reference.
- If V1 output is identical or within documented tolerance, keep the existing
  reference output, tag/record `producer_engine_id` provenance, and do not
  overwrite solely to change engines.
- If V1 output is beyond documented tolerance, treat it as a blocker. The only
  allowed branches are a V1 bug fix, an explicit `value_schema_version`
  boundary, or re-materialization through the official keystone path in a
  governed phase.
- Do not silently mix reference and V1 values within one logical value series.
- Producer provenance is registry metadata and must not enter
  `feature_version_id` or `label_version_id`.

Evidence:

- ADR-0007: `decisions/0007-producer-compute-fast-path.md`
- Reconciliation summary:
  `research/feature_compute_fast_path_v1/reconciliation/reconciliation_summary.md`
- Reconciliation docs:
  `docs/feature_compute_fast_path/ENGINE_PROVENANCE_RECONCILIATION.md`

## Reset And Resume Recipe

These are coordinator actions after FCFP closes. Do not perform them from a
phase executor worktree.

1. Confirm the target run directory from the actual live FUTSUB state, expected
   shape:

   ```text
   runs/<futsub_run_id>/state.json
   runs/<futsub_run_id>/STOP
   runs/<futsub_run_id>/phases/FUTSUB-P14/
   ```

2. Back up the local registries before any registry-touching FUTSUB phase:

   ```bash
   TS=$(date -u +%Y%m%dT%H%M%SZ)
   cp "$ALPHA_DATA_ROOT/registry/features.sqlite" "$ALPHA_DATA_ROOT/registry/features.sqlite.bak_futsub_v1_$TS"
   cp "$ALPHA_DATA_ROOT/registry/labels.sqlite" "$ALPHA_DATA_ROOT/registry/labels.sqlite.bak_futsub_v1_$TS"
   ```

3. In `runs/<futsub_run_id>/state.json`, preserve completed P00-P13 history and
   reset only the `FUTSUB-P14` phase dict to the clean provider-wired PENDING
   shape. The clean key-set is:

   ```json
   {
     "phase_id": "FUTSUB-P14",
     "name": "FeaturePack Registry Integration, Coverage Audit, and Resolver Smoke",
     "lane": "YELLOW",
     "dependencies": [
       "FUTSUB-P06",
       "FUTSUB-P07",
       "FUTSUB-P08",
       "FUTSUB-P09",
       "FUTSUB-P10",
       "FUTSUB-P11",
       "FUTSUB-P12",
       "FUTSUB-P13"
     ],
     "parallel_safe": false,
     "allowed_paths": [
       "research/futures_substrate_scaleout_v1/feature_packs/**",
       "docs/futures_substrate_scaleout/FEATURE_INTEGRATION.md",
       "tests/unit/futures_substrate_scaleout/features/test_feature_resolver_smoke.py",
       "handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P14.md",
       "reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P14/**"
     ],
     "forbidden_paths": "<carry exact forbidden_paths from campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/campaign.yaml>",
     "conflicts_with": [],
     "resource_class": ["materialization_registry"],
     "must_run_alone": true,
     "merge_group": "feature_integration",
     "status": "PENDING",
     "execution_mode": "provider_wired",
     "artifact_paths": {
       "spec_prompt": "runs/<futsub_run_id>/phases/FUTSUB-P14/spec_prompt.md",
       "spec": "runs/<futsub_run_id>/phases/FUTSUB-P14/spec.md",
       "executor_prompt": "runs/<futsub_run_id>/phases/FUTSUB-P14/executor_prompt.md",
       "executor_output": "runs/<futsub_run_id>/phases/FUTSUB-P14/executor_output.md",
       "validation": "runs/<futsub_run_id>/phases/FUTSUB-P14/validation.md",
       "review_prompt": "runs/<futsub_run_id>/phases/FUTSUB-P14/review_prompt.md",
       "review": "runs/<futsub_run_id>/phases/FUTSUB-P14/review.md",
       "verdict": "runs/<futsub_run_id>/phases/FUTSUB-P14/verdict.json",
       "done_check_prompt": "runs/<futsub_run_id>/phases/FUTSUB-P14/done_check_prompt.md",
       "done_check": "runs/<futsub_run_id>/phases/FUTSUB-P14/done_check.md",
       "done_check_json": "runs/<futsub_run_id>/phases/FUTSUB-P14/done_check.json",
       "handoff": "runs/<futsub_run_id>/phases/FUTSUB-P14/handoff.md",
       "git_phase": "runs/<futsub_run_id>/phases/FUTSUB-P14/git_phase.json",
       "branch_prepare": "runs/<futsub_run_id>/phases/FUTSUB-P14/branch_prepare.json",
       "branch": "runs/<futsub_run_id>/phases/FUTSUB-P14/branch.txt",
       "base_sha": "runs/<futsub_run_id>/phases/FUTSUB-P14/base_sha.txt",
       "commit_sha": "runs/<futsub_run_id>/phases/FUTSUB-P14/commit_sha.txt",
       "push_branch": "runs/<futsub_run_id>/phases/FUTSUB-P14/push_branch.json",
       "remote_branch": "runs/<futsub_run_id>/phases/FUTSUB-P14/remote_branch.json",
       "pr_create": "runs/<futsub_run_id>/phases/FUTSUB-P14/pr_create.json",
       "ci_status": "runs/<futsub_run_id>/phases/FUTSUB-P14/ci_status.json",
       "branch_protection": "runs/<futsub_run_id>/phases/FUTSUB-P14/branch_protection.json",
       "merge_gate": "runs/<futsub_run_id>/phases/FUTSUB-P14/merge_gate.json",
       "merge_result": "runs/<futsub_run_id>/phases/FUTSUB-P14/merge_result.json",
       "provider_limit": "runs/<futsub_run_id>/phases/FUTSUB-P14/provider_limit.json",
       "stage_checkpoints": "runs/<futsub_run_id>/phases/FUTSUB-P14/stage_checkpoints.jsonl"
     }
   }
   ```

   `runs/**` must remain local-only artifact state. If an older FUTSUB
   `campaign.yaml` or `state.json` contains `runs/**` in `allowed_paths`, treat
   that as stale harness data and do not stage it; run-local paths belong only
   under `artifact_paths`.

   Also reset top-level resume helpers for this phase if present:

   ```text
   current_phase_id = null
   current_micro_attempt = 0
   attempts["FUTSUB-P14"] = 0
   repair_attempts["FUTSUB-P14"] = 0
   stop_requested = false only after the STOP condition is resolved
   ```

4. Remove stale local-only P14 artifacts from the actual run:

   ```text
   runs/<futsub_run_id>/phases/FUTSUB-P14/
   ```

5. Remove the stale Frontier-owned P14 worktree and branch using the
   coordinator's normal safe worktree cleanup path. Do not remove
   non-Frontier-owned worktrees.

6. Clear `runs/<futsub_run_id>/STOP` only when the coordinator is ready for
   provider execution to continue.

7. Resume FUTSUB through Ralph from recorded state:

   ```bash
   just frontier-resume ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
   ```

Expected resume path:

```text
FUTSUB-P14 -> FUTSUB-P15 -> FUTSUB-P16 -> ... -> FUTSUB-P33
```

## Recommended Active Campaign Repoint

After this FCFP closeout is reviewed and accepted, the coordinator should repoint
`ACTIVE_CAMPAIGN.md` from:

```text
FEATURE_COMPUTE_FAST_PATH_V1
```

to:

```text
ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
```

This handoff records the recommendation only. It does not edit
`ACTIVE_CAMPAIGN.md`.

## Pre-Resume Checklist

- `research/feature_compute_fast_path_v1/closeout/CLOSEOUT.md` exists with a
  closeout verdict.
- V1 default producer path is confirmed by
  `research/feature_compute_fast_path_v1/integration/integration_report.md`.
- Worker parallelism is available through `--workers` and
  `ALPHA_CPU_WORKERS`; requested workers `4` is the fastest stable requested
  count in `research/feature_compute_fast_path_v1/workers/worker_benchmark_summary.md`.
- Registry backups are made before any registry-touching FUTSUB resume phase.
- `ALPHA_DATA_ROOT` points at the local data root and remains local-only.
- Artifact guardrails remain active: no values, Parquet payloads, SQLite
  registries, DB journals/WAL, provider responses, logs, caches, or `runs/**`
  artifacts are staged or committed.
- `ACTIVE_CAMPAIGN.md` repoint is performed only by the coordinator.
- Ralph, not Codex, owns review routing, verdict parsing, PR creation, CI wait,
  merge gate, merge, and done-checks.

## Boundaries

This handoff authorizes no live trading, paper trading, broker operation, order
routing, production deployment, external provider call, destructive cleanup,
alpha ideation, new AlphaSpec batch, parameter search, profitability claim, or
tradability claim. It preserves the reference engine as oracle, exact
`feature_version_id` / `label_version_id` identity, resolver fail-closed
semantics, and serial official registry writes.
