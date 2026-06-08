# Feature Compute Fast Path

This directory is the durable documentation index for
`FEATURE_COMPUTE_FAST_PATH_V1`.

- `OVERVIEW.md` summarizes the campaign purpose, parity-first discipline, and
  hard boundaries.
- `PACK_MATERIALIZER.md` documents the P01 fast engine contract, identity
  guarantee, persistence path, parity harness, and optional-dependency policy.
- `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/` contains the authoritative campaign
  contract bundle and per-phase plan.
- `research/feature_compute_fast_path_v1/` is the value-free evidence root for
  later parity, benchmark, and reconciliation summaries.

`FCFP-P01` adds the `src/alpha_system/features/fast/` engine core and the
synthetic reference-parity harness under `tests/unit/feature_compute_fast_path/`.
It adds no production family pack, no CLI command, no real-data backfill, no
feature/label values, no broker/live/paper behavior, and no heavy artifacts.

`FCFP-P02` adds the first production family pack, `base_ohlcv`, under
`src/alpha_system/features/fast/`. Its synthetic parity test covers the six
governed Base OHLCV features and its value-free report lives under
`research/feature_compute_fast_path_v1/parity/base_ohlcv/`.

`FCFP-P03` adds the `session_calendar_roll` pack for the governed Session /
Calendar / Roll family. Its synthetic parity test covers exact integer/string
values, row timing, entity ids, feature-version identity, sorted quality flags,
RTH/ETH session edges, roll proximity, synthetic no-trade position-only flags,
and absent optional expiration/status metadata.
