# Feature/Label Foundation — Entry Contract

This document is the **entry contract** for the next campaign,
`ALPHA_FEATURE_LABEL_FOUNDATION_V1`. It states what that campaign may consume,
how, and under which rules. It points at existing code; it adds no implementation
and authorizes no alpha/feature/label work by itself. Authoritative field-level
contracts live in `src/alpha_system/data/foundation/` and
`src/alpha_system/governance/`; the campaign contract (once authored) governs scope.

## Inputs — accepted DatasetVersions only

Feature/Label code consumes **accepted, local-only DatasetVersions**, never raw
provider files. Resolve them through the registry:

- `alpha_system.data.foundation.version_registry.resolve_dataset_version(...)`
  (`version_registry.py:153`) returns a `DatasetVersion` from the local registry
  (`$ALPHA_DATA_ROOT/registry/datasets.sqlite`, local-only, uncommitted).

Available corpora (see `handoffs/ADF1_DATABENTO_ES_NQ_RTY_OHLCV_BBO_DEEP_HISTORY.md`
and `handoffs/...IBKR...`):

- **Databento (primary deep-history):** 27 DatasetVersions = 9 years (2018–2026) ×
  {sparse OHLCV-1m, dense research grid, BBO-1m} for ES/NQ/RTY continuous.
- **IBKR (broker-validation):** separate DatasetVersions, ~2 years of available depth.

Databento and IBKR DatasetVersions are kept **separate**; do not silently merge them.

## Allowed canonical records (provider-agnostic)

Consume only these canonical contracts — they carry no provider knowledge and are
reusable across providers:

- `CanonicalBarRecord` — `data/foundation/bars.py:1111`. Sparse OHLCV truth
  (a missing minute means **no trade**, not missing data).
- `CanonicalBBORecord` — `data/foundation/quotes.py:219`. Best bid/offer with
  `bid`, `ask`, `bid_size`, `ask_size`, and precomputed `mid`, `spread`
  (required), plus optional `spread_ticks`, `microprice`.
- `DenseGridBarRecord` — `data/foundation/grid.py:165`. A **derived dense research
  view** over sparse OHLCV: one row per expected session minute. No-trade minutes
  are emitted as previous-close placeholders with `has_trade=False`,
  `synthetic=True`, `fill_method` set, `volume=0`, and the `no_trade` quality
  flag. **Synthetic rows are not executable prices, tradability evidence, broker
  readiness, or live-data readiness.** Consumers must filter on
  `has_trade`/`synthetic` and treat synthetic rows accordingly.

## Required timestamp rules (no-lookahead)

Every canonical record enforces `available_ts >= bar_end_ts` at construction
(`bars.py:1165`, `quotes.py:287`, `grid.py:224`). Research must order usability by
**`available_ts`**, never by `event_ts`, `ingested_at`, or provider timestamps.
`ingested_at != available_ts`.

## Required governance gates

Feature/label/alpha work must go through the governance specs in
`src/alpha_system/governance/` — there is no compliant path that adds features,
labels, or alpha without one:

- `FeatureRequest` (`governance/feature_request.py`) — request/justify a feature.
- `LabelSpec` (`governance/label_spec.py`) — declare a label with availability semantics.
- `StudySpec` (`governance/study_spec.py`) — declare a study/experiment.
- `AlphaSpec` (`governance/alpha_spec.py`) — later, for candidate alpha.

Negative controls, leakage guards, the TrialLedger, and the PromotionGate remain
in force. Loading a DatasetVersion does not imply research approval.

## Partitions and locked-test contamination

`DatasetPartitionPlan` (`data/foundation/datasets.py:3000`) defines the canonical
partitions: `development` (2018–2022), `validation` (2023–2024),
`locked_test_candidate` (2025–2026), and an optional latest shadow. The
locked-test partition carries contamination metadata and **must not be consumed
without governance metadata** — enforced by
`require_governance_metadata_for_locked_partition_use(...)`
(`data/foundation/datasets.py:3162`).

## What Feature/Label MAY build

- Features/labels over `CanonicalBarRecord` / `DenseGridBarRecord` OHLCV and
  `CanonicalBBORecord` quotes, keyed by `available_ts`, behind a `FeatureRequest`/
  `LabelSpec`.
- Basic **tradability proxies from BBO** — spread, mid, microprice — using the
  existing `spread`/`mid`/`microprice` fields (diagnostics only; not tradability claims).
- Deterministic, reproducible, fixture-testable transforms with explicit availability semantics.

## What Feature/Label MAY NOT build

- No raw provider access (`.dbn`/`.zst`/parquet) from research code — canonical records only.
- No alpha search, strategy, portfolio, ML beyond an authorized scoped spec.
- No order/account/broker/paper/live/order-routing code or calls.
- No consumption of the locked-test partition without governance contamination metadata.
- No alpha/tradability/profitability/production claims; synthetic dense-grid rows are not evidence of any of these.

## Gaps to address in the campaign (not in this consolidation)

- There is no dedicated `cli/label.py` group yet; label-generation CLI surface is the
  Feature/Label campaign's responsibility.

All real data stays local-only under `ALPHA_DATA_ROOT`; nothing market-data is
committed. This contract is research-readiness only.
