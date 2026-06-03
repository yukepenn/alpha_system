# ALPHA_DATA_FOUNDATION_V1 Campaign Goal

## Campaign Identity

**ALPHA_DATA_FOUNDATION_V1 — The Read-Only Real-Market-Data Truth Layer for AI Alpha Research**

* **Campaign ID:** `ALPHA_DATA_FOUNDATION_V1`
* **Campaign path:** `campaigns/ALPHA_DATA_FOUNDATION_V1`
* **Repo name:** `alpha_system`
* **Repo path:** `~/projects/alpha_system`
* **Host environment:** Windows host
* **Primary runtime:** WSL2 Ubuntu
* **Required active filesystem location:** WSL2 Linux filesystem
* **Forbidden active worktree locations:** `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, temporary directories
* **Project profile:** `trading_research` / `research` / `data_foundation`
* **Campaign execution mode:** Frontier Harness Generic v3.0 Workflow 2
* **Campaign driver:** Ralph strict autonomous loop
* **Primary executor:** Codex GPT-5.5 high
* **Primary semantic reviewer:** Claude Opus 4.8 xhigh
* **Verifier / source-map / audit support:** Claude Sonnet 4.6
* **Strategic campaign reasoning:** ChatGPT Pro GPT-5.5 Thinking

## Mission

Build the **read-only, provenance-rich, quality-gated historical futures data
foundation** for ES/NQ/RTY research, using IBKR as the *bootstrap historical data source
only*.

This campaign creates the **real-market-data truth layer** that future AI alpha research
will stand on. It bridges synthetic/tiny fixtures to real historical ES/NQ/RTY futures
data. It does not search for alpha, does not research factors or labels, does not run
strategies, and does not touch broker, order, account, paper, or live trading.

One sentence captures the posture:

```text
Real data is dangerous until it is versioned, quality-checked, provenance-labeled, and local-only.
```

## Why This Campaign Exists

`ALPHA_SYSTEM_V1` made the system able to run. `ASV1_RELEASE_HYGIENE` made the V1
baseline clean and reviewable. `ALPHA_RESEARCH_GOVERNANCE_MVP` decided what research
results are allowed to be believed. The strategic ordering is precise:

```text
ALPHA_SYSTEM_V1               made the system able to run.
ASV1_RELEASE_HYGIENE          made the V1 release baseline clean.
ALPHA_RESEARCH_GOVERNANCE_MVP decided what research results are allowed to be believed.
ALPHA_DATA_FOUNDATION_V1      lets real market truth enter — controlled, versioned, read-only.
```

The dependency is mutual and deliberate:

```text
Without Governance:        real data creates overfit risk.
Without Data Foundation:   governance has no real market truth to govern.
Therefore:                 Governance first, Data Foundation second, real alpha search later.
```

`alpha_system` is becoming an **AI Alpha Research Factory**, not merely a backtester and
not merely a strategy repository. The long-term north star is an AI-driven,
evidence-gated, cost-aware intraday alpha factory that continuously discovers, validates,
combines, monitors, deweights, and retires alphas under strict point-in-time and
reproducibility rules. In that factory:

* AI generates research throughput.
* `alpha_system` owns evidence and truth.
* Ralph / Workflow 2 owns process and gates.
* Claude reviews semantics and runs done-checks.
* Codex implements scoped phase specs.
* The human owns direction and risk/capital judgment.

Governance now exists. Before real alpha search, an Agent Factory, a Feature/Label
Foundation, Futures Core Alpha, an AlphaBook, ML, L1/L2 work, paper/live trading, or any
broker integration, the system needs a real data foundation that admits real data **only
as controlled, versioned, read-only research data** with an auditable provenance trail:

```text
which data source
which request
which contract
which session
which roll
which timestamp semantics
which quality status
which dataset version
which partition
which provenance
which local artifact policy
```

## Baseline from ALPHA_SYSTEM_V1, ASV1_RELEASE_HYGIENE, and ALPHA_RESEARCH_GOVERNANCE_MVP

All three prior campaigns are treated as **complete**. The current baseline provides:

* a clean local-first research harness foundation;
* domain contracts, a factor-registry foundation, a label-store foundation, research
  diagnostics, and a reference 1-minute backtest execution truth;
* artifact policy and explicit-staging discipline, review bundles, source maps, and
  deterministic fixture validation;
* release hygiene with validation gates and reference semantics;
* the admissibility / evidence-governance protocol: `AlphaSpec`, `HypothesisCard`,
  `FeatureRequest`, `LabelSpec`, `StudySpec`, `TrialLedger`, `EvidenceBundle`,
  `RejectedIdeaLedger`, `PromotionGate`, `ReviewerVerdict`, negative-control canaries,
  and the hard rules *no-code-before-spec*, *no-candidate-without-evidence*, and
  *no-promotion-without-ledger*.

That baseline deliberately did **not** provide real ES/NQ/RTY historical data, a futures
instrument master, contract-details snapshots, a roll calendar, an RTH/ETH session model,
canonical real 1-minute bars, an IBKR request manifest, a pacing/chunk/resume protocol, a
dataset-version registry for real data, coverage reports, data-quality reports, or
real-data partition metadata. This campaign supplies exactly that missing layer.

## What This Campaign Builds

Across 25 Workflow 2 phases (`DATA-P00` … `DATA-P24`) the campaign defines, designs, and
(where local-only and authorized) implements:

* a read-only IBKR historical-data boundary and an order-method kill switch;
* an IBKR clientId safety policy (hard-block `101`/`102`; data namespace `201–209`);
* a connection doctor for Windows/WSL2 reachability diagnostics;
* a futures instrument master and contract economics for ES/NQ/RTY and MES/MNQ/M2K;
* contract-details snapshots and contract discovery;
* historical request specs and a request manifest;
* a pacing / chunking / retry / resume ledger and a provider-error ledger;
* a raw local data-lake layout with immutable, content-addressed provider responses;
* parsed (bronze) provider bars and canonical (silver) 1-minute bars;
* session templates, a trading calendar, a roll policy, and a roll calendar;
* continuous-vs-dated-vs-stitched-vs-adjusted provenance separation;
* data-quality reports and coverage reports that fail closed on silent gaps or timestamp defects;
* a dataset-version registry linking manifest, code, config, and quality hashes;
* dataset partition metadata (development / validation / locked-test candidates);
* a separate micro-batch policy for MES/MNQ/M2K;
* an optional BID_ASK / spread-proxy pilot track;
* synthetic IBKR fixture tests, a small authorized smoke pull, a backfill runbook with a
  resume drill, and an end-to-end dry-run and closeout.

## What This Campaign Does Not Build

This campaign must not implement or require any of the following:

* no alpha discovery, factor research, label research, or strategy research;
* no Feature/Label Foundation, Agent Factory, Futures Core Alpha, or AlphaBook;
* no order placement, account trading, position polling, broker execution, or order routing;
* no paper trading, live trading, or real-time signal generation;
* no L1 live quote stream, L2 depth, MBO, order-book replay, or execution simulator;
* no tick data, ML/DL, or portfolio allocation;
* no production execution adapter;
* no profitability, tradability, alpha-validity, or production-readiness claims.

## IBKR Read-Only Boundary

IBKR is scoped strictly as a **bootstrap historical data source**, never as a broker or
execution venue. The TWS API exposes both market/historical data and order/account
surfaces; this campaign exposes only the historical/read-only surface and must block or
avoid every order/account/trading API. The data module must not be able to place an
order, query positions, or touch account-trading paths.

* Historical data only. No orders, no account trading, no positions.
* No paper trading. No live trading. No real-time signal loop.
* `read_only_mode = true` is the default; a connection doctor must run before any pull.
* External provider calls require explicit RED-lane authorization and never run in CI.

## User-Specific clientId Safety Policy

The existing local pattern may look like `ib.connect("127.0.0.1", 4002, clientId=101)`.
For this campaign that is forbidden:

```text
clientId 101: forbidden  (reserved for paper account / paperaccountclient separation)
clientId 102: forbidden  (reserved for paper account / paperaccountclient separation)

DATA_HIST_CLIENT_ID_BASE = 201
allowed data client IDs:   201-209
default clientId:          201
optional worker IDs:       201 = ES, 202 = NQ, 203 = RTY (when multiple connections are used)
hard fail:                 clientId in {101, 102}
```

This must be a **fail-closed validation**, not a warning. The connector design must
explicitly log and validate clientId; clientId uniqueness is not optional.

Default connection profile: `host 127.0.0.1`, `port 4002`, `clientId 201`. Because the
host runs Windows and the runtime is WSL2, a connection doctor must detect and report
host/port reachability failures rather than silently retrying into the wrong host. The
required config/env semantics (names may be adapted to repo conventions) are:
`ALPHA_IBKR_HOST`, `ALPHA_IBKR_PORT`, `ALPHA_IBKR_CLIENT_ID`,
`ALPHA_IBKR_READ_ONLY_MODE`, `ALPHA_DATA_ROOT`, `ALPHA_DATA_PULL_AUTHORIZED`,
`ALPHA_ALLOW_EXTERNAL_IBKR`, `ALPHA_ALLOW_RAW_LOCAL_WRITE`.

## Futures Universe

```text
Primary mini roots:    ES, NQ, RTY
Secondary micro roots: MES, MNQ, M2K
Main batch:            ES, NQ, RTY
Micro batch:           MES, MNQ, M2K   (separate batch; never mixed with the mini batch)
max_concurrent_roots:  3
```

### Contract Economics Anchors (to verify during implementation)

These are economic anchors to verify against official sources and repo tests during the
relevant phase; they are not production-certified until verified. `tick_value =
tick_size × point_value` when applicable.

| Root | Name | Point value | Tick size | Tick value |
| ---- | ---- | ----------- | --------- | ---------- |
| ES  | E-mini S&P 500       | $50 × S&P 500 Index    | 0.25 index pts | $12.50 |
| NQ  | E-mini Nasdaq-100    | $20 × Nasdaq-100 Index | 0.25 index pts | $5.00  |
| RTY | E-mini Russell 2000  | $50 × Russell 2000     | 0.10 index pts | $5.00  |
| MES | Micro E-mini S&P 500 | $5 × S&P 500 Index     | 0.25 index pts | $1.25  |
| MNQ | Micro E-mini Nasdaq-100 | $2 × Nasdaq-100 Index | 0.25 index pts | $0.50 |
| M2K | Micro E-mini Russell 2000 | $5 × Russell 2000 | 0.10 index pts | $0.50  |

## Historical Window Strategy

The canonical MVP default is the modern common ES/NQ/RTY panel:

```text
Primary common panel:
  symbols:    ES, NQ, RTY
  start_date: 2018-01-01
  end_date:   present / as_of_run
  bar_size:   1 min
  what_to_show: TRADES
  session handling: store ETH-capable canonical bars; derive RTH views from session templates
```

`2018-01-01` is the default because it gives a clean modern common panel that avoids the
2017 RTY-to-CME transition as the primary panel while still covering multiple regimes:
the 2018 volatility shock, 2019 calm / pre-COVID baseline, the 2020 COVID crash and
rebound, the 2021 liquidity/bull regime, the 2022 inflation/rate-shock/bear regime, the
2023 rates/AI transition, and the 2024–2026 high-rate/AI/liquidity regimes.

Optional, clearly-labeled secondary panels:

* **Optional ES/NQ long panel** (`2015-01-01 →`, ES/NQ): longer-regime data-QA and
  baselines; provider-continuous if needed; not mixed with the common panel without
  marking missing RTY-era differences.
* **RTY transition QA panel** (`2017-07-10 → 2017-12-31`, RTY): coverage/transition QA
  only; not the primary panel.
* **Contract-truth panel** (ES/NQ/RTY dated FUT over a rolling available expired window):
  contract-master and roll validation, provider-continuous comparison; no dated-contract
  truth claim beyond discovered availability.
* **Micro batch** (`2020-01-01 or earliest clean`, MES/MNQ/M2K): execution-sizing
  compatibility and mini/micro parity checks; separate batch; not a primary alpha source
  in V1.

The campaign must not promise full dated-contract history back to 2015 or 2018 through
IBKR. Dated-contract truth is strongest for current contracts, recent expired contracts
available from IBKR, and roll-validation windows; availability must be discovered and
logged, not assumed.

## Data Architecture Layers

```text
Raw Local Data Lake (immutable):
  immutable provider responses, local-only, never committed, content-addressed or versioned,
  request-manifest linked.

Bronze / parsed layer:
  parsed IBKR bars with provider metadata; still provider-shaped.

Silver / canonical layer:
  canonical 1m bars, normalized symbols, session labels, event_ts / available_ts,
  contract references, and data-quality flags.

DatasetVersion registry:
  reproducible canonical dataset reference (source, universe, bar size, what_to_show,
  start/end, contract universe, roll policy, manifest/code/config/quality hashes).
```

Continuous (`CONTFUT`) history is labeled `provider_continuous`, `non_orderable`,
`not_dated_contract_truth`, and `research_diagnostics_only` until provenance is clear. The
campaign keeps provider-continuous, dated-contract, canonical-stitched, roll-adjusted, and
non-adjusted series explicitly separate.

## Timestamp Semantics

The campaign aligns with the V1 no-lookahead semantics. Every canonical bar must
distinguish: `event_ts`, `bar_start_ts`, `bar_end_ts`, `available_ts`, `provider_ts` (if
available), `ingested_at`, `source_request_id`, and `data_version`. For historical
1-minute bars, `event_ts` / `bar_end_ts` must be clear; `available_ts` must represent when
the completed bar would have been usable in research/backtest semantics (not merely when
the historical API returned it); and `ingested_at` is separate from `available_ts`. No
factor or label research is possible on raw provider timestamps without canonical
timestamp validation.

## Required Data Foundation Objects

These objects organize the phases. The campaign contract does not implement all objects
immediately; field-level requirements are specified in `campaign.yaml`
(`data_foundation_objects`) and audited in `ACCEPTANCE.md`.

`DataSourceProfile`, `IBKRConnectionProfile`, `IBKRClientIdPolicy`,
`HistoricalRequestSpec`, `HistoricalRequestManifest`, `HistoricalChunkRecord`,
`HistoricalPullLedger`, `ProviderErrorRecord`, `RawDataObject`, `ParsedBarRecord`,
`CanonicalBarRecord`, `InstrumentMasterRecord`, `FuturesContractRecord`,
`ContractDetailsSnapshot`, `SessionTemplate`, `TradingCalendarRecord`, `RollPolicy`,
`RollCalendarRecord`, `DatasetVersion`, `DataQualityReport`, `CoverageReport`,
`DataIngestionRunRecord`, `LocalDataRootPolicy`, `DataAccessMode`,
`ContinuousFuturesSeriesRecord`, `DatedFuturesSeriesRecord`, `MicroBatchPolicy`,
`SymbolBatchPlan`, `RequestPacingPolicy`, `TimestampSemanticsPolicy`,
`DatasetPartitionPlan`.

## Data Lifecycle State Model Summary

```text
NOT_REQUESTED
  -> REQUEST_PLANNED       (HistoricalRequestSpec)
  -> REQUEST_AUTHORIZED    (manifest + clientId validation + local data-root validation)
  -> REQUEST_SUBMITTED     (RED-lane authorization for external IBKR calls)
  -> PARTIAL_RAW           (at least one completed chunk)
  -> RAW_COMPLETE          (all chunks accounted for or explicit incomplete ledger)
  -> PARSED                (parser success + raw object refs)
  -> CANONICALIZED         (timestamp/session/contract normalization)
  -> QUALITY_CHECKED       (quality report)
  -> VERSIONED             (coverage report + manifest/code/config hashes)
  -> READY_FOR_RESEARCH    (dataset version + non-blocking quality + coverage + artifact pass)

Any state -> REJECTED      (reason + error records)
Any state -> QUARANTINED   (uncertain provenance, gaps, session/roll/timestamp defects)
```

The states `READY_FOR_TRADING`, `LIVE_FEED_READY`, `BROKER_ENABLED`, `ALPHA_VALIDATED`,
and `PROFITABLE` are **prohibited MVP states**. They may be named only as future,
non-MVP concepts and must not be reachable by any transition implemented in this campaign.

Blocks: a missing manifest blocks any provider pull; clientId `101`/`102` blocks
connection; a missing pacing guard blocks a pull; a missing local-data-root policy blocks
raw writes; a missing `available_ts` blocks canonicalization; silent gaps block
versioning; a raw-data commit blocks merge; an order-API surface blocks merge; and any
alpha/tradability claim blocks merge.

## Artifact Policy

Raw and canonical real market data are **local-only** and must never be committed.
Campaign files may describe paths but must not commit data. The suggested data root is
outside the repo (e.g. `~/alpha_data/alpha_system`) or configured via `ALPHA_DATA_ROOT`.

Never commit: `data/raw/**`, `data/canonical/**`, `data/factors/**`, `data/labels/**`,
`data/cache/**`, `metadata/*.sqlite`/`*.db`/`*.db-journal`/`*.wal`, `runs/**`,
`*.parquet`/`*.feather`/`*.arrow`, `*.db`/`*.sqlite`, `*.log`, full historical reports,
provider responses, account info, IBKR logs, and credentials.

Commit-eligible: source code, configs, schemas, docs, tests, tiny synthetic fixtures
(`tests/fixtures/**`), handoffs, reviews, curated summaries, and sample manifests built
from fake/synthetic data only.

## Hard Constraints

* IBKR is read-only historical data; never broker, order, account, paper, or live.
* clientId `101`/`102` fail closed; data namespace is `201–209`, default `201`.
* No provider pull without a request manifest, pacing guard, and resume ledger.
* No silent gaps; coverage and quality reports fail closed.
* Continuous futures are never treated as dated-contract truth.
* Canonical bars must carry `available_ts`; `event_ts` / `bar_end_ts` / `available_ts`
  are never conflated.
* No real-data pull runs in CI; external pulls require RED-lane authorization.
* No raw/heavy/local-DB artifacts committed; explicit staging only; no `git add .` /
  `git add -A`; no force push.
* No alpha/profitability/tradability/production-readiness claims anywhere.

## Success Definition

`ALPHA_DATA_FOUNDATION_V1` succeeds when:

1. The repo can define and validate a read-only IBKR historical data profile.
2. clientId `101` and `102` are hard-blocked and the data namespace `201–209` is enforced.
3. ES/NQ/RTY mini batch and MES/MNQ/M2K micro batch are explicitly separated.
4. Historical requests are manifest-driven, chunked, paced, resumable, and auditable.
5. Raw provider data, parsed bars, canonical bars, and dataset versions are separate layers.
6. Futures contract economics, sessions, rolls, and provenance are first-class records.
7. Canonical bars preserve `event_ts` / `bar_start_ts` / `bar_end_ts` / `available_ts` / `ingested_at`.
8. Data-quality and coverage reports fail closed on silent gaps or timestamp defects.
9. Real-data artifacts are local-only and never committed.
10. No alpha, profitability, tradability, broker, paper, or live claim is introduced.

## Out-of-Scope Claims

This campaign must not claim that any alpha is validated, that any strategy is profitable,
tradable, robust, production-ready, paper-ready, live-ready, or broker-ready, that real
data is fully pulled, or that data quality is accepted (except when describing future
acceptance criteria). It produces a governed data-admissibility foundation only.

## Relationship to Next Campaigns

`ALPHA_DATA_FOUNDATION_V1` is the truth layer that later campaigns consume. Once it exists
and is reviewed, later campaigns may add a feature/label foundation
(`ALPHA_FEATURE_LABEL_FOUNDATION_V1`), an agent factory (`ALPHA_AGENT_FACTORY_MVP`), core
futures alpha research (`ALPHA_FUTURES_CORE_ALPHA_V1`), a portfolio AlphaBook
(`ALPHA_PORTFOLIO_ALPHA_BOOK_V1`), and deeper validation governance
(`ALPHA_VALIDATION_GOVERNANCE_V1`) — each only under its own explicitly authorized
campaign contract, and each constrained by the governance gates and the data-admissibility
rules this campaign installs. Future alpha research must not use the locked-test partition
without Governance metadata, and any future use of locked partitions must create
contamination metadata.
