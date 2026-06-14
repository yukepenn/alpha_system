# PA_GRAMMAR_SUBSTRATE_V1

`PA_GRAMMAR_SUBSTRATE_V1` is the reserved name for a future price-action grammar
substrate. It is not built in STRATEGY_SHAPED_RESEARCH_LANE_V0.

## Naming

- Use `PA_GRAMMAR_SUBSTRATE_V1` for any future reusable price-action grammar
  substrate.
- Keep `FactorLibrary` reserved for surviving-alpha memory only.
- Do not route exploratory setup declarations into `FactorLibrary`.

## Positioning

The substrate name separates reusable grammar from survivor memory:

- `PA_GRAMMAR_SUBSTRATE_V1` is a future content substrate for expressing setup
  shapes, tokens, and naming conventions.
- `FactorLibrary` is reserved for records that survive the governed memory path
  after trusted-lane review.
- `MechanismCard` and `SetupSpec` stay the V0 declaration surface for
  strategy-shaped exploratory work.

## Shape Split

Use factor-first shape when the research question is a point-in-time or
path-outcome read:

- A single factor or small set of factors is the primary object.
- Existing path labels and diagnostics are enough to read the question.
- The existing single-factor path or bounded conditional probe is sufficient.

Use setup-first shape when the research question is a sequence or a
context-not-trigger shape:

- Entry context and event trigger must be separate.
- Confirmation, invalidation, stop, target, and hold time are part of the
  declaration.
- A `SetupSpec` is the governed surface, and any later trusted rerun must be
  authored through the trusted-lane spec chain.

## Non-Build Statement

This note names and positions the substrate only. It does not define a grammar
pack, add a parser, add sequence logic, add geometry sweeps, create trusted-lane
evidence, or change promotion policy.
