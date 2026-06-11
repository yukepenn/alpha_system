# Review: PR #332 — harness(agent-layer): WF1 minimal-real + enforcement-floor hardening

- Reviewer: Claude (fresh adversarial review agent, 2026-06-11)
- Scope: full PR diff on `harness/agent-layer-hardening-v1` vs `main`
- Verdict: **PASS_WITH_WARNINGS** (no blockers; 3 MINOR findings fixed on-branch in `f69e45b` before merge)

## Deterministic evidence baseline

- CI: `gh pr checks 332` — canaries + validate green on the reviewed head.
- Artifact policy: `git diff main...harness/agent-layer-hardening-v1 --stat | grep runs` → empty; `git ls-files runs` → 0.
- Tests: 42 passed (`test_phase_workflow1.py`, `test_status_doctor.py`, `test_hooks.py`, `test_frontier_config.py`, `test_canaries.py`); diff contains only test additions, no skip/xfail/narrowed assertions.
- `python tools/hooks/canary_runner.py` → all 14 PASS, including `forbidden_second_pnl_truth` and `sanctioned_pnl_truth_allowed`.
- Canary fail-closed proof: neutering `second_truth_violation` in a copy flips the `expect_block=True` canary to FAIL; canary runner sandboxes fixtures in a temp git repo, never the real tree.
- Second-truth scan of real `src/**` → zero matches (no false positives on today's tree).
- `max_estimated_usd: null` consumers verified: `tools/frontier/config.py` skips validation on None; `ralph_driver.py` budget gate `> limit > 0` permanently disarmed — both unit-tested.
- 5 deleted subagent stubs: whole-repo grep shows no remaining references.

## Priority finding — pre_push force-push guard: CLEAN

`force_push_violations()` (`tools/hooks/pre_push.py`) probed against every legitimate-push scenario: new-branch first push (zero remote sha → allowed), remote-deleted branch (allowed), delete-push `:branch` (allowed except `main`), tags (new allowed; moving an existing tag blocked — that IS a forced update), colon refspecs (stdin protocol always 4 fields), TTY/manual invocation (stdin guarded by `isatty`). The squash-merge-then-reuse case blocks, but a plain push would be server-rejected as non-fast-forward anyway — not a false block. No case falsely blocks a push that could succeed without `--force`.

## Findings (all MINOR; 1–3 fixed in `f69e45b`)

1. **FIXED** `phase.py` `run_validation` out_dir — phase-id path traversal could write outside `runs/wf1/` (proven: `--phase '../../../../tmp/...'` escaped). Fix: `workflow1` rejects phase ids outside `[A-Za-z0-9_-]+`.
2. **FIXED** `workflow1` review-gate stage returned before placeholder/draft spec-approval checks. Fix: review-gate now runs after spec-approval gating.
3. **FIXED** `SECOND_TRUTH_DEF_RE` missed `async def` definitions. Fix: `(?:async\s+)?` added; probe asserts the match.
4. NOTED — docstring-level false positive possible (regex is text-level, not AST); zero hits on the real tree today; cost is a reword at commit time. Accepted for a pre-commit guard.
5. NOTED — WF1 `run_validation` executes spec Validation commands with no allowlist; mitigated (human-gated per phase, approved-spec gating, `shlex` no-shell, cwd pinned). Follow-up allowlist (pytest/verify/canary/just) if WF1 ever runs headless.
6. NOTED — `find_spec` silent first-match on duplicate phase_id; suggest exit 2 on >1 match if duplicates ever appear.
7. NOTED — `"TBD"` substring anywhere in a spec refuses WF1; clearly messaged, only the template contains it today.
8. NOTED — `second_truth_violation` prefix-matches relative paths only; real wiring (`pre_commit.py` → `git diff --cached --name-only`) always passes relative paths.

## Conclusion

Scope matches the PR description 1:1; no test weakening, no second truth, no artifact violations, no boundary violations. A fresh future agent can inherit safely. Merge approved after findings 1–3 landed and CI re-greened.
