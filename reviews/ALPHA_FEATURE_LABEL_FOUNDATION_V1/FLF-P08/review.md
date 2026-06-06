## Claude Review — FLF-P08: Base OHLCV Feature Families

### Scope & lane
YELLOW substrate-construction phase. I reviewed the actual working tree, not just the executor summary.

### What I verified

**Artifact policy — clean.**
- `git status --short` shows only `README.md` modified plus untracked `configs/features/families/`, `docs/feature_label_foundation/features/`, `handoffs/.../FLF-P08.md`, `src/.../families/ohlcv/`, `tests/.../families/`. No shared-core, cross-family, label, governance, broker/live/paper, data, or `ACTIVE_CAMPAIGN.md` edits.
- `git ls-files runs` → empty. No `runs/` path staged or present. No data/DB/heavy/provider artifacts (only stray `__pycache__` `.pyc`, which are ignored, not committed).
- Validation output: `just frontier-doctor` exit 0; `just verify-canaries` all 16+ canaries PASS (including `forbidden_scope_drift`, `forbidden_boundary_import`, `forbidden_raw_data_commit`, `governance_future_shift`, `governance_permuted_labels`).

**Scope compliance — additive only.** All source/test/doc/config writes confined to the disjoint `families/ohlcv/**` namespace. The only shared write is the compact README snapshot (spec-permitted, reconciled by serial merge queue). README diff is factual, append-style, restates safety boundaries, adds no run details/local paths/alpha/tradability/broker claims.

**Contracts genuinely consumed, not re-implemented (R-022).** Confirmed the imported symbols exist in shared core: `require_feature_request_implementation_allowed` + `FeatureRequestGateDecision` (`request_gate.py`), `is_real_trade_bar` (`semantics.py`), `derive_feature_version` + `is_live_compatible` (`contracts.py`). The family routes admission through the FLF-P05 gate and derives `FeatureVersion` from the FLF-P06 `FeatureSpec`.

**Fail-closed semantics — correct.**
- `_require_definition` rejects non-eligible specs, gate-denied decisions, version mismatches, and non-causal windows.
- `available_ts` carried on every `FeatureValueRecord`; rows sorted by `available_ts`; window state restricted to `available_ts <= t`.
- No-trade rows (`is_real_trade_bar`) excluded from return/range/volume/VWAP/trend logic, emitting `None` + `no_trade`/`ohlcv_gap` flags rather than fills.
- Future/centered live windows rejected at `FeatureSpec` construction (`contracts.py:344` — test asserts `match="live FeatureSpec"`).
- Negative-path tests cover missing `available_ts`, absent/pending `FeatureRequest`, and future/centered windows.

**No prohibited scope/claims.** No materialization/persistence (in-memory records only), no provider calls, no broker/live/paper/order, no alpha/tradability/profitability claims, no prohibited MVP state. Docs and config are non-promotional.

### Warnings
1. **Bare-import validation command needs `PYTHONPATH=src`.** The spec lists `python -c "import alpha_system.features.families.ohlcv"` expecting success, but it fails on a raw interpreter (src-layout, package not installed). The executor disclosed this honestly and showed the `PYTHONPATH=src` variant passing; pytest passes via its own path handling. Cosmetic, but the spec's literal validation step is inaccurate as written.
2. **Test suite not independently re-executed in this review.** `pytest` was blocked by the review environment's permission mode. I relied on the provided validation output (canaries + doctor PASS) and the executor's reported `6 passed` / ruff-clean, corroborated by static reading of the test file (assertions are concrete and self-consistent). Ralph's `CHECKS_RUN` state owns authoritative test execution.
3. **Feature count vs. test count.** 17 features are implemented and parametrically swept in `test_all_base_ohlcv_features_are_gated_versioned_and_causal`, but the suite is 6 test functions. Coverage of the gating/causality invariant is broad; per-feature numerical assertions exist for the main cases. Adequate for this phase; not a defect.

None of these block merge. Handoff is complete and truthful (explicit staged-file list, validation results with skipped-check reasons, artifact/DAG/README/safety confirmations).

VERDICT: PASS_WITH_WARNINGS
