# Reference Label Parallel Compute V1 Evidence

This directory is the commit-eligible evidence root for
`REFERENCE_LABEL_PARALLEL_COMPUTE_V1`.

Allowed artifacts here are value-free: determinism reports, benchmark
summaries, counts, booleans, content hashes, command results, component
timings, worker-policy decisions, and concise interpretation notes.

Never commit label values, feature values, Parquet, Arrow, Feather, SQLite,
database journals/WAL files, raw or canonical market data, provider responses,
logs, caches, secrets, or credentials here. Any local materialization values,
registries, checkpoint ledgers, and run artifacts stay outside git.

RLPC-P00 creates only this skeleton. Determinism and benchmark evidence belong
to later phases after their gates run.
