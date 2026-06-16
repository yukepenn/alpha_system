# ADR-0010: BBO-Resident Microstructure Cost-Adjusted Label

## Status

Accepted for the microstructure research lane (config-extension build; no engine
change). Build-time decision; first real materialization is gated separately
(see "Execute gate" below) and is NOT performed by this change.

## Context

The microstructure research lane (top-of-book imbalance and related BBO
features) needs an outcome label that lives ON the BBO DatasetVersion so a
study can be authored single-dsv against `dsv_databento_bbo_*` with zero new
materialization. The canonical BBO-1m panels (`bbo_1m`) are already accepted on
disk for ES/NQ/RTY across 2019-2026; only a label that *registers on the BBO
dsv* was missing.

The sanctioned value math already exists. The `cost_adjusted` label family
([`labels/families/cost_adjusted/family.py`](../src/alpha_system/labels/families/cost_adjusted/family.py))
computes the BBO mid-to-mid gross forward return and the governed
`spread_adjusted_fwd_ret` / `cost_adjusted_fwd_ret` overlays entirely from a
`BBOInputView`. The accepted scaleout config
[`configs/labels/scaleout/cost_adjusted.json`](../configs/labels/scaleout/cost_adjusted.json)
already drives that family through the reference engine. Its only obstacle to
the microstructure lane is that it lists `input_schemas: ["ohlcv_1m","bbo_1m"]`,
so the scaleout driver's `_primary_input_dataset` returns the OHLCV dataset
(`input_datasets[0]`), and every unit therefore *registers* on the OHLCV dsv
(`features/scaleout/driver.py` lines ~792-800, ~760/763). BBO is only wired as a
secondary input view.

## Decision

Add one new scaleout config,
[`configs/labels/scaleout/bbo_microstructure_cost_adjusted.json`](../configs/labels/scaleout/bbo_microstructure_cost_adjusted.json),
that reuses the `cost_adjusted` family and the reference engine but makes BBO the
PRIMARY (and only) input schema. No engine, family, or value-math code changes.

1. **Registration on the BBO dsv.** `batch_unit_grid.input_schemas` and
   `dataset_selection.required_schemas` are `["bbo_1m"]` only. Because the driver
   takes `primary = input_datasets[0]` and a unit registers on
   `primary.{schema_id,dataset_version_id}`, every planned unit binds
   `schema_id == "bbo_1m"` and a `dsv_databento_bbo_*` DatasetVersion. The
   reference engine still resolves its BBO input view from the same dsv
   (`_reference_label_bbo_view` / `_label_bbo_input_dataset`), so the gross
   mid-to-mid terminal and the spread overlay are computed from the BBO panel.

2. **No second value truth.** All return/cost arithmetic stays in the reference
   `cost_adjusted` family. The config only selects family, governed scope, input
   schema, horizons, and a value namespace. `engine.selected = "reference"`, the
   only accepted engine for this family.

3. **Pre-registered GATE vs diagnostic.** `spread_adjusted_fwd_ret` (gross BBO
   mid-to-mid forward return minus a half-spread round-trip proxy cost) is the
   pre-registered research GATE for the lane: it is cost-aware without baking a
   speculative fixed-fee assumption. `cost_adjusted_fwd_ret` (the same minus a
   fixed 0.25 bps overlay) is retained as a strictly-more-conservative diagnostic
   variant. The internal gross mid-to-mid terminal is not emitted as a label id.

4. **Distinct value namespace.** Values write to
   `labels/materialized/futures_substrate_scaleout_v1/bbo_microstructure_cost_adjusted`,
   distinct from the deprecated OHLCV-primary
   `.../cost_adjusted` namespace, so the BBO-resident lvers never collide with or
   overwrite OHLCV-primary lvers. Checkpoints use the matching distinct root.

5. **Single-dsv wall respected.** The lane is unblocked by *registering the label
   on the BBO dsv*, not by allowing two dsvs through `fast_probe`/`slice_spec`.
   Each planned unit wires exactly one input DatasetVersion (the BBO one).

6. **Horizons.** `5m`, `15m`, `30m`, the microstructure-relevant short horizons.

### Dry-run identity preview

`alpha scaleout label-pack --config
configs/labels/scaleout/bbo_microstructure_cost_adjusted.json --symbols ES
--years 2024 --dry-run` plans 3 accepted units (one per horizon), each binding
`dataset_version_id = dsv_databento_bbo_f9e1d70a04d9dae4`, `schema = bbo_1m`,
`acceptance_state = ACCEPTED` (source: acceptance_summary), 0 failed. The
inventory JSON marks BBO-2024 `BLOCKED`, but that is acceptance-lock bookkeeping;
the live acceptance summary
(`research/futures_substrate_scaleout_v1/dataset_acceptance/acceptance_summary.md`)
and the persisted `registry/datasets.sqlite` lock both state `ACCEPTED` (the
"config gate state != disk truth" rule). The config does NOT edit the inventory
to mint a lock.

### Execute gate

A later `--execute` evaluates `_require_persisted_acceptance_lock` against the
live `registry/datasets.sqlite` for the BBO dsv. For ES/2024 that lock is present
and `ACCEPTED`, matching the planning summary, so execute would PASS the
acceptance gate with no additional sanctioned `accept-datasets` action. (Other
symbol/year cells must be confirmed against their own persisted locks before a
full-grid execute; 2018 BBO is BLOCKED and intentionally outside this config's
year grid.) The real materialization is NOT run by this change.

## Consequences

The microstructure lane can author a single-dsv study against the BBO panel with
a cost-aware outcome label, with no new feature/label materialization and no new
value-truth surface. Risk is contained to a config + canaries; the value math,
no-look-ahead guard, roll/maintenance guards, and acceptance-lock gate are the
existing reference-engine ones, exercised here on a BBO-primary unit by the
canaries in
`tests/unit/futures_substrate_scaleout/labels/test_bbo_microstructure_cost_adjusted_scaleout.py`.
