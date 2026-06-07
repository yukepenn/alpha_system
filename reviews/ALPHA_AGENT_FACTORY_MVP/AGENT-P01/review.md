I've reviewed all artifacts directly. Command execution is blocked in this review environment, so I rely on the file contents I read directly plus the provided validation output (frontier-doctor pass; all 16 canaries pass) and the executor's reported run.

---

# Claude Review — AGENT-P01: Agent Factory Entry Contract and Preflight Gates

## Summary

AGENT-P01 implements a **contracts-only** Agent Factory entry contract (`alpha_system.agent_factory.entry_contract`) encoding the four preflight gates with fail-closed semantics and truthful degradation. I read every created file directly: `entry_contract.py`, `__init__.py`, `preflight.toml`, `PREFLIGHT_GATES.md`, the README diff, the unit tests, and the handoff. The implementation is tightly scoped to the spec, introduces no autonomous agent, runner, or loop, and touches no consumed primitive.

## Scope & Contracts-Only Compliance — PASS

- **No agent instantiated, no runner, no loop.** `entry_contract.py` only evaluates declarative flags and checks marker-file *existence*. No `runtime.*` / `governance.*` / `features.*` / `labels.*` / `data.*` import appears anywhere.
- **Four gates present and identified** (`entry_contract.py:43-49`): `SEED_PACKS`, `RUNTIME_REAL_SMOKE`, `FEATURE_LABEL_PARQUET_SINK_V1`, `SESSION_LABEL_GUARD_FIX_V1`. All four are always represented in the result (`evaluate`, lines 278-284).
- **Fails closed** (the core requirement):
  - Runtime smoke `false` → `PREFLIGHT_BLOCKED` (lines 351-362).
  - Malformed/unparseable marker → `BLOCKED` (lines 364-375).
  - Parquet-sink not landed **and** large-scale value-consuming study requested without human approval → `BLOCKED` (lines 405-420).
  - Session-guard not fixed **and** a session-context feature requested → `BLOCKED` (lines 454-466).
- **Truthful degrade, not crash**: absent `ALPHA_DATA_ROOT` or missing registry markers → `PREFLIGHT_WARN` with an explicit `limitations` note (lines 288-338). No exception path.
- **Never reads values**: the seed gate is existence-only and never opens the SQLite files. Notably, the runtime-smoke marker reader **refuses to read** any path with a forbidden raw/heavy suffix (`.dbn/.zst/.parquet/.arrow/.feather`) and fails closed instead (lines 535-541, `FORBIDDEN_MARKER_SOURCE_SUFFIXES`) — a defensive measure beyond what the spec required.
- **Deterministic / injectable**: `AgentFactoryPreflightConfig` allows full input override; no absolute machine path is hard-coded (root resolves via env/config). Default config path is derived relative to the module.

## Value-Free / No-Claims — PASS

- Result `to_dict()` (lines 117-128) emits only gate names, status strings, reasons, scope blockers, and follow-up identifiers — no DB rows, raw data, or provider payloads. The test `test_result_is_structured_and_value_free` asserts the absence of `raw_payload`/`provider_payload`/`db_rows` and of the tmp path.
- `PREFLIGHT_GATES.md` and the README section use no-claims language: explicit statements that entry implies no agent ran, no diagnostic passed, no alpha exists, and never opens raw provider data or external calls. No alpha/tradability/profitability/strategy/paper/live/broker wording.

## Tests — PASS (not weakened)

- 10 hermetic tests on synthetic fixtures using `tmp_path`/monkeypatched `ALPHA_DATA_ROOT`. They assert genuine behavior: all four gates represented, fail-closed on unsatisfied smoke, truthful WARN on absent registries, PASS on all-satisfied, value-free results, both scope blockers, and the forbidden-suffix fail-closed path. No `skip`/`xfail`, no visible test-only branch in source, no assertion relaxation.

## Artifact Policy — PASS

- Executor reports `git ls-files runs` empty; validation canary `forbidden_local_artifacts` and `forbidden_raw_data_commit` both PASS. No `runs/` path appears in the handoff's commit-eligible list.
- Config is `configs/agent_factory/preflight.toml` — value-free, declarative, no secrets/data (spec permitted `.toml`).
- Handoff at `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P01.md` lists exactly the spec's Allowed Paths and nothing else. No `ACTIVE_CAMPAIGN.md` write. No forbidden path created.
- README snapshot is factual and compact; correctly states AGENT-P01 complete, next phase AGENT-P02, boundaries unchanged.

## Handoff Honesty — PASS

The handoff transparently records that the two *bare* `python -c` imports failed (`ModuleNotFoundError`) because the shell lacked `src` on `PYTHONPATH`, and that the same imports passed under `PYTHONPATH=src`, with the scoped pytest suite (10 passed) and `verify.py --smoke` passing. This is a truthful, non-hidden recording of an environment quirk, not a concealed failure.

## Warnings (non-blocking)

1. **Verification limitation (mine):** command execution was blocked in this review environment, so I could not independently re-run the unit tests or `verify.py --smoke`. I relied on the executor's reported run (10 passed) and the provided validation output (frontier-doctor + all 16 canaries PASS). The source I read directly is consistent with those results.
2. **Runtime-smoke gate trusts a static config flag.** `preflight.toml` declares `real_dataset_version_smoke_ran = true` (the smoke was proven by `POST_RUNTIME_FEATURE_LABEL_STORAGE_AND_SEED_PACKS_V1`). This is within spec (Gate 2 explicitly "reads a declared status flag … injectable"), but a hard-coded `true` is only as trustworthy as the human keeping it current; a later phase may want to bind it to an actual recorded marker. Acceptable for this contracts-only foundation phase.

## Conclusion

The phase is on-scope, contracts-only, fail-closed, value-free, with honest handoff and clean artifact posture. No broker/live/paper scope, no destructive operation, no test weakening, no hidden failure, no unsupported claim, no scope drift. The only reservations are my inability to independently execute tests in this environment and a minor note on the static smoke flag — neither warrants rework.

VERDICT: PASS_WITH_WARNINGS
