"""Per-instrument contract-multiplier resolution for the reference engine.

The reference backtest accounts for PnL in *dollars*, which requires the futures
contract multiplier (ES=50, NQ=20, RTY=50, ...). The multiplier is economic
identity, not market data, so it is resolved here at the engine boundary keyed by
the bars' ``instrument_id`` and threaded into accounting.

Resolution is FAIL-LOUD by construction: an unknown instrument raises rather than
silently defaulting to ``1`` (the historical silent bug). There is exactly one
source of multiplier truth (the futures instrument master); callers may supply an
explicit ``instrument_id -> root_symbol`` mapping (real canonical bars use
``instrument_id`` values such as ``inst_databento_es`` that are not root symbols)
or an explicit ``instrument_id -> multiplier`` override for synthetic fixtures
whose instrument is intentionally not in the master.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal, InvalidOperation

from alpha_system.data.foundation.instruments import (
    InstrumentMasterRecord,
    load_futures_instrument_master_by_root,
)


class InstrumentMultiplierError(ValueError):
    """Raised when a traded instrument's contract multiplier cannot be resolved."""


def _decimal(value: object, instrument_id: str) -> Decimal:
    if isinstance(value, bool):
        msg = f"instrument multiplier for {instrument_id!r} must be numeric, not boolean"
        raise InstrumentMultiplierError(msg)
    if isinstance(value, Decimal):
        active = value
    else:
        try:
            active = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            msg = f"instrument multiplier for {instrument_id!r} must be numeric"
            raise InstrumentMultiplierError(msg) from exc
    if not active.is_finite() or active <= 0:
        msg = f"instrument multiplier for {instrument_id!r} must be a positive finite value"
        raise InstrumentMultiplierError(msg)
    return active


def resolve_instrument_multipliers(
    instrument_ids: Iterable[str],
    *,
    multipliers: Mapping[str, object] | None = None,
    roots: Mapping[str, str] | None = None,
    master: Mapping[str, InstrumentMasterRecord] | None = None,
) -> dict[str, Decimal]:
    """Resolve a positive contract multiplier for every traded instrument.

    Resolution order, per ``instrument_id``:

    1. explicit ``multipliers`` override (fixtures / out-of-master instruments);
    2. the futures instrument master, keyed by ``roots[instrument_id]`` if a
       mapping is supplied, otherwise by ``instrument_id`` interpreted directly as
       a root symbol;
    3. otherwise FAIL LOUD.

    The master is the single source of multiplier truth; this helper never returns
    a silent default of ``1``.
    """

    override = {str(key): value for key, value in (multipliers or {}).items()}
    root_map = {str(key): str(value) for key, value in (roots or {}).items()}
    resolved: dict[str, Decimal] = {}
    master_records: Mapping[str, InstrumentMasterRecord] | None = master
    for raw_instrument_id in instrument_ids:
        instrument_id = str(raw_instrument_id)
        if instrument_id in resolved:
            continue
        if instrument_id in override:
            resolved[instrument_id] = _decimal(override[instrument_id], instrument_id)
            continue
        root_symbol = root_map.get(instrument_id, instrument_id).strip().upper()
        if master_records is None:
            master_records = load_futures_instrument_master_by_root()
        record = master_records.get(root_symbol)
        if record is None:
            msg = (
                f"cannot resolve contract multiplier for instrument {instrument_id!r} "
                f"(root {root_symbol!r}): not in the futures instrument master and no "
                "explicit multiplier override was supplied; refusing to default to 1"
            )
            raise InstrumentMultiplierError(msg)
        resolved[instrument_id] = _decimal(record.multiplier, instrument_id)
    return resolved


__all__ = ["InstrumentMultiplierError", "resolve_instrument_multipliers"]
