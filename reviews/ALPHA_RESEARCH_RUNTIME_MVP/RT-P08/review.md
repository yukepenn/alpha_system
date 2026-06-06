I have sufficient evidence from direct repository inspection. The pytest re-run needs approval and the provided validation output already confirms canaries and frontier-doctor pass; I'll rely on that rather than retry. Here is my review.

---

# Claude Opus Review — RT-P08 — Label Diagnostics Runtime

**Campaign:** `ALPHA_RESEARCH_RUNTIME_MVP` · **Lane:** YELLOW · **Dep:** RT-P06 · **Merge group:** `diagnostics` (Wave 1, `parallel_safe`)
**Commit reviewed:** `610942c` — "repair label diagnostics scope"

## What this phase is

A bounded **repair** of RT-P08. The prior Claude review returned **REWORK** for finding **B1**: the executor had edited the repo-root `README.md`, which is **not** in RT-P08's authoritative `campaign.yaml` `allowed_paths` and created a global-file race for a `parallel_safe` diagnostics-wave phase. This repair removes the README edit and re-commits the in-scope deliverables.

## Verification performed (against actual repository, not just the summary)

| Check | Result |
|---|---|
| Working tree clean; `README.md` diff vs HEAD | ✅ clean; **no README diff** — B1 correctly resolved |
| `README.md` in RT-P08 `allowed_paths`? | ✅ Confirmed **NOT** present (campaign.yaml L1287–1293) — REWORK was correct, repair is correct |
| Committed file set (7 files) ⊆ `allowed_paths` | ✅ all under `runtime/diagnostics/label/**`, `tests/unit/runtime/diagnostics/label/**`, `docs/.../label.md`, `configs/runtime/diagnostics/label/**`, `handoffs/.../RT-P08.md` |
| `git ls-files runs` | ✅ empty (0 tracked) |
| Forbidden paths / heavy artifacts / `review.md` / `verdict.json` in commit | ✅ none staged or committed |
| Orchestrates `research.*`, no duplicated diagnostic math | ✅ delegates MFE/MAE → `post_event_mfe_mae`, path-ambiguity → `target_before_stop_probability`, label audit → `build_feature_label_diagnostics` |
| `label_available_ts` discipline / leakage fail-closed | ✅ missing ts → `leakage_risk`; ts precedes event/horizon_end → `leakage_risk`; label-as-live-feature reference → `leakage_risk`; leakage → terminal `REJECTED` (visible) |
| Failed/inconclusive runs stay visible | ✅ `_status_from_reasons` maps to `REJECTED` / `DIAGNOSTICS_FAILED` / `INCONCLUSIVE`, never silently passes |
| Test weakening (skip/xfail/tamper) | ✅ none; 5 tests, 34 asserts, covering rejection + leakage + low-sample + fail-closed-cost paths |
| Promotional / alpha-validation language | ✅ none; all matches are anti-promotional disclaimers ("not a promotion decision") |
| No spec/study binding bypass; accepted-DatasetVersion only; no raw provider/broker/live/paper | ✅ consumes `RuntimeInputPack` + `ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES`; no provider/broker imports |
| Canaries / frontier-doctor (validation output) | ✅ all 17 canaries PASS; doctor PASS |
| No PR/merge/push/review/verdict by executor | ✅ confirmed (Ralph owns those gates) |

## Findings

**B1 (prior blocker) — RESOLVED.** The out-of-contract `README.md` edit is fully removed; `README.md` matches HEAD with no diff. The handoff documents the repair and corrected staging list. The spec generator's "README Snapshot Policy" was itself the error — it contradicted the authoritative `allowed_paths` for a `parallel_safe` phase; honoring the campaign contract over the spec narrative was the right call.

### Warnings (non-blocking)

- **W1 — Full suite is red (out-of-scope).** `python tools/verify.py --all` reports `13 failed, 2243 passed`. The failures are entirely in `tests/test_github_utils.py` and `tests/test_ralph_driver.py` — Workflow 2 GitHub/Ralph driver harness tests that require provider/GitHub wiring (scaffolded per AGENTS.md) and cannot be affected by an isolated `runtime/diagnostics/label` subpackage. They pre-date this phase. **Documented**, lane-required narrow checks (targeted pytest `5 passed`, smoke, import, canaries) pass. Flagging so the red `--all` is not silently inherited as "green" at the merge gate.
- **W2 — Some descriptive aggregation is local.** Distribution / class-balance / horizon-coverage / cost-sanity summaries are computed in-module (Counter-based histograms), not via a `research.*` primitive. This is report **assembly** of trivial descriptive counts, not re-derivation of a research diagnostic algorithm, so it does not violate the "consume, never duplicate" rule — but it's the one area where a future drift toward re-implementing research math could start. Worth keeping an eye on in RT-P09/P10 siblings for consistency.

## Lane / safety / artifact posture

No broker/live/paper/order scope, no destructive ops, no deployment, no auto-merge or PR performed. Artifact policy clean (no `runs/`, no heavy/data/DB artifacts, explicit staging). DAG parallel-safety preserved (disjoint `allowed_paths`, no `ACTIVE_CAMPAIGN.md` write, README race removed). No unsupported claims; descriptive no-promotion posture enforced in code, tests, docs, and configs.

The phase is correct, in-scope, leakage-safe, and policy-compliant. The two warnings are a pre-existing unrelated red suite and a minor orchestration-boundary observation — neither blocks merge through the serial queue.

VERDICT: PASS_WITH_WARNINGS
