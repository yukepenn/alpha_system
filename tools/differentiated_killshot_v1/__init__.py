"""Tools-side harness for DIFFERENTIATED_KILLSHOT_V1 (Track A real-data scoring).

Modules here run on the tools/runtime side of the no-second-PnL rail: they load
already-materialized values via ``core.value_store.load_parquet_values`` and
inject pooled observation rows into the pure research scorer. ``research/`` never
imports the value engine.
"""
