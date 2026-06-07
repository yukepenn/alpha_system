# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
Workflow: `workflow2`
Run: `workflow2 complete`
Status: `complete (with warnings)` - all 31 phases done; the autonomous
`FUTCORE-P30` closeout recorded `BLOCKED` on a local-only `verify.py --all`
failure, resolved `COMPLETE_WITH_WARNINGS` by coordinator (CI green; failures
environmental/pre-existing). See
`campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT_COORDINATOR_RESOLUTION.md`.

Current phase: `none` - campaign complete
Last completed phase: `FUTCORE-P30` - Acceptance Audit and Closeout
Last completed status: `complete (with warnings) after coordinator resolution`
Completed phases: `31/31`

Campaign `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` remains the active pointer by
closeout convention. It is the first bounded, evidence-gated, cost-aware
ES/NQ/RTY futures alpha research pilot over the completed Data + Feature/Label
+ Research Runtime + Agent Factory stack. It drove one controlled research
loop:

```text
Hypothesis -> AlphaSpec -> StudySpec -> Runtime diagnostics
  -> cost / session / regime / no-lookahead review
  -> TrialLedger / RejectedIdeaLedger
  -> REJECT | INCONCLUSIVE | WATCH | CANDIDATE_RESEARCH
```

The final P28 promotion boundary is `4` `REJECT`, `6` `INCONCLUSIVE`, `0`
`WATCH`, and `0` `CANDIDATE_RESEARCH`. No FactorLibrary-ingestible survivor and
no Strategy Reference validation candidate is produced by this pilot.

Ralph owns authoritative validation, staged-set audit, review routing, verdict
parsing, repair routing, PR, CI, merge, and final done-check actions. This
pointer is updated by `FUTCORE-P30` only because the phase is `must_run_alone`
and coordinator-owned.

## Campaign Identity

- Campaign ID: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
- Campaign path: `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
- Repo: `alpha_system`
- Repo path: `~/projects/alpha_system`
- Workflow: `workflow2`
- Mode: Ralph-driven strict autonomous loop
- Project profile: `trading_research` / `research` / `core_alpha_pilot`
- Phase count: 31 phases (`FUTCORE-P00` ... `FUTCORE-P30`)
- Lane policy: Green/Yellow only; **no Red scope**
- Final verdict: `COMPLETE_WITH_WARNINGS` (coordinator resolution; autonomous
  `FUTCORE-P30` recorded `BLOCKED` on a local-only verifier failure)
- Coordinator resolution:
  `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT_COORDINATOR_RESOLUTION.md`
- Closeout audit:
  `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT.md`
- Next campaign handoff:
  `research/futures_core_alpha_pilot_v1/closeout/SUBSTRATE_SCALEOUT_V1_HANDOFF.md`

## Closeout Evidence

- Human-facing closeout:
  `docs/futures_core_alpha_pilot/CLOSEOUT.md`
- Research closeout summary:
  `research/futures_core_alpha_pilot_v1/closeout/README.md`
- Promotion decisions:
  `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`
- Downstream handoffs:
  `docs/futures_core_alpha_pilot/DOWNSTREAM_HANDOFFS.md`
- Commit-eligible P30 handoff:
  `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P30.md`

## Boundaries

The pilot consumed - and did not broaden - the runtime/governance/
agent_factory/research/experiments/backtest/data/core primitives. Diagnostics
ran only through the Research Runtime tool surface; inputs resolved through
registry tools and `resolve_dataset_version`; research-scale references stayed
registry-resolved and value-free in committed artifacts.

Out of scope remains unchanged: scaled/autonomous mining, continuous research
runner, FactorLibrary V1 promotion, Strategy Reference validation, AlphaBook,
strategy/backtest/portfolio products, ML/DL/RL, L1/L2 event-stream, portfolio
construction, paper/live/broker/order, external provider calls, raw/canonical/
feature/label/value or local-DB commits, and any profitability or tradability
claim.

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request; Ralph checks it before
phase selection, execution, checks, review, PR, CI, merge gate, merge,
done-check, and next-phase. Resume continues from recorded run state. In
parallel mode a wave builds concurrently in isolated worktrees but merges
serially; a STOP halts new phase selection and new merges.
