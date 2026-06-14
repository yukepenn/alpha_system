# Progress

> **HISTORICAL — not live status.** This file lags the running campaign and may
> name a stale "next campaign". For the authoritative campaign/phase, run
> `just status-doctor` (or read `runs/<run_id>/state.json`). Entry point: `CRITICAL.md`.

Project: `alpha_system`

## Current status

`DIFFERENTIATED_KILLSHOT_V1` (DK) is **COMPLETE 6/6** (2026-06-14) with **0 survivors**
— the second clean kill-shot after `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
(FUTSUB). Track A (calendar/flow conditioning factors as main-effect context) is a
WELL-POWERED CLEAN NULL (4 `ZERO_PASS_MET` mechanisms, all REJECT). Track B (the
EXPLORATORY `context != trigger` conditional probe) is a SUBSTRATE-GAP, UNTESTED result
— it ran on a single-class (degenerate) 120m `target_before_stop` slice, so it is not a
null; it is a closable DATA_GAP. `roll_week` is an honest DATA_GAP.

Survivor gate = **0**. No promotion; no downstream factory module, no universe
expansion, no paid data (all trigger-gated behind the survivor gate). Next: post-DK
factory production-line adjudication → a narrow Track B substrate gap-closure (same
SetupSpec, existing `ES_2020_120m` barrier-resolving slice, no new mechanisms/sweep/
promotion) → a fresh narrow shot from a ranked MechanismCard queue. ES/NQ/RTY only.

Earlier completed since the rigor/substrate work: `DISCOVERY_RIGOR_FLOOR_V1` (rigor
floor 8/8 — VariantLedger, sealed-holdout, RANDOM_TARGET + planted-fake-alpha canary,
surrogate-FDR/`ZERO_PASS_MET`), `STRATEGY_SHAPED_RESEARCH_LANE_V0` (SSRL 5/5 — the
EXPLORATORY expression lane), and `SHIP_REFIT_V1`. The deep history below predates these
and is not the authoritative ledger; for live status run `status-doctor`.

## Completed: ALPHA_SYSTEM_V1

ALPHA_SYSTEM_V1 completed executor coverage through ASV1-P29 with
recommendation `COMPLETE_WITH_WARNINGS`. This was correctness validation only
on deterministic fixtures. No real market data was validated, and no alpha,
profitability, robustness, tradability, paper/live, broker, or deployment claim
was made.

## Completed: ASV1_RELEASE_HYGIENE

ASV1_RELEASE_HYGIENE was a post-closeout cleanup pass, not a new alpha research
phase. It covered docs currency, dev tooling and verification gates,
artifact/git guards, golden tests for existing conservative reference
semantics, and preparation for later campaigns.

## Completed: ALPHA_RESEARCH_GOVERNANCE_MVP

ALPHA_RESEARCH_GOVERNANCE_MVP installed the AlphaSpec, StudySpec,
EvidenceBundle, TrialLedger, PromotionGate, RejectedIdeaLedger, governance CLI,
and negative-control canaries. The closeout verdict is
`COMPLETE_WITH_WARNINGS`; it did not start alpha search or authorize live,
paper, broker, or production behavior.

## Completed: ALPHA_DATA_FOUNDATION_V1

ALPHA_DATA_FOUNDATION_V1 completed `DATA-P00` through `DATA-P24` (`25/25`) as a
read-only, quality-gated historical data foundation. It added the
DatasetVersion registry path, canonical timestamp and partition contracts,
synthetic end-to-end dry run, read-only IBKR connector/backfill/materialize
entry points, and local-only artifact rules.

Post-closeout Task 1A added the read-only IBKR connector and smoke path (PR
#96). Task 1B added resumable backfill/materialize machinery and registered the
first real local-only DatasetVersion,
`dsv_ibkr_es_nq_rty_eth_20260603_v1`, for ES/NQ/RTY ETH data (PR #97). No raw
data, registry DB, cache, or generated market-data artifact is committed.

A subsequent post-closeout track added Databento as the primary deep-history
research source, kept separate from the IBKR broker-validation source. Phase B
(PR #107) pulled the full GLBX.MDP3 ES/NQ/RTY continuous OHLCV-1m + BBO-1m
history (2018-01-01 → 2026-06-01), canonicalized it into sparse provider truth
plus a derived dense research grid, applied quality/coverage gates, and
registered 27 local-only DatasetVersions across development, validation, and
locked-test partitions. All raw/canonical/registry data stays local-only under
`ALPHA_DATA_ROOT`; nothing is committed. This is research-readiness only and
implies no alpha, tradability, profitability, paper/live, broker, or production
claim. See `handoffs/ALPHA_DATA_FOUNDATION_V1/ADF1_DATABENTO_ES_NQ_RTY_OHLCV_BBO_DEEP_HISTORY.md`.

## Next intended campaign

Post-DK **factory production-line adjudication** (`ALPHA_FACTORY_PRODUCTION_LINE_ADJUDICATION_V1`)
to charter the generic Idea → MechanismCard → testability gate → diagnostics → verdict
→ rejected/survivor-memory line, then a narrow Track B substrate gap-closure on the
existing `ES_2020_120m` slice. No broad mining, FactorLibrary, AlphaBook, sandbox, PA
grammar, universe expansion, or paid data until the survivor gate (currently 0) earns
them. Loading any DatasetVersion implies no alpha/tradability/profitability claim.
