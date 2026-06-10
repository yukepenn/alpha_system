# Path Label Fast Pack

LCFP-P05 adds the governed path-label pack under `alpha_system.labels.fast`:

- `build_path_label_pack(...)` for `mfe`, `mae`,
  `target_before_stop`, and `triple_barrier` definitions.

The pack emits `LabelValueRecord` values only. It preserves
`label_version_id` identity from the reference-derived `LabelContractSpec` and
does not write registries by itself.

## Routing

| Label | Fast route | Safe fallback | Reason |
| --- | --- | --- | --- |
| `mfe` | P02 guarded panel scan | Reference path family | MFE is max favorable return over the retained path window. |
| `mae` | P02 guarded panel scan | Reference path family | MAE is min adverse return over the retained path window. |
| `target_before_stop` | P02 guarded panel first-touch scan | Reference path family | First-touch ordering and same-bar policy are explicit and parity-tested. |
| `triple_barrier` | P02 guarded panel first-touch scan | Reference path family | Target, stop, horizon timeout, and same-bar ambiguity map to the reference outcomes. |

The kernelized boundary is a P02 `TerminalKind.FIXED_HORIZON` terminal whose
minutes equal the governed path `horizon_steps` on the shared panel. Roll and
maintenance crossing dispositions come from that terminal model. If a caller
cannot satisfy the P02 terminal proof boundary, it must route the label through
the reference path family rather than widening tolerance or changing semantics.

## Same-Bar Policy

Same-bar target/stop ambiguity follows
`alpha_system.labels.families.path.SameBarBarrierPolicy` exactly:

- `ambiguous`: barrier value is null and quality flags include
  `ambiguous_same_bar_barrier`;
- `target_first`: target wins on the same bar;
- `stop_first`: stop wins on the same bar.

Barrier-never-touched rows resolve at the retained terminal as the reference
horizon outcome, with `horizon_no_barrier` on target/stop labels.

## Guard And Gap Coverage

The P05 tests cover:

- target-first and stop-first rows;
- same-bar ambiguous rows and the forced target-first / stop-first policy
  variants;
- barrier-never-touched timeout rows;
- no-trade session-gap source rows omitted like the reference path family;
- roll-crossing and maintenance-crossing source rows dropped by the P02
  terminal guard before value emission.

Path value assertions use `abs=1e-12, rel=1e-12` because the reference computes
from `Decimal` OHLCV input rows while the fast panel stores floats. Timestamp,
identity, event-set, same-bar quality flag, horizon-timeout quality flag, and
guard-disposition assertions remain exact.
