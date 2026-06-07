# Handoff — PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1

## Status

**COMPLETE (PASS).** Both data-access blockers for `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
are landed and verified on real local data:

1. **FEATURE_LABEL_PARQUET_SINK_V1** — research-scale Parquet value sink + reader for
   feature and label value records, alongside the preserved JSONL audit/small tier.
2. **SESSION_LABEL_GUARD_FIX_V1** — the no-lookahead/leakage guard no longer
   false-positives on the canonical point-in-time `session_label` field; session-context
   features (`rth_flag`, `eth_flag`, `session_minute`) now materialize and resolve, while
   true labels and forward-looking fields remain blocked.

Workflow 1: Claude planned/reviewed; Codex executed the scoped code patches; Claude
authored ADR/docs/handoff, repaired findings, and ran the real local smokes.

## Branch

`pre-core-alpha-data-access-hardening-v1` (off `main`). Not yet pushed/merged at time of
writing this section; see Next Step.

## What the Parquet sink does

- New shared abstraction `src/alpha_system/core/value_store.py`:
  - `ValueStoreFormat` = `jsonl | parquet | dual`.
  - `ValueStoreHandle` (format, jsonl_path, parquet_path, value_count, content_hash,
    schema_version, dataset_version_id, set_id, partition_id, min/max event_ts,
    min/max available_ts).
  - `compute_value_content_hash` (format-agnostic, hashes the record dicts — identical for
    JSONL and Parquet), Polars-guarded `write_parquet_values` / `load_parquet_values`,
    `read_parquet_manifest`, `parquet_is_current` (idempotency).
  - Parquet layout: `values.parquet` (one row per record; `value` and `quality_flags`
    serialized to canonical JSON string columns `value_json` / `quality_flags_json` for
    exact round-trip) + sidecar `values.parquet.manifest.json` (plan, content_hash,
    schema_version, value_count). Atomic temp-write + replace.
- Feature and label materialization (`features/engine/materialization.py`,
  `labels/engine.py`) accept `value_store_format` and dual-write idempotently. The
  low-level `materialize_*` API defaults to **JSONL** (back-compat/test tier); the CLI
  operator defaults to **DUAL**.
- Operator CLI: `alpha feature|label materialize --execute --value-store {jsonl,parquet,dual}`
  (default `dual`), threaded through `cli/seed_pack.py`. Summary surfaces value-store handle
  metadata (paths/hash/count only — no value rows).
- Reader: `features/reports.py` resolves Parquet (via registry `parquet_path` or sibling)
  → JSONL → fail-closed, all through the registry handle.

## What remains JSONL

JSONL (`values.jsonl`) remains the sanctioned **audit/small tier** (tiny fixtures,
audit/debug, MVP smoke, small seed packs) and the **default of the low-level
`materialize_*` functions and the stdlib test substrate** (which has no polars). Parquet is
the research-scale tier, written when `--value-store parquet|dual` is requested.

## Why SQLite stays metadata-only

`features.sqlite` / `labels.sqlite` remain metadata/pointer registries: they record value
file paths, counts, timestamp ranges, lineage, exposure, and (new) `value_store_format`,
`parquet_path`, `value_content_hash`, `value_schema_version` — never value payloads, raw
data, or Parquet/Arrow blobs. New columns were added via idempotent `PRAGMA table_info`
+ `ALTER TABLE ADD COLUMN` backfill (backward-compatible: old JSONL-only rows load with
`value_store_format='jsonl'`, NULL parquet metadata). This honors ADR-0001/ADR-0006.

## session_label fix explanation

Root cause: `runtime/audit/no_lookahead.py` (`LABEL_AS_FEATURE_TOKENS` contained bare
`"label"`, substring-matched) and `runtime/input_resolver.py`
(`_looks_like_label_feature_field` matched `endswith("_label")`) rejected `session_label`.
Fix (semantic, not weakened), confined to those two modules:
- `FieldRole` enum (FEATURE/LABEL_TARGET/SESSION_METADATA/QUALITY_FLAG/PROVIDER_METADATA/
  COST_METADATA), `SESSION_METADATA_FIELDS` (canonical point-in-time set), and
  `FORBIDDEN_FUTURE_FIELDS` (fwd_ret*, target, triple_barrier, future_liquidity_quality,
  final_session_high/low/vwap, label_value/outcome/available_ts, horizon_end_ts, y_true).
- A label-token-looking field is exempt **only** when (a) in the canonical session set,
  (b) **declared** `SESSION_METADATA` via `FeatureInputSpec.input_metadata.field_roles`,
  and (c) not a forbidden-future field. Forbidden-future fields are **always** rejected,
  overriding any role declaration; undeclared `session_label` still fails closed.
- Producer side: the OHLCV family (`features/families/ohlcv/family.py`) now declares
  `field_roles={"session_label":"SESSION_METADATA"}` for `rth_flag`/`eth_flag`/
  `session_minute` (which already existed as POINT_IN_TIME causal features).
- Doc: `docs/research_runtime/SESSION_LABEL_GUARD.md`.

## Local real smoke (local-only; nothing committed)

- Fresh smoke root: `~/alpha_data/alpha_system_parquet_smoke` (outside repo).
  Read real canonical data from `~/alpha_data/alpha_system/databento/canonical/glbx_mdp3`
  and the accepted DatasetVersion `dsv_databento_ohlcv_05404069799decb0` from the real
  `~/alpha_data/alpha_system/registry/datasets.sqlite`.
- Config: `configs/seed_packs/es_ohlcv_session_smoke_v1.json` (NEW; ES, 2024-01-02→01-09;
  `feature_set fset_es_session_ctx_smoke` = `rth_flag`, `session_minute`; label `fwd_ret_5m`).
  The original `es_ohlcv_2024_smoke_v1.json` is untouched (smoke-pack scope preserved).
- Operator `--value-store dual` results (counts / content hashes):
  - `rth_flag`: 6,896 records — `sha256:58c42ab7515299d64ea4f90348290e88e3510849b3f31490a22f5a56638c7705`
  - `session_minute`: 6,896 records — `sha256:d953e7f4bd32998b0fc5d3db7e28b968dc25bf0896bc491b8fb5ba6442fc8278`
  - `fwd_ret_5m`: 6,862 records — `sha256:abb5f53c7ede5f359a79541b237d71d44e79304ebbb6333a101a3c0588e32a9f`
  - Each wrote `values.jsonl` + `values.parquet` + `values.parquet.manifest.json` under
    the smoke root; feature/label quality+coverage PASSING.
- Registry paths (smoke root, local-only):
  `~/alpha_data/alpha_system_parquet_smoke/registry/{features,labels,datasets}.sqlite`.
  Registry rows record `value_store_format='dual'`, `parquet_path`, `value_content_hash`,
  `value_record_count`. Core reader round-tripped 6,896 rth_flag rows = manifest count/hash.
- Output path family (example):
  `~/alpha_data/alpha_system_parquet_smoke/features/materialized/fset_es_session_ctx_smoke/v1_rth_flag/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet`

## Optional dependency environment used

Isolated operator venv `~/.venvs/alpha_system_research` (polars 1.41.2, pyarrow 24.0.0,
duckdb 1.5.3, editable alpha_system; pytest added for local verification). No core
dependency change (`pyproject` core `dependencies=[]` unchanged); Parquet is reached only
through the existing `require_dependency("polars")` guard. `parquet|dual` with polars
absent raises an actionable `DataDependencyError`.

## Runtime / agent preflight result

- `python -m alpha_system.runtime.smoke` over the Parquet-backed session feature packs +
  `fwd_ret_5m` label: **status PASS**, `input_resolution_status=INPUTS_RESOLVED`,
  `real_dataset_version_smoke_ran=True`, no rejections, no leakage warnings,
  `external_provider_call=false`, `raw_file_read=false`, `raw_or_heavy_data_embedded=false`.
- Agent Factory preflight (`AgentFactoryPreflight.evaluate`) with large-scale value-consuming
  study + session-context features requested: **PREFLIGHT_PASS** on all four gates
  (SEED_PACKS, RUNTIME_REAL_SMOKE, FEATURE_LABEL_PARQUET_SINK_V1, SESSION_LABEL_GUARD_FIX_V1).
- `configs/agent_factory/preflight.toml` flipped: `parquet_sink_landed=true`,
  `session_label_guard_fixed=true`.

## Tests run

- `python tools/verify.py --all`: **2806 passed, 7 skipped** (pytest + typecheck +
  boundaries + artifacts + compileall) — green.
- Parquet-bodied tests under the research venv (polars present): **164 passed** (the 7 skips
  on the stdlib substrate are the polars-guarded Parquet round-trips).
- `python tools/hooks/canary_runner.py`: all 7 Frontier canaries PASS.
- `ruff check` on all changed files: clean. (Repo-wide ruff backlog remains out of scope and
  is excluded from `--all`, per `tools/verify.py`.)
- New coverage: `tests/unit/core/test_value_store.py`, Parquet/dual + registry-backfill +
  reader-fallback tests in features/labels, `tests/no_lookahead/test_session_label_guard.py`
  (all Part C cases), CLI `--value-store` tests, OHLCV family `field_roles` tests.

## Changed files (36)

- Code: `core/value_store.py` (new); `features/engine/materialization.py`,
  `features/engine/__init__.py`, `features/registry.py`, `features/reports.py`,
  `features/store.py`, `features/families/ohlcv/family.py`; `labels/engine.py`,
  `labels/registry.py`; `runtime/audit/no_lookahead.py`, `runtime/input_resolver.py`;
  `cli/feature.py`, `cli/label.py`, `cli/seed_pack.py`.
- Config: `configs/agent_factory/preflight.toml`, `configs/seed_packs/es_ohlcv_session_smoke_v1.json` (new).
- Docs: `decisions/0006-...md`, `docs/RESEARCH_INTERPRETATION_POLICY.md`,
  `docs/agent_factory/NEXT_CORE_ALPHA_PILOT_READINESS.md`,
  `docs/feature_label_foundation/{FEATURE_MATERIALIZATION,FEATURE_STORE,LABEL_MATERIALIZATION,LABEL_STORE}.md`,
  `docs/research_runtime/{REAL_SMOKE.md,SESSION_LABEL_GUARD.md (new)}`.
- Tests: `tests/unit/core/test_value_store.py` (new), `tests/no_lookahead/test_session_label_guard.py`
  (new), `tests/unit/cli/{test_feature_cli,test_label_cli}.py`,
  `tests/unit/features/{test_feature_engine,test_feature_reports,test_feature_store,families/ohlcv/test_ohlcv_family}.py`,
  `tests/unit/labels/{test_label_engine,test_label_store}.py`,
  `tests/integration/features/test_seed_pack_execute.py`.

## Notable repair during review

- Fixed a latent bug in `features/reports.py` `_load_jsonl_feature_observations`: the OSError
  path returned a stale 3-tuple referencing an undefined `non_blocking` (refactor remnant);
  corrected to `return observations` (blocking findings mutate the passed list), matching the
  Parquet variant. Surfaced by `ruff F821`; not hit by existing tests.
- Removed gratuitous `getattr(..., "read_" + "parquet_values")` obfuscation in feature code;
  instead renamed the core reader to `load_parquet_values` so the `read_parquet` raw-reader
  token stays only inside `core/` (the feature/label boundary test forbids it in those trees).

## Horizon / session-segment policy (docs/contracts only)

Per direction: docs now state 5–30m is the **primary starting** horizon (not a hard cap);
the one hard intraday boundary is flat before the exchange daily maintenance / trade-date
break; ETH/RTH/pre_RTH/post_RTH are all research-in-scope but require session-segment
diagnostics + stricter thin-session cost stress. No event calendar and no broad
label-family materialization were added (smoke-pack scope preserved).

## Artifact audit

- `git ls-files runs .frontier/upgrade_reports` → empty.
- `git ls-files data metadata` → only README.md placeholders.
- No tracked `.parquet/.jsonl/.sqlite/.db/.dbn/.zst/.arrow/.feather` files; no data-ish files
  staged. All real values/registries/Parquet are local-only under `~/alpha_data/**`.

## No-raw-data / no-claims statements

- No raw provider data, real market values, local registries, or Parquet/JSONL value outputs
  were committed. No external Databento/IBKR provider calls; no raw file reads in the smoke.
- This is data-access hardening only. No alpha, profitability, tradability, strategy,
  portfolio, paper, or live claim is made or implied.

## Readiness for ALPHA_FUTURES_CORE_ALPHA_PILOT_V1

Both pre-pilot blockers are cleared and preflight reports PASS. Large-scale value-consuming
studies and session-context features are unblocked at the data-access layer. The Core Alpha
Pilot remains a separate, separately-authorized campaign with its own governance/evidence/
review gates.

## Remaining warnings

- Dataset-registry report rehydration (ADR-0006 item 4) is still an open follow-up:
  `datasets.sqlite` persists report hashes, not full quality/coverage report objects. The
  runtime smoke requires `datasets.sqlite` present under `ALPHA_DATA_ROOT` (copied into the
  smoke root for this run). Not a blocker for this campaign.
- `parquet_sink_human_approved` / `session_context_features_explicitly_available` remain
  `false` (separate human-approval flags, intentionally not auto-flipped).

## Next Step

Stage curated files by path (no `runs/`, no data), commit, push, open PR, and merge to
`main` after CI. Then the separately-authorized `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` may begin.
