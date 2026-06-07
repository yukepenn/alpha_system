I now have enough to render a verdict. The `diagnostics_runner.py` (from prior phase AGENT-P13) references `RuntimeToolResult`/`RuntimeRunSummary` as type refs and also imports `cli.runtime` — a pre-existing condition outside P21's allowed paths.

Note: I could not independently execute `pytest`/`verify.py --smoke` in this review sandbox (blocked by permission mode), so I verified all 10 tests by static tracing against the actual contracts; the canary suite and frontier-doctor did run and passed.

---

# Claude Review — AGENT-P21: Runtime Tool Integration Bridge

**Lane:** YELLOW · **Reviewer:** Claude Opus 4.8 (fresh) · **Verdict basis:** spec §1–§15, AGENTS.md, CLAUDE.md, campaign `forbidden_paths`, on-disk artifacts.

## What was verified

**Scope & deliverables (all present, all within Allowed Paths §5):**
- `src/alpha_system/agent_factory/runtime_bridge.py` — the single runtime→agent adapter.
- `tests/unit/agent_factory/test_runtime_bridge.py` — 10 tests covering all §7 requirements.
- `docs/agent_factory/RUNTIME_BRIDGE.md`, `README.md` snapshot, commit-eligible handoff.
- `git status` shows exactly the 5 allowed files (one modified README, four new). No runtime edits, no `data/**` edits, no `ACTIVE_CAMPAIGN.md` write, `git ls-files runs` empty.

**Boundary & invariant compliance:**
- The bridge **imports** `runtime.tool_results` and `data.foundation.version_registry.resolve_dataset_version` and **never edits** them (`git diff` shows no `src/alpha_system/runtime/**` or `data/**` change). ✔
- Dataset resolution goes **only** through `resolve_dataset_version`; admissible states are exactly `{VERSIONED, READY_FOR_RESEARCH}` (line 22), with fail-closed `BLOCKED` + `next_required_gate=resolve_dataset_version` for not-found / id-mismatch / missing / inadmissible states. ✔
- Every runtime outcome handled defensively (`BLOCKED`/`REJECTED`/`INCONCLUSIVE`→non-success; forward states→`OK`); `cost_summary=None`, empty refs/artifacts/limitations degrade gracefully. ✔
- **Value-free guarantee is genuinely enforced**, not just claimed: the bridge constructs an `AgentToolResult`, whose `__post_init__` runs `_reject_raw_or_heavy_text` / `_reject_raw_object` (AGENT-P05). I traced the §7.5 test — the `"raw bars"` rejection-reason marker triggers `ValueError("rejection_reasons contains a forbidden raw/heavy payload marker")`, satisfying the test's `pytest.raises(... match="forbidden raw/heavy payload marker")`. The bridge carries only ids/refs/short summary strings; no raw bars/BBO/feature/label values, full report objects, or heavy payloads. ✔
- No autonomous agent, no continuous runner, no diagnostics re-implementation, no provider/file readers introduced (grep for `.dbn/.zst/parquet/pyarrow/databento/ib_insync` in the new module is clean). ✔
- No broker/live/paper/order/account scope; no alpha/tradability/profitability/promotion claim. Docs carry explicit no-claims framing (§8 satisfied). ✔

**Test integrity:** All tests are new (no existing test touched/weakened/skipped). `just verify-canaries` passed all 16 canaries including `forbidden_test_tamper`, `forbidden_boundary_import`, `forbidden_scope_drift`, `forbidden_raw_data_commit`. `just frontier-doctor` passed.

**Handoff truthfulness:** Complete and honest — explicit file list, per-command results (including the deliberately recorded bare-`python -c` failure with its `PYTHONPATH=src` resolution), clean artifact audit, and forthright disclosure of the caveat below. A model handoff.

## Warnings (do not block this phase, but require follow-up)

1. **The campaign-level "single runtime-tool-surface importer" invariant (spec §4) is not actually achieved.** `src/alpha_system/agent_factory/roles/diagnostics_runner.py:17` (from prior phase AGENT-P13) already imports `from alpha_system.runtime.tool_results import RuntimeRunSummary, RuntimeToolResult` (used at lines 53–54, 94) and also imports `alpha_system.cli.runtime`. P21 **correctly** did not touch it — that module is outside P21's Allowed Paths, so editing it would be scope drift. The executor disclosed this truthfully. **Recommended follow-up:** a later allowed-path phase should route `diagnostics_runner.py` through this bridge (or the campaign should formally relax §4 to the "single *adapter*" framing the docs already use). Note the P21 docs/README avoid the false literal "only importer" claim — `RUNTIME_BRIDGE.md:11` says "single runtime-output **adapter**," which is accurate — so no unsupported claim was committed.

2. **Independent test execution was not possible in this review environment** (pytest/verify.py blocked by sandbox permission mode). The executor's `10 passed` / smoke-pass claim is credible: I statically traced all 10 tests against the real contracts and each holds, and the canary + doctor suites did execute and passed. A re-run of `python -m pytest tests/unit/agent_factory/test_runtime_bridge.py -q` and `python tools/verify.py --smoke` on the merge gate against fresh `main` is the only residual confirmation needed.

## Merge conditions
- Stage **only** the 5 explicit paths (no `git add .`/`-A`); README resolved against fresh `main` through the serial merge queue (§5.1).
- Re-run pytest + `verify.py --smoke` on the merge gate (warning 2).
- File the §4 reconciliation follow-up (warning 1).

No blockers: no broker/live/paper scope, no destructive op, no hidden failed run, no test weakening, no artifact-policy violation, no unsupported claim, no scope drift.

VERDICT: PASS_WITH_WARNINGS
