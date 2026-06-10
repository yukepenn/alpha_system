# Operating Discipline (recurring corrections, encoded once)

- Verify before believing: never act on an audit/review/doc claim (including your
  own earlier finding) without re-verifying it against the current code. Audit
  claims have been wrong here before (fabricated README finding; the "safe"
  62-file archive move).
- Test before apply: for any destructive or wide change, run the narrowest real
  check first and stage a reversible dry-run when one exists. This discipline is
  what caught the random_target canary and the spurious `--strict` preflight.
- Uncertain ⇒ keep: when deletion/retention is ambiguous, keep and record the
  question; never delete on suspicion.
- No silent scope expansion: aggressive or surprising changes get surfaced
  before execution, not discovered in the diff.
- Live status comes from `python tools/frontier/status_doctor.py`, never from
  committed pointers. Structure comes from `docs/SYSTEM_MAP.md` (generated).
- Review stance is adversarial, not hygiene: assume tests were weakened, status
  is stale, and a second truth leaked until the diff proves otherwise.
- Research-only language: no alpha/profitability/tradability/production claims;
  diagnostics and gates decide, not priors.
- FUTSUB campaign work requires explicit user go-ahead while its run is stopped.
