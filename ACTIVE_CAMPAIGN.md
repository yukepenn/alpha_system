# Active Campaign

Project: `alpha_system`

* **Campaign ID:** `ALPHA_DATA_FOUNDATION_V1`
* **Campaign path:** `campaigns/ALPHA_DATA_FOUNDATION_V1`
* **Repo:** `alpha_system`
* **Repo path:** `~/projects/alpha_system`
* **Workflow:** `workflow2`
* **Mode:** Ralph-driven strict autonomous loop
* **Current run:** `not_started`
* **Current phase:** `DATA-P00` — Data Foundation Campaign Bootstrap
* **Last completed phase:** `none`
* **Status:** `not_started`
* **Project profile:** `trading_research` / `research` / `data_foundation`

This pointer lives only at the repository root. There is no campaign-local
`ACTIVE_CAMPAIGN.md`. Ralph updates this pointer through reviewed phase commits so the
tracked repo stays clean after Workflow 2 stops.

## What This Campaign Is

`ALPHA_DATA_FOUNDATION_V1` builds the **read-only, provenance-rich, quality-gated
historical futures data foundation** for ES/NQ/RTY research, using IBKR as the
*bootstrap historical data source only*. It is the real-market-data truth layer for
future AI alpha research. It is **not** an IBKR downloader, a broker integration, or an
alpha search.

It builds on three campaigns treated as complete: `ALPHA_SYSTEM_V1`,
`ASV1_RELEASE_HYGIENE`, and `ALPHA_RESEARCH_GOVERNANCE_MVP`. Governance now exists, so
real data may enter — but only as controlled, versioned, read-only research data.

## Model Routing Summary

* **Strategy / campaign reasoning:** ChatGPT Pro GPT-5.5 Thinking.
* **Specs / semantic review / done-check:** Claude Opus 4.8 xhigh.
* **Source-map / verifier / mechanical audit:** Claude Sonnet 4.6.
* **Implementation / repair / handoffs:** Codex GPT-5.5 high.
* **Workflow 2 driver / gates:** Ralph.

## Boundaries

In scope: read-only IBKR historical-data boundary, clientId safety, connection doctor,
contract economics, request manifests, pacing/chunking/retry/resume, raw local data
lake, parsed and canonical bars, sessions/calendars, roll metadata, continuous-vs-dated
provenance, data quality and coverage reports, dataset versions, partition metadata, and
local-only artifact discipline.

Out of scope (must never appear): order placement, account trading, paper trading, live
trading, broker execution, real-time signal loops, alpha/factor/label/strategy research,
ML/DL, L2/MBO replay, portfolio allocation, production execution, and any
alpha/profitability/tradability claim. IBKR clientId `101` and `102` are hard-forbidden;
the data-client namespace is `201–209` with default `201`.

## Campaign Files

* `campaigns/ALPHA_DATA_FOUNDATION_V1/GOAL.md`
* `campaigns/ALPHA_DATA_FOUNDATION_V1/PHASE_PLAN.md`
* `campaigns/ALPHA_DATA_FOUNDATION_V1/campaign.yaml`
* `campaigns/ALPHA_DATA_FOUNDATION_V1/ACCEPTANCE.md`
* `campaigns/ALPHA_DATA_FOUNDATION_V1/RISK_REGISTER.md`
* `campaigns/ALPHA_DATA_FOUNDATION_V1/RUNBOOK.md`

The full phase plan is in `PHASE_PLAN.md` (human-authoritative) and `campaign.yaml`
(machine-authoritative). This pointer intentionally does not duplicate them.

## External Authorization Summary

Most phases are YELLOW (local-only, no external provider call). Two phases are RED
because they touch the external IBKR API and write heavy local data:

* `DATA-P22` — Small Authorized IBKR Smoke Pull
* `DATA-P23` — Local Backfill Runbook and Resume Drill

RED phases require explicit local authorization (`ALPHA_DATA_PULL_AUTHORIZED`,
`ALPHA_ALLOW_EXTERNAL_IBKR`, and the harness scope variables
`PROJECT_OP_AUTHORIZED` / `PROJECT_OP_SCOPE` / `PROJECT_OP_EXPIRES`), never run in CI,
never auto-merge data artifacts, and never commit raw or canonical market data. RED here
means external/stateful/provider-facing — never trading.

## Acceptance Gate Summary

`campaign_bootstrap` (P00–P02), `ibkr_read_only_boundary` (P03–P04),
`futures_contract_master` (P05–P06), `request_and_storage` (P07–P10),
`provenance_sessions_rolls` (P11–P13),
`canonicalization_quality_versioning` (P14–P18), `secondary_data_tracks` (P19–P20),
`validation_and_authorized_smoke` (P21–P23), `closeout` (P24). Every phase belongs to
exactly one gate.

## Stop / Resume Rules

A `runs/<run_id>/STOP` file is an active stop request for that run. Ralph checks STOP
before provider calls, phase selection, Codex execution, validation, review, PR, CI,
merge gate, merge, done-check, and next-phase selection. Resume requires the STOP
condition to be removed or resolved; Ralph then resumes from recorded run state rather
than regenerating completed work. `runs/**` is local-only and must never be staged or
committed.

Broker/live trading, paper trading, order routing, real-time feeds, raw/canonical data
commits, heavy artifact commits, local DB commits, and alpha/tradability claims without
evidence remain out of scope for this campaign.
