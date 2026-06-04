# Databento Data Foundation

Databento is the planned primary deep-history research corpus for CME index
futures data in this repository. The scoped dataset is `GLBX.MDP3` for ES, NQ,
and RTY only. The intended local corpus contains:

- `ohlcv-1m` continuous front-month bars.
- `bbo-1m` companion best-bid-offer bars.
- `definition`, `statistics`, and `status` metadata refs.

Databento continuous symbols are provenance labels, not roll-truth labels. A
Databento continuous DatasetVersion must retain `provider_continuous`,
`front_month`, `unadjusted`, and `not_roll_truth` metadata so downstream
research does not treat provider continuity as a discovered roll calendar.

Databento and IBKR remain separate sources. Their records are not merged into a
single DatasetVersion. `compare_sources` writes only a diagnostic overlap report
for local QA, including close, volume, timestamp coverage, and BBO availability
notes. It does not choose canonical truth or authorize feature/label use.

All raw DBN/Zstd, canonical refs, metadata refs, registries, reports, logs, and
provider artifacts stay under `ALPHA_DATA_ROOT` outside the repository. The
Databento SDK, DBN reader, pandas, and Parquet libraries are optional and lazy;
offline tests use injected records and must pass under `CI=true`.

No broker, order, account, live, paper-trading, alpha-search, feature
materialization, label materialization, profitability, tradability, or
production-readiness scope is introduced by this Databento docs folder.
