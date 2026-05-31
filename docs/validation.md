# Validation

Document standard validation commands and when to use them.

Default commands:

```bash
python tools/verify.py --smoke
python tools/verify.py --lint
python tools/verify.py --typecheck
python tools/verify.py --test
python tools/verify.py --all
python tools/hooks/canary_runner.py
```

Record command output in handoffs or reviews when validation informs a decision.
