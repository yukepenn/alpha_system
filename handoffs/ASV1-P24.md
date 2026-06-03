# ASV1-P24 Handoff - Multi-Symbol Universe Support

## Universe Support Summary

Implemented multi-symbol universe readiness with `UniverseSpec`, `UniverseMember`, JSON config loading, active-date filtering, symbol-to-`instrument_id` resolution through an instrument master, deterministic universe hash input, and a tiny deterministic fixture runner.

`instrument_id` is the stable identity throughout the new contracts. Symbol-only universe members require an `InstrumentMasterCatalog` and must resolve unambiguously before a `UniverseMember` is created.

## Instrument Master Field Coverage

| Field | Covered |
| --- | --- |
| `instrument_id` | yes |
| `symbol` | yes |
| `asset_class` | yes |
| `exchange` | yes |
| `currency` | yes |
| `timezone` | yes |
| `tick_size` | yes |
| `lot_size` | yes |
| `multiplier` | yes |
| `start_date` | yes |
| `end_date` | yes |
| `corporate_action_policy` | yes |
| `metadata` | yes |

Instrument records validate non-empty identity fields, supported enum values, positive decimal metadata, valid IANA timezones, and active-date ordering.

## Session And Timezone Summary

`src/alpha_system/experiments/universe_runner.py` aligns sessions per `instrument_id` using independent `TradingCalendar` objects. It rejects calendar/member timezone mismatches and records per-instrument aligned session metadata plus expected one-minute bar counts. Active membership at timestamps uses each universe member's configured timezone before applying date ranges.

## Portfolio Constraint Summary

`src/alpha_system/portfolio/universe_constraints.py` evaluates and deterministically scales gross and net exposure across instrument targets. Future sector exposure, future asset exposure, and future correlation-aware allocation are explicit `contract_only` representations; enabling them raises an error.

## Cross-Sectional Point-In-Time Summary

`src/alpha_system/research/cross_sectional.py` ranks only active universe members at a decision timestamp. Rows are excluded and flagged when they are unavailable at the decision timestamp, misaligned to a different event timestamp, inactive, missing, or outside the universe. Future active members cannot enter ranks before their local active date.

## Registry Hash Behavior

The universe runner records deterministic `universe_hash` and `config_hash` values in temp/local SQLite registry metadata using the existing `study_runs` table. Tests write registry DBs only under pytest `tmp_path`; no registry table migration was added.

## Files Changed

Source:

- `src/alpha_system/data/universe.py`
- `src/alpha_system/core/instruments.py`
- `src/alpha_system/core/instrument_master.py`
- `src/alpha_system/experiments/universe_runner.py`
- `src/alpha_system/portfolio/universe_constraints.py`
- `src/alpha_system/research/cross_sectional.py`

Docs/configs:

- `docs/UNIVERSES_AND_MULTI_ASSET.md`
- `docs/INSTRUMENT_MASTER.md`
- `configs/universes/examples/tiny_multi_symbol.json`
- `README.md`

Tests:

- `tests/unit/data/test_universe_hash_input.py`
- `tests/unit/research/test_cross_sectional_rank.py`
- `tests/integration/test_multi_symbol_tiny_fixture.py`
- `tests/integration/test_universe_registry_hash.py`
- `tests/integration/test_universe_runner_fixture.py`
- `tests/unit/test_universe_config_validation.py`
- `tests/unit/test_instrument_metadata_required_fields.py`
- `tests/unit/test_instrument_master_active_dates.py`
- `tests/unit/test_universe_active_date_filtering.py`
- `tests/unit/test_multi_symbol_session_alignment.py`
- `tests/unit/test_multi_symbol_timezone_handling.py`
- `tests/unit/test_per_symbol_missing_data_flags.py`
- `tests/unit/test_multi_symbol_portfolio_limits.py`
- `tests/unit/test_future_sector_asset_constraints.py`
- `tests/unit/test_future_correlation_aware_allocation_contract.py`
- `tests/unit/test_universe_artifact_policy.py`

Handoff:

- `handoffs/ASV1-P24.md`

Staged files: none. No commit or push was performed by this executor.

## Validation

Passed:

- `python -m pytest tests/unit tests/integration tests/no_lookahead` - 559 passed.
- `python -m pytest tests/unit/test_universe_config_validation.py tests/unit/test_instrument_metadata_required_fields.py tests/unit/test_multi_symbol_session_alignment.py` - 7 passed.
- `python -m pytest tests/unit/data tests/unit/research/test_cross_sectional_rank.py tests/integration/test_multi_symbol_tiny_fixture.py || true` - 4 passed.
- `python -m compileall src` - passed.
- `find data -type f ! -name README.md ! -name .gitkeep -print` - no output.
- `find metadata -type f ! -name README.md ! -name .gitkeep -print` - no output.
- `find artifacts -type f ! -name README.md ! -name .gitkeep -print 2>/dev/null || true` - no output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` - no output.
- `find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print` - no output.
- `git ls-files runs` - no output.

Non-blocking unavailable:

- `python -m ruff check src tests || true` - `/usr/bin/python: No module named ruff`.
- `python -m mypy src || true` - `/usr/bin/python: No module named mypy`.

`git status --short` shows only intended unstaged source, docs, config, tests, README, and this handoff. `runs/**` is not staged or tracked.

## Artifact Policy

No real multi-symbol data, raw/canonical data, generated universe outputs, factor/label/signal stores, local DBs, Parquet/Arrow/Feather files, logs, caches, or heavy artifacts were committed. Universe runner tests write JSON output and SQLite registries only under pytest temp directories.

No broker, live, paper-trading, order-routing, deployment, or production execution scope was introduced. No alpha, profitability, robustness, or tradability claims were introduced.

## README Snapshot

`README.md` was updated with the ASV1-P24 snapshot: new universe/instrument/runner/portfolio/cross-sectional modules, new docs/configs, unchanged safety boundaries, and ASV1-P25 as the next planned phase after ASV1-P24.

## Risk Status

- R-031 cross-sectional universe leakage: mitigated by point-in-time membership, timestamp alignment, and availability flag tests.
- R-032 symbol identity misuse: mitigated by `instrument_id`-first universe members and ambiguous symbol-resolution rejection.
- R-001/R-002 no-lookahead and availability semantics: no-lookahead suite remains green; cross-sectional rows require availability at decision time.
- R-014 overclaiming: docs and README state readiness/limitations only and avoid tradability claims.
- R-022 broker/live scope creep: no broker/live/paper/order-routing paths touched.
- R-037 temp/local runner writes: universe runner output and registry tests use temp paths and reject repo artifact roots.
- R-012/R-013/R-024/R-038/R-039 artifact discipline: artifact checks produced no forbidden output.

## Known Limitations

- Universe runner is a bounded synthetic fixture runner only.
- No real multi-symbol datasets or generated universe outputs are included.
- No FX conversion, live universe updates, broker sync, production optimizer, or L2 processing is implemented.
- Sector/asset exposure and correlation-aware allocation remain representation-only contracts.
- Registry hash recording uses the existing `study_runs` experiment table; no dedicated `universe_runs` table was added.
- No CLI surface was added for universe runs in this phase.

## Review Focus

Review should focus on stable `instrument_id` identity discipline, symbol-resolution ambiguity handling, instrument metadata completeness, per-instrument timezone/calendar behavior, point-in-time cross-sectional membership and availability semantics, universe/config hash recording, artifact policy enforcement, and docs/README language for no overclaims.
