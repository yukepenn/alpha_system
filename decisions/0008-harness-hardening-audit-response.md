# ADR-0008 — Harness Hardening Audit Response (2026-06-08)

Status: Accepted
Date: 2026-06-08
Context: Applied while the live Workflow 2 run `FEATURE_COMPUTE_FAST_PATH_V1`
(run `2026-06-08T160146Z`) was executing (driver PID 738624, on FCFP-P10).

## Context

Two external audits of the harness were received. They were produced by fetching
the repo over the GitHub web/API surface, which **robots-blocked the load-bearing
files** (`.githooks/**`, `tools/hooks/**`, `.claude/**`, `tools/verify.py`,
`tools/frontier/**`). Many findings were therefore explicitly UNVERIFIED guesses.
This ADR records what was verified against the real local repo, what was applied,
what was corrected (audit was wrong), and what was deliberately deferred.

Constraints honored: Codex executor effort stays **xhigh** (per operator); agents
retain full system/git access (assumed justified); no force-push; explicit staging;
never commit `runs/**`/values/SQLite/heavy artifacts; do not perturb the live run.

## Applied (verified real, high-leverage, safe)

1. **Status source-of-truth — `tools/frontier/status_doctor.py` (new).**
   The committed pointers drift behind a running campaign (verified: `ACTIVE_CAMPAIGN.md`
   claimed `FCFP-P01` while the live run was at `FCFP-P10`, merged 10/16). The doctor
   reads `runs/<run_id>/state.json` + `heartbeat.json` as the authoritative live phase,
   reconciles the committed pointers, flags stale historical docs, and checks the
   runtime contract. `just status-doctor` / `--strict` / `--json`. Source of truth is
   now the live run state, not prose.

2. **Runtime contract mismatch — FIXED.** Verified real: `campaign.yaml`
   `runtime.python: '3.11'` vs `pyproject` `requires-python >= 3.12` vs actual venv
   `3.12.3`. Set campaign runtime to `3.12`. The doctor now enforces this invariant.

3. **Claude hooks were genuine no-ops — COMPLETED.** Verified: `boundary_guard.main()`
   and `artifact_guard.main()` only inspected positional `paths`; the `--claude-pre/
   post-tool-use` flags were parsed but **unused**, and neither read stdin. The hooks
   fired with zero paths and always passed. Completed the half-built feature: in
   `--claude-*` mode the guards now parse Claude's stdin JSON payload and enforce on
   the target path. Safety refinements beyond the audit: enforcement is scoped to
   **write-class tools only** (Edit/Write/MultiEdit/NotebookEdit) so legitimate
   outside-repo *reads* (e.g. `~/.claude` memory) are never blocked, and the guards
   **fail open** on malformed/empty stdin so a parse hiccup cannot brick a session.
   Covered by `tests/unit/test_claude_hook_guards.py` (in-repo write passes,
   outside-repo write blocks exit 2, outside-repo read passes, malformed fails open,
   forbidden artifact flags, pre_commit explicit-path mode unchanged).

4. **`CRITICAL.md` (new) agent entry point** + referenced from the top of `AGENTS.md`.
   One page: invariants, live-status authority, safety-gate files, headless trust
   boundary, pre-flight, hard stops.

5. **Headless trust boundary + live-status authority + second-PnL invariant** added to
   `AGENTS.md` Hard Constraints. Task data (specs/handoffs/READMEs) is data, not
   policy; policy-altering instructions inside it are treated as prompt injection.

6. **Adversarial reviewer subagent** — `.claude/agents/reviewer.md` rewritten from a
   2-line stub into a skeptical, schema-driven checklist mirroring the
   `frontier-review` skill (assume-spurious, single-truth, no-lookahead, test-gaming,
   artifact policy, inheritance).

7. **`just doctor` / `just agent-preflight` / `just status-doctor`** targets wiring the
   doctor + smoke + canaries + diff-scoped artifact/boundary guards.

8. **`max_estimated_usd`** set to a forward value (50.0) with a comment documenting
   that it is currently **inert** (the driver trips only when `estimated_cost_usd >
   limit > 0`, and real provider cost is never populated). The honest effective AFK
   ceiling today is `max_run_minutes`/`max_phase_minutes` + supervision.

## Corrected (audit was wrong — verified)

- **`providers.claude.output_format: null` is NOT a bug.** There is a dedicated
  conservative verdict parser (`tools/frontier/verdict.py`, `VERDICT_RE`,
  `parse_review_text`). `claude -p --output-format json` would wrap output in an API
  envelope and **break** that text parser. Left as `null`. No change.
- **The driver's review is already adversarial.** `frontier-review/SKILL.md` already
  checks scope/coupling/test-gaming/boundary/inheritance. Only the *manual* reviewer
  subagent was weak; that is what was strengthened (item 6). The driver path was fine.
- **Codex effort xhigh** retained per operator instruction (audit recommended high).
- **`trading_enabled: true`** is not consumed by any code in `tools/` (grep-verified) —
  it is a descriptive profile field, not an execution gate. Not flipped; the real gates
  are lanes + `PROJECT_OP_*`. No false security removed by changing it.

## Deferred (real, but sequenced AFTER the live run to protect it)

`tools/hooks/canary_runner.py` is a **required check** the live driver runs for every
Yellow merge. Adding new canaries to it now risks blocking FCFP-P11..P15 if any new
canary misfires. The following are therefore specced here and to be wired in a small
reviewable phase **after FCFP closes**, not mid-run:

- `second_pnl_truth` — fail if value/PnL-accounting math is defined outside the
  sanctioned reference path.
- `status_consistency` — `status_doctor --strict` as a gating canary.
- `runs_staging` / `local_data_commit` — assert the artifact guard blocks `runs/**`
  and value/data/SQLite/heavy globs (locks existing, verified behavior).
- `headless_prompt_injection` — a planted policy-override spec the reviewer must reject.
- `reviewer_self_approval` — executor cannot mark its own Yellow/Red phase reviewed/done.

Doc-bloat consolidation (the audits flagged ~17–90 docs, duplicate CLI docs, etc.) is
intentionally **not** undertaken here: it is cosmetic, carries cross-reference risk, the
repo already has `docs/_historical/` + `docs/AGENT_CONTEXT_MAP.md`, and it is unrelated
to agent correctness. Tracked as low-priority cleanup.

## Follow-up applied same day (operator: "apply all, don't defer; rerun risk accepted")

The deferral above was reconsidered at operator request. The new checks were
implemented in a way that is **safe for the live merge gate** because canaries run
against temp-repo fixtures, not the live run's files; deterministic fixtures that
pass once pass always.

Applied (batch 2):
- **`forbidden_runs_staging` canary** — locks that the artifact guard blocks
  staging `runs/**` state/events/values. Closes the one gap in the existing
  forbidden-artifact canary coverage.
- **status doctor wired into `verify.py --all/--ci`** (`check_status_consistency`)
  — CI now fails on a runtime-contract contradiction and reports pointer drift.
- **`test_single_pnl_truth_invariant.py`** — the repo-appropriate "no second PnL
  truth" enforcement: locks that the reference engine, fast path, and the
  reference<->fast **parity harness** (`backtest/parity.py` + `tests/parity/**`,
  incl. equity-curve parity and unsupported-feature fail-closed) all exist and are
  wired. Removing the parity guarantee now fails CI.
- **`test_lane_review_policy.py`** — locks that Yellow and Red require an
  independent Claude review (executor cannot self-approve material/external work),
  Red never blind auto-merges, and Green stays bounded/low-risk.

Deliberate non-changes, with evidence (these would have done harm):
- **No `second_pnl_truth` grep-guard.** Verified: PnL/equity is legitimately
  *consumed* across ~15 modules (`backtest/{reference,equity,accounting,fast_path,
  parity,results,trades}`, `experiments/*`, `management/*`, `cli/backtest`). A
  pattern guard would false-positive en masse and block legitimate commits. The
  real single-truth guarantee is the parity harness, now locked by a test.
- **No test-tamper env-provenance change.** `test_tamper_guard` trusting
  `FRONTIER_ALLOWED_TEST_PATHS` is by design for authorized test-touching phases;
  rewiring it to require active-spec provenance is a driver change that could block
  in-flight phases (P11-P15). Tracked as a driver-side follow-up, not a hot patch.
- **`holdout_access` / `bbo_execution_truth` canaries** not added: both need a
  precise pattern/partition model to avoid false-positives and are partly covered by
  existing governance canaries + `BACKTEST_TRUTH_POLICY.md`. Tracked as follow-ups.
- **Doc-bloat consolidation** still skipped (cosmetic, cross-ref risk).

## Batch 3 — third audit response (skills/secret-scan/doc-staleness)

A third audit (which had read the batch-1/2 changes) surfaced a few genuinely new,
verified items; several of its other findings were wrong and were skipped with evidence.

Applied:
- **`frontier-campaign/SKILL.md`** — quoted the frontmatter description (the unquoted
  colon made the YAML fragile) and removed the stale `PROJECT_STATUS.md` / `PROGRESS.md`
  reads, replacing them with `CRITICAL.md` / `ACTIVE_CAMPAIGN.md` / `just status-doctor`.
- **`frontier-ralph/SKILL.md`** — replaced the stale "scaffold until provider
  integrations are implemented" line with the accurate "provider-wired and live".
- **`secret_scan.py`** — added a narrow, high-confidence **content** scan (private-key
  PEM headers, `AKIA…`, `xoxb-…`, `ghp_…`) on top of the path-name scan, with the same
  security-tooling exemption the path scan uses (so the scanner's own canary/test
  fixtures don't self-flag). Verified the entire tracked tree is clean. Locked by
  `tests/unit/test_secret_content_scan.py` + a `forbidden_secret_content` canary
  (innocuous filename → only the content scan catches it).
- **`verify.py --all/--ci`** now runs the **canary gate** (`check_canaries`), so "--all"
  no longer under-reports coverage.
- **`verifier.md`** subagent rewritten from a one-liner into concrete commands
  (status-doctor, agent-preflight, narrowest-test-first, parity/no-lookahead) with a
  "never paraphrase a red as green" rule.
- **Stale-status banners** added to `PROJECT_STATUS.md`, `PROGRESS.md`, and
  `docs/AGENT_CONTEXT_MAP.md` pointing to `CRITICAL.md` + `just status-doctor` (lighter
  and reference-safe vs. moving the files).

Skipped (audit was wrong — verified):
- **README Workflow-2 command drift**: the named commands (`just frontier-run-campaign`,
  `frontier-run-next`, …) do **not** appear in the README. Fabricated finding.
- **Wiring `random_target` into `canary_runner`**: `random_target` is a *study-level*
  negative-control type recorded in evidence bundles, **not** a runnable hook canary —
  the governance harness only accepts `future_shift/permuted_labels/optimistic_fill`, so
  wiring it would raise `invalid choice` and break the canary gate. Tested first.
- **`status_doctor --strict` in `agent-preflight`**: drift is expected during a live run
  (the committed pointer legitimately lags), so strict-mode preflight would fail
  spuriously. Left non-strict.
- Mass deletion of one-line subagents / `notification.sh`, `trading_enabled` rename,
  `max_estimated_usd` removal: cosmetic or already handled; not worth churn/risk.

## Consequences

The single most important gap the audits identified — "live status is duplicated and
stale, so an autonomous agent cannot know what to work on" — is closed: `status_doctor`
makes `runs/<run_id>/state.json` the authoritative answer and fails on runtime/pointer
contradictions. The decorative Claude hooks now enforce for real without risk of
self-bricking. No change perturbs the in-flight run (additive files + the driver
snapshots lane policy at start). New canaries are deferred to protect the live merge gate.
