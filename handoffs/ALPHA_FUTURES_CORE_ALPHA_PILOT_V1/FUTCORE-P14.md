# FUTCORE-P14 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P14` - Approved StudySpec Pack  
Executor: Codex GPT-5.5  
Lane: Yellow  
Status: executor work complete; Ralph-owned review, authoritative staging, and merge flow remain pending

## Scope Completed

- Refreshed one value-free governance `StudySpec` per `FUTCORE-P12`
  accepted AlphaSpec.
- Bound each StudySpec to the `FUTCORE-P03` DatasetVersion and the
  `FUTCORE-P13` corrected FeaturePack / LabelPack ids and hashes by reference
  only.
- Corrected stale session FeatureVersion references from the prior P14 artifact:
  `base_ohlcv_rth_flag` now binds `fver_acbfa783...`, and
  `base_ohlcv_session_minute` now binds `fver_fd739ad...`.
- Bound `5m`, `10m`, and `30m` labels as locked P03/P13 labels and carried
  only `15m` as the pending horizon-label gap.
- Recorded the required session x horizon matrix, `FUTCORE-P04` cost profile
  ladder, thin-session penalty applicability, family no-lookahead audit targets,
  and finite per-study `variant_budget`.
- Wrote the StudySpec traceability index, the durable docs summary, and the
  compact README snapshot.

No diagnostics, feature/label/signal/cost computations, consumed primitive
edits, FeatureRequests, LabelSpecs, review artifacts, verdicts, PR, merge,
staging, commit, provider calls, raw/value data reads, broker/live/paper/order,
deployment, or favorable evidence action was performed by Codex.

## Curated File Paths For Ralph

Codex staged no files. The user override explicitly directed Codex not to run
`git add`, `git commit`, `git push`, `git status`, or `git diff`. Ralph owns
authoritative staging and commit.

Commit-eligible files for Ralph explicit staging:

- `research/futures_core_alpha_pilot_v1/study_specs/study_specs.json`
- `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md`
- `research/futures_core_alpha_pilot_v1/study_specs/sspec_dde3e64667fe158f9bad527d.json`
- `research/futures_core_alpha_pilot_v1/study_specs/sspec_c671fbeeb143512cbc03bc5b.json`
- `research/futures_core_alpha_pilot_v1/study_specs/sspec_90b28233d828128664588a9a.json`
- `research/futures_core_alpha_pilot_v1/study_specs/sspec_7c8fb13628843890c171b122.json`
- `research/futures_core_alpha_pilot_v1/study_specs/sspec_69c22ec5847395ac8e81b5b6.json`
- `research/futures_core_alpha_pilot_v1/study_specs/sspec_aff70fcbc4b7ff226fcc8149.json`
- `research/futures_core_alpha_pilot_v1/study_specs/sspec_267cc052e37668339c38d179.json`
- `research/futures_core_alpha_pilot_v1/study_specs/sspec_27bf1262b0bd23d27191cc86.json`
- `research/futures_core_alpha_pilot_v1/study_specs/sspec_02c400a561891171a33c0c66.json`
- `research/futures_core_alpha_pilot_v1/study_specs/sspec_9f6f741192a4b534f06e51c0.json`
- `docs/futures_core_alpha_pilot/STUDY_SPECS.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P14.md`

No `runs/**` path should be staged.

## StudySpec Traceability

| AlphaSpec id | StudySpec id | Family | P13 mapping | P15 gaps carried | Variant budget |
| --- | --- | --- | --- | --- | ---: |
| `aspec_0ebd90cecfd475607685b445` | `sspec_dde3e64667fe158f9bad527d` | `cross_market` | `AVAILABLE_BUT_NEEDS_REVIEW` | no P15 gap for locked `5m` baseline | 4 |
| `aspec_8d9e272e4b78eedcd27f0bec` | `sspec_c671fbeeb143512cbc03bc5b` | `cross_market` | `MISSING` | `P15-G3` | 4 |
| `aspec_a41dcccac5552de945aba825` | `sspec_90b28233d828128664588a9a` | `cross_market` | `MISSING` | `P15-G1`, `P15-G3` | 4 |
| `aspec_fa4895a43a80d4eef0a607a4` | `sspec_7c8fb13628843890c171b122` | `cross_market` | `MISSING` | `P15-G3` | 4 |
| `aspec_b40aee52d4399dd5b855a6ed` | `sspec_69c22ec5847395ac8e81b5b6` | `vwap_session` | `MISSING` | `P15-G1`, `P15-G2` | 4 |
| `aspec_43cd6c154bca2fcc419eee83` | `sspec_aff70fcbc4b7ff226fcc8149` | `vwap_session` | `MISSING` | `P15-G1`, `P15-G2` | 4 |
| `aspec_eb962fc197eaf3955c5e4711` | `sspec_267cc052e37668339c38d179` | `regime` | `MISSING` | `P15-G1`, `P15-G4` | 4 |
| `aspec_df2d040e45564c259ef3de6d` | `sspec_27bf1262b0bd23d27191cc86` | `liquidity_pa` | `MISSING` | `P15-G1`, `P15-G4` | 4 |
| `aspec_39ffc190cfbfa6ba0b1a2a25` | `sspec_02c400a561891171a33c0c66` | `liquidity_pa` | `MISSING` | `P15-G1`, `P15-G4` | 4 |
| `aspec_1284e49b083df11eeb0481ea` | `sspec_9f6f741192a4b534f06e51c0` | `bbo_tradability` | `MISSING` | `P15-G1`, `P15-G5` | 4 |

The canonical JSON pack is
`research/futures_core_alpha_pilot_v1/study_specs/study_specs.json`. Each
object validates with `alpha_system.governance.study_spec.validate_study_spec`
and carries a handle-only `StudyInputPack` shape.

## Family Budget Reconciliation

| Family | Required budget | StudySpecs | Share | Reconciliation |
| --- | ---: | ---: | ---: | --- |
| `cross_market` | 40% | 4 | 40% | Aligned with P12 accepted allocation. |
| `vwap_session` | 20% | 2 | 20% | Aligned with P12 accepted allocation. |
| `regime` | 15% | 1 | 10% | Matches P12 integer-rounding note. |
| `liquidity_pa` | 15% | 2 | 20% | Matches P12 integer-rounding note. |
| `bbo_tradability` | 10% | 1 | 10% | Aligned with P12 accepted allocation. |
| **Total** | 100% | **10** | **100%** | Approved cap `<=10` is held. |

Every StudySpec declares `variant_budget: 4`. The two predeclared variant axes
in each payload create at most four parameter combinations. Sessions, horizons,
instruments, and cost profiles are fixed diagnostic/reporting slices and are
not additional grid knobs.

## Deferred Gap Items For FUTCORE-P15

The StudySpecs carry forward the P13 gap list by id without implementing it:

1. `P15-G1` - `fwd_ret_15m` LabelPack binding.
2. `P15-G2` - VWAP/session FeaturePack binding.
3. `P15-G3` - cross-market derived-state FeaturePack binding.
4. `P15-G4` - additional base-OHLCV derived-state FeaturePack binding for
   regime and liquidity/PA.
5. `P15-G5` - BBO top-book confirmation FeaturePack binding.

`fwd_ret_10m` and `fwd_ret_30m` are not deferred because P03/P13 resolve them
with valid `label_available_ts` metadata.

Diagnostics that require a pending horizon label, derived OHLCV primitive,
VWAP/session primitive, cross-market derived state, or BBO primitive must stop
until `FUTCORE-P15` resolves the binding or records an explicit no-op
constraint.

## Validation Run By Codex

```bash
test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP && test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P14/STOP
```

Result: exit code `0`; no active STOP file was present.

```bash
PYTHONPATH=src python - <<'PY'
... validate 10 StudySpec objects, matching StudyInputPack shapes, family counts,
    variant budgets, horizon bindings, individual sspec files, and stale-id absence ...
PY
```

Result: exit code `0`; output:

```text
study_specs 10
ids_unique True
families {'bbo_tradability': 1, 'cross_market': 4, 'liquidity_pa': 2, 'regime': 1, 'vwap_session': 2}
variant_budgets [4]
schema_validation ok
```

```bash
python -c "import alpha_system.governance.study_spec"
```

Result: exit code `0`; no stdout.

```bash
python tools/verify.py --smoke
```

Result: exit code `0`; no stdout.

```bash
test -d research/futures_core_alpha_pilot_v1/study_specs
```

Result: exit code `0`; no stdout.

```bash
test -f docs/futures_core_alpha_pilot/STUDY_SPECS.md && test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P14.md
```

Result: exit code `0`; no stdout.

```bash
git ls-files runs
```

Result: exit code `0`; empty output.

```bash
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'
```

Result: exit code `0`; empty output.

Supplemental generated-artifact scan for stale session FeatureVersion ids and
forbidden claim/state tokens across the P14 StudySpec pack, docs page, README,
and handoff.

Result: exit code `0`; empty output before this handoff was refreshed. The
same token family was checked again after the handoff refresh.

Validation intentionally not run by Codex:

- `git status --short`: not run because the user explicitly forbade
  `git status`.
- `git diff --cached --name-only`: not run because the user explicitly forbade
  `git diff`, and Codex staged nothing. Ralph owns authoritative staged-set
  validation.
- `git add`, `git commit`, `git push`: not run because the user explicitly
  forbade staging and committing.
- Fresh Yellow-lane semantic review: not run because the user explicitly
  forbade calling Claude or running reviewer. Ralph owns review orchestration.
- `review.md` and `verdict.json`: not created because the user explicitly
  forbade creating them. Ralph owns reviewer artifacts and verdict parsing.

## Review Artifacts

Codex did not create
`reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P14/**` artifacts,
`review.md`, or `verdict.json` because the user override explicitly forbade
reviewer execution and review/verdict artifact creation. Ralph owns review
orchestration and verdict parsing.

## README Snapshot Summary

`README.md` now records that `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` has advanced
through `FUTCORE-P14` in the `spec_audit_and_packs` gate, names `FUTCORE-P15`
as the next phase, lists the StudySpec pack and docs index as the new durable
surfaces, and preserves the research-only, no broker/live/paper/deployment,
explicit-staging, local-only `runs/**`, and no heavy/raw/value/DB artifact
boundaries.

## Boundaries

The work remains research-only and value-free. It adds no raw/canonical data,
feature values, label values, provider responses, Parquet/Arrow/Feather, DBN,
Zstd, SQLite/DB/WAL files, logs, caches, secrets, tests, runtime behavior,
broker/live/paper/order code, deployment behavior, diagnostics, FeatureRequests,
LabelSpecs, review artifacts, PR/merge actions, staging, or commits.
