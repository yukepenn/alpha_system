# FUTSUB-P16 Executor Handoff

## Branch / Commit

- Branch: not queried by executor; the prompt explicitly forbade `git status`.
- Commits: none by Codex. All repository changes were left unstaged.
- Review / verdict / PR / merge: not created by Codex per executor
  instructions. Ralph owns review, verdict parsing, staging, commit, PR, CI,
  and merge gates.

## Scope Completed

- Wired the existing roll-splice guard into the shared fixed-horizon terminal
  resolution path for trade-price and midprice fixed-horizon labels.
- Added contract-scoped terminal lookup:
  `series_id+contract_id+event_ts`.
- Added materialization-time maintenance-crossing drops for the daily
  maintenance break.
- Added fixed-horizon metadata for `roll_policy_id`, `roll_guard_version`,
  `roll_cross_policy`, `roll_window`, `maintenance_policy_id`,
  `maintenance_guard_version`, `maintenance_crossing_policy`, and
  `terminal_key`.
- Added `fwd_ret_15m` to the seed LabelPack path.
- Added partition-scoped fixed-horizon LabelVersion identity through
  materialization scope metadata (`symbol`, `partition_id`, schema, DatasetVersion,
  and window). This prevents ES/NQ/RTY partitions in the same DatasetVersion from
  colliding in the label registry.
- Added stale-checkpoint protection so label resume records must match the
  current write-free LabelVersion preview before they can skip a unit.
- Added `alpha scaleout label-pack` as a thin label-mode dispatch through the
  existing scaleout driver and `run_seed_label_pack`; label mode forces the
  reference engine and serial registry writes.
- Added the fixed-horizon label scaleout config and value-free coverage summary.
- Updated README with the required compact FUTSUB-P16 snapshot and unchanged
  safety boundaries.

## Files Changed For Ralph To Stage Explicitly

- `README.md`
- `configs/labels/scaleout/fixed_horizon.json`
- `research/futures_substrate_scaleout_v1/label_packs/fixed_horizon/coverage_summary.md`
- `src/alpha_system/cli/scaleout.py`
- `src/alpha_system/cli/seed_pack.py`
- `src/alpha_system/features/scaleout/__init__.py`
- `src/alpha_system/features/scaleout/driver.py`
- `src/alpha_system/labels/families/fixed_horizon/__init__.py`
- `src/alpha_system/labels/families/fixed_horizon/family.py`
- `tests/unit/futures_substrate_scaleout/labels/test_fixed_horizon_guards.py`
- `tests/unit/futures_substrate_scaleout/scaleout/test_fixed_horizon_label_scaleout_driver.py`

## Local-Only Materialization

- Dry-run label CLI validation: `ES,NQ` / `2024` / `fwd_ret_5m` planned two
  units with distinct scoped `label_version_id`s.
- Real local bounded validation:
  `PYTHONPATH=src python -m alpha_system.cli scaleout label-pack --execute --rollout bounded-real ...`
  completed the 2024 bounded grid.
- Bounded result: `18` selected units, `16` completed, `2` skipped from current
  registry truth, `0` failed.
- Full accepted-window expansion was not run in this executor turn. The full
  accepted grid remains `144` units and is restart-safe from the local
  checkpoint/registry evidence.
- Local values, checkpoints, and `registry/labels.sqlite` updates are under
  `ALPHA_DATA_ROOT` and must not be staged.
- During validation, one pre-fix targeted ES/2024 `fwd_ret_5m` local label
  artifact was created before partition-scoped identity was added. It is
  local-only and no current preview/checkpoint uses it; no direct SQLite cleanup
  was performed.

## Validation Run

| Command | Result |
| --- | --- |
| `python tools/verify.py --smoke` | exit 0 |
| `python -m pytest tests/unit/futures_substrate_scaleout/labels -q` | exit 0; 4 passed |
| `python -m pytest tests/unit/futures_substrate_scaleout/scaleout -q` | exit 0; 26 passed |
| `python tools/verify.py --typecheck` | exit 0; `compileall -q src tests tools` |
| `python tools/hooks/canary_runner.py` | exit 0; all Frontier canaries passed |
| `python tools/verify.py --lint` | exit 0, but lint was skipped because `ruff` is not installed |
| `test -f configs/labels/scaleout/fixed_horizon.json` | exit 0 |
| `test -d research/futures_substrate_scaleout_v1/label_packs/fixed_horizon` | exit 0 |
| non-git heavy-artifact scan with `find` for Parquet/SQLite/Arrow/Feather/DBN/ZST/DB/PYC outside `.git` and `runs` | empty |
| non-git `runs` file scan | empty |

## Non-Runs

- `git status --short`: not run; executor prompt forbade all git commands.
- `git ls-files runs`: not run; executor prompt forbade all git commands.
- `git ls-files '**/*.parquet' ...`: not run; executor prompt forbade all git
  commands.
- `git diff --cached --name-only`: not run; Codex did not stage anything and
  the prompt forbade git commands.
- Full 144-unit materialization: not run in this executor turn; only the full
  2024 bounded-real grid was executed.
- Reviewer / Claude / `review.md` / `verdict.json`: not run or created per
  executor instructions.

## Risks / Caveats

- Full-window materialization remains to be expanded by Ralph/local execution if
  required before review. The driver is restart-safe and should skip the 2024
  bounded units already registered under the current scoped identities.
- The label registry contains local-only validation artifacts from this executor
  run, including the obsolete pre-scope ES/2024 `fwd_ret_5m` artifact noted
  above. Current scoped identity checks ignore it.
- `ruff` is unavailable in the active environment, so lint was not actually
  performed despite `tools/verify.py --lint` exiting 0 with a skip message.

## Review Request Focus

- Confirm roll-splice and maintenance-crossing windows are dropped or flagged
  before return computation.
- Confirm the terminal key is contract-scoped and cannot splice across
  `contract_id`.
- Confirm partition-scoped LabelVersion identity is acceptable registry metadata
  and does not include producer provenance.
- Confirm label-mode scaleout remains a thin wrapper around `run_seed_label_pack`
  and does not introduce a V1 fast label path.
- Confirm checkpoint/resume cannot skip a unit with stale label-version evidence.

## Next Recommended Step

Ralph should stage only the listed commit-eligible files by explicit path, run
its authoritative artifact/git audits, and decide whether to run full 144-unit
local materialization before review.
