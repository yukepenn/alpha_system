# Validation

Default commands:

```bash
python tools/verify.py --smoke
python tools/verify.py --lint
python tools/verify.py --typecheck
python tools/verify.py --test
python tools/verify.py --all
python tools/hooks/canary_runner.py
just frontier-doctor
just verify-canaries
python tools/verify.py --artifacts
```

Workflow2 smoke validation:

```bash
FRONTIER_MOCK_PROVIDERS=1 FRONTIER_MAX_PHASES=1 just frontier-run-campaign G005_WORKFLOW2_TOY
just frontier-acceptance
```

Generated CI compiles tools/tests, runs pytest when tests exist, runs frontier doctor, runs canaries, and checks artifact policy. It does not fail solely because project tests are absent.

Provider-wired validation records `validation.md` for each phase. CI polling records `ci_status.json` and `ci_status.md`; branch protection records `branch_protection.json` and `branch_protection.md`; merge policy records `merge_gate.json` and `merge_gate.md`.

Record relevant command output in handoffs or reviews when validation informs a decision. Do not hide failed commands or convert failures into passing summaries.
