## Claude Opus Review — FLF-P01: Entry Contract and DatasetVersion Consumption

### Scope of review
Verified against AGENTS.md / CLAUDE.md artifact + lane policy, the generated YELLOW spec, the executor output, and the actual repository state. I read the implementation, `__init__`, tests, doc, handoff, and README diff directly, and confirmed the upstream foundation APIs the adapter consumes.

### What was verified independently

**Scope & contract correctness — confirmed.**
- `src/alpha_system/features/consumption.py` is a genuinely thin, read-only adapter. It wraps `version_registry.resolve_dataset_version(...)` and the canonical `from_mapping` loaders only; it reads no files, imports no provider client, and materializes nothing.
- Admissibility is **fail-closed**: `resolve_dataset_version` returns `None` for missing records (confirmed at `version_registry.py:180-182`) → adapter raises `DataFoundationValidationError`. Lifecycle gating delegates to the real `DatasetVersion.require_lifecycle_prerequisites(...)` (signature matches exactly, `datasets.py:2951`).
- Admissible states resolve to the genuine `DATASET_VERSION_ADMISSIBLE_STATES = {"VERSIONED", "READY_FOR_RESEARCH"}` (`datasets.py:132-134`). **No prohibited MVP lifecycle state is reachable** — the prohibited states cannot enter this set.
- Locked-partition use routes through the real `require_governance_metadata_for_locked_partition_use(..., plan=...)` (`datasets.py:3162`); kwarg shape matches. Non-QA locked-partition access without contamination metadata fails closed.
- Databento/IBKR kept distinct: the `AcceptedDatasetVersion` handle binds exactly one provenance line, and `_require_record_data_version` enforces per-record `data_version` match. No merge path exists.

**Boundary / governance — confirmed.** `git status` shows only `README.md` modified plus untracked `features/`, `tests/unit/features/`, the doc, and the handoff. **No governance module touched** (R-022 satisfied — consumed, never duplicated). No broker/live/paper/order/account, strategy/backtest/portfolio, or provider-call scope introduced.

**Artifact policy — confirmed.** `git ls-files runs` is empty. The untracked set matches the spec's Allowed Paths exactly; no `runs/**`, no heavy/DB/data/log artifacts, no `configs/features/**` (correctly omitted — no config values needed). Explicit-staging discipline preserved (executor left everything unstaged for Ralph).

**README & doc — confirmed factual and compact.** README diff is a clean snapshot update: progress (P00 merged, P01 complete, next P02), new durable surface, and *strengthened* safety boundaries ("no raw provider access" added). No alpha/tradability/profitability claims, no broker/live/paper/deployment language, no local-artifact paths. The entry-contract doc accurately describes fail-closed admissibility and partition gating.

**Validation — independent canary suite passed** (`verify-canaries`: all 16 PASS, including `forbidden_scope_drift`, `forbidden_boundary_import`, `forbidden_raw_data_commit`; `frontier-doctor` clean).

### Warnings (non-blocking)
1. **Test run not re-executed by reviewer.** The sandbox declined my attempts to re-run `pytest tests/unit/features` and `tools/verify.py --smoke`. I rely on the executor's reported "9 passed" / smoke-pass. This is consistent with the passing canary suite and with code inspection (tests are well-formed, use synthetic fixtures + monkeypatch, and assert the correct fail-closed paths), and there is **no evidence of a hidden failed run** — but it is an un-reproduced claim, noted for the merge gate to confirm via CI.
2. **Raw-field rejection is enforced indirectly.** "No raw provider fields exposed" relies on the underlying canonical `from_mapping` rejecting unsupported fields (verified by `test_raw_provider_fields_are_rejected...`), not by adapter-level logic. This is appropriate for a thin adapter and is intentional per spec, but worth flagging: the guarantee lives upstream, so later phases must keep passing real canonical mappings rather than bypassing the loaders.

### Blocking checks (all clear)
No broker/live/paper scope · no destructive ops · no hidden failed runs · no test weakening or skip-only changes · no artifact-policy violation · no unsupported alpha/tradability claims · no scope drift · no `ACTIVE_CAMPAIGN.md` write · DAG metadata (run-alone, foundation merge group) correct.

VERDICT: PASS_WITH_WARNINGS
