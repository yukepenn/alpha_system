# Handoff - FUTCORE-P04

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P04` - CostModelVersion and Session-Specific Cost Stress Contract  
Executor: Codex  
Date: 2026-06-07

## Executor Status

Execution artifacts are written and left unstaged in the working tree. This
handoff does not mark the phase PASS; Ralph owns validation orchestration,
review, staging, commit, PR, CI, merge, and done-check.

No source primitive under `src/alpha_system/**` was edited. No tests were added
or modified. No runtime diagnostics, `cost` tool, provider call, broker/live/
paper/order/account/deployment action, destructive cleanup, PR, merge, commit,
reviewer call, `review.md`, or `verdict.json` was performed or created.

## Files Written Or Updated

- `research/futures_core_alpha_pilot_v1/cost_model/cost_model_contract.md`
- `docs/futures_core_alpha_pilot/COST_MODEL.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P04.md`

## Explicit Commit-Eligible File List For Ralph

The executor staged nothing. Ralph should stage only these paths explicitly,
subject to its authoritative artifact and staged-set checks:

- `research/futures_core_alpha_pilot_v1/cost_model/cost_model_contract.md`
- `docs/futures_core_alpha_pilot/COST_MODEL.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P04.md`

No `runs/**` path should be staged.

## CostModelVersion Summary

The contract pins `CostModelVersion`
`cmv_futcore_pilot_three_layer_session_stress_v1` at semantic version `1.0.0`.
It is bound by reference to the `FUTCORE-P03` input-pack ids/hashes only:

- DatasetVersion: `dsv_databento_ohlcv_05404069799decb0`
- FeatureVersions:
  `fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f`,
  `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978`
- LabelVersion:
  `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395`

The three cost layers are:

- Layer 1 - hard transaction cost placeholders for broker/exchange/clearing/
  regulatory fee schedules, with declared units and dated/versioned references
  where later reviewed config supports them.
- Layer 2 - spread crossing methodology over valid point-in-time BBO
  bid/ask/mid/`spread_ticks`, with missing/invalid BBO explicitly flagged and
  never fabricated.
- Layer 3 - bucketed slippage and capacity proxy methodology, scaled by profile
  and session overlays. It is proxy-only and not realized slippage, market
  impact, fill capacity proof, or tradability evidence.

The stress ladder is exactly `zero_cost`, `base`, `stress_1`, `stress_2`, and
`double_cost`. `zero_cost` is explicitly diagnostic-only and never a promotion
basis. `base` is the central non-zero assumption; `stress_1` and `stress_2` are
escalating non-zero stress sensitivities; `double_cost` is the upper stress
bound relative to `base` before thin-session overlays under the same inputs.

Thin-session rules require stricter spread, slippage, and capacity proxy
treatment for `ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, and
`post_RTH`. ETH remains research-in-scope but not trading-approved. `1m` and
`3m` horizons remain execution-fragile diagnostics only, especially in thin
session views. No capacity or tradability claim is made.

## Validation Commands

STOP checks before validation:

```bash
test -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP
```

Result: exit code `1`; no active run-root STOP file was present.

```bash
test -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P04/STOP
```

Result: exit code `1`; no active phase-root STOP file was present.

Spec validation commands:

`git status --short` was not run because the executor instructions explicitly
forbid `git status`.

`git diff --cached --name-only` was not run because the executor instructions
explicitly forbid `git diff`.

```bash
python tools/verify.py --smoke
```

Result: exit code `0`.

```bash
test -f research/futures_core_alpha_pilot_v1/cost_model/cost_model_contract.md
```

Result: exit code `0`.

```bash
test -f docs/futures_core_alpha_pilot/COST_MODEL.md
```

Result: exit code `0`.

```bash
test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P04.md
```

Result: exit code `0`.

```bash
git ls-files runs
```

Result: exit code `0`; empty output.

```bash
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'
```

Result: exit code `0`; empty output.

## Artifact Confirmation

The executor did not stage any file. `git ls-files runs` returned empty, and the
requested heavy-artifact glob check returned empty. Because this executor was
forbidden from running `git diff --cached --name-only`, authoritative staged-set
verification remains with Ralph before commit. No run-local handoff, review,
verdict, checks, repair artifact, raw/canonical data, feature value, label value,
provider response, Parquet/SQLite/DBN/Zstd artifact, local DB, log, cache,
secret, or credential was intentionally created for commit.

## Forward Notes

- `FUTCORE-P05` should make the AlphaSpec batch protocol cite
  `cmv_futcore_pilot_three_layer_session_stress_v1` and the exact profile
  ladder rather than allowing ad hoc cost assumptions.
- `FUTCORE-P16` through `FUTCORE-P20` should consume the contract when later
  diagnostics run through sanctioned runtime tools over approved StudySpecs and
  locked input packs.
- `FUTCORE-P21` should consolidate `zero_cost`/`base`/`stress_1`/`stress_2`/
  `double_cost` outcomes and flag zero-cost-only, under-stressed, and
  thin-session-fragile outcomes.
- `FUTCORE-P22` should carry thin-session and horizon limitations into the
  session x horizon matrix.
