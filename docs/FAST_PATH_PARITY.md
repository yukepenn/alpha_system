# Fast Path Parity

ASV1-P19 introduces a scoped fast path for local research simulation. The fast
path is acceleration only. The Tier 1 reference 1-minute engine remains the
single PnL truth, and fast-path output is usable only when deterministic parity
has passed for the selected feature set.

## Parity Model

Parity cases live in `src/alpha_system/backtest/parity_cases.py`. Each case
defines:

- tiny synthetic in-memory bars and signals,
- the reference configuration,
- any management specification,
- feature labels,
- expected fast-path route,
- deterministic tolerance.

The checker in `src/alpha_system/backtest/parity.py` runs the reference engine
and the fast path with the same fixture, run id, config, and initial cash. It
compares these parity domains:

- summary,
- trade journal,
- equity curve,
- fills.

Manifest metadata is not a parity truth domain. It remains reproducibility
metadata. No parity run writes trade logs, equity logs, benchmark output, array
files, registry files, or database files into the repository.

## Supported Accelerated Feature Set

The ASV1-P19 accelerated subset is intentionally narrow:

| Feature | Route | Tolerance |
| --- | --- | --- |
| no-trade hold-only case | accelerated | exact |
| simple long entry and signal exit | accelerated | exact |
| simple short entry and signal exit | accelerated | exact |
| fixed bps costs through the reference compatibility hook | accelerated | exact |
| fixed percent stop | accelerated | exact |
| fixed percent target | accelerated | exact |
| same-bar stop/target ambiguity | accelerated, adverse-first | exact |
| reference `eod_flat` exit | accelerated | exact |
| deterministic trade summary | accelerated | exact |
| deterministic equity curve | accelerated | exact |

Exact means zero decimal tolerance for summary, trade, equity, and fill fields.
The fixtures use Decimal-compatible values so exact equality is expected.

## Reference Fallback Features

Some features are covered by parity but are not accelerated in ASV1-P19. They
route to the reference path instead of being approximated:

| Feature | Route |
| --- | --- |
| slippage-configured execution metadata | reference fallback |
| laddered partial exits | reference fallback through management adapter |
| cooldown | reference fallback through management adapter |
| max holding bars | reference fallback through management adapter |
| management EOD exit | reference fallback through management adapter |
| ATR, volatility, breakeven, trailing, time, scale-in, scale-out rules | reference fallback |
| portfolio desired exposure or target semantics | reference fallback |
| multi-instrument or multi-session fixtures | reference fallback |

Fallback parity proves that the fast-path entrypoint did not silently
approximate the feature. It does not certify accelerated grid use for that
feature.

## Grid Gate

Later grid code must require a `ParityCertification` from:

```python
from alpha_system.backtest.parity import (
    assert_grid_fast_path_allowed,
    certify_parity,
)

certification = certify_parity()
assert_grid_fast_path_allowed(certification, ("simple_long", "fixed_stop"))
```

`assert_grid_fast_path_allowed` fails closed unless every requested feature is
covered by a passing accelerated parity case. Features that only passed through
reference fallback remain blocked from fast-path grid use.

## Truth Boundary

The reference engine remains canonical accounting truth. The fast path reuses
reference validators, signal scheduling, result containers, fill construction,
and accounting helpers. The reference engine is not modified to match fast-path
output. Any divergence is a fast-path defect or an unsupported feature that must
fail closed or use reference fallback.

These fixtures are correctness checks only. They are not market evidence and do
not support alpha, profitability, robustness, tradability, broker, paper, live,
or production claims.
