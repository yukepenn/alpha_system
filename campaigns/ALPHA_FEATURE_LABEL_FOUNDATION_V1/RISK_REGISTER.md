# ALPHA_FEATURE_LABEL_FOUNDATION_V1 Risk Register

## Purpose

This register records the campaign-specific risks for the **Feature/Label Foundation**:
the versioned, no-lookahead-safe research substrate that future AI Alpha Researchers will
consume via `StudySpec` over a `FeatureStore` and `LabelStore` built on **accepted
DatasetVersions**. This campaign is **contract generation and substrate construction only**.
It does **not** implement alpha search, does **not** materialize committed values, does
**not** call Databento/IBKR, and does **not** pull data. Most risks here are therefore about
**substrate integrity, no-lookahead safety, governance reuse, scope discipline, parallel-DAG
correctness, and artifact discipline** — the substrate silently leaking the future, becoming
a dumping ground, duplicating governance, drifting into alpha/strategy claims, or committing
forbidden values — rather than market risk.

A feature is not alpha. A label is not alpha. A `FeatureStore` is not a factor library. A
materialized `FeatureSet` is not a promoted candidate. A good diagnostic is not production
readiness. The register reflects that framing: every "Blocking condition" below is a hard
STOP/merge-block that Ralph must enforce through the serial merge queue, and several map
directly to the `merge_policy.global_blockers` list in `campaign.yaml`.

## Severity Scale

* **S1 Critical** — bakes lookahead/leakage into the substrate, exposes forbidden
  trading/broker/alpha scope, makes an unsupported alpha/tradability claim, or commits
  forbidden raw/canonical/value/DB artifacts; the campaign cannot be accepted.
* **S2 High** — materially weakens a feature/label guard, governance-reuse boundary,
  provenance/availability trail, BBO/no-trade semantics, or parallel-DAG/merge-queue
  invariant.
* **S3 Medium** — local correctness or clarity issue with contained impact.
* **S4 Low** — cosmetic or documentation-only issue.

## Likelihood Scale

* **L1 Rare** — unlikely given current controls.
* **L2 Possible** — plausible without explicit attention.
* **L3 Likely** — expected if not actively prevented.

## Risk Status Values

* **Open** — active and monitored.
* **Mitigated** — controls in place; residual risk accepted.
* **Closed** — no longer applicable.

## Risk Table Summary

| ID | Name | Severity | Likelihood | Blocking? |
| -- | ---- | -------- | ---------- | --------- |
| R-001 | FeatureStore dumping ground | S2 | L3 | No |
| R-002 | Raw provider data bypass | S1 | L2 | Yes |
| R-003 | FeatureRequest bypass | S2 | L2 | Yes |
| R-004 | FeatureSpec too vague | S2 | L2 | No |
| R-005 | Duplicate / equivalent exposure explosion | S2 | L3 | Yes |
| R-006 | available_ts missing or incorrect | S1 | L2 | Yes |
| R-007 | Centered / future window leakage | S1 | L2 | Yes |
| R-008 | Label-as-feature leakage | S1 | L2 | Yes |
| R-009 | label_available_ts missing | S1 | L2 | Yes |
| R-010 | Cost-unaware labels dominate | S2 | L2 | No |
| R-011 | BBO missingness silently filled | S2 | L2 | Yes |
| R-012 | No-trade synthetic rows misused | S2 | L2 | Yes |
| R-013 | Cross-market timestamp misalignment | S2 | L2 | No |
| R-014 | Partition / locked-test contamination | S2 | L2 | Yes |
| R-015 | Feature/label materialization too large or slow | S3 | L2 | No |
| R-016 | Feature/Label docs claim alpha value | S1 | L2 | Yes |
| R-017 | Unsupported alpha / tradability claims | S1 | L2 | Yes |
| R-018 | Tests only cover happy path | S2 | L3 | No |
| R-019 | Raw / heavy data artifacts committed | S1 | L2 | Yes |
| R-020 | Governance gates bypassed | S2 | L2 | Yes |
| R-021 | Agent Factory later cannot consume outputs cleanly | S2 | L2 | No |
| R-022 | Feature/Label object duplication with Governance objects | S2 | L3 | Yes |
| R-023 | Labels tied too tightly to specific strategy wrappers | S2 | L2 | No |
| R-024 | BBO-derived cost labels mis-specified | S2 | L2 | No |
| R-025 | Future Core Alpha Pilot blocked by missing base features/labels | S2 | L2 | No |
| R-026 | DAG scheduler metadata missing or wrong | S2 | L2 | Yes |
| R-027 | Parallel phase path conflict | S2 | L2 | Yes |
| R-028 | ACTIVE_CAMPAIGN.md conflict in parallel wave | S2 | L2 | Yes |
| R-029 | Serial merge queue bypassed | S2 | L1 | Yes |
| R-030 | External provider call introduced by mistake | S1 | L1 | Yes |

---

# Detailed Risk Entries

## R-001 — FeatureStore dumping ground

### Description
Features accumulate in the `FeatureStore`/`FeatureRegistry` without governance, lineage, or
purpose — every convenient transform is added "just in case", with no `FeatureRequest`,
no `FeatureSpec`, no duplicate-exposure check, and no deprecation path. The substrate
degrades into an undisciplined catalog rather than a governed, deduplicated, lineage-traced
research substrate.

### Impact
The substrate loses its purpose as a governed research input: duplicate/near-duplicate
exposures multiply, lineage is incomplete, and future researchers cannot reason about what a
feature means or where it came from. S2.

### Likelihood
L3 — adding "one more feature" is the path of least resistance, so a dumping ground is the
expected outcome unless governance and a deprecation path are actively enforced.

### Detection
* `FeatureRegistry` integration requires every registered feature to bind a `FeatureSpec`,
  `FeatureVersion`, `FeatureLineageRecord`, and an approved `FeatureRequest`.
* Coverage/quality reports surface unregistered or undocumented features; a
  `FeatureDeprecationRecord` path exists for retired features.
* Claude Opus review of FLF-P14 registry semantics and the no-dumping-ground rule.
* `merge_policy.global_blockers`: `FeatureRequest/FeatureSpec/LabelSpec bypassed`.

### Mitigation
`feature_store_dumping_ground_forbidden: true`; every feature traces to an approved
`FeatureRequest` + validated `FeatureSpec` + `FeatureVersion` + lineage; duplicate/equivalent
exposure is recorded; a `FeatureDeprecationRecord` path retires features rather than letting
them accumulate; values stay local-only.

### Owner
Codex (registry/lineage + deprecation path) / Claude Opus (no-dumping-ground review).

### Related Phases
FLF-P05, FLF-P06, FLF-P14, FLF-P15.

### Blocking Condition
A feature is registered without a bound `FeatureSpec`/`FeatureVersion`/lineage and an
approved `FeatureRequest`, or duplicate exposure is allowed without a record.

---

## R-002 — Raw provider data bypass

### Description
Feature or label code reads raw provider files directly (`.dbn`, `.zst`, parquet, arrow,
feather, or any provider response) instead of consuming an **accepted DatasetVersion** through
the sanctioned `resolve_dataset_version` + canonical-record loaders. The no-lookahead and
admissibility guarantees that ride on canonical records are bypassed entirely.

### Impact
The single sanctioned consumption boundary is broken: the substrate consumes data that has
not passed quality/coverage/admissibility gating and that may carry provider artifacts and
lookahead, corrupting every downstream feature and label. S1.

### Likelihood
L2 — raw provider files are local and convenient, so a shortcut into them is plausible
without an explicit forbidden-path guard and import audit.

### Detection
* `import alpha_system.features.consumption` is the only consumption entry; tests assert no
  feature/label module imports a provider reader or opens `.dbn`/`.zst`/parquet/arrow/feather.
* Forbidden-path globs in every phase (`data/raw/**`, `data/canonical/**`, `**/*.dbn`,
  `**/*.zst`, `**/*.parquet`, `**/*.arrow`, `**/*.feather`).
* `merge_policy.global_blockers`: `raw provider data read by feature/label code` and
  `accepted DatasetVersion bypassed`.
* Claude Opus review of FLF-P01 consumption adapter and FLF-P03 input views.

### Mitigation
`raw_provider_access_forbidden: true`; the only sanctioned consumption API is
`alpha_system.data.foundation.version_registry.resolve_dataset_version` plus
`CanonicalBarRecord`/`CanonicalBBORecord`/`DenseGridBarRecord` `from_mapping` loaders;
admissibility limited to `{VERSIONED, READY_FOR_RESEARCH}`; reading provider files from
feature/label code is fail-closed and merge-blocking.

### Owner
Codex (consumption adapter + import guards) / Claude Opus (boundary review).

### Related Phases
FLF-P01, FLF-P03, FLF-P08, FLF-P09.

### Blocking Condition
Any feature/label code reads a raw provider file or bypasses an accepted DatasetVersion.

---

## R-003 — FeatureRequest bypass

### Description
A feature is implemented or materialized without an approved governance `FeatureRequest`
(`freq_`), skipping the request gate, the `approval_status` check, and the
duplicate/equivalent-exposure assessment.

### Impact
Features enter the substrate ungoverned, defeating the request-gate the campaign installs and
re-opening the path to a feature factory with no duplicate-exposure discipline. S2.

### Likelihood
L2 — wiring the gate is easy to forget for a "small" feature, and a single bypass normalizes
the rest.

### Detection
* FLF-P05 request gate asserts: no `FeatureRequest` (`freq_`) with `approval_status: APPROVED`
  → no feature implementation; `PENDING`/`NEEDS_REVIEW`/`BLOCKED_DUPLICATE` fail closed.
* Family phases (FLF-P08..P12) register each feature through the gate; tests prove
  fail-closed behavior when the request is absent or unapproved.
* `merge_policy.global_blockers`: `FeatureRequest/FeatureSpec/LabelSpec bypassed`.
* Claude Opus review that the gate consumes governance and is not re-implemented.

### Mitigation
`feature_request_required: true`; `consumes_governance_feature_request: true`; the request
gate adapts `alpha_system.governance.feature_request.FeatureRequest` and the duplicate-exposure
guard; no approved `FeatureRequest` means no implementation, enforced fail-closed.

### Owner
Codex (request gate + family registration) / Claude Opus (gate-reuse review).

### Related Phases
FLF-P05, FLF-P08, FLF-P09, FLF-P10, FLF-P11, FLF-P12.

### Blocking Condition
A feature is implemented or materialized without an approved governance `FeatureRequest`.

---

## R-004 — FeatureSpec too vague

### Description
A `FeatureSpec` underspecifies its inputs, transform, window, normalization, availability
assumptions, or `available_ts` derivation, so the feature is not reproducible and its
no-lookahead status cannot be audited.

### Impact
Features cannot be reproduced or leakage-audited from their spec; lineage is nominal but not
meaningful, weakening the substrate's reproducibility guarantee. S2.

### Likelihood
L2 — spec fields are easy to fill in loosely without a completeness check.

### Detection
* FLF-P06 `FeatureSpec`/`FeatureVersion` contracts require `FeatureInputSpec`, `TransformSpec`,
  `WindowSpec`, `NormalizationSpec`, availability assumptions, and an `available_ts` rule; a
  deterministic `FeatureVersion` id binds them.
* Contract tests reject specs missing required fields; family specs are validated before
  `IMPLEMENTATION_ALLOWED`.
* Claude Opus review of FLF-P06 contract completeness and FLF-P08..P12 family specs.

### Mitigation
`feature_spec_required: true`; immutable, hashable `FeatureSpec` with mandatory
input/transform/window/normalization fields and an explicit `available_ts` derivation; the
lifecycle gates `SPEC_VALIDATED` before `IMPLEMENTATION_ALLOWED`.

### Owner
Codex (FeatureSpec contracts + validation) / Claude Opus (spec-completeness review).

### Related Phases
FLF-P06, FLF-P07, FLF-P08.

### Blocking Condition
A feature is implemented from a `FeatureSpec` missing required input/transform/window/
normalization or `available_ts` fields.

---

## R-005 — Duplicate / equivalent exposure explosion

### Description
Many features encode the same underlying exposure (e.g. several near-identical momentum or
spread transforms) without being recognized as duplicates/equivalents, inflating the catalog
and biasing any future low-correlation selection.

### Impact
The substrate accumulates redundant exposures that masquerade as distinct features,
undermining the low-correlation framing future research depends on and re-creating a factor
zoo. S2.

### Likelihood
L3 — equivalent transforms are easy to introduce independently across five parallel feature
families unless a guard records them.

### Detection
* FLF-P05 duplicate-exposure guard (consuming `alpha_system.governance.duplicate_exposure`)
  produces a `DuplicateExposureReport` and `EquivalentFeatureGroup` views; `BLOCKED_DUPLICATE`
  requests fail closed.
* FLF-P15 quality/coverage reports surface equivalent-feature groups across families.
* `merge_policy.global_blockers`: `duplicate exposure allowed without record`.
* Claude Opus review across the parallel feature families.

### Mitigation
`duplicate_exposure_check_required: true`; every `FeatureRequest` runs the governance
duplicate/equivalent-exposure guard; equivalents are grouped and recorded rather than silently
admitted; cross-family duplicates are reported at integration.

### Owner
Codex (duplicate-exposure views + reports) / Claude Opus (cross-family exposure review).

### Related Phases
FLF-P05, FLF-P08, FLF-P09, FLF-P10, FLF-P11, FLF-P12, FLF-P15.

### Blocking Condition
A duplicate/equivalent exposure is admitted without a recorded `DuplicateExposureReport`
entry.

---

## R-006 — available_ts missing or incorrect

### Description
A feature value omits `available_ts`, or `available_ts` reflects when the input was ingested
rather than when the completed bar/quote became usable in research/backtest semantics
(`available_ts >= bar_end_ts`, distinct from `ingested_at`).

### Impact
Lookahead is baked into the feature layer: a value appears usable before its inputs were
actually available, invalidating any point-in-time study built on the substrate. S1.

### Likelihood
L2 — timestamp conflation (`event_ts`/`bar_end_ts`/`available_ts`/`ingested_at`) is a subtle,
classic source of leakage.

### Detection
* FLF-P03 input views key strictly off `available_ts` and expose the five distinct timestamps;
  no-lookahead tests assert usability never keys off `event_ts`/`ingested_at`.
* FLF-P06 contracts require `available_ts` on every `FeatureValueRecord`.
* `merge_policy.global_blockers`: `feature without available_ts`.
* Claude Opus review of timestamp semantics in FLF-P03/FLF-P06/FLF-P07.

### Mitigation
`available_ts_required: true`; input views and contracts make `available_ts` mandatory and
derived from `bar_end_ts`/quote availability, never from `ingested_at`; no-lookahead test
suite under `tests/no_lookahead/feature_label/` fails closed.

### Owner
Codex (available_ts wiring + no-lookahead tests) / Claude Opus (timestamp/leakage review).

### Related Phases
FLF-P03, FLF-P06, FLF-P07, FLF-P15.

### Blocking Condition
Any feature value lacks `available_ts` or derives it from `ingested_at`/`event_ts` rather
than bar/quote availability.

---

## R-007 — Centered / future window leakage

### Description
A live feature uses a centered or forward-looking rolling window (a window that peeks at
future bars), so the feature value at time *t* depends on data only available after *t*.

### Impact
Future information leaks into live features, producing inflated, non-reproducible research
signals — the most direct form of lookahead in the feature layer. S1.

### Likelihood
L2 — centered windows are a common, convenient default in time-series code and easy to apply
without realizing they peek forward.

### Detection
* FLF-P07 primitives make centered/future windows **offline-only** and unavailable to live
  feature contracts; causal-window tests prove no forward peeking.
* FLF-P06 contracts forbid future/centered windows for live features at the contract level.
* `merge_policy.global_blockers`: `future/centered rolling window used as live feature`.
* Claude Opus review of primitive causality and family window usage.

### Mitigation
`no_future_window_features: true`; `no_centered_live_windows: true`; primitives default to
causal windows keyed off `available_ts`; centered/future windows are restricted to offline
label/diagnostic use and blocked from live-feature contracts.

### Owner
Codex (causal primitives + contract guard) / Claude Opus (window-causality review).

### Related Phases
FLF-P06, FLF-P07, FLF-P08, FLF-P12.

### Blocking Condition
A live feature uses a centered or future-looking window.

---

## R-008 — Label-as-feature leakage

### Description
A label value (which legitimately uses future data) is exposed as, or reused as, a live
feature input, leaking the future outcome the label encodes into the feature space.

### Impact
The label's forward-looking information contaminates features, fabricating predictive power
and invalidating any study — a leakage-factory failure mode. S1.

### Likelihood
L2 — labels and features share primitives and input views, so accidentally feeding a label
into a feature is plausible without an explicit forbidden-overlap guard.

### Detection
* FLF-P16 `LabelSpec` carries `forbidden_feature_overlap` and `leakage_checks`
  (`label_as_feature`); the governance `label_leakage_guard` is consumed.
* FLF-P23 leakage/availability audits assert no label series is reachable as a live feature.
* `merge_policy.global_blockers`: `label values exposed as live features`.
* Claude Opus review of the feature/label boundary in FLF-P16/FLF-P23.

### Mitigation
`label_as_feature_forbidden: true`; `future_data_allowed_only_for_labels: true`; `LabelSpec`
records `forbidden_feature_overlap`; the governance `label_leakage_guard` enforces the
`label_as_feature` check; leakage audits fail closed.

### Owner
Codex (forbidden-overlap + leakage audits) / Claude Opus (feature/label boundary review).

### Related Phases
FLF-P16, FLF-P17, FLF-P23.

### Blocking Condition
Any label value is exposed or reused as a live feature input.

---

## R-009 — label_available_ts missing

### Description
A label value omits `label_available_ts` (the time at which the label's forward outcome is
actually known and usable), so a label can be joined to features before its horizon has
elapsed.

### Impact
Labels become usable before their outcome is determined, leaking the future into any
feature/label join and invalidating training/validation splits. S1.

### Likelihood
L2 — `label_available_ts` is easy to omit because the label's value computation completes
offline over the full series.

### Detection
* FLF-P16 contracts require `label_available_ts` (derived from horizon/path rules +
  availability time) on every `LabelValueRecord`.
* FLF-P23 availability audits assert `label_available_ts >= availability_time` and that joins
  respect it.
* `merge_policy.global_blockers`: `label without label_available_ts`.
* Claude Opus review of label availability semantics.

### Mitigation
`label_available_ts_required: true`; `LabelSpec`/`LabelAvailabilityPolicy` derive
`label_available_ts` from `horizon` + `path_rules` + `availability_time`; availability audits
fail closed when it is missing or inconsistent.

### Owner
Codex (label availability wiring + audits) / Claude Opus (availability review).

### Related Phases
FLF-P16, FLF-P21, FLF-P23.

### Blocking Condition
Any label value lacks `label_available_ts` or sets it earlier than its availability time.

---

## R-010 — Cost-unaware labels dominate

### Description
The label families are dominated by raw forward-return labels with no cost-/spread-adjusted
counterparts, so the substrate steers future research toward a cost-unaware backtest factory.

### Impact
Future studies inherit a label set that ignores transaction costs and spread, biasing
research toward signals that look profitable only before costs — a cost-unaware backtest
factory failure mode. S2.

### Likelihood
L2 — raw forward returns are the simplest labels and tend to dominate unless cost-adjusted
labels are explicitly required.

### Detection
* FLF-P18 provides cost-adjusted/spread-adjusted forward-return labels with a `CostAdjustmentSpec`
  and `cost_model` from the governance `LabelSpec`.
* Label coverage report (FLF-P22/FLF-P24) shows cost-adjusted labels exist alongside raw ones.
* Claude Opus review that cost-adjusted labels are first-class, not an afterthought.

### Mitigation
`cost_adjusted_labels_required: true`; FLF-P18 supplies `cost_adjusted_fwd_ret` /
`spread_adjusted_fwd_ret` using BBO spread fields and the `LabelSpec` cost model; cost-aware
labels are required alongside raw forward returns. (No tradability/profitability claim is made
— these are descriptive labels only.)

### Owner
Codex (cost-adjusted label family) / Claude Opus (cost-coverage review).

### Related Phases
FLF-P18, FLF-P22, FLF-P24.

### Blocking Condition
None on its own (S2, non-blocking); flagged in label coverage review when cost-adjusted labels
are absent.

---

## R-011 — BBO missingness silently filled

### Description
Missing or abnormal BBO quotes are silently forward-filled or interpolated instead of being
flagged with the `missing_bbo` / `bbo_quarantined` quality-flag tokens, so a synthetic quote
is treated as a real, executable quote.

### Impact
Spread/microprice/imbalance features and BBO-derived cost labels are computed over fabricated
quotes, corrupting tradability-related features and cost-adjusted labels. S2.

### Likelihood
L2 — forward-fill is a common default for missing series and is easy to apply without
realizing it manufactures quotes.

### Detection
* FLF-P04 semantics encode BBO missingness via `missing_bbo` / `bbo_quarantined` tokens with
  no silent forward-fill; predicates exclude/flag missing-BBO rows.
* FLF-P09 BBO families consume the flags; tests assert no fabricated quotes.
* `merge_policy.global_blockers`: `missing BBO silently forward-filled`.
* Claude Opus review of FLF-P04/FLF-P09 missingness handling.

### Mitigation
`no_silent_forward_fill: true`; `missing_bbo_flag_required: true`; missing/abnormal quotes are
flagged with `missing_bbo` (missing/bad-quote) and `bbo_quarantined` (crossed/abnormal,
non-blocking); microprice requires valid bid/ask sizes; no forward-fill.

### Owner
Codex (BBO missingness semantics + BBO families) / Claude Opus (BBO-missingness review).

### Related Phases
FLF-P04, FLF-P09, FLF-P18.

### Blocking Condition
Missing/abnormal BBO is silently forward-filled or otherwise treated as a real quote without
a `missing_bbo`/`bbo_quarantined` flag.

---

## R-012 — No-trade synthetic rows misused

### Description
Dense-grid synthetic no-trade rows (`has_trade=False`, `synthetic=True`,
`fill_method="previous_close"`, `volume==0`, `no_trade` flag) are treated as actual trade
bars in feature or label computation, so a minute with no trade is mistaken for real activity.

### Impact
Volume, return, range, and path features/labels are computed over fabricated bars, inflating
sample counts and corrupting volatility/volume/path statistics. S2.

### Likelihood
L2 — the dense grid is convenient for alignment, and synthetic rows look like normal bars
unless their flags are checked.

### Detection
* FLF-P04 semantics expose predicates over `has_trade`/`synthetic`/`no_trade`; tests assert
  synthetic rows are excluded from trade-bar logic.
* Feature/label families consume the predicates; FLF-P12 structure primitives and FLF-P19
  path labels are audited for synthetic-row handling.
* `merge_policy.global_blockers`: `synthetic no-trade row treated as actual trade bar`.
* Claude Opus review of dense-grid semantics usage.

### Mitigation
Dense-grid no-trade rows are flagged (`has_trade=false`, `synthetic=true`, `no_trade`,
`volume==0`, `provider_bar_ref=None`) and never treated as trade bars; families use the FLF-P04
predicates to exclude or flag them; provider trade-truth is preserved.

### Owner
Codex (dense-grid semantics + family consumption) / Claude Opus (no-trade-handling review).

### Related Phases
FLF-P04, FLF-P08, FLF-P12, FLF-P19.

### Blocking Condition
A synthetic no-trade row is treated as an actual trade bar in any feature or label.

---

## R-013 — Cross-market timestamp misalignment

### Description
Cross-market ES/NQ/RTY features align series on the wrong timestamp (e.g. mixing `event_ts`
across instruments or ignoring per-instrument availability), so a cross-market spread/beta is
computed across non-contemporaneous, or future-peeking, bars.

### Impact
Cross-market return spreads, rolling beta residuals, and confirmation/divergence flags are
computed over misaligned bars, producing spurious cross-market signal and possible lookahead.
S2.

### Likelihood
L2 — aligning three instruments correctly on `available_ts` is error-prone, and a naive join
can silently peek forward on the slower-arriving instrument.

### Detection
* FLF-P11 cross-market families align strictly on `available_ts` via the FLF-P03 input views;
  tests assert contemporaneous, no-lookahead alignment across ES/NQ/RTY.
* No-lookahead tests cover the cross-market join; Databento and IBKR DatasetVersions are never
  merged.
* Claude Opus review of cross-market alignment semantics.

### Mitigation
Cross-market families consume `available_ts`-keyed input views and align on common
availability; no cross-instrument forward peeking; ES/NQ/RTY drawn from a single accepted
DatasetVersion family, never a Databento+IBKR merge.

### Owner
Codex (cross-market alignment + tests) / Claude Opus (alignment review).

### Related Phases
FLF-P03, FLF-P11.

### Blocking Condition
None on its own (S2, non-blocking); escalates to R-006/R-007 blocking if the misalignment
introduces lookahead or a missing `available_ts`.

---

## R-014 — Partition / locked-test contamination

### Description
The locked-test partition (`2025-01-01 → as_of_run`) is read or used to build/normalize
features or labels without recording governance contamination metadata, silently
contaminating the held-out window before any research begins.

### Impact
The locked-test window loses its held-out meaning at the substrate stage, weakening future
out-of-sample validation for everything built on top. S2.

### Likelihood
L2 — partition handling and normalization fits can inadvertently touch locked data without
recording contamination.

### Detection
* FLF-P01 consumption gates locked-partition use through
  `require_governance_metadata_for_locked_partition_use`; tests assert locked use records
  contamination metadata.
* Partition policy: development 2018–2022, validation 2023–2024, locked_test_candidate
  2025–as_of_run; `latest_shadow_candidate` optional.
* `merge_policy.global_blockers`: `locked-test partition used without contamination metadata`.
* Claude Opus review of partition handling in consumption and materialization.

### Mitigation
`locked_test_use_requires_governance_metadata: true`;
`partition_contamination_must_be_recorded: true`; any locked-partition use flows through the
governance contamination gate and records metadata; normalization/fit windows default to
development/validation partitions.

### Owner
Codex (partition gating + contamination metadata) / Claude Opus (partition review).

### Related Phases
FLF-P01, FLF-P14, FLF-P22, FLF-P26.

### Blocking Condition
The locked-test partition is used without recorded governance contamination metadata.

---

## R-015 — Feature/label materialization too large or slow

### Description
The feature/label materialization engines produce dry-run materializations that are too large
or too slow to run locally within reasonable bounds, or that tempt committing heavy outputs to
share results.

### Impact
Local dry runs become impractical, and pressure builds to commit heavy artifacts (which is
forbidden); the substrate's local-first, CI-safe property is weakened. S3.

### Likelihood
L2 — materialization over multiple instruments/partitions naturally grows large without
explicit bounds on the dry-run scope.

### Detection
* FLF-P13/FLF-P21 materialization engines expose a `FeatureMaterializationPlan` /
  `LabelMaterializationPlan` with bounded, configurable scope; FLF-P26/FLF-P30 dry runs use a
  small DatasetVersion.
* Dry-run docs/handoffs record runtime and size; values remain local-only.
* Claude Opus review of dry-run scope bounds; truthful `PASS_WITH_WARNINGS` allowed if slow.

### Mitigation
Materialization plans are explicitly bounded and configurable; dry runs use a small accepted
DatasetVersion; feature/label values are `local_only` and never committed; performance is a
documented, non-blocking concern resolved by scope, not by committing outputs.

### Owner
Codex (bounded materialization plans + dry-run scope) / Claude Opus (scope/perf review).

### Related Phases
FLF-P13, FLF-P21, FLF-P26, FLF-P30.

### Blocking Condition
None on its own (S3, non-blocking); becomes blocking via R-019 if heavy materialized outputs
are staged.

---

## R-016 — Feature/Label docs claim alpha value

### Description
Docs, family descriptions, diagnostics, or templates describe a feature or label as having
predictive/alpha value, or imply a feature "works" — conflating substrate construction with
alpha discovery.

### Impact
The substrate is misrepresented as containing validated alpha, misleading future researchers
and violating the campaign's no-claims framing (a feature is not alpha). S1.

### Likelihood
L2 — describing what a feature is "good for" easily slips into implying it predicts returns.

### Detection
* FLF-P15/FLF-P24 reports are descriptive/non-promotional by contract; diagnostics describe
  distributions/coverage, not predictive value.
* Docs (FLF-P29) follow `RESEARCH_INTERPRETATION_POLICY.md` no-claims language.
* `merge_policy.global_blockers`: `unsupported alpha/tradability claim introduced`.
* Claude Opus review of all committed docs/diagnostics for claim language.

### Mitigation
`alpha_tradability_claims_allowed_without_evidence: false`; diagnostics and docs are
explicitly descriptive (distribution, coverage, availability), never promotional; the
no-claims policy governs all committed text; a feature is not alpha.

### Owner
Codex (descriptive reports/docs) / Claude Opus (claims/no-claims review).

### Related Phases
FLF-P15, FLF-P24, FLF-P29.

### Blocking Condition
Any committed doc/report/diagnostic claims or implies alpha/predictive value for a feature or
label.

---

## R-017 — Unsupported alpha / tradability claims

### Description
Code, lifecycle states, reports, or handoffs assert alpha validity, profitability,
tradability, strategy/production/live readiness, or reach a prohibited MVP state
(`ALPHA_VALIDATED`, `STRATEGY_READY`, `LIVE_READY`, `PROFITABLE`, `TRADABLE`,
`PRODUCTION_READY`).

### Impact
The substrate falsely signals downstream readiness it has not earned, the highest-risk
semantic boundary violation for a substrate-only campaign. S1.

### Likelihood
L2 — convenience language and aspirational state names make these claims easy to introduce.

### Detection
* Lifecycle contracts make the prohibited MVP states **unreachable** by any transition; tests
  assert they cannot be set.
* Scope/claims audit across code, reports, and handoffs; `RESEARCH_INTERPRETATION_POLICY.md`
  governs language.
* `merge_policy.global_blockers`: `unsupported alpha/tradability claim introduced`;
  `strategy/backtest/portfolio scope introduced`.
* Claude Opus review and semantic done-check (FLF-P31).

### Mitigation
`production_trading_claims_allowed: false`; prohibited MVP states are listed as future-only
and are unreachable; precise wording throughout; no alpha/profitability/tradability/strategy/
production/live/broker claims; the done-check fails closed on any such claim.

### Owner
Ralph (scope/claims enforcement + done-check routing) / Claude Opus (semantic review).

### Related Phases
FLF-P02, FLF-P16, FLF-P29, FLF-P31.

### Blocking Condition
Any alpha/profitability/tradability/strategy/production/live/broker claim, or any prohibited
MVP lifecycle state, is introduced.

---

## R-018 — Tests only cover happy path

### Description
Tests exercise only the well-formed cases and omit the fail-closed paths — missing
`available_ts`/`label_available_ts`, absent `FeatureRequest`/`LabelSpec`, label-as-feature,
future/centered windows, BBO missingness, synthetic-row misuse, locked-partition use — so the
guards are never proven to actually block.

### Impact
The campaign's guards look present but are unverified; a regression could silently re-open a
leakage or governance hole without any test failing. S2.

### Likelihood
L3 — fail-closed/negative tests are the most commonly skipped, and the substrate depends
heavily on them.

### Detection
* FLF-P25 synthetic fixtures + fail-closed test suite explicitly cover each guard's blocking
  behavior; `tests/no_lookahead/feature_label/` covers causality/availability.
* Canary tests (`python tools/hooks/canary_runner.py`) fail when guards are bypassed.
* `merge_policy.global_blockers`: `test weakening detected`.
* Claude Opus review of negative-path coverage in FLF-P25 and family tests.

### Mitigation
FLF-P25 fail-closed tests assert each guard blocks on its violation; no-lookahead tests prove
causality/availability; canaries fail when guards are bypassed; test weakening is forbidden
and merge-blocking.

### Owner
Codex (fail-closed + no-lookahead tests) / Claude Opus (negative-coverage review).

### Related Phases
FLF-P25, FLF-P07, FLF-P23.

### Blocking Condition
None on its own (S2, non-blocking) unless test weakening/gaming is detected, which is a hard
merge-block.

---

## R-019 — Raw / heavy data artifacts committed

### Description
Raw/canonical data, materialized feature/label values, provider responses, heavy artifacts
(parquet/arrow/feather/`.dbn`/`.zst`/`.npy`/`.npz`), local DB/registry files
(sqlite/db/wal), logs, or caches are staged or committed instead of remaining local-only.

### Impact
Forbidden data/heavy artifacts enter git, violating the artifact policy and risking data
exposure; the campaign cannot be accepted. S1.

### Likelihood
L2 — materialization and reports produce heavy outputs near the repo that are easy to stage
without explicit, path-by-path staging.

### Detection
* `git ls-files runs` returns empty; artifact audit before every merge gate.
* `never_commit` globs (`data/raw/**`, `data/canonical/**`, `data/factors/**`, `data/labels/**`,
  `**/*.parquet|*.arrow|*.feather|*.dbn|*.zst|*.npy|*.npz`, `metadata/*.sqlite|*.db|*.wal`,
  `runs/**`).
* `merge_policy.global_blockers`: `raw or canonical data staged`, `feature or label values
  staged`, `heavy artifact staged`, `local DB staged`.
* Claude Opus review of the staged set; explicit-staging confirmation in every handoff.

### Mitigation
`feature_values_local_only` / `label_values_local_only`; explicit staging only (`git add .`/
`git add -A` forbidden); `never_commit` globs enforced; artifact audit before merge; tiny
synthetic fixtures only under `tests/fixtures/**`.

### Owner
Ralph (artifact policy + merge gating) / Codex (local-only writes + explicit staging).

### Related Phases
FLF-P13, FLF-P14, FLF-P15, FLF-P21, FLF-P22, FLF-P26, FLF-P30.

### Blocking Condition
Any raw/canonical data, feature/label value, provider response, heavy artifact, or local DB
is staged.

---

## R-020 — Governance gates bypassed

### Description
The campaign skips a required governance gate — materializing features without a validated
`FeatureSpec`/approved `FeatureRequest`, or labels without a validated `LabelSpec` — or
advances a lifecycle state past its required gate, bypassing the governance the prior campaign
installed.

### Impact
Ungoverned features/labels enter the substrate, defeating the request/spec gating and the
lifecycle that keeps the substrate disciplined. S2.

### Likelihood
L2 — gates are easy to short-circuit under time pressure, and one bypass normalizes more.

### Detection
* Lifecycle enforcement: `SPEC_VALIDATED` → `IMPLEMENTATION_ALLOWED` for features;
  `LABEL_SPEC_VALIDATED` → `MATERIALIZATION_ALLOWED` for labels; tests assert no skip.
* Materialization engines (FLF-P13/FLF-P21) refuse unvalidated specs.
* `merge_policy.global_blockers`: `FeatureRequest/FeatureSpec/LabelSpec bypassed`.
* Claude Opus review of gate ordering and the semantic done-check.

### Mitigation
`feature_spec_required` / `label_spec_required`; the lifecycle state models gate each
transition; materialization engines require validated specs and approved requests; no state is
reachable out of order.

### Owner
Codex (lifecycle gating + engine guards) / Claude Opus (gate-order review) / Ralph (merge-gate
enforcement).

### Related Phases
FLF-P05, FLF-P06, FLF-P13, FLF-P16, FLF-P21.

### Blocking Condition
A feature/label is materialized or advanced past a required governance gate without the
validated spec/approved request.

---

## R-021 — Agent Factory later cannot consume outputs cleanly

### Description
The `FeatureStore`/`LabelStore` interfaces, versioning, and `StudySpec` Input Pack handles are
shaped such that the future `ALPHA_AGENT_FACTORY_MVP` (AI Alpha Researchers consuming
`FeatureSet`+`LabelSet` via `StudySpec`) cannot cleanly resolve features/labels by version.

### Impact
The substrate fails its core purpose as a consumable input for downstream research, forcing
rework before the Agent Factory can use it. S2.

### Likelihood
L2 — without an explicit consumer contract, store/registry interfaces drift from what the
StudySpec consumer needs.

### Detection
* FLF-P14/FLF-P22 stores expose stable, versioned resolution; FLF-P27 StudySpec Input Pack
  bundles `freq_`/`lspec_`/`aspec_` handles + `dataset_scope` without modifying the StudySpec
  schema.
* FLF-P30 end-to-end dry run exercises the consumer path; FLF-P31 audit checks next-campaign
  readiness.
* Claude Opus review of the consumer-facing surface.

### Mitigation
Stores/registries expose versioned, deterministic resolution; the FLF-P27 StudySpec Input Pack
is additive (bundles handles a StudySpec references; does not modify the StudySpec schema or
governance modules); the end-to-end dry run validates the consumer path.

### Owner
Codex (store/registry + Input Pack) / Claude Opus (consumer-contract review) / ChatGPT
(roadmap framing for the Agent Factory consumer).

### Related Phases
FLF-P14, FLF-P22, FLF-P27, FLF-P30, FLF-P31.

### Blocking Condition
None on its own (S2, non-blocking); flagged in the FLF-P31 acceptance audit if the consumer
path is not demonstrably clean.

---

## R-022 — Feature/Label object duplication with Governance objects

### Description
The campaign re-implements governance objects (`FeatureRequest`, `LabelSpec`, `StudySpec`,
`AlphaSpec`) or their guards (duplicate-exposure, label-leakage) inside the feature/label
packages instead of consuming the existing, fully-built `src/alpha_system/governance/`
modules.

### Impact
Two divergent sources of truth for requests/specs/guards appear, so governance can be silently
bypassed through the duplicate and the prior campaign's governance is undermined. S2.

### Likelihood
L3 — re-defining a local `FeatureRequest`/`LabelSpec` is a tempting shortcut, and the campaign
explicitly flags this as the prime duplication risk.

### Detection
* Governance modules are in the per-phase `forbidden_paths` for feature/label phases (cannot
  be edited); the request gate (FLF-P05) and label contracts (FLF-P16) import and adapt them.
* FLF-P27 StudySpec Input Pack references governance handles without modifying the schema.
* `merge_policy.global_blockers`: `duplicate governance object`.
* Claude Opus review that governance is consumed, not re-implemented (the explicit R-022
  check in `review_must_check`).

### Mitigation
`consumes_governance_feature_request: true`; `consumes_governance_label_spec: true`;
governance modules (`feature_request.py`, `label_spec.py`, `study_spec.py`,
`duplicate_exposure.py`, `label_leakage_guard.py`) are consumed and are forbidden-to-edit;
no parallel re-implementation; the Input Pack is additive only.

### Owner
Codex (governance adapters, no re-implementation) / Claude Opus (duplication review).

### Related Phases
FLF-P05, FLF-P16, FLF-P27.

### Blocking Condition
Any governance object or guard is re-implemented in the feature/label packages instead of
consumed.

---

## R-023 — Labels tied too tightly to specific strategy wrappers

### Description
Label families encode a specific strategy's entry/exit logic or a particular trading wrapper
(rather than strategy-agnostic outcomes), so the labels presuppose a strategy and drift toward
strategy/backtest scope that is out of bounds for this campaign.

### Impact
Labels become strategy-specific instead of a reusable, strategy-agnostic substrate, narrowing
their usefulness and edging into forbidden strategy scope. S2.

### Likelihood
L2 — path/barrier labels naturally invite embedding a concrete strategy's stop/target logic.

### Detection
* FLF-P20 provides strategy-agnostic event labels; FLF-P19 path labels (MFE/MAE/triple
  barrier) are parameterized by spec, not by a strategy wrapper.
* Scope audit for strategy/backtest/portfolio code; `LabelSpec` `target_stop_rules` are
  generic, not a named strategy.
* `merge_policy.global_blockers`: `strategy/backtest/portfolio scope introduced`.
* Claude Opus review that labels stay strategy-agnostic.

### Mitigation
`strategy_backtest_portfolio_in_scope: false`; labels are strategy-agnostic and
spec-parameterized; barrier/path/event labels describe outcomes, not a strategy; no strategy
wrapper or backtest harness is introduced.

### Owner
Codex (strategy-agnostic label families) / Claude Opus (strategy-coupling review).

### Related Phases
FLF-P19, FLF-P20.

### Blocking Condition
None on its own (S2, non-blocking); becomes a hard merge-block via R-017 if a strategy/
backtest/portfolio wrapper is introduced.

---

## R-024 — BBO-derived cost labels mis-specified

### Description
Cost-/spread-adjusted labels derive their cost from BBO incorrectly — using a stale,
forward-filled, crossed, or `bbo_quarantined` quote, mis-applying `spread = ask - bid`, or
costing against a fabricated quote — so the cost adjustment is wrong.

### Impact
Cost-adjusted labels encode an incorrect transaction cost, biasing the cost-aware label set
the substrate is meant to provide. S2.

### Likelihood
L2 — BBO quoting/sizing edge cases (missing/crossed quotes, spread definition) are easy to
mis-handle when deriving costs.

### Detection
* FLF-P18 cost labels consume the FLF-P09 BBO features and FLF-P04 missingness flags; tests
  assert costs are not derived from `missing_bbo`/`bbo_quarantined` quotes and use
  `spread == ask - bid`.
* `CostAdjustmentSpec`/`cost_model` from the governance `LabelSpec` is applied with valid
  bid/ask only.
* Claude Opus review of the BBO→cost derivation.

### Mitigation
`spread_cost_fields_required: true`; cost labels use only valid (non-`missing_bbo`,
non-`bbo_quarantined`) quotes; `spread == ask - bid` and `mid == (bid+ask)/2` enforced;
microprice requires valid bid/ask sizes; the `CostAdjustmentSpec` cost model is applied per
governance `LabelSpec`. (Descriptive cost labels only — no tradability claim.)

### Owner
Codex (cost-label derivation + BBO validity) / Claude Opus (cost-spec review).

### Related Phases
FLF-P09, FLF-P18.

### Blocking Condition
None on its own (S2, non-blocking); becomes blocking via R-011 if a cost label is derived from
a silently forward-filled/abnormal quote.

---

## R-025 — Future Core Alpha Pilot blocked by missing base features/labels

### Description
The substrate omits base features or labels that the future `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
needs (e.g. a core OHLCV/BBO feature family, fixed-horizon/cost-adjusted labels), so the core
alpha pilot cannot proceed without first backfilling the substrate.

### Impact
The next campaign in the roadmap (Data Foundation → Feature/Label Foundation → Agent Factory →
Core Alpha) is blocked on missing substrate, forcing rework. S2.

### Likelihood
L2 — coverage gaps across five feature families and four+ label families are plausible without
a coverage check against the required object lists.

### Detection
* FLF-P15/FLF-P24 coverage reports enumerate implemented families against the required
  feature/label object and family lists.
* FLF-P30 end-to-end dry run exercises a representative feature+label set; FLF-P31 audit checks
  next-campaign readiness.
* Claude Opus review of family/object coverage vs the campaign's required lists.

### Mitigation
The required feature families (Base OHLCV, BBO, Session/Calendar/Roll, Cross-Market,
Liquidity/Structure) and label families (fixed-horizon/midprice, cost/spread-adjusted,
path MFE/MAE/triple-barrier, strategy-agnostic event) are each implemented; coverage reports
and the acceptance audit confirm the base set exists.

### Owner
Codex (family coverage) / Claude Opus (coverage/readiness review) / ChatGPT (roadmap
prioritization of base families).

### Related Phases
FLF-P08, FLF-P09, FLF-P17, FLF-P18, FLF-P19, FLF-P31.

### Blocking Condition
None on its own (S2, non-blocking); flagged in the FLF-P31 acceptance audit if a required base
feature/label family is missing.

---

## R-026 — DAG scheduler metadata missing or wrong

### Description
A phase declares incorrect or missing DAG metadata — `parallel_safe`, `must_run_alone`,
`allowed_paths`, `merge_group`, `conflicts_with`, or `dependencies` — so the DAG wave
scheduler either parallelizes a phase that should run alone or mis-orders the waves.

### Impact
The scheduler builds an unsafe wave (e.g. a run-alone integration phase running concurrently
with a family phase), risking path/resource conflicts and incorrect merge ordering. S2.

### Likelihood
L2 — DAG metadata is easy to get subtly wrong, and an omission defaults a phase into the wrong
parallel posture.

### Detection
* `just frontier-plan ALPHA_FEATURE_LABEL_FOUNDATION_V1` (read-only plan-dag) previews waves before any live run;
  `just frontier-run-parallel-mock ALPHA_FEATURE_LABEL_FOUNDATION_V1 3` validates parallel scheduling before the first live run.
* Default posture is conservative: omitting `parallel_safe`/`allowed_paths` means run-alone
  (`default_parallel_safe: false`, `default_must_run_alone: true`).
* `merge_policy.global_blockers`: `parallel phase lacks disjoint allowed_paths`.
* Claude Opus review of DAG metadata correctness (explicit `review_must_check` item).

### Mitigation
Parallel-safe phases (FLF-P08..P12, FLF-P17..P20, FLF-P24/P25/P27/P29) declare disjoint
`allowed_paths`, `must_run_alone: false`, and no global/coordinator file; everything else runs
alone by default; plan-dag and the parallel mock are run before live parallel execution.

### Owner
Ralph (DAG scheduler + plan/mock gating) / Claude Opus (DAG-metadata review).

### Related Phases
FLF-P08, FLF-P13, FLF-P24, FLF-P26, FLF-P28, FLF-P30, FLF-P31.

### Blocking Condition
A parallel-safe phase lacks disjoint `allowed_paths`, or DAG metadata schedules a run-alone
phase concurrently.

---

## R-027 — Parallel phase path conflict

### Description
Two phases in the same parallel wave write overlapping paths (e.g. a shared feature-core file,
a shared `__init__.py`, or the same config/doc), so concurrent worktrees produce conflicting
edits in a single wave.

### Impact
The parallel build produces a path/resource conflict within a wave, breaking the
build-in-isolation guarantee and risking merge corruption. S2.

### Likelihood
L2 — five concurrent feature families (and four concurrent label families) can easily collide
on a shared core file unless `allowed_paths` are strictly disjoint and shared core is
forbidden.

### Detection
* Family phases forbid editing shared feature/label core (contracts, store, engine, registry,
  primitives, `families/__init__.py`) via per-phase `forbidden_paths`; `allowed_paths` are the
  disjoint family dirs only.
* Plan-dag/mock detect path/resource conflicts before live runs; isolated worktrees per phase.
* `merge_policy.global_blockers`: `parallel wave has path/resource conflict`.
* Claude Opus review of disjointness across the wave.

### Mitigation
`parallel_safe_phases_require_disjoint_allowed_paths`; each family writes only its own
`families/<name>/**`, `tests/.../<name>/**`, `docs/.../<name>.md`, `configs/.../<name>/**`;
shared core is forbidden to family phases; conflicts are detected by plan-dag/mock and are
merge-blocking.

### Owner
Ralph (conflict detection + serial merge) / Codex (additive, disjoint family writes) / Claude
Opus (disjointness review).

### Related Phases
FLF-P08, FLF-P09, FLF-P10, FLF-P11, FLF-P12, FLF-P17, FLF-P18, FLF-P19, FLF-P20, FLF-P24,
FLF-P25, FLF-P27, FLF-P29.

### Blocking Condition
Two phases in the same parallel wave declare or write overlapping paths.

---

## R-028 — ACTIVE_CAMPAIGN.md conflict in parallel wave

### Description
A phase branch writes `ACTIVE_CAMPAIGN.md` while running in parallel mode, but that file is
coordinator-owned; concurrent phase branches editing it would conflict and corrupt the
coordinator's single source of campaign pointer truth.

### Impact
The coordinator-owned `ACTIVE_CAMPAIGN.md` is contended across parallel phase branches,
breaking the `update_active_campaign: coordinator_only` invariant. S2.

### Likelihood
L2 — bootstrap-style phases historically wrote the pointer, so a phase branch writing it is a
plausible carryover unless explicitly forbidden.

### Detection
* `ACTIVE_CAMPAIGN.md` is in the per-phase `forbidden_paths` (e.g. FLF-P00) and is never in any
  phase's `allowed_paths`; the bootstrap phase's "Non-Goals" forbid writing it.
* `update_active_campaign: coordinator_only`; `phase_branches_do_not_write_active_campaign`.
* `merge_policy.global_blockers`: `phase branch writes ACTIVE_CAMPAIGN.md in parallel mode`.
* Claude Opus review that no phase branch writes the pointer.

### Mitigation
`ACTIVE_CAMPAIGN.md` is coordinator-owned; no phase branch writes it in parallel mode; it is a
forbidden path for phases; the coordinator updates the campaign pointer outside phase branches.

### Owner
Ralph (coordinator-owned pointer + merge gating) / Claude Opus (pointer-ownership review).

### Related Phases
FLF-P00, FLF-P08, FLF-P24, FLF-P31.

### Blocking Condition
Any phase branch writes `ACTIVE_CAMPAIGN.md` in parallel mode.

---

## R-029 — Serial merge queue bypassed

### Description
Two PRs from a parallel wave are merged concurrently (or out of the serial queue) instead of
one at a time, so the "parallel build, serial merge" invariant is broken and merges interleave.

### Impact
Concurrent merges can interleave changes from a wave, defeating the serial-merge safety the
DAG scheduler depends on and risking a corrupt main. S2.

### Likelihood
L1 — the merge queue is serial by configuration (`merge_queue: serial`,
`parallel_build_serial_merge: true`), so a bypass is unlikely; it remains tracked because the
consequence is a corrupt merge.

### Detection
* `merge_queue: serial`; `parallel_build_serial_merge: true`; Ralph merges one PR at a time
  through the queue.
* `serial_merge_queue_required` is a `workflow2.requirements` entry; plan/mock confirm serial
  merge.
* `merge_policy.global_blockers`: `merge occurs outside serial merge queue`.
* Claude Opus review of merge-queue behavior in the run summary.

### Mitigation
Merge is always serial — one PR at a time — regardless of parallel build; the serial merge
queue is required and any merge outside it is merge-blocking; Ralph owns merge ordering.

### Owner
Ralph (serial merge queue + merge gating) / Claude Opus (merge-order review).

### Related Phases
FLF-P08, FLF-P17, FLF-P24, FLF-P30, FLF-P31.

### Blocking Condition
A merge occurs outside the serial merge queue, or two wave PRs merge concurrently.

---

## R-030 — External provider call introduced by mistake

### Description
Feature/label or dry-run code introduces an external Databento/IBKR (or any provider) call —
even a "small" one in the dry-run phases — despite the campaign being entirely local-only over
already-pulled, accepted DatasetVersions.

### Impact
An external provider call runs in a campaign that must make none, crossing the local-only
boundary, spending budget without authorization, and risking CI/credential exposure. S1.

### Likelihood
L1 — the campaign consumes already-pulled local DatasetVersions and has no RED-lane phases, so
an external call is unlikely; it remains S1 because the consequence is a serious boundary
violation.

### Detection
* `no_external_provider_calls_in_this_campaign: true`; the consumption adapter (FLF-P01) reads
  only local accepted DatasetVersions via `resolve_dataset_version`; no provider client is
  imported.
* The "Small Real Databento DatasetVersion Dry Run" (FLF-P26) consumes a small **already-local**
  accepted DatasetVersion — it does not pull from Databento.
* `merge_policy.global_blockers`: `external provider call attempted`;
  `forbidden_global_changes`: `external provider call`.
* Claude Opus review of FLF-P26/FLF-P30 dry runs; CI never runs a real pull.

### Mitigation
`external_provider_calls_require_red_authorization: true` and this campaign has **no RED
phases**; all consumption is local-only over accepted DatasetVersions; no provider client is
imported by feature/label/dry-run code; an external call attempt is fail-closed and
merge-blocking.

### Owner
Ralph (scope/stop enforcement + merge gating) / Codex (local-only consumption, no provider
client) / Claude Opus (boundary review).

### Related Phases
FLF-P01, FLF-P26, FLF-P30.

### Blocking Condition
Any external Databento/IBKR (or other provider) call is attempted from any phase.

---

## Blocking Risk Summary

The following are hard STOP/merge-block conditions (each maps to a
`merge_policy.global_blockers` entry or a fail-closed gate): **R-002, R-003, R-005, R-006,
R-007, R-008, R-009, R-011, R-012, R-014, R-016, R-017, R-019, R-020, R-022, R-026, R-027,
R-028, R-029, R-030**. Any one of these makes the affected phase ineligible for merge until
resolved or truthfully blocked.

The remaining risks (**R-001, R-004, R-010, R-013, R-015, R-018, R-021, R-023, R-024,
R-025**) are non-blocking on their own (S2/S3) but are reviewed at their related phases and
several escalate into a blocking condition when they cross into a leakage, claim, artifact, or
test-weakening violation (noted in each entry).

## Risk Review Cadence

* **Per phase**: Claude Opus review checks the risks tied to that phase's Related Phases (the
  `review_must_check` list in `campaign.yaml` covers consumption, governance reuse,
  `available_ts`/`label_available_ts`, label-as-feature, BBO/no-trade, locked partition,
  DAG metadata, serial merge, artifact policy, and claims).
* **Per gate**: each acceptance gate re-checks all blocking risks for its phases
  (`canonical_inputs` → R-006/R-007/R-011/R-012; `feature_contracts` → R-003/R-004/R-005/R-006;
  `feature_families`/`label_families` → R-005/R-008/R-026/R-027; `label_materialization` →
  R-008/R-009/R-014; `workflow_and_closeout` → R-016/R-017/R-022/R-029).
* **Per parallel wave**: before each live parallel run, `just frontier-plan ...` and
  `just frontier-run-parallel-mock ... 3` re-verify R-026/R-027/R-028/R-029.
* **Campaign closeout (FLF-P31)**: the full register is reviewed in the semantic done-check,
  including the no-claims/no-leakage audit (R-016/R-017) and next-campaign readiness
  (R-021/R-025).

## Risk Ownership Summary

* **Ralph** — scope/stop enforcement, artifact policy + merge gating, DAG scheduler and
  serial merge queue, coordinator-owned `ACTIVE_CAMPAIGN.md`, and external-call prevention
  (R-017, R-019, R-026, R-027, R-028, R-029, R-030; merge-gate enforcement of R-020).
* **Codex** — fail-closed consumption and governance adapters, `available_ts`/
  `label_available_ts` wiring, BBO/no-trade semantics, causal primitives, contracts, stores/
  registries, fail-closed/no-lookahead tests, and local-only writes (R-001, R-002, R-003,
  R-004, R-005, R-006, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-018,
  R-022, R-023, R-024, R-025).
* **Claude Opus** — semantic review of the consumption boundary, governance reuse, no-lookahead/
  availability, leakage, claims/no-claims, DAG metadata, serial merge, and the final
  done-check (the semantic review side of every risk; primary on R-016, R-017, R-021).
* **ChatGPT** — roadmap framing and consumer prioritization for the downstream Agent Factory
  and Core Alpha Pilot (R-021, R-025) and post-run reasoning.
* **Human (repo owner)** — direction and capital/live judgment; this campaign is local-only
  with no RED scope and no external provider calls, so no per-operation human authorization is
  required, but the human owns final acceptance of the substrate.
