# Futures Research Substrate Scaleout Evidence

`research/futures_substrate_scaleout_v1/` is the commit-eligible, value-free
research evidence root for `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`.

This tree starts as scaffolding in `FUTSUB-P00`. Later phases may add
acceptance-lock summaries, reality baselines, guard contracts, materialization
plans, resolver-smoke summaries, coverage matrices, quality reports,
walk-forward and N_eff summaries, Core Pilot rerun summaries, artifact audits,
closeout notes, and downstream handoffs when their phase specs authorize those
artifacts.

## Artifact Rules

- Store only value-free research evidence: ids, references, summaries,
  decisions, limitations, warnings, coverage metadata, and review links.
- Do not store raw market data, canonical data, provider responses,
  materialized feature values, materialized label values, per-row diagnostics,
  Parquet, Arrow, Feather, DBN, Zstd, SQLite, DB files, logs, caches, secrets,
  or credentials.
- Do not copy run-local artifacts into this tree unless a later phase explicitly
  creates a value-free commit-eligible summary.
- Keep report language conservative and consistent with
  `docs/RESEARCH_INTERPRETATION_POLICY.md`.

## Current Contents

- `README.md` - this evidence-tree contract.
- `.gitkeep` - placeholder so the evidence root exists before later phases
  populate it.
