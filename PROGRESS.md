# Progress

Project: `alpha_system`

## Current status

Latest (Workflow 1): `PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1` — **COMPLETE (PASS)**.
The two pre-pilot data-access blockers are landed and verified on real local data:
`FEATURE_LABEL_PARQUET_SINK_V1` (research-scale Parquet value sink/reader + registry
pointer metadata via `core/value_store.py`, dual JSONL+Parquet operator, JSONL preserved
as audit/small tier) and `SESSION_LABEL_GUARD_FIX_V1` (role-aware no-lookahead guard;
session-context features `rth_flag`/`eth_flag`/`session_minute` now resolve via declared
`SESSION_METADATA`, true labels still blocked). Real smoke materialized Parquet-backed
session features + `fwd_ret_5m`; runtime smoke PASS; Agent Factory preflight PREFLIGHT_PASS
on all four gates. `verify.py --all` = 2806 passed / 7 skipped; canaries PASS; artifact audit
clean (no values/registries/Parquet committed). See
`handoffs/PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1.md`. Next campaign (separately authorized):
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`.

Previously (Workflow 1): `POST_RUNTIME_FEATURE_LABEL_STORAGE_AND_SEED_PACKS_V1` —
storage architecture converged (ADR-0006: JSONL audit tier now, Parquet
research-scale deferred to `FEATURE_LABEL_PARQUET_SINK_V1`), a governed seed
FeaturePack/LabelPack operator + canonical-Parquet loader were added, and the
Research Runtime **real-data smoke now PASSES** against real Databento ES 2024
seed packs (local-only). See
`handoffs/POST_RUNTIME_FEATURE_LABEL_STORAGE_AND_SEED_PACKS_V1.md`. Next campaign:
`ALPHA_AGENT_FACTORY_MVP`. (Note: the lines below predate the
`ALPHA_FEATURE_LABEL_FOUNDATION_V1` and `ALPHA_RESEARCH_RUNTIME_MVP` campaigns,
which are complete; this log is not the authoritative ledger.)

Workflow 2 is paused after `ALPHA_DATA_FOUNDATION_V1` completed all 25 phases.
`ACTIVE_CAMPAIGN.md` points to current phase `none`.

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

ALPHA_FEATURE_LABEL_FOUNDATION_V1. Future feature/label work must consume only
accepted DatasetVersions under the governance and partition-contamination rules;
loading a DatasetVersion does not imply alpha value, profitability,
tradability, broker readiness, paper/live readiness, or production readiness.
