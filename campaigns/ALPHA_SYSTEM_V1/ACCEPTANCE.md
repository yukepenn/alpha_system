
# ALPHA_SYSTEM_V1 Acceptance Criteria

## Acceptance Philosophy

`ALPHA_SYSTEM_V1` is accepted only when the repository contains a functioning, test-backed, reviewable, local-first v0.1 foundation for an Alpha Research Platform.

Acceptance is based on semantic completeness, domain correctness, no-lookahead protections, artifact discipline, reproducibility, review evidence, and Frontier Harness Workflow 2 compliance.

Passing tests alone is not sufficient.

The campaign must not be accepted if any of the following are true:

* raw data is committed,
* heavy artifacts are committed,
* local SQLite databases are committed,
* broker/live trading is introduced,
* paper trading is introduced,
* order routing is introduced,
* production execution adapters are introduced,
* alpha/tradability claims are made without evidence and review context,
* test weakening or gaming is detected,
* failed runs are hidden,
* fast path creates separate PnL truth,
* reference backtest truth is ambiguous,
* candidate promotion can occur without review,
* no-lookahead invariants are knowingly broken,
* phases are marked done without required handoffs,
* Yellow phases are merged without fresh Claude review,
* Red operations are executed without required scoped authorization,
* generated local-only artifacts are committed as proof of success.

A truthful `BLOCKED` verdict is acceptable. A false `COMPLETE` verdict is not acceptable.

## Campaign-Level Acceptance Criteria

The campaign is accepted when all of the following are true:

1. `ACTIVE_CAMPAIGN.md` identifies `ALPHA_SYSTEM_V1` as the active campaign or records its completion status.
2. `campaigns/ALPHA_SYSTEM_V1/GOAL.md` exists and defines the campaign objective, non-goals, architecture principles, local-first stack, Workflow 2 assumptions, success definition, and final outcome.
3. `campaigns/ALPHA_SYSTEM_V1/ACCEPTANCE.md` exists and defines campaign-level, layer-level, release-validation, and semantic done-check acceptance gates.
4. Later campaign control files are generated before execution proceeds beyond Prompt 1, including:

   * `campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md`
   * `campaigns/ALPHA_SYSTEM_V1/campaign.yaml`
   * `campaigns/ALPHA_SYSTEM_V1/RISK_REGISTER.md`
   * `campaigns/ALPHA_SYSTEM_V1/RUNBOOK.md`
5. All phases defined in the eventual phase plan are complete, or any non-complete phase is explicitly marked `BLOCKED` with a clear blocked handoff and no false completion.
6. Every executed phase has:

   * generated spec,
   * executor prompt,
   * executor notes,
   * checks result,
   * handoff,
   * review when required,
   * parsed verdict,
   * merge/done-check result.
7. All Yellow phases have fresh Claude review.
8. Every merged phase has `PASS` or `PASS_WITH_WARNINGS` where review is required.
9. Every run has visible run artifacts and a run summary.
10. All required local checks pass, or unavailable checks are explicitly documented with a non-blocking reason.
11. Artifact policy audit is clean.
12. No raw data, canonical data, factor values, label values, caches, local DBs, logs, or heavy artifacts are committed outside explicit tiny fixtures.
13. No `git add .` or `git add -A` usage is recorded as part of staging.
14. No broker, paper trading, live trading, order routing, or production execution adapter is introduced.
15. No alpha, profitability, robustness, or tradability claim appears in docs, reports, examples, summaries, or templates without evidence and review context.
16. The repository remains local-first and does not require cloud storage, paid databases, database servers, Ray, MLflow server, Dagster, Prefect, or web UI.
17. Semantic done-check confirms the platform is an Alpha Research Platform foundation, not merely a backtester.
18. Final closeout documents known limitations and next-campaign candidates.
19. The final verdict is one of:

* `COMPLETE`
* `COMPLETE_WITH_WARNINGS`
* `BLOCKED`

## Layer Acceptance Criteria

## 1. Harness and Repository Layer

Accepted when:

* `AGENTS.md` exists.
* `CLAUDE.md` exists.
* `frontier.yaml` exists.
* `ACTIVE_CAMPAIGN.md` exists.
* `README.md` exists.
* `PROJECT_STATUS.md` exists.
* `campaigns/ALPHA_SYSTEM_V1/` contains:

  * `GOAL.md`
  * `PHASE_PLAN.md`
  * `campaign.yaml`
  * `ACCEPTANCE.md`
  * `RISK_REGISTER.md`
  * `RUNBOOK.md`
* Repo path policy requires `~/projects/alpha_system` under the WSL2 Linux filesystem.
* Active worktree paths under `/mnt/c`, OneDrive, Windows-synced folders, network drives, and temporary directories are forbidden.
* `.gitignore` protects:

  * `data/raw/`
  * `data/canonical/`
  * `data/factors/`
  * `data/labels/`
  * `data/cache/`
  * `metadata/*.sqlite`
  * `metadata/*.db`
  * generated artifacts
  * logs
  * caches
  * temporary outputs
  * local model artifacts
* Explicit staging policy is documented:

  * never `git add .`
  * never `git add -A`
  * stage curated files only
* Workflow 2 state machine is documented and represented in control files.
* STOP file behavior is documented.
* Handoff, review, run-output, and repair-attempt paths are documented.
* Green, Yellow, and Red lane policy is documented.
* Green and Yellow auto PR / auto merge are allowed only when lane gates pass.
* Red is described as pre-authorized automatic when scoped and authorized, not banned, but not expected in this campaign.
* Broker/live trading is explicitly out of scope.

Not accepted if:

* active worktree policy permits `/mnt/c` or OneDrive execution,
* raw/heavy artifact commit rules are absent,
* Yellow phase review requirements are omitted,
* automatic merge does not require checks and artifact policy,
* STOP handling is missing,
* `git add .` or `git add -A` is permitted,
* Red operations can run without scoped authorization variables,
* broker/live trading is listed as a campaign objective.

## 2. Data Contracts Layer

Accepted when contracts exist and tests verify required fields for the following.

### Instrument Master

Required fields:

* `instrument_id`
* `symbol`
* `asset_class`
* `exchange`
* `currency`
* `timezone`
* `tick_size`
* `lot_size`
* `multiplier`
* `start_date`
* `end_date`
* `corporate_action_policy`
* `metadata`

### Trading Calendar / Session

Required fields:

* `calendar_id`
* `trading_date`
* `session_id`
* `open_ts`
* `close_ts`
* `is_holiday`
* `is_half_day`
* `session_type`
* `timezone`
* `quality_flags`

### 1-Minute Bars

Required fields:

* `instrument_id`
* `session_id`
* `bar_index`
* `bar_start_ts`
* `bar_end_ts`
* `event_ts`
* `available_ts`
* `open`
* `high`
* `low`
* `close`
* `volume`
* `vwap`
* `trade_count`
* `bid`
* `ask`
* `spread`
* `source_version`
* `data_version`
* `quality_flags`

Accepted when no-lookahead rules are represented and tested:

* completed 1-minute bar can only be used after `bar_end_ts` plus configured latency,
* signals based on bar `t` cannot execute inside bar `t` by default,
* default execution is next-bar conservative,
* same-bar stop/target ambiguity is conservative,
* `available_ts` is present and ordered correctly,
* `bar_start_ts < bar_end_ts`,
* `available_ts >= bar_end_ts` plus configured latency when latency is specified.

Accepted when quote/trade readiness exists for:

* quote data,
* trade prints,
* bid/ask spread,
* future executable labels,
* future cost modeling.

Accepted when future L2 schemas are design-ready with:

* snapshot table,
* event/delta table,
* book levels,
* side,
* price,
* size,
* order count if available,
* event timestamp,
* receive timestamp,
* available timestamp,
* data version,
* quality flags.

Not accepted if:

* `available_ts` is missing,
* timestamp ordering is untested,
* 1-minute bars can be used before availability,
* quote/trade readiness is absent,
* L2 work implies an implemented replay engine in this campaign,
* data contracts assume all instruments share a single timezone/session,
* raw or canonical datasets are committed outside tiny fixtures.

## 3. Data Layer, Calendar, Session, and Quality Layer

Accepted when:

* canonical 1-minute local data validation exists,
* local fixture-compatible bar building exists,
* `alpha data validate` exists,
* `alpha data build-bars` exists,
* data validation checks required fields,
* data validation checks timestamp ordering,
* data validation checks duplicate bars,
* data validation checks null handling,
* data validation checks data version presence,
* data validation checks `available_ts`,
* data validation checks OHLC sanity,
* data validation checks negative volume,
* data validation checks spread consistency,
* calendar/session assignment exists,
* timezone conversion is tested,
* session assignment is tested,
* `bar_index` resets per session,
* half-day close handling is tested,
* holiday no-session behavior is tested,
* missing bars create quality flags,
* duplicate bars create quality flags,
* out-of-session bars create quality flags.

Not accepted if:

* the data layer requires cloud storage,
* the data layer requires a data vendor integration,
* calendar logic ignores exchange timezone,
* half-days are treated as full sessions,
* generated local data is committed outside tiny fixtures.

## 4. Metadata Registry Layer

Accepted when:

* SQLite is the local metadata registry.
* No database server is required.
* Migrations are idempotent and tested in temporary DBs.
* No `.sqlite` or `.db` file is committed.
* The following tables exist and are tested:

  * `dataset_versions`
  * `factor_registry`
  * `factor_versions`
  * `factor_validation_runs`
  * `label_versions`
  * `study_runs`
  * `strategy_registry`
  * `strategy_versions`
  * `grid_runs`
  * `ml_runs`
  * `backtest_runs`
  * `artifact_manifest`
  * `promotion_decisions`
* Every run record supports:

  * run id,
  * timestamp,
  * git commit,
  * code hash,
  * config hash,
  * data version,
  * factor versions,
  * label versions,
  * engine version,
  * parameters,
  * artifact paths,
  * decision status.
* `alpha registry status` exists and reports:

  * registry location,
  * migration status,
  * table status,
  * whether the active DB is local-only.

Not accepted if:

* registry requires PostgreSQL, MySQL, ClickHouse, QuestDB, ArcticDB, DolphinDB, or kdb+,
* run records omit hashes,
* run records omit data/factor/label versions,
* promotion decisions are not represented,
* failed runs cannot be recorded,
* local SQLite DB files are committed.

## 5. Reproducibility and Artifact Manifest Layer

Accepted when:

* run manifest model exists,
* artifact manifest model exists,
* deterministic config hashing exists,
* code hash utility exists,
* git commit and dirty-tree detection exist,
* run manifests record:

  * run id,
  * command or phase name,
  * timestamp,
  * git commit,
  * dirty tree indicator,
  * code hash,
  * config hash,
  * data version,
  * factor versions,
  * label versions,
  * engine version,
  * parameters,
  * artifact paths,
  * decision status,
  * warnings,
  * failed-step visibility.
* artifact manifests reject forbidden committed paths,
* failed runs can be represented,
* reproducibility audit detects missing hashes and missing version references.

Not accepted if:

* failed run manifests can be silently omitted,
* dirty-tree state is ignored,
* artifact paths can point to forbidden committed locations,
* generated local-only artifacts are committed as proof of reproducibility.

## 6. Factor Registry Layer

Accepted when:

* `FactorSpec` exists and includes:

  * `factor_id`
  * `name`
  * `version`
  * `owner`
  * `description`
  * `input_fields`
  * `parameters`
  * `frequency`
  * `warmup_bars`
  * `session_reset`
  * `availability_lag`
  * `factor_type`
  * `evaluation_type`
  * `code_hash`
  * `config_hash`
  * `status`
  * `created_at`
  * `validation_artifact_path`
* Factor lifecycle is enforced:

  * `draft`
  * `candidate`
  * `validated`
  * `approved`
  * `deprecated`
* Draft factor values are not permanently materialized by default.
* Factor registration records code and config hashes.
* Factor versions are unique and reproducible.
* Promotion to `approved` requires review and promotion decision.
* Deprecated factors remain queryable for reproducibility.
* `alpha factor validate` exists.
* `alpha factor materialize` exists and enforces lifecycle/materialization controls.

Not accepted if:

* draft factors can be materialized by default,
* label values can be used as factor inputs,
* approval can occur without review,
* computed factor stores are committed,
* lifecycle transitions are not tested,
* deprecated factors disappear in a way that breaks reproducibility.

## 7. Factor Compute Layer

Accepted when:

* factor compute SDK exists,
* deterministic factor computation works on tiny fixtures,
* factor dependency validation exists,
* warmup behavior is represented and tested,
* session reset behavior is represented and tested,
* availability lag behavior is represented and tested,
* quality flag propagation exists,
* factor value schema exists with:

  * `factor_id`
  * `factor_version`
  * `instrument_id`
  * `event_ts`
  * `available_ts`
  * `session_id`
  * `bar_index`
  * `value`
  * `normalized_value`
  * `quality_flags`
  * `data_version`
  * `compute_version`
* materialization command writes only to local-only factor store unless using tiny fixtures,
* materialization records registry metadata in temp/local DBs.

Not accepted if:

* labels can be factor inputs,
* warmup bars are ignored,
* factors carry state across sessions when `session_reset` requires reset,
* `availability_lag` is ignored,
* factor Parquet outputs are committed outside tiny fixtures.

## 8. Label Store Layer

Accepted when:

* label schema exists with:

  * `label_id`
  * `instrument_id`
  * `event_ts`
  * `horizon`
  * `label_type`
  * `value`
  * `path_metadata`
  * `data_version`
  * `label_available_ts`
* Standard labels are represented:

  * forward return 1m,
  * forward return 3m,
  * forward return 5m,
  * forward return 10m,
  * forward return 30m,
  * MFE by horizon,
  * MAE by horizon,
  * target-before-stop,
  * stop-before-target,
  * future realized volatility,
  * future spread/liquidity labels.
* Label generation/alignment works on deterministic fixtures.
* `label_available_ts` is after required future information.
* Labels are versioned in registry.
* Tests cover session boundaries.
* Tests cover half-days.
* Labels cannot be consumed as live factor inputs.
* Labels cannot be consumed as live strategy inputs.

Not accepted if:

* labels leak into features,
* labels are available before their horizon completes,
* generated label stores are committed outside tiny fixtures,
* session close is ignored for forward horizons,
* MFE/MAE path metadata is missing.

## 9. Factor Diagnostics Layer

Accepted when diagnostics exist and are tested for the following.

### Directional Continuous Factors

* Pearson IC
* Rank IC
* IC by horizon
* IC decay
* IC by day/week/month
* ICIR
* bucket monotonicity

### Nonlinear Bucket Factors

* bucket forward returns
* tail expectancy
* U-shape profile
* extreme bucket hit rate
* MFE/MAE by bucket

### Event Trigger Factors

* event study
* conditional forward returns
* sample size
* false breakout rate
* target-before-stop probability
* post-event MFE/MAE

### Regime Filters

* with-filter vs without-filter uplift
* coverage
* false rejection rate
* conditional strategy improvement

### Execution Filters

* spread sensitivity
* liquidity sensitivity
* slippage sensitivity
* volume participation
* adverse selection proxy

### Management Features

* target-before-stop
* time-to-target
* time-to-stop
* breakeven usefulness
* trailing stop usefulness

Accepted when:

* `alpha study run` exists,
* study runs record reproducibility metadata,
* diagnostics include sample size,
* diagnostics include warnings,
* diagnostics validate factor/label version alignment,
* diagnostics validate label availability,
* diagnostics do not emit tradability claims.

Not accepted if:

* diagnostics omit sample size,
* diagnostics imply tradability,
* diagnostics use labels before availability,
* diagnostics are treated as strategy PnL truth,
* full study outputs are committed.

## 10. Factor Reporting Layer

Accepted when factor cards and study reports include:

* time-of-day stability,
* session segment stability,
* monthly stability,
* volatility regime stability,
* liquidity regime stability,
* correlation to existing factors,
* factor cluster id,
* promotion recommendation,
* sample size,
* warnings,
* data version,
* factor version,
* label version,
* run manifest path,
* no-lookahead validation status,
* review status.

Accepted promotion recommendations are limited to:

* `reject`
* `needs_more_data`
* `candidate_for_strategy_test`
* `candidate_for_review`
* `do_not_promote`

Not accepted if report text claims:

* profitable,
* tradable,
* production-ready,
* guaranteed alpha,
* market-beating,
* robust without evidence,
* approved without review.

Not accepted if:

* reports automatically approve candidates,
* reports hide insufficient sample warnings,
* full report bundles are committed,
* report templates include performance-marketing language.

## 11. Strategy and Signal API Layer

Accepted when:

* Signal store exists.
* StrategySpec exists.
* Strategies produce:

  * entry signal,
  * exit signal,
  * direction,
  * optional confidence score,
  * optional desired exposure,
  * required factor dependencies.
* Strategies do not directly handle:

  * account equity,
  * position sizing,
  * fills,
  * order lifecycle,
  * slippage,
  * commission,
  * partial take-profit accounting,
  * portfolio aggregation.
* Strategy versions are registry-backed.
* Strategy tests verify dependencies.
* Strategy tests verify no label leakage.
* Signal timestamps respect `available_ts`.
* Template strategy output is deterministic on fixtures.

Not accepted if:

* strategy code includes fills,
* strategy code includes slippage,
* strategy code includes commission,
* strategy code includes account equity,
* strategies read raw ad hoc columns without declared dependencies,
* strategies read label values as live inputs,
* generated signal stores are committed.

## 12. Reference Backtest Truth Layer

Accepted when:

* Tier 1 reference 1-minute bar execution truth exists.
* Reference engine is documented as canonical PnL truth.
* Default execution is next-bar conservative.
* Data latency and `available_ts` are enforced.
* Same-bar stop/target ambiguity is conservative.
* Trade journal output schema is defined.
* Equity output schema is defined.
* Accounting is deterministic on fixtures.
* Costs/slippage hooks are integrated.
* `alpha backtest run` exists.
* Backtest runs are registry-backed in temp/local tests.
* Reference engine does not require broker or live trading dependencies.

Not accepted if:

* same-bar optimistic fills are default,
* reference engine permits signal execution before information availability,
* fast path or another engine defines conflicting PnL truth,
* full trade logs are committed,
* cost model is silently bypassed for non-test configs,
* backtest outputs claim tradability.

## 13. Cost and Slippage Layer

Accepted when cost/slippage models support and test:

* fixed commission,
* per-share/per-contract commission,
* bps cost,
* half-spread/full-spread assumptions,
* configurable slippage bps,
* spread-sensitive slippage,
* volume participation cap,
* liquidity rejection/penalty,
* adverse-selection proxy hook,
* deterministic fixture behavior.

Accepted when:

* reference backtest uses configured cost model,
* non-test default config is conservative,
* spread fields are used when present,
* docs explain limitations and no live-execution claims.

Not accepted if:

* zero-cost is silently default for non-test configs,
* spread fields are ignored when present,
* broker-specific live commission adapters are introduced,
* execution validation artifacts are committed.

## 14. Management Layer

Accepted when ManagementSpec supports and tests:

* fixed stop,
* ATR stop,
* volatility stop,
* target R multiple,
* laddered partial take profit,
* breakeven stop,
* trailing stop,
* time exit,
* EOD exit,
* max trades per day,
* cooldown,
* scale-in,
* scale-out,
* max holding bars,
* risk per trade,
* max position percent.

Accepted when:

* conservative same-bar stop/target ambiguity is tested,
* partial take-profit accounting is deterministic,
* management behavior integrates with reference engine fixtures,
* `alpha management grid` exists,
* management overfit risks are documented.

Not accepted if:

* management rules are hidden inside StrategySpec,
* partial exits are omitted from accounting,
* management grid can run unbounded,
* management outputs claim tradability,
* same-bar ambiguity defaults optimistically.

## 15. Portfolio Layer

Accepted when PortfolioSpec supports and tests:

* portfolio target,
* position sizing,
* capital allocation,
* risk limits,
* multi-symbol constraints,
* max gross exposure,
* max net exposure,
* sector/asset constraints for future,
* correlation-aware allocation for future,
* signal-to-target conversion.

Accepted when:

* fixed-risk sizing works on fixtures,
* max position percent is tested,
* insufficient capital behavior is tested,
* portfolio target output schema exists,
* reference engine integration fixture exists,
* StrategySpec remains separate from portfolio responsibilities.

Not accepted if:

* fills/slippage/commission move into portfolio layer,
* portfolio assumes single-symbol-only semantics,
* broker account sync is introduced,
* portfolio outputs claim production readiness.

## 16. Fast Path Parity Layer

Accepted when:

* NumPy/Numba fast path exists.
* Fast path is explicitly acceleration only.
* Reference path remains truth.
* Parity checker exists.
* Parity tests pass on deterministic fixtures for scoped features:

  * no trade,
  * simple long,
  * simple short if supported,
  * costs,
  * slippage,
  * fixed stop,
  * target,
  * same-bar ambiguity,
  * partial exits,
  * EOD exit,
  * cooldown,
  * max holding bars,
  * deterministic equity curve,
  * deterministic trade summary.
* Unsupported fast path features fail closed or route to reference.
* Grid engine can use fast path only after parity is certified for the selected feature set.

Not accepted if:

* reference behavior is weakened to match fast path,
* grid uses fast path without parity gate,
* fast path is described as a second truth,
* benchmark logs or large arrays are committed.

## 17. Grid Engine Layer

Accepted when:

* `alpha grid run` exists.
* Grid types are supported:

  * factor parameter grid,
  * strategy signal grid,
  * execution cost grid,
  * risk sizing grid,
  * position management grid.
* Grid discipline is enforced:

  1. Factor diagnostics first.
  2. Simple signal grid.
  3. Simple management baseline.
  4. Survivor strategy management grid.
  5. Finalist execution validation.
* Grid outputs have schemas:

  * `leaderboard.csv`
  * `grid_summary.md`
  * `monthly_breakdown.csv`
  * `cost_sensitivity.csv`
  * `top_configs.yaml`
  * `rejected_configs.csv`
  * `run_manifest.json`
* Max-combination controls are tested.
* Rejected configs are visible.
* Registry records grid runs.
* Fast path requires parity gate.
* Reference fallback exists for unsupported accelerated configurations.

Not accepted if:

* unbounded Cartesian products are allowed,
* rejected configs are hidden,
* grids rank configs as tradable/profitable without evidence,
* full grid outputs are committed,
* fast path is used without parity.

## 18. Management Grid Layer

Accepted when:

* `alpha management grid` supports bounded execution.
* Survivor workflow exists.
* Management grid only runs on eligible candidates.
* Survivor records include:

  * candidate id,
  * source run id,
  * factor versions,
  * strategy version,
  * baseline management config,
  * reason for survivor eligibility,
  * warnings,
  * review status,
  * allowed management grid scope.
* Management overfit controls are documented and tested.
* Baseline comparison output exists.
* Cost sensitivity is retained.
* Monthly breakdown is retained.
* Registry records management-grid runs.

Not accepted if:

* management grid can run on arbitrary unvalidated ideas without warning/fail,
* management grid can run unbounded,
* automatic approval occurs,
* generated management grid outputs are committed,
* survivor records omit review status.

## 19. Experiment Registry Layer

Accepted when:

* study runs can record reproducibility metadata,
* factor validation runs can record reproducibility metadata,
* strategy runs can record reproducibility metadata,
* backtest runs can record reproducibility metadata,
* grid runs can record reproducibility metadata,
* management grid runs can record reproducibility metadata,
* ML runs can record reproducibility metadata,
* failed runs can be recorded and surfaced,
* artifact manifests can be recorded and audited,
* promotion decisions require review status,
* registry audit detects missing hashes,
* registry audit detects missing data versions,
* registry audit detects missing factor versions,
* registry audit detects missing label versions,
* registry audit detects missing artifact paths.

Not accepted if:

* failed runs are hidden,
* run metadata is incomplete,
* promotion status can be changed without review trail,
* local SQLite DBs are committed.

## 20. ML MVP Layer

Accepted when:

* `FeatureSetSpec` exists.
* `LabelSpec` exists.
* `ModelSpec` exists.
* `alpha ml run` exists.
* ML consumes versioned factor versions only.
* Raw ad hoc columns are rejected.
* Label leakage is rejected.
* Train/validation split is represented and tested.
* Walk-forward split is represented and tested.
* Purge/embargo readiness is represented and tested.
* Score output schema exists.
* Score-to-portfolio conversion contract exists.
* ML run registry entries exist.
* ML artifacts are local-only unless tiny explicit fixtures are allowed.

Not accepted if:

* ML reads raw ad hoc columns,
* labels appear in feature sets,
* MLflow server is required,
* trained model binaries are committed,
* ML output claims tradability,
* future validation labels are used in training.

## 21. Multi-Symbol and Multi-Asset Readiness Layer

Accepted when:

* universe config exists,
* instrument metadata supports:

  * asset class,
  * exchange,
  * currency,
  * timezone,
  * multiplier,
  * active dates,
  * tick size,
  * lot size.
* multi-symbol session alignment is tested,
* per-symbol missing data flags are represented,
* portfolio constraints support multi-symbol gross/net limits,
* future sector/asset constraints are represented,
* registry records universe/config hash.

Not accepted if:

* all symbols are assumed to share one timezone/session,
* currency/multiplier metadata is ignored,
* core contracts are hardcoded to single-symbol operation,
* real multi-symbol datasets are committed.

## 22. L2 Readiness Layer

Accepted when:

* L2 snapshot schema exists with required fields.
* L2 delta/event schema exists with required fields.
* Event timestamp, receive timestamp, and available timestamp are distinct.
* Side, book level, price, size, order count, data version, and quality flags are represented.
* Timestamp ordering is tested.
* Side enum is tested.
* Book level validation is tested.
* Future replay requirements are documented:

  * book reconstruction,
  * queue position,
  * latency,
  * passive fills,
  * snapshot/delta consistency,
  * event ordering.
* L2-derived feature skeleton exists for synthetic fixtures.
* L2-derived features propagate `available_ts`.
* L2-derived features propagate quality flags.

Not accepted if:

* full L2 replay is implemented or claimed as complete,
* live market data connection is added,
* real L2 datasets are committed,
* L2-derived features can be used before availability,
* passive fill validation is implied to exist.

## 23. Reporting and Review Bundle Layer

Accepted when:

* `alpha report build` exists.
* Review bundles include:

  * run manifest,
  * source map,
  * config hashes,
  * code hashes,
  * data/factor/label versions,
  * registry records,
  * diagnostics summary,
  * backtest summary when applicable,
  * cost sensitivity when applicable,
  * monthly breakdown when applicable,
  * rejected configs when applicable,
  * warnings,
  * failed-step visibility,
  * promotion decision status,
  * no-lookahead validation status,
  * artifact manifest.
* Missing artifacts are visible.
* Failed runs are visible.
* Prohibited claim language is rejected.
* Review bundles are local-only unless tiny curated summaries are explicitly allowed.

Not accepted if:

* review bundles hide missing artifacts,
* report bundles imply approval/tradability,
* web server is required,
* full bundles are committed,
* source maps are absent.

## 24. Documentation and Onboarding Layer

Accepted when docs exist for:

* onboarding,
* researcher guide,
* AI Agent guide,
* CLI reference,
* example workflows,
* troubleshooting,
* artifact policy,
* no-lookahead policy,
* data contracts,
* factor lifecycle,
* label store,
* factor diagnostics,
* backtest tiers,
* reference truth,
* fast path parity,
* grid engine,
* ML layer,
* L2 readiness,
* review bundles,
* local-first stack.

Docs must explain:

* WSL2 path policy,
* no raw/heavy commits,
* no broker/live trading,
* no alpha/tradability claims without evidence,
* no candidate promotion without review,
* explicit staging only,
* no `git add .`,
* no `git add -A`,
* how to inspect registry status,
* how to build review bundles,
* how to interpret reports without overclaiming,
* how to create handoffs,
* how to avoid local artifact commits.

Not accepted if:

* docs instruct live/broker trading,
* docs omit artifact policy,
* docs overstate research results,
* docs call fixture results evidence of alpha,
* docs hide known limitations.

## Required Final Release Validation

Before closeout, the campaign must run an end-to-end deterministic local fixture validation that exercises:

1. data validation,
2. canonical 1-minute fixture bars,
3. calendar/session assignment,
4. factor validation,
5. label generation/alignment,
6. factor compute,
7. factor diagnostics,
8. factor card/report generation,
9. signal/strategy generation,
10. reference backtest,
11. cost/slippage,
12. management rules,
13. portfolio sizing,
14. fast path parity,
15. bounded grid,
16. management grid,
17. experiment registry,
18. ML MVP,
19. multi-symbol fixture if feasible,
20. L2 schema/feature fixture if feasible,
21. review bundle generation,
22. registry status.

Validation must produce a small curated summary and must not commit:

* release SQLite DB,
* generated factor values,
* generated label values,
* full grid outputs,
* full trade logs,
* full review bundle directory,
* logs,
* cache,
* raw datasets,
* canonical datasets,
* large Parquet files.

The final validation summary must clearly state:

* fixture validation is correctness validation, not market evidence,
* no live/broker scope exists,
* no alpha/tradability claim is made,
* limitations remain documented.

## Required Final Campaign Run Summary

The final run summary must include:

* campaign id,
* run id,
* repo path,
* final state,
* completed phases,
* blocked phases if any,
* checks run,
* review verdicts,
* repair attempts,
* acceptance gate results,
* artifact audit result,
* no-lookahead status,
* fast parity status,
* registry status,
* known limitations,
* next campaign candidates,
* explicit statement that broker/live trading is out of scope,
* explicit statement that no alpha/tradability claims are made,
* explicit statement that raw/heavy/local artifacts are absent from commits,
* final recommendation:

  * `COMPLETE`,
  * `COMPLETE_WITH_WARNINGS`,
  * or `BLOCKED`.

## Required Semantic Done-Check

The final semantic done-check must answer yes/no with evidence for:

1. Is this an Alpha Research Platform foundation, not merely a backtester?
2. Are data/factor/label/signal/strategy/management/portfolio/execution boundaries enforced?
3. Is the reference engine the single PnL truth?
4. Is fast path acceleration only?
5. Are no-lookahead rules represented and tested?
6. Are `available_ts` and `label_available_ts` enforced?
7. Are draft factors prevented from default long-term materialization?
8. Does candidate promotion require review?
9. Are registry records reproducible?
10. Are failed runs visible?
11. Are rejected grid configurations visible?
12. Are grid and management-grid searches bounded?
13. Does ML consume versioned factors only?
14. Are raw ad hoc ML columns rejected?
15. Is L2 readiness design-only?
16. Are artifact policies enforced?
17. Are raw/heavy/local artifacts absent from commits?
18. Is broker/live trading absent?
19. Are alpha/tradability claims absent unless evidence-backed and reviewed?
20. Are docs and onboarding sufficient for human and AI Agent workflows?
21. Are all Yellow phases reviewed?
22. Are all run artifacts and handoffs present?
23. Are test weakening and gaming absent?
24. Are remaining risks documented in `KNOWN_LIMITATIONS.md` or final closeout?
25. Is any blocked work truthfully recorded rather than marked complete?

## Prohibited Acceptance Shortcuts

The campaign must not be accepted by any of the following shortcuts:

* “Tests pass” without semantic review.
* Skipping Claude review for Yellow phases.
* Committing generated local artifacts to demonstrate success.
* Removing tests instead of fixing failures.
* Weakening no-lookahead assertions.
* Weakening artifact policy checks.
* Marking blocked phases complete.
* Ignoring dirty tree or unstaged generated outputs.
* Treating fast path as equivalent to reference without parity.
* Treating factor diagnostics as proof of tradability.
* Treating fixture results as market evidence.
* Approving candidates automatically.
* Using real raw data in the repository.
* Relying on cloud infrastructure.
* Requiring external paid databases.
* Introducing broker/live trading and calling it optional.
* Hiding failed runs or rejected configs.
* Omitting handoffs.
* Omitting run summaries.
* Omitting known limitations.
* Allowing multiple conflicting PnL truths.
* Accepting incomplete registry reproducibility fields.

## Required Artifact Audit

Final artifact audit must verify that committed files do not include:

* `data/raw/**` except allowed `.gitkeep`,
* `data/canonical/**` except allowed `.gitkeep`,
* `data/factors/**` except allowed `.gitkeep`,
* `data/labels/**` except allowed `.gitkeep`,
* `data/cache/**` except allowed `.gitkeep`,
* `metadata/*.sqlite`,
* `metadata/*.db`,
* generated files under `artifacts/**` except allowed `.gitkeep` or explicitly curated tiny summaries,
* large Parquet files,
* large CSVs,
* generated logs,
* generated benchmark outputs,
* generated full trade logs,
* generated full grid outputs,
* generated review bundles,
* local ML model binaries,
* cache directories.

Final artifact audit must also verify that committed fixture data is:

* tiny,
* deterministic,
* explicitly under test fixture paths,
* documented as correctness fixtures only,
* not represented as market evidence.

## Required Review Evidence

The campaign must preserve review evidence showing:

* each Yellow phase received fresh Claude review,
* each required review produced a verdict,
* only `PASS` or `PASS_WITH_WARNINGS` phases were merged,
* any `REWORK` phase entered repair loop,
* any `BLOCKED` phase produced blocked handoff,
* warnings were recorded and either resolved or accepted as limitations,
* semantic done-check was not replaced by tests alone.

## Required Final Closeout Documents

Final closeout must include or update:

* `PROJECT_STATUS.md`
* `docs/V0_1_RELEASE_NOTES.md`
* `docs/KNOWN_LIMITATIONS.md`
* `docs/NEXT_CAMPAIGN_CANDIDATES.md`
* `campaigns/ALPHA_SYSTEM_V1/CLOSEOUT.md`
* final handoff under `handoffs/`
* final review under `reviews/`
* final `runs/<run_id>/RUN_SUMMARY.md`

Closeout must explicitly state:

* whether the campaign is `COMPLETE`, `COMPLETE_WITH_WARNINGS`, or `BLOCKED`,
* which acceptance gates passed,
* which warnings remain,
* which future capabilities are deferred,
* that broker/live trading remains out of scope,
* that no alpha/tradability claims are made.

## Final Acceptance Verdicts

Allowed final campaign verdicts:

### `COMPLETE`

Allowed only when:

* all acceptance gates pass,
* no material warnings remain,
* no blocked phases remain,
* artifact audit is clean,
* all required reviews exist,
* semantic done-check passes.

### `COMPLETE_WITH_WARNINGS`

Allowed only when:

* acceptance gates pass,
* known limitations are documented,
* warnings do not violate non-negotiable principles,
* no blocked required acceptance gate remains,
* artifact audit is clean,
* semantic done-check passes.

### `BLOCKED`

Required when:

* one or more required acceptance gates fail,
* a non-negotiable principle is violated,
* a required phase cannot complete,
* artifact integrity is compromised,
* review integrity is compromised,
* no-lookahead integrity is compromised,
* execution truth is ambiguous,
* broker/live scope is introduced,
* test weakening/gaming is detected,
* failed runs are hidden,
* required review is missing.

A `BLOCKED` verdict is acceptable and honest. A false `COMPLETE` verdict is not acceptable.
