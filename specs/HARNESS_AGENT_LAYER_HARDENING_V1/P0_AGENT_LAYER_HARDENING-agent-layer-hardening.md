---
campaign_id: HARNESS_AGENT_LAYER_HARDENING_V1
phase_id: P0_AGENT_LAYER_HARDENING
lane: yellow
status: in_progress
---

# P0_AGENT_LAYER_HARDENING: Agent-layer enforcement-floor hardening

## Purpose

Close verified enforcement gaps in the agent-operating layer surfaced by an
external audit. Every audit claim is re-verified against the current code
before acting (see Verification Notes); stale claims are recorded, not acted
on. This phase makes Workflow 1 minimally real, adds missing guard coverage
(hooks floor, second-PnL-truth canary, force-push ancestry), makes the budget
key honest, hardens the nightly audit, rewrites the review skill to the
adversarial standard, and removes decorative subagent stubs.

## Scope

1. Minimal real Workflow 1 in `tools/frontier/phase.py`: `workflow1 --phase`
   resolves the spec under `specs/**`, fails (exit 2) on missing spec,
   template placeholders, or `draft` status; parses `## Validation`, executes
   each backticked command in order, streams output, records results to
   `runs/wf1/<PHASE>/validation.json` + `validation.md` (local-only).
   `--stage review-gate` requires `reviews/<campaign_id>/<PHASE>-verdict.json`
   with verdict PASS / PASS_WITH_WARNINGS. `review --phase` prints the review
   contract and exits 1 (review is produced by the frontier-review skill /
   reviewer agent, not this CLI). Justfile recipe comments updated. Unit
   tests in `tests/unit/frontier/test_phase_workflow1.py`.
2. Hooks floor check in `tools/frontier/status_doctor.py`: WARN (not FAIL)
   when `git config --get core.hooksPath` is not `.githooks`, reporting the
   actual value. Unit test added to `tests/unit/test_status_doctor.py`.
3. Second-PnL-truth detection + canary: definition-scoped detection in
   `tools/hooks/forbidden_pattern_guard.py` (function definitions matching
   pnl / equity_curve in `src/**` outside the sanctioned reference engine
   `src/alpha_system/backtest/**`), plus a blocking canary and a sanctioned
   negative canary in `tools/hooks/canary_runner.py`.
4. Adversarial rewrite of `.claude/skills/frontier-review/SKILL.md`, aligned
   with `.claude/agents/reviewer.md` (assume-broken stance, required proof
   order, required outputs and verdict schema).
5. `frontier.yaml` `workflow2.max_estimated_usd: null` with a comment marking
   it inert until real provider USD accounting exists; null-safety verified
   in config validation and the driver budget gate; unit tests added.
6. `.github/workflows/frontier-nightly-audit.yml` extended with the canary
   runner (gating) and status doctor (informational, exit-tolerant).
7. Force-push detection in `tools/hooks/pre_push.py`: parse the pre-push
   stdin ref lines, block non-fast-forward updates (remote sha not an
   ancestor of local sha) and deletion of `refs/heads/main`; branch deletes
   for non-main refs stay allowed. Decision logic refactored into a testable
   function; unit tests in `tests/test_hooks.py`.
8. Delete decorative subagent stubs with zero functional references:
   `.claude/agents/{architect,researcher,release_manager,done_checker,harness_maintainer}.md`.
   `reviewer.md` and `verifier.md` are kept unconditionally.

## Non-goals

- No `ralph_driver` review-path or CHECKS_RUN changes (deferred post-LCFP).
- No `merge_gate` policy-boolean changes (deferred post-LCFP).
- No provider verdict-format changes (deferred post-LCFP).
- No frontier-audit / frontier-review skill merge (deferred post-LCFP).
- No `frontier.yaml` key renames (deferred post-LCFP).

## Validation

- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/frontier/test_phase_workflow1.py tests/unit/test_status_doctor.py tests/test_hooks.py tests/test_frontier_config.py tests/test_canaries.py -q`
- `python tools/verify.py --smoke`
- `python tools/hooks/canary_runner.py`
- `just frontier-check-config`
- `bash -n .githooks/pre-push`
- `bash -n .githooks/pre-commit`

## Verification Notes

Claim-by-claim verification against origin/main (8ef17e6), performed before
any change. One claim was partially stale; everything else verified true.

1. **Workflow 1 scaffold — VERIFIED TRUE.** `tools/frontier/phase.py`
   `workflow1` printed `"Workflow 1 scaffold for phase <X>."` and `review`
   printed `"Review scaffold for phase <X>."`, both returning 0 with no spec
   resolution, no validation execution, no review-gate. Implemented for real.
2. **status_doctor lacks core.hooksPath check — VERIFIED TRUE.** No
   `hooksPath` reference anywhere in `tools/frontier/status_doctor.py`.
   Added as WARN-level (not FAIL) so CI containers without hook config do
   not fail; CI enforces guards via workflows instead.
3. **No second-PnL-truth canary — VERIFIED TRUE, with context.**
   `canary_runner.py` hardcodes scenarios and has no second-truth case. No
   existing guard catches a PnL/equity-curve definition outside the
   sanctioned engine: `boundary_guard.py` is path-escape-only and
   `forbidden_pattern_guard.py` had no pnl/equity snippets. The audit's
   suggestion to put detection "in boundary_guard" was misdirected;
   `forbidden_pattern_guard` is the content-pattern guard and got the check.
   ADR-0008 had deliberately rejected a *consumption*-grep (PnL is
   legitimately consumed across ~15 modules); this implementation is
   *definition*-scoped (`def \w*(pnl|equity_curve)\w*(`) and restricted to
   `src/**` outside `src/alpha_system/backtest/**`, which a full-tree grep
   confirmed has zero false positives today (rolls.py `equity_index` and
   `accounting_weight`-style names do not match; "accounting" was
   deliberately excluded from the pattern because
   `data/foundation/requests.py:accounting_weight` and
   `governance/trial_ledger.py:evaluate_trial_ledger_accounting` are
   legitimate non-value-truth definitions). `features/fast/**` and
   `labels/fast/**` fall under the general `src/**` rule (value-only, not
   sanctioned for PnL). A negative canary proves the sanctioned engine path
   is not false-positived.
4. **frontier-review skill not adversarial — PARTIALLY STALE.** The audit's
   framing that "the review layer is not adversarial" is stale for
   `.claude/agents/reviewer.md`, which ADR-0008 already rewrote to the
   adversarial standard (assume-broken stance, proof order, cite file:line).
   It remained TRUE for `.claude/skills/frontier-review/SKILL.md`, which was
   still a thin inputs/outputs checklist with no assumed-broken stance, no
   proof order, no status-doctor step, no single-truth/no-lookahead checks,
   and no verdict schema. SKILL.md rewritten, aligned with reviewer.md.
5. **Budget inert — VERIFIED TRUE.** `ralph_driver.py:641` trips only when
   `estimated_cost_usd > max_estimated_usd > 0`; `estimated_cost_usd` is
   initialized 0.0 and never populated with real USD (PR #322 keeps USD
   honestly 0.0; only tokens/duration are real). `frontier.yaml` already
   carried an "currently INERT" comment (ADR-0008 item 8) but kept the
   misleading `50.0`. Set to `null`: `config.py` validation skips None
   (key presence still satisfies `REQUIRED_WORKFLOW2_KEYS`), and
   `env_or_config_number(..., None, 0)` returns 0.0, which disarms the
   `> 0` gate. Unit tests added for both.
6. **Nightly audit only boundaries/artifacts — VERIFIED TRUE.** The workflow
   ran exactly `verify.py --boundaries` and `verify.py --artifacts`.
   Extended with the canary runner (gating) and status doctor
   (exit-tolerant: no run state exists in CI, so it is informational there).
7. **pre_push lacks ancestry check — VERIFIED TRUE.** `pre_push.py` only ran
   smoke + canaries and never read the pre-push stdin ref lines, so a
   `--force` push that survived the forbidden-pattern guard would pass.
   Implemented `force_push_violations()` over the
   `<local_ref> <local_sha> <remote_ref> <remote_sha>` stdin protocol:
   remote-sha-zero (new ref) allowed; local-sha-zero (delete) allowed except
   `refs/heads/main`; otherwise `git merge-base --is-ancestor` must hold or
   the push is blocked citing the AGENTS.md force-push policy. An unknown
   remote sha (remote ahead) is conservatively treated as non-fast-forward.
   stdin is only consumed when not a TTY, so manual invocation keeps the old
   behavior.
8. **Decorative subagents — VERIFIED TRUE.** Whole-repo grep found zero
   functional references to `.claude/agents/{architect,researcher,release_manager,done_checker,harness_maintainer}.md`
   (each was a 2-line description stub). `frontier.yaml`'s `claude_architect`
   is a provider-config key, unrelated to the agent file. The Ralph
   done-check path does NOT use `done_checker.md` (no reference in
   `tools/frontier/**`). The only `.claude/agents/` mentions outside
   `reviewer.md`/`verifier.md` live in immutable historical artifacts
   (campaign plans, handoffs, reviews) and are generic, not file-specific —
   no doc-line updates required. `docs/SYSTEM_MAP.md` does not enumerate
   agent files. All five deleted; `reviewer.md` and `verifier.md` kept.

Audit-misdirection note (the stale parts): claim 4's blanket "review layer
not adversarial" ignored the ADR-0008 reviewer.md rewrite, and claim 3 named
`boundary_guard` as the detection point when that guard is path-escape-only.
Both recorded here; implementation went to the correct surfaces.
