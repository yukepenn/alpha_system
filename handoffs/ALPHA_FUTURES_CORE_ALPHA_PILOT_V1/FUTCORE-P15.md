# FUTCORE-P15 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P15` - Minimal Missing FeatureRequest / LabelSpec Additions, If Needed  
Executor: Codex GPT-5.5  
Lane: Yellow  
Status: executor work complete; Ralph review, staging, commit, PR, CI, and merge actions pending

## Decision

Decision recorded: **Minimal additions**.

The P13 gap list was not empty, and P14 StudySpecs still carry P15 gap ids for
`10m`, `15m`, `30m`, grouped causal OHLCV derived features, and BBO top-book
confirmation. The locked P03 pack still resolves only the two session-context
FeaturePack members and the `fwd_ret_5m` LabelPack member, so a no-op would not
close the accepted StudySpec input gaps.

## Primitive Mapping

Exactly five governed primitive budget items were added, matching the P13 cap.

| P13 gap | Governed record | Governance id | StudySpec mapping | Code impact |
| --- | --- | --- | --- | --- |
| `P15-G1` | `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_10m.json` | `lspec_297ba9c00b50043020a1945e` | `sspec_16f6de31387d8289d0fbb394`; horizon-matrix StudySpecs `sspec_ab3cbb830a2cede5485de19b`, `sspec_8b8037013e7b3c14fd5b2844`, `sspec_28e943d62d4b2eb29a8c445f`, `sspec_b4f5d27095d4f419c078bbcc`, `sspec_62f0ef13ec4f47c2f8c1c784`, `sspec_98d73578b6891eefe52eece5` | Existing fixed-horizon label code already supported `fwd_ret_10m`. |
| `P15-G2` | `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json` | `lspec_c9e388fde3d860ae012b2ad0` | `sspec_fc7b0408e59a83f2e69714d3`; the same horizon-matrix StudySpecs | Added minimal `fwd_ret_15m` enum and horizon mapping plus focused unit tests. |
| `P15-G3` | `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_30m.json` | `lspec_85a5a466430a814f6a608b2c` | `sspec_6fe5fa12b333d19ea95915d2`; the same horizon-matrix StudySpecs | Existing fixed-horizon label code already supported `fwd_ret_30m`. |
| `P15-G4` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g4_causal_ohlcv_derived.json` | `freq_ef650ea8306d52dd9edfb6a3` | `sspec_16f6de31387d8289d0fbb394`, `sspec_fc7b0408e59a83f2e69714d3`, `sspec_6fe5fa12b333d19ea95915d2`, `sspec_ab3cbb830a2cede5485de19b`, `sspec_8b8037013e7b3c14fd5b2844`, `sspec_28e943d62d4b2eb29a8c445f`, `sspec_b4f5d27095d4f419c078bbcc`, `sspec_62f0ef13ec4f47c2f8c1c784` | Existing OHLCV and structure feature families already cover the grouped causal primitives; no feature code changed. |
| `P15-G5` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g5_bbo_top_book_confirmation.json` | `freq_5ed19554444f449b7c2da377` | `sspec_98d73578b6891eefe52eece5` | Existing BBO feature family already covers the grouped top-book confirmation primitives; no feature code changed. |

## Files Written Or Updated

- `research/futures_core_alpha_pilot_v1/feature_requests/DECISION.md`
- `research/futures_core_alpha_pilot_v1/feature_requests/p15_g4_causal_ohlcv_derived.json`
- `research/futures_core_alpha_pilot_v1/feature_requests/p15_g5_bbo_top_book_confirmation.json`
- `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_10m.json`
- `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json`
- `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_30m.json`
- `src/alpha_system/labels/families/fixed_horizon/family.py`
- `tests/unit/labels/families/fixed_horizon/test_fixed_horizon_family.py`
- `docs/futures_core_alpha_pilot/PRIMITIVE_ADDITIONS.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P15.md`

No `src/alpha_system/features/**` files were changed because existing feature
families already covered `P15-G4` and `P15-G5`. No `tests/unit/features/**`
files were changed.

## Staging Status

Codex staged no files. The user override explicitly directed Codex not to run
`git add`, `git commit`, `git push`, `git status`, or `git diff`. Ralph owns
authoritative staging and commit.

Staged files by Codex:

- None.

Commit-eligible files for Ralph explicit staging:

- `research/futures_core_alpha_pilot_v1/feature_requests/DECISION.md`
- `research/futures_core_alpha_pilot_v1/feature_requests/p15_g4_causal_ohlcv_derived.json`
- `research/futures_core_alpha_pilot_v1/feature_requests/p15_g5_bbo_top_book_confirmation.json`
- `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_10m.json`
- `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json`
- `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_30m.json`
- `src/alpha_system/labels/families/fixed_horizon/family.py`
- `tests/unit/labels/families/fixed_horizon/test_fixed_horizon_family.py`
- `docs/futures_core_alpha_pilot/PRIMITIVE_ADDITIONS.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P15.md`

No `runs/**` path should be staged.

## Validation Run By Codex

```bash
test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP && test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P15/STOP
```

Result: exit code `0`; no active STOP file was present.

```bash
PYTHONPATH=src python - <<'PY'
... validate_feature_request and validate_label_spec over P15 JSON records ...
PY
```

Result: exit code `0`; output `governance records validated`.

```bash
PYTHONPATH=src pytest tests/unit/labels/families/fixed_horizon/test_fixed_horizon_family.py
```

First run result: exit code `1`. Failure was a test assertion type mismatch
between `Decimal` and `float` in the new negative same-bar assertion. The test
was corrected to compare floats.

Rerun result: exit code `0`; `9 passed in 0.10s`.

```bash
python tools/verify.py --smoke
```

Result: exit code `0`; no stdout.

```bash
python tools/verify.py --all
```

Result: exit code `0`; verifier ran compileall and pytest; `2811 passed,
7 skipped in 42.87s`.

```bash
python tools/hooks/canary_runner.py
```

Result: exit code `0`; all Frontier canaries passed.

```bash
test -f research/futures_core_alpha_pilot_v1/feature_requests/DECISION.md
```

Result: exit code `0`.

```bash
git ls-files runs
```

Result: exit code `0`; empty output.

```bash
git ls-files '**/*.parquet' '**/*.sqlite'
```

Result: exit code `0`; empty output.

```bash
git ls-files '**/*.dbn' '**/*.zst' '**/*.arrow' '**/*.feather' '**/*.db'
```

Result: exit code `0`; empty output.

Additional artifact check:

```bash
git ls-files '**/*.sqlite3' '**/*.db-journal' '**/*.wal' '**/*.log'
```

Result: exit code `0`; empty output.

Validation intentionally not run by Codex:

- `git status --short`: not run because the user explicitly forbade
  `git status`.
- `git diff --cached --name-only`: not run because the user explicitly forbade
  `git diff`, and Codex staged nothing.
- Any `git add`, `git commit`, or `git push`: not run because the user
  explicitly forbade staging and committing.
- Fresh Yellow-lane Claude review: not run because the user explicitly forbade
  calling Claude or running reviewer.
- `review.md` and `verdict.json`: not created because the user explicitly
  forbade creating them. Ralph owns reviewer artifacts and verdict parsing.

## Artifact And Boundary Confirmation

- `git ls-files runs` returned empty.
- Tracked Parquet, SQLite, DBN, Zst, Arrow, Feather, DB, WAL, DB journal, and
  log globs returned empty.
- No raw/canonical market data, provider responses, materialized feature values,
  materialized label values, heavy artifacts, local DB/registry files, logs,
  caches, secrets, or credentials were added.
- No live trading, paper trading, broker/order call, account operation,
  deployment, PR creation, merge, reviewer call, review artifact, or verdict
  action was performed.
- The work remains research-only and value-free. It makes no alpha,
  profitability, tradability, production, broker, paper/live, or
  capital-allocation claim.
