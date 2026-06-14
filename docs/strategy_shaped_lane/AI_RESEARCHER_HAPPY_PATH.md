# AI Researcher Happy Path

This is the canonical V0 flow for a human or AI researcher using the
strategy-shaped lane.

## Flow

1. Start from an idea stated as a mechanism, not as a result.
2. Declare a `MechanismCard` with source, rationale, expected mechanism,
   horizon, session, required features, required labels, cost sensitivity,
   variant budget, duplicate-exposure note, and `EXPLORATORY` stamp.
3. Declare a `SetupSpec` with entry context, event trigger separate from
   context, regime filter, confirmation, invalidation, stop, target, hold time,
   horizon, path-label binding, allowed variants, forbidden post-hoc changes,
   mechanism link, and `EXPLORATORY` stamp.
4. Run the bounded EXPLORATORY conditional probe over existing path labels and
   existing path-outcome diagnostics. The probe remains quarantined and
   variant-ledgered.
5. If the readout is interesting, run the trusted-handoff scaffold. The scaffold
   emits missing `AlphaSpec`, `StudySpec`, `FeatureRequest`, and `LabelSpec`
   objects and fields for a later trusted rerun. The handoff is still
   `EXPLORATORY`; the promotion guard must refuse it.
6. Author and run the trusted rerun separately. This step is outside V0 and is
   the first place trusted-lane evidence can be created.
7. After the trusted lane has a reviewed verdict, route durable survivor memory
   only through the governed memory path.

## Handoff Boundary

The trusted-handoff report is a checklist, not evidence. It names the specs and
fields that must be supplied for a separate trusted rerun. It does not change a
lifecycle state, does not create a `PromotionDecision`, does not remove the
`EXPLORATORY` stamp, and does not make a result claim.

## V0 Boundaries

- EXPLORATORY artifacts are not promotion evidence.
- The trusted and promotion paths refuse `EXPLORATORY`-stamped artifacts.
- The single-factor path and SSRL-P02 conditional compiler remain additive and
  unchanged.
- Research code has no reference-sim bridge.
- V0 does not build sequence logic, geometry sweeps, a feature fast lane, a PA
  grammar pack, or a trusted rerun.
- V0 adds no runtime dependency, paid data, broker operation, paper/live
  workflow, order routing, deployment, or live-use approval.
