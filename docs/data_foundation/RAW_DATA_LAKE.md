# Raw Data Lake Contract

`DATA-P09` defines the local-only raw provider-response layer for
`ALPHA_DATA_FOUNDATION_V1`. The layer records immutable raw response metadata and
the path policy for future raw bytes. It does not pull provider data, write real
provider responses, parse bars, canonicalize data, run quality checks, or imply
that any data is research-ready.

## Raw Data Object

`RawDataObject` is the frozen metadata record for one immutable local provider
response. Required fields are:

| Field | Meaning |
| --- | --- |
| `raw_object_id` | Non-empty stable metadata id. |
| `source` | `DataSourceProfile.source_id` such as `dsrc_ibkr_historical`. |
| `request_id` | Required link to the request or manifest request record. |
| `chunk_id` | Required link to the `HistoricalChunkRecord`. |
| `path` | Local-only path under `ALPHA_DATA_ROOT/raw/...`. |
| `content_hash` | Content address in `sha256:<64 hex digest>` form. |
| `schema_hint` | Provider-shape hint only. |
| `retrieved_at` | Timezone-aware retrieval timestamp. |
| `row_count` | Non-negative provider row count. |

Validation fails closed on missing fields, malformed ids, invalid hashes, naive
timestamps, negative row counts, paths outside the configured local data root,
or schema hints that imply canonical truth. `raw_object_ref` is derived as
`raw://sha256/<digest>` so it can be linked from `HistoricalChunkRecord`.

## Local Layout

`RawDataLakeLayoutPolicy` delegates root validation to `LocalDataRootPolicy`.
The local root comes from `ALPHA_DATA_ROOT` and must remain outside the repo,
outside synced or mounted paths, and under an ignored local filesystem location.
A missing `LocalDataRootPolicy` or missing raw layout policy blocks path
resolution before any raw write can occur.

Resolved raw object paths use this content-addressed and request/chunk-linked
shape:

```text
$ALPHA_DATA_ROOT/raw/source=<source>/request=<request_id>/chunk=<chunk_id>/sha256=<first2>/<digest>.raw
```

The repository `data/` tree is not a raw lake. It may carry only `README.md` or
`.gitkeep` placeholders under policy-approved placeholder directories. Real raw
provider responses, canonical data, local DBs, logs, caches, Parquet/Arrow/
Feather files, and heavy artifacts remain outside git.

## Immutability And No Overwrite

The content address is `content_hash`. Equal raw bytes produce the same
`sha256:<digest>` address and therefore the same derived raw object ref. The
logical raw slot is:

```text
(source, request_id, chunk_id)
```

`assert_raw_slot_immutable()` refuses to bind a different `content_hash` to an
existing logical slot. This mirrors the DATA-P08 `HistoricalChunkRecord`
no-overwrite rule: retries and resumes may reuse the same content-addressed raw
object, but they must not replace a completed chunk with different raw bytes.

## Boundary

Raw objects are provider-response provenance only. They are not parsed bars,
canonical bars, quality reports, coverage reports, dataset versions, research
approval, or canonical truth. Parser and canonicalization behavior belongs to
later phases and must continue to trace back to these immutable raw refs without
treating raw provider shape as final research semantics.
