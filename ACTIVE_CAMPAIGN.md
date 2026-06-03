# Active Campaign

Project: `alpha_system`

* **Campaign ID:** `ALPHA_RESEARCH_GOVERNANCE_MVP`
* **Campaign path:** `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP`
* **Repo:** `alpha_system`
* **Repo path:** `~/projects/alpha_system`
* **Workflow:** `workflow2`
* **Mode:** Ralph-driven strict autonomous loop
* **Current run:** `not_started`
* **Current phase:** `ARGOV-P00` — Governance Campaign Bootstrap
* **Last completed phase:** `none`
* **Status:** `not_started`
* **Project profile:** `trading_research` / `research` hybrid

## Model Routing Summary

* **ChatGPT Pro GPT-5.5 Thinking** — strategy, roadmap, campaign reasoning, post-run reasoning.
* **Claude Opus 4.8 xhigh** — phase specs, semantic review, done-check.
* **Claude Sonnet 4.6** — source map, verifier, audit, mechanical inspection.
* **Codex GPT-5.5 high** — implementation, tests, repair, handoff.
* **Ralph** — Workflow 2 state machine, run control, phase transitions, gates.

## Boundaries

This campaign installs the admissibility and evidence-governance protocol for AI alpha
research. It does **not** search for alpha, ingest real data, connect to IBKR/brokers, or
touch paper/live trading, order routing, L2 replay, ML/DL, strategy optimization, or
portfolio allocation. No alpha/profitability/tradability/production-readiness claims.
Raw-data commits, heavy-artifact commits, local-DB commits, and `runs/**` commits remain
out of scope. Be aggressive about evidence governance; conservative about market scope.

## Campaign Files

* `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/GOAL.md`
* `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/PHASE_PLAN.md`
* `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/campaign.yaml`
* `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/ACCEPTANCE.md`
* `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/RISK_REGISTER.md`
* `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/RUNBOOK.md`

## Acceptance Gate Summary

Seven gates cover all 20 phases (`ARGOV-P00` … `ARGOV-P19`), each phase in exactly one
gate: `campaign_bootstrap`, `governance_contracts`, `ledger_and_evidence`,
`promotion_and_review`, `canary_and_validation`, `registry_and_tools`,
`end_to_end_and_closeout`. Final verdict is `COMPLETE`, `COMPLETE_WITH_WARNINGS`, or
`BLOCKED`.

## Stop / Resume Rules

A STOP file at `runs/<run_id>/STOP` is an active stop request; Ralph checks it before
provider calls, phase selection, execution, validation, review, PR, CI, merge, done-check,
and next-phase selection. Resume requires the STOP condition to be removed or resolved,
after which Ralph resumes from recorded run state rather than regenerating completed work.

Ralph updates this pointer through reviewed phase commits so the tracked repo stays clean
after Workflow 2 stops.

Note: Prior campaign `ALPHA_SYSTEM_V1` completed at `ASV1-P29` (30/30,
`PASS_WITH_WARNINGS`), followed by `ASV1_RELEASE_HYGIENE`. Both are treated as complete
baselines for this campaign.
