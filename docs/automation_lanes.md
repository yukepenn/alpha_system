# Automation Lanes

Project profile: `trading_research`

Automation lane: `supervised`

Human review required: `true`

## Green

Low-risk automatic work. Generated policy enables auto PR and auto-merge, but real merge still requires passing CI, passing verdict/done-check, artifact policy success, branch protection validation, and authenticated `gh`.

## Yellow

Material engineering or research work. Claude review is required. `PASS_WITH_WARNINGS` can merge only when lane policy allows it and no critical findings are present.

## Red

External, destructive, production, live, or broker-adjacent work. Auto PR can be enabled, but real auto-merge is blocked unless all standard gates pass plus:

```bash
FRONTIER_RED_AUTHORIZED=1
FRONTIER_RED_SCOPE=<matching scope>
```

If `merge_policy.require_operation_scope_match` is true, the authorization scope must match the phase or configured lane scope.

## Global Controls

```bash
FRONTIER_CREATE_PR=0          # force PR dry-run/off
FRONTIER_CREATE_PR=1          # explicit PR creation override
FRONTIER_MERGE_DRY_RUN=1      # never execute gh pr merge
FRONTIER_DISABLE_AUTOMERGE=1  # emergency kill switch
```

STOP always stops before the next phase. BLOCKED, repair exhaustion, branch protection failure, and CI failure stop the run unless a lane explicitly allows the condition.
