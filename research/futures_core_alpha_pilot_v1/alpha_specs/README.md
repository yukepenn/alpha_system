# AlphaSpec Evidence Index

`research/futures_core_alpha_pilot_v1/alpha_specs/` is the value-free evidence
subtree for AlphaSpec protocol and later family drafts in
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`.

## Current Contents

- `PROTOCOL.md` - canonical `FUTCORE-P05` AlphaSpec Batch Protocol.
- `README.md` - this index.

## Forthcoming Batch Directories

Later phases may create these directories and draft files when their phase specs
authorize them:

- `cross_market/` - `FUTCORE-P07`, cross-market / relative-value drafts.
- `vwap_session/` - `FUTCORE-P08`, VWAP / session-auction drafts.
- `regime/` - `FUTCORE-P09`, regime-gated momentum vs reversion drafts.
- `liquidity_pa/` - `FUTCORE-P10`, liquidity sweep / failed breakout /
  objective PA drafts.
- `bbo_tradability/` - `FUTCORE-P11`, BBO tradability / top-book confirmation
  drafts.

These directories are intentionally not created by `FUTCORE-P05`. This phase
defines the protocol only and drafts no family AlphaSpec.

## Artifact Rules

- Store only value-free protocol text, draft payloads, critique records, ids,
  references, assumptions, limitations, and reviewer links authorized by a
  later phase.
- Do not store raw market data, canonical data, provider responses,
  materialized feature values, materialized label values, per-row diagnostics,
  Parquet, Arrow, Feather, DBN, Zstd, SQLite, DB files, logs, caches, secrets,
  or credentials.
- Do not copy run-local artifacts from `runs/**`.
- Keep all draft language consistent with
  `docs/RESEARCH_INTERPRETATION_POLICY.md`; AlphaSpecs are research evidence for
  review, not profitability, tradability, paper/live, broker, production, or
  capital-allocation claims.
