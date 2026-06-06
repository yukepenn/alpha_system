I've completed a thorough review. All key checks pass. Let me record the verdict.

## Claude Opus Review — RT-P17: Reference Candidate Handoff Builder

**Lane:** YELLOW · **Verifier:** independent Claude Opus 4.8 review · **Branch:** `auto/alpha_research_runtime_mvp/rt-p17-reference-candidate-handoff-builder`

### Scope & contract compliance
- **Builder is handoff-only, not Reference validation.** `ReferenceCandidateHandoff` and `build_reference_candidate_handoff` (`src/alpha_system/runtime/handoff/reference.py`) assemble reference-only metadata (ids, hashes, states, scalar cost metadata, limitations). The payload carries `not_reference_validation`, `not_promotion`, `not_alpha_validation`, `reference_validation_performed=False`, and `handoff_only=True`. Matches GOAL.md Tier 2 and ACCEPTANCE.md.
- **State cap honored.** Forward state is hard-capped at `REFERENCE_HANDOFF_READY` (constructor raises if any other forward state is supplied; `_ready_or_blocked_decision` only emits `REFERENCE_HANDOFF_READY` or `BLOCKED`). `RuntimeDecisionState` does not even define the prohibited MVP states (`ALPHA_VALIDATED`/`FACTOR_PROMOTED`/`TRADABLE`/…), so none are reachable. Consistent with `decisions/states.py` and `campaign.yaml:282`.
- **`strategy_not_validated=True` and `next_required_gate = REFERENCE_VALIDATION_REQUIRED`** set on every handoff (`reference.py:342`, `:500`).
- **Fail-closed preconditions verified.** Missing `CostSensitivityReport`, missing `CostModelVersion`, missing `base`/`double_cost` profile, slippage not labeled proxy, or a non-`POINT_IN_TIME_SAFE` audit each yield a terminal `BLOCKED` with a visible `RejectionReasonRecord`. Upstream terminal `EvidenceDraft` stays terminal (not recast as ready). Tests cover all of these (missing cost stress, missing base profile, rejected audit, terminal-stays-terminal, scope-honest/value-free).
- **Orchestrates, does not duplicate.** Imports are confined to `alpha_system.runtime.*` plus `governance.serialization`/`ids` (hashing/IDs only, consistent with prior phases). No edits to `research/experiments/governance/backtest/features/labels/data` primitives — confirmed by grep and handoff attestation. No `cli/main.py` edit (CLI deferred to RT-P18). No `ACTIVE_CAMPAIGN.md` write.

### Safety
- No broker/live/paper/order/account/deployment/provider scope or imports. No alpha/tradability/profitability claims; scope-honesty test asserts absence of such tokens and of `.parquet`/raw/feature/label value keys. No raw or heavy data embedded (`raw_or_heavy_data_embedded=False`); refs are id+hash only.

### Artifacts & git discipline
- Working tree shows only allowed paths: `README.md` (M), `docs/research_runtime/REFERENCE_HANDOFF.md`, `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P17.md`, `src/alpha_system/runtime/handoff/`, `tests/unit/runtime/handoff/`. `git ls-files runs` empty. `.pyc`/`__pycache__` are gitignored, so curated-path staging won't drag artifacts. No forbidden/heavy/DB paths. Executor left everything unstaged per protocol.
- README snapshot is factual and compact: 18/27 through RT-P17 in `runtime_integration`, next RT-P18, new module + doc listed, safety boundaries reaffirmed including "a `ReferenceCandidateHandoff` is not Reference validation."

### Validation
- Independent stage: `just frontier-doctor` PASS; `just verify-canaries` all 17 canaries PASS (incl. scope-drift, boundary-import, raw-data, governance leakage canaries).
- Executor-reported: handoff tests `6 passed`, `tests/unit/runtime` `171 passed`, smoke PASS, ruff clean, canaries PASS, `git ls-files runs` empty. (Local pytest re-run blocked by sandbox; relied on executor + canary-stage corroboration.)
- `verify.py --all`: 13 failures, **confirmed out-of-scope** — all in `tests/test_github_utils.py` / `tests/test_ralph_driver.py` (provider-wired/resume/DAG-wave WF2 plumbing), none reference `runtime.handoff`. This is the same pre-existing WF2/GitHub/Ralph failure class documented in RT-P16, truthfully disclosed in the handoff caveats — not introduced by this phase.

### Notes / minor warnings
- The generated spec's literal `python -c "import alpha_system.runtime.handoff"` requires `PYTHONPATH=src` in this shell; the handoff documents this clearly and the `PYTHONPATH=src` form passes. Cosmetic, not a defect.
- The standing `verify.py --all` red (out-of-scope WF2 tests) remains an environmental backlog item, not a blocker for this YELLOW runtime phase.

No broker/live/paper scope, no destructive ops, no hidden failed runs, no test weakening, no artifact-policy violation, no unsupported claims, no scope drift. The handoff is truthful and complete.

VERDICT: PASS
