# Universes And Multi-Asset Readiness

ASV1-P24 adds a small, deterministic universe layer for future multi-symbol research. It is configuration and correctness infrastructure only; it does not add real multi-symbol data, live universe updates, broker sync, FX conversion, production optimization, or any alpha/tradability claim.

## Universe Config

`src/alpha_system/data/universe.py` defines `UniverseSpec` and `UniverseMember`.

Universe configs support:

- stable `instrument_id` values,
- raw symbols as metadata or as instrument-master lookup inputs,
- asset class, exchange, currency, and timezone,
- member active date ranges,
- data versions,
- inclusion and exclusion rules,
- representation-only future sector constraints,
- representation-only future asset constraints.

`instrument_id` is the internal identity. Symbol-only config entries are accepted only when an `InstrumentMasterCatalog` resolves the symbol to exactly one instrument id using active date, exchange, and currency context where needed.

Example config:

```text
configs/universes/examples/tiny_multi_symbol.json
```

The example is a tiny deterministic synthetic correctness config. It is not market evidence.

## Active Membership

Universe active-date filtering is point-in-time:

- `UniverseSpec.active_members(date)` filters by each member's configured active range.
- `UniverseSpec.active_members_at(timestamp)` converts the timestamp into each member's configured timezone before applying active dates.
- `UniverseSpec.resolve_symbol(...)` returns an `instrument_id` only when the result is unambiguous.

This prevents future universe membership from entering cross-sectional calculations before the member is active.

## Session And Timezone Handling

`src/alpha_system/experiments/universe_runner.py` provides a bounded fixture runner for tiny synthetic multi-symbol checks. It accepts independent `TradingCalendar` instances per `instrument_id` and verifies each calendar timezone matches the universe member timezone.

The runner records:

- aligned sessions per instrument,
- expected one-minute bar counts per session,
- per-instrument missing-data flags,
- deterministic universe hash,
- deterministic runner config hash.

Registry writes are optional and use existing local SQLite experiment tables. Tests use pytest temp directories only. Generated runner outputs are JSON files under temp/local paths, not repository artifact roots.

## Portfolio Readiness

`src/alpha_system/portfolio/universe_constraints.py` adds universe-level exposure contracts:

- gross exposure across instrument targets,
- net exposure across instrument targets,
- future sector exposure constraint representation,
- future asset exposure constraint representation,
- future correlation-aware allocation contract representation.

Sector, asset, and correlation-aware allocation contracts are `contract_only` in this phase. Enabling them raises an error.

## Cross-Sectional Ranking

`src/alpha_system/research/cross_sectional.py` ranks rows at one decision timestamp only when:

- the instrument is active in the point-in-time universe,
- the row timestamp is aligned to the decision timestamp,
- the row is available no later than the decision timestamp.

Missing, unavailable, misaligned, inactive, and out-of-universe rows are reported as per-instrument flags rather than silently entering the rank.

## Limitations

This phase does not implement full cross-asset analytics, FX conversion, live universe changes, broker sync, production optimization, real multi-symbol datasets, or L2 processing. It prepares stable metadata, hashing, fixture validation, and explicit contracts for later reviewed work.
