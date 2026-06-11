# Review: P233000_RIGOR_P01_CI_REPAIR — build-evidence trial-ledger-path plumbing

- Campaign: `DISCOVERY_RIGOR_FLOOR_V1`
- Phase: `P233000_RIGOR_P01_CI_REPAIR` (Workflow-1 CI repair for PR #374)
- Reviewer: Claude (fresh adversarial review)
- Date: 2026-06-11
- Worktree reviewed: `/home/yuke_zhang/projects/alpha_system-discovery_rigor_floor_v1-rigor-p01`
  (branch `auto/discovery_rigor_floor_v1/rigor-p01-verdict-reason-code-taxonomy-ledger-presence-gates-core-pilot-annotations`,
  HEAD `0632faf`, uncommitted repair diff)
- Spec: `specs/DISCOVERY_RIGOR_FLOOR_V1/P233000_RIGOR_P01_CI_REPAIR-build-evidence-ledger-path-plumbing.md`
- Stance: adversarial; assumed gate-weakening until disproven by deterministic evidence.

## Verdict

**PASS**

## 1. Scope check — PASS

`git status --short` shows exactly the four authorized files, nothing else:

```text
 M src/alpha_system/cli/governance.py
 M tests/integration/governance/test_cli_smoke.py
 M tests/integration/governance/test_end_to_end_dry_run.py
 M tests/unit/governance/test_cli.py
```

No staged files, no new files, no `runs/**`, no registries/values/generated
artifacts (artifact-policy check, section 6).

## 2. Gate integrity — PASS

- `git diff --stat -- src/alpha_system/governance/` is **empty**:
  `promotion_gate.py` (including `require_trial_ledger_present()` at `:302+`
  and the `trial_ledger_path` context field at `:108`) is byte-for-byte
  untouched. `evals/canaries/` diff is also empty.
- The CLI change is pure pass-through:
  `PromotionGateContext(evidence_bundle=bundle, trial_ledger_path=args.trial_ledger_path)`.
  No default other than `None`, no fabrication, no auto-create, no skip.
- The argparse option is `default=None` and intentionally NOT
  `required=True`, per spec: the promotion gate (which raises
  `missing_trial_ledger_path` on `None`) remains the enforcement point, and
  the rejection path stays executable end to end. Verified
  `require_trial_ledger_present()` does the real work: substantive-string
  check, `stat()`, regular-file check, read/write permission-bit checks,
  `open("r+")`, JSON parse — all in untouched code.
- `resolved_trial_ledger_path` is added to the success payload only AFTER
  `validate_governance_transition` passes, so it cannot mask a rejection.

## 3. Test honesty — PASS

- Both integration consumers satisfy the gate with a REAL file: a new
  `_trial_ledger_file()` helper in each test module writes
  `tmp_path / "trial-ledger.json"` via the existing `_write_json()` (regular
  file, default-umask readable+writable, valid JSON containing the test's own
  `TrialLedgerRecord.to_dict()` records — reusing existing fixtures as the
  spec asked). The path is passed via `--trial-ledger-path` on the real CLI
  invocation (subprocess in both integration tests).
- Zero occurrences of `monkeypatch`, `mock`, or `patch(` in any of the three
  test files. No gate, context, or transition function is stubbed.
- Negative test `test_build_evidence_without_trial_ledger_path_rejects_at_gate`
  (tests/unit/governance/test_cli.py) runs the real CLI `main()` without the
  flag and asserts `code == 2` (the `_run_json_command` rejection exit code,
  strictly non-zero), `payload["status"] == "rejected"`, and
  `payload["issues"][0]["code"] == "missing_trial_ledger_path"` — exactly the
  spec's required assertions.
- `TrialLedgerRecord` import confirmed pre-existing in `test_cli_smoke.py`
  (line 20) and `test_end_to_end_dry_run.py` (line 65); helper annotations
  resolve.

## 4. Mutation tests (executed in the worktree) — BOTH PASS

Baseline `git diff` snapshot sha256
`0b08e0de3e290cd0bb31605f2ad284abeaf8cf756b6e60ee8853c2b181b89c39` taken
before mutations.

### Mutation A — revert the plumbing

Edited `run_build_evidence` context construction back to
`PromotionGateContext(evidence_bundle=bundle)` (flag still parsed, value
dropped). Ran the two integration tests:

```text
FAILED tests/integration/governance/test_cli_smoke.py::test_governance_cli_end_to_end_smoke
FAILED tests/integration/governance/test_end_to_end_dry_run.py::test_synthetic_end_to_end_governance_dry_run
2 failed in 2.89s
```

Expected FAIL, observed FAIL → the integration tests genuinely depend on the
pass-through; they are not green by accident.

### Mutation B — silent fabricated default

Edited `run_build_evidence._execute` to fabricate an existing parseable temp
JSON file whenever `args.trial_ledger_path is None` (simulating a silent
default that would neuter the fail-closed gate). Ran the negative test:

```text
FAILED tests/unit/governance/test_cli.py::test_build_evidence_without_trial_ledger_path_rejects_at_gate
1 failed in 0.53s   (AssertionError at the `code == 2` assertion)
```

Expected FAIL, observed FAIL → the negative test catches this class of
weakening.

### Restoration

Restored from the pre-mutation copy. Post-restore `git diff` sha256 equals
the baseline (`0b08e0de…b89c39`), and `sha256sum -c` over all four modified
files reports OK. Worktree left byte-identical; post-restore sanity run of
the three key tests: `3 passed in 5.49s`.

## 5. Validation counts — PASS

```bash
~/.venvs/alpha_system_research/bin/python -m pytest \
  tests/integration/governance tests/unit/governance tests/unit/cli -q
```

Result: **613 passed, 0 failed, 0 errors, 0 skipped** (10.28s). This includes
the 8 integration governance tests (the two previously failing CI tests now
pass) and the new negative rejection test.

## 6. Artifact policy — PASS

Worktree contains no new untracked files; nothing staged; no `runs/**`,
SQLite/registry, Parquet/value, or generated-report paths in the diff. Test
artifacts (ledger JSON, sqlite registries) are created strictly under pytest
`tmp_path`.

## Findings

1. (INFO, non-blocking) The negative test pins the exact rejection exit code
   `2` rather than merely non-zero. This matches the stable
   `_run_json_command` contract and is strictly stronger than the spec's
   minimum; noted only so a future exit-code refactor knows this test will
   flag it.
2. (INFO, non-blocking) The executor ran only the first two spec validation
   commands (documented truthfully in the executor notes as user-directed for
   this CI-repair turn). This review independently re-ran the contracted
   validation command (613 passed) and verified zero diff in
   `src/alpha_system/governance/` and `evals/canaries/`, so canary/full-suite
   exposure from this diff is nil; CI on PR #374 remains the final arbiter.

No gate-weakening, scope, honesty, or artifact findings.
