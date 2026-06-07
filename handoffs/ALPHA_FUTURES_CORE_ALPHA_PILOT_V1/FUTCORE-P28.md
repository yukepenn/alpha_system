# FUTCORE-P28 Executor Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P28` - PromotionDecision: Reject / Inconclusive / Watch / CandidateResearch  
Executor: Codex  
Lane: Yellow

## Scope Completed

- Recorded one value-free PromotionDecision record for each of the 10 accepted
  StudySpecs carried into the P25-P27 evidence gate.
- Created per-idea JSON decisions under
  `research/futures_core_alpha_pilot_v1/promotion/decisions/`.
- Created aggregate and human-readable promotion summaries under
  `research/futures_core_alpha_pilot_v1/promotion/`.
- Created durable pilot documentation at
  `docs/futures_core_alpha_pilot/PROMOTION_DECISIONS.md`.
- Updated the root `README.md` snapshot for P28 and next phase `FUTCORE-P29`.
- Did not create reviewer artifacts, `review.md`, `verdict.json`, PRs, merges,
  commits, staging actions, or phase PASS markings.

The run-local phase directory named by the prompt,
`runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P28`,
was absent in this worktree. The generated spec embedded in the executor prompt
was used as the active phase contract.

## Decision Summary

| Outcome | Count |
| --- | ---: |
| `REJECT` | 4 |
| `INCONCLUSIVE` | 6 |
| `WATCH` | 0 |
| `CANDIDATE_RESEARCH` | 0 |
| `WATCH` + `CANDIDATE_RESEARCH` | 0 |

`WATCH` + `CANDIDATE_RESEARCH` count: `0`, which is within the campaign cap of
`2`. No survivor was self-promoted. All six P27 survivors have independent P25
Statistical Reviewer verdict artifacts, and all six are `INCONCLUSIVE`, so none
supports `WATCH` or `CANDIDATE_RESEARCH`.

## Idea Decision Table

| StudySpec | AlphaSpec | Family | Assigned state | Reviewer-verdict ref | Ledger/evidence refs | Duplicate hint |
| --- | --- | --- | --- | --- | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | `aspec_0ebd90cecfd475607685b445` | `cross_market` | `REJECT` | not applicable: rejected before P25 | `trial_b4e25da7c409809fc1cb54b7`; `rej_c27b447c282967db390ff10d` | `cm-lead-lag-pair` |
| `sspec_c671fbeeb143512cbc03bc5b` | `aspec_8d9e272e4b78eedcd27f0bec` | `cross_market` | `REJECT` | not applicable: rejected before P25 | `trial_587d6da288aa8ff2ca25fa37`; `rej_9ed40aaf995f1f70f5f94cdf` | `cm-beta-residual` |
| `sspec_90b28233d828128664588a9a` | `aspec_a41dcccac5552de945aba825` | `cross_market` | `REJECT` | not applicable: rejected before P25 | `trial_bdbfa08dcf63fe1fe8e5921d`; `rej_20d88b59ce09f47d364fd529` | `cm-rty-rotation` |
| `sspec_7c8fb13628843890c171b122` | `aspec_fa4895a43a80d4eef0a607a4` | `cross_market` | `REJECT` | not applicable: rejected before P25 | `trial_1fc87c34cf31d8055d3d224d`; `rej_fa471f1ddeaa066dc4a95feb` | `cm-pair-divergence` |
| `sspec_69c22ec5847395ac8e81b5b6` | `aspec_b40aee52d4399dd5b855a6ed` | `vwap_session` | `INCONCLUSIVE` | `research/futures_core_alpha_pilot_v1/reviewer_verdicts/reviewer_verdict_sspec_69c22ec5847395ac8e81b5b6.json` | `trial_fffbb48dc4111caeabcc55c9`; `evidence_draft_sspec_69c22ec5847395ac8e81b5b6.json`; `rej_7107e99008c6a7aaf7d2d5b4` | `vwap-reclaim-reject` |
| `sspec_aff70fcbc4b7ff226fcc8149` | `aspec_43cd6c154bca2fcc419eee83` | `vwap_session` | `INCONCLUSIVE` | `research/futures_core_alpha_pilot_v1/reviewer_verdicts/reviewer_verdict_sspec_aff70fcbc4b7ff226fcc8149.json` | `trial_3b8f60dd0f4793288360159e`; `evidence_draft_sspec_aff70fcbc4b7ff226fcc8149.json` | `vwap-rth-open-eth` |
| `sspec_267cc052e37668339c38d179` | `aspec_eb962fc197eaf3955c5e4711` | `regime` | `INCONCLUSIVE` | `research/futures_core_alpha_pilot_v1/reviewer_verdicts/reviewer_verdict_sspec_267cc052e37668339c38d179.json` | `trial_94781614f100a2aa0878aae4`; `trial_13c98257a704ce5641a51626`; `trial_58fdb5456d910efccdd95b7b`; `trial_fce335815b1bda26eb898aed`; `evidence_draft_sspec_267cc052e37668339c38d179.json` | `regime-trend-vol-range` |
| `sspec_27bf1262b0bd23d27191cc86` | `aspec_df2d040e45564c259ef3de6d` | `liquidity_pa` | `INCONCLUSIVE` | `research/futures_core_alpha_pilot_v1/reviewer_verdicts/reviewer_verdict_sspec_27bf1262b0bd23d27191cc86.json` | `trial_666433ac863d5adb1368a3d1`; `evidence_draft_sspec_27bf1262b0bd23d27191cc86.json` | `pa-sweep-closeback` |
| `sspec_02c400a561891171a33c0c66` | `aspec_39ffc190cfbfa6ba0b1a2a25` | `liquidity_pa` | `INCONCLUSIVE` | `research/futures_core_alpha_pilot_v1/reviewer_verdicts/reviewer_verdict_sspec_02c400a561891171a33c0c66.json` | `trial_45df4e0c5999da63a57ff9b2`; `evidence_draft_sspec_02c400a561891171a33c0c66.json` | `pa-failed-breakout` |
| `sspec_9f6f741192a4b534f06e51c0` | `aspec_1284e49b083df11eeb0481ea` | `bbo_tradability` | `INCONCLUSIVE` | `research/futures_core_alpha_pilot_v1/reviewer_verdicts/reviewer_verdict_sspec_9f6f741192a4b534f06e51c0.json` | `trial_2ae03a839098b6ff741b2f84`; `trial_4ee4909066d85d4abcdfaa42`; `trial_3a61fa6378614054674171ec`; `trial_2c32c84a140e6e99f67f5aa8`; `evidence_draft_sspec_9f6f741192a4b534f06e51c0.json` | `bbo-spread-depth-confirmation` |

## Commit-Eligible Files Left For Ralph To Stage

Staged files by executor: none. The executor did not run `git add`, `git
commit`, `git push`, `git status`, or `git diff`.

- `README.md`
- `docs/futures_core_alpha_pilot/PROMOTION_DECISIONS.md`
- `research/futures_core_alpha_pilot_v1/promotion/INDEX.md`
- `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`
- `research/futures_core_alpha_pilot_v1/promotion/decisions.json`
- `research/futures_core_alpha_pilot_v1/promotion/decisions/promotion_decision_sspec_02c400a561891171a33c0c66.json`
- `research/futures_core_alpha_pilot_v1/promotion/decisions/promotion_decision_sspec_267cc052e37668339c38d179.json`
- `research/futures_core_alpha_pilot_v1/promotion/decisions/promotion_decision_sspec_27bf1262b0bd23d27191cc86.json`
- `research/futures_core_alpha_pilot_v1/promotion/decisions/promotion_decision_sspec_69c22ec5847395ac8e81b5b6.json`
- `research/futures_core_alpha_pilot_v1/promotion/decisions/promotion_decision_sspec_7c8fb13628843890c171b122.json`
- `research/futures_core_alpha_pilot_v1/promotion/decisions/promotion_decision_sspec_90b28233d828128664588a9a.json`
- `research/futures_core_alpha_pilot_v1/promotion/decisions/promotion_decision_sspec_9f6f741192a4b534f06e51c0.json`
- `research/futures_core_alpha_pilot_v1/promotion/decisions/promotion_decision_sspec_aff70fcbc4b7ff226fcc8149.json`
- `research/futures_core_alpha_pilot_v1/promotion/decisions/promotion_decision_sspec_c671fbeeb143512cbc03bc5b.json`
- `research/futures_core_alpha_pilot_v1/promotion/decisions/promotion_decision_sspec_dde3e64667fe158f9bad527d.json`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P28.md`

Reviewer-owned paths under
`reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P28/**` were not created by
this executor. Ralph owns review routing and review/verdict artifacts.

## Validation

Commands run from the provided WSL2 worktree root:

| Command | Outcome |
| --- | --- |
| `test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP` | Passed; exit code `0`; no output. |
| `git status --short` | Not run: explicitly forbidden by the executor prompt for this turn. |
| `python -c "import alpha_system.runtime.decisions.states, alpha_system.governance.promotion_gate"` | Passed; exit code `0`; no output. |
| `python tools/verify.py --smoke` | Passed; exit code `0`; no output. |
| `test -d research/futures_core_alpha_pilot_v1/promotion` | Passed; exit code `0`; no output. |
| `test -f docs/futures_core_alpha_pilot/PROMOTION_DECISIONS.md` | Passed; exit code `0`; no output. |
| `git ls-files runs` | Passed; exit code `0`; output empty. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'` | Passed; exit code `0`; output empty. |

Supporting local checks:

| Command | Outcome |
| --- | --- |
| `test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P28.md` | Passed; exit code `0`; no output. |
| `jq -e . research/futures_core_alpha_pilot_v1/promotion/decisions.json research/futures_core_alpha_pilot_v1/promotion/decisions/*.json >/dev/null` | Passed; exit code `0`; no output. |
| `python - <<'PY' ... promotion structural check ... PY` | Passed; printed `decision_records=10`, `state_counts=REJECT:4,INCONCLUSIVE:6,WATCH:0,CANDIDATE_RESEARCH:0`, `watch_plus_candidate_research=0`, and `accepted_studyspec_coverage=exact`. |
| Disallowed uppercase-state token scan over `README.md`, promotion docs, promotion records, and this handoff | Passed; no matches; `rg` exit code `1` because no matches were found. |
| `test ! -e reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P28` | Passed; exit code `0`; no output. |

Spec-listed commands intentionally not run by Codex due the explicit prompt
override:

- `git status --short`
- `git diff --cached --name-only`
- `git add`
- `git commit`
- `git push`
- reviewer / Claude commands
- PR creation, CI, merge, merge gate, verdict parsing, and done-check

Yellow-lane broader checks (`lint`, `typecheck`, `test`, `verify_canaries`) are
Ralph-owned for orchestration in `CHECKS_RUN`.

## Artifact And Boundary Confirmation

- No `runs/**` files were created, edited, staged, or committed by this
  executor.
- No staging command was run; all created or edited files are left for Ralph to
  stage explicitly by path.
- No `src/alpha_system/**` consumed primitives were edited.
- No tests were edited.
- No broker, live, paper-trading, order-routing, account, deployment, PR,
  merge, or destructive operation was performed.
- Promotion artifacts are value-free: ids, statuses, repo-relative references,
  rationale text, duplicate-exposure hints, limitations, and non-claim labels
  only.
- P28 promotion decisions do not perform Reference validation and do not create
  downstream readiness.
- This handoff does not mark the phase PASS; Ralph owns validation ledger
  recording, review routing, verdict parsing, staging, commit, PR, CI, merge,
  and done-check actions.
