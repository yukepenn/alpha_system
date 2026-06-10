set shell := ["bash", "-uc"]

default:
    just --list

smoke:
    python tools/verify.py --smoke

lint:
    python tools/verify.py --lint

typecheck:
    python tools/verify.py --typecheck

test:
    python tools/verify.py --test

verify:
    python tools/verify.py --all

verify-ci:
    python tools/verify.py --ci

verify-canaries:
    python tools/hooks/canary_runner.py

audit:
    python tools/verify.py --boundaries

validate-artifacts:
    python tools/verify.py --artifacts

frontier-status:
    python tools/frontier/phase.py status

frontier-doctor:
    python tools/frontier/bootstrap.py doctor

# Authoritative "what campaign/phase are we on" from the live run state, with
# pointer-drift and runtime-contract checks. Source of truth for status.
status-doctor:
    python tools/frontier/status_doctor.py

# Regenerate docs/SYSTEM_MAP.md from the repo (anchors, packages, commands).
# CI fails on drift via tests/tools/test_system_map.py.
system-map:
    python tools/frontier/system_map.py

# One command an agent (or human) runs before a handoff/merge: live-status truth,
# fast checks, the canary gate, and the artifact/boundary guards over the diff.
agent-preflight:
    python tools/frontier/status_doctor.py
    python tools/verify.py --smoke
    python tools/hooks/canary_runner.py
    @bash -c 'files="$(git diff --name-only HEAD)"; if [ -n "$files" ]; then python tools/hooks/artifact_guard.py $files && python tools/hooks/boundary_guard.py $files; else echo "no changed files to guard"; fi'

# Is the deterministic floor intact? Quick smoke + canaries + status reconciliation.
doctor:
    python tools/frontier/status_doctor.py
    python tools/verify.py --smoke
    python tools/hooks/canary_runner.py

frontier-check-config:
    python tools/frontier/bootstrap.py check-config

frontier-new-phase:
    python tools/frontier/phase.py new --name "${FRONTIER_PHASE_NAME:-manual-phase}" --lane "${FRONTIER_LANE:-yellow}" --campaign "${FRONTIER_CAMPAIGN:-MANUAL}"

frontier-run-workflow1:
    python tools/frontier/phase.py workflow1 --phase "${FRONTIER_PHASE:?set FRONTIER_PHASE}"

frontier-review:
    python tools/frontier/phase.py review --phase "${FRONTIER_PHASE:?set FRONTIER_PHASE}"

frontier-merge:
    python tools/frontier/merge_gate.py --phase "${FRONTIER_PHASE:?set FRONTIER_PHASE}"

frontier-new-campaign:
    python tools/frontier/campaign.py new --campaign-id "${FRONTIER_CAMPAIGN:?set FRONTIER_CAMPAIGN}"

# ── Workflow 2 (Ralph) — autonomous campaign loop ────────────────────
# LIVE recipes (frontier-run / -resume / -next / -run-parallel / -overnight)
# arm REAL PR creation + auto-merge (FRONTIER_CREATE_PR=1,
# FRONTIER_ALLOW_AUTOMERGE=1, FRONTIER_MERGE_DRY_RUN=0): they merge to the
# protected branch once CI + the merge gate pass. The *-mock recipes are the
# safe local dry runs (no providers, no network, no merge). Omit the campaign id
# to use the ACTIVE_CAMPAIGN.md pointer (resume picks the latest run).

# Start (or continue) a campaign run; sequential or dag_wave per campaign.yaml.
frontier-run $campaign_id="":
    env -u FRONTIER_DISABLE_AUTOMERGE FRONTIER_CREATE_PR=1 FRONTIER_ALLOW_AUTOMERGE=1 FRONTIER_MERGE_DRY_RUN=0 python tools/frontier/ralph_driver.py run --campaign-id "$campaign_id" --provider-wired

# Auto-resume the latest non-completed run of the active (or given) campaign.
frontier-resume $campaign_id="":
    env -u FRONTIER_DISABLE_AUTOMERGE FRONTIER_CREATE_PR=1 FRONTIER_ALLOW_AUTOMERGE=1 FRONTIER_MERGE_DRY_RUN=0 python tools/frontier/ralph_driver.py resume --campaign-id "$campaign_id" --provider-wired

# Step a run forward by N phases (default 1).
frontier-next $campaign_id="" $max_phases="1":
    env -u FRONTIER_DISABLE_AUTOMERGE FRONTIER_CREATE_PR=1 FRONTIER_ALLOW_AUTOMERGE=1 FRONTIER_MERGE_DRY_RUN=0 python tools/frontier/ralph_driver.py resume --campaign-id "$campaign_id" --provider-wired --max-phases "$max_phases"

# DAG-wave parallel run: concurrent build in isolated worktrees, serial merge.
frontier-run-parallel $campaign_id="" $max_parallel="3":
    env -u FRONTIER_DISABLE_AUTOMERGE FRONTIER_CREATE_PR=1 FRONTIER_ALLOW_AUTOMERGE=1 FRONTIER_MERGE_DRY_RUN=0 python tools/frontier/ralph_driver.py run --campaign-id "$campaign_id" --provider-wired --parallel --max-parallel "$max_parallel"

# Read-only DAG plan: dependency graph, ready waves, conflicts, run-alone phases.
frontier-plan $campaign_id="":
    python tools/frontier/ralph_driver.py plan-dag --campaign-id "$campaign_id"

# Unattended long run (overnight); same live merge arming as frontier-run.
frontier-overnight $campaign_id="":
    env -u FRONTIER_DISABLE_AUTOMERGE FRONTIER_RUN_MODE=overnight FRONTIER_CREATE_PR=1 FRONTIER_ALLOW_AUTOMERGE=1 FRONTIER_MERGE_DRY_RUN=0 python tools/frontier/ralph_driver.py run --campaign-id "$campaign_id" --provider-wired

# ── Safe mock variants (no providers / network / merge) ──────────────
frontier-run-mock $campaign_id="G005_WORKFLOW2_TOY":
    FRONTIER_MOCK_PROVIDERS=1 python tools/frontier/ralph_driver.py run --campaign-id "$campaign_id" --provider-wired

frontier-next-mock $campaign_id="G005_WORKFLOW2_TOY" $max_phases="1":
    FRONTIER_MOCK_PROVIDERS=1 python tools/frontier/ralph_driver.py resume --campaign-id "$campaign_id" --provider-wired --max-phases "$max_phases"

frontier-run-parallel-mock $campaign_id="G005_WORKFLOW2_TOY" $max_parallel="3":
    FRONTIER_MOCK_PROVIDERS=1 python tools/frontier/ralph_driver.py run --campaign-id "$campaign_id" --provider-wired --parallel --max-parallel "$max_parallel"

# Deterministic local toy campaign (mock providers, no network).
frontier-run-workflow2-toy:
    FRONTIER_MOCK_PROVIDERS=1 python tools/frontier/ralph_driver.py run --campaign-id G005_WORKFLOW2_TOY --provider-wired

# ── Scaffold / power-user resume ─────────────────────────────────────
# Ledger-only scaffold: parse phases, no provider execution, no merge.
frontier-ledger $campaign_id="":
    python tools/frontier/ralph_driver.py run --campaign-id "$campaign_id" --ledger-only

# Resume a specific run directory by run id.
frontier-resume-run $run_id:
    python tools/frontier/ralph_driver.py resume --run-id "$run_id" --provider-wired

# Surgical stage-level resume of one phase (skips provider replay).
frontier-resume-stage $campaign_id $run_dir $phase_id $from_stage="merge_gate":
    FRONTIER_NO_PROVIDER_REPLAY=1 python tools/frontier/ralph_driver.py resume --campaign-id "$campaign_id" --run-dir "$run_dir" --phase-id "$phase_id" --from-stage "$from_stage" --provider-wired --no-provider-replay

# ── Run lifecycle helpers ────────────────────────────────────────────
frontier-stop $run_id:
    touch "runs/$run_id/STOP"

# Promote a run's per-phase review.md/verdict.json into the commit-eligible
# reviews/<campaign>/ tree at closeout. Copies only; stage + commit explicitly.
frontier-promote-reviews $run_id $campaign_id:
    python tools/frontier/promote_reviews.py --run-dir "runs/$run_id" --campaign-id "$campaign_id"

frontier-heartbeat $run_id:
    cat "runs/$run_id/heartbeat.json"

frontier-tail $run_id:
    tail -f "runs/$run_id/events.jsonl"

frontier-summary $run_id:
    cat "runs/$run_id/RUN_SUMMARY.md"

frontier-clean-worktrees:
    python tools/frontier/worktree_manager.py clean

frontier-list-worktrees:
    git worktree list

frontier-acceptance:
    python tools/frontier/acceptance.py
