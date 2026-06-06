# Runtime Cache and Artifact Policy

RT-P19 adds the descriptive policy surface for runtime derived-summary caching
and commit eligibility. The policy is orchestration-only: it derives cache keys,
classifies artifact descriptors, and exposes manifest flags. It does not run
diagnostics, compute probe results, load provider data, materialize feature or
label values, or write cache contents.

## Commit Eligibility

Runtime outputs are local-only by default. An output is commit-eligible only
when all of these are true:

- the output kind is a curated summary kind, such as `summary`,
  `diagnostic_summary`, `evidence_summary`, `reference_summary`,
  `markdown_summary`, `text_summary`, `runtime_summary`, or `manifest`;
- the descriptor explicitly marks the output as curated;
- the descriptor is row-free, either with `row_free=True` or `row_count=0`;
- the payload size is at or below the curated-summary threshold;
- the location is a relative non-forbidden summary path;
- the kind and path do not indicate raw, canonical, feature, label, provider,
  runtime-value, cache, log, local-DB, or heavy-output content.

Everything else is classified as `local_only`. Local-only does not mean useful
or valid evidence; it means the output is not commit-eligible.

## Never Commit

The runtime artifact policy always keeps these output classes local-only:

- raw or canonical data references;
- feature values, label values, value tables, market values, and runtime values;
- provider payloads or provider responses;
- parquet, arrow, feather, DBN, ZST, NumPy arrays, SQLite/DB/WAL, journals, and
  logs;
- cache outputs and local DBs;
- anything under `runs/**`, `artifacts/**`, `data/raw/**`,
  `data/canonical/**`, `data/factors/**`, `data/labels/**`,
  `data/cache/**`, `metadata/**`, `logs/**`, `cache/**`, or
  `$ALPHA_DATA_ROOT/**`.

`runs/**` remains run-local audit state and must not be staged or committed.
Heavy runtime outputs and derived caches live under `$ALPHA_DATA_ROOT` or a
run-local root and remain local-only.

## Cache Policy

`RuntimeCachePolicy` is exposed from `alpha_system.runtime.cache_policy` as a
metadata-only policy for derived summaries. It derives a deterministic cache key
from:

- dataset version id and hash;
- feature-pack versions and hashes;
- label-pack versions and hashes;
- code version and code hash;
- config version and config hash;
- optional cost-model version and hash;
- caller-supplied run scope.

Any change to one of those lineage fields changes the lineage hash and therefore
the cache key. Existing metadata for a different lineage is classified as
`stale`, not as a hit.

The lookup surface is limited to three states:

- `hit`: metadata schema, summary kind, lineage hash, payload hash, and cache
  key match the current lineage;
- `miss`: no metadata is available;
- `stale`: metadata exists but no longer matches the current lineage or policy
  schema.

The policy does not read cache payloads and does not create directories or
files. It classifies cache metadata only.

## Storage Roots

The preferred cache root is `$ALPHA_DATA_ROOT/runtime/cache/derived_summaries`,
outside the repository tree. A run-local root under `runs/**` can be resolved
for local audit/resume state, but it is still `local_only` and
`commit_allowed=False`.

Cache roots inside the repository tree are rejected unless they are explicitly
run-local `runs/**` roots. The source module
`src/alpha_system/runtime/cache_policy.py` is policy code, not cache content.

## Safety Boundary

This policy is local-only and descriptive. It does not call external providers,
does not read raw provider files, does not touch broker/live/paper/order scope,
does not start a service or distributed cache, and does not assert alpha,
tradability, profitability, strategy readiness, portfolio readiness, or
production readiness.
