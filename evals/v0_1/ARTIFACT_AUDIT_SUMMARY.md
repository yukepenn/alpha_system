# v0.1 Artifact Audit Summary

## Policy

Commit-eligible ASV1-P29 artifacts are limited to closeout docs, the integration
test, curated small eval summaries, README snapshot, and
`handoffs/ALPHA_SYSTEM_V1/ASV1-P29.md`.

Never commit:

- `runs/**`
- raw data or canonical generated data,
- generated factor, label, signal, grid, management-grid, ML, report-bundle, or
  backtest outputs,
- local SQLite/DB files,
- Parquet/Arrow/Feather files outside documented tiny fixture exceptions,
- logs, caches, model binaries, trade logs, equity curves, or heavy artifacts.

## Executor Audit Result

The bounded repair audit and command outputs are recorded in
`handoffs/ALPHA_SYSTEM_V1/ASV1-P29.md`. The closeout recommendation depends on `git ls-files
runs` returning empty and no forbidden data, DB, generated artifact, or heavy
path appearing in tracked or staged commit-eligible files.

The original broad tracked-artifact grep treated any tracked `artifacts/**` path
as a violation and therefore matched the legitimate placeholder
`artifacts/README.md`. The repaired audit checks for forbidden data, DB, heavy,
cache, and generated artifact payload patterns while allowing policy-compliant
placeholder README files.
