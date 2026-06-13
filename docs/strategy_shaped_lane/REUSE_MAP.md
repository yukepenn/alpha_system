# Strategy-Shaped Research Lane V0 Reuse Map

This map locks what STRATEGY_SHAPED_RESEARCH_LANE_V0 reuses. The campaign adds
bounded strategy-shaped research contracts and probes around these surfaces; it
does not rebuild them, fork them, or create a second value or PnL truth.

This document is value-free. It makes no alpha, profitability, tradability,
deployment, paper-trading, live-trading, or broker-readiness claim.

## Campaign Bundle

The six-file campaign bundle is present under
`campaigns/STRATEGY_SHAPED_RESEARCH_LANE_V0/`:

- `GOAL.md`
- `PHASE_PLAN.md`
- `campaign.yaml`
- `ACCEPTANCE.md`
- `RISK_REGISTER.md`
- `RUNBOOK.md`

`ACTIVE_CAMPAIGN.md` points at
`campaigns/STRATEGY_SHAPED_RESEARCH_LANE_V0`. The coordinator owns that pointer;
this phase only confirms it.

## Reused Anchors

Anchors below were verified against the current code on 2026-06-13. Symbols are
the durable references; line ranges are convenience pointers and may drift.

| Capability | Verified current anchor | Reuse lock |
| --- | --- | --- |
| Path-outcome diagnostics dispatch | `src/alpha_system/research/diagnostics.py:33-40` imports `target_before_stop_probability` and `post_event_mfe_mae`; `src/alpha_system/research/diagnostics.py:450-458` wires both under the existing `events` diagnostics block. | SSRL probes consume this diagnostics surface. They do not introduce a new diagnostics engine for path outcomes. |
| Path-label optional indexing for diagnostic rows | `src/alpha_system/research/diagnostics.py:940-970` maps governed optional labels into MFE, MAE, target-before-stop, stop-before-target, and liquidity fields. | V0 outcomes come from materialized path labels through the existing diagnostic row model. |
| Path-label relabeling support for diagnostic panels | `src/alpha_system/research/diagnostics.py:973-1005` applies supplied label values for the same optional path-label fields. | Surrogate and relabeling flows reuse this existing path-label value plumbing. |
| Single-factor template path | `src/alpha_system/strategies/templates.py:25` declares `SINGLE_FACTOR_THRESHOLD_TEMPLATE`; `src/alpha_system/strategies/templates.py:28-71` builds the one-factor template; `src/alpha_system/strategies/templates.py:74-138` evaluates it; `src/alpha_system/strategies/templates.py:141-151` enforces exactly one declared factor dependency. | V0 is additive only. Do not weaken or modify the single-factor template semantics. |
| Strategy template additive boundary | Current code also exposes `CONTEXT_TRIGGER_CONDITIONAL_TEMPLATE` at `src/alpha_system/strategies/templates.py:186`, with builder/evaluator/separate-factor guard at `src/alpha_system/strategies/templates.py:190-377`. | This P00 map authorizes no code change. Any strategy-shaped template behavior must remain additive and must not alter the single-factor path. |
| StudySpec contract and deterministic identity | `src/alpha_system/governance/study_spec.py:31-65` declares required fields and states; `src/alpha_system/governance/study_spec.py:127-181` defines the typed record and serialization; `src/alpha_system/governance/study_spec.py:184-215` constructs a validated record; `src/alpha_system/governance/study_spec.py:218-229` generates deterministic IDs. | `SetupSpec`/`MechanismCard` compose with this governance chain rather than duplicate `StudySpec` or `AlphaSpec`. |
| StudySpec validation and diagnostics gate | `src/alpha_system/governance/study_spec.py:232-291` validates the schema fail-closed; `src/alpha_system/governance/study_spec.py:294-322` checks declared variant budgets; `src/alpha_system/governance/study_spec.py:325-360` gates diagnostics on a valid `StudySpec`. | V0 variant accounting and diagnostics admission reuse existing budget and gate semantics. |
| Variant ledger records and budget amendments | `src/alpha_system/governance/variant_ledger.py:47-89` declares record and amendment fields; `src/alpha_system/governance/variant_ledger.py:126-169` defines validated variant records; `src/alpha_system/governance/variant_ledger.py:172-209` defines budget amendments; `src/alpha_system/governance/variant_ledger.py:252-281` defines budget-validation result metadata. | Strategy-shaped exploratory variants are ledgered through the existing ledger model. |
| Variant ledger persistence and budget enforcement | `src/alpha_system/governance/variant_ledger.py:284-340` provides JSONL loading and append setup; `src/alpha_system/governance/variant_ledger.py:429-473` validates ledger records; `src/alpha_system/governance/variant_ledger.py:684-823` enforces variant and family budgets fail-closed. | SSRL does not add a parallel variant ledger. Family-budget checks stay fail-closed and explicit. |
| Rejected idea / research graveyard records | `src/alpha_system/governance/rejected_idea.py:97-139` declares closed reason categories; `src/alpha_system/governance/rejected_idea.py:142-192` defines the typed rejected record; `src/alpha_system/governance/rejected_idea.py:238-391` defines append-only ledger operations; `src/alpha_system/governance/rejected_idea.py:404-520` creates, IDs, and validates rejected records. | Rejected, duplicate, leaky, or weak exploratory setups reuse this graveyard model instead of inventing a second rejection memory. |
| IC detection-power helpers | `src/alpha_system/runtime/diagnostics/power.py:21-40` estimates IC standard error and MDE; `src/alpha_system/runtime/diagnostics/power.py:43-79` builds one power statement; `src/alpha_system/runtime/diagnostics/power.py:81-109` builds stacked and per-factor reports. | Per-factor MDE/power statements for readouts reuse this helper. |
| Detection statistic power integration | `src/alpha_system/governance/detection_statistic.py:57-86` attaches detection-power reporting to the shared diagnostic-layer detection statistic. | V0 readouts reuse the existing value-free power reporting shape. |
| Surrogate-FDR zero-pass machinery | `src/alpha_system/governance/surrogate_run.py:780-891` calibrates surrogate runs; `src/alpha_system/governance/surrogate_run.py:894-917` aggregates rows and returns `ZERO_PASS_MET` only when no statistic passes and no errors block calibration. | V0 keeps surrogate-FDR as an existing governance gate and does not add a separate multiple-testing engine. |
| Path label family exports | `src/alpha_system/labels/families/path/__init__.py:3-29` exports the path label family API. | Later phases bind to the existing path label family rather than creating a new label family. |
| Path label definitions | `src/alpha_system/labels/families/path/family.py:47-54` declares MFE, MAE, target-before-stop, and triple-barrier labels; `src/alpha_system/labels/families/path/family.py:126-140` exposes supported labels and definition building; `src/alpha_system/labels/families/path/family.py:141-222` binds definitions to governed `LabelSpec` records. | V0 path outcomes must remain governed label outcomes. |
| Path label computation and guarded path windows | `src/alpha_system/labels/families/path/family.py:244-284` computes path label records; `src/alpha_system/labels/families/path/family.py:287-351` resolves MFE, MAE, target-before-stop, and triple-barrier outcomes; `src/alpha_system/labels/families/path/family.py:354-383` guards path windows; `src/alpha_system/labels/families/path/family.py:466-494` emits label records with `label_available_ts`. | V0 does not implement target/stop simulation or a research-to-reference-sim bridge; it consumes these path-label values. |

## Explicit Non-Reuse Boundaries

- No source changes in this phase.
- No second diagnostics engine for path outcomes.
- No second PnL or value-accounting truth.
- No research-to-reference-sim bridge.
- No changes to `SINGLE_FACTOR_THRESHOLD_TEMPLATE`.
- No new label family for MFE, MAE, target-before-stop, or triple-barrier.
- No new surrogate-FDR or power-reporting engine.
- No new dependency, new paid data, live trading, paper trading, broker operation,
  order routing, deployment, or production behavior.
