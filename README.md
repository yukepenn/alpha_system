# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
an Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`ALPHA_RESEARCH_RUNTIME_MVP`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`.

`ALPHA_RESEARCH_RUNTIME_MVP` is the active Workflow 2 campaign. As of the
RT-P19 Runtime Cache and Local Artifact Policy snapshot, progress is 20/27
phases through RT-P19 in the `runtime_integration` gate. RT-P19 adds the
metadata-only `RuntimeCachePolicy` and the pure runtime artifact policy for
derived-summary cache keys and `commit_allowed` classification. Active/next:
`RT-P19` done; next phase `RT-P20` - Synthetic Runtime Fixtures and Fail-Closed
Tests, in the parallel tests/tools/docs wave. Ralph remains responsible for
validation, review, merge queue handling, and next-phase selection; phase
branches do not update `ACTIVE_CAMPAIGN.md` in parallel mode.

Durable Research Runtime modules currently include
`alpha_system.runtime.entry_contract`, `alpha_system.runtime.input_resolver`,
`alpha_system.runtime.contracts`, `alpha_system.runtime.diagnostics`,
`alpha_system.runtime.diagnostics.factor`,
`alpha_system.runtime.diagnostics.label`,
`alpha_system.runtime.diagnostics.splits`, and
`alpha_system.runtime.diagnostics.cross_market`,
`alpha_system.runtime.cost`, `alpha_system.runtime.probe`, and
`alpha_system.runtime.grid`, `alpha_system.runtime.audit`,
`alpha_system.runtime.decisions`, `alpha_system.runtime.evidence`, and
`alpha_system.runtime.handoff`, plus `alpha_system.runtime.cache_policy` and
`alpha_system.runtime.artifact_policy`. RT-P18 adds
`alpha_system.cli.runtime` and the `alpha runtime` commands: `plan`,
`validate-inputs`, `run-diagnostics`,
`run-label-diagnostics`, `run-signal-probe`, `run-cost-stress`,
`build-evidence-draft`, `build-reference-handoff`, `summarize`, `inspect`, and
`replay-summary`. RT-P19 adds value-free cache lineage keys, hit/miss/stale
metadata decisions, local-only storage-root resolution, and reusable
commit-eligible-vs-local-only artifact classification. The CLI is an
orchestration layer only; it does not duplicate runtime logic.

Durable runtime documentation:

- `docs/research_runtime/README.md`
- `docs/research_runtime/OVERVIEW.md`
- `docs/research_runtime/ENTRY_CONTRACT.md`
- `docs/research_runtime/NAMING.md`
- `docs/research_runtime/INPUT_RESOLVER.md`
- `docs/research_runtime/RUN_SPEC_AND_PLAN.md`
- `docs/research_runtime/RUN_RECORD_AND_MANIFEST.md`
- `docs/research_runtime/DIAGNOSTICS_CONTRACTS.md`
- `docs/research_runtime/diagnostics/splits.md`
- `docs/research_runtime/diagnostics/factor.md`
- `docs/research_runtime/diagnostics/label.md`
- `docs/research_runtime/diagnostics/cross_market.md`
- `docs/research_runtime/COST_STRESS.md`
- `docs/research_runtime/SIGNAL_PROBE.md`
- `docs/research_runtime/BOUNDED_GRID.md`
- `docs/research_runtime/NO_LOOKAHEAD_AUDIT.md`
- `docs/research_runtime/DECISION_STATES.md`
- `docs/research_runtime/EVIDENCE_DRAFT.md`
- `docs/research_runtime/REFERENCE_HANDOFF.md`
- `docs/research_runtime/CLI.md`
- `docs/research_runtime/CACHE_AND_ARTIFACTS.md`

Safety boundaries are unchanged: local-first execution; accepted
DatasetVersion-only consumption via `resolve_dataset_version`; no raw-provider
access; no external provider calls; `available_ts` / `label_available_ts`
discipline with no label-as-feature path; no centered or future live feature
windows; no same-bar optimistic signal-probe fills; no locked-test use without
governance contamination metadata; failed, inconclusive, and blocked runs stay
visible through structured reasons; no broker, live, paper, order, or account
scope; bounded grids, no-lookahead audits, and decision states are not
promotion; descriptive non-promotional reports only; and no alpha, tradability,
profitability, strategy, backtest, portfolio, or production-readiness claim. The
`EvidenceDraft` is an evidence input only, not a candidate, not Reference
validation, not Reference truth, and not alpha/tradability/profitability. A
`ReferenceCandidateHandoff` is a handoff only, not Reference validation, not
Reference truth, not strategy validation, and not a promotional or trading
claim. Runtime cache and artifact policy remains local-only and
orchestration-only: derived caches stay out of commit-eligible source paths,
heavy and value-bearing outputs are never commit-eligible, and curated summary
commit eligibility is row-free and descriptive. The `alpha runtime` CLI
remains local-only and CI-safe: help and argument-validation paths perform no
provider, network, broker, live, paper, or heavy work. The Research Runtime
campaign is the executable research loop layer over the completed Feature/Label
substrate; it is not Agent Factory, alpha search, factor promotion, Strategy
Reference Validation, or a Portfolio AlphaBook.

`ALPHA_FEATURE_LABEL_FOUNDATION_V1` is complete. `FLF-P31` records the Workflow 2
acceptance audit and closeout with a `COMPLETE_WITH_WARNINGS` verdict after clean
full-suite validation on HEAD `9b2a0b3` (`2120 passed`, all canaries pass, clean
artifact audit). All 32 phases (`FLF-P00` through `FLF-P31`) are accounted for;
`FLF-P00` through `FLF-P30` are merged (PRs #112–#144) and `FLF-P31` is the
closeout recorded in `campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/CLOSEOUT.md`.
The next separately authorized campaign may consume the completed substrate after
coordinator authorization; this repository still makes no alpha, tradability,
profitability, broker, paper, live, order, account, strategy, backtest,
portfolio, or production-readiness result.

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

`FLF-P12` adds the additive Liquidity Sweep / Structure Primitive feature
family package `alpha_system.features.families.structure`, scoped synthetic
fixture tests, family config placeholders, and:

- `docs/feature_label_foundation/features/structure.md`

`FLF-P13` adds the local-only feature materialization engine
`alpha_system.features.engine`, scoped synthetic tests, and:

- `docs/feature_label_foundation/FEATURE_MATERIALIZATION.md`

`FLF-P14` adds the local-only FeatureStore / FeatureRegistry integration in
`alpha_system.features.store` and `alpha_system.features.registry`, scoped
synthetic temp-DB tests, and:

- `docs/feature_label_foundation/FEATURE_STORE.md`

`FLF-P15` adds descriptive feature quality and coverage reports in
`alpha_system.features.reports`, the plain-text `FeatureCard` renderer in
`alpha_system.reports.feature_card`, scoped fail-closed synthetic tests, and:

- `docs/feature_label_foundation/FEATURE_REPORTS.md`

`FLF-P16` adds immutable label-layer contract objects in
`alpha_system.labels.version`, additive label-family contract wiring in
`alpha_system.labels.families`, scoped fail-closed label contract tests, and:

- `docs/feature_label_foundation/LABEL_CONTRACTS.md`

`FLF-P17` adds the additive Fixed-Horizon / Forward-Return label family package
`alpha_system.labels.families.fixed_horizon`, scoped synthetic fixture tests,
family config placeholders, and:

- `docs/feature_label_foundation/labels/fixed_horizon.md`

`FLF-P18` adds the additive Cost-Adjusted / Spread-Adjusted label family
package `alpha_system.labels.families.cost_adjusted`, scoped synthetic fixture
tests, family config placeholders, and:

- `docs/feature_label_foundation/labels/cost_adjusted.md`

`FLF-P19` adds the additive path label family package
`alpha_system.labels.families.path` for MFE, MAE, target-before-stop, and
triple-barrier labels, scoped synthetic fixture tests, family config
placeholders, and:

- `docs/feature_label_foundation/labels/path.md`

`FLF-P20` adds the additive strategy-agnostic event label family package
`alpha_system.labels.families.event` for breakout, VWAP-return, sweep-outcome,
and future-liquidity-quality event labels, scoped synthetic fixture tests,
family config placeholders, and:

- `docs/feature_label_foundation/labels/event.md`

`FLF-P21` adds the local-only label materialization engine
`alpha_system.labels.engine`, scoped synthetic unit and integration tests, and:

- `docs/feature_label_foundation/LABEL_MATERIALIZATION.md`

`FLF-P22` adds the local-only LabelStore / LabelRegistry integration in
`alpha_system.labels.registry`, scoped synthetic temp-DB tests, and:

- `docs/feature_label_foundation/LABEL_STORE.md`

`FLF-P23` adds the label leakage and availability audit layer
`alpha_system.labels.leakage_audit`, scoped no-lookahead/fail-closed tests, and:

- `docs/feature_label_foundation/LABEL_LEAKAGE_AUDIT.md`

`FLF-P24` adds the descriptive Feature/Label diagnostics module
`alpha_system.research.feature_label_diagnostics`, scoped synthetic report tests,
and:

- `docs/feature_label_foundation/diagnostics.md`

`FLF-P25` adds tiny deterministic synthetic fixtures under
`tests/fixtures/feature_label/`, the cross-cutting fail-closed suite under
`tests/no_lookahead/feature_label/`, illustrative example configs under
`configs/features/examples/` and `configs/labels/examples/`, and:

- `docs/feature_label_foundation/fixtures.md`

`FLF-P26` adds the small real DatasetVersion dry-run documentation and the
provider-neutral dry-run helper under `alpha_system.features.engine`, with a
CI-safe synthetic integration test under `tests/integration/feature_label/`.

- `docs/feature_label_foundation/DRY_RUN_DATABENTO.md`

`FLF-P27` adds the additive StudySpec input-pack helper
`alpha_system.governance.study_input_pack`, a synthetic input-pack template, and
governance integration docs.

- `docs/feature_label_foundation/governance_integration.md`

`FLF-P28` adds the local-only Feature/Label CLI surface:
`alpha feature list|plan|materialize --dry-run|report|duplicate-audit` and
`alpha label list|plan|materialize --dry-run|report|leakage-audit|input-pack`.
It also updates:

- `docs/CLI_REFERENCE.md`

`FLF-P29` adds durable Feature/Label Foundation researcher and agent docs plus
request templates for FeatureRequest, FeatureSpec, and LabelSpec workflows.

- `docs/feature_label_foundation/guide/`
- `docs/feature_label_foundation/AGENT_GUIDE.md`
- `docs/feature_label_foundation/templates/`
- `templates/feature_label/`

`FLF-P30` adds the end-to-end Feature/Label dry-run summary and CI-safe
integration test for the governed local-only path from FeatureRequest through
StudySpec Input Pack validation.

- `docs/feature_label_foundation/E2E_DRY_RUN.md`
- `tests/integration/feature_label/test_e2e_dryrun.py`

`FLF-P31` records the final Workflow 2 acceptance audit and campaign closeout
(`COMPLETE_WITH_WARNINGS`), the durable closeout notes, and this README snapshot.

- `campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/CLOSEOUT.md`
- `docs/feature_label_foundation/CLOSEOUT_NOTES.md`
- `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P31/`
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P31.md`

Safety boundaries are unchanged: local-only values; accepted DatasetVersions
only; materialized outputs stay under `ALPHA_DATA_ROOT`; no raw provider access;
no external provider calls; no label-as-feature path; no silent BBO forward-fill
or interpolation; no synthetic no-trade row is treated as a trade bar; feature
and label values remain local-only; report bundles and registry DBs remain
local-only and uncommitted; governance is consumed, not duplicated; no broker,
live, paper, order, or account scope; and no alpha, tradability, or
profitability claims.

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

## Feature/Label Foundation Snapshot

`ALPHA_FEATURE_LABEL_FOUNDATION_V1` is implemented through `FLF-P31` with a
`COMPLETE_WITH_WARNINGS` closeout on HEAD `9b2a0b3` (all 32 phases accounted for;
`FLF-P00` through `FLF-P30` merged). Durable modules now include feature request
gating, feature contracts, feature families, feature materialization and registry
integration, feature reports, label contracts, label families, label
materialization, the local-only LabelRegistry in `alpha_system.labels.registry`,
label leakage and availability audits in `alpha_system.labels.leakage_audit`,
descriptive Feature/Label diagnostics in
`alpha_system.research.feature_label_diagnostics`, synthetic fixture and
fail-closed coverage, the small accepted-DatasetVersion dry-run helper in
`alpha_system.features.engine`, the StudySpec input-pack helper in
`alpha_system.governance.study_input_pack`, and the local-only `alpha feature`
/ `alpha label` CLI groups. Durable docs now include the Feature/Label
Foundation researcher guide, agent guide, request templates, row-free end-to-end
dry-run summary, final closeout, and closeout notes. FLF-P28 updates
`docs/CLI_REFERENCE.md`; FLF-P30 adds the CI-safe end-to-end dry-run test under
`tests/integration/feature_label/`. The next separately authorized campaign can
consume the substrate after coordinator authorization; the completed
data-foundation baseline remains unchanged.

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

## Data Foundation Source Of Truth

The completed data-foundation campaign contract bundle lives under
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
- Commit-eligible Research Runtime handoffs live under
  `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/**`.

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
campaign policy allows them. Commit-eligible phase handoffs for the active
Research Runtime campaign belong under `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/`.

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

Research-runtime docs:

- `docs/research_runtime/README.md`
- `docs/research_runtime/OVERVIEW.md`

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
