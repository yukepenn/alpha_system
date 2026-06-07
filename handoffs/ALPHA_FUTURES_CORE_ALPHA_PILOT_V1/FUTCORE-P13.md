# FUTCORE-P13 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P13` - Data Contract / FeaturePack / LabelPack Audit  
Executor: Codex GPT-5.5  
Lane: Yellow  
Status: executor work complete, review and authoritative staging pending Ralph

## Scope Completed

- Audited the 10 `accept-for-StudySpec` AlphaSpecs from the P12 budget audit.
- Resolved the P03 locked DatasetVersion, FeaturePack, and LabelPack references
  through sanctioned registry/resolver surfaces by reference only.
- Confirmed the two locked FeaturePack members carry non-empty `available_ts`
  windows and the locked `fwd_ret_5m` LabelPack member carries a non-empty
  `label_available_ts` window.
- Wrote the per-AlphaSpec primitive mapping and the minimal P15 gap list.
- Updated the durable docs page and README snapshot.

No consumed primitive under `src/alpha_system/**` was edited. No tests were
added or modified. No FeatureRequest, LabelSpec, StudySpec, diagnostic, review
artifact, `review.md`, `verdict.json`, PR, merge, staging, commit, provider
call, raw/value data read, live, paper, broker, order, account, deployment, or
production action was performed.

## Files Written Or Updated

- `research/futures_core_alpha_pilot_v1/audits/data_contract/AUDIT.md`
- `research/futures_core_alpha_pilot_v1/audits/data_contract/gap_list.md`
- `docs/futures_core_alpha_pilot/DATA_CONTRACT_AUDIT.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P13.md`

## Explicit Commit-Eligible File List For Ralph

The executor staged nothing. Ralph should stage only these paths explicitly,
subject to its authoritative artifact and staged-set checks:

- `research/futures_core_alpha_pilot_v1/audits/data_contract/AUDIT.md`
- `research/futures_core_alpha_pilot_v1/audits/data_contract/gap_list.md`
- `docs/futures_core_alpha_pilot/DATA_CONTRACT_AUDIT.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P13.md`

No `runs/**` path should be staged.

## Audit Outcome

Locked and available by reference:

- DatasetVersion `dsv_databento_ohlcv_05404069799decb0` resolves for ES/NQ/RTY
  OHLCV 1 minute bars.
- FeatureVersion
  `fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f`
  resolves as `base_ohlcv_rth_flag` with non-empty `available_ts`.
- FeatureVersion
  `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978`
  resolves as `base_ohlcv_session_minute` with non-empty `available_ts`.
- LabelVersion
  `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395`
  resolves as `fwd_ret_5m` with non-empty `label_available_ts`.
- One value-free `StudyInputPack` shape validates for each accepted AlphaSpec
  using the locked feature request ids and label spec id.

Minimal P15 gap budget items:

1. `fwd_ret_10m` LabelPack binding.
2. `fwd_ret_15m` LabelPack binding.
3. `fwd_ret_30m` LabelPack binding.
4. Grouped causal OHLCV derived FeaturePack binding.
5. Grouped BBO top-book confirmation FeaturePack binding.

The gap list has exactly five candidate request budget items and does not
exceed the campaign cap. P15 still owns any implementation or no-op decision.

## Validation Run By Codex

```bash
test ! -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP
```

Result: exit code `0`; no active STOP file was present.

```bash
PYTHONPATH=src python - <<'PY'
... resolve_dataset_version, FeatureLabelPackResolver, validate_study_input_pack ...
PY
```

Result: exit code `0`. Resolved DatasetVersion
`dsv_databento_ohlcv_05404069799decb0`, two FeaturePack handles, one LabelPack
handle, and 10 value-free per-AlphaSpec `StudyInputPack` shapes. The feature
handles carried non-empty `available_ts`; the label handle carried non-empty
`label_available_ts`.

```bash
PYTHONPATH=src python - <<'PY'
... registry inventory count ...
PY
```

Result: exit code `0`. Feature registry record count was `2`
(`base_ohlcv_rth_flag`, `base_ohlcv_session_minute`); label registry record
count was `1` (`fwd_ret_5m`); all reported `value_store_format=dual`.

```bash
python -c "import alpha_system.governance.study_input_pack"
```

Result: exit code `1`. Failure:
`ModuleNotFoundError: No module named 'alpha_system'`. Reason: this executor
shell does not have `src` on `PYTHONPATH` for the exact command in the generated
spec.

Fallback import check:

```bash
PYTHONPATH=src python -c "import alpha_system.governance.study_input_pack"
```

Result: exit code `0`.

```bash
python tools/verify.py --smoke
```

Result: exit code `0`; no stdout.

```bash
test -d research/futures_core_alpha_pilot_v1/audits/data_contract
```

Result: exit code `0`.

```bash
test -f docs/futures_core_alpha_pilot/DATA_CONTRACT_AUDIT.md
```

Result: exit code `0`.

```bash
test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P13.md
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

## Review Artifacts

Codex did not create `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P13/**`
artifacts, `review.md`, or `verdict.json` because the user override explicitly
forbade reviewer execution and review/verdict artifact creation. Ralph owns
review orchestration and verdict parsing.

## Boundaries

The work remains research-only and value-free. It adds no raw/canonical data,
feature values, label values, provider responses, Parquet/Arrow/Feather, DBN,
Zstd, SQLite/DB/WAL files, logs, caches, secrets, tests, runtime behavior,
broker/live/paper/order code, deployment behavior, diagnostics, StudySpecs,
FeatureRequests, LabelSpecs, promotion decisions, review artifacts, PR/merge
actions, staging, or commits.
