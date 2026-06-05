# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
an Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`ALPHA_FEATURE_LABEL_FOUNDATION_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`.

`ALPHA_FEATURE_LABEL_FOUNDATION_V1` is the active campaign. After this phase
merge, Wave 1 feature-family work is underway: FLF-P08 Base OHLCV, FLF-P09 BBO
tradability, FLF-P10 Session / Calendar / Roll, and FLF-P11 Cross-Market
ES/NQ/RTY feature families are present alongside the governed FeatureRequest
gate, FeatureSpec / FeatureVersion contracts, and shared causal primitives.
Active phase snapshot: `FLF-P10` - Session / Calendar / Roll Feature Families.
The next dependency-ready work remains the remaining Wave 1 family phase(s),
then Wave 2 feature integration `FLF-P13`.

`FLF-P00` adds the durable `docs/feature_label_foundation/` documentation root:

- `docs/feature_label_foundation/README.md`
- `docs/feature_label_foundation/OVERVIEW.md`

`FLF-P01` adds the `alpha_system.features` package root, the read-only
DatasetVersion consumption adapter `alpha_system.features.consumption`, and:

- `docs/feature_label_foundation/ENTRY_CONTRACT_CONSUMPTION.md`

`FLF-P02` adds the importable feature package skeleton
(`families/`, `primitives/`, `engine/`), the additive `labels/families/`
subpackage, feature/label config roots, import-smoke test roots, and:

- `docs/feature_label_foundation/NAMING.md`

`FLF-P03` adds the durable canonical input-view layer
`alpha_system.features.input_views`, scoped available-time tests, and:

- `docs/feature_label_foundation/INPUT_VIEWS.md`

`FLF-P04` adds the dense-grid / no-trade / BBO missingness semantics module
`alpha_system.features.semantics`, scoped synthetic-fixture tests, and:

- `docs/feature_label_foundation/DENSE_GRID_AND_BBO_SEMANTICS.md`

`FLF-P05` adds the governed feature implementation gate
`alpha_system.features.request_gate`, scoped synthetic-governance tests, and:

- `docs/feature_label_foundation/FEATURE_REQUEST_GATE.md`

`FLF-P06` adds immutable feature contract objects in
`alpha_system.features.contracts`, scoped contract tests, and:

- `docs/feature_label_foundation/FEATURE_CONTRACTS.md`

`FLF-P07` adds the shared causal primitive package
`alpha_system.features.primitives`, scoped primitive and no-lookahead tests,
and:

- `docs/feature_label_foundation/PRIMITIVES.md`

`FLF-P08` adds the additive Base OHLCV feature family package
`alpha_system.features.families.ohlcv`, scoped synthetic fixture tests, family
config placeholders, and:

- `docs/feature_label_foundation/features/ohlcv.md`

`FLF-P09` adds the additive BBO tradability feature family package
`alpha_system.features.families.bbo`, scoped synthetic fixture tests, family
config placeholders, and:

- `docs/feature_label_foundation/features/bbo.md`

`FLF-P10` adds the additive Session / Calendar / Roll feature family package
`alpha_system.features.families.session`, scoped synthetic fixture tests,
family config placeholders, and:

- `docs/feature_label_foundation/features/session.md`

`FLF-P11` adds the additive Cross-Market ES/NQ/RTY feature family package
`alpha_system.features.families.cross_market`, scoped synthetic fixture tests,
family config placeholders, and:

- `docs/feature_label_foundation/features/cross_market.md`

No new command surface is added by FLF-P10.

Safety boundaries are unchanged: local-only values; accepted DatasetVersions
only; ES/NQ/RTY cross-market inputs must stay within one accepted
DatasetVersion family; session/calendar/roll features never fabricate absent
expiration or status metadata; no raw provider access; no external provider
calls; no silent BBO forward-fill or interpolation; feature and label values
remain local-only; governance is consumed, not duplicated; no broker, live,
paper, order, or account scope; and no alpha, tradability, or profitability
claims.

Post-closeout, the data foundation was exercised with real local-only data from
two providers with distinct roles. **Databento** is the primary deep-history
research source: Phase B (PR #107) pulled the full GLBX.MDP3 ES/NQ/RTY
continuous OHLCV-1m + BBO-1m history (2018–2026), canonicalized it into sparse
provider truth plus a derived dense research grid, and registered 27 local-only
DatasetVersions. **IBKR** is the read-only broker-validation source (~2 years of
available depth) with its own separate DatasetVersions. All raw/canonical data,
registries, and reports stay local-only under `ALPHA_DATA_ROOT`; nothing is
committed, and no alpha, tradability, profitability, paper/live, or broker claim
is made. See `handoffs/ALPHA_DATA_FOUNDATION_V1/ADF1_DATABENTO_ES_NQ_RTY_OHLCV_BBO_DEEP_HISTORY.md` and
the `docs/data_foundation/` docs (including the `databento/` subdirectory).

This repository is not a broker, paper-trading, live-trading, order-routing, or
production execution system. It must not introduce alpha, profitability,
tradability, or production-readiness claims.

## Current Repo Snapshot

`ALPHA_FEATURE_LABEL_FOUNDATION_V1` foundation-wave progress includes FLF-P08,
FLF-P09, FLF-P10, and FLF-P11 after this phase merge; the active phase snapshot
is `FLF-P10`, the feature-contract gate includes the FeatureRequest gate,
FeatureSpec / FeatureVersion contracts, `alpha_system.features.primitives`, the
additive Base OHLCV family, the additive BBO tradability family, the additive
Session / Calendar / Roll family, and the additive Cross-Market ES/NQ/RTY
family, and the next work is the remaining Wave 1 family phase(s) before
FLF-P13 feature integration. The completed
data-foundation baseline remains unchanged:
`ALPHA_DATA_FOUNDATION_V1` is
complete. Within the
`campaign_bootstrap` gate,
`DATA-P00` and `DATA-P01` are complete; the `DATA-P02` executor snapshot adds
validated `DataSourceProfile` and `LocalDataRootPolicy` records; and the
`DATA-P03` executor snapshot adds `IBKRConnectionProfile`,
`IBKRClientIdPolicy`, and a diagnostic-only connection-doctor scaffold. The
`ibkr_read_only_boundary` gate has the `DATA-P04` executor scope complete:
read-only IBKR API boundary, order-method kill switch, and `DataAccessMode`
gate. The `futures_contract_master` gate has progressed through `DATA-P06`:
`DATA-P05` adds `InstrumentMasterRecord`, six to-be-verified futures
contract-economics anchors, and exact `tick_value = tick_size * point_value`
validation; `DATA-P06` adds `ContractDetailsSnapshot`,
`FuturesContractRecord`, and the no-live-call contract-discovery scaffold. The
`request_and_storage` is complete through `DATA-P10`: `DATA-P07` adds
`HistoricalRequestSpec`, `HistoricalRequestManifest`, deterministic
`manifest_hash` validation, the no-manifest-no-pull guard, the synthetic sample
manifest under `templates/data/`, and
`docs/data_foundation/REQUEST_SPEC_AND_MANIFEST.md`. `DATA-P08` is complete and
adds `RequestPacingPolicy`, `HistoricalChunkRecord`, `HistoricalPullLedger`,
`ProviderErrorRecord`, conservative to-be-verified pacing config, and
`docs/data_foundation/PACING_AND_RESUME.md`. The `DATA-P09` executor scope adds
`RawDataObject`, `RawDataLakeLayoutPolicy`, content-addressed raw path
resolution, raw-slot immutability/no-overwrite validation, and
`docs/data_foundation/RAW_DATA_LAKE.md`. The `DATA-P10` executor scope adds
`SymbolBatchPlan`, the ES/NQ/RTY mini main-batch pull plan, labeled optional
secondary panels, the synthetic mini-batch manifest, and
`docs/data_foundation/MINI_BATCH_PLAN.md`. The `provenance_sessions_rolls` gate
is complete through the `DATA-P13` executor snapshot: DATA-P11 adds
provenance-rich `ContinuousFuturesSeriesRecord` and
`DatedFuturesSeriesRecord` validation in
`src/alpha_system/data/foundation/series.py`, plus
`docs/data_foundation/PROVENANCE.md`; DATA-P12 adds fail-closed
`SessionTemplate` and `TradingCalendarRecord` validation in
`src/alpha_system/data/foundation/sessions.py`, the synthetic
`session_cme_index_futures_eth` template config, and
`docs/data_foundation/SESSIONS_AND_CALENDAR.md`; DATA-P13 adds fail-closed
`RollPolicy` and `RollCalendarRecord` validation in
`src/alpha_system/data/foundation/rolls.py`, with explicit adjusted vs
unadjusted state, required roll evidence and validation status, and
`docs/data_foundation/ROLL_POLICY.md`. The `canonicalization_quality_versioning`
gate has the `DATA-P14` executor scope complete: provider-shaped
`ParsedBarRecord` validation, deterministic raw-object bar parsing with
raw-to-parsed provenance, and `docs/data_foundation/PARSED_BARS.md`; DATA-P15
adds `CanonicalBarRecord`, `TimestampSemanticsPolicy`, explicit
`available_ts` no-lookahead validation, canonical timestamp tests, and
`docs/data_foundation/CANONICAL_BARS.md`; DATA-P16 adds fail-closed
`DataQualityReport` and `CoverageReport` contracts, aggregate quality and
coverage tests, and `docs/data_foundation/DATA_QUALITY.md` /
`docs/data_foundation/COVERAGE_REPORT.md`; DATA-P17 adds the fail-closed
`DatasetVersion` contract, the data-foundation registry adapter for the
existing local SQLite `dataset_versions` table, duplicate-ID rejection,
reproducibility hash binding enforced before registry writes, temp-DB registry
tests, and
`docs/data_foundation/DATASET_VERSION.md`; DATA-P18 adds the
`DatasetPartitionPlan` contract, canonical development / validation /
locked-test candidate windows, the optional latest-shadow candidate, the
locked-test contamination-metadata rules, and
`docs/data_foundation/PARTITION_PLAN.md`. This advances the
`canonicalization_quality_versioning` gate through the DATA-P18 executor
snapshot. The `secondary_data_tracks` gate has progressed through the DATA-P20
executor snapshot: DATA-P19 adds `MicroBatchPolicy`, the separate MES/MNQ/M2K
secondary micro-batch plan, mini-to-micro parity-check target declarations, and
`docs/data_foundation/MICRO_BATCH.md`; DATA-P20 adds the optional bounded
`BidAskPilotPlan`, the pilot-only `SpreadProxyMetric` scaffold, the
declarative BID_ASK pilot config, synthetic spread-proxy fixture tests, and
`docs/data_foundation/BID_ASK_PILOT.md`. The
`validation_and_authorized_smoke` gate is complete through the DATA-P23
executor snapshot: DATA-P21 synthetic IBKR-shaped fixture tests compose the
read-only boundary, manifest, pacing/resume ledger, parser, canonical bars,
quality/coverage, and dataset-version registry path with no external provider
call; DATA-P22 adds the guarded read-only IBKR smoke-pull entry point and
`docs/data_foundation/SMOKE_PULL.md`; DATA-P23 adds the local backfill
resume-drill entry point under `src/alpha_system/data/ibkr/backfill.py` and
`docs/data_foundation/BACKFILL_RUNBOOK.md`. DATA-P24 is the final closeout
phase, bringing `DATA-P00` through `DATA-P24` to 25 of 25 executor scopes. It
adds the synthetic end-to-end dry-run entry point
`alpha_system.data.foundation.dry_run`,
`docs/data_foundation/END_TO_END_DRY_RUN.md`, and
`campaigns/ALPHA_DATA_FOUNDATION_V1/CLOSEOUT.md`; the closeout verdict is
`COMPLETE_WITH_WARNINGS` after Ralph completed all Workflow 2 gates and a
post-run `python tools/verify.py --all` rerun passed locally. The active phase
is `none` because the campaign is complete; there is no next phase in this
campaign. The read-only IBKR boundary, clientId `101`/`102` hard-block,
data-client namespace `201-209` with default `201`, never-in-CI external
pulls, local-only data artifacts, and no broker/order/account/paper/live scope
are unchanged.

`DATA-P00` added the durable `docs/data_foundation/` root:

- `docs/data_foundation/README.md`
- `docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md`

`DATA-P01` adds the data-foundation skeleton under `src/alpha_system/data/foundation/`
alongside the pre-existing `alpha_system.data` modules. It defines placeholder
names for data sources, local data-root policy, IBKR historical-data connection
metadata, request manifests and ledgers, raw/parsed/canonical bars, instruments,
sessions, rolls, series provenance, batches, dataset versions, quality, coverage,
and partitions.

`DATA-P02` adds fail-closed policy behavior for provider usage modes and the
local data root under `src/alpha_system/data/foundation/sources.py`, plus unit
tests under `tests/unit/data/` and these durable docs:

- `docs/data_foundation/DATA_SOURCE_PROFILE.md`
- `docs/data_foundation/LOCAL_DATA_ROOT_POLICY.md`

`DATA-P03` adds fail-closed IBKR historical connection configuration under
`src/alpha_system/data/foundation/ibkr.py`. clientId `101` and `102` are
hard-blocked, the data namespace is `201-209` with default `201`, worker IDs are
`ES=201`, `NQ=202`, `RTY=203`, and the connection doctor records scaffold
reachability status without opening a socket or calling IBKR. It also adds:

- `docs/data_foundation/IBKR_CONNECTION_PROFILE.md`
- `docs/data_foundation/CLIENT_ID_POLICY.md`

`DATA-P04` adds the read-only IBKR API boundary under
`src/alpha_system/data/foundation/ibkr.py` and the `DataAccessMode` gate under
`src/alpha_system/data/foundation/sources.py`. The boundary stores only
registered historical read-only callables, exposes no generic IBKR client path,
and hard-refuses order, account, position, broker, paper, live, and trading
methods. It also adds:

- `docs/data_foundation/READ_ONLY_BOUNDARY.md`

`DATA-P05` adds the futures instrument master under
`src/alpha_system/data/foundation/instruments.py`, with the ES/NQ/RTY and
MES/MNQ/M2K contract-economics anchors in
`configs/data/futures_instrument_master.json`. The anchors are recorded as
to-be-verified economic anchors, not production-certified values, and are
validated with exact `Decimal` equality for tick value, tick size, and point
value. It also adds:

- `docs/data_foundation/INSTRUMENT_MASTER.md`

`DATA-P06` adds dated futures contract identity and contract-details provenance
under `src/alpha_system/data/foundation/instruments.py`. It defines
`FuturesContractRecord`, immutable content-addressed `ContractDetailsSnapshot`
records, and a pure contract-discovery scaffold that logs includeExpired
availability as discovered, not assumed. It also adds:

- `docs/data_foundation/CONTRACT_DISCOVERY.md`

`DATA-P07` adds historical request planning under
`src/alpha_system/data/foundation/requests.py`. It defines
`HistoricalRequestSpec`, `HistoricalRequestManifest`, deterministic
`manifest_hash` computation, and a lifecycle guard that blocks provider-pull
preflight without a valid manifest. It also adds the synthetic-only manifest
template `templates/data/synthetic_historical_request_manifest.json` and:

- `docs/data_foundation/REQUEST_SPEC_AND_MANIFEST.md`

`DATA-P08` adds pacing, chunk lifecycle, retry/error, and resume-ledger records
under `src/alpha_system/data/foundation/requests.py`. It defines
`RequestPacingPolicy`, `HistoricalChunkRecord`, `HistoricalPullLedger`,
`ProviderErrorRecord`, duplicate-request detection, `resume_token` resume
state, no-silent-gaps reconciliation, and immutable content-addressed
`raw_object_ref` validation. It also adds:

- `configs/data/request_pacing_policy_to_be_verified.json`
- `docs/data_foundation/PACING_AND_RESUME.md`

`DATA-P09` adds the raw local data lake contract under
`src/alpha_system/data/foundation/bars.py`. It defines `RawDataObject`,
`RawDataLakeLayoutPolicy`, content-addressed raw object refs compatible with
`HistoricalChunkRecord.raw_object_ref`, local-only raw path validation under
`ALPHA_DATA_ROOT`, and the raw-slot immutability guard. It also adds:

- `docs/data_foundation/RAW_DATA_LAKE.md`

`DATA-P10` adds the mini main-batch plan under
`src/alpha_system/data/foundation/batches.py`. It defines `SymbolBatchPlan`
with exact ES/NQ/RTY mini roots, MES/MNQ/M2K micro roots,
`max_concurrent_roots = 3`, and fail-closed rejection for any mini/micro mix.
It also defines the primary `2018-01-01 -> present_as_of_run`, `1 min`,
`TRADES` mini panel, the labeled optional ES/NQ long, RTY transition QA, and
contract-truth diagnostic panels, plus the synthetic-only mini manifest
`templates/data/synthetic_mini_batch_manifest.json`. It also adds:

- `docs/data_foundation/MINI_BATCH_PLAN.md`

`DATA-P11` adds futures series provenance validation under
`src/alpha_system/data/foundation/series.py`. It defines
`ContinuousFuturesSeriesRecord` with the required
`provider_continuous` / `non_orderable` / `not_dated_contract_truth` /
`research_diagnostics_only` labels, `orderable = false`, and
`dated_truth = false`; and it defines `DatedFuturesSeriesRecord` with explicit
adjustment method, dated-contract universe validation, and
`availability_source = discovered_not_assumed`. It also adds:

- `docs/data_foundation/PROVENANCE.md`

`DATA-P12` adds session-template and dated calendar validation under
`src/alpha_system/data/foundation/sessions.py`. It defines `SessionTemplate`
and `TradingCalendarRecord` with explicit IANA timezone enforcement,
timezone-aware timestamp requirements, DST offset-transition representation,
early-close and holiday validation, and a resolver for the DATA-P05
`InstrumentMasterRecord.session_template_id` linkage. It also adds the
synthetic `configs/data/session_templates_and_calendar.json` scaffold and:

- `docs/data_foundation/SESSIONS_AND_CALENDAR.md`

`DATA-P13` adds roll-policy and roll-calendar validation under
`src/alpha_system/data/foundation/rolls.py`. It defines `RollPolicy` and
`RollCalendarRecord` with closed roll methods/triggers, explicit
`adjustment_method`, required evidence and validation status, distinct dated
`FuturesContractRecord` transitions, and provider-continuous vs derived roll
separation. It also adds:

- `docs/data_foundation/ROLL_POLICY.md`

`DATA-P14` adds parsed bronze bar records and a deterministic raw-object parser
under `src/alpha_system/data/foundation/bars.py`. It defines
`ParsedBarRecord`, `ParsedBarParser`, and `parse_raw_bar_records()` with
provider-shaped timestamp preservation, optional WAP/bar-count fields,
mandatory `request_id` and `raw_object_id` provenance, payload hash checks, and
fail-closed malformed-row behavior. It also adds:

- `docs/data_foundation/PARSED_BARS.md`

`DATA-P15` adds the canonical 1-minute bar contract under
`src/alpha_system/data/foundation/bars.py`. It defines `CanonicalBarRecord` and
`TimestampSemanticsPolicy` with separate `bar_start_ts`, `bar_end_ts`,
`event_ts`, `available_ts`, and `ingested_at` fields, mandatory
`available_ts`, `available_ts >= bar_end_ts`, OHLCV/session/quality-flag
validation, and no-lookahead tests under `tests/no_lookahead/`. It also adds:

- `docs/data_foundation/CANONICAL_BARS.md`

`DATA-P16` adds fail-closed quality and coverage reports under
`src/alpha_system/data/foundation/datasets.py`. `DataQualityReport` classifies
aggregate gaps, duplicate and non-monotonic timestamps, OHLC/price defects,
zero-volume anomalies, DST anomalies, session coverage, roll discontinuities,
and provider errors with explicit `PASSING` / `WARNING` / `BLOCKING` status.
`CoverageReport` records aggregate symbol, contract, session, and partition
coverage plus missing intervals and incomplete chunks; coverage alone is not
quality unless linked to a non-blocking `DataQualityReport` for the same dataset
version. It also adds:

- `docs/data_foundation/DATA_QUALITY.md`
- `docs/data_foundation/COVERAGE_REPORT.md`

`DATA-P17` adds the data-foundation `DatasetVersion` contract and registry
adapter under `src/alpha_system/data/foundation/`. Dataset versions carry
source, symbol/contract universes, bar settings, timestamps, roll policy, and
the manifest/code/config/quality-report hashes required for reproducibility.
The adapter reuses `core.registry.init_registry` and `connect_registry` against
the existing local SQLite `dataset_versions` table, requires linked quality,
coverage, and manifest prerequisites before writes, persists the full DATA-P17
object in `metadata_json`, resolves by `dataset_version_id`, and rejects
duplicate IDs without overwrite. It also adds:

- `docs/data_foundation/DATASET_VERSION.md`

`DATA-P18` adds the data-foundation `DatasetPartitionPlan` contract under
`src/alpha_system/data/foundation/datasets.py`. The plan pins the canonical
development window (`2018-01-01` through `2022-12-31`), validation window
(`2023-01-01` through `2024-12-31`), locked-test candidate window
(`2025-01-01` through `as_of_run`), and optional latest-shadow candidate. Its
structured contamination-metadata rules allow data QA coverage inspection across
partitions while requiring Governance contamination metadata before any future
non-QA use of locked partitions. It does not authorize locked-partition use. It
also adds:

- `docs/data_foundation/PARTITION_PLAN.md`

`DATA-P19` adds the micro-batch policy under
`src/alpha_system/data/foundation/batches.py`. It defines `MicroBatchPolicy`
with exact MES/MNQ/M2K symbols, `start_date = 2020-01-01` as a to-be-verified
planning default, `separate_batch = true`, and declaration-only parity-check
targets ES->MES, NQ->MNQ, and RTY->M2K. The policy references the DATA-P05
`InstrumentMasterRecord` economics for micro roots and the DATA-P10
mini/micro separation contract without duplicating economics or mixing batches.
Micros remain a separate secondary path, not a primary alpha source in V1. It
also adds:

- `docs/data_foundation/MICRO_BATCH.md`

`DATA-P20` adds the optional BID_ASK pilot plan and spread-proxy scaffold under
`src/alpha_system/data/foundation/bid_ask_pilot.py`. The pilot is optional,
bounded, secondary to the primary TRADES panel, and tied to the DATA-P08
manifest/pacing/resume contracts and DATA-P16 quality/coverage contracts. The
spread proxy is pilot-only and research-diagnostics-only; it computes from tiny
synthetic inputs and makes no tradability, cost, liquidity, or execution-truth
claim. It also adds:

- `configs/data/bid_ask_pilot_plan.json`
- `docs/data_foundation/BID_ASK_PILOT.md`

`DATA-P21` adds synthetic IBKR fixture tests under `tests/unit/data/` and
`tests/integration/data/`, plus the tiny hand-authored
`tests/fixtures/data/synthetic_ibkr_e2e_provider_fixture.json`. The tests drive
the existing read-only boundary, manifest, pacing/resume ledger, parser,
canonical bar, quality/coverage, and dataset-version registry contracts on
synthetic inputs only. They assert no external call, clientId `101`/`102`
fail-closed behavior, no-manifest/no-pacing blocking, missing `available_ts`
blocking, silent-gap versioning blocks, and continuous-not-dated-truth
provenance separation. It also adds:

- `docs/data_foundation/SYNTHETIC_FIXTURE_TESTS.md`

`DATA-P22` adds the guarded read-only IBKR smoke-pull entry point under
`src/alpha_system/data/ibkr/pull.py` and `docs/data_foundation/SMOKE_PULL.md`.
`DATA-P23` adds the local backfill resume-drill entry point under
`src/alpha_system/data/ibkr/backfill.py`, the tiny synthetic fixture
`tests/fixtures/data/synthetic_backfill_resume_drill.json`, synthetic
resume/no-gap/no-overwrite unit tests, and
`docs/data_foundation/BACKFILL_RUNBOOK.md`. The real external leg remains
operator-run only, requires the data-pull authorization env, never runs in CI,
and writes only under `$ALPHA_DATA_ROOT` outside the repo.

`DATA-P24` adds the synthetic end-to-end dry-run entry point under
`src/alpha_system/data/foundation/dry_run.py`, plus
`tests/unit/data/test_data_foundation_dry_run.py`,
`tests/integration/data/test_end_to_end_data_foundation_dry_run.py`,
`docs/data_foundation/END_TO_END_DRY_RUN.md`, and
`campaigns/ALPHA_DATA_FOUNDATION_V1/CLOSEOUT.md`. The dry run exercises
source, connection, manifest, pacing/resume ledger, raw object metadata,
parsed bars, canonical bars, quality/coverage reports, dataset-version
prerequisites, registry round-trip, and partition metadata over synthetic
fixtures only. The campaign has no next phase; future campaigns consume this
layer under their own contracts.

The prior `ALPHA_SYSTEM_V1`, `ASV1_RELEASE_HYGIENE`, and
`ALPHA_RESEARCH_GOVERNANCE_MVP` baselines are treated as complete. This campaign
builds on that local-first research harness by adding a read-only, provenance-rich
historical futures data foundation.

Safety boundaries are unchanged: IBKR remains read-only historical only;
clientId `101` and `102` remain fail-closed, the data namespace remains
`201-209`; mini and micro batches remain separate; no provider pull proceeds
without manifest, pacing guard, and resume ledger; continuous futures are never
dated-contract truth; no broker, order, account, paper, live, or real-time
scope is introduced; real data is local-only via `ALPHA_DATA_ROOT`; no raw or
heavy artifact commits, no local DB commits, explicit staging only, and no
alpha, profitability, tradability, best-execution-roll, or
production-readiness claims.

## Data Foundation Docs

The data-foundation docs root currently includes:

- `docs/data_foundation/README.md`
- `docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md`
- `docs/data_foundation/databento/` — primary deep-history provider docs
  (`README.md`, `CONSUMPTION.md`, `INGESTION_RUNBOOK.md`)
- `docs/data_foundation/NAMING.md`
- `docs/data_foundation/DATA_SOURCE_PROFILE.md`
- `docs/data_foundation/LOCAL_DATA_ROOT_POLICY.md`
- `docs/data_foundation/IBKR_CONNECTION_PROFILE.md`
- `docs/data_foundation/CLIENT_ID_POLICY.md`
- `docs/data_foundation/READ_ONLY_BOUNDARY.md`
- `docs/data_foundation/INSTRUMENT_MASTER.md`
- `docs/data_foundation/CONTRACT_DISCOVERY.md`
- `docs/data_foundation/REQUEST_SPEC_AND_MANIFEST.md`
- `docs/data_foundation/PACING_AND_RESUME.md`
- `docs/data_foundation/RAW_DATA_LAKE.md`
- `docs/data_foundation/MINI_BATCH_PLAN.md`
- `docs/data_foundation/MICRO_BATCH.md`
- `docs/data_foundation/PROVENANCE.md`
- `docs/data_foundation/SESSIONS_AND_CALENDAR.md`
- `docs/data_foundation/ROLL_POLICY.md`
- `docs/data_foundation/PARSED_BARS.md`
- `docs/data_foundation/CANONICAL_BARS.md`
- `docs/data_foundation/DATA_QUALITY.md`
- `docs/data_foundation/COVERAGE_REPORT.md`
- `docs/data_foundation/DATASET_VERSION.md`
- `docs/data_foundation/DATASET_CONSUMPTION.md`
- `docs/data_foundation/BID_ASK_PILOT.md`
- `docs/data_foundation/SYNTHETIC_FIXTURE_TESTS.md`
- `docs/data_foundation/SMOKE_PULL.md`
- `docs/data_foundation/BACKFILL_RUNBOOK.md`
- `docs/data_foundation/END_TO_END_DRY_RUN.md`

These docs describe the read-only data truth layer, campaign hard rules,
data-foundation object list, lifecycle state model, prohibited MVP states, IBKR
read-only posture, canonical object names, ID prefixes, module names,
file-naming conventions, directory layout, `DataSourceProfile`,
`LocalDataRootPolicy`, `IBKRConnectionProfile`, `IBKRClientIdPolicy`,
`IBKRReadOnlyApiBoundary`, `DataAccessMode`, `InstrumentMasterRecord`,
contract-economics anchors, `FuturesContractRecord`,
`ContractDetailsSnapshot`, contract-discovery availability logging, and the
`HistoricalRequestSpec` / `HistoricalRequestManifest` planning records,
`manifest_hash`, the no-manifest-no-pull block, `RequestPacingPolicy`,
`HistoricalChunkRecord`, `HistoricalPullLedger`, `ProviderErrorRecord`,
duplicate-request detection, retry/backoff classification, `resume_token`, the
no-silent-gaps and no-raw-overwrite guards, `RawDataObject`, the raw data-lake
layout policy, immutable raw object refs, raw-slot immutability validation,
`SymbolBatchPlan`, mini/micro batch separation, the ES/NQ/RTY primary common
panel, labeled optional secondary panels, `MicroBatchPolicy`,
`BidAskPilotPlan`, `SpreadProxyMetric`, continuous-vs-dated futures
provenance separation, mandatory continuous diagnostic labels,
discovered-not-assumed dated availability, adjusted-vs-unadjusted explicitness,
session templates, dated trading calendar records, explicit timezone/DST and
early-close/holiday handling, roll policy, roll calendar records, required
roll evidence and validation status, provider-continuous vs derived roll
separation, provider-shaped parsed bars, raw-to-parsed provenance links, the
parsed-not-canonical boundary, canonical 1-minute bar fields,
`TimestampSemanticsPolicy`, explicit `available_ts` no-lookahead semantics, and
fail-closed data quality and coverage reports, `DatasetVersion`,
reproducibility hash binding, local SQLite registry integration, duplicate-ID
rejection, DatasetVersion consumption rules for later feature/label campaigns,
the `QUALITY_CHECKED -> VERSIONED -> READY_FOR_RESEARCH` data-admissibility
gate, synthetic IBKR fixture composition tests with a no-external-call proof,
the guarded smoke pull, local backfill resume drill, and the `ALPHA_DATA_ROOT`
local-only data-root pointer.
Field-level acceptance rules, risks, and operator procedures remain in the
campaign contract bundle.

## Campaign Source Of Truth

The current completed campaign contract bundle lives under
`campaigns/ALPHA_DATA_FOUNDATION_V1/`:

- `GOAL.md`
- `PHASE_PLAN.md`
- `campaign.yaml`
- `ACCEPTANCE.md`
- `RISK_REGISTER.md`
- `RUNBOOK.md`

`ACTIVE_CAMPAIGN.md` is the repository-level active-campaign pointer. Do not
create `campaigns/ALPHA_DATA_FOUNDATION_V1/ACTIVE_CAMPAIGN.md`.

## Prior Baselines

`ALPHA_DATA_FOUNDATION_V1` builds on these completed baselines:

- `ALPHA_SYSTEM_V1`
- `ASV1_RELEASE_HYGIENE`
- `ALPHA_RESEARCH_GOVERNANCE_MVP`

The governance docs remain under `docs/governance/`; future research must still
honor the governance protocol before broader research campaigns expand scope.

## Repository Location

Canonical repo path:

```text
~/projects/alpha_system
```

The active repo and any active worktree must live on the WSL2 Linux
filesystem. Do not run active work from `/mnt/c`, `/mnt/d`, `/mnt/e`,
OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, or
temporary directories.

## Workflow 2 Boundary

Frontier Workflow 2 uses Ralph as the strict autonomous driver. Codex executes
generated phase specs and writes executor output and commit-eligible handoffs.
Ralph owns formal validation, independent review, verdict parsing, repair
orchestration, semantic done-checks, PR creation, CI, and merge gates.

Required safety defaults:

- STOP files halt the Workflow 2 loop at configured checkpoints.
- Yellow phases require fresh independent review before merge eligibility.
- No phase may weaken or game tests.
- Run-local Workflow 2 artifacts stay under `runs/**`.
- Commit-eligible data-foundation handoffs live under
  `handoffs/ALPHA_DATA_FOUNDATION_V1/**`.

## Git Discipline

Use explicit staging only. Stage curated paths one by one.

Forbidden:

```bash
git add .
git add -A
git push --force
```

Before any commit or merge-gate evaluation, inspect:

```bash
git status --short
git diff --cached --name-only
git ls-files runs
```

The staged set must contain only commit-eligible paths for the active phase and
must not include `runs/**`, raw data, canonical data, provider responses,
account artifacts, DB files, logs, caches, or heavy artifacts.

## Artifact Policy

Never commit raw data, canonical generated data, materialized factor values,
materialized label values, local SQLite or DB files, heavy artifacts, generated
reports, logs, caches, local model artifacts, credential material, provider
responses, account information, or local environment files.

Raw and canonical real market data remain local-only outside git. `runs/**` is
local-only runtime state and must not be staged or committed.
Permitted placeholders are limited to `.gitkeep` or `README.md` files where the
campaign policy allows them. Commit-eligible phase handoffs for this campaign
belong under `handoffs/ALPHA_DATA_FOUNDATION_V1/`.

## Documentation Map

Project-level orientation:

- `ACTIVE_CAMPAIGN.md`
- `PROJECT_STATUS.md`
- `AGENTS.md`
- `CLAUDE.md`

Data-foundation docs:

- `docs/data_foundation/README.md`
- `docs/data_foundation/DATA_FOUNDATION_OVERVIEW.md`
- `docs/data_foundation/NAMING.md`

Governance docs:

- `docs/governance/README.md`
- `docs/governance/GOVERNANCE_OVERVIEW.md`
- `docs/governance/WORKFLOW2_INTEGRATION.md`

Architecture and workflow docs:

- `docs/ONBOARDING.md`
- `docs/RESEARCHER_GUIDE.md`
- `docs/AI_AGENT_GUIDE.md`
- `docs/CLI_REFERENCE.md`
- `docs/EXAMPLE_WORKFLOWS.md`
- `docs/TROUBLESHOOTING.md`
- `docs/RESEARCH_INTERPRETATION_POLICY.md`
- `docs/ARTIFACT_POLICY.md`
- `docs/DOMAIN_BOUNDARIES.md`
- `docs/NO_LOOKAHEAD_POLICY.md`
- `docs/BACKTEST_TIERS.md`
- `docs/REPRODUCIBILITY_PRINCIPLES.md`
- `docs/CLI_COMMANDS_TARGET.md`

## Directory Layout

Commit-eligible policy and campaign files live under:

- `campaigns/`
- `specs/`
- `handoffs/`
- `reviews/`
- `docs/`
- `decisions/`
- `evals/`
- `configs/`
- `templates/`
- `src/alpha_system/cli/`
- `src/alpha_system/data/`
- `src/alpha_system/governance/`
- `tests/unit/data/`
- `tools/governance/`
- `tests/unit/governance/`
- `tests/integration/governance/`
- `tests/no_lookahead/`

Local data and generated artifact roots are present for structure only:

- `data/raw/`
- `data/canonical/`
- `data/factors/`
- `data/labels/`
- `data/cache/`
- `metadata/`
- `artifacts/`

## Useful Commands

The DATA-P01 data-foundation skeleton imports through
`alpha_system.data.foundation`. The governance CLI command group remains
`alpha governance`; see `docs/governance/CLI.md` for arguments and gate behavior.
Local validation commands include:

```bash
python -c "import alpha_system.data"
python -m pytest tests/unit/data -q
python -c "import alpha_system.governance"
python -m pytest tests/unit/governance/test_canary_harness.py -q
python -m pytest tests/unit/governance/test_negative_controls.py -q
python -m pytest tests/integration/governance/test_end_to_end_dry_run.py -q
python -m pytest tests/unit/governance -q
python -m pytest tests/integration/governance -q
python -m pytest tests/no_lookahead/test_governance_canaries.py -q
python -m pytest tests/no_lookahead -q
python tools/governance/validate_objects.py --object AlphaSpec:tests/fixtures/governance/alpha_spec_valid.json
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
```
