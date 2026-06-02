"""Deterministic, injectable run-id generation."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any

from alpha_system.core.hashing import hash_config


Clock = Callable[[], datetime]


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _slug_prefix(prefix: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", prefix).strip("_").lower()
    if not slug:
        msg = "run-id prefix must contain at least one alphanumeric character"
        raise ValueError(msg)
    return slug


def generate_run_id(
    prefix: str,
    *,
    timestamp: datetime | None = None,
    clock: Clock | None = None,
    seed: str = "",
    components: Mapping[str, Any] | None = None,
) -> str:
    """Generate a run id that is deterministic when timestamp/clock are injected."""
    if timestamp is not None and clock is not None:
        msg = "provide either timestamp or clock, not both"
        raise ValueError(msg)
    if timestamp is not None:
        effective_timestamp = timestamp
    elif clock is not None:
        effective_timestamp = clock()
    else:
        effective_timestamp = datetime.now(timezone.utc)
    effective_timestamp = _coerce_utc(effective_timestamp)
    normalized_prefix = _slug_prefix(prefix)
    timestamp_token = effective_timestamp.strftime("%Y%m%dT%H%M%S%fZ")
    payload = {
        "prefix": normalized_prefix,
        "timestamp": effective_timestamp,
        "seed": seed,
        "components": components or {},
    }
    suffix = hash_config(payload)[:16]
    return f"{normalized_prefix}_{timestamp_token}_{suffix}"
