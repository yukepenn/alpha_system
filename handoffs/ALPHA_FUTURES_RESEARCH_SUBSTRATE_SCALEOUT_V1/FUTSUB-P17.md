# FUTSUB-P17 Executor Handoff

## Branch / Commit

- Branch: not queried by Codex; the executor prompt explicitly forbade
  `git status`.
- Commits: none by Codex. All repository changes were left unstaged.
- Review / verdict / PR / merge: not created by Codex per executor
  instructions. Ralph owns review, verdict parsing, staging, commit, PR, CI,
  and merge gates.

## Files For Ralph To Stage Explicitly

- `README.md`
- `configs/labels/scaleout/extended_horizon.json`
- `research/futures_substrate_scaleout_v1/label_packs/extended_horizon/coverage_summary.md`
- `src/alpha_system/cli/seed_pack.py`
- `src/alpha_system/labels/families/fixed_horizon/__init__.py`
- `src/alpha_system/labels/families/fixed_horizon/family.py`
- `tests/unit/futures_substrate_scaleout/labels/test_extended_horizon_scaleout.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P17.md`

## Scope Completed

- Added the extended intraday fixed-horizon labels `fwd_ret_60m`,
  `fwd_ret_120m`, and `fwd_ret_240m` to the existing fixed-horizon family and
  seed LabelPack allow-list.
- Kept labels on the reference materialization path:
  `alpha scaleout label-pack` label mode -> `run_seed_label_pack` -> official
  keystone registry write path. No V1 fast or worker label path was added.
- Applied the inherited FUTSUB-P16 roll-splice and maintenance-crossing guard
  path at extended horizons. The guard was not forked or re-implemented, and
  `src/alpha_system/labels/roll_guard.py` plus `src/alpha_system/labels/engine/**`
  were not edited.
- Added overlap-aware horizon metadata for extended fixed-horizon label
  contracts. The metadata records raw row count separately from effective sample
  count, marks rows as non-independent, and uses the conservative
  `floor(row_count / horizon_minutes)` rule.
- Authored the value-free extended-horizon scaleout config and coverage summary.
- Added the focused synthetic unit test for `label_available_ts`, required
  registry record fields, shared guard crossing behavior, and overlap-aware
  N_eff metadata.
- Updated the README snapshot for FUTSUB-P17 and the next FUTSUB-P18 phase.

## Local-Only Materialization

All materialized values, manifests, checkpoint ledgers, and SQLite registry
records are local-only under `ALPHA_DATA_ROOT` and are not commit-eligible.

| Step | Result |
| --- | --- |
| Dry-run full-window planning | exit 0; `72` accepted units selected, `2018` excluded |
| Bounded-real execution, year `2024` x `ES/NQ/RTY` x `60m/120m/240m` | exit 0; `9` completed, `0` failed |
| Full-window execution | exit 0; `63` completed, `9` skipped from current bounded-real checkpoint/registry evidence, `0` failed |
| Completion ledger | `72` completed units |
| Registry verification | `72` / `72` records had required registry fields and `label_available_ts` ranges |

Registry field check covered `value_store_format`, `parquet_path`,
`value_content_hash`, `value_schema_version`, `dataset_version_id`, and
`label_version_id`. Registry states checked: `54` units were `ACCEPTED`; `18`
units were `ACCEPTED_WITH_WARNINGS`.

## Coverage Summary

| Horizon | Units | Candidate terminals | Rows materialized | Roll dropped | Maintenance dropped | Roll flagged | Roll truncated | Effective samples |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fwd_ret_60m` | 24 | 7270082 | 7153505 | 116577 | 0 | 0 | 0 | 119212 |
| `fwd_ret_120m` | 24 | 7169230 | 6819369 | 114320 | 235541 | 0 | 0 | 56816 |
| `fwd_ret_240m` | 24 | 7008445 | 6153429 | 103787 | 751229 | 0 | 0 | 25625 |

Expected gap classification:

- `2018` `ohlcv_1m` remains `BLOCKED` in the accepted inventory and was
  excluded rather than forced into materialization.
- `2019` and `2026` were included as `ACCEPTED_WITH_WARNINGS`; `2026` is the
  partial-year window ending `2026-06-01T00:00:00+00:00`.
- The committed accepted inventory is year-level for `ohlcv_1m`; it does not
  expose a separate ES/NQ-2018 eligibility surface, so no 2018 symbol was
  selected.

## Guard Result

- Cross-roll policy: `drop`.
- Roll policy id: `roll_cme_index_futures_quarterly`.
- Roll guard version: `roll_guard_v1`.
- Maintenance policy: `drop`.
- Maintenance policy id:
  `cme_index_futures_daily_maintenance_break_v1`.
- Maintenance guard version: `maintenance_crossing_guard_v1`.
- Contract-scoped terminal key confirmed:
  `series_id+contract_id+event_ts`.
- Exact guard counts were computed with the shared fixed-horizon guard helpers
  after contract-scoped terminal matching. No extended label silently crossed a
  roll splice or the daily maintenance / trade-date break in the materialized
  rows.

## Overlap-Aware N_eff Metadata

- Metadata version: `horizon_overlap_metadata_v1`.
- Sampling interval: 1 minute.
- Rule: `effective_sample_count = floor(raw_row_count / horizon_minutes)`.
- Rows are explicitly not represented as independent samples.
- Effective samples were below raw rows for every extended-horizon unit.
- Runtime N_eff reporting remains FUTSUB-P25 scope; this phase records the
  per-pack overlap metadata that feeds that reporting.

## Validation Run

| Command | Result |
| --- | --- |
| `source ~/.venvs/alpha_system_research/bin/activate && export ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system && python tools/verify.py --smoke` | exit 0 |
| `source ~/.venvs/alpha_system_research/bin/activate && export ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system && python -m pytest tests/unit/futures_substrate_scaleout/labels/test_extended_horizon_scaleout.py -q` | exit 0; `3 passed in 0.39s` |
| `source ~/.venvs/alpha_system_research/bin/activate && export ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system && python tools/hooks/canary_runner.py` | exit 0; all Frontier canaries passed |
| `test -f configs/labels/scaleout/extended_horizon.json` | exit 0 |
| `test -f research/futures_substrate_scaleout_v1/label_packs/extended_horizon/coverage_summary.md` | exit 0 |
| `git ls-files runs` | exit 0; empty output |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'` | exit 0; empty output |

## Non-Runs

- `git status --short`: not run; the executor prompt explicitly forbade
  `git status`.
- `git diff --cached --name-only`: not run; Codex staged nothing and the
  executor prompt explicitly forbade `git diff`.
- Reviewer / Claude / `review.md` / `verdict.json`: not run or created per
  executor instructions.
- PR creation, CI waiting, merge gate, merge, and PASS marking: not performed by
  Codex per executor instructions.

## Risks / Caveats

- `python tools/frontier/status_doctor.py` was run during discovery and reported
  no authoritative live `state.json` run directory to reconcile. The prompt's
  run artifact directory was absent in this worktree, so no run-local handoff was
  written and no run-local STOP file was found.
- The handoff and coverage summary are value-free. They contain no per-row label
  values, prices, returns, SQLite content, value content hashes, provider
  responses, or roll-calendar data.
- Ralph should perform the authoritative staged-set audit after explicit
  staging. Codex did not stage any file.

## Review Request Focus

- Confirm the inherited shared roll/maintenance guard is applied at
  60m/120m/240m and that terminal lookup remains contract-scoped.
- Confirm the overlap-aware metadata prevents raw minute rows from being
  represented as independent effective samples.
- Confirm `label_available_ts`, required registry fields, accepted
  `dataset_version_id` states, and Parquet-first value storage hold for all
  extended-horizon units.
- Confirm no V1 fast/worker label path or guard/engine re-implementation was
  introduced.
- Confirm the committed summary remains value-free and contains no
  profitability, tradability, live, paper, broker, or order-routing claim.

## Next Recommended Step

Ralph should stage only the listed commit-eligible files by explicit path, run
its authoritative staged-set and artifact audits, then route the Yellow-lane
Claude review.
