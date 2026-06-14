# DK-P05 — Campaign Verdict Aggregation, Survivor Gate, and Closeout (Track A + Track B, Research-Only)

---
campaign_id: DIFFERENTIATED_KILLSHOT_V1
phase_id: DK-P05
lane: YELLOW
status: draft
dependencies: [DK-P04]
executor: Codex GPT-5.5 high
reviewer: Claude Opus 4.8 xhigh
verifier: Claude Sonnet 4.6
---

## Purpose

Aggregate the campaign's already-produced evidence into **one honest, conclusive verdict** and apply
the **survivor gate**, so the differentiated-substrate kill-shot ends with a trustworthy negative
(or a properly-surfaced survivor) rather than a quiet inertia drift into a factory. Concretely:

- **Aggregate** the five Track A mechanism verdicts from `DK-P03`
  (`research/differentiated_substrate_v1/verdict_refresh.md`) and the Track B `EXPLORATORY` readout
  from `DK-P04` (`research/differentiated_substrate_v1/.../EVIDENCE.json`) into a single
  `research/differentiated_substrate_v1/CAMPAIGN_VERDICT.md`: per-item `primary_state` +
  `VerdictReasonCode`, plus the boundary roll-up across `REJECT` / `INCONCLUSIVE`+code / `WATCH` /
  `CANDIDATE_RESEARCH`.
- **Apply the survivor gate.** Mirror the FUTSUB `verdict_refresh.md` framing: **0 clean survivors
  with no remaining substrate excuse is a successful, conclusive kill-shot** — a trustworthy
  negative in which the machine did not fool itself, *because* the surrogate-FDR zero-pass gate
  (DK-P02) and the planted-fake-alpha + true-alpha-pair canaries held. **Any** `WATCH` /
  `CANDIDATE_RESEARCH` survivor is **SURFACED** to the user for the survivor-gate decision with a
  `reviewer_verdict` artifact + `reason_code`, **never auto-promoted** — no factory by inertia
  (the Command-Center constitution).
- **Write the closeout.** Produce an evidence summary + a `RUN_SUMMARY`-equivalent closeout under
  `research/differentiated_substrate_v1/**`, carrying every caveat forward (zero-feed calendar
  approximations, `N_eff`/power limits, any Track B `DATA_GAP`, `fomc`/`cpi` deferred =
  `needs_paid_data`, the governed-overnight family deferred). Research-only language; **no**
  profitability / tradability / alpha claim; **no** promotion; **no** next-campaign authoring.

This phase is **aggregation + adjudication only**. It runs **no new study, no new metric, no new
calibration**. It consumes the locked, committed evidence of DK-P03 and DK-P04 and maps it to the
closed verdict taxonomy.

## Context

- **Reused machinery (locked by the DK-P00 REUSE-MAP, `docs/differentiated_killshot_v1/REUSE_MAP.md`):**
  - Verdict taxonomy + reason codes: `governance/trial_ledger.py` / `governance/verdict*`
    (`VerdictReasonCode`, the closed primary-state set). Allowed states are **only** `REJECT`,
    `INCONCLUSIVE`+`reason_code`, `WATCH`, `CANDIDATE_RESEARCH`.
  - Variant accounting: `governance/variant_ledger.py` (`VariantLedgerRecord`, `FamilyBudgetCheck`)
    — read-only here; the roll-up reflects what DK-P02/DK-P03/DK-P04 already ledgered.
  - Track A evidence: `research/differentiated_substrate_v1/verdict_refresh.md` (DK-P03) — the five
    mechanisms `day_of_week_effect`, `opex_pinning`, `month_end_flow`, `roll_week_flow`,
    `open_close_auction_flow`, each already carrying `primary_state` + `reason_code` + `N_eff`/power.
  - Track B evidence: the DK-P04 `EXPLORATORY` `EVIDENCE.json` (stamp `EXPLORATORY`,
    `promotion_eligible:false`) — a real `context!=trigger` readout **or** an honest
    `status=INCONCLUSIVE` / `issue_code=DATA_GAP`.
  - Survivor-gate framing precedent: `research/futures_substrate_scaleout_v1/rerun/verdict_refresh.md`
    (the FUTSUB "no-survivor refresh" framing — trustworthy negative, non-claim discipline, residual
    caveats carried forward). This is the **shape to mirror**, not a file to edit.
- **Why the gate is trustworthy (the load-bearing argument this phase records):** a no-survivor
  result is conclusive **only because** the truth chain held every phase — surrogate-FDR zero-pass
  (`SurrogateGateStatus`/`ZERO_PASS_MET`, DK-P02) preceded any real metric; the FDR active-subset
  restatement (DK-P00) pre-registered the surface before the earliest variant; and the
  planted-fake-alpha + true-alpha-pair + `forbidden_second_pnl_truth` +
  `forbidden_exploratory_promotion` + `governance_random_target` + `forbidden_scope_drift` canaries
  stayed green. The closeout must **state** this argument, not merely assert "0 survivors".
- **Asymmetric survivor handling (HARD):** a clean negative needs **no** reviewer verdict (mirrors
  FUTSUB-P29). But any `WATCH`/`CANDIDATE_RESEARCH` survivor is **promotion-adjacent** and requires a
  committed `reviewer_verdict` artifact + `reason_code` and is **surfaced to the user** — it is
  **never** auto-promoted and **never** earns the next layer inside this phase.
- **Track B quarantine survives aggregation:** the `EXPLORATORY` readout is **context** in
  `CAMPAIGN_VERDICT.md`, never promotion evidence. It may inform the narrative and the survivor-gate
  surface, but it can **never** be a survivor that earns promotion, and the trusted resolver still
  refuses it (`forbidden_exploratory_promotion` canary).
- **No second PnL truth / no bridge:** this phase reads markdown/JSON evidence only. `research/`
  imports **zero** `backtest`/`management`/`fast_path`/`value_store`; no value engine is touched; no
  new value is computed. Outcomes were already injected upstream from `tools`/`runtime`.
- **Carried-evidence integrity (C2/C3):** the SSRL first-light `EVIDENCE.json` is an honest
  `DATA_GAP`, **not** real ES_2024 evidence, and must not be cited as a result (C2); the de-stack
  `ic=0.068/n=6862` is a carried SHIP_REFIT restatement, **not** fresh corroboration (C3). The
  closeout repeats these non-claims if either is referenced.

## Scope

Allowed work (binds to the DK-P05 `scope`/`allowed_paths`/`done_criteria` in `campaign.yaml`):

1. **Aggregate into `CAMPAIGN_VERDICT.md`.** Write
   `research/differentiated_substrate_v1/CAMPAIGN_VERDICT.md` that lists, **per item**, the
   `primary_state` + `VerdictReasonCode`:
   - the five Track A mechanisms (`day_of_week_effect`, `opex_pinning`, `month_end_flow`,
     `roll_week_flow`, `open_close_auction_flow`) exactly as resolved in DK-P03 `verdict_refresh.md`
     (do **not** re-derive or change any state), and
   - the one Track B item from DK-P04 `EVIDENCE.json`, carried as `EXPLORATORY` / non-promotion (its
     `status` + `issue_code`/`reason_code`, e.g. real readout or `DATA_GAP`).
   Include the **boundary roll-up table** counting items across `REJECT` / `INCONCLUSIVE`+code /
   `WATCH` / `CANDIDATE_RESEARCH`, with each cell traceable to the per-item rows.
2. **Apply the survivor gate.** State the gate decision explicitly:
   - **0 clean survivors** (no `WATCH`/`CANDIDATE_RESEARCH` Track A survivor, Track B permanently
     `EXPLORATORY`/non-promotion) **with no remaining substrate excuse** = a **successful, conclusive
     kill-shot**. Record the trustworthy-negative argument (surrogate zero-pass + planted/true-alpha
     canaries + FDR-before-metric) so the conclusion is earned, not asserted.
   - **Any** `WATCH`/`CANDIDATE_RESEARCH` survivor ⇒ **SURFACE** it for the survivor-gate decision:
     produce a committed `reviewer_verdict` artifact (e.g.
     `reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P05/reviewer_verdict.md` or an equivalent committed
     survivor record under the allowed research path) + `reason_code`, and state plainly that it is
     **surfaced to the user, not auto-promoted** (no factory by inertia). Do **not** build any
     factory/FactorLibrary/AlphaBook entry here.
3. **Write the evidence summary + `RUN_SUMMARY` equivalent.** Produce a closeout (e.g.
   `research/differentiated_substrate_v1/RUN_SUMMARY.md` and/or an `EVIDENCE_SUMMARY.md`) that
   summarizes what each phase delivered (DK-P00 FDR restatement + scope lock; DK-P01 additive
   zero-feed flags under the parity gate; DK-P02 StudySpecs + declared-conditioning-factor admission
   + surrogate zero-pass `ZERO_PASS_MET`; DK-P03 real-data verdicts; DK-P04 `EXPLORATORY` probe /
   `DATA_GAP`), and the final boundary + survivor-gate outcome. **Carry caveats forward**: zero-feed
   calendar approximations (analytic third-Friday opex/quad-witch; month/quarter-end = last trading
   session within the committed calendar's covered window, non-exchange-official; `in_roll_window` =
   approximate analytic CME quarterly roll); `N_eff`/power/MDE limits (rows not independent; metadata
   not significance); any Track B `DATA_GAP`; `fomc`/`cpi` deferred = `needs_paid_data`;
   governed-overnight family deferred (no cards this round).
4. **Optional docs** under `docs/differentiated_killshot_v1/**` if a durable closeout/runbook note is
   warranted (no claims, research-only).
5. **Commit-eligible handoff** at `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P05.md` and YELLOW review
   artifacts under `reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P05/**`.

The work is **strictly additive and value-aggregating**. No engine, feature, label, study, or
calibration is created or modified.

## Non-Goals

- **No promotion of any kind:** no `FactorLibrary` ingestion, no `AlphaBook`/Strategy-Reference
  entry, no `PromotionDecision`, no paper/live/broker/deploy. A `WATCH`/`CANDIDATE_RESEARCH` survivor
  is **surfaced**, not promoted.
- **No next-campaign authoring.** Recommending or authoring the next campaign is a **separate,
  triggered decision** owned by the user; this phase does not write a new campaign contract or queue
  one.
- **No new metric beyond aggregation.** No re-run of studies, no re-score, no new IC/return/diagnostic
  value, no re-calibration, no new surrogate run. States are **carried** from DK-P03/DK-P04, not
  re-derived.
- **No change to any prior verdict.** DK-P03 mechanism states and the DK-P04 `EXPLORATORY` status are
  consumed as authored; this phase neither overrides nor "upgrades" them.
- **No second PnL truth / no bridge:** `research/` imports no `backtest`/`management`/`fast_path`/
  `value_store`; no value engine is touched.
- **No new dependency** (`numpy`/`pandas`/`polars` stay unimportable); **no new paid data**
  (`fomc`/`cpi` stay deferred); no edits under `forbidden_paths`; no FUTSUB / core-pilot artifact
  edits; no single-factor-template (`SINGLE_FACTOR_THRESHOLD_TEMPLATE` /
  `src/alpha_system/strategies/templates.py`) edit.

## Expected Files (illustrative, not prescriptive)

- `research/differentiated_substrate_v1/CAMPAIGN_VERDICT.md` — **new** (per-item `primary_state` +
  `reason_code`; boundary roll-up; survivor-gate decision).
- `research/differentiated_substrate_v1/RUN_SUMMARY.md` — **new** (RUN_SUMMARY-equivalent closeout;
  per-phase deliverables; final boundary; carried caveats).
- `research/differentiated_substrate_v1/EVIDENCE_SUMMARY.md` — optional new (evidence inputs index,
  FUTSUB-style).
- `reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P05/reviewer_verdict.md` — **conditional**: present **only**
  if a `WATCH`/`CANDIDATE_RESEARCH` survivor exists (the asymmetric promotion-adjacent artifact +
  `reason_code`); **absent** for a clean no-survivor refresh (mirrors FUTSUB-P29).
- `docs/differentiated_killshot_v1/CLOSEOUT.md` — optional new (durable closeout/runbook note, no
  claims).
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P05.md` — **new** (commit-eligible handoff).
- `reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P05/**` — **new** (YELLOW review notes + verdict).

## Forbidden Changes

- Editing any path under `forbidden_paths`: `src/alpha_system/execution/**`, `broker/**`, `live/**`,
  `portfolio/**`, `management/**`, `backtest/**`, `l2/**`, `agent_factory/**`,
  `core/value_store.py`, `strategies/templates.py`, `research/futures_substrate_scaleout_v1/**`,
  `research/futures_core_alpha_pilot_v1/**`, all `data/**`, `metadata/*.sqlite|*.db`,
  `registry/*.sqlite`, `artifacts/**`, and any
  `*.parquet`/`*.arrow`/`*.feather`/`*.dbn`/`*.zst`/`*.sqlite`/`*.db`.
- Re-running, re-scoring, re-calibrating, or **changing** any DK-P03 mechanism state or the DK-P04
  `EXPLORATORY` status; "upgrading" a state or inventing a new metric.
- **FDR-before-metric breach:** introducing any new real-data metric in this phase (the FDR
  active-subset restatement and surrogate zero-pass already gated the only allowed metrics in DK-P03;
  DK-P05 inspects no new value). Encoding any down-scope as a `BudgetAmendmentRecord`
  (`create_budget_amendment_record` enforces `new_budget > prior_budget` — strictly increasing — so
  it **cannot** encode the campaign's downward restatement; the restatement stays a value-free
  pre-registration note).
- Promoting, or letting Track B `EXPLORATORY` output become promotion evidence; auto-promoting a
  `WATCH`/`CANDIDATE_RESEARCH` survivor; building any factory/FactorLibrary/AlphaBook entry by
  inertia.
- Importing `backtest`/`management`/`fast_path`/`value_store` from `research/`; creating a second PnL
  truth; touching the value engine or the single-factor template.
- Adding a runtime dependency (`numpy`/`pandas`/`polars`); new paid data (`fomc`/`cpi` stay
  deferred); secrets/credentials; raw/canonical/factor/label data, caches, model binaries, large
  artifacts.
- `git add .`, `git add -A`, force push, auto-merge, deployment, PR creation, or any broker/live call.
- Weakening, skipping, or adding visible test-only branches to existing tests/checks/canaries.

## Interfaces / Contracts

- **Aggregation is a faithful carry, not a re-derivation.** Each `CAMPAIGN_VERDICT.md` per-item row
  reproduces the DK-P03 `primary_state` + `VerdictReasonCode` (or the DK-P04 `status` +
  `issue_code`/`reason_code`) **verbatim**; the boundary roll-up counts are the sum of the per-item
  rows and must be internally consistent (each cell traceable to listed items).
- **Allowed states only:** every assigned `primary_state` ∈ {`REJECT`, `INCONCLUSIVE` (with a
  `reason_code`), `WATCH`, `CANDIDATE_RESEARCH`}. No other state is emitted.
- **Survivor-gate contract (asymmetric):**
  - **No-survivor branch:** if zero `WATCH`/`CANDIDATE_RESEARCH` survivors exist, the closeout records
    a **conclusive kill-shot** with the trustworthy-negative argument; **no** `reviewer_verdict`
    artifact is required (mirrors FUTSUB-P29).
  - **Survivor branch:** if any `WATCH`/`CANDIDATE_RESEARCH` survivor exists, a committed
    `reviewer_verdict` artifact + `reason_code` is **required**, the survivor is **surfaced to the
    user**, and the closeout states no auto-promotion occurred.
- **Track B is permanently `EXPLORATORY`/non-promotion:** the DK-P04 readout enters
  `CAMPAIGN_VERDICT.md` as context with `promotion_eligible:false`; it can never be the survivor that
  earns promotion, and the trusted resolver still refuses it.
- **No-bridge / no-second-PnL:** the aggregation reads committed markdown/JSON only; `research/`
  imports no `backtest`/`management`/`fast_path`/`value_store`; no value is computed.
- **Non-claim language:** the document is an allowed-state verdict record + evidence summary; it makes
  **no** profitability, tradability, or alpha claim and creates no promotion/strategy/PnL truth.

## Validation

Run from the repo root. All commands are local-only and make **no** provider, network, merge, or
external calls.

```bash
# 1) Repo smoke.
python tools/verify.py --smoke

# 2) Authoritative suite (closeout phase runs --all). Run in a clean shell with FRONTIER_* env
#    unset to avoid the known driver-env false negative.
python tools/verify.py --all

# 3) Safety canaries must remain all-PASS (planted_fake_alpha, true-alpha pair,
#    forbidden_second_pnl_truth, forbidden_exploratory_promotion, governance_random_target,
#    forbidden_scope_drift).
python tools/hooks/canary_runner.py

# 4) No new dependency: numpy/pandas/polars must remain unimportable.
python -c "import importlib.util,sys; bad=[m for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]; sys.exit('forbidden dependency importable: '+','.join(bad) if bad else 0)"

# 5) No research->sim bridge: research/ must not import backtest/management/fast_path/value_store.
grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)|from +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)" src/alpha_system/research && echo "FORBIDDEN IMPORT FOUND" && exit 1 || echo "no forbidden research->sim imports"

# 6) Aggregation is value-aggregating only: confirm CAMPAIGN_VERDICT.md exists, uses only the four
#    allowed states, and that the boundary roll-up is internally consistent (manual + reviewer check).
test -f research/differentiated_substrate_v1/CAMPAIGN_VERDICT.md

# 7) Run-artifact discipline: must print nothing.
git ls-files runs
```

Record any skipped check and its exact reason in the handoff. If `python tools/verify.py --all`
shows only the known `FRONTIER_*`-env driver false negative, re-run in a clean shell and document
the outcome rather than weakening any check.

## Artifact Policy

Run artifacts are local-only and must never be committed:

- `runs/**` is **local-only runtime state** (state, events, costs, STOP, run-local
  `handoff.md`/`review.md`/`verdict.json`, checks, repair attempts) — local audit and resume only.
- `runs/.gitkeep`, `runs/README.md`, and `runs/**` must **not** appear in Allowed Paths.
- The commit-eligible handoff goes under `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P05.md`; the
  run-local `runs/<run_id>/.../handoff.md` stays local-only.
- `git ls-files runs` must return empty; explicit staging only; never `git add .` / `git add -A`;
  never force push.
- Never commit: `runs/**`, any `*.parquet`/`*.arrow`/`*.feather`/`*.dbn`/`*.zst`/`*.sqlite`/`*.db`,
  `data/raw/**`, `data/canonical/**`, `secrets/**`, `**/*.key`.

### Allowed Paths (commit-eligible — explicit staging only)

These are the **only** paths this phase may stage and commit. Stage by explicit path.

- `research/differentiated_substrate_v1/**`
- `campaigns/DIFFERENTIATED_KILLSHOT_V1/**`
- `docs/differentiated_killshot_v1/**`
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P05.md`
- `reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P05/**`

### Local-only run artifacts (NOT commit-eligible, never staged)

- `runs/**` — local audit and resume only. **No `runs/` path appears under Allowed Paths above.**

## Allowed Test Paths

- No new product tests are expected for this aggregation-only phase. If a small consistency check is
  added (e.g. asserting `CAMPAIGN_VERDICT.md` uses only the four allowed states, or that the roll-up
  counts equal the per-item rows), it lives under `tests/**` and must not weaken or skip existing
  tests, and must not add visible test-only special cases. Note: `tests/**` is **not** in this
  phase's Allowed Paths — if a test is genuinely warranted, surface it to the user rather than
  silently staging outside the locked path set.

## Auto-Merge / Review Policy

This spec authorizes no PR creation, no auto-merge, and no deployment. Merge gating is the Ralph
driver's responsibility under the YELLOW lane policy (fresh Claude Opus review required; block on
critical / test-tamper / boundary violation / promotion drift) plus human authorization — not this
spec.

## Repair-or-Rollback

- **In-scope repair only:** fix aggregation/roll-up/caveat/survivor-gate wording or the conditional
  `reviewer_verdict` artifact within the Allowed Paths; do not expand scope to re-run studies, change
  upstream states, or fix unrelated findings.
- **Rollback:** the change is additive documentation (plus a conditional survivor `reviewer_verdict`);
  revert the new `CAMPAIGN_VERDICT.md` / `RUN_SUMMARY.md` / closeout docs and any survivor artifact to
  restore the prior state — no code, engine, data, or migration change.
- **STOP / escalate (do not auto-proceed):** any pressure to change a DK-P03/DK-P04 verdict, invent a
  new metric, promote or auto-promote a survivor, build a factory/FactorLibrary/AlphaBook entry,
  author the next campaign, encode the down-scope as a `BudgetAmendmentRecord`, import the value
  engine into `research/`, add a dependency or paid data, weaken a truth-chain invariant, or commit a
  `runs/`/data/secret artifact — treat as out-of-scope and surface to the user.

## Done Criteria

- `research/differentiated_substrate_v1/CAMPAIGN_VERDICT.md` aggregates **all 5 Track A mechanisms +
  the 1 Track B item**, each with `primary_state` + `reason_code`, using **only** the four allowed
  states, with an internally-consistent boundary roll-up.
- The **survivor gate is applied**: either (a) **0 clean survivors** documented as a **conclusive
  kill-shot** with the trustworthy-negative argument (surrogate zero-pass + planted/true-alpha
  canaries + FDR-before-metric) and **no** reviewer-verdict artifact required; or (b) a
  `WATCH`/`CANDIDATE_RESEARCH` survivor **surfaced** with a committed `reviewer_verdict` artifact +
  `reason_code`, **not auto-promoted**, **no** factory built.
- An **evidence summary + RUN_SUMMARY-equivalent** closeout is written, carrying caveats forward
  (zero-feed calendar approximations, `N_eff`/power limits, any Track B `DATA_GAP`, `fomc`/`cpi`
  deferred = `needs_paid_data`, overnight family deferred).
- **Research-only language**; no profitability/tradability/alpha claim; **no promotion**; **no
  next-campaign authoring**; Track B stays permanently `EXPLORATORY`/non-promotion.
- No DK-P03/DK-P04 state changed; no new metric/calibration; `research/` imports no value engine.
- `python tools/verify.py --smoke` + `--all` pass (or the only failure is the documented
  `FRONTIER_*`-env false negative); `python tools/hooks/canary_runner.py` all-PASS;
  `numpy`/`pandas`/`polars` remain unimportable; no new paid data.
- `git ls-files runs` empty; explicit staging only; no edits under `forbidden_paths`.
- Commit-eligible handoff written; YELLOW review artifacts present.

## Handoff Requirements

Write the commit-eligible handoff at `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P05.md`: scope
delivered, the exact validation commands run with results, any skipped check + reason, files changed
by path, and confirmation that —

1. `CAMPAIGN_VERDICT.md` carries all 5 Track A + 1 Track B item with `primary_state` + `reason_code`,
   uses only the four allowed states, and the boundary roll-up is internally consistent;
2. the survivor gate was applied — state the branch taken (conclusive 0-survivor kill-shot **or**
   surfaced survivor with a committed `reviewer_verdict` + `reason_code`, not auto-promoted);
3. no DK-P03/DK-P04 verdict was changed and no new metric/calibration was produced;
4. `research/` imports no `backtest`/`management`/`fast_path`/`value_store` (no second PnL truth);
5. the closeout carries the caveats forward (zero-feed approximations, `N_eff`/power, Track B
   `DATA_GAP` if any, `fomc`/`cpi` deferred, overnight deferred) and makes no profitability/
   tradability/alpha claim and no promotion;
6. canaries all-PASS; `numpy`/`pandas`/`polars` unimportable; `git ls-files runs` empty.

The run-local `runs/<run_id>/.../handoff.md` stays local-only and must not be staged.

## Review Requirements

YELLOW lane requires a **fresh Claude Opus review**. Commit-eligible review notes + verdict belong
under `reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P05/**`; run-local `review.md`/`verdict.json` stay under
`runs/<run_id>/...` and are not committed. The reviewer must adversarially confirm:

- **Verdict honesty:** every per-item state in `CAMPAIGN_VERDICT.md` matches DK-P03 `verdict_refresh.md`
  / DK-P04 `EVIDENCE.json` verbatim (no silent re-derivation or "upgrade"); only the four allowed
  states appear; the boundary roll-up counts equal the per-item rows.
- **Survivor-gate discipline:** the trustworthy-negative argument is **earned** (surrogate zero-pass +
  planted/true-alpha canaries + FDR-before-metric), not asserted; for any `WATCH`/`CANDIDATE_RESEARCH`
  survivor, a committed `reviewer_verdict` + `reason_code` exists and the survivor is **surfaced, not
  auto-promoted** — no factory by inertia.
- **No promotion / no bridge / no second metric:** no promotion, no FactorLibrary/AlphaBook entry, no
  next-campaign authoring, no new metric/calibration, no down-scope `BudgetAmendmentRecord`;
  `research/` imports no value engine; Track B stays permanently `EXPLORATORY`/non-promotion.
- **Caveat fidelity + non-claims:** zero-feed approximations, `N_eff`/power limits, Track B
  `DATA_GAP`, `fomc`/`cpi` deferred, and overnight deferred are all carried; C2 (first-light is a
  `DATA_GAP`, not real evidence) and C3 (de-stack is a restatement, not corroboration) non-claims
  hold; research-only language throughout.
- **Discipline:** no new dependency / paid data; canaries green; artifact + explicit-staging
  discipline honored; `git ls-files runs` empty; no edits under `forbidden_paths`.
