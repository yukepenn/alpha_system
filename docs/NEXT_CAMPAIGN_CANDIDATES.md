# Next Campaign Candidates

> For the decided next campaign, check `ACTIVE_CAMPAIGN.md` and
> `python tools/frontier/status_doctor.py` — never this file. The tables below
> are a menu of candidate ideas, not the committed roadmap.

These candidates require separate specs, review, and artifact policies. They
are not implied v0.1 capabilities.

## Research rigor gaps (2026-06-10 legibility audit) — `RESEARCH_RIGOR_V1`

Capability gaps in the statistical-rigor layer, distinct from cleanup. Already
in code: trial ledger + variant budgets (`governance/trial_ledger.py`,
`governance/study_spec.py`), mechanical promotion FSM
(`governance/promotion_gate.py`), unsupported-claims guard
(`governance/claims.py`), walk-forward purge/embargo splits
(`experiments/splits.py`), executable negative-control canaries
(future_shift / permuted_labels / optimistic_fill). Missing:

| Gap | Shape | Guardrails |
| --- | --- | --- |
| Multiple-testing correction | Deflated-Sharpe / SPA-style adjustment computed from existing trial-ledger counts; surfaced in diagnostics; consumed by the promotion gate | No new PnL/value truth; pure post-processing of ledger + reference-engine outputs |
| Sealed holdout | Locked evaluation partition the search path cannot resolve: enforce in `runtime/input_resolver.py` (refuse locked partitions without armed governance metadata), not policy prose | Unlock requires explicit governance metadata + review; unlock events ledgered |
| Planted-fake-alpha end-to-end control | Inject a known-spurious signal through the full study pipeline and assert the promotion gate rejects it (extends canaries from guard-plumbing tests to pipeline-outcome tests) | Runs under the canary gate; failure blocks Yellow/Red merges |
| Crowding/correlation gate | Promotion gate mechanically consumes the existing `research/correlation.py` correlation-to-existing-factors diagnostics (max-correlation threshold) instead of treating them as informational | Threshold lives in code; changes spec-authorized only |
| Decay persistence | Persist per-study decay summaries across runs so degradation is visible across studies, not just within one diagnostic run | Local-only storage; summaries referenced from evidence bundles |

## Historical candidate menu (captured during ALPHA_SYSTEM_V1)

| Candidate | Purpose | Guardrails |
| --- | --- | --- |
| Real-data validation pilot | Validate one documented local dataset contract | No raw data commits; no market claims from exploratory outputs |
| Data quality expansion | Add broader missing/duplicate/outlier diagnostics | Keep generated summaries curated and small |
| Research protocol hardening | Define out-of-sample, walk-forward, and review gates | Prevent alpha/tradability conclusions without review |
| Factor library pilot | Add a small reviewed factor catalog | Keep draft materialization disabled by default |
| Strategy evidence workflow | Standardize candidate-to-strategy evidence bundles | Recommendations remain distinct from approvals |
| Portfolio risk expansion | Add broader constraints and multi-symbol allocation checks | Keep portfolio separate from execution and broker scope |
| Cost/slippage calibration design | Document calibration inputs and assumptions | No venue guarantees or live execution claims |
| Fast-path expansion | Add parity cases before any broader acceleration | Fail closed when parity is absent |
| Registry reporting | Improve local status/audit summaries | SQLite remains local-only and uncommitted |
| L2 replay research design | Specify future event/replay assumptions | No queue/passive-fill/live scope without explicit reviewed authorization |
| AI Agent run governance | Improve failed-run, repair, and source-map workflows | Failed attempts remain visible |
| Release artifact policy | Define any future curated report bundles | Keep raw/heavy/generated artifacts out of git |
