# Repo Integrity Sweep V1 - Root Cause Matrix

Date: 2026-06-16
Branch: `fix/repo-integrity-precondition-data-consistency-v1`
Scope: repo integrity / generic fixes only. No alpha mining, no materialization,
no broker/paper/live work, and no promotion rail changes.

## Matrix

| Bug class | Observed failure mode | Root cause | Generic fix | Guard |
| --- | --- | --- | --- | --- |
| Env/dependency masked as data absence | Missing `polars`, bad root, or registry failure surfaced downstream as `DATA_GAP`. | Callers let resolver/load exceptions fall into data-gap paths. | Preserve `environment_preflight`; classify fast-probe unresolved inputs by cause; gate resolver failures now separates precondition/registry from true gap. | `precondition_not_datagap`; unit tests in `test_environment_preflight.py`, `test_fast_probe.py`, `test_testability_gate.py`. |
| Deprecated pack pin masked at run time | Authored idea with stale fver/lver could validate, then fail later in a confusing run/gate path. | `alpha idea validate` built governance objects but did not audit versioned pack lifecycle. | Added value-free `pack_pin_audit` and validate-time registry check for ideas carrying fver/lver refs. | `pack_pin_validate_not_datagap`; `test_idea_validate_fails_loud_on_deprecated_pack_pin`. |
| Cross-DatasetVersion replacement ambiguity | BBO-deprecated labels can name OHLCV replacements; auto-use would mix datasets. | Replacement metadata existed, but validate had no front-door fail-loud check. | Validate reports `DATASET_VERSION_MISMATCH`; runtime resolver already fails closed on exact DatasetVersion mismatch. No auto-adopt. | `pack_pin_validate_not_datagap`; `test_idea_validate_fails_loud_on_cross_dataset_replacement`. |
| Pack-pin FAIL masked by later DATA_GAP | A deprecated/mismatch resolver rejection could be a check-level `FAIL` but overall status became `DATA_GAP`. | Gate rollup ranked `DATA_GAP` before `FAIL`. | Gate rollup now ranks `ENVIRONMENT_NOT_CONFIGURED` > `FAIL` > `DATA_GAP` > `PASS`. | `test_gate_deprecated_pack_pin_fails_not_datagaps`; canary rollup assertion. |
| Missing value file indistinguishable from substrate gap | `fast_probe` unresolved readout always used `DATA_GAP`. | Single `build_fast_probe_data_gap` issue code. | Added top-level and row-access issue code classification: `MISSING_DEPENDENCY`, `ALPHA_DATA_ROOT_MISSING`, `REGISTRY_UNAVAILABLE`, `DEPRECATED_PACK_PIN`, `DATASET_VERSION_MISMATCH`, `VALUE_FILE_MISSING`, `TRUE_DATA_GAP`. | `test_fast_probe_missing_value_file_is_value_file_missing`; existing routing canaries. |
| Live prose drift | Schema map carried live-status wording (`live exemplar`, survivor count). | Historical docs used present-tense operational language. | Reworded the schema map as historical IVL context and pointed survivor status to live tools/ledger. | Targeted `rg` scan over live pointer docs. |
| Hook drift | `status_doctor` warned `core.hooksPath` was absolute. | Local git config drift. | Set local hooks path to `.githooks`. | `status_doctor` now OK. |
| Stale branches/worktrees | Merged PR heads and local worktree branches remained after merge. | Branch/worktree cleanup did not run after PR merge. | Deleted merged `fix-52-conditioned-power-gate` remote head, removed stale worktree and local worktree branches, pruned stale remote-tracking ref. | `git worktree list`, `git branch --all`, `gh pr list --head`. |

## Non-Changes

- No raw/canonical/value parquet or registry SQLite was deleted.
- No DatasetVersion invariant was weakened.
- No multi-dataset slice support was introduced.
- No compute-on-demand fast lane was implemented.
- No FDR/power/promotion rails were weakened; existing canaries still pass.
