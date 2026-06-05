# Canonical Input Views

`alpha_system.features.input_views` is the shared input layer for feature and
label code that needs accepted canonical OHLCV or BBO records. It is
descriptive only: it orders and exposes canonical input rows, but it does not
compute features, labels, normalized values, dense grids, missingness policy, or
materialized outputs.

## Construction Boundary

Input views are built from an `AcceptedDatasetVersion` handle and canonical
in-memory mappings through `alpha_system.features.consumption`. The builders
call the FLF-P01 consumption surface, which resolves and gates accepted
DatasetVersions and reconstructs canonical records through their `from_mapping`
loaders.

The view module does not import provider clients, open provider files, or expose
provider-shaped fields. If a row contains unsupported fields, the canonical
loader rejects it before a view row is returned.

## Timestamp Semantics

Every OHLCV and BBO input row exposes the five canonical timestamps:

- `bar_start_ts`: inclusive start of the canonical bar interval.
- `bar_end_ts`: exclusive end of the canonical bar interval.
- `event_ts`: event timestamp after canonical validation.
- `available_ts`: earliest time the record is usable by research logic.
- `ingested_at`: local ingestion timestamp, retained as provenance only.

`available_ts` is the only usability key. View construction sorts rows by
`available_ts`, and `as_of(...)` filters rows by `available_ts <= cutoff`.
`event_ts`, `bar_start_ts`, `bar_end_ts`, and `ingested_at` remain visible for
inspection and alignment diagnostics, but they do not determine usability.

## View Rows

`OHLCVInputView` exposes frozen `OHLCVInputRow` values with canonical identity,
the five timestamps, `open`, `high`, `low`, `close`, `volume`, `data_version`,
`quality_flags`, and `session_label`.

`BBOInputView` exposes frozen `BBOInputRow` values with canonical identity, the
five timestamps, `bid`, `ask`, `bid_size`, `ask_size`, `mid`, `spread`,
`data_version`, `quality_flags`, `session_label`, and the optional
`spread_ticks`, `microprice`, `bid_order_count`, and `ask_order_count` fields.

`CanonicalInputViews` keeps the OHLCV and BBO views together and exposes the
combined `available_ts` timeline. It does not synthesize rows when one side is
missing.

## BBO Flags

BBO quality flags are surfaced verbatim. The shared known tokens are
`missing_bbo` and `bbo_quarantined`; the input layer does not impute, fill,
drop, quarantine, or reinterpret rows based on those tokens. FLF-P04 owns the
dense-grid, no-trade, and BBO-missingness policy built on top of this view.

## Safety Boundary

The input-view layer consumes accepted DatasetVersions only and keeps feature
and label values local-only. It adds no external provider call, broker, live,
paper, order, account, strategy, portfolio, deployment, governance-definition,
alpha-claim, tradability-claim, or profitability-claim scope.
