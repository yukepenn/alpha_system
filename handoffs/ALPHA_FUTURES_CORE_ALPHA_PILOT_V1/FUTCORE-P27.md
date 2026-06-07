# FUTCORE-P27 Executor Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P27` - EvidenceDraft and ReferenceCandidateHandoff for Survivors  
Executor: Codex  
Date: 2026-06-07

## Scope Completed

- Derived the survivor set from the P26 TrialLedger plus the P25 statistical
  reviewer verdict artifacts.
- Created one value-free EvidenceDraft JSON, FactorCard draft JSON, and
  ReferenceCandidateHandoff JSON per survivor under
  `research/futures_core_alpha_pilot_v1/evidence/**`.
- Wrote `research/futures_core_alpha_pilot_v1/evidence/survivors.json` and
  `research/futures_core_alpha_pilot_v1/evidence/INDEX.md`.
- Wrote `docs/futures_core_alpha_pilot/EVIDENCE.md`.
- Updated the root `README.md` snapshot for P27 and next phase `FUTCORE-P28`.
- Did not create reviewer artifacts, `review.md`, `verdict.json`, PRs, merges,
  commits, staging actions, or phase PASS markings.

The run-local `runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P27/spec.md`
path named by the prompt was absent in the worktree. The executor used the
generated spec embedded in the executor prompt as the active contract.

## Survivor Set

Survivor count: `6`.

| StudySpec | AlphaSpec | Family | P25 judgement | P26 TrialLedger records | Duplicate hint | Linked RejectedIdea refs |
| --- | --- | --- | --- | ---: | --- | --- |
| `sspec_69c22ec5847395ac8e81b5b6` | `aspec_b40aee52d4399dd5b855a6ed` | `vwap_session` | `INCONCLUSIVE` | 1 | `vwap-reclaim-reject` | `rej_7107e99008c6a7aaf7d2d5b4` |
| `sspec_aff70fcbc4b7ff226fcc8149` | `aspec_43cd6c154bca2fcc419eee83` | `vwap_session` | `INCONCLUSIVE` | 1 | `vwap-rth-open-eth` | none exact |
| `sspec_267cc052e37668339c38d179` | `aspec_eb962fc197eaf3955c5e4711` | `regime` | `INCONCLUSIVE` | 4 | `regime-trend-vol-range` | none exact |
| `sspec_27bf1262b0bd23d27191cc86` | `aspec_df2d040e45564c259ef3de6d` | `liquidity_pa` | `INCONCLUSIVE` | 1 | `pa-sweep-closeback` | none exact |
| `sspec_02c400a561891171a33c0c66` | `aspec_39ffc190cfbfa6ba0b1a2a25` | `liquidity_pa` | `INCONCLUSIVE` | 1 | `pa-failed-breakout` | none exact |
| `sspec_9f6f741192a4b534f06e51c0` | `aspec_1284e49b083df11eeb0481ea` | `bbo_tradability` | `INCONCLUSIVE` | 4 | `bbo-spread-depth-confirmation` | none exact |

All six EvidenceDraft runtime decisions remain `INCONCLUSIVE`. P27 did not
recast them as ready, validated, promoted, or Reference-validated.

## Commit-Eligible Files Left For Ralph To Stage

Staged files by executor: none. The executor did not run `git add`, `git
commit`, `git push`, `git status`, or `git diff`.

- `README.md`
- `docs/futures_core_alpha_pilot/EVIDENCE.md`
- `research/futures_core_alpha_pilot_v1/evidence/INDEX.md`
- `research/futures_core_alpha_pilot_v1/evidence/survivors.json`
- `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/evidence_draft_sspec_02c400a561891171a33c0c66.json`
- `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/evidence_draft_sspec_267cc052e37668339c38d179.json`
- `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/evidence_draft_sspec_27bf1262b0bd23d27191cc86.json`
- `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/evidence_draft_sspec_69c22ec5847395ac8e81b5b6.json`
- `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/evidence_draft_sspec_9f6f741192a4b534f06e51c0.json`
- `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/evidence_draft_sspec_aff70fcbc4b7ff226fcc8149.json`
- `research/futures_core_alpha_pilot_v1/evidence/factor_cards/factor_card_sspec_02c400a561891171a33c0c66.json`
- `research/futures_core_alpha_pilot_v1/evidence/factor_cards/factor_card_sspec_267cc052e37668339c38d179.json`
- `research/futures_core_alpha_pilot_v1/evidence/factor_cards/factor_card_sspec_27bf1262b0bd23d27191cc86.json`
- `research/futures_core_alpha_pilot_v1/evidence/factor_cards/factor_card_sspec_69c22ec5847395ac8e81b5b6.json`
- `research/futures_core_alpha_pilot_v1/evidence/factor_cards/factor_card_sspec_9f6f741192a4b534f06e51c0.json`
- `research/futures_core_alpha_pilot_v1/evidence/factor_cards/factor_card_sspec_aff70fcbc4b7ff226fcc8149.json`
- `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_02c400a561891171a33c0c66.json`
- `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_267cc052e37668339c38d179.json`
- `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_27bf1262b0bd23d27191cc86.json`
- `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_69c22ec5847395ac8e81b5b6.json`
- `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_9f6f741192a4b534f06e51c0.json`
- `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_aff70fcbc4b7ff226fcc8149.json`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P27.md`

Reviewer-owned paths under
`reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P27/**` were not created by
this executor per the explicit executor prompt. Ralph owns review routing and
review/verdict artifacts.

## Validation

| Command | Outcome |
| --- | --- |
| `test -e runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP && printf 'STOP_PRESENT\n' || printf 'STOP_ABSENT\n'` | Passed; printed `STOP_ABSENT`. |
| `python -c "import alpha_system.runtime.evidence.draft, alpha_system.runtime.handoff.reference"` | Passed. |
| `test -d research/futures_core_alpha_pilot_v1/evidence` | Passed. |
| `git ls-files runs` | Passed; printed nothing. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'` | Passed; printed nothing. |
| `python tools/verify.py --smoke` | Passed. |
| `python tools/verify.py --lint` | Exit 0, but lint was skipped because `ruff` is not installed (`pip install -e ".[dev]"` needed). |
| `python tools/verify.py --typecheck` | Passed; verifier ran `compileall -q src tests tools`. |
| `python tools/verify.py --test` | Failed: 4 failed, 2840 passed in 43.02s. Failures: `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`; `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`; `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`; `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`. These match the P26 handoff's residual failures. |
| `python tools/hooks/canary_runner.py` | Passed; all Frontier canaries passed. |

Additional local artifact inspections:

- Survivor/card/draft/handoff sets match exactly: 6 StudySpecs.
- All generated EvidenceDraft runtime decisions are `INCONCLUSIVE`.
- Forbidden uppercase states were not found in `README.md`,
  `docs/futures_core_alpha_pilot/EVIDENCE.md`, or
  `research/futures_core_alpha_pilot_v1/evidence/**`.
- `find research/futures_core_alpha_pilot_v1/evidence -type f` with heavy/DB
  suffix filters printed nothing.

Commands intentionally not run by executor due explicit prompt override:

- `git status --short`
- `git diff --cached --name-only`
- `git add`
- `git commit`
- `git push`
- reviewer / Claude commands

## Artifact And Boundary Confirmation

- No `runs/**` files were created, edited, staged, or committed by this
  executor.
- No staging command was run; all created or edited files are left for Ralph to
  stage explicitly by path.
- No `src/alpha_system/**` consumed primitives were edited.
- No broker, live, paper-trading, order-routing, account, deployment, PR,
  merge, or destructive operation was performed.
- Evidence artifacts are value-free: ids, statuses, hashes, repo-relative
  references, summary metadata, limitations, and non-claims labels only.
- ReferenceCandidateHandoff artifacts are handoff packages only and are not
  Reference validation.
- FactorCard artifacts are drafts for later review input only.
- This handoff does not mark the phase PASS; Ralph owns validation ledger
  recording, review routing, verdict parsing, staging, commit, PR, CI, merge,
  and done-check actions.
