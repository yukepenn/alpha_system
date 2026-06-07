# ALPHA_AGENT_FACTORY_MVP Closeout

## Final Verdict

`COMPLETE_WITH_WARNINGS`

This campaign has completed the Agent Factory MVP contract layer after
`AGENT-P25` closeout. The result is not a clean `COMPLETE` because the final
integration dry run recorded a truthful `PASS_WITH_WARNINGS` on this runner:
local seed FeaturePack/LabelPack registry markers were absent, so the dry run
used the deterministic synthetic resolver path. The two named future blockers
remain open: `FEATURE_LABEL_PARQUET_SINK_V1` and
`SESSION_LABEL_GUARD_FIX_V1`.

The verdict is documentation and audit closeout only. It does not self-approve
the `AGENT-P25` phase, replace the required fresh YELLOW-lane review, create a
review verdict, create a PR, merge, or mark any phase PASS.

## Acceptance Gate Status

| Gate | Phases | Status | Notes |
| --- | --- | --- | --- |
| `bootstrap_and_entry` | `AGENT-P00` - `AGENT-P02` | `PASS` | Campaign files, package skeleton, entry contract, preflight config, and initial docs are present. The entry contract is contracts-only and degrades missing local registries to a truthful warning. |
| `core_contracts` | `AGENT-P03` - `AGENT-P06` | `PASS` | Role contracts, discovery registry, default-deny permission matrix, structured tool contracts/results, and finite research queue contracts are present. |
| `agent_roles` | `AGENT-P07` - `AGENT-P15` | `PASS` | The ten MVP role contracts exist in disjoint role modules/docs/templates and register additively through the role registry. |
| `enforcement_and_records` | `AGENT-P16` - `AGENT-P18` | `PASS` | Separation-of-duties enforcement, wiring, passive record contracts, and rejected-idea/research memory are present and fail closed. |
| `assets_and_bridge` | `AGENT-P19` - `AGENT-P21` | `PASS` | Prompt/operator/readiness docs and the runtime bridge are present. The bridge consumes runtime outputs and accepted DatasetVersion resolution without editing runtime primitives. |
| `dry_run_and_closeout` | `AGENT-P22` - `AGENT-P25` | `PASS_WITH_WARNINGS` | The bounded non-alpha dry-run harness, integration dry run, DAG plan, and this closeout are present. The warning is the P23 synthetic fallback caused by absent local seed registries / unset `ALPHA_DATA_ROOT`; P25 still requires the coordinator-owned fresh review before merge. |

## Recorded Warnings

- The integration dry run recorded `PASS_WITH_WARNINGS` because local seed
  FeaturePack/LabelPack registries were absent on this runner and
  `ALPHA_DATA_ROOT` was unset. The test path used deterministic synthetic
  fixtures and did not claim seed data evidence.
- `FEATURE_LABEL_PARQUET_SINK_V1` remains open. Large-scale
  value-consuming studies remain blocked until the Parquet value sink lands or
  a separate human authorization records a narrower exception.
- `SESSION_LABEL_GUARD_FIX_V1` remains open. Session-context feature use
  involving `rth_flag`, `eth_flag`, or `session_minute` remains blocked until
  the guard fix lands or those fields are explicitly marked available.
- The dataset-registry report rehydration gap remains a pilot constraint:
  agents must use registry/runtime tools and must not bypass accepted
  DatasetVersion policy to work around persisted report hashes.
- Fresh YELLOW-lane review and final semantic done-check remain
  coordinator-owned for `AGENT-P25`; this executor did not create
  `review.md`, `verdict.json`, a PR, or a merge.

## Boundary Confirmation

`ALPHA_AGENT_FACTORY_MVP` is a contracts-only layer over existing governance,
feature/label, data-foundation, and research-runtime primitives. It defines
roles, permissions, tool result contracts, queue records, separation rules,
handoffs, memory, runtime adaptation, and a bounded non-alpha dry-run path. It
does not instantiate an autonomous agent, start a continuous research runner,
conduct alpha search, promote a factor, validate a strategy, write a portfolio
artifact, materialize feature/label/runtime/agent values, call external
providers, call brokers, route orders, or use paper/live/account scope.

The most advanced forward MVP state remains
`REFERENCE_HANDOFF_RECORDED`. Terminal outcomes remain `REJECTED`,
`INCONCLUSIVE`, and `BLOCKED`. The prohibited MVP states
`ALPHA_VALIDATED`, `FACTOR_PROMOTED`, `STRATEGY_READY`, `PORTFOLIO_READY`,
`CANDIDATE_PROMOTED`, `LIVE_READY`, `PAPER_READY`, `PROFITABLE`, `TRADABLE`,
`PRODUCTION_READY`, and `AUTONOMOUS_RESEARCH_RUNNING` are not campaign
outcomes.

## ALPHA_FUTURES_CORE_ALPHA_PILOT_V1 Readiness

`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` is ready to be considered as a separate,
separately authorized next campaign that may consume the Agent Factory contract
layer. Readiness means the controlled team contracts and local-first runtime
bridge exist; it does not mean any research claim has been established.

No-claims wording for the next campaign:

- A dry-run success is not alpha.
- An agent-drafted `AlphaSpec` is not implementation approval.
- A runtime diagnostic PASS is not factor promotion.
- An `EvidenceDraft` is not a candidate.
- A `ReferenceCandidateHandoff` is not Reference validation.
- Validated research is not paper/live approval.

The next campaign must restate and satisfy its own governance, data
admissibility, evidence, review, artifact, and human authorization gates before
any pilot work starts. The human retains risk, capital, paper/live, broker,
order, deployment, promotion, strategy, portfolio, and production judgment.

## Coordinator Closeout Addendum

This section is written by the coordinator after the full Workflow 2 live run,
to record run mechanics and the one supervisor intervention that the
`AGENT-P25`-authored sections above could not capture.

### Live run

- Run id: `2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP` (provider-wired, external
  providers, `dag_wave` parallel, `max_parallel = 3`, serial merge queue,
  worktree mode). 18 waves, all 26 phases (`AGENT-P00`–`AGENT-P25`) merged.
- Final phase tally: **10 `PASS`, 16 `PASS_WITH_WARNINGS`, 0 `BLOCKED`** →
  `RUN_COMPLETE`, final campaign done-check `PASS_WITH_WARNINGS`.
- Phase PRs **#182–#208** (squash-merged to `main` through the protected-branch
  PR/CI path). No external provider, broker, paper/live, order, or deployment
  scope was exercised; `git ls-files runs` is empty.
- Closeout validation on clean `main` after all merges: `python tools/verify.py
  --all` → **2773 passed, 1 skipped**; `canary_runner` all PASS. (The single
  transient failure during closeout was `test_no_l2_db_or_columnar_artifacts_are_present`
  catching two operator-created `runs/*.log` console captures — not a campaign
  artifact; the logs were removed and the suite is green.)
- The 26 Opus review records were promoted run-local →
  `reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P00..P25/` (`just frontier-promote-reviews`).

### Supervisor intervention — `AGENT-P16` done-check parser false-negative

`AGENT-P16` (Separation-of-Duties and No-Self-Review Enforcement) **passed**
review (`PASS_WITH_WARNINGS`) and every check (24 tests, ruff, smoke, canaries,
`frontier-doctor`), but the run stopped because the **verdict parser** mis-read a
**Markdown-bold** done-check line. The Claude done-check rendered
`**DONE_CHECK: PASS_WITH_WARNINGS**`; `tools/frontier/verdict.py`'s
`DONE_CHECK_RE` required the verdict to be the *entire* line, so the leading and
trailing `**` produced zero matches and the parser defaulted to `BLOCKED`
("missing or ambiguous"). The dag_wave coordinator did the right thing — it
isolated the phase, merged nothing broken, wrote a STOP, and exited at 16/26.

Resolution (supervisor, not a phase):

1. Relaxed `VERDICT_RE` and `DONE_CHECK_RE` to tolerate leading Markdown
   decoration and emphasis/backtick padding while staying anchored to a single
   line (prose can't false-match); added 3 regression tests. Shipped as **PR
   #198** (`f66a1b2`, CI green) so every remaining done-check and the final
   campaign done-check were protected.
2. Re-running `AGENT-P16` from `done_check` revealed a second-order detail: the
   resume **reuses a fresh `done_check.json` without re-parsing the markdown**,
   so the stale `BLOCKED` json shadowed the fix. Regenerated `done_check.json`
   from the real (correct) `done_check.md` with the fixed parser →
   `PASS_WITH_WARNINGS`, then resumed; `AGENT-P16` merged as **PR #199** (CI
   green, base-synced against the fixed `main`). The parallel run then resumed
   and drove `AGENT-P17`–`AGENT-P25` to completion with no further stops.

This was a harness parsing bug, not a contract defect: the separation-of-duties
layer itself was correct and is now merged. No test was weakened and no phase was
marked PASS without its required fresh review.
