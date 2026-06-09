# ADR-0009: Two-Lane Feature Authoring (Research Fast Lane + Promotion Gate)

## Status

Proposed (architecture direction). Drafted during `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
(FUTSUB-P14, first full-window V1 feature materialization). Implementation is a
scoped follow-up campaign `FEATURE_RESEARCH_FAST_LANE_V1`, to be authored **after**
FUTSUB closes. Non-blocking for the current campaign.

## Context

The original system intent is a research harness where an alpha researcher can
**quickly backtest a strategy over data we already have, and quickly add the
features a strategy needs.** [ADR-0007](0007-producer-compute-fast-path.md)
delivered the producer compute fast path (V1 Polars pack-materializer, ~100-500x
over the reference engine), and `FEATURE_COMPUTE_FAST_PATH_V1` productionized it
with CPU worker parallelism. So the *compute* is fast: materializing one feature
for a recent symbol-year slice is seconds; a single family full-window is minutes.

A timing analysis during FUTSUB-P14 surfaced a tension with the "fast" intent. The
current path forces **every** new feature through the full production gate **before**
a researcher can test it:

```text
reference-engine impl  ->  V1 fast expression  ->  parity test  ->  WF2 review  ->  merge  ->  THEN backtest
```

That ceremony is correct for a feature that production alpha conclusions depend on
(the no-second-truth invariant, [ADR-0002](0002-reference-backtest-truth.md),
AGENTS.md "Do not create a second PnL/value truth"). But it is the wrong **entry**
cost for "I have a hunch — does this feature have any signal at all?" The researcher
pays the **promotion** price for the ~95% of experiments that will be discarded.

Two distinct modes are currently conflated under one gate:

1. **Exploration** — try a feature idea, look for signal, iterate fast, discard most.
   A wrong value here means "this experiment was inconclusive," not "production is
   poisoned." Speed and iteration dominate.
2. **Promotion** — a promising feature graduates into the trusted substrate that
   real alpha conclusions (and eventually capital) depend on. Here reference parity,
   the oracle, and no-second-truth are essential.

The system **already has** an explore-then-promote ladder — for *alpha ideas*
(`REJECT / INCONCLUSIVE / WATCH / CANDIDATE` in the Core Alpha Pilot). **Feature
authoring lacks the equivalent ladder**: features are forced to production-trusted
status on day one. Empirically, FUTSUB-P14 itself confirms the cost is in authoring/
governance, not compute — regime's `returns` / `rolling_range` were already governed
and only needed *materializing*, which took minutes.

## Decision

Adopt a **two-lane feature-authoring model**: parity-gating is a **promotion** gate,
not an **entry** gate. Give feature authoring the same explore-then-promote ladder the
system already trusts for alpha ideas.

### Lane 1 — Research sandbox (fast, minutes; explicitly untrusted)

- A researcher authors a feature as a **V1 fast-engine expression only** — no
  reference implementation, no parity test required to start.
- It materializes into a **quarantined namespace** with provenance
  `producer_engine_id = v1_unverified` and `parity_status = UNVERIFIED`, defaulting to
  a **small slice** (one symbol, recent year) — sufficient to detect signal.
- The researcher backtests immediately. Every result computed against an unverified
  feature is **auto-stamped `EXPLORATORY — unverified feature; not parity-gated`**.
- This does **not** violate "no second truth." The value is explicitly labeled
  untrusted and is **structurally barred** from entering the promoted/trusted
  substrate, any registry resolver used by trusted studies, or any production
  conclusion. A clearly-quarantined, labeled hypothesis is not a competing truth —
  the invariant protects against two *trusted* truths coexisting, which the
  fail-closed promotion boundary preserves.

### Lane 2 — Promotion (rigorous; only for survivors)

- Only when a sandbox feature shows promise does it graduate: write the
  **reference-engine implementation** + the **parity test** proving the V1 expression
  matches the oracle, routed through one **WF2 phase** (spec -> Codex execute ->
  Claude parity review -> CI -> merge).
- On promotion the feature flips to `parity_status = VERIFIED`,
  `producer_engine_id = producer_fast_path_v1`, and becomes resolvable by trusted
  studies. The expensive governance tax is paid **only for the features that survive
  exploration**, not the ones discarded.

### Supporting levers (ship alongside)

- **Research-slice defaults** — exploration defaults to one-symbol / recent-year
  (seconds), not full accepted window. Full-window is a promotion/production concern.
- **Feature scaffold generator** — one command stubs the reference impl + V1
  expression + parity-test skeleton from a feature spec, cutting *promotion* time.
- **(Longer-term) Expression DSL** — author a feature **once** as a declarative spec;
  the system generates *both* the naive-reference and vectorized-fast implementations
  and auto-derives the parity test. Structurally eliminates the "write it twice" tax,
  the real long-term cause of slow promotion. Highest effort; revisit only if feature
  velocity becomes the dominant constraint.

### Hard invariants preserved

- The reference engine remains the sole correctness oracle
  ([ADR-0002](0002-reference-backtest-truth.md)).
- Trusted feature values still require a passing reference-parity gate before any
  trusted study or production conclusion may use them.
- The sandbox/quarantine boundary must **fail closed**: an `UNVERIFIED` feature lock
  is unresolvable by the trusted resolver; any trusted study that references one is a
  blocking error, not a silent downgrade.
- Value/accounting math stays in the sanctioned reference engine; the fast path emits
  values only and stays reference-parity-gated for trusted use
  ([ADR-0006](0006-feature-label-value-storage.md), [ADR-0007](0007-producer-compute-fast-path.md)).

## Consequences

**Positive**

- Exploration collapses from "hours-to-a-day" to **minutes**, reconciling the harness
  with its original "fast backtest, fast feature-add" intent — *without* weakening the
  production gate.
- Governance cost is paid only for surviving features (the minority), not every
  experiment.
- Conceptually consistent with the existing alpha promotion ladder; an extension of a
  trusted pattern, not a new paradigm.
- Exploratory results are self-labeling, so an unverified-feature result can never be
  mistaken for a trusted finding.

**Negative / risks**

- A new quarantine namespace + `parity_status` provenance + a fail-closed promotion
  boundary is real engineering and a new surface to keep honest (the boundary must be
  canary-tested so an `UNVERIFIED` value can never leak into a trusted study).
- Researcher discipline: exploratory results must be read as exploratory. The
  auto-stamp mitigates this but does not eliminate it.
- Two lanes mean two materialization namespaces to reason about; status reporting must
  make a feature's lane/parity status obvious.

**Neutral**

- Does not change the compute engine, the reference oracle, or the trusted resolver
  semantics — only adds an explicitly-untrusted lane in front of them and moves the
  parity gate from "entry" to "promotion."

## Proposed Implementation Campaign (`FEATURE_RESEARCH_FAST_LANE_V1`, post-FUTSUB)

Sketch only — to be authored with `frontier-campaign` after FUTSUB closes and the
current V1 substrate is verified.

- **P0x — Sandbox namespace + provenance**: `parity_status` (`UNVERIFIED`/`VERIFIED`)
  and `producer_engine_id = v1_unverified` in feature registry metadata; quarantined
  materialization path under `ALPHA_DATA_ROOT`; no commit of values.
- **P0x — Fail-closed promotion boundary + canary**: trusted resolver refuses
  `UNVERIFIED` locks; a safety canary fails if an unverified value resolves in a
  trusted study.
- **P0x — Fast research CLI**: `alpha feature explore --expr ... --symbols ES --years 2024`
  -> materialize quarantined slice -> backtest with `EXPLORATORY` stamping.
- **P0x — Promotion command**: scaffold reference impl + parity test, run parity gate,
  flip to `VERIFIED` on pass (WF2 phase).
- **P0x — Scaffold generator** (supporting lever).
- **(Deferred) Expression DSL** — separate later campaign if justified.

Acceptance: a researcher can author an exploratory feature and see a stamped backtest
in **minutes**; an `UNVERIFIED` feature provably cannot enter any trusted study
(canary-enforced); promotion remains fully parity-gated.
