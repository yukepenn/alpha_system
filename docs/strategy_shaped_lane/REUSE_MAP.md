# Strategy-Shaped Research Lane V0 Reuse Map

This map locks what `STRATEGY_SHAPED_RESEARCH_LANE_V0` reuses. It is
documentation only: no source code, engine behavior, data contract, dependency,
or runtime path is changed by `SSRL-P00`.

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

`ACTIVE_CAMPAIGN.md` names `STRATEGY_SHAPED_RESEARCH_LANE_V0`. The coordinator
owns that pointer; this phase confirms it and does not repoint it.

## Reused Engines

The anchors below were re-verified against the current tree on 2026-06-13.
Line ranges are convenience pointers to the checked code; symbols and paths are
the durable reuse contract.

| Surface | Verified current anchor | Reuse lock |
| --- | --- | --- |
| Path-outcome diagnostics dispatch | `src/alpha_system/research/diagnostics.py:450-458` wires the existing `events` diagnostics block, including `target_before_stop_probability` and `post_event_mfe_mae`. | Later SSRL probes must consume the existing path-outcome diagnostics surface, not add a second path-outcome diagnostics engine. |
| Path-label optional fields in diagnostic rows | `src/alpha_system/research/diagnostics.py:940-970` maps optional governed labels into MFE, MAE, target-before-stop, stop-before-target, and liquidity fields; `src/alpha_system/research/diagnostics.py:973-991` performs the same mapping for supplied label values. | V0 outcomes come through materialized path-label fields already understood by the diagnostics panel. |
| Current context==trigger collapse | `src/alpha_system/research/diagnostics.py:1039-1053` builds an observation from one factor/label pair and sets both `regime_filter` and `event_trigger` from the same numeric factor predicate. | The V0 capability target is to add a bounded context!=trigger path later without rewriting this existing observation path in P00. |
| Single-factor strategy template | `src/alpha_system/strategies/templates.py:25` declares `SINGLE_FACTOR_THRESHOLD_TEMPLATE`; `src/alpha_system/strategies/templates.py:28-71` builds the one-factor template; `src/alpha_system/strategies/templates.py:74-151` evaluates and guards it as exactly one declared factor dependency. | Later strategy-shaped work adds alongside the single-factor template. It must not modify, weaken, or duplicate the single-factor path. |
| StudySpec governance chain | `src/alpha_system/governance/study_spec.py:31-65` declares fields and states; `src/alpha_system/governance/study_spec.py:127-181` defines the typed record; `src/alpha_system/governance/study_spec.py:184-229` creates validated records and deterministic IDs; `src/alpha_system/governance/study_spec.py:232-360` validates and gates diagnostics. | `SetupSpec` and `MechanismCard` compose/link the existing spec chain. They do not duplicate `AlphaSpec` or `StudySpec`. |
| Shared governance conventions | `src/alpha_system/governance/ids.py:24-69` reserves governance ID kinds and prefixes, including `MechanismCard` and `SetupSpec`; `src/alpha_system/governance/ids.py:114-144` generates deterministic IDs; `src/alpha_system/governance/serialization.py:43-90` provides canonical serialization and hashing; `src/alpha_system/governance/validation.py:52-173` provides fail-closed validation primitives. | New V0 contract objects reuse the existing identity, serialization, and validation conventions instead of creating parallel conventions. |
| Variant ledger and family budget | `src/alpha_system/governance/variant_ledger.py:47-89` declares record/amendment schemas; `src/alpha_system/governance/variant_ledger.py:126-209` defines records and budget amendments; `src/alpha_system/governance/variant_ledger.py:212-281` defines family-budget and validation-result metadata; `src/alpha_system/governance/variant_ledger.py:684-823` enforces variant and family budgets fail-closed. | Strategy-shaped exploratory variants are bounded through the existing `VariantLedger` and family-budget machinery. No parallel ledger is introduced. |
| Rejected-idea ledger | `src/alpha_system/governance/rejected_idea.py:97-139` declares closed rejection categories, including duplicate, weak evidence, leakage, cost, failed diagnostics, and out-of-scope; `src/alpha_system/governance/rejected_idea.py:142-192` defines `RejectedIdeaRecord`; `src/alpha_system/governance/rejected_idea.py:238-391` provides append-only ledger operations. | Rejected, duplicate, leaky, weak, or out-of-scope exploratory setups reuse the existing research graveyard model. |
| Surrogate-FDR zero-pass gate | `src/alpha_system/governance/surrogate_run.py:780-891` calibrates surrogate runs; `src/alpha_system/governance/surrogate_run.py:894-917` aggregates rows and returns `ZERO_PASS_MET` only when no statistic passes and no calibration error blocks the report. | V0 keeps surrogate-FDR as an existing governance gate and does not add a separate multiple-testing engine. |
| Detection power helpers | `src/alpha_system/runtime/diagnostics/power.py:21-40` estimates IC standard error and minimum detectable absolute IC; `src/alpha_system/runtime/diagnostics/power.py:43-109` builds value-free stacked and per-factor power reports; `src/alpha_system/governance/detection_statistic.py:57-86` attaches those reports to the diagnostic-layer detection statistic. | Per-factor MDE/power statements reuse the existing helper shape. |
| Path-label family exports | `src/alpha_system/labels/families/path/__init__.py:3-29` exports the path label family API. | V0 binds to the existing path label family and does not create a new outcome family. |
| Path-label definitions | `src/alpha_system/labels/families/path/family.py:47-54` declares MFE, MAE, target-before-stop, and triple-barrier labels; `src/alpha_system/labels/families/path/family.py:126-222` exposes supported labels and binds definitions to governed `LabelSpec` records. | V0 path outcomes are governed label outcomes only. |
| Path-label computation | `src/alpha_system/labels/families/path/family.py:244-284` computes path label records; `src/alpha_system/labels/families/path/family.py:287-351` resolves MFE, MAE, target-before-stop, and triple-barrier outcomes; `src/alpha_system/labels/families/path/family.py:354-383` guards path windows; `src/alpha_system/labels/families/path/family.py:466-494` emits records with `label_available_ts`. | V0 does not implement target/stop simulation, a geometry sweep engine, or a research-to-reference-sim bridge; it consumes these label values. |

## Non-Reimplementation Rules

- Do not rebuild path labels, path-outcome diagnostics, the governance spec
  chain, the variant ledger, the rejected-idea ledger, or the single-factor
  template.
- Do not rebuild surrogate-FDR or detection-power reporting.
- Do not create a second PnL or value-accounting truth.
- Do not add a research-to-reference-sim bridge.
- Do not modify `SINGLE_FACTOR_THRESHOLD_TEMPLATE`; later templates must be
  additive.
- Do not introduce a new runtime dependency, new paid data, live/paper/broker
  workflow, order routing, deployment behavior, or promotion evidence.
