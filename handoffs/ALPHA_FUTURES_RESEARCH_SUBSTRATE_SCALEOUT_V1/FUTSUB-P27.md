# FUTSUB-P27 Handoff

Phase: `FUTSUB-P27` - Re-lock Core Pilot StudySpecs Against Full Substrate  
Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Date: 2026-06-11  
Executor: Codex

## Scope Completed

- Classified all 10 accepted Core Pilot StudySpecs from
  `research/futures_core_alpha_pilot_v1/study_specs/study_specs.json`.
- Re-issued 8 value-free StudySpec lock documents under
  `research/futures_substrate_scaleout_v1/rerun/study_specs/` through
  `alpha_system.governance.study_spec.create_study_spec`.
- Preserved `alpha_spec_id`, top-level `label_spec_id`, split protocol,
  metrics, costs, variant budget, locked-test policy, negative controls, and
  stopping rules for each re-locked StudySpec.
- Re-issued only dataset-scope DatasetVersion locks, feature locks, label
  locks, StudyInputPack references, and old-to-new provenance.
- Recorded 2 named fail-closed gaps rather than hand-patching or substituting
  locks.
- Added a hermetic unit smoke test over the committed re-lock artifacts.

No diagnostics run, registry write, value materialization, AlphaSpec edit,
LabelSpec edit, source-module edit, original Core Pilot artifact edit, review
call, review artifact, verdict artifact, PR, merge, staging, commit, or push
was performed by the executor.

## Files For Ralph To Stage

- `README.md`
- `docs/futures_substrate_scaleout/CORE_PILOT_RELOCK.md`
- `research/futures_substrate_scaleout_v1/rerun/studyspec_relock.md`
- `research/futures_substrate_scaleout_v1/rerun/study_specs/sspec_1d54b7d14ae9c4a1d7453a81.json`
- `research/futures_substrate_scaleout_v1/rerun/study_specs/sspec_44c3ee4595987af664e7c0d7.json`
- `research/futures_substrate_scaleout_v1/rerun/study_specs/sspec_88a1be32841d4fd955e3f5ee.json`
- `research/futures_substrate_scaleout_v1/rerun/study_specs/sspec_983a98603f6369127405cb33.json`
- `research/futures_substrate_scaleout_v1/rerun/study_specs/sspec_b3b188f263c9abbc128faa80.json`
- `research/futures_substrate_scaleout_v1/rerun/study_specs/sspec_b5ed14fe095c6eeeb1def00e.json`
- `research/futures_substrate_scaleout_v1/rerun/study_specs/sspec_b780acc576267566cabfe28a.json`
- `research/futures_substrate_scaleout_v1/rerun/study_specs/sspec_cde8480dfa70919cfdf224f4.json`
- `tests/unit/futures_substrate_scaleout/test_studyspec_relock_smoke.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P27.md`

The executor left all changes unstaged as instructed. No `runs/` path should be
staged.

## Re-lock Summary

| Original StudySpec | Re-lock StudySpec | Prior state | Family | Targets | Horizons | Feature locks | Label locks | P28 scope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | `sspec_44c3ee4595987af664e7c0d7` | REJECT | cross_market | NQ,ES | 5m,10m,30m | 248 | 48 | audit-only |
| `sspec_c671fbeeb143512cbc03bc5b` | `sspec_983a98603f6369127405cb33` | REJECT | cross_market | NQ,ES,RTY | 5m,10m,30m | 328 | 72 | audit-only |
| `sspec_90b28233d828128664588a9a` | `sspec_b5ed14fe095c6eeeb1def00e` | REJECT | cross_market | RTY,ES,NQ | 5m,10m,15m,30m | 328 | 96 | audit-only |
| `sspec_7c8fb13628843890c171b122` | `sspec_88a1be32841d4fd955e3f5ee` | REJECT | cross_market | NQ,ES | 5m,10m,30m | 248 | 48 | audit-only |
| `sspec_69c22ec5847395ac8e81b5b6` | `sspec_b780acc576267566cabfe28a` | INCONCLUSIVE | vwap_session | ES,NQ,RTY | 5m,10m,15m,30m | 528 | 96 | rerun candidate |
| `sspec_aff70fcbc4b7ff226fcc8149` | `sspec_1d54b7d14ae9c4a1d7453a81` | INCONCLUSIVE | vwap_session | ES,NQ,RTY | 5m,10m,15m,30m | 528 | 96 | rerun candidate |
| `sspec_267cc052e37668339c38d179` | named gap | INCONCLUSIVE | regime | ES,NQ,RTY | 5m,10m,15m,30m | 504 attempted | 96 attempted | blocked |
| `sspec_27bf1262b0bd23d27191cc86` | `sspec_cde8480dfa70919cfdf224f4` | INCONCLUSIVE | liquidity_pa | ES,NQ,RTY | 5m,10m,15m,30m | 600 | 96 | rerun candidate |
| `sspec_02c400a561891171a33c0c66` | `sspec_b3b188f263c9abbc128faa80` | INCONCLUSIVE | liquidity_pa | ES,NQ,RTY | 5m,10m,15m,30m | 600 | 96 | rerun candidate |
| `sspec_9f6f741192a4b534f06e51c0` | named gap | INCONCLUSIVE | bbo_tradability | ES,NQ,RTY | 5m,10m,15m,30m | 648 attempted | 96 attempted | blocked |

Totals for committed re-lock documents: 3408 feature locks and 648 label locks.

## Resolver-Smoke Result

Committed re-locks:

- `FeatureLabelPackResolver.resolve_feature_packs`: PASS for 3408 committed
  feature locks.
- `FeatureLabelPackResolver.resolve_label_packs`: PASS for 648 committed label
  locks.
- `alpha_system.governance.feature_lock_validation.validate_feature_locks`:
  PASS for 3408 committed feature locks.
- `alpha governance validate-feature-locks` CLI path, invoked via
  `python -m alpha_system.cli.main`: PASS, `ok: true`, `lock_count: 3408`,
  `resolved_count: 3408`, `stale_lock_count: 0`.
- Deliberate unresolvable probe:
  `fver_0000000000000000000000000000000000000000000000000000000000000000`
  returned `feature_pack_not_found`.

For each committed lock, the local smoke checked exact ID resolution, registered
lifecycle, expected DatasetVersion, expected partition, expected
FeatureRequest/LabelSpec, value metadata presence, positive record count, and a
real local Parquet file under `ALPHA_DATA_ROOT`. The committed artifacts omit
local file paths and per-row values.

## Previously INCONCLUSIVE Classification

- `sspec_69c22ec5847395ac8e81b5b6` (`vwap_session`): re-locked as
  `sspec_b780acc576267566cabfe28a`; P28 rerun candidate.
- `sspec_aff70fcbc4b7ff226fcc8149` (`vwap_session`): re-locked as
  `sspec_1d54b7d14ae9c4a1d7453a81`; P28 rerun candidate.
- `sspec_267cc052e37668339c38d179` (`regime`): still gapped. Current
  `regime_volatility_compression` records for
  `liquidity_structure_range_contraction` fail `resolve_feature_packs` with
  `label_as_feature_input` on `session_label`.
- `sspec_27bf1262b0bd23d27191cc86` (`liquidity_pa`): re-locked as
  `sspec_cde8480dfa70919cfdf224f4`; P28 rerun candidate.
- `sspec_02c400a561891171a33c0c66` (`liquidity_pa`): re-locked as
  `sspec_b3b188f263c9abbc128faa80`; P28 rerun candidate.
- `sspec_9f6f741192a4b534f06e51c0` (`bbo_tradability`): still gapped. Current
  `bbo_tradability_top_book` records for `bbo_tradability_spread_zscore` fail
  `resolve_feature_packs` with `label_as_feature_input` on `session_label`.

These gaps were routed as substrate/runtime metadata findings. No replacement
features were materialized, no registry records were changed, and resolver
semantics were not weakened.

## Validation

| Command | Outcome |
| --- | --- |
| `git status --short` | NOT RUN; the executor prompt explicitly forbade `git status` |
| `PYTHONPATH=src python -m alpha_system.cli.main governance validate-feature-locks --locks /tmp/futsub_p27_feature_locks.json --registry-path /home/yuke_zhang/alpha_data/alpha_system/registry/features.sqlite > /tmp/futsub_p27_validate_feature_locks.json` | PASS, exit 0; stderr emitted Python runpy warning; JSON output had `ok: true`, `lock_count: 3408`, `resolved_count: 3408`, `stale_lock_count: 0` |
| `PYTHONPATH=src python -m ruff check tests/unit/futures_substrate_scaleout/test_studyspec_relock_smoke.py` | Initial run found import order formatting; fixed mechanically; final run PASS, `All checks passed!` |
| `PYTHONPATH=src python -m ruff format --check tests/unit/futures_substrate_scaleout/test_studyspec_relock_smoke.py` | Initial run would reformat; fixed mechanically; final run PASS, `1 file already formatted` |
| `PYTHONPATH=src python -m pytest tests/unit/futures_substrate_scaleout/test_studyspec_relock_smoke.py -q` | PASS, `5 passed in 0.34s` |
| `PYTHONPATH=src python tools/verify.py --smoke` | PASS, exit 0, no output |
| `PYTHONPATH=src python tools/hooks/canary_runner.py` | PASS, all Frontier canaries passed |
| `test -f research/futures_substrate_scaleout_v1/rerun/studyspec_relock.md` | PASS, exit 0, no output |
| `test -f docs/futures_substrate_scaleout/CORE_PILOT_RELOCK.md` | PASS, exit 0, no output |
| `test -f handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P27.md` | PASS, exit 0, no output |
| `git ls-files runs` | PASS, empty output |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'` | PASS, empty output |

The executor did not run `git diff`, `git add`, `git commit`, `git push`, PR
creation, reviewer calls, review generation, verdict generation, CI wait, or
merge operations.

## Artifact Policy Confirmation

- No file under `src/**` was edited by this executor.
- No file under `research/futures_core_alpha_pilot_v1/**` was edited by this
  executor.
- No `runs/` file was created, staged, or committed by this executor.
- No run-local `handoff.md`, `review.md`, `verdict.json`, `checks.json`, or
  repair-attempt artifact was created.
- No commit-eligible review artifact or verdict artifact was created.
- No feature value, label value, raw/canonical data, provider payload, Parquet,
  Arrow, Feather, SQLite/DB, DBN/ZST, model artifact, cache, log, secret, or
  local data artifact was created inside the repository.
- Scratch validation files were written only under `/tmp`:
  `/tmp/futsub_p27_feature_locks.json` and
  `/tmp/futsub_p27_validate_feature_locks.json`.
- Changes are left unstaged for Ralph.
