# Databento Dataset Consumption

Feature and label campaigns consume Databento by resolving accepted local
DatasetVersions from the registry:

```python
from alpha_system.data.foundation.version_registry import resolve_dataset_version

ohlcv = resolve_dataset_version(registry_path, "<dsv_databento_ohlcv_PLACEHOLDER>")
bbo = resolve_dataset_version(registry_path, "<dsv_databento_bbo_PLACEHOLDER>")
```

Use the OHLCV DatasetVersion for canonical one-minute bars and the companion BBO
DatasetVersion for quote-aware features. BBO records expose `bid`, `ask`,
`bid_size`, `ask_size`, `mid`, `spread`, and optional `spread_ticks`,
`microprice`, `bid_order_count`, and `ask_order_count` when available.

The Databento continuous front-month series is not roll truth. Consumers must
preserve the registered continuous-provenance metadata and avoid claims that it
discovers the correct roll calendar. Databento and IBKR source records stay
separate; the cross-source report is QA evidence only and is not a combined
DatasetVersion.

No-lookahead consumers must order by `available_ts`, not by provider event time
or local `ingested_at`. Locked-test and latest-shadow use still requires the
existing partition and contamination-metadata guards. Resolving a DatasetVersion
is a data-admissibility step only; it does not imply alpha value, label quality,
tradability, broker readiness, paper/live readiness, or production readiness.
