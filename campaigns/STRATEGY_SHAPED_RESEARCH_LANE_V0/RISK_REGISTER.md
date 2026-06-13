# Risk Register — STRATEGY_SHAPED_RESEARCH_LANE_V0

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| EXPLORATORY output leaks into promotion evidence | HIGH — corrupts the trust boundary | Fail-closed refusal in the trusted/promotion path + a dedicated canary asserting EXPLORATORY artifacts are rejected (P02 done-criterion) | Mitigated by gate |
| A second PnL truth (research drives the reference sim) | HIGH — forbidden by AGENTS.md | CI assert: `research/` has zero import of `backtest`/`management`/`fast_path`; V0 outcomes come only from materialized path labels | Mitigated by check |
| The conditional capability becomes a p-hacking surface (many context×trigger×target knobs) | HIGH — false discovery | Pre-registered VariantLedger/family_budget + BudgetAmendmentRecord; surrogate-FDR zero-pass before any readout; per-factor MDE/power statement; **no grid, fixed geometry, no sequence** in V0 | Mitigated by bound |
| Modifying the single-factor engine breaks truth-chain invariants | HIGH | Conditional template is **added alongside** `SINGLE_FACTOR_THRESHOLD_TEMPLATE`, never modifies it; single-factor path asserted byte-unchanged; full canary + parity suite each phase | Mitigated by design |
| Scope creep into sequence / geometry sweeps / sim-bridge / feature fast lane | MED — overbuild | Explicit OUT-of-scope list (P00 V0_SCOPE.md) + non_goals per phase; those are DEFERRED behind a later trigger | Mitigated by contract |
| Capability built but no idea ever survives (the honest null risk) | MED — sunk cost | Framed as a **capability investment, not an alpha bet**; the de-stack + first-light probes gather cheap evidence; if strategy-shaped probes also null at power, that itself is the signal (the SHAPE is not the gap) | Accepted + instrumented |
| `SetupSpec`/`MechanismCard` duplicates AlphaSpec/StudySpec | MED — duplication | P00 REUSE-MAP locks reuse of the governance spec chain; SetupSpec composes/links existing specs, not re-implements | Mitigated by reuse-map |
| Naming collision with FactorLibrary (= surviving-alpha memory) | LOW | PA substrate named `PA_GRAMMAR_SUBSTRATE_V1`; FactorLibrary name reserved; documented in P04 | Mitigated |
| Committing runs/ or data during evidence phases | MED | `git ls-files runs` check every phase; never_commit anchor; value-free evidence only | Mitigated by check |

## Hard stops (escalate to user, do not auto-proceed)
New paid data; broker/live/order/capital; non-regenerable deletion; committing
raw/canonical/Parquet/SQLite/secrets; weakening a truth-chain invariant; building the
multi-bar sequence encoder or the research→sim bridge (deferred); broad PA library / strategy zoo.
