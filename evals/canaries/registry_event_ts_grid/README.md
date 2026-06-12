# Registry Event Timestamp Grid Canary

Expected behavior: registered feature and label metadata must report
`first_event_ts` and `last_event_ts` on the completed-bar minute grid.

The canary has two modes:

- `synthetic`: used by CI and `tools/hooks/canary_runner.py`; it exercises a
  tiny fixture with one clean grid row and the two known grandfathered debts.
- `live`: scans local `$ALPHA_DATA_ROOT/registry/features.sqlite` and
  `$ALPHA_DATA_ROOT/registry/labels.sqlite`; when those registries are absent it
  prints a loud `SKIP` line instead of silently passing.

Known off-grid debt is visible in
`REGISTRY_EVENT_TS_GRID_ALLOWLIST`:

- BBO feature packs: pending re-materialization after BBO family emission was
  normalized to `bar_end_ts`.
- Cost/spread-adjusted label packs: documented mirror defect until the label
  packs are repaired and re-locked.
