I have enough to complete the review. I could not re-run pytest in this review shell (commands required approval), but I verified the code statically, confirmed all referenced runtime modules exist, the working tree matches the allowed-path set exactly, and the harness validation (canaries + frontier-doctor) passed.

# Claude Opus Review — RT-P18: Runtime CLI / Tool Surface

**Campaign:** `ALPHA_RESEARCH_RUNTIME_MVP` · **Lane:** YELLOW · **Reviewer:** Claude Opus 4.8 xhigh

## Scope compliance

- **CLI is additive.** `src/alpha_system/cli/main.py:18` imports `register_subparser as register_runtime_subparser` and `:45` calls it inside `build_parser()` alongside the existing `register_*_subparser` calls. No existing group is removed, reordered semantically, or weakened. `test_runtime_registration_is_additive` asserts all 13 prior groups plus `runtime` remain present.
- **Orchestration, not duplication.** Every handler in `runtime.py` lazily imports an existing `alpha_system.runtime.*` entry point (`entry_contract`, `input_resolver`, `contracts.plan`, `diagnostics.*`, `probe`, `cost`, `evidence`, `handoff`, `decisions`) and dispatches to it. I confirmed all referenced modules exist under `src/alpha_system/runtime/`. No diagnostics math, cost model, grid, audit, evidence/handoff, or decision semantics are re-implemented in the CLI — it parses JSON envelopes, rebuilds value-free contract objects via the existing constructors, and renders compact summaries.
- **All 11 sanctioned subcommands** are registered exactly as specified (`plan`, `validate-inputs`, `run-diagnostics`, `run-label-diagnostics`, `run-signal-probe`, `run-cost-stress`, `build-evidence-draft`, `build-reference-handoff`, `summarize`, `inspect`, `replay-summary`), each with `--input`, `--json`, and `--help`.

## Safety boundary

- **CI-safe / local-only.** Runtime imports are deferred inside handlers, so `--help` and missing-input paths dispatch no runtime work (`test_help_does_not_dispatch_handlers`, `test_runtime_subcommands_fail_cleanly_when_input_is_missing`). `_load_mapping` fails closed with exit 2 on missing `--input`. No network, provider, broker, live/paper, order-router, daemon, or scheduler surface is introduced or reachable.
- **No prohibited MVP states.** Output renders only underlying contract `status`/`state` values (e.g., `INPUTS_RESOLVED`, `BLOCKED`) and decision states coerced through the existing `coerce_runtime_decision_state`. None of `ALPHA_VALIDATED`/`TRADABLE`/`PROFITABLE`/etc. are reachable or printed. `_command_payload` hard-codes `local_only: true`, `provider_or_broker_action: false`.
- **No-claims posture.** `docs/research_runtime/CLI.md` and the README snapshot explicitly state no alpha/tradability/profitability/strategy/portfolio/promotion claim and no provider/network call. Help text and command summaries are descriptive only.

## Artifact policy

- Working tree contains **only** the allowed paths: `cli/runtime.py`, `cli/main.py` (additive edit), `tests/unit/cli/test_runtime.py`, `docs/research_runtime/CLI.md`, `README.md`, and the commit-eligible handoff. No `reviews/` artifact was authored by the executor (correct — reviewer-owned).
- `git ls-files runs` is **empty**; no `runs/` path is staged or tracked. No heavy/DB/log/parquet/dbn/zst artifacts. Canary suite passed all 16 checks including `forbidden_boundary_import`, `forbidden_scope_drift`, `forbidden_local_artifacts`, and `forbidden_raw_data_commit`. `frontier-doctor` passed.
- No PR, merge, `verdict.json`, or `review.md` created by the executor; no test weakening (only a new test file added). Staging is left to Ralph per the explicit-path list in the handoff.

## README snapshot

Factual and compact: updates progress to 19/27 (RT-P18 of `RT-P00..RT-P18`), names the new module/commands/doc, advances active→next to RT-P19, and restates unchanged safety boundaries. No run details, local artifact paths, or claims added. Within §7 policy.

## Notes / minor caveats (non-blocking)

- **Test suite not independently re-run in this review shell** (pytest required interactive approval here). I relied on the executor's reported results (`28 passed`, sibling `41 passed`), the harness canary/doctor validation, and a full static read of the implementation and tests, which are internally consistent. Recommend Ralph's `CHECKS_RUN` gate be the authoritative test execution before merge.
- `inspect` echoes the full user-supplied contract payload back (`runtime.py:445-449`). This is bounded to the operator's own local, value-free contract JSON and is explicitly documented in `CLI.md`; it surfaces no committed or provider data. Acceptable for a local-only inspection command.
- Handoff transparently records the executor-shell `PYTHONPATH=src` caveat for the bare import/help commands and the absent run-local spec (inline spec used as authority) — honest, no hidden failures.

## Done-criteria check

All §9 criteria are met: clean import and additive `runtime --help`; additive registration verified by test; local-only/CI-safe; tests cover import/help/registration/CI-safety/fail-closed/dispatch; `CLI.md` present with no-claims language; README updated per §7; handoff complete; artifact audit clean. No scope drift, no broker/live/paper surface, no test weakening, no unsupported claims.

VERDICT: PASS
