## Claude Opus Review — ALPHA_RESEARCH_RUNTIME_MVP / RT-P19 (Runtime Cache and Local Artifact Policy)

### Scope and posture
Verified against `AGENTS.md`, `CLAUDE.md`, the artifact/lane rules, the generated spec, and the live repository artifacts (not just the executor summary).

This is a YELLOW, orchestration-only, descriptive-policy phase. I confirmed it adds two pure modules plus docs/README/handoff and introduces no compute, I/O, network, broker/live/paper, or destructive behavior.

### What I verified directly

**Orchestration-only, no duplication.**
- `artifact_policy.py` is a pure classification surface — fail-closed: `commit_allowed = not reasons` (any negative signal → `local_only`). Forbidden path prefixes include `runs/`, `artifacts/`, `cache/`, `data/{raw,canonical,factors,labels,cache}/`, `metadata/`, `logs/`, `$alpha_data_root/`; heavy suffixes and value-bearing kind tokens are classified out. No values embedded.
- `cache_policy.py` is metadata-only (no payload reads, no directory/file creation). It **reuses** `governance.serialization.content_hash` rather than reimplementing a primitive — correct consume-don't-duplicate posture. `resolve_storage_root` rejects any non-`runs/**` root that resolves inside the repo tree.

**Lineage-keyed invalidation.** Cache key binds dataset/feature/label/code/config (+ optional cost-model) versions and run scope; the parametrized test proves the key changes when any lineage component changes (no stale cross-version hit), and `lookup` classifies hit/miss/stale deterministically.

**Tests are genuine and fail-closed, not weakened.** `test_artifact_policy.py` asserts heavy/value/provider/db/log/cache outputs are `local_only`, only small curated row-free summaries are `commit_allowed`, and a `runs/**` path is never commit-eligible even when curated+row-free. `test_cache_policy.py` correctly imports from the relocated `cache_policy` module.

**Artifact policy / git discipline.**
- `git ls-files runs` → empty. Staged set is exactly the 7 curated paths; no `runs/`, heavy, DB, or data path staged.
- `just frontier-doctor` passed; `just verify-canaries` → all 16 canaries PASS (including `forbidden_cache_data_commit`, `forbidden_local_artifacts`, `forbidden_scope_drift`, `forbidden_raw_data_commit`).

**No prohibited content.** No alpha/tradability/profitability/strategy/portfolio/production claims; README and `CACHE_AND_ARTIFACTS.md` are factual, compact, and reaffirm unchanged safety boundaries; next pointer correctly set to RT-P20.

### Warnings (non-blocking)

1. **Spec-vs-implementation path deviation (the B1 repair).** The spec's Allowed Paths list `src/alpha_system/runtime/cache/**` and `tests/unit/runtime/cache/**`, but `.gitignore:25` (`**/cache/`) would have silently ignored those paths — an internally inconsistent spec that demanded commit-eligible files at a forbidden location. The executor correctly relocated to `cache_policy.py` / `test_cache_policy.py`. This is the right call, but it is a real divergence from the approved spec; future `frontier-spec` generation should not emit `cache/**` as commit-eligible.

2. **Staged handoff is stale.** `handoffs/.../RT-P19.md` shows `AM` — the working tree has a validation appendix (post-staging `git status`, audit commands) that was **not** re-staged because the worktree's real git index is on a read-only mount. The handoff that would be committed is missing that appendix. Ralph/HANDOFF_VALIDATE should re-stage the final handoff before commit.

3. **`verify.py --all`: 13 failed / 2366 passed**, disclosed honestly by the executor, located in existing Frontier/GitHub driver tests. The relevant regression surface passed (runtime suite 197 passed; narrow policy tests 26 passed; canaries pass), and this phase touches no driver code, so these are almost certainly pre-existing baseline failures (consistent with prior FLF closeout warnings). **Ralph's CHECKS_RUN gate must confirm these are pre-existing and unrelated**, not introduced by RT-P19, before merge.

### No blockers found
No broker/live/paper/order scope; no destructive ops; no hidden failed runs (the `--all` failure was disclosed); no test weakening; no artifact-policy violation; no unsupported alpha claims; no scope drift into forbidden packages.

The three items are warnings to be resolved by the driver (re-stage handoff; confirm `--all` baseline) and a spec-quality note — none undermines the deliverable, which is correct and policy-compliant.

VERDICT: PASS_WITH_WARNINGS
