# Changelog

All notable changes to `alpha_system` are recorded here.

## Unreleased — PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1

### Added

- `FEATURE_LABEL_PARQUET_SINK_V1`: research-scale Parquet value sink + reader via a shared
  `core/value_store.py` (`ValueStoreFormat` jsonl/parquet/dual, `ValueStoreHandle`,
  Polars-guarded `write_parquet_values`/`load_parquet_values`, sidecar manifest +
  content-hash idempotency). Feature/label materialization and the
  `alpha feature|label materialize --value-store {jsonl,parquet,dual}` operator (default
  `dual`) write Parquet alongside the preserved JSONL audit/small tier. Registries record
  `value_store_format`, `parquet_path`, `value_content_hash`, `value_schema_version`
  (backward-compatible `ALTER TABLE` backfill); registries stay metadata-only.
- `SESSION_LABEL_GUARD_FIX_V1`: role-aware no-lookahead/leakage guard
  (`FieldRole`, `SESSION_METADATA_FIELDS`, `FORBIDDEN_FUTURE_FIELDS`) that exempts canonical
  point-in-time `session_label`/session-context fields only when declared `SESSION_METADATA`
  via `FeatureInputSpec.input_metadata.field_roles`; true labels and forward-looking fields
  stay blocked. OHLCV `rth_flag`/`eth_flag`/`session_minute` now declare that role.
  See `docs/research_runtime/SESSION_LABEL_GUARD.md`.
- Real local smoke (local-only) materialized Parquet-backed session-context features +
  `fwd_ret_5m` label; runtime smoke PASS; Agent Factory preflight PREFLIGHT_PASS on all four
  gates (`preflight.toml` flags flipped). Horizon/session-segment research policy documented
  (5–30m primary starting horizon; flat before daily maintenance/trade-date break;
  ETH/RTH/pre_RTH/post_RTH in-scope with session-segment diagnostics + thin-session cost
  stress). No values, registries, or Parquet/JSONL committed.

## Unreleased — POST_RUNTIME_FEATURE_LABEL_STORAGE_AND_SEED_PACKS_V1

### Added

- ADR-0006 codifying the two-tier feature/label value-storage policy
  (JSONL audit/small tier now; Parquet research-scale tier deferred to
  `FEATURE_LABEL_PARQUET_SINK_V1`), with doc reconciliations and a
  `RESEARCH_RESOLUTION.md` contract for how research resolves features/labels.
- Dependency-guarded canonical-Parquet → bar-rows loader
  (`data/foundation/canonical_loader.py`).
- Generic governed seed FeaturePack/LabelPack operator (`cli/seed_pack.py`)
  plus `alpha feature|label materialize --execute` (default remains dry-run),
  and `configs/seed_packs/` seed configs.
- First real local seed packs materialized + registered from accepted Databento
  canonical ES 2024 data; Research Runtime real-data smoke now PASSES against
  registered packs (local-only; no values or registries committed).

### Notes

- Backlog: `FEATURE_LABEL_PARQUET_SINK_V1` (§4) and the dataset-registry
  reports gap (§5). Session-context features deferred pending a runtime
  leakage-guard `session_label` false-positive fix.

## 0.1.0 — ALPHA_SYSTEM_V1 foundation closeout

Status: executor-complete with warnings on deterministic fixtures.

### Added

- Local-first research harness with repository-native campaign, spec, review, handoff, and run
  contracts.
- Core contracts and timestamp semantics for point-in-time research workflows.
- Canonical 1-minute data contracts and deterministic fixture validation.
- Factor specification, registry, compute, diagnostics, and report surfaces.
- Label generation with explicit availability semantics.
- Signal and strategy contracts that keep research layers separated from execution simulation.
- Tier 1 reference 1-minute backtest truth with conservative timing and accounting semantics.
- Explicit cost and slippage semantics for reference-engine fixture validation.
- Management, portfolio sizing, bounded grids, ML MVP, and multi-symbol fixture coverage.
- Design-only L2 readiness schema.
- Review bundle and closeout artifacts for the ALPHA_SYSTEM_V1 foundation.

### Validation

- Fixture-only end-to-end validation through ASV1-P29.
- Executor recommendation: `COMPLETE_WITH_WARNINGS`.
- No market data validation was performed.
- No alpha, profitability, robustness, tradability, paper/live, broker, or deployment claim is
  made.

### Known warnings

- Formal validation, Claude review, semantic done-check, PR, CI, and merge gates remain separate
  from the executor recommendation.
- CLI/package smoke requires a clean local environment and package importability.
- Generated artifacts, local DBs, raw/canonical data, factor/label materializations, logs,
  caches, and run-local files remain local-only.

## Unreleased

- `ALPHA_RESEARCH_GOVERNANCE_MVP` closeout is present with verdict
  `COMPLETE_WITH_WARNINGS`.
- `ALPHA_DATA_FOUNDATION_V1` closeout is present with verdict
  `COMPLETE_WITH_WARNINGS` and `25/25` phases passing.
- Post-closeout ADF1 Task 1A/1B added the read-only IBKR connector,
  resumable backfill/materialize path, and first real local-only
  DatasetVersion `dsv_ibkr_es_nq_rty_eth_20260603_v1`.
- Post-closeout ADF1 Databento track added the primary deep-history research
  source: Phase B (PR #107) pulled, canonicalized (sparse provider truth plus a
  derived dense research grid), quality/coverage-gated, and registered 27
  local-only Databento DatasetVersions for GLBX.MDP3 ES/NQ/RTY OHLCV-1m + BBO-1m
  (2018–2026), kept separate from the IBKR DatasetVersions. No raw or heavy data
  is committed; no alpha/tradability/profitability/paper/live/broker claim is made.
- Next intended macro-campaign: `ALPHA_FEATURE_LABEL_FOUNDATION_V1`.
