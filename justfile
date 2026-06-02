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

frontier-run-campaign $campaign_id="G005_WORKFLOW2_TOY":
    python tools/frontier/ralph_driver.py run --campaign-id "$campaign_id" --provider-wired

frontier-run-next $campaign_id="G005_WORKFLOW2_TOY":
    env -u FRONTIER_DISABLE_AUTOMERGE FRONTIER_CREATE_PR=1 FRONTIER_ALLOW_AUTOMERGE=1 FRONTIER_MERGE_DRY_RUN=0 python tools/frontier/ralph_driver.py resume --campaign-id "$campaign_id" --provider-wired --max-phases 1

frontier-run-next-x $campaign_id="G005_WORKFLOW2_TOY" $max_phases="1":
    env -u FRONTIER_DISABLE_AUTOMERGE FRONTIER_CREATE_PR=1 FRONTIER_ALLOW_AUTOMERGE=1 FRONTIER_MERGE_DRY_RUN=0 python tools/frontier/ralph_driver.py resume --campaign-id "$campaign_id" --provider-wired --max-phases "$max_phases"

frontier-run-campaign-mock $campaign_id="G005_WORKFLOW2_TOY":
    FRONTIER_MOCK_PROVIDERS=1 python tools/frontier/ralph_driver.py run --campaign-id "$campaign_id" --provider-wired

frontier-run-next-mock $campaign_id="G005_WORKFLOW2_TOY":
    FRONTIER_MOCK_PROVIDERS=1 python tools/frontier/ralph_driver.py resume --campaign-id "$campaign_id" --provider-wired --max-phases 1

frontier-run-next-x-mock $campaign_id="G005_WORKFLOW2_TOY" $max_phases="1":
    FRONTIER_MOCK_PROVIDERS=1 python tools/frontier/ralph_driver.py resume --campaign-id "$campaign_id" --provider-wired --max-phases "$max_phases"

frontier-run-campaign-ledger $campaign_id="G005_WORKFLOW2_TOY":
    python tools/frontier/ralph_driver.py run --campaign-id "$campaign_id" --ledger-only

frontier-run-overnight $campaign_id="G005_WORKFLOW2_TOY":
    FRONTIER_RUN_MODE=overnight python tools/frontier/ralph_driver.py run --campaign-id "$campaign_id" --provider-wired

frontier-run-workflow2 $campaign_id="G005_WORKFLOW2_TOY":
    python tools/frontier/ralph_driver.py run --campaign-id "$campaign_id"

frontier-run-workflow2-toy:
    python tools/frontier/ralph_driver.py run --campaign-id G005_WORKFLOW2_TOY

frontier-run-workflow2-goal:
    python tools/frontier/ralph_driver.py run --goal "${FRONTIER_GOAL:?set FRONTIER_GOAL}" --lane "${FRONTIER_LANE:-yellow}"

frontier-resume $run_id:
    python tools/frontier/ralph_driver.py resume --run-id "$run_id" --provider-wired

frontier-resume-campaign $campaign_id $run_dir $phase_id $from_stage="merge_gate":
    FRONTIER_NO_PROVIDER_REPLAY=1 python tools/frontier/ralph_driver.py resume --campaign-id "$campaign_id" --run-dir "$run_dir" --phase-id "$phase_id" --from-stage "$from_stage" --provider-wired --no-provider-replay

frontier-stop $run_id:
    touch "runs/$run_id/STOP"

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
