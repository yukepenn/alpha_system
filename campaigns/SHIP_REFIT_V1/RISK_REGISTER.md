# Risk Register — SHIP_REFIT_V1

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Fast-path diverges from reference diagnostics (silent correctness drift) | HIGH — would corrupt every future verdict | **Hard PARITY GATE**: byte-identical `diagnostic_summary` hashes vs reference on a fixed locked sample (≥10 seeds); fast-path INVALID otherwise. P02 done-criterion. | Mitigated by gate |
| Watchdog false-kills a benign slow provider | MED — spurious phase failures | Detection requires (wall>60s ∧ cpu_delta≈0 ∧ no events growth); a provider with advancing CPU ticks or growing events is never killed; tested with a benign-slow fixture. | Mitigated by design |
| Watchdog fails to detect a real hang | MED — re-pays the 6h cost | Synthetic futex-hang fixture must recover <2 min as a done-criterion; samples `/proc/<pid>/stat` + `events.jsonl`. | Mitigated by test |
| Someone "vectorizes" with numpy/pandas/polars | MED — breaks the pure-Python contract, adds a dependency | Acceptance invariant + a check asserting numpy/pandas/polars stay unimportable; `dependencies=[]` preserved. | Mitigated by check |
| P01 ∥ P02 merge collision | LOW — disjoint footprints (`tools/frontier/*` vs `governance/surrogate_run.py`+`research/**`) | Disjoint `allowed_paths`; serial merge queue; `conflicts_with` set vs P04. | Mitigated |
| Lowering timeout 21600→3600 truncates a legitimately long provider call | LOW — but the watchdog now recovers anyway | 3600s is generous for a single provider turn; the progress-watchdog (not the timeout) is the primary liveness mechanism. | Accept |
| Settler comes back NONZERO mid-flight (gate is interaction-blind) | MED — P03 scope must grow | P03 scope is explicitly **settler-amended by the coordinator before the phase runs**; the interaction detector is the documented expansion path. | Planned |
| Weakening the truth chain while refactoring the surrogate engine | HIGH | Canary all-PASS every phase; surrogate-FDR zero-pass + constant-factor exclusion + `spec_index->seed` mapping are acceptance invariants; the planted_fake_alpha canary is the tripwire. | Mitigated by invariant |
| Scope creep into researcher UX / FactorLibrary / Mining V2 | MED — violates survivor-gate=0 doctrine | Explicit non-goals in GOAL + campaign profile; P04 strictly bounded + non-gating. | Mitigated by contract |
| P04 (non-gating) blocks the campaign | LOW | P04 done-criterion explicitly states the campaign is NOT gated on it; it trails P01–P03. | Mitigated by design |
| Committing runs/ or data debris during ops cleanup (P04) | MED | `git ls-files runs` check every phase; never_commit anchor; explicit staging only. | Mitigated by check |

## Hard stops (escalate to user, do not auto-proceed)

New paid data; broker/live/order/capital scope; deleting non-regenerable local data;
committing raw/canonical/value Parquet or local SQLite; weakening a truth-chain
invariant; a major compass change with capital/live/commercial implications.
