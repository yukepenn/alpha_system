# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`FEATURE_COMPUTE_FAST_PATH_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress: `FEATURE_COMPUTE_FAST_PATH_V1` has the P01 V1 engine
core plus governed `base_ohlcv`, `session_calendar_roll`,
`vwap_session_auction`, `regime_vol_compression`, `liquidity_pa_structure`,
`volume_activity`, `bbo_tradability`, and `cross_market` fast-pack executor
work available in this worktree. This is the `FCFP-P09` executor snapshot within
the `FCFP-P00` through `FCFP-P15` campaign. Ralph owns validation, staging,
Yellow-lane review routing, and any phase verdict.

Active / next phase after P09 review and merge: `FCFP-P10` multi-horizon
fixed-horizon Label Pack + Parity, followed by targeted/incremental CLI work.
Remaining phases merge serially.

New durable surfaces in this `FCFP-P09` executor snapshot:

- `PackMaterializer`, `FastFeaturePack`, and `FastFeatureDeclaration` under
  `src/alpha_system/features/fast/`
- The V1 `base_ohlcv` Polars pack and fail-closed pack resolver under
  `src/alpha_system/features/fast/`
- The V1 `session_calendar_roll` Polars pack and resolver wiring under
  `src/alpha_system/features/fast/`
- The V1 `vwap_session_auction` Polars pack, pack preparation hook, and resolver
  wiring under `src/alpha_system/features/fast/`
- The V1 `regime_vol_compression` Polars pack and resolver wiring under
  `src/alpha_system/features/fast/`
- The V1 `liquidity_pa_structure` Polars pack and resolver wiring under
  `src/alpha_system/features/fast/`
- The V1 `volume_activity` Polars pack and resolver wiring under
  `src/alpha_system/features/fast/`
- The V1 `bbo_tradability` Polars pack and resolver wiring under
  `src/alpha_system/features/fast/`
- The V1 `cross_market` aligned-panel Polars pack and resolver wiring under
  `src/alpha_system/features/fast/`
- Synthetic reference-parity harness under
  `tests/unit/feature_compute_fast_path/`
- Base OHLCV, Session / Calendar / Roll, and VWAP / Session-Auction synthetic
  parity tests, plus the Regime / Volatility / Compression and Liquidity / PA
  Structure, Volume / Activity, BBO Tradability, and Cross-Market parity tests,
  under
  `tests/unit/feature_compute_fast_path/`
- Tiny documented synthetic fixtures, including the 32-row Base OHLCV pack
  fixture, the dense-grid Session / Calendar / Roll pack fixture, the VWAP /
  Session-Auction pack fixture, the Regime / Volatility / Compression pack
  fixture, the Liquidity / PA Structure pack fixture, the Volume / Activity pack
  fixture, the BBO Tradability pack fixture, and the ES/NQ/RTY Cross-Market
  aligned-panel fixture, under
  `tests/fixtures/feature_compute_fast_path/`
- Fast-path engine contract docs under `docs/feature_compute_fast_path/`
- Value-free Base OHLCV, Session / Calendar / Roll, VWAP / Session-Auction, and
  Regime / Volatility / Compression parity reports plus the Cross-Market parity
  note under
  `research/feature_compute_fast_path_v1/parity/`
- No CLI command, real-data backfill, benchmark, feature/label value artifact,
  broker/live/paper behavior, or heavy artifact was added in this phase.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Campaign bundle: `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/`
- Fast-path docs: `docs/feature_compute_fast_path/`
- Fast-path engine core: `src/alpha_system/features/fast/`
- Fast-path parity tests: `tests/unit/feature_compute_fast_path/`
- Value-free research evidence root:
  `research/feature_compute_fast_path_v1/`
- Commit-eligible handoffs:
  `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
production deployment, account operations, capital allocation, or autonomous
trading behavior.

The reference feature/label engine remains the correctness oracle. Resolver
exact-id semantics, official keystone registry writes, and serial registry writes
are unchanged. The fast engine produces values for existing governed identities;
it never mints V1-specific feature ids. Polars remains an optional dependency
guarded by `require_dependency("polars")`. The campaign uses Green/Yellow scope
only and introduces no Red scope.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data, feature
or label values, provider responses, heavy artifacts, local databases, logs,
caches, secrets, and credentials are never committed.

This campaign makes no profitability or tradability claim. Research outputs are
evidence for review only.

## Validation Commands

Default local validation commands remain:

```bash
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
```

Workflow 2 orchestration, validation routing, review, staging, commit, PR, CI,
merge, and done-check actions are owned by Ralph.
