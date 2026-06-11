# Review: P111500_FUTSUB_P19_COST_TEST_RECONCILE (WF1)

- Reviewer: fresh adversarial Claude agent, 2026-06-11
- Verdict: **PASS_WITH_WARNINGS**
- Scope: restore cost_adjusted fast-vs-reference parity after FUTSUB-P19
  moved reference semantics (bar_end_ts keying + shared guard); 4 files:
  labels/fast/{materializer,panel}.py + 2 LCFP regression test files.

## Deterministic evidence
- Parity is genuine: bar-end anchoring, duplicate collapse, terminal keying,
  branch order/flags, and label_available_ts all verified line-by-line
  against the post-P19 reference family; fast CALLS the same
  _guarded_forward_terminal (no second guard truth); no fixture-shaped
  constants or test-only branches.
- Coverage intact: assert counts 22→22 and 64→64; 15→15 tests; tolerance
  unchanged (1e-12); maintenance-crossing and misaligned-BBO assertions are
  STRONGER than before (both-engine drop + absolute anchor-set pinning).
- Mutation hardness: guard-bypass mutation → maintenance-crossing parity
  test FAILED; raw-event_ts mutation → misaligned-BBO test FAILED; both
  restored, final diff clean.
- Validation: 91 passed (fast-path + scaleout label suites), labels suites
  green, verify --smoke exit 0, 14/14 canaries.
- Forbidden paths untouched (families/engine/roll_guard/version);
  identity/values-only invariant preserved; production default engine
  remains reference.

## Warnings (follow-ups, not correctness defects)
- W1: fast entry_bbo_gap branch now lacks a direct fast-suite fixture
  (reference-side coverage survives) — add invalid-entry + valid-terminal
  parity fixture later.
- W2: new duplicate-BBO fast branches verified by inspection, not fixture.
- W3 (pre-existing, NOT introduced here): synthetic_no_trade reference gap
  branch has no fast equivalent — a parity hole invisible to current
  fixtures; MUST be addressed before any future fast-promotion of
  cost_adjusted (recorded for the fast-promotion gate).
- W4: dead derive_label_available_ts COST_ADJUSTED branch in panel.py.
- W5: spec done-criteria reconciled with the amendment (this commit).
