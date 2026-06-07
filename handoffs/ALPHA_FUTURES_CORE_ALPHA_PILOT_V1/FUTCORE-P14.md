# FUTCORE-P14 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P14` - Approved StudySpec Pack  
Executor: Codex GPT-5.5  
Lane: Yellow  
Status: executor work complete, review and authoritative staging pending Ralph

## Scope Completed

- Authored one value-free governance `StudySpec` per `FUTCORE-P12` accepted
  AlphaSpec.
- Bound each StudySpec to the locked `FUTCORE-P03` DatasetVersion,
  FeaturePack, and LabelPack ids/hashes by reference only.
- Bound the required session x horizon matrix, the `FUTCORE-P04` cost profile
  ladder, thin-session penalty applicability, no-lookahead timing discipline,
  and a finite per-study `variant_budget`.
- Wrote the StudySpec traceability index and the durable docs summary.
- Updated `README.md` with the compact `FUTCORE-P14` campaign snapshot.

No diagnostics, factor/label/signal/cost computations, primitive edits,
FeatureRequests, LabelSpecs, review artifacts, verdicts, PR, merge, staging,
commit, provider calls, raw/value data reads, broker/live/paper/order,
deployment, or promotion action was performed by Codex.

## Staging Status

Codex staged no files. The user override explicitly directed Codex not to run
`git add`, `git commit`, `git push`, `git status`, or `git diff`. Ralph owns
authoritative staging and commit.

Staged files by Codex:

- None.

Commit-eligible files for Ralph explicit staging:

- `research/futures_core_alpha_pilot_v1/study_specs/study_specs.json`
- `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md`
- `docs/futures_core_alpha_pilot/STUDY_SPECS.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P14.md`

No `runs/**` path should be staged.

## StudySpec Traceability

| AlphaSpec id | StudySpec id | Family | P13 mapping | P15 gaps carried | Variant budget |
| --- | --- | --- | --- | --- | ---: |
| `aspec_0ebd90cecfd475607685b445` | `sspec_ac883ec0b962f4ae4f25e190` | `cross_market` | `AVAILABLE_BUT_NEEDS_REVIEW` | none for locked `5m` baseline | 4 |
| `aspec_8d9e272e4b78eedcd27f0bec` | `sspec_16f6de31387d8289d0fbb394` | `cross_market` | `MISSING` | `P15-G1`, `P15-G4` | 4 |
| `aspec_a41dcccac5552de945aba825` | `sspec_fc7b0408e59a83f2e69714d3` | `cross_market` | `MISSING` | `P15-G2`, `P15-G4` | 4 |
| `aspec_fa4895a43a80d4eef0a607a4` | `sspec_6fe5fa12b333d19ea95915d2` | `cross_market` | `MISSING` | `P15-G3`, `P15-G4` | 4 |
| `aspec_b40aee52d4399dd5b855a6ed` | `sspec_ab3cbb830a2cede5485de19b` | `vwap_session` | `MISSING` | `P15-G1`, `P15-G2`, `P15-G3`, `P15-G4` | 4 |
| `aspec_43cd6c154bca2fcc419eee83` | `sspec_8b8037013e7b3c14fd5b2844` | `vwap_session` | `MISSING` | `P15-G1`, `P15-G2`, `P15-G3`, `P15-G4` | 4 |
| `aspec_eb962fc197eaf3955c5e4711` | `sspec_28e943d62d4b2eb29a8c445f` | `regime` | `MISSING` | `P15-G1`, `P15-G2`, `P15-G3`, `P15-G4` | 4 |
| `aspec_df2d040e45564c259ef3de6d` | `sspec_b4f5d27095d4f419c078bbcc` | `liquidity_pa` | `MISSING` | `P15-G1`, `P15-G2`, `P15-G3`, `P15-G4` | 4 |
| `aspec_39ffc190cfbfa6ba0b1a2a25` | `sspec_62f0ef13ec4f47c2f8c1c784` | `liquidity_pa` | `MISSING` | `P15-G1`, `P15-G2`, `P15-G3`, `P15-G4` | 4 |
| `aspec_1284e49b083df11eeb0481ea` | `sspec_98d73578b6891eefe52eece5` | `bbo_tradability` | `MISSING` | `P15-G1`, `P15-G2`, `P15-G3`, `P15-G5` | 4 |

The canonical JSON pack is
`research/futures_core_alpha_pilot_v1/study_specs/study_specs.json`. Each
object validates with `alpha_system.governance.study_spec.validate_study_spec`
and carries a handle-only `StudyInputPack` shape with the two locked
FeatureRequest ids and locked `5m` LabelSpec id.

## Family Budget Reconciliation

| Family | Required budget | StudySpecs | Share | Reconciliation |
| --- | ---: | ---: | ---: | --- |
| `cross_market` | 40% | 4 | 40% | Adheres to P12 accepted allocation. |
| `vwap_session` | 20% | 2 | 20% | Adheres to P12 accepted allocation. |
| `regime` | 15% | 1 | 10% | Matches P12 integer-rounding note. |
| `liquidity_pa` | 15% | 2 | 20% | Matches P12 integer-rounding note. |
| `bbo_tradability` | 10% | 1 | 10% | Adheres to P12 accepted allocation. |
| **Total** | 100% | **10** | **100%** | Approved cap `<=10` is held. |

Every StudySpec declares `variant_budget: 4`. The two predeclared variant axes
in each payload create at most four parameter combinations. Sessions, horizons,
instruments, and cost profiles are fixed diagnostic/reporting slices and are
not additional grid knobs.

## Deferred Gap Items For FUTCORE-P15

The StudySpecs carry forward the P13 gap list by id without implementing it:

1. `P15-G1` - `fwd_ret_10m` LabelPack binding.
2. `P15-G2` - `fwd_ret_15m` LabelPack binding.
3. `P15-G3` - `fwd_ret_30m` LabelPack binding.
4. `P15-G4` - grouped causal OHLCV derived FeaturePack binding.
5. `P15-G5` - grouped BBO top-book confirmation FeaturePack binding.

Diagnostics that require a pending horizon label, derived OHLCV primitive, or
BBO primitive must stop until `FUTCORE-P15` resolves the binding or records an
explicit no-op constraint.

## Validation Run By Codex

```bash
test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P14/STOP && test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP
```

Result: exit code `0`; no active STOP file was present.

```bash
python -c "import alpha_system.governance.study_spec"
```

Result: exit code `1`. Failure: `ModuleNotFoundError: No module named
'alpha_system'`. Reason: this executor shell does not have `src` on
`PYTHONPATH` for the exact generated-spec command.

Fallback import check:

```bash
PYTHONPATH=src python -c "import alpha_system.governance.study_spec"
```

Result: exit code `0`.

```bash
PYTHONPATH=src python - <<'PY'
... validate 10 StudySpec objects and matching StudyInputPack shapes ...
PY
```

Result: exit code `0`. Counted 10 StudySpecs with family allocation
`cross_market=4`, `vwap_session=2`, `regime=1`, `liquidity_pa=2`,
`bbo_tradability=1`; all `variant_budget` values were `4`.

```bash
python tools/verify.py --smoke
```

Result: exit code `0`; no stdout.

```bash
test -d research/futures_core_alpha_pilot_v1/study_specs
```

Result: exit code `0`.

```bash
test -f docs/futures_core_alpha_pilot/STUDY_SPECS.md
```

Result: exit code `0`.

```bash
test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P14.md
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

Validation intentionally not run by Codex:

- `git status --short`: not run because the user explicitly forbade
  `git status`.
- Any `git diff` or staged-set command: not run because the user explicitly
  forbade `git diff`, and Codex staged nothing. Ralph owns authoritative
  staging and staged-set validation.
- `git add`, `git commit`, `git push`: not run because the user explicitly
  forbade staging and committing.
- Fresh Yellow-lane Claude review: not run because the user explicitly forbade
  calling Claude or running reviewer. Ralph owns review orchestration.
- `review.md` and `verdict.json`: not created because the user explicitly
  forbade creating them. Ralph owns reviewer artifacts and verdict parsing.
- Full Yellow-lane `lint`, `typecheck`, `test`, and `verify_canaries`: not run
  by Codex in this executor pass; the generated spec states Ralph orchestrates
  Yellow-lane required checks at `CHECKS_RUN`.

## Review Artifacts

Codex did not create
`reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P14/**` artifacts,
`review.md`, or `verdict.json` because the user override explicitly forbade
reviewer execution and review/verdict artifact creation. Ralph owns review
orchestration and verdict parsing.

## Boundaries

The work remains research-only and value-free. It adds no raw/canonical data,
feature values, label values, provider responses, Parquet/Arrow/Feather, DBN,
Zstd, SQLite/DB/WAL files, logs, caches, secrets, tests, runtime behavior,
broker/live/paper/order code, deployment behavior, diagnostics, FeatureRequests,
LabelSpecs, promotion decisions, review artifacts, PR/merge actions, staging,
or commits.
