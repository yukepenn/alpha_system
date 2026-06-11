---
campaign_id: DISCOVERY_RIGOR_FLOOR_V1
phase_id: P233000_RIGOR_P01_CI_REPAIR
lane: yellow
status: in_progress
---

# P233000_RIGOR_P01_CI_REPAIR: build-evidence trial-ledger-path plumbing

## Purpose

RIGOR-P01 (PR #374) added the spec-authorized fail-closed
`require_trial_ledger_present()` gate on the DIAGNOSTICS_RUN→EVIDENCE_READY
transition (`src/alpha_system/governance/promotion_gate.py:207`, context
field at `:108`). CI is red because the gate is unsatisfiable from the CLI:
`run_build_evidence` (`src/alpha_system/cli/governance.py:287-317`)
constructs `PromotionGateContext(evidence_bundle=bundle)` with no
`trial_ledger_path`, and the `build-evidence` parser (`:473-482`) exposes no
flag. Two pre-existing end-to-end consumers therefore fail with
`missing_trial_ledger_path`:

- `tests/integration/governance/test_cli_smoke.py::test_governance_cli_end_to_end_smoke`
- `tests/integration/governance/test_end_to_end_dry_run.py::test_synthetic_end_to_end_governance_dry_run`

The gate semantics are CORRECT and must not change. The repair plumbs the
path through the CLI and updates the two consumers to satisfy the gate.

## Scope (in-bounds)

1. `src/alpha_system/cli/governance.py`:
   - Add `--trial-ledger-path` option to the `build-evidence` subparser
     (default `None`, help text naming the fail-closed gate). Do NOT make it
     argparse-required: the promotion gate, not argparse, is the enforcement
     point, so the fail-closed rejection path stays executable end to end.
   - Pass it through: `PromotionGateContext(evidence_bundle=bundle,
     trial_ledger_path=args.trial_ledger_path)`.
   - On success include `resolved_trial_ledger_path` in the JSON payload.
2. Update both failing tests to write a small valid trial-ledger JSON file
   (regular file, readable+writable, parseable JSON — see
   `require_trial_ledger_present()` in
   `src/alpha_system/governance/promotion_gate.py:302+`) under the test tmp
   dir and pass `--trial-ledger-path` to `build-evidence`. Reuse each test's
   existing trial-record fixtures for ledger content where natural; an
   honest minimal JSON document is acceptable if the gate only checks
   parseability.
3. Add a NEGATIVE test (in `tests/integration/governance/test_cli_smoke.py`
   or the unit CLI test module if one exists): `build-evidence` WITHOUT
   `--trial-ledger-path` exits non-zero and the JSON error payload contains
   `"code": "missing_trial_ledger_path"` and `"status": "rejected"`.

## Hard constraints

- Do NOT modify `require_trial_ledger_present()` or any promotion-gate
  semantics, reason codes, canaries, or bypass tests from RIGOR-P01.
- Do NOT touch `runs/**`, registries, values, or any forbidden path from the
  RIGOR-P01 spec (no historical Core Pilot evidence mutation).
- No `git worktree` commands; no `.git` config edits; explicit staging only;
  work only on the current branch of this worktree.
- Research-only language in any text you write.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/integration/governance -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/governance tests/unit/cli -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit tests/no_lookahead tests/integration -q
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
```

Full-suite green modulo the 3 known pre-existing env failures; exact counts
in the handoff.

## Done criteria

- Both previously failing integration tests pass by SATISFYING the gate
  (real ledger file + flag), not by weakening it; negative rejection test
  exists and passes; full validation green; truthful handoff appended to
  the executor notes; fresh adversarial review PASS or PASS_WITH_WARNINGS
  under `reviews/DISCOVERY_RIGOR_FLOOR_V1/`.
