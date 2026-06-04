# Progress

Project: `alpha_system`

## Current status

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

## Next intended campaign

ALPHA_FEATURE_LABEL_FOUNDATION_V1. Future feature/label work must consume only
accepted DatasetVersions under the governance and partition-contamination rules;
loading a DatasetVersion does not imply alpha value, profitability,
tradability, broker readiness, paper/live readiness, or production readiness.
