# P194500_FUTSUB_OHLCV_RTH_TRUTH_REPOINT Handoff

## Branch / Commits

- Branch: `repair/futsub-ohlcv-rth-repoint`
- Base / HEAD before handoff: `origin/main` @ `f0986bd`; local HEAD `f0986bd`
- Commits: none. Changes are intentionally unstaged and uncommitted per executor instruction.

## Scope Completed

- Repointed `src/alpha_system/features/families/ohlcv/family.py` so OHLCV
  session-conditioned reference behavior derives segment truth from
  `alpha_system.data.foundation.sessions.classify_session_timestamp`.
- RTH/ETH flags, `session_minute`, `opening_range`, `overnight_range`, VWAP
  reset state, anchored VWAP activation, distance-to-VWAP, and local primitive
  reset labels now use the shared CME index futures session template
  (`America/Chicago`, RTH `[08:30, 15:00)`).
- Added session-template provenance to affected OHLCV feature contracts:
  `session_template_id`, `session_timezone`, `rth_open_time_local`,
  `rth_close_time_local`, and `session_truth_source`.
- Implemented P183000 review W2 because it was trivially safe in this env:
  `src/alpha_system/features/fast/session_calendar_roll.py` now uses
  Polars `dt.offset_by("1d")` for calendar-day trade-date rollover.
- Added absolute-truth OHLCV tests for static `session_label="ETH"` across EST
  and EDT RTH edges, including non-null `opening_range` on timestamp-derived RTH
  rows.
- Strengthened vwap/session-auction fast-reference parity by forcing the shared
  fixture's canonical `session_label` to static `ETH` on both engines.
- Updated stale synthetic fixture expectations with P194500 provenance notes:
  regime and volume/activity fast-path fixture session resets now land on real
  timestamp-derived RTH/ETH boundaries.

## Files Changed

- `src/alpha_system/features/families/ohlcv/family.py`
- `src/alpha_system/features/fast/session_calendar_roll.py`
- `tests/fixtures/feature_compute_fast_path/regime_vol_compression.py`
- `tests/fixtures/feature_compute_fast_path/volume_activity.py`
- `tests/unit/feature_compute_fast_path/test_vwap_session_auction_pack.py`
- `tests/unit/features/families/ohlcv/test_ohlcv_family.py`
- `tests/unit/futures_substrate_scaleout/features/test_vwap_session_scaleout.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/P194500_FUTSUB_OHLCV_RTH_TRUTH_REPOINT.md`

## Validation Run

- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features -q`
  - `129 passed in 0.96s`
- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit -k 'ohlcv or session or vwap or rth' -q`
  - `138 passed, 2480 deselected in 2.34s`
- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit tests/no_lookahead tests/integration -q`
  - `3 failed, 2854 passed, 1 skipped in 54.20s`
  - Failures match the three known pre-existing environment failures:
    `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`,
    `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`,
    `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`.
- `python tools/verify.py --smoke`
  - Passed with no output.
- `python tools/hooks/canary_runner.py .`
  - Passed: 21 `PASS` lines; final line `All Frontier canaries passed.`

Extra local checks:

- Focused post-repair check:
  `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features/families/ohlcv/test_ohlcv_family.py tests/unit/feature_compute_fast_path/test_vwap_session_auction_pack.py tests/unit/feature_compute_fast_path/test_volume_activity_pack.py tests/unit/futures_substrate_scaleout/features/test_vwap_session_scaleout.py -q`
  - `20 passed in 0.42s`
- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/feature_compute_fast_path/test_regime_vol_compression_pack.py -q`
  - `3 passed in 0.27s`
- Artifact / staging audit:
  - `git diff --cached --name-only`: empty
  - `git ls-files runs`: empty
  - `git diff --check`: no output
  - Forbidden-path changed-file grep: no matches

## Non-Runs / Notes

- No materialization, registry mutation, data rewrite, PR, review artifact, or
  commit was created.
- No `git worktree` command was run and `.git` config was not modified.
- No edits were made under `src/alpha_system/labels/**`,
  `data/databento/canonicalize.py`, dataset configs, or registry write paths.
- The phase spec file is untracked task input in this worktree and was left
  unstaged.
- P183000 review N1 carry-forward: labels close-out anchoring treats a 15:00 CT
  event timestamp as close-out-anchor eligible, while feature segment membership
  for bar-start timestamps remains `[08:30, 15:00)`. This is not changed here
  and must remain explicit in the labels-adoption follow-up.

## Risks / Caveats

- OHLCV feature version ids for session-truth-dependent features change because
  the computational contract now records the shared session template metadata.
- Other fast packs may still use static `session_label` for their own internal
  non-vwap session grouping; this phase only repointed the OHLCV reference
  family and preserved existing fast parity via timestamp-aligned synthetic
  fixtures outside the vwap/session-auction pack.
- The full suite still has the documented three environment failures listed
  above.

## Review Request Focus

- Confirm `family.py` has no remaining RTH/ETH decisions keyed to canonical
  `session_label`; `session_label` is retained as input metadata only.
- Check the feature-version contract change for affected OHLCV features.
- Check static-ETH vwap/session-auction parity and the provenance-marked stale
  fixture timestamp shifts.
- Check the W2 `dt.offset_by("1d")` rollover change in the fast session pack.

## Next Recommended Step

- Run fresh Yellow-lane semantic review.
- After review/merge, coordinator should re-materialize affected feature packs
  through sanctioned paths and carry P183000 N1 into the labels-adoption
  follow-up.
