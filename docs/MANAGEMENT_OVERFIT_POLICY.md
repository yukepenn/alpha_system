# Management Overfit Policy

Management rules can overfit historical paths when many stop, target, partial,
cooldown, and holding parameters are searched without strict controls. This
repository treats management-grid execution as deferred to `ASV1-P21`.

For this phase:

- `alpha management grid` validates configs only.
- Unbounded grid definitions are rejected.
- No survivor workflow, approval workflow, or automatic promotion is available.
- No equity curves, management study outputs, or trade logs are written by the
  management CLI.
- A tiny validation summary may be written only when the caller provides an
  explicit temp/local JSON path outside the repository.

Future grid execution must remain bounded, reproducible, and reviewed before
merge eligibility. Reports and docs must avoid claims of profitability,
tradability, or operational readiness.
